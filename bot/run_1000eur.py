"""
SIHT: 1000 EUR KUUS (12 000 EUR aastas). Koik teed, risk ei loe.

Kasutame PARIS tehingute tootlusi (JP225 |z|>1.0, 3% stopp, 2. pool),
block bootstrap (sailitab kaotusseeriad).
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R
rng = np.random.default_rng(1000)

def load(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

jp, spx = load("JP225"), load("SPX")
ix = jp.index.intersection(spx.index); jp, spx = jp.reindex(ix), spx.reindex(ix)
o,h,l,c = jp["Open"],jp["High"],jp["Low"],jp["Close"]
rr = spx["Close"]/spx["Close"].shift(1)-1
z = (rr/rr.rolling(60).std()).shift(1)
w = (np.sign(z)*(z.abs()>1.0)).reindex(o.index).fillna(0.0)
S=0.03
ls,ss=(l/o-1)<=-S,(h/o-1)>=S
ret=np.where(w>0,np.where(ls,-S,c/o-1),np.where(w<0,np.where(ss,-S,1-c/o),0.0))
ret=pd.Series(ret,index=o.index).where(lambda s:s.abs()<0.25,0.0)
net=(ret-(w!=0).astype(float)*6/1e4).fillna(0.0)
mid=len(net)//2
TR=net.iloc[mid:][w.iloc[mid:]!=0].values
B=10
def boot(n,k,degrade=1.0):
    """degrade: NORGEM SERV = vahenda ainult KESKMIST, jata mura alles.
    (Varasem viga: TR*degrade vahendas ka koikumist, mis on lihtsalt
     vaiksem positsioon, mitte norgem serv — ja andis absurdse tulemuse,
     kus "pool serva" oli PAREM kui tais serv.)"""
    nb=k//B+1
    st=rng.integers(0,max(len(TR)-B,1),size=(n,nb))
    out=np.concatenate([TR[st[:,j][:,None]+np.arange(B)] for j in range(nb)],axis=1)[:,:k]
    m=TR.mean()
    return (out-m)+m*degrade

print("="*100); print("SIHT: 1 000€/KUUS = 12 000€/AASTAS"); print("="*100)
print(f"  Strateegia: +20.0%/a, Sharpe +1.87, 76 tehingut aastas")
print(f"  => 12 000€ aastas 20%-ga nõuab {12000/0.20:,.0f}€ kapitali")
print(f"  => sul on 200€. Vaja kasvada {60000/200:.0f}x.")

# ---------- TEE A: oma raha, korge voimendus ----------
def sim_direct(lev,target,years,n=20000,degrade=1.0,start=200.0,floor=100.0,so=0.5):
    k=int(years*76); x=boot(n,k,degrade)*lev
    eq=np.full(n,start); hit=np.zeros(n,bool); dead=np.zeros(n,bool)
    for t in range(k):
        live=~hit&~dead
        if not live.any(): break
        eq=np.where(live,eq*(1+np.maximum(x[:,t],-so)),eq)
        dead|=live&(eq<floor); hit|=live&~dead&(eq>=target)
    return float(hit.mean()),float(dead.mean())

print(); print("="*100)
print("TEE A — oma 200€, maksimaalne võimendus, siht 60 000€")
print("="*100)
print(f"  {'võim.':>7s} {'5 aastat':>18s} {'10 aastat':>18s} {'15 aastat':>18s}")
print("  "+"-"*64)
for lev in (5,8,10,15,20,30):
    cells=[]
    for yy in (5,10,15):
        won,dead=sim_direct(lev,60000,yy)
        cells.append(f"{100*won:5.1f}% / {100*dead:4.1f}†")
    print(f"  {lev:6d}x {cells[0]:>18s} {cells[1]:>18s} {cells[2]:>18s}")
print("  (jõuab% / sureb†)")

# ---------- TEE B: prop-redel ----------
def sim_prop(n=20000, years=6, fee_frac=0.775, start=200.0,
             p1=0.50, p2=0.70, keep=0.85, ret_yr=0.20,
             breach_yr=0.30, scale=True, degrade=1.0):
    """
    Prop-redel: osta challenge, labi 2 sammu, saa rahastatud konto,
    kogu kasum, osta ROHKEM challenge'eid. Konto voib reeglirikkumisega
    kaduda (breach_yr toenaosus aastas).
    Tasud: 10k=155, 25k=250, 50k=345, 100k=540 EUR.
    """
    SIZES=[(10000,155),(25000,250),(50000,345),(100000,540)]
    p1e,p2e = p1*degrade if degrade<1 else p1, p2*degrade if degrade<1 else p2
    cash=np.full(n,start)
    funded=[[] for _ in range(n)]          # rahastatud kontode suurused
    reached=np.zeros(n,bool); reach_m=np.full(n,999)
    for m in range(years*12):
        for i in range(n):
            if reached[i]: continue
            # osta challenge'eid, kui raha jatkub (suurim, mida saab lubada)
            while True:
                aff=[(s,f) for s,f in SIZES if cash[i]>=f]
                if not aff: break
                s,f=aff[-1]
                cash[i]-=f
                if rng.random()<p1e and rng.random()<p2e:
                    funded[i].append(s)
                if cash[i]<SIZES[0][1]: break
            # kuu tulu rahastatud kontodelt
            inc=0.0; surv=[]
            for s in funded[i]:
                if rng.random()<breach_yr/12: continue      # rikkus reegleid
                pay=s*ret_yr/12*keep
                inc+=pay
                surv.append(min(s*1.25,200000) if (scale and rng.random()<1/12) else s)
            funded[i]=surv
            cash[i]+=inc
            if inc>=1000 and not reached[i]:
                reached[i]=True; reach_m[i]=m+1
    return float(reached.mean()), reach_m[reached.astype(bool)]

print(); print("="*100)
print("TEE B — prop-firma redel (200€ -> challenge -> kasum -> rohkem kontosid)")
print("="*100)
print("  Eeldused: 1. samm 50%, 2. samm 70%, hoiad 85%, +20%/a,")
print("            30% aastas kaotad konto reeglirikkumisega, skaleerimine +25%")
print()
print(f"  {'aega':>10s} {'jõuab 1000€/kuus':>20s} {'mediaan kuud':>14s}")
print("  "+"-"*48)
for yy in (3,6,10):
    p,ms=sim_prop(years=yy)
    med=int(np.median(ms)) if len(ms) else 0
    print(f"  {yy:8d}a {100*p:19.1f}% {med:14d}")

print(); print("="*100)
print("AUSUSE TEST — mõlemad teed, kui serv on POOL")
print("="*100)
won,dead=sim_direct(10,60000,10,degrade=0.5)
print(f"  TEE A (10x, 10a):  täis serv {100*sim_direct(10,60000,10)[0]:.1f}%  "
      f"->  pool serva {100*won:.1f}%  (sureb {100*dead:.1f}%)")
pf,_=sim_prop(years=6); ph,_=sim_prop(years=6,p1=0.25,p2=0.45)
print(f"  TEE B (6a):        täis serv {100*pf:.1f}%  ->  pool serva {100*ph:.1f}%")
