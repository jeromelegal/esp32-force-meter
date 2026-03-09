import socket
import json
import gestion_programmes

def init_serveur():
    """ Initializes and returns a non-blocking web server on port 80 """
    serveur = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serveur.bind(('', 80))
    serveur.listen(1)
    # Non-blocking mode is crucial so the main loop can continue reading the button/sensor
    serveur.setblocking(False) 
    return serveur

def urldecode(texte):
    """ Simple decoder for URL-encoded text (replaces + and %20 with spaces) """
    return texte.replace('+', ' ').replace('%20', ' ')

def extraire_parametres(chemin):
    """ Extracts the base route and query parameters from a URL """
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

def gerer_requetes(serveur, programmes):
    """ Main function to handle incoming HTTP requests """
    try:
        conn, addr = serveur.accept()
        requete = conn.recv(1024).decode('utf-8')
        
        # If the request is empty, close the connection and exit
        if not requete:
            conn.close()
            return

        # Extract the requested URL (e.g., "GET /ajouter?nom=Test HTTP/1.1" -> "/ajouter?nom=Test")
        lignes = requete.split('\r\n')
        if len(lignes[0].split(' ')) > 1:
            url_complete = lignes[0].split(' ')[1]
        else:
            url_complete = '/'

        # Separate the route from its parameters
        route, params = extraire_parametres(url_complete)

        # --- 1. HOME PAGE: THE DASHBOARD ---
        if route == '/':
            html = """<!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Dynamometer Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; max-width: 800px; auto; }
                    .card { border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 8px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
                    .btn { padding: 10px 15px; margin: 5px 0; cursor: pointer; border: none; border-radius: 5px; color: white; font-weight: bold; width: 100%; box-sizing: border-box;}
                    .btn-send { background-color: #28a745; }
                    .btn-reset { background-color: #dc3545; }
                    .btn-edit { background-color: #007bff; text-decoration: none; display: block; text-align: center; }
                    input[type="text"], textarea { padding: 10px; width: 100%; box-sizing: border-box; margin-bottom: 10px; border: 1px solid #ccc; border-radius: 4px; }
                    textarea { font-family: monospace; font-size: 14px; resize: vertical; }
                    .header { display: flex; justify-content: space-between; align-items: center; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Session Measurements</h1>
                </div>

                <a href="/programmes" class="btn btn-edit">📝 Edit Programs</a>
                <hr>

                <!-- Measurements cards will be injected here -->
                <div id="mesures-container"><i>Loading measurements...</i></div>

                <hr>
                <h2>JSON Payload Preview</h2>
                <p style="font-size: 0.9em; color: #555;">You can manually edit the JSON data here before sending:</p>
                <textarea id="json-payload" rows="12"></textarea>

                <hr>
                <h2>Export Data</h2>
                <label>PC Endpoint (e.g., http://192.168.1.50:8000/api) :</label>
                <input type="text" id="endpoint-url" value="http://ingestion.lan/api/data">

                <button class="btn btn-send" onclick="envoyerAuPC()">📤 Send to PC</button>
                <br><br>
                <button class="btn btn-reset" onclick="window.location.href='/reset_mesures'">🗑️ Reset Session on ESP32</button>

                <script>
                    // 1. Fetch JSON data from the ESP32 API
                    fetch('/api/mesures')
                        .then(response => response.json())
                        .then(data => {
                            afficherMesures(data);
                            // Inject formatted JSON into the textarea (4 spaces indentation)
                            document.getElementById('json-payload').value = JSON.stringify(data, null, 4);
                        });

                    // 2. Render UI cards for each program
                    function afficherMesures(programmes) {
                        const container = document.getElementById('mesures-container');
                        container.innerHTML = '';

                        programmes.forEach(prog => {
                            const div = document.createElement('div');
                            div.className = 'card';

                            // Format the measured values
                            let valeursHtml = prog.valeurs.length > 0 
                                ? prog.valeurs.map(v => v + " Kg").join(', ') 
                                : "<span style='color:gray;'>No measurements yet</span>";

                            div.innerHTML = `
                                <h3 style="margin-top:0;">${prog.nom}</h3>
                                <p style="margin:5px 0;">Goal: ${prog.valeurs.length} / ${prog.total} measurements</p>
                                <p style="margin:5px 0;"><strong>Results:</strong> ${valeursHtml}</p>
                            `;
                            container.appendChild(div);
                        });
                    }

                    // 3. Send data (modified or not) via POST request to the PC
                    function envoyerAuPC() {
                        const url = document.getElementById('endpoint-url').value;
                        const jsonText = document.getElementById('json-payload').value;

                        // Security: Check if the user manually broke the JSON format
                        try {
                            JSON.parse(jsonText);
                        } catch (e) {
                            alert("❌ Error: Invalid JSON format. Check quotes, commas, and brackets!");
                            return; 
                        }

                        // Send valid JSON to the target URL
                        fetch(url, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: jsonText
                        })
                        .then(response => {
                            if(response.ok) alert("✅ Data successfully sent!");
                            else alert("⚠️ The PC responded with an error.");
                        })
                        .catch(err => alert("❌ Network Error. Check the PC IP and server status.\\nDetails: " + err));
                    }
                </script>
            </body>
            </html>
            """
            conn.send("HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n")
            conn.sendall(html)

        # --- 2. PROGRAMS MANAGEMENT PAGE ---
        elif route == '/programmes':
            liste_html = ""
            for p in programmes:
                liste_html += f"<li>{p['nom']} - {p['temps']}s - {p['poids']}kg "
                liste_html += f" <a href='/supprimer?id={p['id']}' style='color:red;'>[Delete]</a></li>"

            html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>Programs</title></head>
