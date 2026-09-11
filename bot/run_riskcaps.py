"""Kas riskilaed lubavad KOIK NELI instrumenti alles jatta ja siiski ellu jaada?"""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R, strategies as S, portfolio_sim as PS
from config import GRID_CONFIG as G

SIG = {"donchian": S.sig_donchian, "bollinger_fade": S.sig_bollinger_reversion,
       "donchian_trend": S.sig_donchian_trendfiltered, "ts_momentum": S.sig_ts_momentum}

def load(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns = [c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

print("Ehitan signaalid ette (uks kord, siis korduvkasutus)...")
legs = []
for leg in G["portfolio_legs"]:
    nm = leg["name"]; df = load(nm)
    cfg = dict(G); cfg.update(leg.get("params", {}))
    sigs = PS.precompute_signals(df, SIG[leg["signal"]], cfg)
    legs.append(dict(name=nm, df=df, signals=sigs, pip_value=leg["pip_value"]))
    print(f"  {nm:8s} {len(sigs):4d} signaali")
rates = R.load_rates(pd.DatetimeIndex(sorted(set().union(*[set(l['df'].index) for l in legs]))))

def show(lbl, res, n_boot=0):
    t = res["taken"]; sk = res["skipped"]
    tot = sum(t.values())
    print(f"{lbl:46s} lopp {res['balance']:8.2f}EUR  maxDD {100*res['mdd']:6.1f}%  "
          f"tehinguid {tot:4d}  vahele {sum(sk.values()):4d}  "
          f"{'SURI' if res['dead'] else 'elas'}")
    return res

print()
print("=" * 122)
print("UHE KONTO SIMULATSIOON, 214 EUR, koik neli jalga alles")
print("=" * 122)
base = PS.run(legs, rates, 214.0, max_trade_risk=1.0, max_portfolio_risk=1.0)
show("ilma laeta (= praegune loogika)", base)

print()
print("  --- TEHINGUTASANDI LAGI: jata tehing vahele, kui 0.01 lot riskiks ule X% ---")
for cap in (0.25, 0.15, 0.10, 0.07, 0.05):
    r = PS.run(legs, rates, 214.0, max_trade_risk=cap, max_portfolio_risk=1.0)
    show(f"    max_trade_risk = {100*cap:4.1f}%", r)

print()
print("  --- PORTFELLI LAGI: koik avatud positsioonid kokku max X% ---")
for cap in (0.30, 0.20, 0.15, 0.10):
    r = PS.run(legs, rates, 214.0, max_trade_risk=1.0, max_portfolio_risk=cap)
    show(f"    max_portfolio_risk = {100*cap:4.1f}%", r)

print()
print("  --- TIHEDAM STOPP: sl_mult (vahendab riski otse, aga rohkem stoppe) ---")
for m in (1.0, 0.6, 0.4, 0.25):
    r = PS.run(legs, rates, 214.0, sl_mult=m)
    show(f"    sl_mult = {m:.2f}", r)

print()
print("  --- KOMBINATSIOON ---")
for tc, pc, sm in [(0.10, 0.20, 1.0), (0.07, 0.15, 1.0), (0.10, 0.20, 0.5), (0.05, 0.10, 0.5)]:
    r = PS.run(legs, rates, 214.0, max_trade_risk=tc, max_portfolio_risk=pc, sl_mult=sm)
    show(f"    tehing {100*tc:.0f}% / portfell {100*pc:.0f}% / stopp x{sm}", r)
    for nm in r["taken"]:
        print(f"          {nm:8s} tehtud {r['taken'][nm]:3d}  vahele {r['skipped'][nm]:4d}")
