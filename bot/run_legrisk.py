"""Milline jalg mahub 214 EUR kontole? Minimaalne lot 0.01 maarab riski."""
import warnings; warnings.filterwarnings("ignore")
import os, numpy as np, pandas as pd
import research as R, strategies as S
from config import GRID_CONFIG as G

MK=0.030; RISK=0.015
SIG={"donchian":S.sig_donchian,"bollinger_fade":S.sig_bollinger_reversion,
     "donchian_trend":S.sig_donchian_trendfiltered,"ts_momentum":S.sig_ts_momentum}
SPREAD={"XAUUSD":0.40,"SPX":0.50,"USDJPY":0.15,"EURUSD":0.12}
NOT={"XAUUSD":lambda l,p:l*100*p,"SPX":lambda l,p:l*100*p,
     "USDJPY":lambda l,p:l*100000,"EURUSD":lambda l,p:l*100000*p}

def load(s):
    d=pd.read_csv(os.path.join(R.DATA,f"{s}_d.csv"),parse_dates=["Date"]).set_index("Date").sort_index()
    d=d[~d.index.duplicated(keep="last")]; d.columns=[c.lower() for c in d.columns]
    for c in ("open","high","low","close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()

legs={}
print("=" * 116)
print("A) MIS ON 0.01 LOTI RISK IGAL JALAL? (214 EUR konto)")
print("=" * 116)
print(f"{'jalg':9s} {'kesk stopp':>11s} {'0.01 loti risk':>15s} {'% 214EUR kontost':>18s} {'hinnang':>22s}")
print("-"*116)
for leg in G["portfolio_legs"]:
    nm=leg["name"]; d=load(nm); rates=R.load_rates(d.index)
    cfg=dict(G); cfg.update(leg.get("params",{})); cfg["risk_pct"]=RISK; cfg["max_positions"]=1
    res=S.simulate(d,SIG[leg["signal"]],cfg,account_balance=214.0,pip_value=leg["pip_value"])
    tr=res["trades"]
    if not tr: continue
    rows=[]
    for t in tr:
        risk=abs(t.entry-t.sl)*leg["pip_value"]*t.lot
        if risk<=0: continue
        rows.append(dict(sym=nm,r=t.pnl/risk,sl=abs(t.entry-t.sl),pv=leg["pip_value"],
                         px=t.entry,days=max(1,(t.closed_at-t.opened_at).days),
                         rate=float(rates.asof(t.opened_at))))
    legs[nm]=pd.DataFrame(rows)
    sl_m=np.mean([r["sl"] for r in rows])
    risk001=sl_m*leg["pip_value"]*0.01
    pct=100*risk001/214.0
    verdict="OK" if pct<5 else ("piiripealne" if pct<10 else "LIIGA SUUR")
    print(f"{nm:9s} {sl_m:11.2f} {risk001:15.2f} {pct:17.1f}% {verdict:>22s}")

def replay(seq,bal0,minlot=0.01):
    bal=bal0;peak=bal0;mdd=0.0
    for _,t in seq.iterrows():
        if bal<=20: return 0.0,mdd
        lot=max(minlot,min(round(bal*RISK/(t.sl*t.pv),3),0.5))
        risk=t.sl*t.pv*lot
        bal+=t.r*risk - SPREAD[t.sym]*(lot/0.01) - NOT[t.sym](lot,t.px)*(t.rate+MK)*t.days/365.0
        peak=max(peak,bal); mdd=min(mdd,bal/peak-1)
    return bal,mdd

rng=np.random.default_rng(11)
def mc(pool,bal0,n=1200):
    outs=[];dds=[]
    for _ in range(n):
        s=pool.sample(frac=1.0,replace=False,random_state=int(rng.integers(1e9)))
        b,dd=replay(s,bal0); outs.append(b/bal0); dds.append(dd)
    outs=np.array(outs)
    return np.median(outs),np.percentile(outs,5),100*(outs<0.5).mean(),100*np.mean(dds)

print()
print("=" * 116)
print("B) HAVIMISRISK JALA KAUPA JA KOMBINATSIOONIDES — 214 EUR konto, 1200 korrast")
print("=" * 116)
print(f"{'koosseis':34s} {'tehinguid':>10s} {'mediaan':>9s} {'5%':>7s} {'kaotas>50%':>12s} {'kesk maxDD':>12s}")
print("-"*116)
combos=[(["XAUUSD"],"ainult XAUUSD"),(["SPX"],"ainult SPX"),
        (["USDJPY"],"ainult USDJPY"),(["EURUSD"],"ainult EURUSD"),
        (["USDJPY","EURUSD"],"ainult FX (USDJPY+EURUSD)"),
        (["XAUUSD","SPX"],"XAUUSD+SPX"),
        (["XAUUSD","SPX","USDJPY","EURUSD"],"KOIK NELI = praegune LIVE")]
for syms,lbl in combos:
    pool=pd.concat([legs[s] for s in syms if s in legs],ignore_index=True)
    if pool.empty: continue
    med,p5,ruin,dd=mc(pool,214.0)
    star=" <-- PRAEGU" if "LIVE" in lbl else ""
    print(f"{lbl:34s} {len(pool):10d} {med:8.2f}x {p5:6.2f}x {ruin:11.1f}% {dd:11.1f}%{star}")
