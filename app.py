# Tableau de bord San Pedro Bay (Los Angeles + Long Beach) face au monde
# Lancement : streamlit run app.py
# Le tableau de bord LIT les fichiers préparés par les scripts (data/clean et data/live) :
# il n'appelle aucune API lui-même.
import json
import os
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Tableau de bord San Pedro Bay", page_icon="⚓", layout="wide")

CLEAN = "data/clean"
LIVE = "data/live"


# =====================================================================
# 1) LECTURE DES DONNÉES (mise en cache pour ne pas relire à chaque clic)
# =====================================================================
@st.cache_data(ttl=600)   # relu au plus toutes les 10 minutes
def lire_csv(chemin, dates=None):
    if not os.path.exists(chemin):
        return None
    return pd.read_csv(chemin, parse_dates=dates)


@st.cache_data(ttl=600)
def lire_json(chemin):
    if not os.path.exists(chemin):
        return None
    with open(chemin, encoding="utf-8") as f:
        return json.load(f)


def date_fichier(chemin):
    """Date de dernière modification d'un fichier (UTC), ou None."""
    if not os.path.exists(chemin):
        return None
    return datetime.fromtimestamp(os.path.getmtime(chemin), tz=timezone.utc)


def age_texte(dt):
    """'il y a 12 min', 'il y a 3 h', 'il y a 2 j'."""
    if dt is None:
        return "jamais"
    minutes = (datetime.now(timezone.utc) - dt).total_seconds() / 60
    if minutes < 60:
        return f"il y a {minutes:.0f} min"
    if minutes < 48 * 60:
        return f"il y a {minutes / 60:.0f} h"
    return f"il y a {minutes / 1440:.0f} j"


def nombre(x, decimales=0):
    """Format français : 1 234 567"""
    return f"{x:,.{decimales}f}".replace(",", " ").replace(".", ",")


teu = lire_csv(f"{CLEAN}/san_pedro_teu_mensuel.csv", dates=["date"])
prev = lire_csv(f"{CLEAN}/prevision_teu.csv")
cppi = lire_csv(f"{CLEAN}/cppi_ports.csv")
cnuced = lire_csv(f"{CLEAN}/cnuced_pays.csv")
ais = lire_csv(f"{LIVE}/ais_navires.csv")
ais_statut = lire_json(f"{LIVE}/ais_statut.json")
meteo_h = lire_csv(f"{LIVE}/meteo_horaire.csv", dates=["heure_locale"])
meteo = lire_json(f"{LIVE}/meteo_actuelle.json")
meteo_statut = lire_json(f"{LIVE}/meteo_statut.json")


# =====================================================================
# 2) STYLE DES TUILES ET DES BADGES
# =====================================================================
st.markdown("""
<style>
.tuile {border:1px solid #d0d7de; border-radius:10px; padding:12px 14px; background:white; height:100%;}
.tuile.vigilance {border:2px solid #dd6b20;}
.tuile.alerte {border:2px solid #c53030;}
.tuile .titre {font-size:0.85rem; color:#4a5568; font-weight:600; margin-bottom:4px;}
.tuile .valeur {font-size:1.6rem; font-weight:700; color:#1f2a37; line-height:1.2;}
.tuile .ref {font-size:0.8rem; color:#1f2a37; margin-top:6px;}
.tuile .tendance {font-size:0.8rem; margin-top:2px;}
.tuile .maj {font-size:0.72rem; color:#6b7280; font-style:italic; margin-top:6px;}
.badge {display:inline-block; padding:3px 9px; border-radius:12px; color:white; font-size:0.75rem;
        margin:2px 4px 2px 0;}
.ok {background:#2f855a;} .ko {background:#c53030;} .vieux {background:#dd6b20;}
</style>
""", unsafe_allow_html=True)


def tuile(titre, valeur, reference, tendance, maj, couleur_tendance="#4a5568", niveau=""):
    """Une tuile = les 4 éléments du cours (diapo 10) : valeur, référence, tendance, fraîcheur."""
    st.markdown(f"""
    <div class="tuile {niveau}">
      <div class="titre">{titre}</div>
      <div class="valeur">{valeur}</div>
      <div class="ref">{reference}</div>
      <div class="tendance" style="color:{couleur_tendance}">{tendance}</div>
      <div class="maj">{maj}</div>
    </div>""", unsafe_allow_html=True)


