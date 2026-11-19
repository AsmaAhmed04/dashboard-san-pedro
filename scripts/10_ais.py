# AIS en direct : navires autour de San Pedro Bay (Los Angeles + Long Beach)
# Source : aisstream.io (websocket) - https://aisstream.io/documentation
# Le script écoute pendant DUREE_ECOUTE secondes, puis enregistre un "instantané" dans data/live/.
# Le tableau de bord lit ce fichier : on n'ouvre PAS une connexion à chaque actualisation.
import asyncio
import json
import os
import time
from datetime import datetime, timezone

import pandas as pd
import websockets
from dotenv import load_dotenv

# ---------- Réglages ----------
URL = "wss://stream.aisstream.io/v0/stream"
DUREE_ECOUTE = 180     # secondes d'écoute (3 minutes)
DELAI_CONNEXION = 60   # secondes d'attente maximum pour ouvrir la connexion
DELAI_PING = 60        # secondes de tolérance pour le "ping" (connexion lente)
NB_ESSAIS = 3          # nombre d'essais si la connexion échoue

# Rectangle autour de San Pedro Bay : [coin 1 (lat, lon), coin 2 (lat, lon)]
# Il couvre les deux ports et la zone de mouillage au large de Long Beach.
ZONE = [[33.55, -118.40], [33.80, -118.05]]

DOSSIER = "data/live"
FICHIER_NAVIRES = f"{DOSSIER}/ais_navires.csv"
FICHIER_STATUT = f"{DOSSIER}/ais_statut.json"
FICHIER_FICHES = f"{DOSSIER}/ais_fiches_navires.csv"   # mémoire des fiches (nom, type) d'une écoute à l'autre

# Statut de navigation AIS (code -> texte)
STATUTS = {0: "en route", 1: "au mouillage", 2: "non manoeuvrant", 3: "manoeuvre restreinte",
           5: "à quai", 8: "en route (voile)", 15: "non défini"}


class ErreurCle(Exception):
    """Erreur renvoyée par aisstream.io (clé refusée...) : inutile de réessayer."""


def type_navire(code):
    """Traduit le code AIS du type de navire en grande famille."""
    if code is None:
        return "inconnu"
    if 70 <= code <= 79:
        return "cargo / porte-conteneurs"
    if 80 <= code <= 89:
        return "pétrolier / citerne"
    if 60 <= code <= 69:
        return "passagers"
    if code in (31, 32, 52):
        return "remorqueur"
    if code == 50:
        return "pilote"
    if code == 30:
        return "pêche"
    if code in (36, 37):
        return "plaisance"
    return "autre"


def statut_affiche(code, vitesse):
    """Statut lisible. Le statut AIS est saisi à la main par l'équipage :
    s'il n'est pas renseigné, on s'aide de la vitesse."""
    if code in (1, 5):
        return STATUTS[code]
    if code in (0, 8):
        return "en route" if (vitesse or 0) >= 0.5 else "à l'arrêt"
    return "à l'arrêt" if (vitesse or 0) < 0.5 else "en route"


def enregistrer_statut(ok, nb_messages, nb_navires, erreur=None):
    """Petit fichier lu par le tableau de bord pour afficher l'état de la source."""
    statut = {
        "ok": ok,
        "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "duree_ecoute_s": DUREE_ECOUTE,
        "nb_messages": nb_messages,
        "nb_navires": nb_navires,
        "erreur": erreur,
    }
    with open(FICHIER_STATUT, "w", encoding="utf-8") as f:
        json.dump(statut, f, ensure_ascii=False, indent=2)


def charger_fiches():
    """Relit les fiches (nom, type) déjà reçues lors des écoutes précédentes."""
    if not os.path.exists(FICHIER_FICHES):
        return {}
    anciennes = pd.read_csv(FICHIER_FICHES)
    return {int(r["mmsi"]): r.to_dict() for _, r in anciennes.iterrows()}


async def ecouter(cle, fiches):
    """Ouvre la connexion, s'abonne à la zone et collecte les messages pendant DUREE_ECOUTE.
    'fiches' contient déjà les fiches connues : on les complète avec les nouvelles."""
    positions = {}   # MMSI -> dernière position connue
    nb_messages = 0

    abonnement = {
        "APIKey": cle,
        "BoundingBoxes": [ZONE],
        "FilterMessageTypes": ["PositionReport", "ShipStaticData"],
    }

    # open_timeout : plus de temps pour ouvrir la connexion
    # ping_timeout : plus de tolérance quand la connexion est lente (évite l'erreur 1011)
    async with websockets.connect(URL, open_timeout=DELAI_CONNEXION, ping_timeout=DELAI_PING) as ws:
        print("  Connexion ouverte, écoute en cours...")
        await ws.send(json.dumps(abonnement))
        fin = asyncio.get_running_loop().time() + DUREE_ECOUTE

        while True:
            reste = fin - asyncio.get_running_loop().time()
            if reste <= 0:
                break
            try:
                brut = await asyncio.wait_for(ws.recv(), timeout=reste)
            except asyncio.TimeoutError:
                break

            msg = json.loads(brut)
            if "error" in msg:                     # ex. clé refusée
                raise ErreurCle(msg["error"])
            nb_messages += 1
            meta = msg.get("MetaData", {})
            mmsi = meta.get("MMSI")

            if msg.get("MessageType") == "PositionReport":
                p = msg["Message"]["PositionReport"]
                positions[mmsi] = {
                    "mmsi": mmsi,
                    "latitude": p.get("Latitude"),
                    "longitude": p.get("Longitude"),
                    "vitesse_noeuds": p.get("Sog"),
                    "cap": p.get("Cog"),
                    "statut_code": p.get("NavigationalStatus"),
                    "heure_utc": meta.get("time_utc"),
                    "nom_meta": (meta.get("ShipName") or "").strip(),
                }
            elif msg.get("MessageType") == "ShipStaticData":
                s = msg["Message"]["ShipStaticData"]
                fiches[mmsi] = {
                    "mmsi": mmsi,
                    "nom": (s.get("Name") or "").strip(),
                    "type_code": s.get("Type"),
                    "destination": (s.get("Destination") or "").strip(),
                }

            if nb_messages % 50 == 0:
                print(f"  {nb_messages} messages reçus, {len(positions)} navires positionnés...")

    return positions, nb_messages


