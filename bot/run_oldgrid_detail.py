import warnings; warnings.filterwarnings("ignore")
import copy
import numpy as np, pandas as pd
import backtest as bt
from config import GRID_CONFIG as BASE, INSTRUMENTS

h1 = bt.load_ohlc_csv("data/xauusd_h1_2024-08_2026-08.csv")
BAL, PV, COST = 200.0, 100.0, 0.40
INST = {"trend_thresh": 0.3, "grid_size": 15.0}

def grid_run(df, over, bal=BAL):
    cfg = copy.deepcopy(BASE); cfg.update(over)
    inst = copy.deepcopy(INSTRUMENTS["XAUUSD"]); inst.update(INST)
    return bt.simulate_gold_grid(df, grid_cfg=cfg, instrument_cfg=inst, account_balance=bal)

res = grid_run(h1, {"adx_filter": False, "risk_based_lot": True})
eq = res["equity"]
tr = res["trades"]

print(f"Periood: {eq.index[0]} .. {eq.index[-1]}")
print(f"Algkapital: {BAL}€   Loppekvivalent: {eq.iloc[-1]:.2f}€   Tehinguid: {len(tr)}\n")

# tapne madalaim punkt EUROdes (mitte %), ja millal
trough_idx = eq.idxmin()
peak_before = eq[:trough_idx].max()
print(f"Madalaim eKVIVALENT kogu perioodil: {eq.min():.2f}€  ({trough_idx})")
print(f"  (tipp enne seda: {peak_before:.2f}€, dd sellest tipust: {100*(eq.min()-peak_before)/peak_before:.1f}%)")
print(f"Kõrgeim ekvivalent kogu perioodil:  {eq.max():.2f}€  ({eq.idxmax()})")
print(f"Loppsaldo:                          {eq.iloc[-1]:.2f}€\n")

# aastate/kvartalite kaupa
eq_m = eq.resample("ME").last()
print("Ekvivalent kuu lõpus:")
for d, v in eq_m.items():
    print(f"  {d.date()}  {v:8.2f}€")

# hoiuaegade jaotus - kas positsioonid hoitakse uleoo, mis tahendaks
# finantseerimiskulu, mida see backtest EI arvesta
holds_h = [(t.closed_at - t.opened_at).total_seconds()/3600 for t in tr]
print(f"\nHoiuaeg (tunde): mediaan {np.median(holds_h):.1f}h  keskmine {np.mean(holds_h):.1f}h  "
      f"max {np.max(holds_h):.1f}h   ule-ooseid (>20h) tehinguid: {sum(1 for h in holds_h if h>20)}/{len(holds_h)}")

# kas backtest.py simulate_gold_grid arvestab oist finantseerimist?
import inspect
src = inspect.getsource(bt.simulate_gold_grid)
print(f"\n'financing'/'swap'/'intress' sõna backtest.py simulate_gold_grid koodis: "
      f"{'financing' in src or 'swap' in src or 'intress' in src.lower()}")