def fleche(variation_pct):
    """Flèche et couleur selon le sens de la variation."""
    if variation_pct > 0:
        return f"▲ +{nombre(variation_pct, 1)} %", "#2f855a"
    if variation_pct < 0:
        return f"▼ {nombre(variation_pct, 1)} %", "#c53030"
    return "► 0 %", "#4a5568"


# =====================================================================
# 3) EN-TÊTE : titre + état de chaque source
# =====================================================================
st.title("⚓ San Pedro Bay (Los Angeles + Long Beach) face au monde")
st.caption("Pour : responsable de la planification des escales d'un armateur desservant San Pedro Bay "
           "et Djibouti · Décision : choisir LA ou LB et ajuster l'heure d'arrivée des navires "
           "des deux prochaines semaines.")


def badge(nom, ok, detail):
    classe = "ok" if ok else "ko"
    symbole = "✓" if ok else "⚠"
    return f'<span class="badge {classe}" title="{detail}">{nom} {symbole} · {detail}</span>'


badges = [
    badge("EVP LA/LB", teu is not None, age_texte(date_fichier(f"{CLEAN}/san_pedro_teu_mensuel.csv"))),
    badge("CPPI", cppi is not None, "éditions 2024-2025"),
    badge("CNUCED", cnuced is not None, "données 2018-2023"),
    badge("AIS", bool(ais_statut and ais_statut.get("ok")),
          age_texte(date_fichier(f"{LIVE}/ais_navires.csv"))),
    badge("Météo", bool(meteo_statut and meteo_statut.get("ok")),
          age_texte(date_fichier(f"{LIVE}/meteo_horaire.csv"))),
]
st.markdown("".join(badges), unsafe_allow_html=True)
st.write("")


# =====================================================================
# 4) LES TUILES (5 indicateurs de la fiche de conception)
# =====================================================================
c1, c2, c3, c4, c5 = st.columns(5)

# --- Tuile 1 : EVP totaux San Pedro du dernier mois commun ---
with c1:
    if teu is None:
        tuile("EVP San Pedro Bay", "—", "Données indisponibles", "", "")
    else:
        large = teu.pivot_table(index="date", columns="port", values="total").dropna()
        large["san_pedro"] = large["Los Angeles"] + large["Long Beach"]
        dernier = large.index.max()
        valeur = large.loc[dernier, "san_pedro"]
        an_moins_1 = large["san_pedro"].get(dernier - pd.DateOffset(years=1))
        ref_2019 = large["san_pedro"].get(dernier.replace(year=2019))
        tendance, couleur = fleche((valeur / an_moins_1 - 1) * 100) if an_moins_1 else ("", "#4a5568")
        tuile(f"EVP San Pedro Bay ({dernier.strftime('%m/%Y')})",
              f"{nombre(valeur / 1e6, 2)} M EVP",
              f"Réf. : {nombre(an_moins_1 / 1e6, 2)} M un an avant · "
              f"{nombre(ref_2019 / 1e6, 2)} M en {dernier.strftime('%m')}/2019",
              f"{tendance} sur un an", "Source : ports LA (site) et LB (BTS) · mensuel",
              couleur)

# --- Tuile 2 : part des conteneurs vides (Los Angeles) ---
with c2:
    if teu is None:
        tuile("Part des vides", "—", "Données indisponibles", "", "")
    else:
        la = teu[teu["port"] == "Los Angeles"].set_index("date").sort_index()
        part = la["vides"] / la["total"] * 100
        dernier_la = part.index.max()
        ref = part[part.index.year == 2019].mean()
        ecart = part.iloc[-1] - ref
        tuile(f"Part des vides – Los Angeles ({dernier_la.strftime('%m/%Y')})",
              f"{nombre(part.iloc[-1], 1)} %",
              f"Réf. : moyenne 2019 = {nombre(ref, 1)} %",
              f"{'▲' if ecart > 0 else '▼'} {nombre(ecart, 1)} pts vs 2019",
              "Source : port de LA · mensuel (LB : vides exportés seulement)",
              "#dd6b20" if ecart > 5 else "#4a5568")

