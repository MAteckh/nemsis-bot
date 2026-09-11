"""Kontrolli teise vestluse €200->€37477 vaidet MEIE OMA backtest.py-ga,
tapselt tema kirjeldatud mehaanikaga: LOT_TIERS astmed (mitte risk_based_lot),
TP=30/SL=45 fikseeritud, sama andmefail."""
import warnings; warnings.filterwarnings("ignore")
import copy
import numpy as np, pandas as pd
import backtest as bt
from config import GRID_CONFIG as BASE, INSTRUMENTS

h1 = bt.load_ohlc_csv("data/xauusd_h1_2024-08_2026-08.csv")
print(f"Andmed: {len(h1)} rida, {h1.index[0]} .. {h1.index[-1]}\n")

INST = {"trend_thresh": 0.3, "grid_size": 15.0}
cfg = copy.deepcopy(BASE)
cfg.update({"adx_filter": False, "risk_based_lot": False})   # tema kirjeldatud mehaanika
inst = copy.deepcopy(INSTRUMENTS["XAUUSD"]); inst.update(INST)

res = bt.simulate_gold_grid(h1, grid_cfg=cfg, instrument_cfg=inst, account_balance=200.0)
tr = res["trades"]
eq = res["equity"]

print(f"MEIE tulemus: {len(tr)} tehingut, loppekvivalent {eq.iloc[-1]:.2f}€")
print(f"  (tema vaide: 316 tehingut, 37477.26€)\n")

print("MEIE esimesed 10 tehingut:")
for t in tr[:10]:
    print(f"  {t.closed_at}  {t.reason:12s} pnl={t.pnl:+8.2f}")
print("\nMEIE viimased 10 tehingut:")
for t in tr[-10:]:
    print(f"  {t.closed_at}  {t.reason:12s} pnl={t.pnl:+8.2f}")

# lot iga tehingu juures - kontrolli kas kunagi joudis korgeimasse astmesse
lots = [t.lot for t in tr]
print(f"\nLot-vahemik meie jooksus: min {min(lots):.2f}  max {max(lots):.2f}")
print(f"Kas kunagi 0.13 (max aste) jouti: {'JAH' if max(lots) >= 0.13 else 'EI'}")
print(f"Kõrgeim equity kunagi saavutatud: {eq.max():.2f}€  ({eq.idxmax()})")
