# Météo du port de San Pedro Bay : vent, rafales et vagues, actuels et prévus (48 h)
# Source : Open-Meteo (gratuit, sans clé API)
#   - vent et rafales : https://open-meteo.com/en/docs              (API "forecast")
#   - vagues          : https://open-meteo.com/en/docs/marine-weather-api (API "marine")
# Cache : si les données ont moins de 60 minutes, on ne rappelle PAS l'API.
import json
import os
import time
from datetime import datetime, timezone

import pandas as pd
import requests

# ---------- Réglages ----------
# Point de mesure : avant-port de Long Beach / Los Angeles (en mer, pour avoir les vagues)
LATITUDE, LONGITUDE = 33.71, -118.21
FUSEAU = "America/Los_Angeles"   # heures affichées à l'heure locale du port
HEURES_PREVISION = 48
CACHE_MINUTES = 60

# Seuils d'alerte (voir fiche de conception)
RAFALES_VIGILANCE = 50   # km/h : marge choisie sous le seuil d'arrêt
RAFALES_ALERTE = 72      # km/h (≈ 45 mph) : arrêt des portiques observé à Felixstowe
VAGUES_VIGILANCE = 2.0   # m : seuil indicatif (hypothèse à valider)

URL_VENT = "https://api.open-meteo.com/v1/forecast"
URL_MER = "https://marine-api.open-meteo.com/v1/marine"

DOSSIER = "data/live"
FICHIER_HORAIRE = f"{DOSSIER}/meteo_horaire.csv"
FICHIER_ACTUEL = f"{DOSSIER}/meteo_actuelle.json"
FICHIER_STATUT = f"{DOSSIER}/meteo_statut.json"


def cache_recent():
    """Vrai si la dernière récupération réussie date de moins de CACHE_MINUTES."""
    if not (os.path.exists(FICHIER_STATUT) and os.path.exists(FICHIER_HORAIRE)):
        return False
    with open(FICHIER_STATUT, encoding="utf-8") as f:
        statut = json.load(f)
    if not statut.get("ok"):
        return False
    age_min = (time.time() - os.path.getmtime(FICHIER_HORAIRE)) / 60
    print(f"Données météo en cache : {age_min:.0f} min")
    return age_min < CACHE_MINUTES


def appeler(url, params, essais=3):
    """Appelle une API Open-Meteo avec 3 essais (réseau parfois lent)."""
    for essai in range(1, essais + 1):
        try:
            rep = requests.get(url, params=params, timeout=30)
            rep.raise_for_status()
            return rep.json()
        except requests.exceptions.RequestException as erreur:
            print(f"  Essai {essai}/{essais} échoué : {type(erreur).__name__}")
            if essai < essais:
                time.sleep(5 * essai)
    raise ConnectionError(f"API indisponible : {url}")


def niveau(rafales, vagues):
    """Niveau d'alerte d'une heure donnée : 'alerte', 'vigilance' ou 'normal'."""
    if rafales is not None and rafales >= RAFALES_ALERTE:
        return "alerte"
    if (rafales is not None and rafales >= RAFALES_VIGILANCE) or \
       (vagues is not None and vagues >= VAGUES_VIGILANCE):
        return "vigilance"
    return "normal"


