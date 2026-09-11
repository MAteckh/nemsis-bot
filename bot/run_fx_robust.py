"""Kas EURUSD ts_momentum_120 ja USDJPY donchian_50 on stabiilsed
valikud voi juhuslikud onneleiud lahedaste parameetrite seas?"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R, strategies as S

BAL = 205.0
SPREAD = {"USDJPY": 0.15, "EURUSD": 0.12}
PV = {"USDJPY": 1000.0, "EURUSD": 100000.0}
NOTIONAL = {"USDJPY": lambda l,p: l*100000, "EURUSD": lambda l,p: l*100000*p}

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()

def net_result(d, rates, sym, fn, params, bal=BAL):
    res = S.simulate(d, fn, params, account_balance=bal, pip_value=PV[sym])
    tr = res["trades"]
    if not tr: return None
    gross = sum(t.pnl for t in tr)
    sp = sum(SPREAD[sym]*(t.lot/0.01) for t in tr)
    fin = 0.0
    for t in tr:
        days = max(1, (t.closed_at - t.opened_at).days)
        rr = float(rates.asof(t.opened_at))
        fin += NOTIONAL[sym](t.lot, t.entry) * (rr + 0.030) * days / 365.0
    return dict(n=len(tr), net=gross-sp-fin)

print("=" * 100)
print("A) PARAMEETRI-TUNDLIKKUS — kas naabrid on ka plussis, voi on see terav tipp?")
print("=" * 100)
d = load("EURUSD"); rates = R.load_rates(d.index)
print("EURUSD ts_momentum, lookback sweep:")
for lb in (60, 80, 100, 110, 120, 130, 140, 160, 180):
    r = net_result(d, rates, "EURUSD", S.sig_ts_momentum, {"mom_lookback": lb})
    if r: print(f"  lookback={lb:3d}  n={r['n']:3d}  NETO {r['net']:+8.2f}€")

d = load("USDJPY"); rates = R.load_rates(d.index)
print("\nUSDJPY donchian, lookback sweep:")
for lb in (10, 15, 20, 30, 40, 50, 60, 70, 80):
    r = net_result(d, rates, "USDJPY", S.sig_donchian, {"lookback": lb})
    if r: print(f"  lookback={lb:3d}  n={r['n']:3d}  NETO {r['net']:+8.2f}€")

print()
print("=" * 100)
print("B) POOLTEST — kas kasumlik molemal poolel eraldi, mitte ainult kokku?")
print("=" * 100)
for sym, fn, params in [("EURUSD", S.sig_ts_momentum, {"mom_lookback": 120}),
                        ("USDJPY", S.sig_donchian, {"lookback": 50})]:
    d = load(sym); rates = R.load_rates(d.index)
    mid = len(d) // 2
    h1, h2 = d.iloc[:mid+260], d.iloc[mid:]   # 260 baari kattuvus min_history jaoks
    r1 = net_result(h1, R.load_rates(h1.index), sym, fn, params)
    r2 = net_result(h2, R.load_rates(h2.index), sym, fn, params)
    full = net_result(d, rates, sym, fn, params)
    print(f"{sym} {fn.__name__} {params}:")
    print(f"  1. pool ({d.index[0].date()}..{d.index[mid].date()}):  "
          f"n={r1['n'] if r1 else 0:3d}  NETO {r1['net'] if r1 else 0:+8.2f}€")
    print(f"  2. pool ({d.index[mid].date()}..{d.index[-1].date()}):  "
          f"n={r2['n'] if r2 else 0:3d}  NETO {r2['net'] if r2 else 0:+8.2f}€")
    print(f"  KOKKU:                                       n={full['n']:3d}  NETO {full['net']:+8.2f}€\n")
