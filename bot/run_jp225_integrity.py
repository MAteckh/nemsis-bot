"""
JP225 tulemuse TERVIKLIKKUSE KONTROLL — kas see on paris voi andmeviga?

Kolm viisi, kuidas see tulemus voib olla vale:
  1. ANDMEVIGA: kui Open == eelmine Close, siis "paevasisene" sisaldab
     tegelikult LUNKA, mida ei saa kaubelda. (UK100 on just selline —
     93.4% lunkadest on tapselt null.)
  2. KONTSENTRATSIOON: kogu kasum tuleb 3-5 paevast (nt aug 2024 krahh).
  3. TULEVIKKUVAATAMINE: z-skoori vol-aken voi signaali nihe on vale.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open", "High", "Low", "Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

print("=" * 100)
print("1) ANDMETE TERVIKLIKKUS — kas Open on päris või koopia eelmisest Close'ist?")
print("=" * 100)
print(f"  {'sümbol':10s} {'n':>6s} {'Open==prevClose':>17s} {'|lünk| mediaan':>16s} "
      f"{'|päevasisene| med':>19s}")
print("  " + "-" * 72)
for sym in ("JP225", "SPX", "NAS100", "GER40", "UK100"):
    d = load(sym)
    gap = d["Open"] / d["Close"].shift(1) - 1
    intr = d["Close"] / d["Open"] - 1
    exact = float((gap.abs() < 1e-9).mean())
    print(f"  {sym:10s} {len(d):6d} {100*exact:16.1f}% {1e4*gap.abs().median():15.1f}bp "
          f"{1e4*intr.abs().median():18.1f}bp")

jp, spx = load("JP225"), load("SPX")
ix = jp.index.intersection(spx.index)
jp, spx = jp.reindex(ix), spx.reindex(ix)
y = jp["Close"] / jp["Open"] - 1
y = y[y.abs() < 0.25]
r = spx["Close"] / spx["Close"].shift(1) - 1
z = (r / r.rolling(60).std()).shift(1).reindex(y.index)
w = (np.sign(z) * (z.abs() > 1.00)).fillna(0.0)
RT = 6 / 10000.0
net = (w * y - (w != 0).astype(float) * RT).fillna(0.0)

mid = len(y) // 2
net2 = net.iloc[mid:]
w2 = w.iloc[mid:]
tr = net2[w2 != 0]


def sh(x):
    return x.mean() / x.std() * np.sqrt(252) if x.std() > 0 else 0.0


print()
print("=" * 100)
print("2) KONTSENTRATSIOON — kas kasum tuleb üksikutest päevadest? (2. pool, n=%d)" % len(tr))
print("=" * 100)
tot = (1 + net2).prod() - 1
print(f"  kogutootlus 2. poolel: {100*tot:+.1f}%")
srt = tr.sort_values()
print(f"\n  5 PARIMAT päeva:")
for t, v in srt.tail(5)[::-1].items():
    print(f"    {t.date()}  {100*v:+6.2f}%   (SPX eile {100*r.get(t - pd.Timedelta(days=0), np.nan):+.2f}%)")
print(f"  5 HALVIMAT päeva:")
for t, v in srt.head(5).items():
    print(f"    {t.date()}  {100*v:+6.2f}%")

print()
for k in (0, 1, 3, 5, 10, 20):
    if k == 0:
        keep = net2
    else:
        drop = set(srt.tail(k).index)
        keep = net2[~net2.index.isin(drop)]
    t2 = (1 + keep).prod() - 1
    yrs = len(keep) / 252
    cagr = (1 + t2) ** (1 / yrs) - 1
    print(f"  ilma {k:2d} parima päevata:  kogu {100*t2:+7.1f}%  CAGR {100*cagr:+6.1f}%  "
          f"Sharpe {sh(keep):+5.2f}")

print()
print("=" * 100)
print("3) AUG 2024 KRAHH — kas see üksik nädal kannab kogu tulemust?")
print("=" * 100)
crash = (net2.index >= "2024-07-25") & (net2.index <= "2024-08-15")
print(f"  krahhinädalate panus: {100*((1+net2[crash]).prod()-1):+.2f}%  ({int(crash.sum())} päeva)")
ex = net2[~crash]
yrs = len(ex) / 252
print(f"  ILMA nende päevadeta: kogu {100*((1+ex).prod()-1):+.1f}%  "
      f"CAGR {100*((1+ex).prod()**(1/yrs)-1):+.1f}%  Sharpe {sh(ex):+.2f}")

print()
print("=" * 100)
print("4) TULEVIKKUVAATAMISE KONTROLL — nihuta signaali 1 päev EDASI (peab lagunema)")
print("=" * 100)
for shift_extra, lbl in [(0, "õige (eilne SPX)"), (1, "1 päev VANEM"),
                         (-1, "1 päev UUEM = TULEVIK (peab olema parem, kui lekib)")]:
    zz = (r / r.rolling(60).std()).shift(1 + shift_extra).reindex(y.index)
    ww = (np.sign(zz) * (zz.abs() > 1.00)).fillna(0.0)
    nn = (ww * y - (ww != 0).astype(float) * RT).fillna(0.0).iloc[mid:]
    print(f"  {lbl:52s} Sharpe {sh(nn):+5.2f}  NETO {1e4*nn.mean():+5.2f}bp/p")

print()
print("=" * 100)
print("5) VOL-AKNA TUNDLIKKUS — kas 60 päeva on ainus, mis töötab?")
print("=" * 100)
for lb in (20, 40, 60, 90, 120, 250):
    zz = (r / r.rolling(lb).std()).shift(1).reindex(y.index)
    ww = (np.sign(zz) * (zz.abs() > 1.00)).fillna(0.0)
    nn = (ww * y - (ww != 0).astype(float) * RT).fillna(0.0)
    n2 = nn.iloc[mid:]
    print(f"  vol-aken {lb:3d}p  n={int((ww!=0).sum()):4d}  kogu Sharpe {sh(nn):+5.2f}  "
          f"2. pool Sharpe {sh(n2):+5.2f}")

print()
print("=" * 100)
print("6) NÄDALAPÄEVADE KAUPA (2. pool) — kas efekt on ühtlane?")
print("=" * 100)
dn = ["esmasp", "teisip", "kolmap", "neljap", "reede"]
for i in range(5):
    m = (w2 != 0) & (net2.index.dayofweek == i)
    if m.sum() < 10: continue
    sub = net2[m]
    print(f"  {dn[i]:8s} n={int(m.sum()):3d}  keskm {1e4*sub.mean():+6.1f}bp  "
          f"võit {100*(sub>0).mean():4.1f}%  Sharpe {sh(sub):+5.2f}")
