"""
PARANDATUD versioon run_maxrisk.py-st.

Esimene versioon andis 10x voimendusel "100% edu, 635 MILJONIT EUROT".
See on ilmne jama. Kolm viga:

  1. I.I.D. BOOTSTRAP havitas kaotusseeriad. Paris kahjumid tulevad
     kobaras (pikim seeria oli 7 tehingut jarjest). Juhuslik segamine
     teeb neist uhtlase mura => drawdown naeb palju vaiksem valja.
     PARANDUS: block bootstrap (votame 10 tehingu kaupa jarjest).

  2. LAOSTUMISE LAVEND OLI VALE (-95%). 200EUR kontol tahendab juba
     -50%, et miinimum-lot on suurem kui sinu lubatud risk => sa EI SAA
     enam plaanikohaselt kaubelda. See on PRAKTILINE lopp, mitte -95%.
     PARANDUS: lopp, kui konto < 100EUR (miinimum-loti pohi).

  3. MARGIN CALL PUUDUS. Broker sulgeb positsioonid, kui equity langeb
     alla ~50% nouetavast marginaalist. Voimendusel 10x juhtub see
     ammu enne -95%.
     PARANDUS: stop-out, kui uks tehing viib konto alla stop-out taseme.

Lisaks: voimendus ei ole vaba muutuja. 200EUR kontol maarab MIINIMUM-LOT
tegeliku voimenduse. Seda naitab viimane osa.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(777)

def load(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

jp, spx = load("JP225"), load("SPX")
ix = jp.index.intersection(spx.index); jp, spx = jp.reindex(ix), spx.reindex(ix)
o, h, l, c = jp["Open"], jp["High"], jp["Low"], jp["Close"]
rr = spx["Close"]/spx["Close"].shift(1)-1
z = (rr/rr.rolling(60).std()).shift(1)
w = (np.sign(z)*(z.abs() > 1.0)).reindex(o.index).fillna(0.0)
STOP = 0.03
ls, ss = (l/o-1) <= -STOP, (h/o-1) >= STOP
ret = np.where(w > 0, np.where(ls, -STOP, c/o-1),
      np.where(w < 0, np.where(ss, -STOP, 1-c/o), 0.0))
ret = pd.Series(ret, index=o.index).where(lambda s: s.abs() < 0.25, 0.0)
net = (ret - (w != 0).astype(float)*6/1e4).fillna(0.0)
mid = len(net)//2
TR = net.iloc[mid:][w.iloc[mid:] != 0].values

mu, sd = TR.mean(), TR.std()
ann_mu, ann_sd = mu*76, sd*np.sqrt(76)
print("=" * 100)
print("1) ALUSSTRATEEGIA (JP225, 3% stopp, 2. pool — parim, mis meil on)")
print("=" * 100)
print(f"   {len(TR)} tehingut, ~76/aastas   keskmine {100*mu:+.3f}%   kõikumine {100*sd:.2f}%")
print(f"   aastas: tootlus {100*ann_mu:+.1f}%   kõikumine {100*ann_sd:.1f}%   "
      f"Sharpe {ann_mu/ann_sd:+.2f}")
print(f"   halvim üksik tehing: {100*TR.min():+.2f}%   pikim kaotusseeria valimis: ", end="")
s_ = np.sign(TR); L = cur = 0
for v in s_:
    cur = cur+1 if v < 0 else 0; L = max(L, cur)
print(f"{L} tehingut")

BLOCK = 10
def block_boot(n, ntr):
    nb = ntr//BLOCK + 1
    starts = rng.integers(0, max(len(TR)-BLOCK, 1), size=(n, nb))
    out = np.concatenate([TR[starts[:, j][:, None] + np.arange(BLOCK)] for j in range(nb)], axis=1)
    return out[:, :ntr]

def sim(lev, target, years, n=20000, degrade=1.0, start=200.0,
        floor=100.0, stopout=0.5):
    """floor: alla selle ei saa enam plaanikohaselt kaubelda (miinimum-lot).
       stopout: broker sulgeb, kui uks tehing sööb üle selle osa kontost."""
    ntr = int(years*76)
    x = block_boot(n, ntr)*degrade*lev
    eq = np.full(n, start)
    hit = np.zeros(n, bool); dead = np.zeros(n, bool)
    for t in range(ntr):
        live = ~hit & ~dead
        if not live.any(): break
        step = x[:, t]
        step = np.maximum(step, -stopout)          # broker stop-out
        eq = np.where(live, eq*(1+step), eq)
        dead |= live & (eq < floor)
        hit  |= live & ~dead & (eq >= target)
    return float(hit.mean()), float(dead.mean()), float(np.median(eq))

print()
print("=" * 100)
print("2) PARANDATUD: siht 50 000€, 10 aastat (block bootstrap + põrand + stop-out)")
print("=" * 100)
print(f"   {'võimendus':>10s} {'JÕUAB':>9s} {'SUREB':>9s} {'mediaan lõpp':>15s}")
print("   " + "-" * 48)
best = (None, -1.0)
for lev in (1, 2, 3, 4, 5, 6, 8, 10, 15, 20):
    won, lost, med = sim(lev, 50000, 10)
    if won > best[1]: best = (lev, won)
    print(f"   {lev:9d}x {100*won:8.1f}% {100*lost:8.1f}% {med:14,.0f}€")
print(f"\n   >>> P(jõuan) suurim {best[0]}x juures: {100*best[1]:.1f}%")

print()
print("=" * 100)
print("3) REALISTLIKUM SIHT: 5 000€ (piisav, et päris strateegia tööle hakkaks)")
print("=" * 100)
print(f"   {'võimendus':>10s} {'JÕUAB 3a':>10s} {'SUREB':>9s} {'mediaan':>12s}")
print("   " + "-" * 45)
for lev in (1, 2, 3, 4, 5, 6, 8, 10):
    won, lost, med = sim(lev, 5000, 3)
    print(f"   {lev:9d}x {100*won:9.1f}% {100*lost:8.1f}% {med:11,.0f}€")

print()
print("=" * 100)
print("4) AUSUSE TEST — mis siis, kui serv nõrgeneb? (siht 5 000€, 3 aastat)")
print("=" * 100)
print(f"   {'võim.':>7s} {'täis serv':>11s} {'pool':>9s} {'veerand':>10s} {'serva pole':>12s}")
print("   " + "-" * 52)
for lev in (2, 3, 5, 8, 10):
    cells = []
    for dg in (1.0, 0.5, 0.25, 0.0):
        won, lost, _ = sim(lev, 5000, 3, degrade=dg)
        cells.append(f"{100*won:.1f}%/{100*lost:.0f}†")
    print(f"   {lev:6d}x {cells[0]:>11s} {cells[1]:>9s} {cells[2]:>10s} {cells[3]:>12s}")
print("\n   (lugeda: jõuab% / sureb%)")
