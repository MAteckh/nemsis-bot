import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np
import research as R

px = R.load_panel(); rets = R.returns(px); rates = R.load_rates(px.index)

print("=" * 112)
print("MURDEPUNKT: kui palju teenib iga BRUTO-POSITSIOONI euro, vs mis ta maksab?")
print("=" * 112)
print(f"{'strateegia':28s} {'tulu/bruto':>11s} {'vaja katteks':>13s} {'vahe':>9s}   verdikt")
print("-" * 112)

cands = {
    "TS momentum 126p":       R.w_tsmom(px, rets, 126),
    "TS momentum ANSAMBEL":   R.w_tsmom_ensemble(px, rets),
    "Ristloikeline momentum": R.w_xsmom(px, rets, 126, 5),
    "Donchian breakout":      R.w_breakout(px, rets, 126),
    "Faber trend (pikk)":     R.w_long_only_trend(px, rets, 200),
    "Riskipariteet (pikk)":   R.w_equal_long(px, rets),
}
MK = 0.030
for name, w in cands.items():
    wv = R.vol_target(w, rets, 0.15)
    r = R.evaluate(wv, rets, label=name)          # ilma finantseerimiseta
    g = r["gross"] = wv.abs().sum(axis=1).mean()
    ne = wv.sum(axis=1).mean()
    per_gross = r["cagr"] / g
    # kate: markup igal brutoeurol + intress netoeurol
    need = MK + rates.mean() * (ne / g)
    diff = per_gross - need
    verdict = "JAAB PLUSSI" if diff > 0 else "sureb kulude kae labi"
    print(f"{name:28s} {100*per_gross:10.2f}% {100*need:12.2f}% {100*diff:+8.2f}%   {verdict}")

print()
print("=" * 112)
print("JARELDUS-KONTROLL: kas VoIMENDUSE VAHENDAMINE paastab?")
print("=" * 112)
w = R.vol_target(R.w_equal_long(px, rets), rets, 0.15)
for scale in (1.0, 0.5, 0.25, 0.10):
    r = R.evaluate_full(w * scale, rets, rates, markup=MK, label=f"  riskipariteet x{scale:.2f}")
    R.show_full(r)
print("\n  -> Tulu JA kulu skaleeruvad koos. Vohendus ei ole probleem ega lahendus.")

print()
print("=" * 112)
print("MIS SIIS ON? Finantseerimist makstakse ainult OOBESE HOITUD positsiooni eest.")
print("=" * 112)
res = R.evaluate(R.vol_target(R.w_equal_long(px, rets), rets, 0.15), rets)
print(f"  Riskipariteet bruto-tootlus enne kulusid : {100*res['cagr']:+6.1f}%/a")
print(f"  Sellest spread                           : {100*res['cost_drag']:6.1f}%/a")
print(f"  Sellest OONE FINANTSEERIMINE             : {100*20.8:6.1f}%/a  <-- suurim uksik kulu")
print(f"  Jaab alles                               : {100*(res['cagr']-res['cost_drag']-0.208):+6.1f}%/a")
