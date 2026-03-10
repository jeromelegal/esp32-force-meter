import socket
import json
import gestion_programmes
import urequests
import time

TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJzdHJlbmd0aC1kZXZpY2UtdjEiLCJzY29wZXMiOlsiaW5nZXN0OnN0cmVuZ2h0Il0sImlzcyI6InBvbXBldHJhY2stZGV2aWNlIn0.uAm1CGALvtnXLKOczM_WMjLDd93goy-wR1gnn9bu0Lc"

# ====================== UTILITAIRES ======================
def init_serveur():
    """Initialise et retourne un serveur web non-bloquant sur le port 80"""
    serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serveur.bind(('', 80))
    serveur.listen(1)
    serveur.setblocking(False)
    return serveur

def urldecode(texte):
    """Décode une chaîne URL-encodée (remplace %xx et +)"""
    result = []
    i = 0
    while i < len(texte):
        if texte[i] == '+':
            result.append(' ')
            i += 1
        elif texte[i] == '%' and i + 2 < len(texte):
            try:
                hex_val = texte[i+1:i+3]
                result.append(chr(int(hex_val, 16)))
                i += 3
            except ValueError:
                result.append(texte[i])
                i += 1
        else:
            result.append(texte[i])
            i += 1
    return ''.join(result)

def extraire_parametres(chemin):
    """Extrait la route et les paramètres d'une URL"""
    params = {}
    if '?' in chemin:
        chemin_base, requete = chemin.split('?', 1)
        paires = requete.split('&')
        for paire in paires:
            if '=' in paire:
                cle, valeur = paire.split('=', 1)
                params[cle] = urldecode(valeur)
        return chemin_base, params
    return chemin, params


def generer_json_payload(programmes):
    """Génère le JSON payload dans le format cible avec métriques structurées"""
    payload = {
        "metrics": []
    }

    t = time.gmtime()
    timestamp_iso = "%04d-%02d-%02dT%02d:%02d:%02d+00:00" % (
        t[0], t[1], t[2], t[3], t[4], t[5]
    )

    for programme in programmes:
        if not programme["valeurs"]:
            continue  # Ignore les programmes sans mesures

        # Convertir les valeurs en Newtons (1 kg ≈ 9.81 N)
        valeurs_n = [round(valeur * 9.81, 2) for valeur in programme["valeurs"]]

        metric = {
            "name": programme["nom"],
            "type": "force",
            "data": []
        }

        for valeur in valeurs_n:
            metric["data"].append({
                "qty": valeur,
                "date": timestamp_iso,
                "units": "N"
            })

        payload["metrics"].append(metric)

    return json.dumps(payload)

# ====================== ROUTES ======================
def generer_html_dashboard(programmes, token):
    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dynamometer Dashboard</title>

