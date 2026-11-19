# Test 2 : la page de Long Beach accepte-t-elle une requête "comme un navigateur" ?
import os
import requests

url = "https://polb.com/business/port-statistics/"

# En-têtes envoyés habituellement par Chrome
entetes = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,fr;q=0.8",
}

reponse = requests.get(url, headers=entetes, timeout=60)
print("Code HTTP :", reponse.status_code)

os.makedirs("data/raw", exist_ok=True)
with open("data/raw/lb_page_statistiques.html", "w", encoding="utf-8") as f:
    f.write(reponse.text)

for mot in ["Loaded Inbound", "Empties Outbound", "TEU", "January"]:
    print(f"'{mot}' présent :", mot in reponse.text)