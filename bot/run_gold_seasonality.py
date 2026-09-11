"""
Kulla FUNDAMENTAALNE (mitte tehniline) hooajalisus: fusiline noudlus
on tsukliline - India pulma/festivalihooaeg (sept-dets) ja Hiina
uusaasta (jaan-veebr) toovad reaalset ostusurvet. See on erinev
koigist varem testitud tehnilistest signaalidest.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

d = pd.read_csv(os.path.join(R.DATA, "XAUUSD_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
d = d[~d.index.duplicated(keep="last")]
c = pd.to_numeric(d["Close"], errors="coerce").dropna()
r = c.pct_change()

print("=" * 100)
print("A) KUU-KAUPA KESKMINE TOOTLUS, 10 AASTAT (kas mone kuu efekt on tugev ja stabiilne?)")
print("=" * 100)
by_month = r.groupby(r.index.month)
for m in range(1, 13):
    vals = by_month.get_group(m) if m in by_month.groups else pd.Series(dtype=float)
    if len(vals) < 10: continue
    tot = 1e4*vals.mean()
    sh = vals.mean()/vals.std()*np.sqrt(252) if vals.std()>0 else 0
    pos_years = (vals.groupby(vals.index.year).apply(lambda x: (1+x).prod()-1) > 0).sum()
    n_years = vals.index.year.nunique()
    marker = " <-- India/Hiina hooaeg" if m in (9,10,11,12,1,2) else ""
    print(f"  {m:2d}  keskm {tot:+6.1f}bp/p  Sharpe {sh:+5.2f}  "
          f"positiivseid aastaid {pos_years}/{n_years}{marker}")

print()
print("=" * 100)
print("B) STRATEEGIA: OSTA AINULT HOOAJALISTEL KUUDEL (sept-veebr), muidu valjas")
print("=" * 100)
MK = 0.030
def cost(w):
    turn = (w-w.shift(1)).abs().fillna(0.0)
    sp = turn * 1.5/10000.0
    rate = R.load_rates(w.index).reindex(w.index).ffill()
    fin = w.shift(1).clip(lower=0)*rate/252.0 + w.shift(1).abs()*MK/252.0
    return sp.fillna(0.0), fin.fillna(0.0)

for months in [(9,10,11,12,1,2), (10,11,12), (9,10,11,12), (1,2)]:
    sig = r.index.month.isin(months).astype(float)
    w = pd.Series(sig, index=r.index).shift(1).fillna(0.0)
    sp, fin = cost(w)
    net = w*r - sp - fin
    eq=(1+net.fillna(0)).cumprod(); yrs=len(net)/252
    cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1]>0 else -1
    sh = net.mean()/net.std()*np.sqrt(252) if net.std()>0 else 0
    bh = (1+r.fillna(0)).cumprod(); bh_cagr = bh.iloc[-1]**(1/yrs)-1
    print(f"  kuud {str(months):24s}  ({100*sig.mean():4.1f}% ajast)  "
          f"CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}  (osta-hoia vordluseks {100*bh_cagr:+6.1f}%)")

print()
print("=" * 100)
print("C) POOLTE-TEST parima variandi peale")
print("=" * 100)
months = (9,10,11,12,1,2)
sig = r.index.month.isin(months).astype(float)
w = pd.Series(sig, index=r.index).shift(1).fillna(0.0)
mid = len(d)//2
for lbl, sl in [("1. pool", slice(0,mid)), ("2. pool", slice(mid,None))]:
    w2, r2 = w.iloc[sl], r.iloc[sl]
    sp, fin = cost(w2)
    net = w2*r2 - sp - fin
    eq=(1+net.fillna(0)).cumprod(); yrs=len(net)/252
    cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1]>0 else -1
    print(f"  {lbl} ({r2.index[0].date()}..{r2.index[-1].date()}):  CAGR {100*cagr:+6.1f}%")
