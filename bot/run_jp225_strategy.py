"""
JP225 PÄEVASISENE STRATEEGIA eilse USA liikumise põhjal.

Loogika: osta/müü JP225 Jaapani turu AVANEMISEL, sulge SULGEMISEL,
suund eilse SPX (või NAS100) close-to-close liikumise järgi.

Miks see on struktuurselt huvitav:
  - PÄEVASISENE => positsiooni ei hoita üle öö => EI MINGIT
    finantseerimist (5.42%/a, mis tappis kõik varasemad strateegiad)
  - Ainus kulu on spread
  - Avanemislünk (kus enamik seosest on) jäetakse TEADLIKULT kasutamata,
    kuna seda ei saa kaubelda — kaupleme ainult jääki

Range kontroll: täiskulud, parameetri-tundlikkus, poolte-test.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

jp = load("JP225")
spx = load("SPX")
nas = load("NAS100")
idx = jp.index.intersection(spx.index).intersection(nas.index)
jp, spx, nas = jp.reindex(idx), spx.reindex(idx), nas.reindex(idx)

# JP225 päevasisene tootlus (avamisest sulgemiseni) — SEDA kaupleme
jp_intraday = (jp["Close"] / jp["Open"] - 1)
jp_intraday = jp_intraday[jp_intraday.abs() < 0.25]

SPREAD_BP = 3.0    # JP225 ühesuunaline (research.py COST_BP)
ROUND_TRIP = 2 * SPREAD_BP / 10000.0

print("=" * 104)
print("A) PÕHIVARIANT: suund eilse signaali märgi järgi, positsioon kogu päev")
print("=" * 104)
print(f"{'signaal':16s} {'n':>5s} {'võit%':>7s} {'bruto/p':>9s} {'NETO/p':>9s} "
      f"{'CAGR':>8s} {'Sharpe':>7s}")
print("-" * 104)

for nimi, src in [("SPX", spx), ("NAS100", nas), ("SPX+NAS keskm", None)]:
    if src is None:
        sig_raw = ((spx["Close"]/spx["Close"].shift(1) - 1) +
                   (nas["Close"]/nas["Close"].shift(1) - 1)) / 2
    else:
        sig_raw = src["Close"]/src["Close"].shift(1) - 1
    w = np.sign(sig_raw).shift(1).reindex(jp_intraday.index).fillna(0.0)
    gross = w * jp_intraday
    net = gross - (w != 0).astype(float) * ROUND_TRIP
    n = int((w != 0).sum())
    wins = int((net > 0).sum())
    eq = (1 + net.fillna(0)).cumprod(); yrs = len(net)/252
    cagr = eq.iloc[-1]**(1/yrs) - 1 if eq.iloc[-1] > 0 else -1
    sh = net.mean()/net.std()*np.sqrt(252) if net.std() > 0 else 0
    print(f"{nimi:16s} {n:5d} {100*wins/max(n,1):6.1f}% {1e4*gross.mean():+8.2f}bp "
          f"{1e4*net.mean():+8.2f}bp {100*cagr:+7.1f}% {sh:+7.2f}")

print()
print("=" * 104)
print("B) LÄVENDIGA: kauple ainult kui eilne liikumine oli piisavalt suur")
print("=" * 104)
sig_raw = spx["Close"]/spx["Close"].shift(1) - 1
sig_vol = sig_raw.rolling(60).std()
zz = (sig_raw / sig_vol).shift(1).reindex(jp_intraday.index)
for thr in (0.0, 0.25, 0.5, 0.75, 1.0, 1.5):
    w = np.sign(zz) * (zz.abs() > thr)
    w = w.fillna(0.0)
    gross = w * jp_intraday
    net = gross - (w != 0).astype(float) * ROUND_TRIP
    n = int((w != 0).sum())
    if n < 50: continue
    eq = (1+net.fillna(0)).cumprod(); yrs = len(net)/252
    cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1] > 0 else -1
    sh = net.mean()/net.std()*np.sqrt(252) if net.std() > 0 else 0
    print(f"  |z| > {thr:.2f}  ({100*n/len(w):4.1f}% päevadest)  n={n:4d}  "
          f"NETO {1e4*net.mean():+6.2f}bp/p  CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}")

print()
print("=" * 104)
print("C) POOLTE-TEST (põhivariant, SPX signaal)")
print("=" * 104)
sig = np.sign(spx["Close"]/spx["Close"].shift(1) - 1).shift(1).reindex(jp_intraday.index).fillna(0.0)
mid = len(jp_intraday)//2
for lbl, sl in [("1. pool", slice(0, mid)), ("2. pool", slice(mid, None))]:
    w2 = sig.iloc[sl]; y2 = jp_intraday.iloc[sl]
    net = w2*y2 - (w2 != 0).astype(float)*ROUND_TRIP
    eq = (1+net.fillna(0)).cumprod(); yrs = len(net)/252
    cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1] > 0 else -1
    sh = net.mean()/net.std()*np.sqrt(252) if net.std() > 0 else 0
    print(f"  {lbl} ({y2.index[0].date()}..{y2.index[-1].date()}):  "
          f"CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}  NETO {1e4*net.mean():+6.2f}bp/p")

print()
print("=" * 104)
print("D) AASTATE KAUPA")
print("=" * 104)
net = sig*jp_intraday - (sig != 0).astype(float)*ROUND_TRIP
yearly = net.groupby(net.index.year).apply(lambda x: (1+x).prod()-1)
for y, v in yearly.items():
    bar = "#" * max(0, int(abs(v)*200))
    print(f"  {y}  {100*v:+7.2f}%  {'-' if v<0 else '+'}{bar}")
print(f"\n  Positiivseid aastaid: {(yearly>0).sum()}/{len(yearly)}")