# --- Tuile 3 : prévision ± MAE ---
with c3:
    if prev is None:
        tuile("Prévision EVP", "—", "Prévision indisponible", "", "")
    else:
        p = prev[prev["serie"] == "San Pedro Bay"].iloc[0]
        mois = pd.to_datetime(p["mois_prevu"]).strftime("%m/%Y")
        tuile(f"Prévision San Pedro Bay ({mois})",
              f"{nombre(p['prevision'] / 1e6, 2)} M EVP",
              f"Entre {nombre(p['borne_basse'] / 1e6, 2)} et {nombre(p['borne_haute'] / 1e6, 2)} M "
              f"(± MAE = {nombre(p['mae'] / 1e3)} k EVP)",
              f"Horizon : mois prochain · modèle « {p['modele']} »",
              "Calcul : backtest sur 12 mois · mensuel")

# --- Tuile 4 : navires au mouillage (AIS) ---
with c4:
    if ais is None:
        tuile("Navires au mouillage", "—", "AIS indisponible", "", "", niveau="vigilance")
    else:
        nb = int((ais["statut"] == "au mouillage").sum())
        ok = bool(ais_statut and ais_statut.get("ok"))
        tuile("Navires au mouillage (AIS)",
                            f"{nb} navire{'s' if nb > 1 else ''}",
              f"sur {len(ais)} navires dans la zone · seuil : médiane 7 j + 2σ (historique en constitution)",
              "" if ok else "⚠ AIS indisponible : dernière liste connue",
              f"Mis à jour {age_texte(date_fichier(f'{LIVE}/ais_navires.csv'))} · Source : aisstream.io",
              "#c53030", "" if ok else "vigilance")

# --- Tuile 5 : alerte météo 48 h ---
with c5:
    if meteo is None:
        tuile("Météo 48 h", "—", "Météo indisponible", "", "", niveau="vigilance")
    else:
        niv = meteo["niveau_48h"]
        proche = meteo["rafales_max_48h_kmh"] >= 45 or meteo["vagues_max_48h_m"] >= 1.8
        texte_niv = {"alerte": "🔴 ALERTE", "vigilance": "🟠 Vigilance",
                     "normal": "🟢 Normal" + (" (proche du seuil)" if proche else "")}[niv]
        tuile("Alerte météo – 48 h",
              f"Rafales {nombre(meteo['rafales_max_48h_kmh'])} km/h",
              f"Seuils : vigilance 50 · alerte 72 km/h · vagues max {nombre(meteo['vagues_max_48h_m'], 1)} m "
              f"(seuil 2 m)",
              f"{texte_niv} · pic le {meteo['heure_rafales_max'][8:10]}/{meteo['heure_rafales_max'][5:7]} "
              f"à {meteo['heure_rafales_max'][11:]} (heure du port)",
              f"Mis à jour {age_texte(date_fichier(f'{LIVE}/meteo_horaire.csv'))} · Source : Open-Meteo",
              "#dd6b20" if (niv != "normal" or proche) else "#2f855a",
              "" if niv == "normal" else niv)

st.divider()

# =====================================================================
# 5) VUE DES VOLUMES : Los Angeles et Long Beach depuis 2019
# =====================================================================
import plotly.graph_objects as go

COULEURS = {"Los Angeles": "#2b6cb0", "Long Beach": "#dd6b20"}
CHOIX = {"Total": "total", "Importations pleines": "imports_pleins",
         "Exportations pleines": "exports_pleins", "Vides": "vides"}

st.subheader("📈 Volumes mensuels depuis 2019 – Los Angeles et Long Beach")

if teu is None:
    st.warning("Volumes indisponibles : lance scripts/02_collecte_la.py et scripts/07_collecte_lb.py.")
