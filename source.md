# Journal des sources – Tableau de bord San Pedro Bay

## 1. Port of Los Angeles – volumes mensuels (EVP)
- Adresse : https://portoflosangeles.org/business/statistics/container-statistics
  (une page par année : .../Container-Statistics/Historical-TEU-Statistics-AAAA)
- Date de récupération : 18/11/2026
- Période : janvier 2019 à octobre 2026 (94 mois)
- Traitements :
  - vides = Empty Imports + Empty Exports
  - lignes de totaux annuels supprimées
  - novembre 2020 : erreur de saisie sur le site ("889.,748.15") ; total recalculé
    à partir des composantes (889 746,15), ce qui est confirmé par le total annuel publié
- Contrôles : 94 mois sur 94 ; somme des composantes = total ; somme 2020 = total annuel
- Scripts : 01_test_la.py, 02_collecte_la.py, 03_diagnostic_2020.py

## 2. Port of Long Beach – volumes mensuels (EVP)
- Site officiel (https://polb.com/business/port-statistics/) : inaccessible depuis Djibouti
  (erreur 403 avec Python, "Access Denied" dans le navigateur), essayé le 18/11/2026.
- Source utilisée : Bureau of Transportation Statistics, "Supply Chain and Freight Indicators"
  - Adresse : https://www.bts.gov/freight-indicators (export CSV)
  - Données mises à jour le 17/11/2026 ; récupérées le 19/11/2026
  - Indicateurs : Loaded Import / Loaded Export / Empty Export Containers (TEUs), port "Long Beach"
- Source de contrôle : BTS "Monthly TEU Data"
  (https://data.transportation.gov/api/views/rd72-aq8r/rows.csv), total par port, 2019 à oct. 2022
- Période : janvier 2019 à septembre 2026 (93 mois)
- Traitements :
  - format long -> format large (une colonne par indicateur)
  - vides = vides exportés seulement (vides importés non publiés par le BTS)
  - total = imports pleins + exports pleins + vides exportés
  - janvier 2019 : exportations corrigées (131 436 -> 117 838, chiffre annoncé par le port)
- Contrôles :
  - pour Los Angeles, chiffres BTS identiques au site du port (0,00 % d'écart sur 93 mois)
  - pour Long Beach, total recalculé inférieur de 1,85 % en moyenne au total officiel (46 mois)
- Limite : total de Long Beach légèrement sous-estimé (vides importés manquants)
- Scripts : 04_test_lb.py, 05_explorer_bts.py, 06_verifier_bts.py, 07_collecte_lb.py
## 3. Container Port Performance Index (CPPI) – Banque mondiale / S&P Global
- Édition 2025 (6e édition, publiée le 10/06/2026) :
  - Page : https://www.worldbank.org/en/topic/transport/publication/cppi
  - Fichier "Annex: CPPI 2020-2025" :
    https://openknowledge.worldbank.org/bitstreams/9cf20807-7dcd-4de7-9de2-fdb2d0589a73/download
- Édition 2024 (5e édition, publiée le 23/09/2025) :
  - Page : https://www.worldbank.org/en/topic/transport/publication/cppi-2024
  - Fichier "Data" :
    https://openknowledge.worldbank.org/bitstreams/6d1086f0-13ed-4d69-92ad-11d93f3e7df6/download
- Date de récupération : 19/11/2026
- Ports retenus (code UN/LOCODE) : Los Angeles (USLAX), Long Beach (USLGB), Djibouti (DJJIB),
  Singapour (SGSIN), Salalah (OMSLL), Tanger Med (MAPTM)
- Traitements :
  - harmonisation des colonnes entre éditions (Rank / Rank 2025, LOCODE / UN/LOCODE)
  - ports repérés par leur code UN/LOCODE (le nom de Tanger change entre les éditions)
  - score arrondi à 0,1
- Contrôles : 6 ports présents dans les 2 éditions ; scores 2024 identiques dans les 2 fichiers
- Lecture : score 0 = port médian ; score négatif = navires plus longtemps au port que la médiane
- Nombre de ports classés : 403 (2024) et 400 (2025)
- Script : 08_cppi.py
## 4. CNUCED (UNCTADstat) – escales et temps médian au port, par pays
- Tableau 1 : "Port calls: Performance indicators - Annual" (temps médian au port)
  - Page : https://unctadstat.unctad.org/datacentre/dataviewer/US.PortCalls
  - Fichier BULK "From 2018 to 2023" : https://unctadstat-api.unctad.org/bulkdownload/US.PortCalls/US_PortCalls
  
  - Dernière mise à jour par la CNUCED : 28/03/2024
- Tableau 2 : "Port calls: Number of arrivals - Annual" (nombre d'escales)
  - Page : http://stats.unctad.org/portcalls_number_a
  - Fichier BULK "From 2018 to 2023" : https://unctadstat-api.unctad.org/bulkdownload/US.PortCallsArrivals/US_PortCallsArrivals
- Date de récupération : 19/11/2026
- Période : 2018 à 2023 (dernière année publiée)
- Type de navire retenu : porte-conteneurs (code CNUCED "03"), pour rester cohérent
  avec les EVP et le CPPI
- Pays retenus : États-Unis, Singapour, Chine, Pays-Bas, Monde (référence)
  + Afrique de l'Est (région de Djibouti) pour le nombre d'escales seulement
- Traitements :
  - décompression des archives .7z avec Python (py7zr)
  - codes lus comme du texte pour garder les zéros ("0000", "03")
  - fusion des deux tableaux par année et par pays (jointure "outer")
  - conversion du temps médian en heures (jours x 24)
- Limites :
  - Djibouti n'est PAS publié par la CNUCED (ni dans les 2 tableaux, ni dans la fiche
    pays maritime ; vérifié le 19/11/2026). Djibouti est comparé avec le CPPI.
  - Le tableau des temps médians ne couvre que 23 pays.
  - Chiffres par PAYS : "États-Unis" = tous les ports américains, pas seulement San Pedro Bay.
  - Singapour : temps médian non publié de 2018 à 2021 ("Not publishable").
  - Données arrêtées en 2023, alors que le CPPI va jusqu'en 2025.
- Script : 09_cnuced.py
## 5. AIS en direct – navires autour de San Pedro Bay
- Source : aisstream.io (flux websocket gratuit, avec clé API)
  - Site : https://aisstream.io
  - Documentation : https://aisstream.io/documentation
  - Adresse du flux : wss://stream.aisstream.io/v0/stream
- Clé API : stockée dans le fichier .env (non rendu, protégé par .gitignore) ;
  modèle sans clé : .env.exemple
- Zone écoutée : rectangle de 33,55° N / -118,40° E à 33,80° N / -118,05° E
  (ports de Los Angeles et Long Beach + zone de mouillage)
- Messages utilisés : PositionReport (position, vitesse, cap, statut)
  et ShipStaticData (nom, type, destination)
- Premier instantané : 19/11/2026 vers 09:54 UTC (45 navires, dont 7 au mouillage et 12 à quai)
- Fréquence prévue : une écoute de 3 minutes, relancée au maximum toutes les 15 minutes
  (pas de connexion à chaque actualisation du tableau de bord)
- Traitements :
  - jointure position + fiche statique par le numéro MMSI
  - mémoire des fiches d'une écoute à l'autre (data/live/ais_fiches_navires.csv),
    car les fiches n'arrivent qu'environ toutes les 6 minutes
  - traduction des codes AIS : type (70-79 = cargo / porte-conteneurs…)
    et statut (1 = au mouillage, 5 = à quai…)
  - si le statut n'est pas renseigné : vitesse < 0,5 nœud = « à l'arrêt »
- Gestion des erreurs :
  - 3 essais de connexion, délai de 60 s (réseau lent depuis Djibouti)
  - en cas d'échec, l'ancien instantané est conservé et l'erreur est notée
    dans data/live/ais_statut.json (message « AIS indisponible » dans le tableau de bord)
  - clé invalide : le serveur ferme la connexion sans message ; le script 10b_diagnostic_ais.py
    vérifie la clé sans l'afficher
- Limites :
  - couverture gratuite incomplète (antennes terrestres bénévoles)
  - statut de navigation saisi à la main par l'équipage, parfois faux ou non mis à jour
  - type de navire souvent inconnu lors des premières écoutes
  - le type AIS 70-79 regroupe tous les cargos (pas seulement les porte-conteneurs)
- Scripts : 10_ais.py, 10b_diagnostic_ais.py

## 6. Météo – Open-Meteo
- Source : Open-Meteo (gratuit, sans clé API)
  - Vent et rafales : https://api.open-meteo.com/v1/forecast
    (documentation : https://open-meteo.com/en/docs)
  - Vagues : https://marine-api.open-meteo.com/v1/marine
    (documentation : https://open-meteo.com/en/docs/marine-weather-api)
- Point : 33,71° N / -118,21° O (avant-port de Los Angeles / Long Beach, en mer pour avoir les vagues)
- Première récupération : 19/11/2026, 02:15 heure du port (10:15 UTC)
- Variables : vent et rafales à 10 m (km/h), direction du vent, hauteur et période des vagues
- Horizon : situation actuelle + prévisions heure par heure sur 48 h (heure locale de Los Angeles)
- Cache : pas de nouvel appel si les données ont moins de 60 minutes
- Seuils d'alerte :
  - alerte : rafales >= 72 km/h (≈ 45 mph, arrêt des portiques observé au port de Felixstowe)
  - vigilance : rafales >= 50 km/h (marge choisie sous le seuil d'arrêt) ou vagues >= 2 m
  - le seuil de vagues est une hypothèse personnelle, à valider avec la capitainerie
- Gestion des erreurs : 3 essais par appel ; en cas d'échec, anciens fichiers conservés
  et erreur notée dans data/live/meteo_statut.json
- Limites :
  - prévision issue d'un modèle numérique, pas d'une mesure sur place
  - un seul point de mesure pour tout le complexe portuaire
  - seuils non officiels (les vraies limites dépendent des portiques et du port)
- Script : 12_meteo.py