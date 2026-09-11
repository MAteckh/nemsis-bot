"""
JP225 lävendi-variandi (|z| > 1.00) ROBUSTSUSE-TEST.

run_jp225_strategy.py naitas:
  - lavendita variant: CAGR -2.8%, Sharpe -0.12  (labi kukkunud)
  - |z| > 1.00:        CAGR +10.1%, Sharpe +1.01 (puhas monotoonne plato)
AGA poolte-test ja aastate-test jooksutati AINULT lavendita variandil.

See skript teeb lavendi-variandiga sama, mis tappis EURUSD ts_momentum_120
ja riskilae-harja:
  1. Poolte-test lavendi-variandil
  2. Aastate kaupa lavendi-variandil
  3. OUT-OF-SAMPLE: vali lavend 1. poole pealt, kauple 2. poolel
  4. Sama NAS100 signaaliga (kas plato on signaalist soltumatu?)
  5. Rullituv 252p Sharpe (kas serv on puskiv voi pidev?)
  6. Kulude tundlikkus (mis spread'i juures serv kaob?)
  7. Platoo test MOLEMAL poolel eraldi
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

jp, spx, nas = load("JP225"), load("SPX"), load("NAS100")
idx = jp.index.intersection(spx.index).intersection(nas.index)
jp, spx, nas = jp.reindex(idx), spx.reindex(idx), nas.reindex(idx)

y = (jp["Close"] / jp["Open"] - 1)
y = y[y.abs() < 0.25]

SPREAD_BP = 3.0
ROUND_TRIP = 2 * SPREAD_BP / 10000.0


def zsig(src, lookback=60):
    r = src["Close"] / src["Close"].shift(1) - 1
    return (r / r.rolling(lookback).std()).shift(1).reindex(y.index)


def weights(z, thr):
    return (np.sign(z) * (z.abs() > thr)).fillna(0.0)


def stats(w, yy, rt=ROUND_TRIP):
    net = w * yy - (w != 0).astype(float) * rt
    net = net.fillna(0.0)
    n = int((w != 0).sum())
    if n == 0:
        return dict(n=0, cagr=0.0, sh=0.0, bp=0.0, wins=0.0, dd=0.0)
    eq = (1 + net).cumprod()
    yrs = len(net) / 252
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1
    sh = net.mean() / net.std() * np.sqrt(252) if net.std() > 0 else 0.0
    traded = net[w != 0]
    dd = float((eq / eq.cummax() - 1).min())
    return dict(n=n, cagr=cagr, sh=sh, bp=1e4 * net.mean(),
                wins=100 * (traded > 0).mean(), dd=dd)


z_spx = zsig(spx)
z_nas = zsig(nas)
THR = 1.00

print("=" * 100)
print("1) POOLTE-TEST — lävendi-variant |z| > 1.00, SPX signaal")
print("=" * 100)
mid = len(y) // 2
for lbl, sl in [("1. pool", slice(0, mid)), ("2. pool", slice(mid, None))]:
    w = weights(z_spx, THR).iloc[sl]
    s = stats(w, y.iloc[sl])
    print(f"  {lbl} ({y.index[sl][0].date()}..{y.index[sl][-1].date()}):  "
          f"n={s['n']:4d}  võit {s['wins']:4.1f}%  NETO {s['bp']:+6.2f}bp/p  "
          f"CAGR {100*s['cagr']:+6.1f}%  Sharpe {s['sh']:+5.2f}  DD {100*s['dd']:+6.1f}%")

print()
print("=" * 100)
print("2) AASTATE KAUPA — lävendi-variant |z| > 1.00")
print("=" * 100)
w_all = weights(z_spx, THR)
net_all = (w_all * y - (w_all != 0).astype(float) * ROUND_TRIP).fillna(0.0)
yearly = net_all.groupby(net_all.index.year).apply(lambda x: (1 + x).prod() - 1)
cnt = (w_all != 0).groupby(w_all.index.year).sum()
for yr, v in yearly.items():
    bar = "#" * max(0, int(abs(v) * 200))
    print(f"  {yr}  n={int(cnt[yr]):3d}  {100*v:+7.2f}%  {'-' if v<0 else '+'}{bar}")
print(f"\n  Positiivseid aastaid: {(yearly>0).sum()}/{len(yearly)}")

print()
print("=" * 100)
print("3) OUT-OF-SAMPLE — lävend valitud 1. poolel, kaubeldud 2. poolel")
print("=" * 100)
grid = [0.0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0]
best_thr, best_sh = None, -9e9
print("  1. poole (IS) tulemused:")
for t in grid:
    s = stats(weights(z_spx, t).iloc[:mid], y.iloc[:mid])
    if s["n"] < 50:
        continue
    print(f"    |z|>{t:.2f}  n={s['n']:4d}  CAGR {100*s['cagr']:+6.1f}%  Sharpe {s['sh']:+5.2f}")
    if s["sh"] > best_sh:
        best_sh, best_thr = s["sh"], t
print(f"\n  --> IS parim lävend: |z| > {best_thr:.2f} (Sharpe {best_sh:+.2f})")
oos = stats(weights(z_spx, best_thr).iloc[mid:], y.iloc[mid:])
print(f"  --> OOS (2. pool) SAMA lävendiga: n={oos['n']}  CAGR {100*oos['cagr']:+.1f}%  "
      f"Sharpe {oos['sh']:+.2f}  NETO {oos['bp']:+.2f}bp/p")

print()
print("=" * 100)
print("4) KAS PLATO ON SIGNAALIST SÕLTUMATU? (NAS100 ja SPX+NAS keskmine)")
print("=" * 100)
r_avg = ((spx["Close"] / spx["Close"].shift(1) - 1) +
         (nas["Close"] / nas["Close"].shift(1) - 1)) / 2
z_avg = (r_avg / r_avg.rolling(60).std()).shift(1).reindex(y.index)
print(f"  {'lävend':>8s} {'SPX Sharpe':>12s} {'NAS Sharpe':>12s} {'keskm Sharpe':>14s}")
print("  " + "-" * 50)
for t in grid:
    a, b, c = (stats(weights(zz, t), y) for zz in (z_spx, z_nas, z_avg))
    if min(a["n"], b["n"], c["n"]) < 50:
        continue
    print(f"  |z|>{t:.2f} {a['sh']:+12.2f} {b['sh']:+12.2f} {c['sh']:+14.2f}")

print()
print("=" * 100)
print("5) RULLITUV 252-PÄEVANE SHARPE — kas serv on pidev või puhkev?")
print("=" * 100)
traded_net = net_all.copy()
roll_sh = traded_net.rolling(252).mean() / traded_net.rolling(252).std() * np.sqrt(252)
roll_sh = roll_sh.dropna()
pos_frac = (roll_sh > 0).mean()
print(f"  aknaid: {len(roll_sh)}   positiivseid: {100*pos_frac:.1f}%   "
      f"min {roll_sh.min():+.2f}   mediaan {roll_sh.median():+.2f}   max {roll_sh.max():+.2f}")
for yr in sorted(set(roll_sh.index.year)):
    sub = roll_sh[roll_sh.index.year == yr]
    print(f"    {yr}: keskm rulliv Sharpe {sub.mean():+5.2f}  "
          f"(vahemik {sub.min():+5.2f} .. {sub.max():+5.2f})")

print()
print("=" * 100)
print("6) KULUDE TUNDLIKKUS — mis spread'i juures serv kaob? (|z|>1.00)")
print("=" * 100)
w = weights(z_spx, THR)
for sp in (1.0, 2.0, 3.0, 4.0, 5.0, 7.0, 10.0):
    s = stats(w, y, rt=2 * sp / 10000.0)
    print(f"  spread {sp:4.1f}bp/pool  NETO {s['bp']:+6.2f}bp/p  "
          f"CAGR {100*s['cagr']:+6.1f}%  Sharpe {s['sh']:+5.2f}")

print()
print("=" * 100)
print("7) PLATOO TEST MÕLEMAL POOLEL ERALDI (kas kuju säilib?)")
print("=" * 100)
print(f"  {'lävend':>8s} {'1. pool Sharpe':>16s} {'2. pool Sharpe':>16s} {'1.pool n':>10s} {'2.pool n':>10s}")
print("  " + "-" * 64)
for t in grid:
    a = stats(weights(z_spx, t).iloc[:mid], y.iloc[:mid])
    b = stats(weights(z_spx, t).iloc[mid:], y.iloc[mid:])
    if min(a["n"], b["n"]) < 30:
        continue
    print(f"  |z|>{t:.2f} {a['sh']:+16.2f} {b['sh']:+16.2f} {a['n']:10d} {b['n']:10d}")
