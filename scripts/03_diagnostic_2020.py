# Diagnostic : quel mois manque en 2020 ?
import io
import pandas as pd

with open("data/raw/la_2020.html", encoding="utf-8") as f:
    html = f.read()

t = max(pd.read_html(io.StringIO(html)), key=len)
# repr() montre les caractères cachés (espaces, étoiles...)
for i, valeur in enumerate(t[0]):
    print(i, repr(valeur), "| total :", t.iloc[i, 7])