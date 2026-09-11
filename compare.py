"""Lõplik õun-õuna võrdlus: kõik variandid samadel andmetel, sama kapitaliga, kulud sees."""
import copy
import warnings
warnings.filterwarnings("ignore")
import numpy as np
import pandas as pd
import backtest as bt
import strategies as S
from config import GRID_CONFIG as BASE, INSTRUMENTS

h1 = bt.load_ohlc_csv("data/xauusd_h1_2024-08_2026-08.csv")
n = len(h1); q = n // 4
quarters = [h1.iloc[i*q:(i+1)*q if i < 3 else n] for i in range(4)]
BAL, PV, COST = 200.0, 100.0, 0.40
c = h1["close"]
INST = {"trend_thresh": 0.3, "grid_size": 15.0}


def grid_run(df, over, bal=BAL):
    cfg = copy.deepcopy(BASE); cfg.update(over)
    inst = copy.deepcopy(INSTRUMENTS["XAUUSD"]); inst.update(INST)
    return bt.simulate_gold_grid(df, grid_cfg=cfg, instrument_cfg=inst, account_balance=bal)


def grid_stats(res, bal=BAL):
    tr = res["trades"]
    if not tr:
        return 0, 0.0, 0.0
    net = sum(t.pnl - COST * (t.lot / 0.01) for t in tr)
    eq = res["equity"]
    dd = (eq - eq.cummax()) / eq.cummax().replace(0, np.nan)
    return len(tr), net, 100 * float(dd.min())


def show(name, n_tr, net, dd, qprofit=None):
    ratio = net / abs(dd) if dd else float("inf")
    extra = f"  kvartalid {qprofit}/4" if qprofit is not None else ""
    print(f"{name:44s} n={n_tr:5d}  net={net:+9.2f} ({100*net/BAL:+7.1f}%)  dd={dd:7.1f}%  tulu/dd={ratio:6.1f}{extra}")


print("KÕIK: XAUUSD H1, 2024-08..2026-08 (2 aastat), algkapital 200 EUR, kulud 0.40$/0.01 lot sees\n")

# 1) praegune live-konfiguratsioon
cfg_live = {"adx_filter": False, "risk_based_lot": False}
r = grid_run(h1, cfg_live); nt, net, dd = grid_stats(r)
qp = sum(1 for qd in quarters if grid_stats(grid_run(qd, cfg_live))[1] > 0)
show("1. SINU PRAEGUNE LIVE (grid, risk-lot väljas)", nt, net, dd, qp)

# 2) sama + risk-põhine lot
cfg_risk = {"adx_filter": False, "risk_based_lot": True}
r = grid_run(h1, cfg_risk); nt, net, dd = grid_stats(r)
qp = sum(1 for qd in quarters if grid_stats(grid_run(qd, cfg_risk))[1] > 0)
show("2. + risk-põhine lot", nt, net, dd, qp)

# 3) dual engine
cfg_dual = {**cfg_risk, "dual_engine": True, "adx_switch": 35.0, "bo_lookback": 20,
            "bo_tp_atr": 3.0, "bo_sl_atr": 1.5}
r = grid_run(h1, cfg_dual); nt, net, dd = grid_stats(r)
qp = sum(1 for qd in quarters if grid_stats(grid_run(qd, cfg_dual))[1] > 0)
show("3. + breakout teine mootor", nt, net, dd, qp)

# 4) osta ja hoia
eq_h = BAL + (c - float(c.iloc[0])) * 0.01 * PV
dd_h = 100 * float(((eq_h - eq_h.cummax()) / eq_h.cummax()).min())
show("4. OSTA JA HOIA (0.01 lot)", 1, float(eq_h.iloc[-1]) - BAL, dd_h)

# 5) tuumik + ülekiht
res_s = S.simulate(h1, S.sig_donchian, {"lookback": 50}, BAL)
eq_s = res_s["equity"].reindex(c.index).ffill().fillna(BAL)
n_s = len(res_s["trades"])
eq_s = eq_s - COST * n_s * (np.arange(len(c)) / len(c))
combo = eq_h + (eq_s - BAL)
dd_c = 100 * float(((combo - combo.cummax()) / combo.cummax()).min())
show("5. HOIDMINE + donchian50 ülekiht", n_s + 1, float(combo.iloc[-1]) - BAL, dd_c)

print("\n--- KULUDE TUNDLIKKUS (variant 5, erinev spread+komisjon) ---")
for cost in [0.0, 0.20, 0.40, 0.80, 1.50]:
    eq_s2 = res_s["equity"].reindex(c.index).ffill().fillna(BAL) - cost * n_s * (np.arange(len(c)) / len(c))
    comb = eq_h + (eq_s2 - BAL)
    print(f"   kulu {cost:.2f}$/tehing: net={float(comb.iloc[-1]) - BAL:+9.2f}  (kulu kokku {cost*n_s:.0f}$)")

print("\n--- SAMA VARIANT 5 SUUREMA KONTOGA (drawdown %-des) ---")
for bal in [200.0, 1000.0, 5000.0]:
    scale = bal / 200.0
    eq_hb = bal + (c - float(c.iloc[0])) * 0.01 * PV * scale
    res_b = S.simulate(h1, S.sig_donchian, {"lookback": 50}, bal)
    eq_sb = res_b["equity"].reindex(c.index).ffill().fillna(bal)
    eq_sb = eq_sb - COST * len(res_b["trades"]) * (np.arange(len(c)) / len(c))
    cb = eq_hb + (eq_sb - bal)
    ddb = 100 * float(((cb - cb.cummax()) / cb.cummax()).min())
    netb = float(cb.iloc[-1]) - bal
    print(f"   algkapital {bal:>6.0f}: net={netb:+10.2f} ({100*netb/bal:+7.1f}%)  dd={ddb:7.1f}%")
print("\nDONE")
