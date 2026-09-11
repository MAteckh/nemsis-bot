import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np
import research as R

px = R.load_panel(); rets = R.returns(px)

base = {
    "TS momentum 126p":           lambda: R.w_tsmom(px, rets, 126),
    "TS momentum ANSAMBEL":       lambda: R.w_tsmom_ensemble(px, rets),
    "Ristloikeline momentum k=5": lambda: R.w_xsmom(px, rets, 126, 5),
    "Donchian breakout 126p":     lambda: R.w_breakout(px, rets, 126),
    "Faber trend (pikk)":         lambda: R.w_long_only_trend(px, rets, 200),
    "Riskipariteet osta-ja-hoia": lambda: R.w_equal_long(px, rets),
}

print("=" * 118)
print("ETAPP 3 — KAIBE OHJAMINE: puhver + harvem umberkaalumine (koik vol-sihitud 15%)")
print("=" * 118)
for name, f in base.items():
    w0 = f()
    variants = {
        "paevane":        w0,
        "+puhver 0.2":    R.buffer(w0, 0.20),
        "+puhver 0.5":    R.buffer(w0, 0.50),
        "nadalane":       R.rebalance(w0, "W-FRI"),
        "kuine":          R.rebalance(w0, "M"),
        "kuine+puhver":   R.buffer(R.rebalance(w0, "M"), 0.30),
    }
    print(f"\n--- {name} ---")
    for vn, wv in variants.items():
        r = R.evaluate(R.vol_target(wv, rets, 0.15), rets, label=f"   {vn}")
        R.show(r)
