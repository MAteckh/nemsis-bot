"""
Walk-forward valideerimine: optimeeri parameetrid AINULT mineviku aknal,
testi järgmisel, veel nägemata aknal, seejärel liigu edasi. See on ainus
viis teada saada, kas parameetrite valimine mineviku pealt üldse töötab
tuleviku peal — kõik senised numbrid olid valitud samade andmete pealt.
"""
import copy
import pandas as pd
import backtest as bt
from config import GRID_CONFIG as BASE, INSTRUMENTS

h1 = bt.load_ohlc_csv("data/xauusd_h1_2024-08_2026-08.csv")

DUAL = {"adx_filter": False, "adx_max_filter": False, "risk_based_lot": True,
        "dual_engine": True, "bo_lookback": 20, "bo_tp_atr": 3.0, "bo_sl_atr": 1.5}
INST = {"trend_thresh": 0.3, "grid_size": 15.0}

# Optimeeritav parameetrite ruum (hoian väikesena, et walk-forward jõuaks joosta)
CANDIDATES = [
    {"adx_switch": 30.0},
    {"adx_switch": 35.0},
    {"adx_switch": 40.0},
    {"adx_switch": 45.0},
]


def run(df, over, bal=200.0):
    cfg = copy.deepcopy(BASE); cfg.update(DUAL); cfg.update(over)
    inst = copy.deepcopy(INSTRUMENTS["XAUUSD"]); inst.update(INST)
    return bt.simulate_gold_grid(df, grid_cfg=cfg, instrument_cfg=inst, account_balance=bal)


def score(df, over, bal=200.0):
    s = bt.compute_stats(run(df, over, bal), bal)
    if s.get("trades", 0) == 0:
        return -1e9, s
    # valime kasumi järgi, aga karistame sügavat drawdown'i
    return s["net_pnl"] + 2.0 * s["max_drawdown_pct"], s


months = pd.period_range(h1.index[0], h1.index[-1], freq="M")
IS_MONTHS, OOS_MONTHS = 12, 3

folds = []
start = 0
while start + IS_MONTHS + OOS_MONTHS <= len(months):
    is_m = months[start:start + IS_MONTHS]
    oos_m = months[start + IS_MONTHS:start + IS_MONTHS + OOS_MONTHS]
    folds.append((is_m, oos_m))
    start += OOS_MONTHS

print(f"Walk-forward: IS={IS_MONTHS}k, OOS={OOS_MONTHS}k, kokku {len(folds)} akent\n")

oos_total = 0.0
rows = []
for k, (is_m, oos_m) in enumerate(folds, 1):
    is_df = h1[(h1.index.to_period("M") >= is_m[0]) & (h1.index.to_period("M") <= is_m[-1])]
    oos_df = h1[(h1.index.to_period("M") >= oos_m[0]) & (h1.index.to_period("M") <= oos_m[-1])]
    best, best_score, best_stats = None, -1e18, None
    for cand in CANDIDATES:
        sc, st = score(is_df, cand)
        if sc > best_score:
            best, best_score, best_stats = cand, sc, st
    oos_stats = bt.compute_stats(run(oos_df, best), 200.0)
    oos_pnl = oos_stats.get("net_pnl", 0) if oos_stats.get("trades", 0) > 0 else 0.0
    oos_total += oos_pnl
    rows.append({"fold": k, "IS": f"{is_m[0]}..{is_m[-1]}", "OOS": f"{oos_m[0]}..{oos_m[-1]}",
                 "valitud": best["adx_switch"], "IS_pnl": round(best_stats["net_pnl"], 1),
                 "OOS_n": oos_stats.get("trades", 0), "OOS_pnl": round(oos_pnl, 1),
                 "OOS_dd": oos_stats.get("max_drawdown_pct", 0)})
    print(f"Fold {k}: IS {is_m[0]}..{is_m[-1]} -> valitud adx_switch={best['adx_switch']:.0f} "
          f"(IS pnl {best_stats['net_pnl']:+.1f}) | OOS {oos_m[0]}..{oos_m[-1]}: "
          f"n={oos_stats.get('trades',0)} pnl={oos_pnl:+.1f} dd={oos_stats.get('max_drawdown_pct',0):.1f}%", flush=True)

df_r = pd.DataFrame(rows)
print("\n=== KOKKUVÕTE ===")
print(df_r.to_string(index=False))
pos = sum(1 for r in rows if r["OOS_pnl"] > 0)
print(f"\nOOS kokku: {oos_total:+.2f}   kasumlikke OOS-aknaid: {pos}/{len(rows)}")

# Võrdlus: fikseeritud adx_switch=35 samadel OOS-akendel (ilma optimeerimiseta)
fixed_total = 0.0
fixed_pos = 0
for k, (is_m, oos_m) in enumerate(folds, 1):
    oos_df = h1[(h1.index.to_period("M") >= oos_m[0]) & (h1.index.to_period("M") <= oos_m[-1])]
    st = bt.compute_stats(run(oos_df, {"adx_switch": 35.0}), 200.0)
    p = st.get("net_pnl", 0) if st.get("trades", 0) > 0 else 0.0
    fixed_total += p
    fixed_pos += 1 if p > 0 else 0
print(f"Fikseeritud adx_switch=35 samadel akendel: {fixed_total:+.2f}  kasumlikke: {fixed_pos}/{len(folds)}")
print("\nDONE")
