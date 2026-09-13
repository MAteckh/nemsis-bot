"""
SUSTEMAATILINE NORKADE, SOLTUMATUTE SIGNAALIDE OTSING.

MUUTUNUD EESMARK: run_combine.py naitas, et 4 norka signaali
(Sharpe 0.44-0.70) annavad koos +1.11, sest nende korrelatsioon on
+0.044. Ehk vaja EI OLE uht tugevat signaali — vaja on MITUT NORKA,
mis on omavahel soltumatud.

See muudab ka otsingukriteeriumi:
  VANA: otsi korget Sharpe't  => leidsin ulesobitatud tippe
  UUS:  otsi tagasihoidlikku Sharpe't + MADALAT KORRELATSIOONI
        olemasoleva korviga

DISTSIPLIIN — ilma selleta on see lihtsalt andmekaevandamine:
  1. molemad pooled peavad olema positiivsed (mitte ainult kokku)
  2. NULL-JAOTUS: mitu kandidaati laheks sama soela labi puhtast
     murast? Kui paris andmed ei anna rohkem, ei ole leidu.
  3. korrelatsioon olemasoleva korviga alla 0.3

Signaalide perekonnad (koik PAEVASISESED voi luhiajalised, et
finantseerimiskulu oleks null voi vaike):
  A) rist-lead-lag: X eilne liikumine -> Y tanane Open->Close
  B) aegrea momentum eri akendega
  C) Donchian breakout eri akendega
  D) z-skoori poore eri akendega
"""
import warnings; warnings.filterwarnings("ignore")
import os, math, itertools
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(20260913)
OUT = "signal_hunt_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

# sihtmargid: vajavad PARIS Open'i (paevasisene kaubeldav)
TGT = ["JP225", "GER40", "NAS100", "SPX", "XAUUSD", "XAGUSD", "COPPER",
       "WTI", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
       "EURJPY"]
# ennustajad: koik, sh need, mille Open on katki (kasutame ainult Close'i)
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
w(f"instrumente laetud: {len(DATA)}")


def sharpe(x):
    x = x[np.isfinite(x)]
    return float(x.mean() / x.std() * math.sqrt(252)) if len(x) > 50 and x.std() > 0 else 0.0


kandidaadid = {}

# ── A) RIST-LEAD-LAG: X eilne close-to-close -> Y tanane open->close ──
for tgt in TGT:
    if tgt not in DATA:
        continue
    t = DATA[tgt]
    y = (t["close"] / t["open"] - 1).where(lambda s_: s_.abs() < 0.25, 0.0)
    rt = 2 * COST[tgt] / 1e4
    for pred in PRED:
        if pred == tgt or pred not in DATA:
            continue
        p = DATA[pred]
        ix = y.index.intersection(p.index)
        if len(ix) < 800:
            continue
        yy = y.reindex(ix)
        r = (p["close"] / p["close"].shift(1) - 1).reindex(ix)
        z = (r / r.rolling(60).std()).shift(1)
        for thr in (0.75, 1.25):
            sg = (np.sign(z) * (z.abs() > thr)).fillna(0.0)
            if int((sg != 0).sum()) < 150:
                continue
            x = (sg * yy - (sg != 0).astype(float) * rt).fillna(0.0)
            kandidaadid[f"LL {pred}->{tgt} z{thr}"] = x

# ── B) AEGREA MOMENTUM (paevasisene sisenemine) ──────────────────
for tgt in TGT:
    if tgt not in DATA:
        continue
    t = DATA[tgt]
    y = (t["close"] / t["open"] - 1).where(lambda s_: s_.abs() < 0.25, 0.0)
    rt = 2 * COST[tgt] / 1e4
    c = t["close"]
    for lb in (10, 40, 120):
        sg = np.sign(c / c.shift(lb) - 1).shift(1).fillna(0.0)
        x = (sg * y - (sg != 0).astype(float) * rt).fillna(0.0)
        kandidaadid[f"MOM {tgt} {lb}p"] = x

# ── C) DONCHIAN BREAKOUT (paevasisene) ───────────────────────────
for tgt in TGT:
    if tgt not in DATA:
        continue
    t = DATA[tgt]
    y = (t["close"] / t["open"] - 1).where(lambda s_: s_.abs() < 0.25, 0.0)
    rt = 2 * COST[tgt] / 1e4
    c, h, l = t["close"], t["high"], t["low"]
    for lb in (20, 55):
        up = (c >= h.rolling(lb).max().shift(1))
        dn = (c <= l.rolling(lb).min().shift(1))
        sg = (up.astype(float) - dn.astype(float)).shift(1).fillna(0.0)
        if int((sg != 0).sum()) < 150:
            continue
        x = (sg * y - (sg != 0).astype(float) * rt).fillna(0.0)
        kandidaadid[f"DON {tgt} {lb}p"] = x

