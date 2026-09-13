"""
TUGI/VASTUPANU TAGASILUKKAMINE — kasutaja idee, aus test.

IDEE: leia tugi- ja vastupanutasemed. Oota, kuni hind neid TESTIB ja
sealt TAGASI PORDUB. Mine tagasiporde suunas. Vota vaike kasum.

METOODIKA, MIDA MA SEEKORD ALGUSEST PEALE JARGIN (opitud vigadest):
  1. Testi koigepealt TOORAST ENNUSTUSVOIMET, ilma TP/SL-ita.
     Kui tagasilukkamine ei ennusta jargmise paeva suunda, ei paasta
     teda ukski TP/SL kombinatsioon.
  2. PUHAS WALK-FORWARD kohe, mitte parast. Vali parameetrid ainult
     1. poole pealt, testi 2. poolel.
  3. NULL-JAOTUS (oige konstruktsiooniga: juhuslikusta SUUND, kulud
     jaavad).
  4. Kontrolli, kas tulemus on lihtsalt triiv (vordle KOIGI paevadega).

MAARATLUSED:
  vastupanu = viimase N baari korgeim tipp (valja arvatud viimased 2)
  tugi      = viimase N baari madalaim pohi (valja arvatud viimased 2)
  tagasilukkamine vastupanult = high >= vastupanu JA close < vastupanu
     (vurr labi taseme, aga sulgemine tagasi allpool) => oota LANGUST
  pordumine toelt = low <= tugi JA close > tugi => oota TOUSU
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import research as R

rng = np.random.default_rng(2609)
OUT = "sr_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

SYMS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
        "EURJPY", "XAUUSD", "XAGUSD", "WTI", "COPPER", "SPX", "NAS100",
        "GER40", "JP225", "BTCUSD", "ETHUSD"]
COST = {"EURUSD": .5, "GBPUSD": .6, "USDJPY": .6, "AUDUSD": .9, "NZDUSD": 1.3,
        "USDCAD": .9, "USDCHF": .9, "EURJPY": .8, "XAUUSD": .4, "XAGUSD": 1.6,
        "WTI": 1.5, "COPPER": 1.2, "SPX": .4, "NAS100": .3, "GER40": .3,
        "JP225": .5, "BTCUSD": 1.6, "ETHUSD": .9}


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
    # kuunlamustrid vajavad PARIS Open'i
    if float(((d["close"] - d["open"]).abs() / d["close"]).median()) < 1e-5:
        return None
    return d if len(d) > 800 else None


DATA = {s: load(s) for s in SYMS}
puudu = [s for s, v in DATA.items() if v is None]
DATA = {k: v for k, v in DATA.items() if v is not None}
w(f"instrumente: {len(DATA)}" + (f"   (välja: {', '.join(puudu)} — Open katki)" if puudu else ""))


def sr_signaal(d, N, tol=0.0):
    """+1 = pöördumine toelt (oota tõusu), -1 = tagasilükkamine vastupanult."""
    h, l, c = d["high"], d["low"], d["close"]
    # tase EELMISTE baaride pealt (välista jooksev baar => ei vaata tulevikku)
    vast = h.rolling(N).max().shift(1)
    tugi = l.rolling(N).min().shift(1)
    rej = (h >= vast * (1 - tol)) & (c < vast)
    bou = (l <= tugi * (1 + tol)) & (c > tugi)
    sg = pd.Series(0.0, index=d.index)
    sg[bou] = 1.0
    sg[rej & ~bou] = -1.0
    return sg.shift(1).fillna(0.0)          # muster eile, kauple täna


def sh(x):
    x = np.asarray(x)
    x = x[np.isfinite(x)]
    return float(x.mean() / x.std() * math.sqrt(252)) if len(x) > 40 and x.std() > 0 else 0.0


# ── ehita kõik kandidaadid ────────────────────────────────────────
kand, toorik = {}, {}
for s, d in DATA.items():
    y = (d["close"] / d["open"] - 1).where(lambda v: v.abs() < 0.25, 0.0)
    rt = 2 * COST[s] / 1e4
    for N in (10, 20, 50, 100):
        sg = sr_signaal(d, N)
        if int((sg != 0).sum()) < 100:
            continue
        kand[f"{s} SR{N}"] = (sg * y - (sg != 0).astype(float) * rt).fillna(0.0)
        toorik[f"{s} SR{N}"] = (sg, y, rt)

w(f"kandidaate: {len(kand)}")

w("")
w("=" * 92)
w("1) TOORES ENNUSTUSVÕIME — kas S/R pööre ennustab järgmist päeva?")
w("=" * 92)
w(f"  {'instrument':10s} {'N':>4s} {'signaale':>9s} {'bruto bp':>10s} "
  f"{'NETO bp':>9s} {'t':>7s} {'vs KÕIK päevad':>16s}")
w("  " + "-" * 70)
read = []
for nimi, (sg, y, rt) in sorted(toorik.items()):
    s_ = nimi.split()[0]
    x = (sg * y)[sg != 0].dropna()
    if len(x) < 100:
        continue
    t = x.mean() / x.std() * math.sqrt(len(x)) if x.std() > 0 else 0
    koik = y.dropna()
    vahe = x.mean() - np.sign(x.mean()) * abs(koik.mean())
    read.append(dict(nimi=nimi, n=len(x), bruto=x.mean(), neto=x.mean() - rt, t=t))
    w(f"  {s_:10s} {nimi.split('SR')[1]:>4s} {len(x):9d} {1e4*x.mean():+9.2f} "
      f"{1e4*(x.mean()-rt):+8.2f} {t:+7.2f} {1e4*vahe:+15.2f}")

df = pd.DataFrame(read)
w("")
w(f"  NETO plussis: {(df['neto'] > 0).sum()} / {len(df)}")
w(f"  keskmine NETO: {1e4*df['neto'].mean():+.2f}bp")
w(f"  |t|>2: {(df['t'].abs() > 2).sum()} / {len(df)}  "
  f"(juhuslikult oodatav {0.0455*len(df):.1f})")

# ── PUHAS WALK-FORWARD ────────────────────────────────────────────
M = pd.DataFrame(kand).fillna(0.0)
m = len(M) // 2
A, B = M.iloc[:m], M.iloc[m:]


def korv(dfp, cols):
    if not cols:
        return pd.Series(0.0, index=dfp.index)
    Z = dfp[cols] / dfp[cols].std().replace(0, np.nan)
    return Z.mean(axis=1).fillna(0.0)


w("")
w("=" * 92)
w("2) PUHAS WALK-FORWARD (vali 1. poole pealt, testi 2. poolel)")
w("=" * 92)
for lavi in (0.0, 0.25, 0.5):
    val = [c for c in M.columns if sh(A[c]) > lavi]
    if not val:
        w(f"   lävend >{lavi:.2f}: ükski ei kvalifitseeru")
        continue
    w(f"   lävend Sharpe>{lavi:.2f}: {len(val):3d} signaali   "
      f"IS {sh(korv(A, val)):+.2f}  ->  OOS {sh(korv(B, val)):+.2f}")
    val2 = [c for c in M.columns if sh(B[c]) > lavi]
    w(f"      vastupidi ({len(val2)} sign.): OOS {sh(korv(A, val2)):+.2f}")

# ── NULL ──────────────────────────────────────────────────────────
def labib(sgv, yv, rt):
    x = sgv * yv - (sgv != 0).astype(float) * rt
    x = np.nan_to_num(x)
    mm = len(x) // 2
    return sh(x) > 0.25 and sh(x[:mm]) > 0 and sh(x[mm:]) > 0


n_real = sum(1 for sg, y, rt in toorik.values()
             if labib(sg.values, y.reindex(sg.index).values, rt))
sims = []
for _ in range(30):
    n_ok = 0
    for sg, y, rt in toorik.values():
        v = sg.values.copy()
        nz = v != 0
        if nz.sum() < 50:
            continue
        v[nz] = rng.choice([-1.0, 1.0], size=int(nz.sum()))
        if labib(v, y.reindex(sg.index).values, rt):
            n_ok += 1
    sims.append(n_ok)
sims = np.array(sims)
w("")
w("=" * 92)
w("3) NULL-JAOTUS (juhuslikustatud suund, kulud jäävad)")
w("=" * 92)
w(f"   PÄRIS: {n_real} läbijat {len(toorik)}-st")
w(f"   MÜRA (30 katset): keskmine {sims.mean():.1f}, max {sims.max()}")
w(f"   p = {float((sims >= n_real).mean()):.3f}")
w("VALMIS")
