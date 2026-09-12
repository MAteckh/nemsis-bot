"""
MUSTER 3: KRUPTO TRENDIJARGIMINE.

Miks just krupto 200EUR konto jaoks:
  - suurim volatiilsus (BTC paevane std ~3%, kuld ~1%)
  - vaikseim miinimum-positsioon brokerites (0.01 BTC ~ 500EUR, aga
    paljud pakuvad 0.001)
  - kaupleb 24/7 => nadalavahetuse lunki pole
Miinus: finantseerimine on krupto CFD-l KOIGE KALLIM (~15-20%/a).

Testime ausalt: trendijargimine erinevate akendega, PARIS kuludega.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

def load(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

# krupto CFD finantseerimine on jarsult kallim kui indeksitel
FIN = {"BTCUSD": 0.15/365, "ETHUSD": 0.18/365}

print("=" * 100)
print("KRÜPTO TRENDIJÄRGIMINE — päris kulude ja finantseerimisega")
print("=" * 100)
print(f"  {'sümbol':8s} {'strateegia':22s} {'CAGR':>9s} {'Sharpe':>8s} {'maxDD':>8s} "
      f"{'1.pool':>8s} {'2.pool':>8s}")
print("  " + "-" * 72)
for sym in ("BTCUSD", "ETHUSD"):
    d = load(sym)
    c = d["Close"]; r = c.pct_change().fillna(0.0)
    cost = 2*R.COST_BP[sym]/1e4
    fin = FIN[sym]
    yrs = len(r)/365
    bh = (c.iloc[-1]/c.iloc[0])**(1/yrs)-1
    bhdd = float(((1+r).cumprod()/(1+r).cumprod().cummax()-1).min())
    m = len(r)//2
    f = lambda x: (1+x).prod()**(365/len(x))-1
    print(f"  {sym:8s} {'OSTA-JA-HOIA':22s} {100*bh:8.1f}% {r.mean()/r.std()*np.sqrt(365):+8.2f} "
          f"{100*bhdd:7.1f}% {100*f(r.iloc[:m]):7.1f}% {100*f(r.iloc[m:]):7.1f}%")
    cands = []
    for name, w in [
        ("EMA 20/50 rist",      (c.ewm(span=20).mean() > c.ewm(span=50).mean()).astype(float)),
        ("EMA 50/200 rist",     (c.ewm(span=50).mean() > c.ewm(span=200).mean()).astype(float)),
        ("hind > 200p EMA",     (c > c.ewm(span=200).mean()).astype(float)),
        ("hind > 50p EMA",      (c > c.ewm(span=50).mean()).astype(float)),
        ("donchian 20",         (c >= c.rolling(20).max().shift(1)).astype(float).replace(0, np.nan).ffill().fillna(0)),
        ("donchian 50",         (c >= c.rolling(50).max().shift(1)).astype(float).replace(0, np.nan).ffill().fillna(0)),
        ("momentum 90p",        (c/c.shift(90) > 1).astype(float)),
        ("momentum 180p",       (c/c.shift(180) > 1).astype(float)),
    ]:
        w = w.shift(1).fillna(0.0)
        turn = w.diff().abs().fillna(0.0)
        net = w*r - turn*cost - w*fin
        eq = (1+net).cumprod()
        cg = eq.iloc[-1]**(365/len(net))-1 if eq.iloc[-1] > 0 else -1
        sh = net.mean()/net.std()*np.sqrt(365) if net.std() > 0 else 0
        dd = float((eq/eq.cummax()-1).min())
        print(f"  {'':8s} {name:22s} {100*cg:8.1f}% {sh:+8.2f} {100*dd:7.1f}% "
              f"{100*f(net.iloc[:m]):7.1f}% {100*f(net.iloc[m:]):7.1f}%")
    print()

print("=" * 100)
print("JÄRELDUS")
print("=" * 100)
print("  Kui ükski aktiivne strateegia ei löö OSTA-JA-HOIA rida, siis")
print("  parim krüpto 'strateegia' on lihtsalt osta ja istu — ja seda")
print("  saab teha ILMA botita ja ILMA finantseerimiskuluta (päris coin).")
