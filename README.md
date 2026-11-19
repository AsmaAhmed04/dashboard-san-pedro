# Tableau de bord San Pedro Bay (Los Angeles + Long Beach) face au monde

**Asma** – Master IAMD, Université de Djibouti
IA sectorielle – secteur portuaire, Séquence 6 (Tableaux de bord intelligents et aide à la décision)
Exercice individuel et facultatif – novembre 2026

---

## 1. Présentation

J'ai construit un tableau de bord avec **Streamlit (Python)** qui montre comment se porte le complexe portuaire de **San Pedro Bay** (ports de Los Angeles et de Long Beach) et comment il se situe face aux autres ports du monde, dont **Djibouti**.

J'ai suivi la méthode du cours : j'ai d'abord rempli la **fiche de conception** (utilisateur, décision, indicateurs, références, fréquence), puis j'ai cherché les données, et seulement à la fin j'ai construit l'écran.

- **Pour qui ?** Le responsable de la planification des escales d'une compagnie maritime qui passe par San Pedro Bay et par Djibouti (niveau tactique).
- **Pour quelle décision ?** Pour les navires des deux prochaines semaines : choisir entre Los Angeles et Long Beach, et décider s'il faut changer l'heure d'arrivée (ralentir pour arriver juste-à-temps, ou attendre si le vent est trop fort).
- **Niveau d'automatisation :** 3 (le tableau de bord recommande, le planificateur valide ou refuse).

La fiche de conception et la maquette de l'écran sont rendues à part (`Fiche_conception_dashboard_San_Pedro.docx`).

### Ce que contient l'écran

