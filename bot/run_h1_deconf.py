"""
KAS TIPPTULEMUSED ON PARIS SERV VOI LIHTSALT PIKK POSITSIOON?

Soel andis tipu: "SPX tund 17 PIKK, 24h hoida, +29bp". Aga soelas oli
SPX tund 13,14,15,16,17,18,19 KOIK plussis +21..+29bp. Kui IGA tund
tootab, ei ole tegu kellaaja efektiga — tegu on sellega, et indeks
tousis ja 24h pikk positsioon teenis.

OIGE VORDLUSALUS: mitte null, vaid SAMA INSTRUMENDI keskmine 24h
tootlus KOIGIL tundidel. Kellaaja efekt on olemas ainult siis, kui
uks tund on teistest OLULISELT parem.

Kontrollime ka:
  - Bonferroni ainult POSITIIVSE poole peal (t > +krit, mitte |t|)
  - kui palju tulemusest jaab jarele, kui lahutada pikk-positsiooni tulu
"""
import warnings; warnings.filterwarnings("ignore")
import math
import numpy as np, pandas as pd
import h1engine as E

OUT = "h1_deconf_tulemus.txt"
def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")
open(OUT, "w", encoding="utf-8").close()

df = pd.read_csv("data/h1_soel.csv")
N = len(df)
try:
    from scipy.stats import norm
    krit = float(norm.ppf(1 - 0.05 / (2 * N)))
except Exception:
    krit = 4.50

w("=" * 100)
w("1) BONFERRONI ÕIGESTI — ainult POSITIIVNE pool (t > +lävend)")
w("=" * 100)
w(f"   teste {N}, lävend t > +{krit:.2f}")
pos = df[df["tstat"] > krit]
neg = df[df["tstat"] < -krit]
w(f"   POSITIIVSEID läbijaid: {len(pos)}")
w(f"   NEGATIIVSEID läbijaid: {len(neg)}   <- need on kulu, mitte serv")
w("")
w("   Eelmine kokkuvõte ütles '3577 läbijat'. See oli |t|-filter, mis")
w("   loeb läbijaks ka statistiliselt kindlad KAOTAJAD. Õige arv on ülal.")

# ── 2) VORDLUSALUS: sama instrumendi keskmine samal horisondil ──
w("")
w("=" * 100)
w("2) DEKONFUNDEERIMINE — lahuta maha lihtsalt-ole-pikk tulu")
w("=" * 100)
D = E.lae_koik()
baas = {}
for sym, d in D.items():
    for k in (1, 4, 8, 24):
        y = E.tulevik(d, k).dropna()
        baas[(sym, k)] = float(y.mean())

df["baas"] = [baas.get((r["sym"], r["hor"]), np.nan) for _, r in df.iterrows()]
# signaali suund: kui signaal on valdavalt pikk, on vordlusalus +baas
df["yle"] = df["bruto"] - df["baas"]      # bruto = ilma kuludeta

w(f"   {'instr':8s} {'signaal':24s} {'h':>3s} {'bruto bp':>9s} "
  f"{'ole-pikk':>9s} {'ÜLE selle':>10s} {'NETO(kulud)':>12s}")
w("   " + "-" * 82)
tipp = df.sort_values("keskm", ascending=False).head(20)
for _, r in tipp.iterrows():
    w(f"   {r['sym']:8s} {r['nimi']:24s} {r['hor']:3d} {1e4*r['bruto']:+9.2f} "
      f"{1e4*r['baas']:+9.2f} {1e4*r['yle']:+10.2f} {1e4*r['keskm']:+12.2f}")

w("")
w("   Kui 'ÜLE selle' on ~0, siis signaal ei anna midagi juurde —")
w("   kogu tulu tuleb sellest, et instrument lihtsalt tõusis.")

