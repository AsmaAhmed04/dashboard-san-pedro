# Diagnostic de la connexion aisstream.io (n'affiche JAMAIS la clé)
import asyncio
import json
import os
import time

import websockets
from dotenv import load_dotenv

load_dotenv()
cle = os.getenv("AISSTREAM_API_KEY")

# 1) Vérifier la clé sans l'afficher
print("Clé trouvée :", cle is not None)
if cle:
    print("Longueur de la clé :", len(cle), "caractères (une clé aisstream fait environ 40)")
    print("Espaces au début ou à la fin :", cle != cle.strip())
    print("Guillemets dans la clé :", ('"' in cle) or ("'" in cle))
    print("Espace au milieu :", " " in cle.strip())


async def tester():
    abonnement = {
        "APIKey": cle.strip().strip('"').strip("'") if cle else "",
        "BoundingBoxes": [[[33.55, -118.40], [33.80, -118.05]]],
    }
    debut = time.time()
    async with websockets.connect("wss://stream.aisstream.io/v0/stream", open_timeout=60) as ws:
        print(f"\nConnexion ouverte après {time.time() - debut:.1f} s")
        await ws.send(json.dumps(abonnement))
        print("Abonnement envoyé, écoute 30 s...")
        nb = 0
        try:
            while time.time() - debut < 30:
                brut = await asyncio.wait_for(ws.recv(), timeout=30)
                msg = json.loads(brut)
                nb += 1
                if nb <= 5:   # on montre les 5 premiers messages
                    print(f"  [{time.time() - debut:.1f} s] message :", msg.get("MessageType"), "|",
                          msg.get("error", msg.get("MetaData", {}).get("ShipName", "")))
        except asyncio.TimeoutError:
            print("  Aucun message pendant 30 s")
        except websockets.ConnectionClosed as e:
            print(f"  Connexion fermée par le serveur après {time.time() - debut:.1f} s")
            print("  Code de fermeture :", e.rcvd.code if e.rcvd else "aucun",
                  "| raison :", e.rcvd.reason if e.rcvd else "aucune")
        print("Messages reçus :", nb)

asyncio.run(tester())