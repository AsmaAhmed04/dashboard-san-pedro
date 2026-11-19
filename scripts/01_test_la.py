# Test : lire le tableau 2019 du port de Los Angeles (diagnostic)
import io
import os
import requests
import pandas as pd

url = "https://portoflosangeles.org/business/statistics/Container-Statistics/Historical-TEU-Statistics-2019"

# Certains sites refusent les requêtes sans "User-Agent" : on se présente comme un navigateur
reponse = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
print("Code HTTP :", reponse.status_code)   # 200 = OK

# 1) On garde une copie brute de la page (donnée "raw")
os.makedirs("data/raw", exist_ok=True)      # crée le dossier s'il n'existe pas
with open("data/raw/la_2019.html", "w", encoding="utf-8") as f:
    f.write(reponse.text)
print("Copie enregistrée dans data/raw/la_2019.html")

# 2) Le mot "January" est-il dans la page ? Si non, les chiffres sont chargés autrement
print("'January' présent dans la page :", "January" in reponse.text)

# 3) On affiche chaque tableau trouvé
tableaux = pd.read_html(io.StringIO(reponse.text))
print("Nombre de tableaux trouvés :", len(tableaux))
for i, t in enumerate(tableaux):
    print(f"\n===== Tableau {i} : {t.shape[0]} lignes x {t.shape[1]} colonnes =====")
    print(t.head(15).to_string())