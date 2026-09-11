"""Kas leitud konfiguratsioon on PLATOO voi uksik onnelik punkt?

Ulesobitatud parameeter on terav tipp: naabrid on palju halvemad.
Paris mehhanism on lai platoo. Sweep naitab kumb.
"""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R, strategies as S, portfolio_sim as PS
from config import GRID_CONFIG as G

SIG={"donchian":S.sig_donchian,"bollinger_fade":S.sig_bollinger_reversion,
     "donchian_trend":S.sig_donchian_trendfiltered,"ts_momentum":S.sig_ts_momentum}
MK,RISK=PS.MK,0.015
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

def replay(tr,bal0,tc):
    bal=bal0;peak=bal0;mdd=0.0
    for t in tr:
        if bal<=20: return 0.0,mdd
        lot=max(PS.MIN_LOT,min(round(bal*RISK/(t["sl_dist"]*t["pv"]),3),PS.MAX_LOT))
        risk=t["sl_dist"]*t["pv"]*lot
        if risk>bal*tc: continue
        bal+=t["r"]*risk - PS.SPREAD[t["sym"]]*(lot/0.01) \
             - PS.NOTIONAL[t["sym"]](lot,t["px"])*(t["rate"]+MK)*t["days"]/365.0
        peak=max(peak,bal); mdd=min(mdd,bal/peak-1)
    return bal,mdd

rng=np.random.default_rng(31)
def mc(tc,pc,sm,n=600):
    res=PS.run(legs,rates,214.0,max_trade_risk=tc,max_portfolio_risk=pc,sl_mult=sm)
    tr=res["trades"]
    if len(tr)<10: return None
    outs=[]
    for _ in range(n):
        b,_=replay([tr[i] for i in rng.permutation(len(tr))],214.0,tc)
        outs.append(b)
    outs=np.array(outs)
    return dict(med=np.median(outs), ruin=100*(outs<107).mean(),
                n=sum(1 for v in res["taken"].values() if v>0), tr=len(tr))

print("="*116)
print("SWEEP: stopi kordaja x tehingulagi   (portfelli lagi = 2x tehingulagi)")
print("="*116)
SMS=[0.30,0.40,0.45,0.50,0.55,0.60,0.70,0.85,1.00]
TCS=[0.05,0.07,0.10,0.13,0.16]
print(f"{'':10s}" + "".join(f"{'x'+format(s,'.2f'):>11s}" for s in SMS))
for tc in TCS:
    row=f"tehing{100*tc:3.0f}% "
    for sm in SMS:
        r=mc(tc,2*tc,sm)
        row += "     -     " if r is None else f"{r['med']:6.0f}/{r['ruin']:3.0f}%"
    print(row)
print()
print("  Lahtrites: MEDIAAN loppsaldo / HAVIMISRISK.  Start 214 EUR.")
print("  Otsi LAIA ala, kus mediaan > 214 ja havimisrisk < 10% — mitte uksikut tippu.")