def assembler(positions, fiches):
    """Relie positions et données statiques grâce au MMSI (comme un merge)."""
    pos = pd.DataFrame(positions.values())
    if pos.empty:
        return pos
    fic = pd.DataFrame(fiches.values()) if fiches else pd.DataFrame(
        columns=["mmsi", "nom", "type_code", "destination"])
    nav = pos.merge(fic, on="mmsi", how="left")          # "left" : on garde tous les navires positionnés
    nav["nom"] = nav["nom"].fillna("").where(nav["nom"].fillna("") != "", nav["nom_meta"])
    nav["type_code"] = pd.to_numeric(nav["type_code"], errors="coerce").astype("Int64")
    nav["type"] = [type_navire(None if pd.isna(c) else int(c)) for c in nav["type_code"]]
    nav["statut"] = [statut_affiche(c, v) for c, v in zip(nav["statut_code"], nav["vitesse_noeuds"])]
    return nav[["mmsi", "nom", "type", "type_code", "statut", "statut_code", "latitude", "longitude",
                "vitesse_noeuds", "cap", "destination", "heure_utc"]]


def main():
    os.makedirs(DOSSIER, exist_ok=True)

    # La clé est lue dans le fichier .env (jamais écrite dans le code)
    load_dotenv()
    cle = os.getenv("AISSTREAM_API_KEY")
    if not cle:
        print("ERREUR : clé AISSTREAM_API_KEY introuvable. Vérifie le fichier .env à la racine du projet.")
        enregistrer_statut(False, 0, 0, "clé API absente")
        return

    # Mémoire des fiches : les types de navires déjà reçus restent connus
    fiches = charger_fiches()
    print("Fiches de navires déjà connues :", len(fiches))

    # Plusieurs essais : le serveur gratuit est parfois lent à répondre
    resultat, derniere_erreur = None, None
    for essai in range(1, NB_ESSAIS + 1):
        print(f"Essai {essai}/{NB_ESSAIS} : connexion à aisstream.io (attente max {DELAI_CONNEXION} s)...")
        try:
            resultat = asyncio.run(ecouter(cle, fiches))
            break                                   # succès : on sort de la boucle
        except ErreurCle as erreur:
            print("ERREUR renvoyée par aisstream.io (vérifie ta clé) :", erreur)
            enregistrer_statut(False, 0, 0, f"aisstream.io : {erreur}")
            return
        except Exception as erreur:
            derniere_erreur = f"{type(erreur).__name__}: {erreur}"
            print("  Échec :", derniere_erreur)
            if essai < NB_ESSAIS:
                print("  Nouvel essai dans 15 s...")
                time.sleep(15)

    # On sauvegarde les fiches dans tous les cas (même un essai raté a pu en recevoir)
    if fiches:
        pd.DataFrame(fiches.values()).to_csv(FICHIER_FICHES, index=False)

    if resultat is None:
        # On ne remplace PAS l'ancien fichier de navires : le tableau de bord affichera
        # la dernière liste connue avec la mention "AIS indisponible"
        print("AIS indisponible après", NB_ESSAIS, "essais.")
        enregistrer_statut(False, 0, 0, derniere_erreur)
        return

    positions, nb_messages = resultat
    navires = assembler(positions, fiches)
    if navires.empty:
        print("Aucun navire reçu pendant l'écoute (couverture AIS faible ou zone vide).")
        enregistrer_statut(False, nb_messages, 0, "aucun navire reçu")
        return

    navires.to_csv(FICHIER_NAVIRES, index=False)
    enregistrer_statut(True, nb_messages, len(navires))

    print(f"\nMessages reçus : {nb_messages} | navires : {len(navires)}")
    print("Fiches de navires connues au total :", len(fiches))
    print("Navires dont le type est connu :", int((navires["type"] != "inconnu").sum()))
    print("\nRépartition par statut :")
    print(navires["statut"].value_counts().to_string())
    print("\nRépartition par type :")
    print(navires["type"].value_counts().to_string())
    print(f"\nFichiers enregistrés : {FICHIER_NAVIRES}, {FICHIER_STATUT} et {FICHIER_FICHES}")
    print(navires[["nom", "type", "statut", "vitesse_noeuds"]].head(8).to_string())


if __name__ == "__main__":
    main()