else:
    col_graph, col_lecture = st.columns([3, 1])

    with col_graph:
        choix = st.radio("Indicateur", list(CHOIX), horizontal=True, label_visibility="collapsed")
        colonne = CHOIX[choix]

        fig = go.Figure()
        for port, couleur in COULEURS.items():
            d = teu[teu["port"] == port].sort_values("date")
            fig.add_trace(go.Scatter(x=d["date"], y=d[colonne], name=port, mode="lines",
                                     line=dict(color=couleur, width=2),
                                     hovertemplate="%{x|%m/%Y} : %{y:,.0f} EVP<extra>" + port + "</extra>"))

            # Prévision du mois prochain (± MAE), seulement pour le total
            if colonne == "total" and prev is not None:
                p = prev[prev["serie"] == port].iloc[0]
                x_prev = pd.to_datetime(p["mois_prevu"])
                fig.add_trace(go.Scatter(
                    x=[d["date"].iloc[-1], x_prev], y=[d["total"].iloc[-1], p["prevision"]],
                    mode="lines+markers", line=dict(color=couleur, dash="dash"),
                    marker=dict(size=[0, 9]), showlegend=False,
                    error_y=dict(type="data", array=[0, p["mae"]], color=couleur, thickness=2, width=8),
                    hovertemplate=(f"Prévision {x_prev:%m/%Y} : {p['prevision']:,.0f} EVP "
                                   f"(± {p['mae']:,.0f})<extra>{port}</extra>")))

        fig.update_layout(height=420, margin=dict(l=10, r=10, t=10, b=10),
                          legend=dict(orientation="h", y=1.08, x=0),
                          yaxis=dict(title="EVP par mois", rangemode="tozero"),   # axe à partir de 0
                          xaxis=dict(title=None), hovermode="x unified",
                          separators=", ")
        st.plotly_chart(fig, use_container_width=True)

        note = "Pointillés et barre : prévision du mois prochain ± erreur moyenne (MAE). " if colonne == "total" else ""
        if colonne in ("vides", "total"):
            note += "Long Beach : vides exportés seulement (source BTS), total sous-estimé d'environ 1,85 %."
        st.caption(note + " Sources : port de Los Angeles ; Bureau of Transportation Statistics (Long Beach).")

    with col_lecture:
        st.markdown("**Lecture rapide** – dernier mois commun")
        large = teu.pivot_table(index="date", columns="port", values=colonne).dropna()
        dernier = large.index.max()
        un_an = dernier - pd.DateOffset(years=1)
        total_sp = large.loc[dernier].sum()
        for port in ["Los Angeles", "Long Beach"]:
            v = large.loc[dernier, port]
            var = (v / large.loc[un_an, port] - 1) * 100 if un_an in large.index else None
            st.metric(f"{port} ({dernier:%m/%Y})", f"{nombre(v / 1e3)} k EVP",
                      f"{nombre(var, 1)} % sur un an" if var is not None else None)
            st.caption(f"Part de San Pedro Bay : {nombre(v / total_sp * 100, 0)} %")


st.divider()

# =====================================================================
# 6) VUE MONDIALE : CPPI (par port) et CNUCED (par pays)
#    Deux graphiques SÉPARÉS : les deux sources ne mesurent pas la même chose
# =====================================================================
st.subheader("🌍 San Pedro Bay face au monde")
col_cppi, col_cnuced = st.columns(2)

# Ports mis en valeur (les autres en couleur plus discrète)
PORTS_CLES = {"Los Angeles": "#2b6cb0", "Long Beach": "#dd6b20", "Djibouti": "#2f855a"}

