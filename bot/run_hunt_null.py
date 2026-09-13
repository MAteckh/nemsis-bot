"""
PARANDATUD NULL-TEST run_signal_hunt.py jaoks.

VIGA ESIMESES VERSIOONIS: null tekitati nii, et voeti valmis
tootlusseeriast abs() ja anti juhuslik mark:
    v2[nz] = np.abs(v[nz]) * rng.choice([-1, 1])
Aga tootlusseerias oli KULU JUBA MAHA ARVATUD. abs() muutis kulu
osaks suurusest, mis siis pooltel juhtudel muutus KASUMIKS.
=> null oli liiga lihtne labida ja andis 113 labijat, samal ajal kui
paris andmed andsid 62. Sellest ei saa jareldada midagi.

OIGE NULL: juhuslikusta SIGNAALI SUUND, seejarel rakenda kulud
uuesti — tapselt nagu paris andmetel. Nii jaab kulukoormus samaks.
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(913)
OUT = "hunt_null_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

TGT = ["JP225", "GER40", "NAS100", "SPX", "XAUUSD", "XAGUSD", "COPPER",
       "WTI", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
       "EURJPY"]
PRED = TGT + ["EURUSD", "BTCUSD", "ETHUSD", "US10Y", "VIX"]
COST = {"JP225": .5, "GER40": .3, "NAS100": .3, "SPX": .4, "XAUUSD": .4,
        "XAGUSD": 1.6, "COPPER": 1.2, "WTI": 1.5, "GBPUSD": .6,
        "USDJPY": .6, "AUDUSD": .9, "NZDUSD": 1.3, "USDCAD": .9,
        "USDCHF": .9, "EURJPY": .8}


def load(s):
    p = os.path.join(R.DATA, f"{s}_d.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        if c not in d.columns:
            return None
        d[c] = pd.to_numeric(d[c], errors="coerce")
    d = d.dropna()
    return d if len(d) > 800 else None


DATA = {s: load(s) for s in set(TGT + PRED)}
DATA = {k: v for k, v in DATA.items() if v is not None}

# ehita (signaal, sihtmark, kulu) kolmikud — EI ehita valmis tootlust
PAARID = []
for tgt in TGT:
    if tgt not in DATA:
        continue
    t = DATA[tgt]
    y = (t["close"] / t["open"] - 1).where(lambda s_: s_.abs() < 0.25, 0.0)
    rt = 2 * COST[tgt] / 1e4
    c, h, l = t["close"], t["high"], t["low"]
    for pred in PRED:
        if pred == tgt or pred not in DATA:
            continue
        p = DATA[pred]
        ix = y.index.intersection(p.index)
        if len(ix) < 800:
            continue
        r = (p["close"] / p["close"].shift(1) - 1).reindex(ix)
        z = (r / r.rolling(60).std()).shift(1)
        for thr in (0.75, 1.25):
            sg = (np.sign(z) * (z.abs() > thr)).fillna(0.0)
            if int((sg != 0).sum()) < 150:
                continue
            PAARID.append((f"LL {pred}->{tgt} z{thr}", sg, y.reindex(ix), rt))
    for lb in (10, 40, 120):
        sg = pd.Series(np.sign(c / c.shift(lb) - 1), index=c.index).shift(1).fillna(0.0)
        PAARID.append((f"MOM {tgt} {lb}p", sg, y, rt))
    for lb in (20, 55):
        up = (c >= h.rolling(lb).max().shift(1))
        dn = (c <= l.rolling(lb).min().shift(1))
        sg = (up.astype(float) - dn.astype(float)).shift(1).fillna(0.0)
        if int((sg != 0).sum()) >= 150:
            PAARID.append((f"DON {tgt} {lb}p", sg, y, rt))
    for lb in (5, 20):
        m_, sd = c.rolling(lb).mean(), c.rolling(lb).std()
        z2 = ((c - m_) / sd).shift(1)
        sg = (-np.sign(z2) * (z2.abs() > 1.5)).fillna(0.0)
        if int((sg != 0).sum()) >= 150:
            PAARID.append((f"REV {tgt} {lb}p", sg, y, rt))

w(f"kandidaate: {len(PAARID)}")


def sharpe(v):
    v = v[np.isfinite(v)]
    return float(v.mean() / v.std() * math.sqrt(252)) if len(v) > 50 and v.std() > 0 else 0.0


def labib(sg_vals, y_vals, rt):
    x = sg_vals * y_vals - (sg_vals != 0).astype(float) * rt
    x = np.nan_to_num(x)
    m = len(x) // 2
    return (sharpe(x) > 0.25 and sharpe(x[:m]) > 0 and sharpe(x[m:]) > 0)


# paris
n_real = 0
for nimi, sg, y, rt in PAARID:
    ix = sg.index.intersection(y.index)
    if labib(sg.reindex(ix).values, y.reindex(ix).values, rt):
        n_real += 1

w("")
w("=" * 84)
w("PARANDATUD NULL-TEST — juhuslikustatakse SIGNAALI SUUND, kulud jäävad")
w("=" * 84)
w(f"  PÄRIS andmed: {n_real} läbijat {len(PAARID)}-st")

N = 25
sims = []
for k in range(N):
    n_ok = 0
    for nimi, sg, y, rt in PAARID:
        ix = sg.index.intersection(y.index)
        v = sg.reindex(ix).values.copy()
        nz = v != 0
        if nz.sum() < 50:
            continue
        v[nz] = rng.choice([-1.0, 1.0], size=int(nz.sum()))
        if labib(v, y.reindex(ix).values, rt):
            n_ok += 1
    sims.append(n_ok)
sims = np.array(sims)
p = float((sims >= n_real).mean())
w(f"  MÜRA ({N} katset): keskmine {sims.mean():.1f}, mediaan {np.median(sims):.0f}, "
  f"min {sims.min()}, max {sims.max()}")
w(f"  p = {p:.3f}")
w("")
if p < 0.05:
    w("  => LEID ON PÄRIS: müra ei tekita nii palju läbijaid.")
else:
    w("  => EI OLE MÜRAST ERISTATAV.")
w("VALMIS")
