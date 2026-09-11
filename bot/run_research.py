import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np
import research as R

px = R.load_panel()
rets = R.returns(px)
print(f"Paneel: {px.shape[1]} instrumenti, {len(px)} päeva, "
      f"{px.index[0].date()} .. {px.index[-1].date()}\n")

BH_G = R.evaluate(pd.DataFrame(1.0, index=px.index, columns=px.columns)[["XAUUSD"]]
                  .reindex(columns=px.columns).fillna(0.0), rets, label="OSTA-JA-HOIA kuld")
BH_S = R.evaluate(pd.DataFrame(1.0, index=px.index, columns=px.columns)[["SPX"]]
                  .reindex(columns=px.columns).fillna(0.0), rets, label="OSTA-JA-HOIA SPX")

cands = {
    "TS momentum 126p":            R.w_tsmom(px, rets, 126),
    "TS momentum ANSAMBEL":        R.w_tsmom_ensemble(px, rets),
    "Ristloikeline momentum k=5":  R.w_xsmom(px, rets, 126, 5),
    "Donchian breakout 126p":      R.w_breakout(px, rets, 126),
    "Faber trend (ainult pikk)":   R.w_long_only_trend(px, rets, 200),
    "Carry-lahend 252p":           R.w_carry_proxy(px, rets, 252),
    "Riskipariteet osta-ja-hoia":  R.w_equal_long(px, rets),
}

print("=" * 118)
print("ETAPP 1 — toores (ilma portfelli vol-sihtimiseta), kulud sees")
print("=" * 118)
R.show(BH_G); R.show(BH_S); print("-" * 118)
res = {}
for name, w in cands.items():
    res[name] = R.evaluate(w, rets, label=name)
    R.show(res[name])

print()
print("=" * 118)
print("ETAPP 2 — sama, aga PORTFELLI VOL-SIHTIMISEGA 15%")
print("=" * 118)
res_vt = {}
for name, w in cands.items():
    wv = R.vol_target(w, rets, target=0.15)
    res_vt[name] = R.evaluate(wv, rets, label=name + " +volsiht")
    R.show(res_vt[name])
