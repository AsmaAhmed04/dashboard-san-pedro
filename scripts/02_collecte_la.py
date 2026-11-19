# Collecte des volumes mensuels (EVP) du port de Los Angeles, 2019 -> 2026
# Source : https://portoflosangeles.org/business/statistics/container-statistics
import io
import os
import re
import time
import requests
import pandas as pd

ANNEES = range(2019, 2027)   # 2019, 2020, ..., 2026
URL = "https://portoflosangeles.org/business/statistics/Container-Statistics/Historical-TEU-Statistics-{annee}"
MOIS = {"January": 1, "February": 2, "March": 3, "April": 4, "May": 5, "June": 6,
        "July": 7, "August": 8, "September": 9, "October": 10, "November": 11, "December": 12}
COLONNES = ["Loaded Imports", "Empty Imports", "Loaded Exports", "Empty Exports", "Total TEUs"]
ANNEE_EN_COURS = 2026   # cette année n'est pas finie : on la retélécharge toujours


def nettoyer_nombre(valeur):
    """Convertit un texte en nombre, même s'il contient des erreurs de saisie.
    Exemple : '889.,748.15' -> 889748.15"""
    texte = re.sub(r"[^0-9.]", "", str(valeur))      # garde seulement chiffres et points
    if texte.count(".") > 1:                         # plusieurs points : seul le dernier est décimal
        partie_entiere, decimales = texte.rsplit(".", 1)
        texte = partie_entiere.replace(".", "") + "." + decimales
    try:
        return float(texte)
    except ValueError:
        return None


def obtenir_page(annee):
    """Renvoie le HTML de l'année : depuis le cache s'il existe, sinon depuis le site
    (3 essais maximum). Renvoie None si le site ne répond pas."""
    chemin = f"data/raw/la_{annee}.html"

    # 1) Cache : années terminées déjà téléchargées -> on relit le fichier
    if os.path.exists(chemin) and annee != ANNEE_EN_COURS:
        print(annee, "-> lu depuis le cache", chemin)
        with open(chemin, encoding="utf-8") as f:
            return f.read()

    # 2) Sinon on télécharge, avec 3 essais
    for essai in range(1, 4):
        try:
            rep = requests.get(URL.format(annee=annee),
                               headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
            print(annee, f"-> téléchargé (essai {essai}), code HTTP", rep.status_code)
            if rep.status_code == 200:
                with open(chemin, "w", encoding="utf-8") as f:
                    f.write(rep.text)
                return rep.text
        except requests.exceptions.RequestException as erreur:
            print(annee, f"-> essai {essai} échoué :", type(erreur).__name__)
        time.sleep(5 * essai)   # on attend 5 s, puis 10 s, puis 15 s

    # 3) Dernier recours : une ancienne copie, même pour l'année en cours
    if os.path.exists(chemin):
        print(annee, "-> site indisponible, on utilise l'ancienne copie du cache")
        with open(chemin, encoding="utf-8") as f:
            return f.read()
    return None


os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/clean", exist_ok=True)

morceaux = []

for annee in ANNEES:
    html = obtenir_page(annee)
    if html is None:
        print("   ⚠ année", annee, "indisponible : relance le script plus tard")
        continue

    # On prend le plus grand tableau de la page (c'est celui des données)
    t = max(pd.read_html(io.StringIO(html)), key=len)

    # La ligne 0 contient les noms des colonnes -> on s'en sert comme en-tête
    t.columns = ["mois"] + [str(c).strip() for c in t.iloc[0, 1:]]
    t = t.iloc[1:].copy()

    manquantes = [c for c in COLONNES if c not in t.columns]
    if manquantes:
        print("   colonnes manquantes :", manquantes, "| colonnes trouvées :", list(t.columns))
        continue

    # On garde seulement les 12 lignes de mois (on enlève les totaux annuels)
    t["mois"] = t["mois"].astype(str).str.strip()
    t = t[t["mois"].isin(MOIS.keys())].copy()

    # Conversion en nombres avec la fonction de nettoyage
    for col in COLONNES:
        t[col] = t[col].apply(nettoyer_nombre)
    t = t.dropna(subset=["Total TEUs"])   # mois pas encore publiés (fin 2026)

    # Une vraie date : le 1er du mois
    t["date"] = pd.to_datetime(pd.DataFrame({"year": annee,
                                             "month": t["mois"].map(MOIS),
                                             "day": 1}))
    print(f"   {len(t)} mois récupérés")
    morceaux.append(t)

# On assemble toutes les années et on garde les colonnes demandées par la prof
df = pd.concat(morceaux)
la = pd.DataFrame({
    "port": "Los Angeles",
    "date": df["date"],
    "imports_pleins": df["Loaded Imports"],
    "exports_pleins": df["Loaded Exports"],
    "vides": df["Empty Imports"] + df["Empty Exports"],   # vides = vides entrants + vides sortants
    "total": df["Total TEUs"],
}).sort_values("date")

# ===== NOUVEAU : correction des totaux faux dans la source =====
# Si le total publié ne correspond pas à la somme de ses composantes
# (cas de novembre 2020 : erreur de saisie sur le site), on recalcule le total
somme = la["imports_pleins"] + la["exports_pleins"] + la["vides"]
a_corriger = (somme - la["total"]).abs() > 1
print("\nMois corrigés :", la.loc[a_corriger, "date"].dt.strftime("%Y-%m").tolist())
la.loc[a_corriger, "total"] = somme[a_corriger]
# ===============================================================

# Contrôle 1 : imports + exports + vides doit être égal au total
ecart = (la["imports_pleins"] + la["exports_pleins"] + la["vides"] - la["total"]).abs()
print("Écart maximal entre la somme et le total :", round(ecart.max(), 2), "EVP")

# Contrôle 2 : la somme des mois de 2020 doit être égale au total annuel publié
somme_2020 = la.loc[la["date"].dt.year == 2020, "total"].sum()
print("Somme des mois 2020 :", round(somme_2020, 2), "| total annuel publié : 9213395.95")

# Contrôle 3 : il ne manque aucun mois
nb_attendu = len(pd.date_range(la["date"].min(), la["date"].max(), freq="MS"))
print("Nombre de mois :", len(la), "| attendu :", nb_attendu)

la.to_csv("data/clean/la_teu_mensuel.csv", index=False)
print("Fichier enregistré : data/clean/la_teu_mensuel.csv")
print(la[la["date"] == "2020-11-01"].to_string())