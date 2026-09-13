"""
v7.1 LOPPOTSUS — kontsentratsioon, multiple testing, 205 EUR, portfell.
"""
import warnings; warnings.filterwarnings("ignore")
import math
import numpy as np, pandas as pd
import h1engine as E

OUT = "v71_otsus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

S = pd.read_pickle("data/v71_signaalid.pkl")
MAJORID = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD"]
aastaid = (S["aeg"].max() - S["aeg"].min()).days / 365.25
def ncdf(x): return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))

w("=" * 96)
w("8) KONTSENTRATSIOON — kas üks paar vastutab enamiku kasumi eest?")
w("=" * 96)
kogu = float(S["bruto"].sum())
w(f"  {'paar':>8s} {'signaale':>10s} {'panus bruto':>13s} {'osa kogusummast':>17s}")
w("  " + "-" * 54)
panused = []
for sym in MAJORID:
    g = S[S["sym"] == sym]
    p = float(g["bruto"].sum())
    panused.append((sym, p))
    w(f"  {sym:>8s} {len(g):10d} {1e4*p:+12.1f}bp {100*p/kogu:16.1f}%")
pos = [(s, p) for s, p in panused if p > 0]
pos.sort(key=lambda x: -x[1])
w("  " + "-" * 54)
w(f"  positiivseid paare: {len(pos)}/7,  negatiivseid: {7-len(pos)}/7")
if pos:
    w(f"  suurim üksikpanus: {pos[0][0]} = {100*pos[0][1]/kogu:.1f}% kogusummast")
    w(f"  kolm suurimat kokku: {100*sum(p for _,p in pos[:3])/kogu:.1f}%")
# jata parim paar valja
ilma = S[S["sym"] != pos[0][0]] if pos else S
w(f"  ILMA parima paarita ({pos[0][0]}): bruto {1e4*float(ilma['bruto'].mean()):+.2f}bp "
  f"(oli {1e4*float(S['bruto'].mean()):+.2f}bp)")

