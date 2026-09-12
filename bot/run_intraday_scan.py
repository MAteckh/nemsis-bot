"""
SUSTEMAATILINE OTSING: kui mitu paevasisest, finantseerimisvaba serva
on olemas koigi instrumentide vahel?

JP225 leid utles meile TUUBI, mitte lihtsalt uht instrumenti:
  - uks turg sulgeb, teine avab hiljem
  - positsioon avatakse avanemisel ja suletakse sulgemisel => EI OOTLE
    => finantseerimiskulu (5.42%/a) on NULL
  - lunk on kaubeldamatu, aga JAAK (Close/Open) on kaubeldav

See skript teeb sama koigi paaridega ja rakendab TAPSELT samu
kontrolle, mis JP225 puhul: andmete terviklikkus, |z| lavend,
poolte-test, OOS, Bonferroni.

VALISTATUD: sihtmargid, mille Open on vale (Open == eelmine Close).
"""
import warnings; warnings.filterwarnings("ignore")
import os, math, itertools
import numpy as np, pandas as pd
import research as R

SYMS = ["SPX", "NAS100", "GER40", "JP225", "UK100", "XAUUSD", "XAGUSD",
        "WTI", "NGAS", "COPPER", "US10Y", "VIX", "EURUSD", "USDJPY",
        "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "EURJPY",
        "BTCUSD", "ETHUSD"]

def load(sym):
    p = os.path.join(R.DATA, f"{sym}_d.csv")
    if not os.path.exists(p): return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"):
        if c not in d.columns: return None
        d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

D = {s: load(s) for s in SYMS}
D = {k: v for k, v in D.items() if v is not None and len(v) > 1200}

print("=" * 100)
print("1) ANDMETE TERVIKLIKKUS — kellel on PÄRIS Open? (ainult need saavad olla SIHTMÄRK)")
print("=" * 100)
ok_targets = []
print(f"  {'sümbol':10s} {'n':>6s} {'Open==prevClose':>17s} {'|päevasisene| med':>19s} {'otsus':>10s}")
print("  " + "-" * 68)
for s, d in sorted(D.items()):
    gap = (d["Open"]/d["Close"].shift(1) - 1)
    intr = (d["Close"]/d["Open"] - 1)
    frac = float((gap.abs() < 1e-9).mean())
    med = 1e4*intr.abs().median()
    good = frac < 0.05 and med > 5.0
    if good: ok_targets.append(s)
    print(f"  {s:10s} {len(d):6d} {100*frac:16.1f}% {med:18.1f}bp {'OK' if good else 'VÄLJA':>10s}")

print(f"\n  Kõlblikke sihtmärke: {len(ok_targets)}")
print("  " + ", ".join(ok_targets))


# ────────────────────────────────────────────────────────────────────
def sharpe(x):
    return float(x.mean()/x.std()*np.sqrt(252)) if len(x) > 5 and x.std() > 0 else 0.0

def build_pair(pred, tgt, thr=1.00, lb=60):
    p, t = D[pred], D[tgt]
    ix = p.index.intersection(t.index)
    if len(ix) < 1200: return None
    p, t = p.reindex(ix), t.reindex(ix)
    y = t["Close"]/t["Open"] - 1
    y = y[y.abs() < 0.25]
    r = p["Close"]/p["Close"].shift(1) - 1
    z = (r/r.rolling(lb).std()).shift(1).reindex(y.index)
    w = (np.sign(z)*(z.abs() > thr)).fillna(0.0)
    rt = 2*R.COST_BP.get(tgt, 5.0)/1e4
    net = (w*y - (w != 0).astype(float)*rt).fillna(0.0)
    return y, w, net

PAIRS = [(p, t) for p in sorted(D) for t in ok_targets if p != t]
print()
print("=" * 100)
print(f"2) TÄISSKANN — {len(PAIRS)} paari, |z|>1.00, täiskulud, sihtmärgi päevasisene osa")
print("=" * 100)

rows = []
for pred, tgt in PAIRS:
    b = build_pair(pred, tgt)
    if b is None: continue
    y, w, net = b
    n = int((w != 0).sum())
    if n < 150: continue
    mid = len(y)//2
    s_all, s1, s2 = sharpe(net), sharpe(net.iloc[:mid]), sharpe(net.iloc[mid:])
    # OOS: vali lavend 1. poolel, kauple 2. poolel
    best_t, best_s = None, -9e9
    for t_ in (0.5, 0.75, 1.0, 1.25, 1.5):
        bb = build_pair(pred, tgt, thr=t_)
        if bb is None: continue
        _, w_, net_ = bb
        if int((w_.iloc[:mid] != 0).sum()) < 80: continue
        s_ = sharpe(net_.iloc[:mid])
        if s_ > best_s: best_s, best_t = s_, t_
    s_oos = 0.0
    if best_t is not None:
        _, _, net_ = build_pair(pred, tgt, thr=best_t)
        s_oos = sharpe(net_.iloc[mid:])
    eq = (1+net).cumprod(); yrs = len(net)/252
    cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1] > 0 else -1
    rows.append(dict(pred=pred, tgt=tgt, n=n, sh=s_all, s1=s1, s2=s2,
                     oos=s_oos, is_thr=best_t, cagr=cagr))

df = pd.DataFrame(rows).sort_values("sh", ascending=False)
print(f"  testitud paare kokku: {len(df)}   Bonferroni-lävend: p < {0.05/max(len(df),1):.5f}")
print()
print(f"  {'ennustaja':10s} {'sihtmärk':10s} {'n':>5s} {'Sharpe':>8s} {'1.pool':>8s} "
      f"{'2.pool':>8s} {'OOS':>8s} {'CAGR':>8s}")
print("  " + "-" * 72)
for _, r_ in df.head(18).iterrows():
    print(f"  {r_['pred']:10s} {r_['tgt']:10s} {r_['n']:5d} {r_['sh']:+8.2f} "
          f"{r_['s1']:+8.2f} {r_['s2']:+8.2f} {r_['oos']:+8.2f} {100*r_['cagr']:+7.1f}%")

print()
print("=" * 100)
print("3) RANGE SÕELA LÄBIJAD")
print("=" * 100)
print("   Nõuded: Sharpe>0.5  JA  MÕLEMAD pooled>0  JA  OOS>0.5  JA  n>=150")
sel = df[(df.sh > 0.5) & (df.s1 > 0) & (df.s2 > 0) & (df.oos > 0.5) & (df.n >= 150)]
if len(sel) == 0:
    print("   MITTE ÜKSKI paar ei läbi.")
else:
    for _, r_ in sel.iterrows():
        print(f"   {r_['pred']:>8s} -> {r_['tgt']:<8s}  n={r_['n']:4d}  Sharpe {r_['sh']:+.2f}  "
              f"(1.pool {r_['s1']:+.2f} / 2.pool {r_['s2']:+.2f})  OOS {r_['oos']:+.2f}  "
              f"CAGR {100*r_['cagr']:+.1f}%")
print(f"\n   Läbijaid: {len(sel)} / {len(df)}")
print(f"   Juhuslikult oodatav (p=0.05): ~{0.05*len(df):.1f} paari")
df.to_csv("data/intraday_scan.csv", index=False)
