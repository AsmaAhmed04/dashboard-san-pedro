# CPPI (Banque mondiale / S&P Global) : score et rang de 6 ports sur 2 éditions (2024 et 2025)
# Sources :
#   2025 : https://openknowledge.worldbank.org/bitstreams/9cf20807-7dcd-4de7-9de2-fdb2d0589a73/download
#   2024 : https://openknowledge.worldbank.org/bitstreams/6d1086f0-13ed-4d69-92ad-11d93f3e7df6/download
import pandas as pd

# Les 6 ports choisis, repérés par leur code UN/LOCODE
# (le code ne change pas, alors que le nom peut changer : "Tanger-Mediterranean" -> "Tanger Med")
PORTS = {
    "USLAX": "Los Angeles",
    "USLGB": "Long Beach",
    "DJJIB": "Djibouti",
    "SGSIN": "Singapour",
    "OMSLL": "Salalah",
    "MAPTM": "Tanger Med",
}

# ---------- 1) Édition 2024 ----------
e24 = pd.read_excel("data/raw/cppi_2024.xlsx")
e24 = e24.rename(columns={"LOCODE": "locode", "CPPI 2024": "score", "Rank": "rang"})
e24 = e24[e24["locode"].isin(PORTS)][["locode", "score", "rang"]]
e24["edition"] = 2024
nb_ports_2024 = int(pd.read_excel("data/raw/cppi_2024.xlsx")["Rank"].notna().sum())   # ports ayant un rang

# ---------- 2) Édition 2025 ----------
e25 = pd.read_excel("data/raw/cppi_2025.xlsx")
e25 = e25.rename(columns={"UN/LOCODE": "locode", "CPPI 2025": "score", "Rank 2025": "rang"})
e25 = e25[e25["locode"].isin(PORTS)][["locode", "score", "rang"]]
e25["edition"] = 2025
nb_ports_2025 = int(pd.read_excel("data/raw/cppi_2025.xlsx")["Rank 2025"].notna().sum())   # ports ayant un rang

# ---------- 3) On empile les deux éditions (format long) ----------
cppi = pd.concat([e24, e25], ignore_index=True)
cppi["port"] = cppi["locode"].map(PORTS)
cppi["score"] = cppi["score"].round(1)
cppi["rang"] = cppi["rang"].astype(int)
cppi["nb_ports_classes"] = cppi["edition"].map({2024: nb_ports_2024, 2025: nb_ports_2025})
cppi = cppi[["port", "locode", "edition", "score", "rang", "nb_ports_classes"]]

# ---------- 4) Contrôle : chaque port doit apparaître dans les 2 éditions ----------
print("Lignes trouvées :", len(cppi), "| attendu :", len(PORTS) * 2)
print("Ports classés : 2024 =", nb_ports_2024, "| 2025 =", nb_ports_2025)

cppi.to_csv("data/clean/cppi_ports.csv", index=False)
print("Fichier enregistré : data/clean/cppi_ports.csv\n")

# Contrôle 2 : le score 2024 recopié dans l'édition 2025 est-il le même que dans l'édition 2024 ?
brut24 = pd.read_excel("data/raw/cppi_2024.xlsx").set_index("LOCODE")["CPPI 2024"]
brut25 = pd.read_excel("data/raw/cppi_2025.xlsx").set_index("UN/LOCODE")["CPPI 2024"]
identiques = all(abs(brut24[c] - brut25[c]) < 0.5 for c in PORTS)
print("Scores 2024 identiques dans les deux éditions :", identiques)

# ---------- 5) Tableau de comparaison (format large) ----------
large = cppi.pivot(index="port", columns="edition", values=["score", "rang"])
large.columns = [f"{a}_{b}" for a, b in large.columns]
large["evolution_rang"] = large["rang_2024"] - large["rang_2025"]   # positif = le port a gagné des places
print(large.sort_values("rang_2025").to_string())