# Fonction intelligente n°1 : PRÉVISION des EVP du mois prochain, avec marge d'incertitude (± MAE)
# Méthode du cours (Séquence 6, diapo 21) :
#   1. mesurer l'erreur moyenne du modèle sur le passé (MAE)
#   2. afficher "prévision - erreur" et "prévision + erreur"
#   3. préciser l'horizon (le mois prochain)
#   4. recalculer l'erreur régulièrement (ici : à chaque lancement du script)
import numpy as np
import pandas as pd

NB_MOIS_TEST = 12   # on teste les modèles sur les 12 derniers mois connus

# ---------- 1) Données : une série mensuelle par port + San Pedro (LA + LB) ----------
df = pd.read_csv("data/clean/san_pedro_teu_mensuel.csv", parse_dates=["date"])
series = {port: d.set_index("date")["total"].sort_index() for port, d in df.groupby("port")}

# San Pedro = LA + LB, seulement sur les mois communs (LB s'arrête un mois plus tôt)
communs = series["Los Angeles"].index.intersection(series["Long Beach"].index)
series["San Pedro Bay"] = series["Los Angeles"][communs] + series["Long Beach"][communs]


# ---------- 2) Trois modèles simples (faciles à expliquer) ----------
# Chacun prend l'historique connu et renvoie la prévision du mois suivant.
def naif_saisonnier(hist):
    """Le mois prochain ressemblera au même mois de l'année dernière."""
    return hist.iloc[-12]


def saisonnier_tendance(hist):
    """Même mois de l'année dernière, corrigé de la tendance récente :
    on multiplie par (3 derniers mois) / (les 3 mêmes mois un an avant)."""
    croissance = hist.iloc[-3:].mean() / hist.iloc[-15:-12].mean()
    return hist.iloc[-12] * croissance


def moyenne_3_mois(hist):
    """Le mois prochain ressemblera à la moyenne des 3 derniers mois."""
    return hist.iloc[-3:].mean()


MODELES = {
    "naïf saisonnier": naif_saisonnier,
    "saisonnier + tendance": saisonnier_tendance,
    "moyenne 3 mois": moyenne_3_mois,
}


# ---------- 3) Backtest : on "remonte le temps" pour mesurer l'erreur réelle ----------
def backtest(serie, modele):
    """Pour chacun des 12 derniers mois, on prévoit avec les données d'AVANT ce mois,
    puis on compare à la vraie valeur. On renvoie le tableau des erreurs."""
    lignes = []
    for i in range(len(serie) - NB_MOIS_TEST, len(serie)):
        hist = serie.iloc[:i]                 # uniquement le passé (pas de triche)
        prevu = modele(hist)
        reel = serie.iloc[i]
        lignes.append({"date": serie.index[i], "reel": reel, "prevu": prevu,
                       "erreur_abs": abs(reel - prevu)})
    return pd.DataFrame(lignes)


resultats, tests = [], []
for nom_serie, serie in series.items():
    # a) MAE de chaque modèle sur les 12 derniers mois
    scores = {}
    for nom_modele, modele in MODELES.items():
        bt = backtest(serie, modele)
        scores[nom_modele] = bt["erreur_abs"].mean()
        bt["serie"], bt["modele"] = nom_serie, nom_modele
        tests.append(bt)

    # b) on garde le modèle qui se trompe le moins
    meilleur = min(scores, key=scores.get)
    mae = scores[meilleur]

    # c) prévision du mois suivant le dernier mois connu
    prevision = MODELES[meilleur](serie)
    mois_prevu = serie.index[-1] + pd.DateOffset(months=1)

    resultats.append({
        "serie": nom_serie,
        "dernier_mois_connu": serie.index[-1].date(),
        "dernier_total": round(serie.iloc[-1]),
        "mois_prevu": mois_prevu.date(),
        "modele": meilleur,
        "prevision": round(prevision),
        "mae": round(mae),
        "borne_basse": round(prevision - mae),
        "borne_haute": round(prevision + mae),
        "mae_pct": round(mae / serie.iloc[-NB_MOIS_TEST:].mean() * 100, 1),
        "mae_naif_saisonnier": round(scores["naïf saisonnier"]),
        "mae_saisonnier_tendance": round(scores["saisonnier + tendance"]),
        "mae_moyenne_3_mois": round(scores["moyenne 3 mois"]),
    })

prev = pd.DataFrame(resultats)
prev.to_csv("data/clean/prevision_teu.csv", index=False)
pd.concat(tests).to_csv("data/clean/prevision_backtest.csv", index=False)

# ---------- 4) Affichage ----------
pd.set_option("display.width", 200)
print("Comparaison des modèles (MAE sur les 12 derniers mois, en EVP) :")
print(prev[["serie", "mae_naif_saisonnier", "mae_saisonnier_tendance", "mae_moyenne_3_mois",
            "modele"]].to_string(index=False))
print("\nPrévisions retenues :")
for _, r in prev.iterrows():
    print(f"  {r['serie']:<14} {r['mois_prevu']} : {r['prevision']:>9,} EVP "
          f"(entre {r['borne_basse']:,} et {r['borne_haute']:,}) "
          f"| erreur moyenne {r['mae']:,} EVP ({r['mae_pct']} %) | modèle : {r['modele']}"
          .replace(",", " "))
print("\nFichiers enregistrés : data/clean/prevision_teu.csv et data/clean/prevision_backtest.csv")