w("")
w("=" * 96)
w("9) MULTIPLE TESTING — kui palju usku see number väärib?")
w("=" * 96)
t_kogu = float(S["bruto"].mean()/S["bruto"].std()*np.sqrt(len(S)))
osad = [S.iloc[:len(S)//3], S.iloc[len(S)//3:2*(len(S)//3)], S.iloc[2*(len(S)//3):]]
t_oos = float(osad[2]["bruto"].mean()/osad[2]["bruto"].std()*np.sqrt(len(osad[2])))
w(f"  kogu periood  t = {t_kogu:+.2f},  p(ühepoolne) = {1-ncdf(t_kogu):.4f}")
w(f"  FINAL OOS     t = {t_oos:+.2f},  p(ühepoolne) = {1-ncdf(t_oos):.4f}")
w("")
w("  KONTEKST: enne seda numbrit on tehtud ~11 500 v4-v6 testi + v7 sõel.")
w("  Selle filtri komponendid (trend, suht.tugevus, ATR-laienemine) VALITI")
w("  v7-s 6 kandidaadi seast tulemuse järgi. See on valik, mitte ennustus.")
w(f"  Bonferroni lävend ainult v7 6 komponendi peale: p < {0.05/6:.4f}")
w(f"  FINAL OOS p = {1-ncdf(t_oos):.4f}  =>  "
  f"{'läbib' if (1-ncdf(t_oos)) < 0.05/6 else 'EI LÄBI isegi seda leebet lävendit'}")

w("")
w("=" * 96)
w("10) PORTFELL — A/B/C/D/E, ainult majorid, järjestus signaalihetkel")
w("=" * 96)
# paevane tootlusmaatriks majoritel, sama signaal
DA = {s: E.lae(s) for s in MAJORID}
DA = {k: v for k, v in DA.items() if v is not None}
w(f"  {'variant':28s} {'paare':>6s} {'teh/a':>7s} {'BRUTO bp':>10s} "
  f"{'@0.8bp NETO':>12s} {'@2.0bp NETO':>12s}")
w("  " + "-" * 80)
def naita(nimi, g, npaare):
    if len(g) < 30:
        w(f"  {nimi:28s} {npaare:6d}   liiga vähe"); return
    b_ = float(g["bruto"].mean())
    w(f"  {nimi:28s} {npaare:6d} {len(g)/aastaid:7.0f} {1e4*b_:+10.2f} "
      f"{1e4*b_-0.8:+12.2f} {1e4*b_-2.0:+12.2f}")
# A) uksikud paarid — keskmine
kesk = np.mean([float(S[S["sym"]==s]["bruto"].mean()) for s in MAJORID
                if len(S[S["sym"]==s]) >= 20])
w(f"  {'A) üksikud paarid (keskm)':28s} {7:6d} {len(S)/aastaid/7:7.0f} "
  f"{1e4*kesk:+10.2f} {1e4*kesk-0.8:+12.2f} {1e4*kesk-2.0:+12.2f}")
# B) koik majorid koos
naita("B) kõik majorid koos", S, 7)
# C/D/E) TOP-N samal ajahetkel, jarjestus ATR-laienemise jargi (teada ette)
S2 = S.copy()
S2["paev"] = S2["aeg"].dt.floor("D")
for topn, nimi in ((1, "C) TOP-1 samal päeval"), (2, "D) TOP-2"), (3, "E) TOP-3")):
    # jarjesta sama paeva signaalid saabumisaja jargi (teada hetkel)
    g = S2.groupby("paev", group_keys=False).head(topn)
    naita(nimi, g, topn)

w("")
w("=" * 96)
w("11) 205 EUR PÄRIS TÄITMINE")
w("=" * 96)
JPY = {"USDJPY"}
sl_eur = {}
for sym in MAJORID:
    d = DA.get(sym)
    if d is None: continue
    a = float(E.atr(d, 14).dropna().median()); hind = float(d["close"].median())
    v = 1.5 * a * 1000.0
    if sym in JPY: v /= hind
    sl_eur[sym] = v
w(f"  {'kapital':>9s} {'risk%':>7s} {'lubatud':>9s} {'täidetavaid signaale':>22s} "
  f"{'paare':>7s}")
w("  " + "-" * 60)
S["sl"] = S["sym"].map(sl_eur)
for kap in (205, 500, 1000):
    for pct in (0.0025, 0.005, 0.0075, 0.01):
        mahub = S["sl"] <= kap * pct
        npaare = S[mahub]["sym"].nunique()
        w(f"  {kap:8d}€ {100*pct:6.2f}% {kap*pct:8.2f}€ "
          f"{int(mahub.sum()):8d}/{len(S):<6d} ({100*mahub.mean():4.1f}%) {npaare:6d}/7")
w("")
w(f"  keskmine SL 0.01 lotiga majoritel: {np.mean(list(sl_eur.values())):.2f}€")
w(f"  = {100*np.mean(list(sl_eur.values()))/205:.1f}% 205€ kontost")

w("")
w("=" * 96)
w("12) LÕPLIK OTSUS")
w("=" * 96)
kriteeriumid = [
    ("positiivne bruto (kogu periood)", 1e4*float(S["bruto"].mean()) > 0),
    ("positiivne neto realistlikul ECN-kulul (0.8bp)", 1e4*float(S["bruto"].mean()) > 0.8),
    ("positiivne FINAL OOS", 1e4*float(osad[2]["bruto"].mean()) > 0),
    ("FINAL OOS statistiliselt oluline (t>2)", t_oos > 2),
    ("TRAIN aken positiivne", float(osad[0]["bruto"].mean()) > 0),
    ("stabiilne üle majorite (>=5/7 plussis)", len(pos) >= 5),
    ("ükski paar ei anna >50% kasumist", (100*pos[0][1]/kogu < 50) if pos else False),
    ("mõistlik tehingute arv (>100/a)", len(S)/aastaid > 100),
    ("täidetav 205€ kontol 0.25% riskiga", bool((S["sl"] <= 205*0.0025).any())),
]
for nimi, ok in kriteeriumid:
    w(f"  [{'OK ' if ok else 'EI '}] {nimi}")
labib = sum(1 for _, ok in kriteeriumid if ok)
w("")
w(f"  Läbitud: {labib}/{len(kriteeriumid)}")
w("VALMIS")
