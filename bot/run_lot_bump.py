"""Kui suurendada EURUSD/USDJPY lotti fikseeritult (mitte lasta
risk_based_lot'il seda 0.01 peale sundida), mida see tahendab
riski ja ajaloolise tulemuse mottes?"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R, strategies as S
from config import GRID_CONFIG as G

BAL = 205.0
SIG = {"donchian_trend": S.sig_donchian_trendfiltered, "ts_momentum": S.sig_ts_momentum}
SPREAD = {"USDJPY": 0.15, "EURUSD": 0.12}
NOTIONAL = {"USDJPY": lambda l,p: l*100000, "EURUSD": lambda l,p: l*100000*p}

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()

legs = [l for l in G["portfolio_legs"] if l["name"] in ("USDJPY","EURUSD")]
rates_cache = {}

print("=" * 108)
print(f"A) PRAEGUNE RISK 0.01 LOTIGA (konto {BAL:.0f}€) — keskmine ja praegune stopikaugus")
print("=" * 108)
for leg in legs:
    nm = leg["name"]; d = load(nm); cfg = dict(G); cfg.update(leg.get("params", {}))
    sigs = []
    for i in range(210, len(d)):
        w = d.iloc[max(0,i-260):i+1]
        s = SIG[leg["signal"]](w, cfg)
        if s: sigs.append(s[1])  # sl_dist
    pv = leg["pip_value"]
    mean_sl = np.mean(sigs); cur_sl = sigs[-1] if sigs else mean_sl
    print(f"  {nm:8s}  keskm sl_dist {mean_sl:.5f}  praegune (viimane signaal) {cur_sl:.5f}")
    for lot in (0.01, 0.02, 0.03, 0.05):
        risk = mean_sl * pv * lot
        print(f"      lot {lot:.2f}  ->  risk/tehing (keskm) {risk:6.2f}€  ({100*risk/BAL:5.1f}% kontost)")

print()
print("=" * 108)
print("B) 10 AASTA AJALOOLINE TULEMUS ERI LOT-TASEMETEL (fikseeritud lot, mitte risk_based)")
print("=" * 108)
for leg in legs:
    nm = leg["name"]; d = load(nm); cfg = dict(G); cfg.update(leg.get("params", {}))
    rates = R.load_rates(d.index)
    pv = leg["pip_value"]
    print(f"\n  --- {nm} ---")
    for lot in (0.01, 0.02, 0.03, 0.05):
        cfg2 = dict(cfg); cfg2["risk_pct"] = 1.0  # irrelevant, override lot manuaalselt allpool
        res = S.simulate(d, SIG[leg["signal"]], cfg2, account_balance=BAL, pip_value=pv)
        tr = res["trades"]
        if not tr:
            print(f"    lot {lot:.2f}  ei tehinguid"); continue
        gross = 0.0; fin = 0.0; sp = 0.0
        for t in tr:
            # skaleeri PNL ja kulud t.lot asemel meie testitava lot'iga
            scale = lot / t.lot if t.lot else 1.0
            gross += t.pnl * scale
            days = max(1, (t.closed_at - t.opened_at).days)
            rr = float(rates.asof(t.opened_at))
            fin += NOTIONAL[nm](lot, t.entry) * (rr + 0.030) * days / 365.0
            sp += SPREAD[nm] * (lot/0.01)
        net = gross - fin - sp
        risk_now = np.mean([abs(t.entry-t.sl) for t in tr]) * pv * lot
        print(f"    lot {lot:.2f}  {len(tr):3d} tehingut  bruto {gross:+9.2f}€  "
              f"fin -{fin:7.2f}€  spread -{sp:6.2f}€  NETO {net:+9.2f}€  "
              f"(keskm risk/tehing {100*risk_now/BAL:4.1f}% kontost)")