| Partie | Contenu |
|---|---|
| En-tête | Pour qui, quelle décision, et un badge d'état pour chaque source (vert = OK, rouge = indisponible, avec l'âge de la donnée) |
| 5 tuiles | EVP San Pedro Bay, part des vides, prévision ± MAE, navires au mouillage, alerte météo 48 h. Chaque tuile a les 4 éléments du cours : valeur, référence, tendance, date et source |
| Volumes | Courbe mensuelle de Los Angeles et Long Beach depuis 2019 (total, importations, exportations, vides), avec la prévision du mois prochain |
| Comparaison mondiale | CPPI (score et rang par port, 2 éditions) et CNUCED (temps médian au port et escales par pays), dans deux graphiques séparés |
| En direct | Carte des navires (AIS) colorés selon leur statut, et météo du port sur 48 h avec les seuils d'alerte |
| Recommandations | 3 règles (météo, choix du port, file d'attente) avec leur raison, et des boutons Valider / Refuser qui enregistrent la décision |

---

## 2. Installation et lancement

### 2.1 Installer les bibliothèques

```
python -m pip install -r requirements.txt
```

### 2.2 Clé API aisstream.io (pour l'AIS seulement)

1. Créer un compte gratuit sur https://aisstream.io (connexion avec GitHub) et créer une clé API.
2. Copier `.env.exemple` en `.env` et remplacer `mets_ta_cle_ici` par sa propre clé.

Le fichier `.env` n'est pas rendu et il est exclu par `.gitignore` : **aucune clé n'apparaît dans le code ou dans les fichiers rendus.** Le code lit la clé avec `os.getenv("AISSTREAM_API_KEY")`.

### 2.3 Préparer les données (dans cet ordre)

| Script | Rôle | Fréquence |
|---|---|---|
| `scripts/02_collecte_la.py` | Volumes mensuels du port de Los Angeles | une fois par mois (vers le 15) |
| `scripts/07_collecte_lb.py` | Volumes mensuels du port de Long Beach (via le BTS) | une fois par mois |
| `scripts/08_cppi.py` | Score et rang CPPI de 6 ports, éditions 2024 et 2025 | une fois par an |
| `scripts/09_cnuced.py` | Escales et temps médian au port, par pays | une fois par an |
| `scripts/11_prevision.py` | Prévision du mois prochain ± MAE | après chaque mise à jour des volumes |
| `scripts/10_ais.py` | Instantané des navires autour du port (écoute de 3 min) | au plus toutes les 15 min |
| `scripts/12_meteo.py` | Vent, rafales et vagues, actuels et prévus sur 48 h | au plus toutes les heures (cache) |

Les autres scripts (`01`, `03`, `04`, `05`, `06`, `10b`) sont des scripts de test et de diagnostic que j'ai gardés pour montrer ma démarche.

### 2.4 Lancer le tableau de bord

```
python -m streamlit run app.py
```

Le tableau de bord **n'appelle aucune API lui-même** : il lit seulement les fichiers préparés par les scripts (`data/clean/` et `data/live/`). Il est donc rapide, il fonctionne même sans Internet, et il ne rappelle pas les API à chaque actualisation.

### 2.5 Organisation du dossier

```
dashboard_san_pedro/
├── app.py                 ← le tableau de bord
├── requirements.txt       ← les bibliothèques
├── README.md              ← ce document
├── sources.md             ← mon journal détaillé des sources (adresses, dates, contrôles)
├── .env.exemple           ← modèle pour la clé API (sans la vraie clé)
├── .gitignore             ← empêche de publier .env
├── scripts/               ← collecte, nettoyage, prévision, AIS, météo
└── data/
    ├── raw/               ← données brutes, jamais modifiées (preuve de la source)
    ├── clean/             ← données nettoyées, lues par le tableau de bord
    └── live/              ← données en direct (AIS, météo) + état des sources + décisions
```

---

## 3. Sources

Toutes les adresses, dates et contrôles sont détaillés dans `sources.md`. Résumé :

| # | Donnée | Source et adresse | Récupérée le |
|---|---|---|---|
| 1 | Volumes mensuels du port de Los Angeles (EVP), 01/2019 à 10/2026 | Port of Los Angeles – https://portoflosangeles.org/business/statistics/container-statistics (une page par année) | 18/11/2026 |
| 2 | Volumes mensuels du port de Long Beach (EVP), 01/2019 à 09/2026 | Bureau of Transportation Statistics, "Supply Chain and Freight Indicators" – https://www.bts.gov/freight-indicators (le site du port, polb.com, est inaccessible depuis Djibouti) | 19/11/2026 |
| 3 | CPPI : score et rang de 6 ports, éditions 2024 et 2025 | Banque mondiale / S&P Global – https://www.worldbank.org/en/topic/transport/publication/cppi et https://www.worldbank.org/en/topic/transport/publication/cppi-2024 | 19/11/2026 |
| 4 | Escales et temps médian au port des porte-conteneurs, par pays, 2018-2023 | CNUCED, UNCTADstat – https://unctadstat.unctad.org/datacentre/dataviewer/US.PortCalls et http://stats.unctad.org/portcalls_number_a | 19/11/2026 |
| 5 | Navires autour du port (position, type, statut) | aisstream.io – wss://stream.aisstream.io/v0/stream | 19/11/2026 (en direct) |
| 6 | Vent, rafales et vagues, actuels et prévus | Open-Meteo – https://api.open-meteo.com/v1/forecast et https://marine-api.open-meteo.com/v1/marine | 19/11/2026 (en direct) |

---

## 4. Traitements

### Los Angeles
- Le port publie une page web par année : j'ai lu le tableau de chaque page (2019 à 2026) avec `pandas.read_html` et je les ai assemblés.
- J'ai gardé une copie brute de chaque page dans `data/raw/` et j'ai supprimé les lignes de totaux annuels.
- **Vides = Empty Imports + Empty Exports.**
- J'ai trouvé une **erreur de saisie sur le site du port** : en novembre 2020, le total est écrit « 889.,748.15 ». J'ai écrit une fonction de nettoyage, puis j'ai recalculé le total à partir des composantes (889 746,15). Ce chiffre est confirmé par le total annuel publié par le port.
- Contrôles : 94 mois sur 94, somme des composantes = total, somme 2020 = total annuel publié.

### Long Beach
- Le site du port (polb.com) refuse les connexions depuis Djibouti (erreur 403 avec Python, « Access Denied » dans le navigateur). J'ai donc utilisé une **source officielle de remplacement**, le BTS (ministère américain des Transports).
- Le fichier BTS est en « format long » : j'ai filtré Long Beach et les 3 indicateurs conteneurs, puis je l'ai remis en « format large » (`pivot_table`).
- Avant de l'utiliser, **j'ai vérifié sa fiabilité** : pour Los Angeles, les chiffres BTS sont identiques à ceux du port (0,00 % d'écart sur 93 mois). Pour Long Beach, le total recalculé est inférieur de 1,85 % en moyenne au total officiel (46 mois), ce qui correspond aux vides importés absents du BTS.
- **Janvier 2019** : les exportations du BTS (131 436) rendaient la somme supérieure au total. Je les ai remplacées par le chiffre annoncé par le port (117 838).
- Vides = vides exportés seulement ; total = imports pleins + exports pleins + vides exportés.

### CPPI
- J'ai lu les deux fichiers Excel de la Banque mondiale et harmonisé les noms de colonnes, qui changent d'une édition à l'autre.
- J'ai repéré les ports par leur **code UN/LOCODE** et non par leur nom, car le nom change (« Tanger-Mediterranean » devient « Tanger Med »).
- Ports retenus : Los Angeles, Long Beach, Djibouti, et pour la comparaison Singapour (hub mondial), Salalah (concurrent régional de Djibouti) et Tanger Med (grand port africain).
- Contrôle : les scores 2024 sont identiques dans les deux éditions, on peut donc les comparer.

### CNUCED
- J'ai décompressé les archives `.7z` directement en Python (`py7zr`) et lu les codes comme du texte, pour garder les zéros (« 0000 » = Monde, « 03 » = porte-conteneurs).
- J'ai gardé les **porte-conteneurs** seulement, pour rester cohérente avec les EVP et le CPPI, et j'ai converti le temps médian en heures.
- Pays retenus : États-Unis, Singapour, Chine, Pays-Bas et Monde (référence), plus l'Afrique de l'Est (région de Djibouti) pour le nombre d'escales.

### AIS
- Le script écoute la zone pendant 3 minutes et garde la dernière position de chaque navire (numéro MMSI).
- La position et le type arrivent dans **deux messages différents** : je les relie par le MMSI (jointure). Les fiches (nom, type) sont gardées en mémoire d'une écoute à l'autre, car elles n'arrivent qu'environ toutes les 6 minutes.
- Je traduis les codes AIS : type 70-79 = cargo / porte-conteneurs, statut 1 = au mouillage, 5 = à quai. Si le statut n'est pas renseigné, une vitesse inférieure à 0,5 nœud donne « à l'arrêt ».

### Météo
- Deux appels (vent et vagues), fusionnés heure par heure, sur les 48 prochaines heures et à l'heure locale du port.
- Pas de nouvel appel si les données ont moins de 60 minutes (cache).

---

## 5. Méthode

### 5.1 Fonction intelligente n°1 : prévision avec marge d'incertitude
J'ai appliqué la méthode de la diapo 21 du cours.
1. **Trois modèles simples** comparés : naïf saisonnier (même mois l'an dernier), saisonnier + tendance, et moyenne des 3 derniers mois.
2. **Backtest** sur les 12 derniers mois : pour chaque mois, je prévois avec les seules données d'avant, puis je compare au vrai chiffre. La **MAE** est la moyenne des erreurs.
3. Je garde le modèle qui a la plus petite MAE et j'affiche « **prévision ± MAE** », avec l'horizon (le mois prochain).
4. La MAE est recalculée à chaque lancement du script.

**Résultat :** c'est la **moyenne des 3 derniers mois** qui gagne pour les trois séries, avec une erreur d'environ **6 à 7 %**. Les modèles saisonniers se trompent davantage parce que 2025 a été une année perturbée (achats anticipés liés aux droits de douane) : le « même mois l'an dernier » n'est pas un bon repère en ce moment.

### 5.2 Fonction intelligente n°2 : alerte météo
- **Alerte** : rafales ≥ 72 km/h (environ 45 mph, niveau qui a arrêté les portiques du port de Felixstowe).
- **Vigilance** : rafales ≥ 50 km/h (marge que j'ai choisie sous le seuil d'arrêt) ou vagues ≥ 2 m.
- J'ai volontairement mis **seulement deux seuils**, pour éviter la fatigue d'alerte (diapo 34).

### 5.3 Recommandations d'action (niveau 3)
| Règle | Données croisées | Recommandation |
|---|---|---|
| Météo | prévisions 48 h | décaler les arrivées non urgentes (alerte), prévoir une marge (vigilance), revérifier (proche du seuil) |
| Choix du port | CPPI + croissance du trafic | privilégier le port le mieux classé ; signaler un risque d'attente si l'autre port est moins efficace et voit son trafic augmenter le plus |
| File d'attente | AIS | ralentir les navires (arrivée juste-à-temps) si au moins 10 navires sont au mouillage |

Chaque recommandation affiche **sa raison** avec les chiffres, pour éviter l'effet « boîte noire ». Les boutons Valider / Refuser enregistrent la décision dans `data/live/decisions.csv` : c'est le **retour** (5e composant d'un système d'aide à la décision, diapo 30).

J'ai choisi le niveau 3 avec les critères de la diapo 33 : la décision n'est pas très fréquente, une erreur peut coûter cher et les données AIS gratuites sont incomplètes. Il vaut donc mieux que l'humain garde la main.

### 5.4 Disponibilité des sources
- Chaque script réessaie 3 fois en cas d'échec et **n'efface jamais** les anciennes données.
- L'état de chaque source est écrit dans un petit fichier (`ais_statut.json`, `meteo_statut.json`). Le tableau de bord affiche alors un badge rouge et un message clair : « AIS indisponible : dernière liste connue, il y a 36 min ».

---

## 6. Limites

**Données**
- **Long Beach** : source de remplacement (BTS) ; total sous-estimé d'environ 1,85 % (vides importés absents) ; données jusqu'en septembre 2026 seulement (un mois de moins que Los Angeles).
- **CNUCED** : **Djibouti n'est pas publié** (vérifié dans les deux tableaux et dans la fiche pays). Les chiffres sont par **pays** : « États-Unis » regroupe tous les ports américains, pas seulement San Pedro Bay. Les données s'arrêtent en 2023, alors que le CPPI va jusqu'en 2025.
- **CPPI** : c'est un score relatif (0 = port médian), pas une durée. Il n'est pas comparable directement avec la CNUCED, d'où les deux graphiques séparés.
- **AIS** : couverture gratuite incomplète ; statut saisi à la main par l'équipage, parfois faux ; type de navire souvent inconnu lors des premières écoutes ; le type 70-79 regroupe tous les cargos, pas seulement les porte-conteneurs.
- **Météo** : prévision d'un modèle numérique en un seul point, pas une mesure sur place.

**Méthode**
- La prévision « moyenne 3 mois » ignore les saisons (risque de surestimer novembre, mois de baisse après le pic d'avant Noël).
- Le choix du modèle et la MAE sont calculés sur les mêmes 12 mois : la MAE affichée est un peu optimiste.
- Les seuils (50 / 72 km/h, 2 m de vagues, 10 navires au mouillage) ne sont pas officiels. Le seuil de 10 navires est provisoire : il faudrait un historique AIS de plusieurs jours pour calculer la référence prévue dans ma fiche (médiane sur 7 jours + 2 écarts-types).
- Les recommandations sont des règles simples. Elles ne remplacent pas l'avis du planificateur, qui doit vérifier la carte et la météo avant de valider (risque de biais d'automatisation, diapo 34).

**Technique**
- L'AIS et la météo ne se mettent à jour que si on relance les scripts (ou si on programme leur lancement automatique).
- La connexion depuis Djibouti est parfois lente : j'ai dû allonger les délais d'attente (60 s) et ajouter des nouveaux essais.

---

## 7. Utilisation de l'IA

Comme le permet la consigne, je me suis fait aider par un assistant d'IA pour écrire une partie du code et pour corriger les erreurs. J'ai lancé et testé chaque script moi-même, étape par étape, j'ai vérifié les résultats avec les chiffres publiés par les ports, et je suis capable d'expliquer chaque partie du code.