# ── D) Z-SKOORI POORE ────────────────────────────────────────────
for tgt in TGT:
    if tgt not in DATA:
        continue
    t = DATA[tgt]
    y = (t["close"] / t["open"] - 1).where(lambda s_: s_.abs() < 0.25, 0.0)
    rt = 2 * COST[tgt] / 1e4
    c = t["close"]
    for lb in (5, 20):
        m, sd = c.rolling(lb).mean(), c.rolling(lb).std()
        z = ((c - m) / sd).shift(1)
        sg = (-np.sign(z) * (z.abs() > 1.5)).fillna(0.0)
        if int((sg != 0).sum()) < 150:
            continue
        x = (sg * y - (sg != 0).astype(float) * rt).fillna(0.0)
        kandidaadid[f"REV {tgt} {lb}p"] = x

w(f"kandidaate genereeritud: {len(kandidaadid)}")

# ── SOEL ────────────────────────────────────────────────────────
def soel(d):
    m = len(d) // 2
    s, s1, s2 = sharpe(d.values), sharpe(d.iloc[:m].values), sharpe(d.iloc[m:].values)
    return s, s1, s2, (s > 0.25 and s1 > 0 and s2 > 0)


read = []
for nimi, x in kandidaadid.items():
    s, s1, s2, ok = soel(x)
    read.append(dict(nimi=nimi, sh=s, s1=s1, s2=s2, ok=ok))
df = pd.DataFrame(read)
labijad = df[df["ok"]].sort_values("sh", ascending=False)

w("")
w("=" * 92)
w("1) SÕEL: Sharpe > 0.25 JA mõlemad pooled positiivsed")
w("=" * 92)
w(f"   kandidaate {len(df)}, läbib {len(labijad)} ({100*len(labijad)/len(df):.1f}%)")

# ── NULL-JAOTUS ─────────────────────────────────────────────────
w("")
w("=" * 92)
w("2) NULL-JAOTUS — mitu läbiks sama sõela PUHTAST MÜRAST?")
w("=" * 92)
sims = []
for _ in range(30):
    n_ok = 0
    for x in kandidaadid.values():
        v = x.values.copy()
        nz = v != 0
        if nz.sum() < 50:
            continue
        # sailita ajastus ja suurusjaotus, juhuslikusta MARK
        v2 = v.copy()
        v2[nz] = np.abs(v[nz]) * rng.choice([-1.0, 1.0], size=int(nz.sum()))
        d2 = pd.Series(v2, index=x.index)
        if soel(d2)[3]:
            n_ok += 1
    sims.append(n_ok)
sims = np.array(sims)
p_null = float((sims >= len(labijad)).mean())
w(f"   PÄRIS andmed : {len(labijad)} läbijat")
w(f"   MÜRA (30 katset): keskmine {sims.mean():.1f}, mediaan {np.median(sims):.0f}, "
  f"max {sims.max()}")
w(f"   p = {p_null:.3f}  =>  "
  f"{'LEID ON PÄRIS' if p_null < 0.05 else 'EI OLE MÜRAST ERISTATAV'}")

w("")
w("=" * 92)
w("3) PARIMAD 25 LÄBIJAT")
w("=" * 92)
w(f"   {'signaal':30s} {'Sharpe':>8s} {'1.pool':>8s} {'2.pool':>8s}")
w("   " + "-" * 58)
for _, r in labijad.head(25).iterrows():
    w(f"   {r['nimi']:30s} {r['sh']:+8.2f} {r['s1']:+8.2f} {r['s2']:+8.2f}")

# salvesta labijate tootlused jargmiseks sammuks
if len(labijad):
    M = pd.DataFrame({r["nimi"]: kandidaadid[r["nimi"]] for _, r in labijad.iterrows()})
    M.to_csv("data/labijad.csv")
    w("")
    w(f"   läbijate päevatootlused salvestatud: data/labijad.csv "
      f"({M.shape[0]} päeva x {M.shape[1]} signaali)")
w("VALMIS")
