import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R

CLEAN = ["SPX", "NAS100", "GER40", "JP225"]
SPREAD_BP = {"SPX": 0.7, "NAS100": 0.7, "GER40": 1.0, "JP225": 1.5}   # uhesuunaline
DIV = R.DIVI

def series(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna()
    return d

rates = None
print("=" * 118)
print("OOINE DRIFT — kas ta elab ule PARIS kulud? (osta kassasulgemisel, muu kassaavamisel)")
print("=" * 118)
print(f"{'sumbol':8s} {'bruto bp/p':>11s} {'spread':>8s} {'finants':>8s} {'divid':>7s} "
      f"{'NETO bp/p':>10s} {'CAGR 1x':>9s} {'Sharpe':>7s} {'maxDD':>8s} {'+aastaid':>9s}")
print("-" * 118)

store = {}
for s in CLEAN:
    d = series(s)
    if rates is None or len(rates) != len(d):
        rates = R.load_rates(d.index)
    r_over = (d["Open"] / d["Close"].shift(1) - 1).dropna()
    r_over = r_over[r_over.abs() < 0.25]
    idx = r_over.index
    rt = R.load_rates(idx)
    # kulud: spread sisse+valja, uks oo finantseerimist (markup 3%), dividend krediit
    sp = 2 * SPREAD_BP[s] / 1e4
    fin = (rt + 0.030) / 365.0
    dv = DIV.get(s, 0.0) / 365.0
    net = r_over - sp - fin + dv
    eq = (1 + net).cumprod(); yrs = len(net)/252
    cagr = eq.iloc[-1]**(1/yrs) - 1
    dd = (eq/eq.cummax() - 1).min()
    sh = net.mean()/net.std()*np.sqrt(252)
    yy = net.groupby(net.index.year).apply(lambda x: (1+x).prod()-1)
    store[s] = net
    print(f"{s:8s} {1e4*r_over.mean():+11.2f} {1e4*sp:8.2f} {1e4*fin.mean():8.2f} "
          f"{1e4*dv:7.2f} {1e4*net.mean():+10.2f} {100*cagr:+8.1f}% {sh:+7.2f} "
          f"{100*dd:+7.1f}% {(yy>0).sum():4d}/{len(yy)}")

print()
print("=" * 118)
print("KoIK NELI KOOS (vordne raskus) — hajutamine")
print("=" * 118)
P = pd.DataFrame(store).dropna(how="all")
for lev, lbl in [(1.0,"1x"), (2.0,"2x"), (3.0,"3x")]:
    pr = P.mean(axis=1) * lev
    eq = (1+pr).cumprod(); yrs = len(pr)/252
    cagr = eq.iloc[-1]**(1/yrs)-1; dd = (eq/eq.cummax()-1).min()
    sh = pr.mean()/pr.std()*np.sqrt(252)
    yy = pr.groupby(pr.index.year).apply(lambda x:(1+x).prod()-1)
    print(f"  vaimendus {lbl}   CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}  "
          f"maxDD {100*dd:+6.1f}%  Calmar {cagr/abs(dd):5.2f}  +aastaid {(yy>0).sum()}/{len(yy)}")

pr = P.mean(axis=1)
print("\n  AASTATE KAUPA (1x):")
yy = pr.groupby(pr.index.year).apply(lambda x:(1+x).prod()-1)
for y, v in yy.items():
    print(f"    {y}  {100*v:+7.2f}%  {'#'*max(0,int(abs(v)*300))}")

print()
print("=" * 118)
print("ALAMPERIOODID (kas muster puseb?)")
print("=" * 118)
for a,b in [("2016-01-01","2019-12-31"),("2020-01-01","2022-12-31"),("2023-01-01","2026-12-31")]:
    x = pr[a:b]
    if len(x) < 100: continue
    eq=(1+x).cumprod(); yrs=len(x)/252
    print(f"  {a[:4]}-{b[:4]}  CAGR {100*(eq.iloc[-1]**(1/yrs)-1):+6.2f}%  "
          f"Sharpe {x.mean()/x.std()*np.sqrt(252):+5.2f}  "
          f"maxDD {100*(eq/eq.cummax()-1).min():+6.1f}%")
