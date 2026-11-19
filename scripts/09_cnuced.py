# CNUCED (UNCTADstat) : escales et temps médian au port des PORTE-CONTENEURS, par pays, 2018-2023
# Sources (téléchargement BULK) :
#   - Port calls: Performance indicators - Annual  -> US_PortCalls.csv.7z        (temps médian)
#   - Port calls: Number of arrivals - Annual       -> US_PortCallsArrivals.csv.7z (nombre d'escales)
import os
import py7zr
import pandas as pd

# 1) Décompresser les deux archives .7z
os.makedirs("data/raw/cnuced", exist_ok=True)
for archive in ["data/raw/US_PortCalls.csv.7z", "data/raw/US_PortCallsArrivals.csv.7z"]:
    with py7zr.SevenZipFile(archive) as z:
        z.extractall("data/raw/cnuced")
print("Fichiers décompressés :", os.listdir("data/raw/cnuced"))

# 2) Lire les deux fichiers (les codes sont lus comme du texte pour garder les zéros : "03", "0000")
perf = pd.read_csv("data/raw/cnuced/US_PortCalls.csv",
                   dtype={"Economy": str, "CommercialMarket": str})
arr = pd.read_csv("data/raw/cnuced/US_PortCallsArrivals.csv",
                  dtype={"Economy": str, "CommercialMarket": str})

# 3) Pays retenus (code CNUCED -> nom en français)
#    Djibouti n'est PAS publié par la CNUCED : on ajoute l'Afrique de l'Est (sa région) pour les escales
PAYS = {
    "0000": "Monde",
    "842": "États-Unis",
    "702": "Singapour",
    "156": "Chine",
    "528": "Pays-Bas",
    "5121": "Afrique de l'Est (région de Djibouti)",
}
PORTE_CONTENEURS = "03"   # code CNUCED du type de navire "Container ships"

# 4) Garder les porte-conteneurs et les pays choisis
perf = perf[(perf["CommercialMarket"] == PORTE_CONTENEURS) & perf["Economy"].isin(PAYS)]
arr = arr[(arr["CommercialMarket"] == PORTE_CONTENEURS) & arr["Economy"].isin(PAYS)]

perf = perf[["Year", "Economy", "Median time in port (days)"]].rename(
    columns={"Median time in port (days)": "temps_median_jours"})
arr = arr[["Year", "Economy", "Number of port calls"]].rename(
    columns={"Number of port calls": "escales"})

# 5) Réunir les deux indicateurs (how="outer" : on garde un pays même s'il n'a qu'un indicateur)
cnuced = arr.merge(perf, on=["Year", "Economy"], how="outer")
cnuced["pays"] = cnuced["Economy"].map(PAYS)
cnuced = cnuced.rename(columns={"Year": "annee", "Economy": "code_cnuced"})
cnuced["temps_median_heures"] = (cnuced["temps_median_jours"] * 24).round(1)   # plus parlant
cnuced["temps_median_jours"] = cnuced["temps_median_jours"].round(2)
cnuced = cnuced[["pays", "code_cnuced", "annee", "escales",
                 "temps_median_jours", "temps_median_heures"]].sort_values(["pays", "annee"])

# 6) Contrôles
print("\nLignes :", len(cnuced), "| années :", sorted(cnuced["annee"].unique()))
manque = cnuced[cnuced["temps_median_jours"].isna()].groupby("pays")["annee"].apply(list)
print("Années sans temps médian (non publiées par la CNUCED) :")
print(manque.to_string())

cnuced.to_csv("data/clean/cnuced_pays.csv", index=False)
print("Fichier enregistré : data/clean/cnuced_pays.csv\n")

# 7) Comparaison 2022 -> 2023
recent = cnuced[cnuced["annee"].isin([2022, 2023])]
tab = recent.pivot(index="pays", columns="annee", values=["escales", "temps_median_jours"])
tab.columns = [f"{a}_{b}" for a, b in tab.columns]
print(tab.sort_values("temps_median_jours_2023").to_string())