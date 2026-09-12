"""
KUI JP225 serv on paris, siis MIS ON TEE RAHANI?

200EUR kontol annab +20%/a notsionaalilt ~40-65EUR aastas. See ei ole
sissetulek. Aga sama strateegia $25k rahastatud kontol on ~$5000/a,
millest kaupleja saab 80-90%.

Prop-firma (FTMO-tuup) reeglid:
  1. samm: +10% eesmark, max 5% PAEVANE kahjum, max 10% KOGUKAHJUM
  2. samm: +5% eesmark, samad limiidid
  rahastatud: hoiad 80-90% kasumist

KUSIMUS: millise voimendusega ja millise stopiga see strateegia
labib, ja kui suur on labikukkumise tõenäosus?

Probleem: strateegial POLE praegu stoppi (hoiab avamisest sulgemiseni).
Halvim paev oli -8.16% => 5% paevalimiit LOHKUB voimendusel > 0.6x.
Seega testime ka KOVA STOPI mojutust.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(4242)

def load(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

jp, spx = load("JP225"), load("SPX")
ix = jp.index.intersection(spx.index)
jp, spx = jp.reindex(ix), spx.reindex(ix)
r = spx["Close"]/spx["Close"].shift(1) - 1
z = (r/r.rolling(60).std()).shift(1)
RT = 6/1e4

print("=" * 100)
print("1) KAS KÕVA STOPP LÕHUB STRATEEGIA? (High/Low põhjal, päevasisene)")
print("=" * 100)
print("   Ilma stopita on halvim päev -8.16% => ei mahu 5% päevalimiiti.")
print()
base = None
print(f"   {'stopp':>10s} {'n':>5s} {'tabatud':>9s} {'NETO bp/p':>11s} {'CAGR':>8s} "
      f"{'Sharpe':>8s} {'halvim päev':>13s}")
print("   " + "-" * 70)
for stop in (None, 0.05, 0.04, 0.03, 0.02, 0.015):
    o, h, l, c = jp["Open"], jp["High"], jp["Low"], jp["Close"]
    w = (np.sign(z)*(z.abs() > 1.0)).reindex(o.index).fillna(0.0)
    if stop is None:
        ret = np.where(w > 0, c/o-1, np.where(w < 0, 1-c/o, 0.0))
    else:
        long_stopped  = (l/o - 1) <= -stop
        short_stopped = (h/o - 1) >= stop
        long_ret  = np.where(long_stopped,  -stop, c/o-1)
        short_ret = np.where(short_stopped, -stop, 1-c/o)
        ret = np.where(w > 0, long_ret, np.where(w < 0, short_ret, 0.0))
    ret = pd.Series(ret, index=o.index)
    ret = ret.where(ret.abs() < 0.25, 0.0)
    net = (ret - (w != 0).astype(float)*RT).fillna(0.0)
    n = int((w != 0).sum())
    hit = 0.0
    if stop is not None:
        hitmask = ((w > 0) & long_stopped) | ((w < 0) & short_stopped)
        hit = 100*float(hitmask.sum())/max(n, 1)
    eq = (1+net).cumprod(); yrs = len(net)/252
    cagr = eq.iloc[-1]**(1/yrs)-1 if eq.iloc[-1] > 0 else -1
    sh = net.mean()/net.std()*np.sqrt(252) if net.std() > 0 else 0
    lbl = "puudub" if stop is None else f"{100*stop:.1f}%"
    print(f"   {lbl:>10s} {n:5d} {hit:8.1f}% {1e4*net.mean():+10.2f} "
          f"{100*cagr:+7.1f}% {sh:+8.2f} {100*net.min():+12.2f}%")
    if stop == 0.03: base = net.copy()
    if stop is None: nostop = net.copy()

print()
print("=" * 100)
print("2) PROP-FIRMA SIMULATSIOON — 3% stopp, erinevad võimendused")
print("=" * 100)
print("   Reeglid: +10% eesmärk | -5% päevas | -10% kokku | 180 päeva aega")
print("   Monte Carlo: 3000 juhuslikku tehingujärjestust (bootstrap)")
print()
tr = base[base != 0].values          # tehingupaevade tootlused (1x)
print(f"   aluseks {len(tr)} tehingut, keskm {1e4*tr.mean():+.1f}bp, "
       f"halvim {100*tr.min():+.2f}%, ~76 tehingut aastas")
print()
print(f"   {'võimendus':>10s} {'LÄBIB':>8s} {'lõhub':>8s} {'aeg otsa':>10s} "
      f"{'mediaan päevi':>14s}")
print("   " + "-" * 56)
NSIM, HORIZON = 3000, 180
for lev in (0.5, 0.75, 1.0, 1.5, 2.0, 3.0):
    npass = nbreach = ntimeout = 0
    days = []
    ntrades = int(HORIZON*76/252)
    for _ in range(NSIM):
        seq = rng.choice(tr, size=ntrades, replace=True)*lev
        eq, peak_loss = 1.0, 0.0
        done = False
        for k, x in enumerate(seq):
            if x <= -0.05:            # paevane limiit
                nbreach += 1; done = True; break
            eq *= (1+x)
            if eq <= 0.90:            # kogukahjumi limiit
                nbreach += 1; done = True; break
            if eq >= 1.10:
                npass += 1; days.append(int((k+1)*252/76)); done = True; break
        if not done: ntimeout += 1
    med = int(np.median(days)) if days else 0
    print(f"   {lev:9.2f}x {100*npass/NSIM:7.1f}% {100*nbreach/NSIM:7.1f}% "
          f"{100*ntimeout/NSIM:9.1f}% {med:14d}")

print()
print("=" * 100)
print("3) MIDA SEE TÄHENDAB RAHAS")
print("=" * 100)
print(f"   {'konto':>10s} {'tasu ~':>8s} {'+20%/a':>10s} {'kaupleja 85%':>14s} {'kuus':>10s}")
print("   " + "-" * 56)
for acc, fee in ((10000, 155), (25000, 250), (50000, 345), (100000, 540)):
    gross = acc*0.202
    print(f"   ${acc:>9,} {fee:7d}€ ${gross:>9,.0f} ${gross*0.85:>13,.0f} "
          f"${gross*0.85/12:>9,.0f}")
print()
print("   NB! See eeldab, et 2. poole serv (+20.2%/a) PÜSIB. Esimesel poolel")
print("   (2016-2021) oli sama strateegia +0.8%/a — siis poleks ükski")
print("   neist läbinud ja tasu oleks kaotatud.")
