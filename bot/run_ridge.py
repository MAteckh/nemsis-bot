"""Miks x0.50 on terav hari? Hupotees: sunnitud 0.01-loti risk maandub
tapselt lavendi alla, nii et instrument kas paaseb kauplema voi ei paase.
Kui nii, siis pole tegu mehhanismiga vaid kokkusattumusega."""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R, strategies as S, portfolio_sim as PS
from config import GRID_CONFIG as G

SIG={"donchian":S.sig_donchian,"bollinger_fade":S.sig_bollinger_reversion,
     "donchian_trend":S.sig_donchian_trendfiltered,"ts_momentum":S.sig_ts_momentum}
def load(s):
    d=pd.read_csv(os.path.join(R.DATA,f"{s}_d.csv"),parse_dates=["Date"]).set_index("Date").sort_index()
    d=d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()
legs=[]
for leg in G["portfolio_legs"]:
    nm=leg["name"]; df=load(nm); cfg=dict(G); cfg.update(leg.get("params",{}))
    legs.append(dict(name=nm,df=df,signals=PS.precompute_signals(df,SIG[leg["signal"]],cfg),
                     pip_value=leg["pip_value"]))
rates=R.load_rates(pd.DatetimeIndex(sorted(set().union(*[set(l['df'].index) for l in legs]))))

TC=0.13
print("="*112)
print(f"MIS MUUTUB x0.50 JUURES? (tehingulagi {100*TC:.0f}%, 214 EUR konto)")
print("="*112)
print(f"{'stopp':>7s} | " + " | ".join(f"{l['name']:>16s}" for l in legs) + " |  kokku")
print(f"{'':>7s} | " + " | ".join(f"{'tehtud/vahele':>16s}" for l in legs) + " |")
print("-"*112)
for sm in (0.40,0.44,0.46,0.48,0.50,0.52,0.54,0.56,0.60):
    r=PS.run(legs,rates,214.0,max_trade_risk=TC,max_portfolio_risk=2*TC,sl_mult=sm)
    cells=[]
    for l in legs:
        nm=l["name"]
        cells.append(f"{r['taken'][nm]:6d}/{r['skipped'][nm]:<9d}")
    print(f"  x{sm:.2f} | " + " | ".join(cells) + f" | {sum(r['taken'].values()):6d}")

print()
print("="*112)
print("SUNNITUD 0.01-LOTI RISK vs LAVEND — kas instrument mahub lae alla?")
print("="*112)
print(f"{'stopp':>7s} | " + " | ".join(f"{l['name']:>10s}" for l in legs))
print("-"*112)
for sm in (0.40,0.45,0.50,0.55,0.60,1.00):
    cells=[]
    for l in legs:
        # keskmine stopikaugus signaalidest
        sds=[s[1]*sm for s in l["signals"].values()]
        risk001=np.mean(sds)*l["pip_value"]*0.01
        pct=100*risk001/214.0
        flag="OK" if pct<100*TC else "yle"
        cells.append(f"{pct:6.1f}% {flag:>3s}")
    print(f"  x{sm:.2f} | " + " | ".join(cells))
print(f"\n  Lavend = {100*TC:.0f}%. 'yle' = iga tehing jaetakse vahele.")
