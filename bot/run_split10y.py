import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R

DATA = R.DATA
syms = sorted(R.COST_BP)
print("=" * 122)
print("PAEVASISENE (Close/Open) vs OOINE (Open/PrevClose) — 10 aastat, 21 instrumenti")
print("=" * 122)
print(f"{'sumbol':9s} {'grupp':7s} {'n':>5s} | {'PAEVASISENE':>28s} | {'OOINE':>28s} | eelistus")
print(f"{'':9s} {'':7s} {'':>5s} | {'kokku%':>9s}{'bp/p':>8s}{'Sharpe':>8s} | {'kokku%':>9s}{'bp/p':>8s}{'Sharpe':>8s} |")
print("-" * 122)

rows = []
for s in syms:
    p = os.path.join(DATA, f"{s}_d.csv")
    if not os.path.exists(p): continue
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna(); d = d[(d[["Open","Close"]] > 0).all(axis=1)]
    if len(d) < 500: continue
    intr = (d["Close"] / d["Open"] - 1).replace([np.inf,-np.inf], np.nan).dropna()
    over = (d["Open"] / d["Close"].shift(1) - 1).replace([np.inf,-np.inf], np.nan).dropna()
    # kaitse vigaste baaride vastu
    intr = intr[intr.abs() < 0.25]; over = over[over.abs() < 0.25]
    def st(x): return (100*((1+x).prod()-1), 1e4*x.mean(),
                       x.mean()/x.std()*np.sqrt(252) if x.std()>0 else 0)
    ti, bi, si = st(intr); to, bo, so = st(over)
    pref = "PAEV" if si > so + 0.15 else ("OO" if so > si + 0.15 else "-")
    rows.append(dict(sym=s, grp=R.GROUP[s], n=len(intr), ti=ti, bi=bi, si=si,
                     to=to, bo=bo, so=so, pref=pref))
    print(f"{s:9s} {R.GROUP[s]:7s} {len(intr):5d} | {ti:+9.1f}{bi:+8.2f}{si:+8.2f} | "
          f"{to:+9.1f}{bo:+8.2f}{so:+8.2f} | {pref}")

df = pd.DataFrame(rows)
print("-" * 122)
print(f"  Paevasisene parem : {(df.pref=='PAEV').sum():2d} instrumenti  -> {list(df[df.pref=='PAEV'].sym)}")
print(f"  Ooine parem       : {(df.pref=='OO').sum():2d} instrumenti  -> {list(df[df.pref=='OO'].sym)}")
print(f"  Vahet pole        : {(df.pref=='-').sum():2d}")
print()
print("  GRUPITI (keskmine Sharpe):")
for g, sub in df.groupby("grp"):
    print(f"    {g:8s} paevasisene {sub.si.mean():+5.2f}   ooine {sub.so.mean():+5.2f}   "
          f"({len(sub)} instr)")