def traiter(vent, mer):
    """Transforme les deux réponses JSON en un tableau horaire + un résumé 'actuel'."""
    # 1) Tableau horaire : une ligne par heure, vent + vagues réunis sur l'heure
    h_vent = pd.DataFrame(vent["hourly"])
    h_mer = pd.DataFrame(mer["hourly"])
    horaire = h_vent.merge(h_mer, on="time", how="left")
    horaire = horaire.rename(columns={
        "time": "heure_locale",
        "wind_speed_10m": "vent_kmh",
        "wind_gusts_10m": "rafales_kmh",
        "wind_direction_10m": "direction_vent_deg",
        "wave_height": "vagues_m",
        "wave_period": "periode_vagues_s",
    })
    horaire["heure_locale"] = pd.to_datetime(horaire["heure_locale"])

    # On garde les 48 prochaines heures à partir de l'heure actuelle du port
    maintenant = pd.to_datetime(vent["current"]["time"]).floor("h")
    horaire = horaire[horaire["heure_locale"] >= maintenant].head(HEURES_PREVISION).copy()
    horaire["niveau"] = [niveau(r, v) for r, v in zip(horaire["rafales_kmh"], horaire["vagues_m"])]

    # 2) Situation actuelle
    actuel = {
        "heure_locale": vent["current"]["time"],
        "vent_kmh": vent["current"].get("wind_speed_10m"),
        "rafales_kmh": vent["current"].get("wind_gusts_10m"),
        "direction_vent_deg": vent["current"].get("wind_direction_10m"),
        "vagues_m": mer.get("current", {}).get("wave_height"),
    }
    actuel["niveau"] = niveau(actuel["rafales_kmh"], actuel["vagues_m"])

    # 3) Résumé des 48 h : pire moment et premières heures à risque
    pire = horaire.loc[horaire["rafales_kmh"].idxmax()]
    risques = horaire[horaire["niveau"] != "normal"]
    actuel["rafales_max_48h_kmh"] = float(pire["rafales_kmh"])
    actuel["heure_rafales_max"] = pire["heure_locale"].strftime("%Y-%m-%d %H:%M")
    actuel["vagues_max_48h_m"] = float(horaire["vagues_m"].max())
    actuel["niveau_48h"] = ("alerte" if (horaire["niveau"] == "alerte").any()
                            else "vigilance" if not risques.empty else "normal")
    actuel["debut_risque"] = (risques["heure_locale"].min().strftime("%Y-%m-%d %H:%M")
                              if not risques.empty else None)
    actuel["fin_risque"] = (risques["heure_locale"].max().strftime("%Y-%m-%d %H:%M")
                            if not risques.empty else None)
    return horaire, actuel


def enregistrer_statut(ok, erreur=None):
    statut = {"ok": ok, "date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
              "erreur": erreur}
    with open(FICHIER_STATUT, "w", encoding="utf-8") as f:
        json.dump(statut, f, ensure_ascii=False, indent=2)


def main():
    os.makedirs(DOSSIER, exist_ok=True)

    if cache_recent():
        print("Cache encore valide : pas d'appel à l'API (relance dans moins d'une heure).")
        return

    commun = {"latitude": LATITUDE, "longitude": LONGITUDE, "timezone": FUSEAU, "forecast_days": 3}
    params_vent = {**commun, "wind_speed_unit": "kmh",
                   "current": "wind_speed_10m,wind_gusts_10m,wind_direction_10m",
                   "hourly": "wind_speed_10m,wind_gusts_10m,wind_direction_10m"}
    params_mer = {**commun, "current": "wave_height",
                  "hourly": "wave_height,wave_period"}

    try:
        print("Appel Open-Meteo (vent)...")
        vent = appeler(URL_VENT, params_vent)
        print("Appel Open-Meteo (vagues)...")
        mer = appeler(URL_MER, params_mer)
        horaire, actuel = traiter(vent, mer)
    except Exception as erreur:
        # On garde les anciens fichiers : le tableau de bord affichera "météo indisponible"
        print("ERREUR météo :", erreur)
        enregistrer_statut(False, str(erreur))
        return

    horaire.to_csv(FICHIER_HORAIRE, index=False)
    with open(FICHIER_ACTUEL, "w", encoding="utf-8") as f:
        json.dump(actuel, f, ensure_ascii=False, indent=2)
    enregistrer_statut(True)

    print(f"\nMaintenant ({actuel['heure_locale']}, heure du port) : vent {actuel['vent_kmh']} km/h, "
          f"rafales {actuel['rafales_kmh']} km/h, vagues {actuel['vagues_m']} m -> {actuel['niveau']}")
    print(f"Sur 48 h : rafales max {actuel['rafales_max_48h_kmh']} km/h ({actuel['heure_rafales_max']}), "
          f"vagues max {actuel['vagues_max_48h_m']} m -> niveau {actuel['niveau_48h']}")
    if actuel["debut_risque"]:
        print(f"Période à surveiller : du {actuel['debut_risque']} au {actuel['fin_risque']}")
    print("\nRépartition des 48 heures :")
    print(horaire["niveau"].value_counts().to_string())
    print(f"\nFichiers enregistrés : {FICHIER_HORAIRE}, {FICHIER_ACTUEL}, {FICHIER_STATUT}")


if __name__ == "__main__":
    main()