"""
PARANDUS: kui palju kapitali on 1000EUR/KUUS jaoks PARISELT vaja?

MINU VIGA: utlesin "60 000EUR kapitali vaja" ja hiljem "11 000EUR =
183EUR/kuus". Molemad eeldasid 1x voimendust. Aga kogu arutelu kais
5x kohta. 5x juures on aastane tootlus 5 * 20% = 100% kapitalist.

Ja siis on teine, palju tahtsam kusimus, mida ma polnud arvutanud:
kui sa hakkad IGA KUU 1000EUR VALJA VOTMA, kas konto peab vastu?
Valjavotmine drawdown'i ajal sooб kontot topelt.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R
rng = np.random.default_rng(31337)

def load(s):
    d=pd.read_csv(os.path.join(R.DATA,f"{s}_d.csv"),parse_dates=["Date"]).set_index("Date").sort_index()
    d=d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c]=pd.to_numeric(d[c],errors="coerce")
    return d.dropna()
jp,spx=load("JP225"),load("SPX")
ix=jp.index.intersection(spx.index); jp,spx=jp.reindex(ix),spx.reindex(ix)
o,h,l,c=jp["Open"],jp["High"],jp["Low"],jp["Close"]
rr=spx["Close"]/spx["Close"].shift(1)-1
z=(rr/rr.rolling(60).std()).shift(1)
w=(np.sign(z)*(z.abs()>1.0)).reindex(o.index).fillna(0.0)
S=0.03
ls,ss=(l/o-1)<=-S,(h/o-1)>=S
ret=np.where(w>0,np.where(ls,-S,c/o-1),np.where(w<0,np.where(ss,-S,1-c/o),0.0))
ret=pd.Series(ret,index=o.index).where(lambda s:s.abs()<0.25,0.0)
net=(ret-(w!=0).astype(float)*6/1e4).fillna(0.0)
mid=len(net)//2
TR=net.iloc[mid:][w.iloc[mid:]!=0].values
mu,sd=TR.mean(),TR.std()
ann_mu,ann_sd=mu*76,sd*np.sqrt(76)

print("="*100)
print("1) PARANDUS — kui palju kapitali on 12 000€/AASTAS jaoks vaja?")
print("="*100)
print(f"   Strateegia 1x: +{100*ann_mu:.1f}%/a, kõikumine {100*ann_sd:.1f}%")
print()
print(f"   {'võimendus':>10s} {'tootlus/a':>11s} {'kõikumine/a':>13s} {'vajalik kapital':>17s}")
print("   "+"-"*56)
for lev in (1,2,3,5,8):
    print(f"   {lev:9d}x {100*ann_mu*lev:10.0f}% {100*ann_sd*lev:12.0f}% "
          f"{12000/(ann_mu*lev):16,.0f}€")
print()
print("   => 5x juures EI OLE vaja 60 000€. Vaja on ~12 000€.")
print("   => Ja ajalooline 5x tee jõudis 11 099€-ni (2016 algus, 10a).")
print("      Ehk TEE A jõuab tegelikult peaaegu sihini. Mu varasem")
print("      '183€/kuus' oli VALE — õige on ~925€/kuus.")

B=10
def boot(n,k,degrade=1.0):
    nb=k//B+1
    st=rng.integers(0,max(len(TR)-B,1),size=(n,nb))
    out=np.concatenate([TR[st[:,j][:,None]+np.arange(B)] for j in range(nb)],axis=1)[:,:k]
    return (out-mu)+mu*degrade

print()
print("="*100)
print("2) AGA KAS KONTO PEAB VASTU, KUI IGA KUU 1000€ VÄLJA VÕTTA?")
print("="*100)
print("   Siin on konks, mida ma polnud arvutanud: väljavõtmine")
print("   drawdown'i ajal sööb kontot topelt. 5x juures on aastane")
print(f"   kõikumine {100*ann_ate if False else 100*ann_sd*5:.0f}% — see EI OLE stabiilne palk.")
print()
def survive(cap, lev, withdraw, years=10, n=20000, degrade=1.0):
    k=int(years*76); x=boot(n,k,degrade)*lev
    per_month=76/12
    eq=np.full(n,float(cap)); dead=np.zeros(n,bool); paid=np.zeros(n)
    nxt=per_month
    for t in range(k):
        live=~dead
        eq=np.where(live,eq*(1+np.maximum(x[:,t],-0.5)),eq)
        if t+1>=nxt:
            nxt+=per_month
            can=live&(eq>=withdraw*1.0)
            eq=np.where(can,eq-withdraw,eq)
            paid+=np.where(can,withdraw,0.0)
        dead|=live&(eq<cap*0.10)
    return float((~dead).mean()), float(np.median(paid)), float(np.median(eq))

print(f"   {'kapital':>9s} {'võim.':>6s} {'välja/kuus':>11s} {'elab 10a üle':>14s} "
      f"{'kokku saadud':>14s} {'lõppkonto':>12s}")
print("   "+"-"*72)
for cap,lev in ((12000,5),(12000,3),(20000,3),(30000,2),(60000,1),(11000,5)):
    alive,paid,fin=survive(cap,lev,1000)
    print(f"   {cap:8,d}€ {lev:5d}x {1000:10,d}€ {100*alive:13.1f}% "
          f"{paid:13,.0f}€ {fin:11,.0f}€")

print()
print("="*100)
print("3) AUSUSE TEST — sama, kui serv on POOL")
print("="*100)
print(f"   {'kapital':>9s} {'võim.':>6s} {'elab üle':>10s} {'kokku saadud':>14s}")
print("   "+"-"*46)
for cap,lev in ((12000,5),(20000,3),(60000,1)):
    alive,paid,_=survive(cap,lev,1000,degrade=0.5)
    print(f"   {cap:8,d}€ {lev:5d}x {100*alive:9.1f}% {paid:13,.0f}€")
