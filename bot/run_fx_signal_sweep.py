"""Kas MOne signaal EURUSD/USDJPY jaoks uldse kulusid katab?

Jooksuta koik strategies.py signaaliperekonnad mollel instrumendil,
10 aastat, PARIS finantseerimise + spread'iga. Kui uksi neist ei
kata kulusid, on jareldus selge: nende instrumentide jaoks pole
meil hetkel head signaali - probleem pole yhes valikus, vaid selles,
et FX-i active-trading serv kaob kulude alla (nagu eile 21-instrumendi
testis leidsime).
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R, strategies as S

BAL = 205.0
LOT = 0.01
SPREAD = {"USDJPY": 0.15, "EURUSD": 0.12}
PV = {"USDJPY": 1000.0, "EURUSD": 100000.0}
NOTIONAL = {"USDJPY": lambda l,p: l*100000, "EURUSD": lambda l,p: l*100000*p}

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()

SIGNALS = {
    "donchian_20":          (S.sig_donchian, {"lookback": 20}),
    "donchian_50":          (S.sig_donchian, {"lookback": 50}),
    "donchian_trend_20_200":(S.sig_donchian_trendfiltered, {"lookback": 20, "ema_trend": 200}),
    "ema_cross_20_50":      (S.sig_ema_cross, {}),
    "ema_pullback_200_50":  (S.sig_ema_pullback, {"ema_trend": 200, "ema_pull": 50}),
    "ts_momentum_60":       (S.sig_ts_momentum, {"mom_lookback": 60}),
    "ts_momentum_120":      (S.sig_ts_momentum, {"mom_lookback": 120}),
    "vol_breakout":         (S.sig_vol_breakout, {}),
    "orb":                  (S.sig_orb, {}),
    "bollinger_fade":       (S.sig_bollinger_reversion, {}),
    "rsi_reversion":        (S.sig_rsi_reversion, {}),
}

def net_result(sym, fn, params):
    d = load(sym)
    rates = R.load_rates(d.index)
    res = S.simulate(d, fn, params, account_balance=BAL, pip_value=PV[sym])
    tr = res["trades"]
    if not tr:
        return None
    gross = sum(t.pnl for t in tr)
    sp = sum(SPREAD[sym]*(t.lot/0.01) for t in tr)
    fin = 0.0
    for t in tr:
        days = max(1, (t.closed_at - t.opened_at).days)
        rr = float(rates.asof(t.opened_at))
        fin += NOTIONAL[sym](t.lot, t.entry) * (rr + 0.030) * days / 365.0
    net = gross - sp - fin
    wins = sum(1 for t in tr if t.pnl > 0)
    return dict(n=len(tr), gross=gross, sp=sp, fin=fin, net=net,
               winrate=100*wins/len(tr))

for sym in ("EURUSD", "USDJPY"):
    print("=" * 100)
    print(f"{sym} — kõik signaaliperekonnad, 10a, päris finantseerimine + spread, 0.01 lot")
    print("=" * 100)
    rows = []
    for name, (fn, params) in SIGNALS.items():
        r = net_result(sym, fn, params)
        if r is None:
            print(f"  {name:24s}  0 tehingut")
            continue
        rows.append((name, r))
    rows.sort(key=lambda x: -x[1]["net"])
    for name, r in rows:
        flag = "  <-- ainuke plussis" if r["net"] > 0 and rows.index((name,r))==0 else ("  PLUSS" if r["net"]>0 else "")
        print(f"  {name:24s} n={r['n']:3d}  winrate {r['winrate']:5.1f}%  "
              f"bruto {r['gross']:+9.2f}  fin -{r['fin']:7.2f}  sp -{r['sp']:5.2f}  "
              f"NETO {r['net']:+9.2f}€{flag}")
    print()
