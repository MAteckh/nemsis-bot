"""
TAIESTI PUHAS WALK-FORWARD TEST SIGNAALIKORVILE.

MIKS SEE VAJALIK ON:
run_signal_hunt.py soelus 634 kandidaadist 62, kasutades tingimust
"molemad pooled positiivsed". Iga jargnev poolte-test nende 62 peal
on RINGTOESTUS — signaalid valiti just selle tingimuse jargi.

Ka "vali 1. poolelt, testi 2. poolel" nende 62 seast ei ole puhas,
sest 62 olid juba eelfiltreeritud MOLEMA poole jargi.

PUHAS TEST: genereeri koik 634, vali AINULT 1. poole andmete pealt,
testi 2. poolel. 2. poole andmeid ei kasutata valikul kuidagi.

Teeme ka vastupidi (vali 2., testi 1.) ja libiseva aknaga, et naha,
kas tulemus on stabiilne.
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import research as R

OUT = "walkforward_tulemus.txt"

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

# ── genereeri KOIK kandidaadid (sama loogika mis run_signal_hunt.py) ──
kand = {}
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
        yy = y.reindex(ix)
        r = (p["close"] / p["close"].shift(1) - 1).reindex(ix)
        z = (r / r.rolling(60).std()).shift(1)
        for thr in (0.75, 1.25):
            sg = (np.sign(z) * (z.abs() > thr)).fillna(0.0)
            if int((sg != 0).sum()) < 150:
                continue
            kand[f"LL {pred}->{tgt} z{thr}"] = (sg * yy - (sg != 0).astype(float) * rt).fillna(0.0)
    for lb in (10, 40, 120):
        sg = pd.Series(np.sign(c / c.shift(lb) - 1), index=c.index).shift(1).fillna(0.0)
        kand[f"MOM {tgt} {lb}p"] = (sg * y - (sg != 0).astype(float) * rt).fillna(0.0)
    for lb in (20, 55):
        up = (c >= h.rolling(lb).max().shift(1))
        dn = (c <= l.rolling(lb).min().shift(1))
        sg = (up.astype(float) - dn.astype(float)).shift(1).fillna(0.0)
        if int((sg != 0).sum()) >= 150:
            kand[f"DON {tgt} {lb}p"] = (sg * y - (sg != 0).astype(float) * rt).fillna(0.0)
    for lb in (5, 20):
        m_, sd = c.rolling(lb).mean(), c.rolling(lb).std()
        z2 = ((c - m_) / sd).shift(1)
        sg = (-np.sign(z2) * (z2.abs() > 1.5)).fillna(0.0)
        if int((sg != 0).sum()) >= 150:
            kand[f"REV {tgt} {lb}p"] = (sg * y - (sg != 0).astype(float) * rt).fillna(0.0)

M = pd.DataFrame(kand).fillna(0.0)
w(f"kandidaate KOKKU: {M.shape[1]}, päevi {M.shape[0]}")
w(f"periood {M.index[0].date()} .. {M.index[-1].date()}")


def sh(x):
    x = np.asarray(x)
    x = x[np.isfinite(x)]
    return float(x.mean() / x.std() * math.sqrt(252)) if len(x) > 40 and x.std() > 0 else 0.0


def korv(df, cols):
    if not cols:
        return pd.Series(0.0, index=df.index)
    Z = df[cols] / df[cols].std().replace(0, np.nan)
    return Z.mean(axis=1).fillna(0.0)


w("")
w("=" * 88)
w("1) PUHAS WALK-FORWARD — vali KÕIGI 634 seast, kasuta ainult valikuakent")
w("=" * 88)
m = len(M) // 2
A, B = M.iloc[:m], M.iloc[m:]
for lavi in (0.0, 0.25, 0.5):
    val = [c for c in M.columns if sh(A[c]) > lavi]
    if not val:
        continue
    w(f"   lävend Sharpe>{lavi:.2f}: valitud {len(val):3d} signaali")
    w(f"      1. pool (valikuaken, IS) : {sh(korv(A, val)):+.2f}")
    w(f"      2. pool (OOS)            : {sh(korv(B, val)):+.2f}   <<<")
    val2 = [c for c in M.columns if sh(B[c]) > lavi]
    w(f"   vastupidi ({len(val2)} sign.) 1. pool (OOS): {sh(korv(A, val2)):+.2f}")
    w("")

w("=" * 88)
w("2) LIBISEV AKEN — vali 2 aasta pealt, kauple järgmised 6 kuud")
w("=" * 88)
w(f"   {'valikuaken':>24s} {'valitud':>8s} {'OOS Sharpe':>12s}")
w("   " + "-" * 48)
oos_kogu = []
i = 504                      # 2 aastat
while i + 126 < len(M):
    tr = M.iloc[i - 504:i]
    te = M.iloc[i:i + 126]
    val = [c for c in M.columns if sh(tr[c]) > 0.25]
    if len(val) >= 5:
        k = korv(te, val)
        oos_kogu.append(k)
        w(f"   {str(te.index[0].date()):>11s}..{str(te.index[-1].date()):>11s} "
          f"{len(val):8d} {sh(k):+12.2f}")
    i += 126

if oos_kogu:
    kogu = pd.concat(oos_kogu)
    w("")
    w(f"   KÕIK OOS-perioodid kokku: Sharpe {sh(kogu):+.2f}  ({len(kogu)} päeva)")
    pos = sum(1 for k in oos_kogu if sh(k) > 0)
    w(f"   positiivseid aknaid: {pos}/{len(oos_kogu)}")
    sk = 0.10 / (kogu.std() * math.sqrt(252))
    eq = (1 + kogu * sk).cumprod()
    w(f"   10% vol sihiga: CAGR {100*(eq.iloc[-1]**(252/len(kogu))-1):+.1f}%  "
      f"maxDD {100*float((eq/eq.cummax()-1).min()):+.1f}%")
w("VALMIS")