<style>
body {{ font-family: Arial; margin:20px; max-width:800px; margin:auto; }}
.card {{ border:1px solid #ddd; padding:15px; margin-bottom:15px; border-radius:8px; }}
.btn {{ padding:10px; border:none; border-radius:5px; color:white; font-weight:bold; width:100%; }}
.btn-send {{ background:#28a745; }}
.btn-reset {{ background:#dc3545; }}
.btn-edit {{ background:#007bff; display:block; text-align:center; text-decoration:none; padding:10px; color:white; }}
textarea {{ width:100%; font-family:monospace; }}
</style>
</head>

<body>

<h1>Session Measurements</h1>

<a href="/programmes" class="btn-edit">Edit Programs</a>

<hr>

<div id="mesures-container">Loading...</div>

<hr>

<h2>JSON Payload Preview</h2>

<textarea id="json-payload" rows="12"></textarea>

<hr>

<h2>Export Data</h2>

<input type="text" id="endpoint-url" value="http://ingestion.lan/ingest/strength">

<br><br>

<button class="btn btn-send" onclick="envoyerAuPC()">Send to PC</button>

<br><br>

<button class="btn btn-reset" onclick="window.location.href='/reset_mesures'">
Reset Session
</button>

<script>

const TOKEN = "{token}"

function chargerMesures() {{

fetch('/api/mesures')
.then(r => r.json())
.then(programmes => {{

afficherMesures(programmes)

const payload = {{
metrics: []
}}

programmes.forEach(p => {{

if(p.valeurs.length === 0) return

const metric = {{
name: p.nom,
type: "force",
data: []
}}

p.valeurs.forEach(v => {{

metric.data.push({{
qty: Math.round(v * 9.81 * 100) / 100,
date: new Date().toISOString(),
units: "N"
}})

}})

payload.metrics.push(metric)

}})

document.getElementById("json-payload").value =
JSON.stringify(payload,null,4)

}})

}}

function afficherMesures(programmes) {{

const container = document.getElementById("mesures-container")

container.innerHTML = ""

programmes.forEach(p => {{

const div = document.createElement("div")
div.className = "card"

let valeurs = "No measurements yet"

if(p.valeurs.length > 0){{
valeurs = p.valeurs.map(v => (v*9.81).toFixed(2) + " N").join(", ")
}}

div.innerHTML =
"<h3>"+p.nom+"</h3>"+
"<p><b>Results:</b> "+valeurs+"</p>"+
"<p>Target: "+p.poids+" kg</p>"+
"<p>Duration: "+p.temps+" s</p>"

container.appendChild(div)

}})

}}

function envoyerAuPC() {{

const url = document.getElementById("endpoint-url").value
const jsonText = document.getElementById("json-payload").value

try {{
JSON.parse(jsonText)
}} catch(e) {{
alert("Invalid JSON")
return
}}

fetch("/envoyer?url="+encodeURIComponent(url),{{

method:"POST",

headers:{{
"Content-Type":"application/json",
"Authorization":"Bearer "+TOKEN
}},

body:jsonText

}})
.then(r=>r.json())
.then(r=>alert("Result: "+JSON.stringify(r)))
.catch(e=>alert(e))

}}

chargerMesures()

</script>

</body>
</html>
"""
    return html

def generer_html_programmes(programmes):
    """Génère le HTML de la page de gestion des programmes"""
    liste_html = ""
    for p in programmes:
        liste_html += f"<li>{p['nom']} - {p['temps']}s - {p['poids']}kg "
        liste_html += f"<a href='/supprimer?id={p['id']}' style='color:red;'>[Delete]</a></li>"

    html = f"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Programs Management</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; max-width: 800px; margin: auto; }}
            .btn {{ padding: 10px 15px; margin: 5px 0; cursor: pointer; border: none; border-radius: 5px; color: white; font-weight: bold; }}
            .btn-back {{ background-color: #007bff; text-decoration: none; display: inline-block; margin-bottom: 20px; }}
            input[type="text"], input[type="number"] {{ padding: 8px; width: 100%; box-sizing: border-box; margin-bottom: 10px; }}
        </style>
    </head>
    <body>
        <h1>Programs Management</h1>
        <a href="/" class="btn btn-back">← Back to Dashboard</a>
        <ul>
            {liste_html}
        </ul>
        <hr>
        <h3>Add a program</h3>
        <form action="/ajouter" method="GET">
            Name: <input type="text" name="nom" required><br><br>
            Time (s): <input type="number" name="temps" required><br><br>
            Weight (kg): <input type="number" step="0.1" name="poids" required><br><br>
            <button type="submit" class="btn" style="background-color: #28a745;">Add Program</button>
        </form>
    </body>
    </html>"""
    return html

def gerer_route_envoyer(conn, lignes, params, token):
    """Gère l'envoi de données vers un endpoint externe"""
    try:
        if 'url' not in params:
            raise ValueError("Missing 'url' parameter")

        url = urldecode(params['url'])
        print(f"[DEBUG] Decoded URL: {url}")

        # Extraire les headers
        headers_dict = {}
        body_start = 0
        for i, ligne in enumerate(lignes):
            if not ligne:
                body_start = i + 1
                break
            if ':' in ligne:
                key, value = ligne.split(':', 1)
                headers_dict[key.strip().lower()] = value.strip()

        content_length = int(headers_dict.get('content-length', 0))
        if content_length == 0:
            raise ValueError("Missing Content-Length header")

        # Extraire le body
        body = '\r\n'.join(lignes[body_start:])

        # Lire le reste si nécessaire
        while len(body) < content_length:
            chunk = conn.recv(1024)
            if not chunk:
                break
            body += chunk.decode()

        print(f"[DEBUG] Received body length: {len(body)} / {content_length}")
        print(f"[DEBUG] Received body: {body[:100]}...")

        # Valider le JSON
        try:
            json_data = json.loads(body)
        except ValueError as e:
            raise ValueError(f"Invalid JSON: {str(e)}")

        # Envoyer la requête
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {token}',
            'User-Agent': 'ESP32-Dynamometer/1.0'
        }

        print(f"[DEBUG] Sending to {url}")
        response = urequests.post(url, data=json.dumps(json_data), headers=headers)

        # Gérer la réponse
        print(f"[DEBUG] Response: {response.status_code}")
        if 200 <= response.status_code < 300:
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            conn.sendall(json.dumps({
                "success": True,
                "status": response.status_code,
                "response": response.text
            }).encode())
        else:
            conn.send(b"HTTP/1.1 502 Bad Gateway\r\nContent-Type: application/json\r\n\r\n")
            conn.sendall(json.dumps({
                "success": False,
                "status": response.status_code,
                "error": response.text
            }).encode())

        response.close()

    except Exception as e:
        print(f"[ERROR] /envoyer: {str(e)}")
        conn.send(b"HTTP/1.1 400 Bad Request\r\nContent-Type: application/json\r\n\r\n")
        conn.sendall(json.dumps({
            "success": False,
            "error": str(e)
        }).encode())

# ====================== SERVEUR PRINCIPAL ======================
def gerer_requetes(serveur, programmes, token):
    """Gère les requêtes HTTP entrantes"""
    try:
        conn, addr = serveur.accept()
        requete = conn.recv(1024).decode('utf-8')

        if not requete:
            conn.close()
            return

        lignes = requete.split('\r\n')
        if len(lignes[0].split(' ')) > 1:
            url_complete = lignes[0].split(' ')[1]
        else:
            url_complete = '/'

        route, params = extraire_parametres(url_complete)

        # --- ROUTING ---
        if route == '/':
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            conn.sendall(generer_html_dashboard(programmes, token).encode())

        elif route == '/programmes':
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n")
            conn.sendall(generer_html_programmes(programmes).encode())

        elif route == '/envoyer':
            gerer_route_envoyer(conn, lignes, params, token)

        elif route == '/ajouter':
            if 'nom' in params and 'temps' in params and 'poids' in params:
                nouvel_id = max((p['id'] for p in programmes), default=0) + 1
                programmes.append({
                    "id": nouvel_id,
                    "nom": params['nom'],
                    "temps": int(params['temps']),
                    "poids": float(params['poids']),
                    "valeurs": [],
                    "total": 3
                })
                gestion_programmes.sauvegarder(programmes)
            conn.send(b"HTTP/1.1 303 See Other\r\nLocation: /programmes\r\n\r\n")

        elif route == '/supprimer':
            if 'id' in params:
                id_a_supprimer = int(params['id'])
                programmes[:] = [p for p in programmes if p['id'] != id_a_supprimer]
                gestion_programmes.sauvegarder(programmes)
            conn.send(b"HTTP/1.1 303 See Other\r\nLocation: /programmes\r\n\r\n")

        elif route == '/api/mesures':
            conn.send(b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\n\r\n")
            conn.sendall(json.dumps(programmes).encode())

        elif route == '/reset_mesures':
            for p in programmes:
                p["valeurs"] = []
            gestion_programmes.sauvegarder(programmes)
            conn.send(b"HTTP/1.1 303 See Other\r\nLocation: /\r\n\r\n")

        else:
            conn.send(b"HTTP/1.1 404 Not Found\r\n\r\n")

        conn.close()

    except OSError:
        pass
    except Exception as e:
        print("Server error:", e)
        try:
            conn.close()
        except:
            pass
