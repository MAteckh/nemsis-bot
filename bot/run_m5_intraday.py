"""
M5 KULD — PAEVASISESED STRATEEGIAD 30min-2h hoidmisajaga.

MIKS SEE AKEN: run_m5_feasible.py mootis kulupiiri.
  uksik M5 baar : liikumine 3.32bp vs kulu 3-6bp  => VOIMATU
  30 min        : 8.4bp  vs 3bp = 2.8x            => piiripealne
  1 h           : 12.3bp vs 3bp = 4.1x            => OK
  2 h           : 18.3bp vs 3bp = 6.1x            => OK
Ja paevasisene hoidmine tahendab NULL finantseerimist — ainus omadus,
mis koik varasemad strateegiad ara tappis (5.42%/a kandis).

TESTIME NELJA PEREKONDA:
  A) luhiajaline poore (short-term reversal) — akadeemiliselt koige
     robustsem anomaalia luhikestel horisontidel (Jegadeesh 1990)
  B) momentum jatkumine
  C) avanemisvahemiku breakout
  D) kellaaja mojud

KONTROLL: iga leiu juures poolte-test ja parameetri-plato.
PIIRANG, mida pean valja utlema: andmeid on ainult 157 paeva
(marts-august 2026). Poolte-test annab ~78 paeva kummale. See on
ROBUSTSUSE JAOKS VAHE — uhtegi leidu ei tohi siit live'i viia ilma
pikema andmestikuga kordamiseta.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import pandas as pd, numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = "m5_intraday_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

d = pd.read_csv(os.path.join(HERE, "data", "xauusd_m5_2026-03_2026-08.csv"))
d["t"] = pd.to_datetime(d["timestamp"], unit="ms", utc=True)
d = d.set_index("t").sort_index()
d = d[~d.index.duplicated(keep="last")]
for c in ("open", "high", "low", "close"):
    d[c] = pd.to_numeric(d[c], errors="coerce")
d = d.dropna()
c = d["close"]
mid = len(d) // 2

SPREAD = 1.5          # bp/pool, optimistlik (BlackBull JPN225 oli 0.93bp)
RT = 2 * SPREAD / 1e4


def hinda(w_, hold, nimi, bp=SPREAD):
    """w_: signaal (-1/0/+1), hold: baaride arv. Tagastab statistika."""
    rt = 2 * bp / 1e4
    fwd = (c.shift(-hold) / c - 1)
    pos = w_.replace(0, np.nan)
    ret = (pos * fwd).dropna()
    if len(ret) < 200:
        return None
    net = ret - rt
    # kattuvad positsioonid => jaga hoidmisajaga, et Sharpe ei paisuks
    per_yr = (288 * 252) / hold
    sh = net.mean() / net.std() * np.sqrt(per_yr / (len(net) / (len(d) / 288 / 252 * per_yr) + 1e-9)) \
        if net.std() > 0 else 0.0
    # lihtsam ja ausam: mitte-kattuvad tehingud
    idx = np.arange(0, len(ret), hold)
    nk = net.iloc[idx]
    if len(nk) < 30:
        return None
    shn = nk.mean() / nk.std() * np.sqrt((288 * 252) / hold) if nk.std() > 0 else 0.0
    eq = (1 + nk).cumprod()
    yrs = len(d) / 288 / 252
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1
    h = len(nk) // 2
    s1 = nk.iloc[:h].mean() / nk.iloc[:h].std() * np.sqrt((288 * 252) / hold) if nk.iloc[:h].std() > 0 else 0
    s2 = nk.iloc[h:].mean() / nk.iloc[h:].std() * np.sqrt((288 * 252) / hold) if nk.iloc[h:].std() > 0 else 0
    return dict(n=len(nk), bp=1e4 * nk.mean(), sh=shn, cagr=cagr, s1=s1, s2=s2,
                wr=100 * (nk > 0).mean())


def rida(nimi, r):
    if r is None:
        w(f"  {nimi:38s}  (liiga vähe tehinguid)")
        return
    mark = "  <<<" if (r["sh"] > 0.5 and r["s1"] > 0 and r["s2"] > 0) else ""
    w(f"  {nimi:38s} {r['n']:5d} {r['bp']:+8.2f}bp {r['wr']:6.1f}% "
      f"{100*r['cagr']:+8.1f}% {r['sh']:+7.2f} {r['s1']:+7.2f} {r['s2']:+7.2f}{mark}")


PEA = (f"  {'variant':38s} {'teh':>5s} {'NETO/teh':>10s} {'võit%':>7s} "
       f"{'CAGR':>9s} {'Sharpe':>7s} {'1.pool':>7s} {'2.pool':>7s}")

w(f"M5 kuld {d.index[0].date()} .. {d.index[-1].date()}  ({len(d):,} baari, "
  f"{d.index.normalize().nunique()} päeva)")
w(f"spread {SPREAD}bp/pool => edasi-tagasi {2*SPREAD}bp")
w("")
w("=" * 104)
w("A) LÜHIAJALINE PÖÖRE — osta pärast langust, müü pärast tõusu")
w("=" * 104)
w(PEA)
w("-" * 104)
for look in (6, 12, 24):
    past = c / c.shift(look) - 1
    z = (past / past.rolling(288).std())
    for thr in (1.0, 1.5, 2.0):
        sig = (-np.sign(z) * (z.abs() > thr)).fillna(0.0)
        for hold in (12, 24):
            rida(f"pööre: vaata {look*5}min, |z|>{thr}, hoia {hold*5}min",
                 hinda(sig, hold, ""))

w("")
w("=" * 104)
w("B) MOMENTUM JÄTKUMINE — sama suund edasi")
w("=" * 104)
w(PEA)
w("-" * 104)
for look in (12, 24, 48):
    past = c / c.shift(look) - 1
    z = (past / past.rolling(288).std())
    for thr in (1.0, 2.0):
        sig = (np.sign(z) * (z.abs() > thr)).fillna(0.0)
        for hold in (12, 24):
            rida(f"mom: vaata {look*5}min, |z|>{thr}, hoia {hold*5}min",
                 hinda(sig, hold, ""))

w("")
w("=" * 104)
w("C) KELLAAJA MÕJU — kas mõnel tunnil on püsiv triiv?")
w("=" * 104)
w(f"  {'tund UTC':>9s} {'baare':>7s} {'keskm/1h':>11s} {'võit%':>7s} {'t-stat':>8s} "
  f"{'1.pool':>10s} {'2.pool':>10s}")
w("  " + "-" * 68)
h1ret = (c.shift(-12) / c - 1)
for hh in range(24):
    m = (d.index.hour == hh) & (d.index.minute == 0)
    x = h1ret[m].dropna()
    if len(x) < 60:
        continue
    t = x.mean() / x.std() * np.sqrt(len(x)) if x.std() > 0 else 0
    k = len(x) // 2
    w(f"  {hh:9d} {len(x):7d} {1e4*x.mean():+10.2f}bp {100*(x>0).mean():6.1f}% "
      f"{t:+8.2f} {1e4*x.iloc[:k].mean():+9.2f}bp {1e4*x.iloc[k:].mean():+9.2f}bp")
w("VALMIS")