with col_cppi:
    st.markdown("**Efficacité des ports – CPPI (Banque mondiale)**")
    if cppi is None:
        st.warning("CPPI indisponible : lance scripts/08_cppi.py.")
    else:
        derniere = cppi["edition"].max()
        precedente = cppi["edition"].min()
        ordre = cppi[cppi["edition"] == derniere].sort_values("score")["port"].tolist()  # barres triées

        fig = go.Figure()
        for edition, opacite in [(precedente, 0.35), (derniere, 1.0)]:
            d = cppi[cppi["edition"] == edition].set_index("port").loc[ordre].reset_index()
            couleurs = [PORTS_CLES.get(p, "#718096") for p in d["port"]]
            fig.add_trace(go.Bar(
                y=d["port"], x=d["score"], orientation="h", name=f"Édition {edition}",
                marker=dict(color=couleurs, opacity=opacite),
                text=[f"{r}e / {n}" for r, n in zip(d["rang"], d["nb_ports_classes"])] if edition == derniere else None,
                textposition="outside",
                hovertemplate="%{y} : score %{x:.1f}<extra>Édition " + str(edition) + "</extra>"))
        fig.add_vline(x=0, line_dash="dot", line_color="#4a5568",
                      annotation_text="0 = port médian", annotation_position="top")
        # de la place à droite pour le texte "3e / 400"
        fig.update_xaxes(range=[min(0, cppi["score"].min()) * 1.15, cppi["score"].max() * 1.35])
        fig.update_layout(barmode="group", height=380, margin=dict(l=10, r=40, t=30, b=10),
                          showlegend=False, xaxis_title="Score CPPI",
                          separators=", ")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Barres claires : édition {precedente} · barres foncées et rang : édition {derniere}. "
                   "Score > 0 : navires traités plus vite que dans le port médian. "
                   "Source : Banque mondiale / S&P Global, CPPI.")

with col_cnuced:
    st.markdown("**Temps médian au port des porte-conteneurs – CNUCED (par pays)**")
    if cnuced is None:
        st.warning("CNUCED indisponible : lance scripts/09_cnuced.py.")
    else:
        derniere_an = int(cnuced["annee"].max())
        d = cnuced[cnuced["annee"].isin([derniere_an - 1, derniere_an])].dropna(subset=["temps_median_heures"])
        ordre = (d[d["annee"] == derniere_an].sort_values("temps_median_heures", ascending=False)["pays"].tolist())

        fig = go.Figure()
        for annee, opacite in [(derniere_an - 1, 0.35), (derniere_an, 1.0)]:
            da = d[d["annee"] == annee].set_index("pays").reindex(ordre).reset_index()
            couleurs = ["#2b6cb0" if p == "États-Unis" else "#a0aec0" if p == "Monde" else "#718096"
                        for p in da["pays"]]
            fig.add_trace(go.Bar(
                y=da["pays"], x=da["temps_median_heures"], orientation="h", name=str(annee),
                marker=dict(color=couleurs, opacity=opacite),
                text=[f"{h:.0f} h" for h in da["temps_median_heures"]] if annee == derniere_an else None,
                textposition="outside",
                customdata=da["escales"],
                hovertemplate="%{y} : %{x:.1f} h · %{customdata:,.0f} escales<extra>" + str(annee) + "</extra>"))
        monde = d[(d["pays"] == "Monde") & (d["annee"] == derniere_an)]["temps_median_heures"]
        if not monde.empty:
            fig.add_vline(x=float(monde.iloc[0]), line_dash="dot", line_color="#4a5568",
                          annotation_text="médiane mondiale", annotation_position="top")
        fig.update_xaxes(range=[0, d["temps_median_heures"].max() * 1.2])
        fig.update_layout(barmode="group", height=380, margin=dict(l=10, r=40, t=30, b=10),
                          showlegend=False, xaxis_title="Heures au port (médiane)",
                          separators=", ")
        st.plotly_chart(fig, use_container_width=True)

        # Escales : l'Afrique de l'Est (région de Djibouti) n'a pas de temps médian
        ae = cnuced[(cnuced["pays"].str.startswith("Afrique de l'Est")) & (cnuced["annee"] >= derniere_an - 1)]
        if len(ae) == 2:
            a, b = ae.sort_values("annee")["escales"].tolist()
            st.caption(f"Afrique de l'Est (région de Djibouti) : {nombre(b)} escales de porte-conteneurs "
                       f"en {derniere_an} ({'+' if b > a else ''}{nombre((b / a - 1) * 100)} % sur un an).")
        st.warning("**Djibouti** : escales et temps au port **non publiés par la CNUCED** "
                   "(vérifié le 19/11/2026). Voir le CPPI à gauche, où Djibouti figure.", icon="ℹ️")
        st.caption(f"Barres claires : {derniere_an - 1} · foncées : {derniere_an} (dernière année publiée). "
                   "Chiffres par PAYS : « États-Unis » = tous les ports américains. Source : CNUCED, UNCTADstat.")
    
