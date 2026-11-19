# Vérifier la fiabilité du fichier BTS avant de l'utiliser pour Long Beach
import pandas as pd

# ---------- 1) Lire les 3 indicateurs conteneurs du BTS ----------
df = pd.read_csv("data/raw/bts_supply_chain.csv")
INDIC = {
    "Loaded Import Containers at Select U.S. Ports in TEUs": "imports_pleins",
    "Loaded Export Containers at Select U.S. Ports in TEUs": "exports_pleins",
    "Empty Export Containers at Select U.S. Ports in TEUs": "vides_exportes",
}
sous = df[df["INDICATOR"].isin(INDIC.keys())
          & df["MEASURE1"].isin(["Long Beach", "Los Angeles"])].copy()

sous["date"] = pd.to_datetime(sous["DATE"], format="%Y %b %d %I:%M:%S %p")
sous["valeur"] = pd.to_numeric(sous["VALUE1"].astype(str).str.replace(",", ""), errors="coerce")
sous["variable"] = sous["INDICATOR"].map(INDIC)

# Format "long" -> format "large" : une colonne par indicateur
large = sous.pivot_table(index=["MEASURE1", "date"], columns="variable",
                         values="valeur").reset_index()

# ---------- 2) Test sur LOS ANGELES : BTS contre chiffres officiels du port ----------
la_port = pd.read_csv("data/clean/la_teu_mensuel.csv", parse_dates=["date"])
la_bts = large[large["MEASURE1"] == "Los Angeles"]
c = la_bts.merge(la_port, on="date", suffixes=("_bts", "_port"))

print("===== TEST 1 : Los Angeles, BTS vs port officiel =====")
print("Mois comparés :", len(c))
for col in ["imports_pleins", "exports_pleins"]:
    ecart = (c[f"{col}_bts"] - c[f"{col}_port"]).abs() / c[f"{col}_port"] * 100
    print(f"{col} : écart moyen {ecart.mean():.2f} % | écart max {ecart.max():.2f} %")

# ---------- 3) Test sur LONG BEACH : somme BTS contre total officiel (2019 - oct. 2022) ----------
lb = large[large["MEASURE1"] == "Long Beach"].copy()
lb["somme_bts"] = lb["imports_pleins"] + lb["exports_pleins"] + lb["vides_exportes"]

# Ce fichier a été enregistré par Excel en français : séparateur = point-virgule
tot = pd.read_csv("data/raw/bts_monthly_teu.csv", sep=";")
print("\nColonnes du fichier des totaux :", list(tot.columns))

col_date = tot.columns[0]                                         # 1re colonne = les dates
col_lb = [c for c in tot.columns if "Long Beach" in c][0]          # colonne qui contient "Long Beach"

tot["date"] = (pd.to_datetime(tot[col_date], format="%m/%d/%Y")    # dates au format mois/jour/année
                 .dt.to_period("M").dt.to_timestamp())             # ramène au 1er du mois
tot["total_officiel"] = pd.to_numeric(tot[col_lb].astype(str).str.replace(",", ""),
                                      errors="coerce")

comp = lb.merge(tot[["date", "total_officiel"]], on="date")
comp["ecart_pct"] = (comp["total_officiel"] - comp["somme_bts"]) / comp["total_officiel"] * 100

print("\n===== TEST 2 : Long Beach, somme BTS vs total officiel =====")
print("Mois comparés :", len(comp))
print("Écart moyen :", round(comp["ecart_pct"].mean(), 2), "%")
print("Écart minimum :", round(comp["ecart_pct"].min(), 2), "% | maximum :",
      round(comp["ecart_pct"].max(), 2), "%")
print("Nombre de mois où la somme DÉPASSE le total (impossible) :", (comp["ecart_pct"] < 0).sum())
print(comp[["date", "imports_pleins", "exports_pleins", "vides_exportes",
            "somme_bts", "total_officiel", "ecart_pct"]].head(6).to_string())