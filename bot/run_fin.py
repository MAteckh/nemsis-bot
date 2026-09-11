import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np
import research as R

px = R.load_panel(); rets = R.returns(px); rates = R.load_rates(px.index)
print(f"Baasintress: keskmine {100*rates.mean():.2f}%  "
      f"2016-2021 {100*rates[:'2021-12-31'].mean():.2f}%  "
      f"2023-2026 {100*rates['2023-01-01':].mean():.2f}%\n")

cands = {
    "TS momentum 126p":          R.w_tsmom(px, rets, 126),
    "TS momentum ANSAMBEL":      R.w_tsmom_ensemble(px, rets),
    "Ristloikeline momentum":    R.w_xsmom(px, rets, 126, 5),
    "Donchian breakout 126p":    R.w_breakout(px, rets, 126),
    "Faber trend (pikk)":        R.w_long_only_trend(px, rets, 200),
    "Riskipariteet (pikk)":      R.w_equal_long(px, rets),
}

print("=" * 126)
print("ETAPP 4 — TAISARVESTUS: spread + OONE FINANTSEERIMINE (paris intressid) + dividendid")
print("=" * 126)
for mk in (0.020, 0.030):
    print(f"\n--- juurdehindlus {100*mk:.1f}% ---")
    for name, w in cands.items():
        wv = R.vol_target(w, rets, 0.15)
        R.show_full(R.evaluate_full(wv, rets, rates, markup=mk, label="  " + name))

print()
print("=" * 126)
print("ETAPP 5 — MIKS: pikk-ainult vs pikk-luhike finantseerimiskoormus")
print("=" * 126)
for name, w in cands.items():
    wv = R.vol_target(w, rets, 0.15)
    r = R.evaluate_full(wv, rets, rates, label=name)
    ls = "PIKK-AINULT" if r["net_exp"] > 0.9 * r["gross"] else "pikk+luhike"
    print(f"  {name:28s} {ls:12s} bruto {r['gross']:5.2f}x  neto {r['net_exp']:+6.2f}x  "
          f"-> finantseerimine {100*r['fin_drag']:+6.2f}%/a")