st.divider()

# =====================================================================
# 7) VUE EN DIRECT : carte des navires (AIS) + météo du port
# =====================================================================
from plotly.subplots import make_subplots

st.subheader("📡 En direct – navires et météo du port")
col_carte, col_meteo = st.columns([3, 2])

COULEURS_STATUT = {"à quai": "#2f855a", "au mouillage": "#dd6b20", "en route": "#2b6cb0",
                   "à l'arrêt": "#a0aec0", "non manoeuvrant": "#c53030", "manoeuvre restreinte": "#805ad5"}

with col_carte:
    st.markdown("**Navires autour de San Pedro Bay (AIS)**")
    ok_ais = bool(ais_statut and ais_statut.get("ok"))
    if ais is None:
        st.error("AIS indisponible : aucune liste de navires. Lance scripts/10_ais.py.")
    else:
        if not ok_ais:
            st.warning(f"⚠ AIS indisponible lors de la dernière écoute "
                       f"({(ais_statut or {}).get('erreur', 'erreur inconnue')}). "
                       f"Affichage de la dernière liste connue, "
                       f"{age_texte(date_fichier(f'{LIVE}/ais_navires.csv'))}.")

        # Filtre par type de navire
        types = sorted(ais["type"].dropna().unique())
        choix_types = st.multiselect("Types de navires", types, default=types, label_visibility="collapsed")
        d = ais[ais["type"].isin(choix_types)].copy()
        d["destination"] = d["destination"].fillna("")

        fig = go.Figure()
        for statut, couleur in COULEURS_STATUT.items():
            ds = d[d["statut"] == statut]
            if ds.empty:
                continue
            fig.add_trace(go.Scattermap(
                lat=ds["latitude"], lon=ds["longitude"], mode="markers",
                marker=dict(size=11, color=couleur), name=f"{statut} ({len(ds)})",
                customdata=ds[["nom", "type", "vitesse_noeuds", "destination"]],
                hovertemplate=("<b>%{customdata[0]}</b><br>%{customdata[1]}<br>"
                               "Vitesse : %{customdata[2]} nœuds<br>Destination : %{customdata[3]}"
                               "<extra>" + statut + "</extra>")))
            fig.update_layout(map=dict(style="open-street-map", center=dict(lat=33.73, lon=-118.22), zoom=11.3),
                          height=430, margin=dict(l=0, r=0, t=0, b=0),
                          legend=dict(orientation="h", y=-0.02, bgcolor="rgba(255,255,255,0.8)"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"{len(d)} navires affichés · écoute de "
                   f"{(ais_statut or {}).get('duree_ecoute_s', '?')} s, "
                   f"{age_texte(date_fichier(f'{LIVE}/ais_navires.csv'))} · Source : aisstream.io. "
                   "Couverture gratuite incomplète ; statut saisi par l'équipage.")

with col_meteo:
    st.markdown("**Météo du port – 48 h (Open-Meteo)**")
    if meteo_h is None or meteo is None:
        st.error("Météo indisponible : lance scripts/12_meteo.py.")
    else:
        if not (meteo_statut and meteo_statut.get("ok")):
            st.warning(f"⚠ Météo indisponible lors du dernier appel. Dernières données connues, "
                       f"{age_texte(date_fichier(f'{LIVE}/meteo_horaire.csv'))}.")

        m1, m2, m3 = st.columns(3)
        m1.metric("Vent", f"{nombre(meteo['vent_kmh'])} km/h")
        m2.metric("Rafales", f"{nombre(meteo['rafales_kmh'])} km/h")
        m3.metric("Vagues", f"{nombre(meteo['vagues_m'], 1)} m")

        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=meteo_h["heure_locale"], y=meteo_h["rafales_kmh"], name="Rafales (km/h)",
                                 line=dict(color="#1f2a37", width=2)), secondary_y=False)
        fig.add_trace(go.Scatter(x=meteo_h["heure_locale"], y=meteo_h["vent_kmh"], name="Vent (km/h)",
                                 line=dict(color="#718096", width=1)), secondary_y=False)
        fig.add_trace(go.Scatter(x=meteo_h["heure_locale"], y=meteo_h["vagues_m"], name="Vagues (m)",
                                 line=dict(color="#3182ce", width=2, dash="dot")), secondary_y=True)
        # Seuils de la fiche de conception
        fig.add_hline(y=72, line_dash="dash", line_color="#c53030", annotation_text="alerte 72",
                      annotation_position="top left")
        fig.add_hline(y=50, line_dash="dot", line_color="#dd6b20", annotation_text="vigilance 50",
                      annotation_position="top left")
        fig.update_yaxes(title_text="km/h", range=[0, max(80, meteo_h["rafales_kmh"].max() * 1.1)],
                         secondary_y=False)
        fig.update_yaxes(title_text="vagues (m)", range=[0, max(3, meteo_h["vagues_m"].max() * 1.2)],
                         secondary_y=True, showgrid=False)
        fig.update_layout(height=330, margin=dict(l=10, r=10, t=10, b=10), hovermode="x unified",
                          legend=dict(orientation="h", y=-0.2), separators=", ")
        st.plotly_chart(fig, use_container_width=True)
        st.caption(f"Heure locale du port (Los Angeles). Seuil vagues : 2 m (hypothèse). "
                   f"Mis à jour {age_texte(date_fichier(f'{LIVE}/meteo_horaire.csv'))} · Source : Open-Meteo.")
        
