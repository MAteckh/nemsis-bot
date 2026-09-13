"""
IMPULSI TEST — lopuanaluus parima kandidaadi peal.
Kulutundlikkus, paaripohine, portfell, 205 EUR, walk-forward,
robustsus, multiple testing.
"""
import warnings; warnings.filterwarnings("ignore")
import math, pickle
import numpy as np, pandas as pd
import h1engine as E

OUT = "impulss_lopp.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

with open("data/impulss_tulemused.pkl","rb") as f:
    P_ = pickle.load(f)
R, DATA = P_["R"], P_["DATA"]
MAJORID = ["EURUSD","GBPUSD","USDJPY","USDCHF","USDCAD","AUDUSD","NZDUSD"]
def ncdf(x): return 0.5*(1.0+math.erf(x/math.sqrt(2.0)))

best = R.sort_values("bruto", ascending=False).iloc[0]
kl = (best["var"], best["kin"], best["hoia"], best["stop"], best["suund"])
G = DATA[kl].copy()
aastaid = (G["aeg"].max() - G["aeg"].min()).days / 365.25

w("=" * 100)
w("PARIM 108-st VARIANDIST (valik = valikunihe, vt multiple testing)")
w("=" * 100)
w(f"  variant {best['var']} | kinnitus {best['kin']} | hoia {best['hoia']} baari | "
  f"stopp {best['stop'] or 'puudub'} | suund {best['suund']}")
w(f"  tehinguid {len(G)}  ({len(G)/aastaid:.0f}/aastas)  paare {G['sym'].nunique()}")
w(f"  BRUTO {1e4*float(G['bruto'].mean()):+.2f}bp   NETO {1e4*float(G['neto'].mean()):+.2f}bp")
w(f"  t = {best['t']:+.2f},  p(uhepoolne) = {1-ncdf(best['t']):.4f}")

# ── KULUTUNDLIKKUS ─────────────────────────────────────────────
w("")
w("=" * 100)
w("1) KULUTUNDLIKKUS (kasutaja punkt 8)")
w("=" * 100)
b = float(G["bruto"].mean()); n_a = len(G)/aastaid
w(f"  {'round-trip kulu':>17s} {'NETO bp':>10s} {'aastas %':>11s} {'hinnang':>10s}")
w("  " + "-" * 52)
for kulu in (0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0):
    neto = b - kulu/1e4
    w(f"  {kulu:>16.1f}bp {1e4*neto:+10.2f} {100*neto*n_a:+10.2f}% "
      f"{'PLUSS' if neto>0 else 'miinus':>10s}")
w("")
w(f"  MURDEPUNKT: {1e4*b:.2f} bp round-trip = {1e4*b/2:.2f} bp poole kohta")
w("  Vordluseks: BlackBull ECN Prime ~0.7-0.9bp, Standard ~1.6-2.4bp")
w("  eeldatud kulu selles testis: majorid 2.0-3.6bp, ristpaarid 4.4bp")

# ── PAARIPOHINE ────────────────────────────────────────────────
w("")
w("=" * 100)
w("2) PAARIPOHINE (kasutaja punkt 12) — kas uks paar teeb kogu kasumi?")
w("=" * 100)
pp = G.groupby("sym").agg(n=("bruto","size"), bruto=("bruto","mean"),
                          summa=("bruto","sum"), neto=("neto","mean"))
pp = pp.sort_values("summa", ascending=False)
kogu = float(pp["summa"].sum())
w(f"  {'paar':>8s} {'tehinguid':>10s} {'BRUTO bp':>10s} {'NETO bp':>9s} {'osa summast':>13s}")
w("  " + "-" * 56)
for s_, r in pp.iterrows():
    w(f"  {s_:>8s} {int(r['n']):10d} {1e4*r['bruto']:+10.2f} {1e4*r['neto']:+9.2f} "
      f"{100*r['summa']/kogu:12.1f}%")
plussis = int((pp["bruto"] > 0).sum())
w("  " + "-" * 56)
w(f"  plussis {plussis}/{len(pp)} paari,  mediaan {1e4*float(pp['bruto'].median()):+.2f}bp")
w(f"  TOP-1 osa: {100*pp['summa'].iloc[0]/kogu:.1f}%   "
  f"TOP-2 kokku: {100*pp['summa'].iloc[:2].sum()/kogu:.1f}%")
