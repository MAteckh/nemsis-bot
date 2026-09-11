"""
PAARIDE KAUPLEMINE — turuneutraalne, seega FINANTSEERIMINE on väiksem.

Miks see on struktuurselt erinev kõigest varasemast: pikk jalg maksab
(intress + juurdehindlus), lühike jalg SAAB (intress - juurdehindlus).
Turuneutraalses paaris intressi-komponent suuresti tühistub ja alles
jääb ainult juurdehindlus brutopositsioonilt. Meie varasem analüüs
näitas, et just intressikomponent (5.42%/a) tappis kõik strateegiad.

Testitavad paarid: ajalooliselt seotud instrumendid.
"""
import warnings; warnings.filterwarnings("ignore")
import os
import numpy as np, pandas as pd
import research as R

MK = 0.030

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    c = pd.to_numeric(d.get("Close", d.get("close")), errors="coerce")
    return c.dropna()

PAIRS = [
    ("XAUUSD", "XAGUSD", "kuld vs hõbe"),
    ("SPX",    "NAS100", "SPX vs Nasdaq"),
    ("EURUSD", "GBPUSD", "EUR vs GBP"),
    ("AUDUSD", "NZDUSD", "AUD vs NZD"),
    ("WTI",    "NGAS",   "nafta vs gaas"),
    ("XAUUSD", "US10Y",  "kuld vs võlakiri"),
    ("USDCAD", "WTI",    "CAD vs nafta"),
]

print("=" * 112)
print("A) KORRELATSIOON JA SUHTE STABIILSUS (kas paar on üldse seotud?)")
print("=" * 112)
for a, b, nimi in PAIRS:
    ca, cb = load(a), load(b)
    idx = ca.index.intersection(cb.index)
    ca, cb = ca.reindex(idx), cb.reindex(idx)
    corr = ca.pct_change().corr(cb.pct_change())
    ratio = ca / cb
    # kas suhe on tagasipöörduv? ADF-i asemel lihtne mõõt:
    # kui palju suhe kaldub oma 60p keskmisest ja kas naaseb
    z = (ratio - ratio.rolling(60).mean()) / ratio.rolling(60).std()
    half_life_proxy = z.autocorr(lag=1)
    print(f"  {nimi:22s} korr {corr:+.2f}   suhte z-autokorr(1) {half_life_proxy:+.3f}"
          f"   {'(tagasipöörduv)' if half_life_proxy < 0.97 else '(triiviv)'}")

print()
print("=" * 112)
print("B) PAARIKAUBANDUS: z-skoor sisenemine, TÄISKULUDEGA")
print("=" * 112)
print("   Pikk A + lühike B kui z < -entry, vastupidi kui z > +entry, sulge kui |z| < exit")

def pair_backtest(a, b, lookback=60, entry=2.0, exit_z=0.5):
    ca, cb = load(a), load(b)
    idx = ca.index.intersection(cb.index)
    ca, cb = ca.reindex(idx), cb.reindex(idx)
    ra, rb = ca.pct_change(), cb.pct_change()
    ratio = ca / cb
    z = (ratio - ratio.rolling(lookback).mean()) / ratio.rolling(lookback).std()

    pos = pd.Series(0.0, index=idx)
    cur = 0.0
    for i in range(lookback + 1, len(idx)):
        zi = z.iloc[i]
        if np.isnan(zi):
            continue
        if cur == 0.0:
            if zi < -entry: cur = 1.0      # suhe liiga madal -> pikk A, lühike B
            elif zi > entry: cur = -1.0
        else:
            if abs(zi) < exit_z: cur = 0.0
        pos.iloc[i] = cur

    w = pos.shift(1).fillna(0.0)
    # tootlus: pikk A, lühike B (võrdne raha mõlemal pool)
    gross = w * (ra - rb)
    # kulud: spread MÕLEMAL jalal, finantseerimine = ainult juurdehindlus
    # brutolt (intress tühistub turuneutraalses paaris)
    turn = (w - w.shift(1)).abs().fillna(0.0)
    sp = turn * (R.COST_BP.get(a, 3.0) + R.COST_BP.get(b, 3.0)) / 10000.0
    fin = w.abs() * 2 * MK / 252.0     # 2x sest kaks jalga
    net = (gross - sp - fin).fillna(0.0)
    return net, int((turn > 0).sum())

for a, b, nimi in PAIRS:
    best = None
    for lb in (40, 60, 90):
        for entry in (1.5, 2.0, 2.5):
            net, n = pair_backtest(a, b, lb, entry)
            if n < 10: continue
            eq = (1 + net).cumprod(); yrs = len(net) / 252
            cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1
            sh = net.mean() / net.std() * np.sqrt(252) if net.std() > 0 else 0
            if best is None or sh > best[0]:
                best = (sh, cagr, lb, entry, n)
    if best:
        sh, cagr, lb, entry, n = best
        print(f"  {nimi:22s} parim: lb={lb} entry={entry}  n={n:3d}  "
              f"CAGR {100*cagr:+6.1f}%  Sharpe {sh:+5.2f}")
