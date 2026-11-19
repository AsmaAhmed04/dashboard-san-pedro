# Explorer le fichier BTS : comment sont rangés les ports pour les 3 indicateurs conteneurs ?
import pandas as pd

df = pd.read_csv("data/raw/bts_supply_chain.csv")

INDICATEURS = [
    "Loaded Import Containers at Select U.S. Ports in TEUs",
    "Loaded Export Containers at Select U.S. Ports in TEUs",
    "Empty Export Containers at Select U.S. Ports in TEUs",
]

for ind in INDICATEURS:
    sous = df[df["INDICATOR"] == ind]
    print("\n==========", ind, "==========")
    print("Nombre de lignes :", len(sous))
    print("Valeurs de MEASURE1 :", sous["MEASURE1"].dropna().unique()[:20])
    print("Valeurs de MEASURE2 :", sous["MEASURE2"].dropna().unique()[:20])
    print("Première date :", sous["DATE"].iloc[0], "| dernière date :", sous["DATE"].iloc[-1])
    print(sous[["DATE", "MEASURE1", "MEASURE2", "VALUE1", "UNITS"]].head(3).to_string())