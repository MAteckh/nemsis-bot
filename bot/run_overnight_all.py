"""
MUSTER 1: OO vs PAEV — kust tootlus tegelikult tuleb?

See on rahanduse uks tuntumaid anomaaliaid: aktsiaindeksite kogu
tootlus tuleb OOSEL (sulgemisest avamiseni), mitte paeval. Paevane
osa on sageli NULL voi NEGATIIVNE.

Kui see kehtib, on strateegia lihtne: osta sulgemisel, mUU avamisel.
AGA: CFD-l maksab uleoo hoidmine ~5.42%/a. Kusimus on, kas oine
triiv katab selle.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

SYMS = ["SPX","NAS100","GER40","JP225","XAUUSD","XAGUSD","COPPER","WTI",
        "BTCUSD","ETHUSD"]

def load(s):
    p = os.path.join(R.DATA, f"{s}_d.csv")
    if not os.path.exists(p): return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

# CFD finantseerimine: intress + markup, paevas
FIN_DAY = 0.0542/252

print("=" * 104)
print("KUST TOOTLUS TULEB? (kogu periood, aastastatud)")
print("=" * 104)
print(f"{'sümbol':9s} {'OSTA-HOIA':>11s} {'ÖÖ (C->O)':>11s} {'PÄEV (O->C)':>12s} "
      f"{'ÖÖ osa':>8s} {'ÖÖ - kulud':>12s} {'PÄEV - kulud':>13s}")
print("-" * 104)
res = {}
for s in SYMS:
    d = load(s)
    if d is None or len(d) < 500: continue
    yrs = len(d)/252
    on  = (d["Open"]/d["Close"].shift(1) - 1).dropna()      # oo
    dy  = (d["Close"]/d["Open"] - 1).dropna()               # paev
    bh  = (d["Close"].iloc[-1]/d["Close"].iloc[0])**(1/yrs) - 1
    cost = 2*R.COST_BP.get(s, 5.0)/1e4
    on_a  = (1+on).prod()**(1/yrs) - 1
    dy_a  = (1+dy).prod()**(1/yrs) - 1
    # oise strateegia: iga paev sisse-valja => kulu + finantseerimine
    on_net = (1+on-cost-FIN_DAY).prod()**(1/yrs) - 1
    dy_net = (1+dy-cost).prod()**(1/yrs) - 1     # paevasisene: EI MINGIT finantseerimist
    share = 100*on_a/(on_a+dy_a) if (on_a+dy_a) != 0 else np.nan
    res[s] = (on, dy, cost)
    print(f"{s:9s} {100*bh:10.1f}% {100*on_a:10.1f}% {100*dy_a:11.1f}% "
          f"{share:7.0f}% {100*on_net:11.1f}% {100*dy_net:12.1f}%")

print()
print("=" * 104)
print("SAMA, POOLTE KAUPA (kas öine triiv on püsiv?)")
print("=" * 104)
print(f"{'sümbol':9s} {'ÖÖ 1.pool':>11s} {'ÖÖ 2.pool':>11s} {'PÄEV 1.pool':>13s} {'PÄEV 2.pool':>13s}")
print("-" * 104)
for s, (on, dy, cost) in res.items():
    m1, m2 = len(on)//2, len(dy)//2
    f = lambda x: 100*((1+x).prod()**(252/len(x))-1)
    print(f"{s:9s} {f(on.iloc[:m1]):10.1f}% {f(on.iloc[m1:]):10.1f}% "
          f"{f(dy.iloc[:m2]):12.1f}% {f(dy.iloc[m2:]):12.1f}%")

print()
print("=" * 104)
print("KAS ÖINE TRIIV ON STATISTILISELT OLULINE? (t-statistik)")
print("=" * 104)
for s, (on, dy, cost) in res.items():
    t_on = on.mean()/on.std()*np.sqrt(len(on))
    t_dy = dy.mean()/dy.std()*np.sqrt(len(dy))
    net = on - cost - FIN_DAY
    t_net = net.mean()/net.std()*np.sqrt(len(net))
    verdict = "KASUMLIK" if t_net > 2 else ("nõrk" if t_net > 0 else "KAHJUMLIK")
    print(f"  {s:9s} öö t={t_on:+6.2f}  päev t={t_dy:+6.2f}  |  "
          f"öö PÄRAST kulusid t={t_net:+6.2f}  -> {verdict}")