st.divider()

# =====================================================================
# 8) RECOMMANDATIONS D'ACTION (niveau d'automatisation 3 :
#    le tableau de bord PROPOSE, le planificateur VALIDE ou REFUSE)
# =====================================================================
st.subheader("🧭 Recommandations pour le planificateur")
st.caption("Niveau d'automatisation 3 : le système recommande, l'humain valide. "
           "Chaque recommandation affiche sa raison. Vérifiez la carte et la météo avant de valider.")

FICHIER_DECISIONS = f"{LIVE}/decisions.csv"
recos = []   # liste de (priorité, titre, action, raison)

# --- Règle 1 : météo (alerte, vigilance ou proche du seuil) ---
if meteo is not None:
    pic = f"{meteo['heure_rafales_max'][8:10]}/{meteo['heure_rafales_max'][5:7]} à {meteo['heure_rafales_max'][11:]}"
    if meteo["niveau_48h"] == "alerte":
        recos.append((1, "🔴 Météo : risque d'arrêt des portiques",
                      f"Décaler les arrivées non urgentes après le {meteo['fin_risque']} (heure du port) "
                      "et ralentir les navires en approche (arrivée juste-à-temps).",
                      f"Rafales prévues jusqu'à {nombre(meteo['rafales_max_48h_kmh'])} km/h (pic le {pic}), "
                      f"au-dessus du seuil d'alerte de 72 km/h."))
    elif meteo["niveau_48h"] == "vigilance":
        recos.append((2, "🟠 Météo : vigilance",
                      f"Prévoir une marge sur les créneaux entre le {meteo['debut_risque']} et le "
                      f"{meteo['fin_risque']} et prévenir les capitaines des navires attendus.",
                      f"Rafales jusqu'à {nombre(meteo['rafales_max_48h_kmh'])} km/h ou vagues jusqu'à "
                      f"{nombre(meteo['vagues_max_48h_m'], 1)} m (seuils : 50 km/h, 2 m)."))
    elif meteo["rafales_max_48h_kmh"] >= 45 or meteo["vagues_max_48h_m"] >= 1.8:
        recos.append((3, "🟡 Météo : proche du seuil",
                      "Pas de changement d'horaire pour l'instant ; revérifier à la prochaine mise à jour "
                      f"(dans moins d'une heure), surtout autour du {pic}.",
                      f"Rafales jusqu'à {nombre(meteo['rafales_max_48h_kmh'])} km/h et vagues jusqu'à "
                      f"{nombre(meteo['vagues_max_48h_m'], 1)} m : juste sous les seuils de vigilance "
                      "(50 km/h, 2 m)."))