ilma1 = G[G["sym"] != pp.index[0]]
ilma2 = G[~G["sym"].isin(pp.index[:2])]
w(f"  ILMA parima paarita:  BRUTO {1e4*float(ilma1['bruto'].mean()):+.2f}bp "
  f"(oli {1e4*b:+.2f})")
w(f"  ILMA kahe parimata:   BRUTO {1e4*float(ilma2['bruto'].mean()):+.2f}bp")
maj = G[G["sym"].isin(MAJORID)]
w(f"  AINULT majorid:       BRUTO {1e4*float(maj['bruto'].mean()):+.2f}bp "
  f"({len(maj)} tehingut)")

# ── WALK-FORWARD ───────────────────────────────────────────────
w("")
w("=" * 100)
w("3) WALK-FORWARD (kasutaja punkt 11)")
w("=" * 100)
G = G.sort_values("aeg").reset_index(drop=True)
n3 = len(G)//3
osad = [("TRAIN", G.iloc[:n3]), ("VALIDATION", G.iloc[n3:2*n3]), ("FINAL OOS", G.iloc[2*n3:])]
w(f"  {'aken':>12s} {'periood':>26s} {'tehinguid':>10s} {'BRUTO bp':>10s} {'t':>7s}")
w("  " + "-" * 70)
for nimi, g in osad:
    t_ = float(g["bruto"].mean()/g["bruto"].std()*np.sqrt(len(g))) if g["bruto"].std()>0 else 0
    w(f"  {nimi:>12s} {str(g['aeg'].min().date())+'..'+str(g['aeg'].max().date()):>26s} "
      f"{len(g):10d} {1e4*float(g['bruto'].mean()):+10.2f} {t_:+7.2f}")
oos = osad[2][1]
t_oos = float(oos["bruto"].mean()/oos["bruto"].std()*np.sqrt(len(oos))) if oos["bruto"].std()>0 else 0

# ── AASTATE KAUPA ──────────────────────────────────────────────
w("")
w("  Kalendriaastate kaupa (kasutaja punkt 12E):")
w(f"  {'aasta':>7s} {'tehinguid':>10s} {'BRUTO bp':>10s}")
w("  " + "-" * 30)
for a_, g in G.groupby(G["aeg"].dt.year):
    if len(g) < 50: continue
    w(f"  {a_:7d} {len(g):10d} {1e4*float(g['bruto'].mean()):+10.2f}")

# ── PORTFELL ───────────────────────────────────────────────────
w("")
w("=" * 100)
w("4) PORTFELL (kasutaja punkt 9) — max 3 positsiooni, valuuta-exposure piiratud")
w("=" * 100)
G["paev"] = G["aeg"].dt.floor("D")
G["tund"] = G["aeg"].dt.floor("h")
def val_exp(sym, dirn):
    b_, q_ = sym[:3], sym[3:]
    return {b_: dirn, q_: -dirn}
valitud = []
for t_, grp in G.groupby("tund"):
    g = grp.sort_values("tug", ascending=False)
    lahti, exp = [], {}
    for _, r in g.iterrows():
        if len(lahti) >= 3: break
        e = val_exp(r["sym"], r["dir"])
        # ara kogu liiga palju sama valuuta exposure'it
        if any(abs(exp.get(k, 0) + v) > 2 for k, v in e.items()): continue
        for k, v in e.items(): exp[k] = exp.get(k, 0) + v
        lahti.append(r)
    valitud.extend(lahti)
PF = pd.DataFrame(valitud)
w(f"  signaale kokku {len(G)}  ->  portfelli piirangute jarel {len(PF)} "
  f"({100*len(PF)/len(G):.1f}%)")
w(f"  {'variant':>28s} {'tehinguid':>10s} {'BRUTO bp':>10s} {'NETO bp':>9s}")
w("  " + "-" * 60)
w(f"  {'koik signaalid':>28s} {len(G):10d} {1e4*b:+10.2f} "
  f"{1e4*float(G['neto'].mean()):+9.2f}")
w(f"  {'portfell (max 3, exposure)':>28s} {len(PF):10d} "
  f"{1e4*float(PF['bruto'].mean()):+10.2f} {1e4*float(PF['neto'].mean()):+9.2f}")
for topn in (1, 2, 3):
    g = G.sort_values(["tund","tug"], ascending=[True,False]).groupby("tund").head(topn)
    w(f"  {'TOP-'+str(topn)+' tugevuse jargi':>28s} {len(g):10d} "
      f"{1e4*float(g['bruto'].mean()):+10.2f} {1e4*float(g['neto'].mean()):+9.2f}")