# ── 3) KELLAAJA-EFEKT: kas ÜKS tund on teistest parem? ─────────
w("")
w("=" * 100)
w("3) KAS KELLAAJAL ON ÜLDSE EFEKTI? (kõigi 24 tunni hajuvus vs juhuslik)")
w("=" * 100)
w(f"   {'instr':8s} {'h':>3s} {'parim tund':>11s} {'parim bp':>9s} "
  f"{'keskm bp':>9s} {'std üle tundide':>16s} {'parim-keskm/std':>16s}")
w("   " + "-" * 78)
kell = df[(df["per"] == "A KELLAAEG") & (df["nimi"].str.contains("PIKK"))]
for (sym, hor), g in kell.groupby(["sym", "hor"]):
    if len(g) < 20 or hor != 24:
        continue
    v = g["bruto"].values * 1e4
    par = g.loc[g["bruto"].idxmax(), "nimi"]
    z = (v.max() - v.mean()) / v.std() if v.std() > 0 else 0
    w(f"   {sym:8s} {hor:3d} {par.split()[1]:>11s} {v.max():+9.2f} "
      f"{v.mean():+9.2f} {v.std():16.2f} {z:16.2f}")
w("")
w("   24 tunni maksimumi oodatav z-skoor puhtast mürast on ~+1.9.")
w("   Kui veerus 'parim-keskm/std' on ~1.9 või vähem, EI OLE kellaajal efekti.")

# ── 4) MIS JÄÄB, KUI NÕUDA MÕLEMA POOLE POSITIIVSUST + t>krit ──
w("")
w("=" * 100)
w("4) RANGE SÕEL: t > +lävend JA mõlemad pooled positiivsed JA ECN plussis")
w("=" * 100)
r4 = df[(df["tstat"] > krit) & (df["p1"] > 0) & (df["p2"] > 0) & (df["ecn"] > 0)]
w(f"   läbijaid: {len(r4)} / {N}")
if len(r4):
    w("")
    w(f"   {'instr':8s} {'perekond':16s} {'signaal':22s} {'h':>3s} {'teh/a':>7s} "
      f"{'keskm bp':>9s} {'ÜLE pikk':>9s} {'t':>7s}")
    w("   " + "-" * 90)
    for _, r in r4.sort_values("keskm", ascending=False).head(30).iterrows():
        w(f"   {r['sym']:8s} {r['per']:16s} {r['nimi']:22s} {r['hor']:3d} "
          f"{r['teh_a']:7.0f} {1e4*r['keskm']:+9.2f} {1e4*r['yle']:+9.2f} {r['tstat']:+7.2f}")

# ── 5) SAGEDUS: mida rohkem tehinguid, seda hullem? ────────────
w("")
w("=" * 100)
w("5) KAS 'PALJU VÄIKSEID TEHINGUID' ON ÜLDSE VÕIMALIK? (sageduse mõju)")
w("=" * 100)
df["ampel"] = pd.cut(df["teh_a"], [0, 100, 300, 700, 1500, 4000, 1e9],
                     labels=["<100/a", "100-300", "300-700", "700-1500",
                             "1500-4000", ">4000/a"])
w(f"   {'tehinguid aastas':>18s} {'teste':>7s} {'plussis':>9s} "
  f"{'keskm bp':>10s} {'parim bp':>10s} {'aasta kulu':>11s}")
w("   " + "-" * 72)
for amp, g in df.groupby("ampel", observed=True):
    kulu_a = 1e4 * (g["bruto"] - g["keskm"]).mean() * g["teh_a"].mean() / 1e4
    w(f"   {str(amp):>18s} {len(g):7d} {100*(g['keskm']>0).mean():8.1f}% "
      f"{1e4*g['keskm'].mean():+10.2f} {1e4*g['keskm'].max():+10.2f} "
      f"{100*kulu_a:10.1f}%")
w("")
w("   'aasta kulu' = kui palju tehingukulu sööb aastas, protsentides")
w("   kapitalist, selle sagedusega kauplemisel (1x võimendus).")
w("VALMIS")
