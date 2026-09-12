"""
KAS VANA GRID OLI IKKA PARIM? — aus, pikk test.

Kasutaja tunne: "headel paevadel tõi 100+ ja demol tegi 200EUR-st
700EUR mone paevaga."

SEE TUNNE ON OIGE. Grid TEEBKI seda. Kusimus ei ole, kas ta teeb
hasid paevi — vaid mis juhtub ULEJAANUD ajal. Seepaerast ei vaata
me keskmist, vaid AJAJOONT ja JAOTUST.

Kasutame TAPSELT sama koodi, mida paris bot kasutas:
backtest.simulate_gold_grid -> gold_logic funktsioonid.

NB: simulaator lubab equity'l miinusesse minna. Paris broker seda ei
luba. Seepaerast markime ara, MILLAL konto oleks surnud, ja koik
parast seda on valjamoeldis.
"""
import warnings; warnings.filterwarnings("ignore")
import pandas as pd, numpy as np, backtest as BT
h1=pd.read_csv("data/XAUUSD_h1.csv",parse_dates=["Date"]).set_index("Date").sort_index()
h1=h1[~h1.index.duplicated(keep="last")]
h1.columns=[c.strip().lower() for c in h1.columns]
for c in ("open","high","low","close"): h1[c]=pd.to_numeric(h1[c],errors="coerce")
h1=h1.dropna()[["open","high","low","close"]]
r=BT.simulate_gold_grid(h1,account_balance=200.0)
eq=r["equity"]
print("="*88)
print("VANA GRID — PÄRIS AJAJOON, 200€ kontoga (sama kood, mida bot kasutas)")
print("="*88)
print(f"  andmed: {h1.index[0].date()} .. {h1.index[-1].date()}\n")
tipp=float(eq.cummax().max()); tp=eq[eq>=tipp].index[0]
a100=eq[eq<100]; a0=eq[eq<=0]
print(f"  START           {eq.index[0].date()}   200.00€")
print(f"  TIPP            {tp.date()}   {tipp:,.2f}€   (+{100*(tipp/200-1):.0f}%, "
      f"{(tp-eq.index[0]).days} päeva pärast)")
if len(a100):
    print(f"  ALLA 100€       {a100.index[0].date()}   {float(a100.iloc[0]):,.2f}€   "
          f"({(a100.index[0]-eq.index[0]).days} päeva pärast)")
if len(a0):
    print(f"  KONTO NULLIS    {a0.index[0].date()}   ({(a0.index[0]-eq.index[0]).days} päeva pärast)")
    print("\n  >>> Kõik, mis simulatsioonis pärast seda juhtub, on VÄLJAMÕELDIS.")
    print("      Päris broker oleks konto siin sulgenud.")
lopp = a0.index[0] if len(a0) else eq.index[-1]
hea = eq[eq.index<=lopp]
print("\n"+"="*88); print("ENNE SURMA — kui hea see periood oli?"); print("="*88)
d=hea.resample("1D").last().dropna(); ch=d.diff().dropna()
print(f"  periood {hea.index[0].date()} .. {lopp.date()}  ({(lopp-hea.index[0]).days} päeva)")
print(f"  parim päev {ch.max():+.2f}€    halvim päev {ch.min():+.2f}€")
print(f"  päevi üle +50€: {int((ch>50).sum())}     päevi alla -50€: {int((ch<-50).sum())}")
w=hea.resample("1W").last().dropna().pct_change().dropna()
print(f"\n  nädalaid üle +50%: {int((w>0.5).sum())}")
print(f"  nädalaid +20..50%: {int(((w>0.2)&(w<=0.5)).sum())}")
print(f"  nädalaid 0..+20% : {int(((w>0)&(w<=0.2)).sum())}")
print(f"  nädalaid miinuses: {int((w<=0).sum())}")