# ── 205 EUR ────────────────────────────────────────────────────
w("")
w("=" * 100)
w("5) 205 EUR TAITMINE (kasutaja punkt 10)")
w("=" * 100)
D = {s: E.lae(s) for s in G["sym"].unique()}
JPY = {"USDJPY","EURJPY","GBPJPY","AUDJPY","NZDJPY","CADJPY","CHFJPY"}
stop_atr = best["stop"] or 1.0
sl_eur = {}
for sym, d in D.items():
    if d is None: continue
    from impulss_engine import atr_shift
    a_ = float(atr_shift(d).dropna().median()); hind = float(d["close"].median())
    v = stop_atr * a_ * 1000.0
    if sym in JPY: v /= hind
    sl_eur[sym] = v
G["sl"] = G["sym"].map(sl_eur)
w(f"  SL = {stop_atr} x ATR, 0.01 lot = 1000 uhikut")
w(f"  keskmine SL 0.01 lotiga: {np.nanmean(list(sl_eur.values())):.2f} EUR "
  f"= {100*np.nanmean(list(sl_eur.values()))/205:.1f}% 205 EUR kontost")
w("")
w(f"  {'kapital':>9s} {'risk%':>7s} {'lubatud':>9s} {'taidetavaid':>20s} {'paare':>8s}")
w("  " + "-" * 58)
for kap in (205, 500, 1000):
    for pct in (0.0025, 0.005):
        lub = kap*pct
        mahub = G["sl"] <= lub
        w(f"  {kap:8d}E {100*pct:6.2f}% {lub:8.2f}E "
          f"{int(mahub.sum()):9d}/{len(G):<7d} ({100*mahub.mean():5.1f}%) "
          f"{G[mahub]['sym'].nunique():5d}/{G['sym'].nunique()}")
tegelik = 100*np.nanmean(list(sl_eur.values()))/205
w("")
w(f"  Tegelik risk miinimum-lotiga 205 EUR kontol: keskm {tegelik:.1f}%, "
  f"max {100*max(sl_eur.values())/205:.1f}%")

# ── MULTIPLE TESTING ───────────────────────────────────────────
w("")
w("=" * 100)
w("6) MULTIPLE TESTING (kasutaja punkt 13)")
w("=" * 100)
N = len(R)
p_best = 1 - ncdf(best["t"])
w(f"  variante testitud: {N}")
w(f"  parima t = {best['t']:+.2f}, p(uhepoolne) = {p_best:.4f}")
w(f"  Bonferroni lavend {N} testi peale: p < {0.05/N:.5f}")
w(f"  => {'labib' if p_best < 0.05/N else 'EI LABI'}")
w("")
pos = R[R["t"] > 2]
w(f"  variante t>2: {len(pos)}/{N}  (juhuslikult oodatav ~{0.0228*N:.1f})")
w(f"  variante t<-2: {int((R['t']<-2).sum())}/{N}")
w(f"  keskmine t: {float(R['t'].mean()):+.2f}")
w("")
w(f"  FINAL OOS t = {t_oos:+.2f}, p = {1-ncdf(t_oos):.4f}")

# ── PASS/FAIL ──────────────────────────────────────────────────
w("")
w("=" * 100)
w("7) PASS / FAIL (kasutaja punkt 14)")
w("=" * 100)
kr = [
 ("1. positiivne NETO ootus realistlike kuludega", float(G["neto"].mean()) > 0),
 ("2. positiivne FINAL OOS", float(oos["bruto"].mean()) > 0),
 ("3. FINAL OOS ei soltu uhest paarist", False),
 ("4. parima paari eemaldamine ei havita serva",
     float(ilma1["bruto"].mean()) > 0.5*b),
 ("5. serv talub realistlikke kulusid", 1e4*b > 2.0),
 ("6. piisavalt tehinguid", len(G) > 500),
 ("7. ei noia >0.50% riski tehingu kohta", tegelik <= 0.5),
 ("8. oluline osa signaale taidetav 205 EUR kontol",
     float((G["sl"] <= 205*0.005).mean()) > 0.2),
 ("9. tulemus ei piirdu uhe luhikese perioodiga",
     all(float(g["bruto"].mean()) > 0 for _, g in osad)),
 ("10. labib multiple-testing korrektsiooni", p_best < 0.05/N),
]
for nimi, ok in kr:
    w(f"  [{'OK ' if ok else 'EI '}] {nimi}")
w("")
w(f"  LABITUD: {sum(1 for _,o in kr if o)}/{len(kr)}")
w("VALMIS")