<body>
    <h1>Programs Management</h1>
    <p><a href="/">Back to Dashboard</a></p>
    <ul>
        {liste_html}
    </ul>

    <hr>
    <h3>Add a program</h3>
    <form action="/ajouter" method="GET">
        Name: <input type="text" name="nom" required><br><br>
        Time (s): <input type="number" name="temps" required><br><br>
        Weight (kg): <input type="number" step="0.1" name="poids" required><br><br>
        <button type="submit">Add</button>
    </form>
</body></html>"""
            conn.send("HTTP/1.1 200 OK\nContent-Type: text/html\nConnection: close\n\n")
            conn.sendall(html)

        # --- 3. ACTION: ADD A PROGRAM ---
        elif route == '/ajouter':
            if 'nom' in params and 'temps' in params and 'poids' in params:
                # Find the highest existing ID to create a unique new ID
                nouvel_id = 1
                if len(programmes) > 0:
                    nouvel_id = max(p['id'] for p in programmes) + 1

                nouveau_prog = {
                    "id": nouvel_id,
                    "nom": params['nom'],
                    "temps": int(params['temps']),
                    "poids": float(params['poids']),
                    "valeurs": [],  
                    "total": 3      
                }
                programmes.append(nouveau_prog)
                # Save changes to flash memory
                gestion_programmes.sauvegarder(programmes) 

            # Redirect back to the programs list
            conn.send("HTTP/1.1 303 See Other\nLocation: /programmes\nConnection: close\n\n")

        # --- 4. ACTION: DELETE A PROGRAM ---
        elif route == '/supprimer':
            if 'id' in params:
                id_a_supprimer = int(params['id'])
                # Rebuild the list WITHOUT the program we want to delete
                programmes[:] = [p for p in programmes if p['id'] != id_a_supprimer]
                # Save changes to flash memory
                gestion_programmes.sauvegarder(programmes) 

            # Redirect back to the programs list
            conn.send("HTTP/1.1 303 See Other\nLocation: /programmes\nConnection: close\n\n")

        # --- 5. API: RETURN DATA AS JSON ---
        elif route == '/api/mesures':
            # Returns the full programs list (including current measurements)
            donnees_json = json.dumps(programmes)
            conn.send("HTTP/1.1 200 OK\nContent-Type: application/json\nConnection: close\n\n")
            conn.sendall(donnees_json)

        # --- 6. ACTION: RESET ALL MEASUREMENTS ---
        elif route == '/reset_mesures':
            # Iterate through all programs and clear their values list
            for p in programmes:
                p["valeurs"] = []

            # Save the cleared state to flash memory
            gestion_programmes.sauvegarder(programmes) 
            conn.send("HTTP/1.1 303 See Other\nLocation: /\nConnection: close\n\n")

        # --- 7. 404 NOT FOUND ---
        else:
            conn.send("HTTP/1.1 404 Not Found\nConnection: close\n\n")

        # Close the connection once the request is fully handled
        conn.close()

    except OSError:
        # Expected behavior for non-blocking sockets when there is no incoming connection
        pass
    except Exception as e:
        # Prevents the server from crashing if malformed data is received
        print("Server error:", e)
        try:
            conn.close()
        except:
            pass
