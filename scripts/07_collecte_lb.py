# Collecte des volumes mensuels (EVP) du port de Long Beach, 2019 -> 2026
# Source : BTS "Supply Chain and Freight Indicators" (data.bts.gov), car polb.com est inaccessible
import pandas as pd

INDIC = {
    "Loaded Import Containers at Select U.S. Ports in TEUs": "imports_pleins",
    "Loaded Export Containers at Select U.S. Ports in TEUs": "exports_pleins",
    "Empty Export Containers at Select U.S. Ports in TEUs": "vides",   # vides EXPORTÉS seulement
}

# 1) Lire le fichier BTS et garder Long Beach + les 3 indicateurs
df = pd.read_csv("data/raw/bts_supply_chain.csv")
sous = df[df["INDICATOR"].isin(INDIC.keys()) & (df["MEASURE1"] == "Long Beach")].copy()

# 2) Nettoyer la date et la valeur
sous["date"] = pd.to_datetime(sous["DATE"], format="%Y %b %d %I:%M:%S %p")
sous["valeur"] = pd.to_numeric(sous["VALUE1"].astype(str).str.replace(",", ""), errors="coerce")
sous["variable"] = sous["INDICATOR"].map(INDIC)

# 3) Format long -> format large (une colonne par indicateur)
lb = sous.pivot_table(index="date", columns="variable", values="valeur").reset_index()
lb.columns.name = None

# 4) Correction de janvier 2019 : exportations fausses dans le BTS
#    Valeur du port : 117 838 EVP (communiqué du port, repris par FreightWaves)
print("Exportations janv. 2019 avant correction :",
      lb.loc[lb["date"] == "2019-01-01", "exports_pleins"].values)
lb.loc[lb["date"] == "2019-01-01", "exports_pleins"] = 117838

# 5) Total = imports + exports + vides exportés (vides importés non disponibles)
lb["total"] = lb["imports_pleins"] + lb["exports_pleins"] + lb["vides"]
lb["port"] = "Long Beach"

# 6) Même ordre de colonnes que le fichier de Los Angeles
lb = lb[["port", "date", "imports_pleins", "exports_pleins", "vides", "total"]].sort_values("date")

# 7) Contrôles
nb_attendu = len(pd.date_range(lb["date"].min(), lb["date"].max(), freq="MS"))
print("Nombre de mois :", len(lb), "| attendu :", nb_attendu)
print("Valeurs manquantes :", int(lb.isna().sum().sum()))
print("Période :", lb["date"].min().date(), "->", lb["date"].max().date())

lb.to_csv("data/clean/lb_teu_mensuel.csv", index=False)
print("Fichier enregistré : data/clean/lb_teu_mensuel.csv")

# 8) Fichier commun San Pedro Bay (LA + LB), utile pour le tableau de bord
la = pd.read_csv("data/clean/la_teu_mensuel.csv", parse_dates=["date"])
san_pedro = pd.concat([la, lb], ignore_index=True)
san_pedro.to_csv("data/clean/san_pedro_teu_mensuel.csv", index=False)
print("Fichier commun enregistré : data/clean/san_pedro_teu_mensuel.csv",
      "(", len(san_pedro), "lignes )")
print(lb.head(3).to_string())
print(lb.tail(3).to_string())