"""Kas riskilagedega konfiguratsioon elab ule ka TEISES jarjekorras?

Taust: uksik lapilugu valetab. Hommikul andis live-konfiguratsioon
+827% uhel teel, aga 3000 juhuslikus jarjekorras suri konto 56% kordadest.
Sama kontroll nuud riskilagedega variantidele.
"""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R, strategies as S, portfolio_sim as PS
from config import GRID_CONFIG as G

SIG = {"donchian": S.sig_donchian, "bollinger_fade": S.sig_bollinger_reversion,
       "donchian_trend": S.sig_donchian_trendfiltered, "ts_momentum": S.sig_ts_momentum}
MK, RISK = PS.MK, 0.015

def load(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()

legs=[]
for leg in G["portfolio_legs"]:
    nm=leg["name"]; df=load(nm); cfg=dict(G); cfg.update(leg.get("params",{}))
    legs.append(dict(name=nm, df=df, signals=PS.precompute_signals(df,SIG[leg["signal"]],cfg),
                     pip_value=leg["pip_value"]))
rates=R.load_rates(pd.DatetimeIndex(sorted(set().union(*[set(l['df'].index) for l in legs]))))

def replay(tr, bal0, max_trade_risk, max_pf_risk):
    """Mangi tehingud etteantud jarjekorras labi, sama suurusloogikaga."""
    bal=bal0; peak=bal0; mdd=0.0
    for t in tr:
        if bal<=20: return 0.0, mdd
        lot=max(PS.MIN_LOT, min(round(bal*RISK/(t["sl_dist"]*t["pv"]),3), PS.MAX_LOT))
        risk=t["sl_dist"]*t["pv"]*lot
        if risk > bal*max_trade_risk: continue          # sama lagi mis simulaatoris
        pnl=t["r"]*risk
        fin=PS.NOTIONAL[t["sym"]](lot,t["px"])*(t["rate"]+MK)*t["days"]/365.0
        bal+=pnl - PS.SPREAD[t["sym"]]*(lot/0.01) - fin
        peak=max(peak,bal); mdd=min(mdd,bal/peak-1)
    return bal, mdd

rng=np.random.default_rng(23)
KONFID=[
    ("praegune (ilma laeta)",           1.00, 1.00, 1.0),
    ("tehing 10% / portfell 20%",       0.10, 0.20, 1.0),
    ("tehing 7% / portfell 15%",        0.07, 0.15, 1.0),
    ("tehing 10% / pf 20% / stopp x0.5",0.10, 0.20, 0.5),
    ("tehing 5% / pf 10% / stopp x0.5", 0.05, 0.10, 0.5),
    ("tehing 5% / pf 10% / stopp x0.35",0.05, 0.10, 0.35),
]
print("="*128)
print("MONTE CARLO riskilagedega — 2000 juhuslikku jarjekorda, 214 EUR")
print("="*128)
print(f"{'konfiguratsioon':36s} {'1 tee':>10s} {'mediaan':>9s} {'5%':>8s} {'95%':>9s} "
      f"{'SURI':>7s} {'maxDD':>8s} {'instr':>6s}")
print("-"*128)
for lbl, tc, pc, sm in KONFID:
    res=PS.run(legs, rates, 214.0, max_trade_risk=tc, max_portfolio_risk=pc, sl_mult=sm)
    tr=res["trades"]
    if len(tr)<10:
        print(f"{lbl:36s}  liiga vahe tehinguid ({len(tr)})"); continue
    outs=[];dds=[]
    for _ in range(2000):
        idx=rng.permutation(len(tr))
        b,dd=replay([tr[i] for i in idx], 214.0, tc, pc)
        outs.append(b); dds.append(dd)
    outs=np.array(outs)
    n_instr=sum(1 for k,v in res["taken"].items() if v>0)
    print(f"{lbl:36s} {res['balance']:10.0f} {np.median(outs):9.0f} "
          f"{np.percentile(outs,5):8.0f} {np.percentile(outs,95):9.0f} "
          f"{100*(outs<107).mean():6.1f}% {100*np.mean(dds):7.1f}% {n_instr:5d}/4")
print("-"*128)
print("  'SURI' = konto kaotas ule poole (alla 107 EUR).  '1 tee' = ajalooline jarjekord.")