# --- Règle 2 : choix du port (LA ou LB) d'après le CPPI et la croissance du trafic ---
if cppi is not None and teu is not None:
    c = cppi[cppi["edition"] == cppi["edition"].max()].set_index("port")
    large = teu.pivot_table(index="date", columns="port", values="total").dropna()
    der = large.index.max()
    un_an = der - pd.DateOffset(years=1)
    croiss = {p: (large.loc[der, p] / large.loc[un_an, p] - 1) * 100 for p in ["Los Angeles", "Long Beach"]}
    meilleur = "Los Angeles" if c.loc["Los Angeles", "score"] > c.loc["Long Beach", "score"] else "Long Beach"
    autre = "Long Beach" if meilleur == "Los Angeles" else "Los Angeles"
    raison = (f"CPPI {int(cppi['edition'].max())} : {meilleur} {int(c.loc[meilleur, 'rang'])}e contre "
              f"{autre} {int(c.loc[autre, 'rang'])}e sur {int(c.loc[meilleur, 'nb_ports_classes'])} ports. "
              f"Trafic sur un an ({der:%m/%Y}) : {meilleur} {nombre(croiss[meilleur], 1)} %, "
              f"{autre} {nombre(croiss[autre], 1)} %.")
    if croiss[autre] > croiss[meilleur]:
        raison += f" {autre} est le moins efficace ET celui dont le trafic augmente le plus : risque d'attente."
    recos.append((2, f"⚓ Choix du port : privilégier {meilleur}",
                  f"Pour les escales des deux prochaines semaines, demander en priorité des créneaux à "
                  f"{meilleur} ; garder {autre} en solution de repli.", raison))

# --- Règle 3 : file d'attente au mouillage (AIS) ---
if ais is not None:
    nb_mouillage = int((ais["statut"] == "au mouillage").sum())
    SEUIL_MOUILLAGE = 10   # seuil provisoire, en attendant l'historique (médiane 7 j + 2 écarts-types)
    if nb_mouillage >= SEUIL_MOUILLAGE:
        recos.append((1, "🟠 Attente au mouillage élevée",
                      "Ralentir les navires en approche pour arriver juste-à-temps plutôt que d'attendre "
                      "au mouillage (économie de carburant et d'émissions).",
                      f"{nb_mouillage} navires au mouillage (seuil provisoire : {SEUIL_MOUILLAGE})."))
    else:
        recos.append((4, "🟢 Pas de file d'attente notable",
                      "Maintenir les heures d'arrivée prévues.",
                      f"{nb_mouillage} navire(s) au mouillage lors de la dernière écoute AIS "
                      f"({age_texte(date_fichier(f'{LIVE}/ais_navires.csv'))}) ; seuil provisoire : {SEUIL_MOUILLAGE}."))

# --- Affichage : la plus prioritaire en premier, avec boutons Valider / Refuser ---
def enregistrer_decision(titre, decision):
    """Le 'retour' du cours (diapo 30) : on garde la décision prise pour l'évaluer plus tard."""
    ligne = pd.DataFrame([{"date_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                           "recommandation": titre, "decision": decision}])
    ligne.to_csv(FICHIER_DECISIONS, mode="a", index=False, header=not os.path.exists(FICHIER_DECISIONS))


if not recos:
    st.info("Aucune recommandation : données insuffisantes.")
for i, (prio, titre, action, raison) in enumerate(sorted(recos)):
    with st.container(border=True):
        col_txt, col_btn = st.columns([5, 1])
        with col_txt:
            st.markdown(f"**{titre}**  \n{action}")
            st.caption(f"Pourquoi ? {raison}")
        with col_btn:
            if st.button("✅ Valider", key=f"ok_{i}"):
                enregistrer_decision(titre, "validée")
                st.toast("Décision enregistrée : validée")
            if st.button("❌ Refuser", key=f"non_{i}"):
                enregistrer_decision(titre, "refusée")
                st.toast("Décision enregistrée : refusée")

if os.path.exists(FICHIER_DECISIONS):
    with st.expander("Historique des décisions (retour d'expérience)"):
        st.dataframe(pd.read_csv(FICHIER_DECISIONS).iloc[::-1], use_container_width=True, hide_index=True)