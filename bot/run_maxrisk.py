"""
KUI LAOSTUMINE ON AKTSEPTEERITUD: mis on MATEMAATILISELT parim risk?

Kasutaja on oelnud, et ta arvestab kogu panga kaotamisega ja kusib,
milline risk oleks sellises olukorras koige mostlikum.

See EI OLE sama kusimus mis "kuidas mitte kaotada". See on:
  maksimeeri P(jouan sihini) tingimusel, et laostumine on lubatud.

Sellel on tapne vastus — KELLY KRITEERIUM. Ja see vastus on
kontraintuitiivne: risk EI OLE "mida rohkem, seda parem".
Ule teatud punkti langeb P(jouan sihini) ISEGI SIIS, kui laostumine
sind ei huvita — sest volatiilsuslohistus soob geomeetrilise kasvu.

Kasutame PARIS tehingute tootlusi (JP225 |z|>1.0, 2. pool), mitte
normaaljaotust. Bootstrap.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(555)

def load(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

jp, spx = load("JP225"), load("SPX")
ix = jp.index.intersection(spx.index); jp, spx = jp.reindex(ix), spx.reindex(ix)
o, h, l, c = jp["Open"], jp["High"], jp["Low"], jp["Close"]
r = spx["Close"]/spx["Close"].shift(1)-1
z = (r/r.rolling(60).std()).shift(1)
w = (np.sign(z)*(z.abs() > 1.0)).reindex(o.index).fillna(0.0)
STOP = 0.03
ls, ss = (l/o-1) <= -STOP, (h/o-1) >= STOP
ret = np.where(w > 0, np.where(ls, -STOP, c/o-1),
      np.where(w < 0, np.where(ss, -STOP, 1-c/o), 0.0))
ret = pd.Series(ret, index=o.index)
ret = ret.where(ret.abs() < 0.25, 0.0)
net = (ret - (w != 0).astype(float)*6/1e4).fillna(0.0)
mid = len(net)//2
TR = net.iloc[mid:][w.iloc[mid:] != 0].values     # paris tehingud, 3% stopiga

mu, sd = TR.mean(), TR.std()
ann_mu, ann_sd = mu*76, sd*np.sqrt(76)
kelly = ann_mu/(ann_sd**2)
print("=" * 100)
print("1) ALUSSTRATEEGIA PÄRIS NÄITAJAD (JP225, 3% stopp, 2. pool)")
print("=" * 100)
print(f"   tehinguid valimis: {len(TR)}   ~76 tehingut aastas")
print(f"   keskmine tehing: {100*mu:+.3f}%   kõikumine: {100*sd:.2f}%")
print(f"   aastane tootlus {100*ann_mu:+.1f}%   aastane kõikumine {100*ann_sd:.1f}%   "
      f"Sharpe {ann_mu/ann_sd:+.2f}")
print(f"\n   >>> TÄIS-KELLY VÕIMENDUS = tootlus / kõikumine² = {kelly:.2f}x")
print( "   (Kelly maksimeerib pikaajalist KASVUKIIRUST. Üle selle langeb")
print( "    tulemus ka siis, kui laostumine sind ei huvita.)")


def sim(lev, target, years, n=20000, degrade=1.0, start=200.0):
    ntr = int(years*76)
    idx = rng.integers(0, len(TR), size=(n, ntr))
    x = TR[idx]*degrade*lev
    x = np.maximum(x, -1.0)                     # ei saa kaotada rohkem kui 100%
    eq = start*np.cumprod(1+x, axis=1)
    hit = (eq >= target)
    bust = (eq <= start*0.05)                   # 95% kadu = lopp
    fh = np.where(hit.any(1), hit.argmax(1), ntr+1)
    fb = np.where(bust.any(1), bust.argmax(1), ntr+1)
    won = float((fh < fb).mean()); lost = float((fb < fh).mean())
    return won, lost, float(np.median(eq[:, -1]))

print()
print("=" * 100)
print("2) PEENEM VÕIMENDUSE SKAALA — siht 50 000€, 10 aastat")
print("=" * 100)
print(f"   {'võimendus':>10s} {'JÕUAB':>9s} {'LAOSTUB':>9s} {'mediaan lõpp':>15s}")
print("   " + "-" * 48)
best = (None, -1)
for lev in (1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 15, 20):
    won, lost, med = sim(lev, 50000, 10)
    star = ""
    if won > best[1]: best, star = (lev, won), ""
    print(f"   {lev:9d}x {100*won:8.1f}% {100*lost:8.1f}% {med:14,.0f}€")
print(f"\n   >>> P(jõuan) on suurim {best[0]}x juures: {100*best[1]:.1f}%")

print()
print("=" * 100)
print("3) ERINEVAD SIHID — kui kaugele tahad jõuda, otsustab riski")
print("=" * 100)
for tgt, lbl in ((1000, "1 000€"), (5000, "5 000€"), (20000, "20 000€"), (50000, "50 000€")):
    print(f"\n   SIHT {lbl} (3 aastat):")
    print(f"     {'võim.':>7s} {'jõuab':>8s} {'laostub':>9s}")
    bl, bw = None, -1
    for lev in (1, 2, 3, 4, 5, 6, 8, 10):
        won, lost, _ = sim(lev, tgt, 3)
        if won > bw: bw, bl = won, lev
        print(f"     {lev:6d}x {100*won:7.1f}% {100*lost:8.1f}%")
    print(f"     --> parim {bl}x ({100*bw:.1f}%)")

print()
print("=" * 100)
print("4) AUSUSE TEST: mis siis, kui serv on POOL sellest, mida backtest näitab?")
print("=" * 100)
print("   (Serv tekkis alles 2021. Kui ta nõrgeneb, muutub kõik.)")
print(f"   {'võimendus':>10s} {'täis serv':>11s} {'pool serva':>12s} {'veerand':>10s} {'serva pole':>12s}")
print("   " + "-" * 60)
for lev in (2, 3, 5, 8):
    row = []
    for dg in (1.0, 0.5, 0.25, 0.0):
        won, lost, _ = sim(lev, 50000, 10, degrade=dg)
        row.append(f"{100*won:.1f}%")
    print(f"   {lev:9d}x {row[0]:>11s} {row[1]:>12s} {row[2]:>10s} {row[3]:>12s}")
