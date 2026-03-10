import json

FICHIER = "programmes.json"

def charger():
    try:
        with open(FICHIER, "r") as f:
            return json.load(f)
    except:
        defaut = [
            {"id": 1, "nom": "Echauffement", "temps": 60},
            {"id": 2, "nom": "Force Max", "temps": 10}
        ]
        sauvegarder(defaut)
        return defaut

def sauvegarder(programmes):
    with open(FICHIER, "w") as f:
        json.dump(programmes, f)
