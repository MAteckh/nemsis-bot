"""
RISTLOIKE-SIGNAALID — 13 instrumenti, pikk JA luhike korraga.

MIKS SEE, MITTE MIDAGI MUUD:
Kuunlamustrite test (run_candles.py) leidis kolm "voitjat", mis koik
osutusid AINULT-PIKKADEKS signaalideks varal, mille triiv on +62%/a.
Muster ei ennustanud midagi — ta juhtus olema sees, kui BTC tousis.

Iga AINULT-PIKK signaal on selle vea suhtes haavatav. Ristloike-signaal
ei ole: me oleme korraga PIKK parimates ja LUHIKE halvimates, seega
turu uldine triiv TAANDUB VALJA. Kui tulemus jaab plussi, siis tuleb
see jarjestusest, mitte triivist.

Lisaks sobib see kasutaja raamistikku: 13 instrumenti, sage
umberkaalumine, vaikesed positsioonid.

TESTIME:
  A) ristloike MOMENTUM  — osta tugevaimad, muu norgimad
  B) ristloike POORE     — osta norgimad, muu tugevaimad
  C) ristloike VOLATIILSUS — osta madala vol, muu korge vol

VOLATIILSUSNORMEERIMINE ON KOHUSTUSLIK: BTC paevane vahemik on 3.5%,
EURUSD-l 0.53%. Ilma normeerimiseta domineeriks krupto koike ja me
mootaksime jalle ainult krupto triivi.
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import research as R

OUT = "crosssection_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()

# run_small_tp.py kinnitatud kulu-kolblikud
SYMS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
        "EURJPY", "XAUUSD", "WTI", "COPPER", "BTCUSD", "ETHUSD"]
COST_BP = {"EURUSD": 0.5, "GBPUSD": 0.6, "USDJPY": 0.6, "AUDUSD": 0.9,
           "NZDUSD": 1.3, "USDCAD": 0.9, "USDCHF": 0.9, "EURJPY": 0.8,
           "XAUUSD": 0.4, "WTI": 1.5, "COPPER": 1.2, "BTCUSD": 1.6,
           "ETHUSD": 0.9}


def load(s):
    p = os.path.join(R.DATA, f"{s}_d.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    d["close"] = pd.to_numeric(d["close"], errors="coerce")
    return d["close"].dropna()


px = pd.DataFrame({s: load(s) for s in SYMS}).dropna(how="all")
px = px.ffill().dropna()
ret = px.pct_change()
kulu = pd.Series({s: 2 * COST_BP[s] / 1e4 for s in px.columns})

w(f"andmed {px.index[0].date()} .. {px.index[-1].date()}  "
  f"{len(px)} päeva, {len(px.columns)} instrumenti")
w(f"instrumendid: {', '.join(px.columns)}")


def aja(sig, hoia=1, k=3):
    """sig: skoor (suurem = osta). Pikk top-k, lühike bottom-k, vol-normeeritud."""
    vol = ret.rolling(60).std()
    s = sig.copy()
    # jarjesta iga paev
    rank = s.rank(axis=1, ascending=False)
    n = s.notna().sum(axis=1)
    kaal = pd.DataFrame(0.0, index=s.index, columns=s.columns)
    kaal[rank.le(k)] = 1.0
    kaal[rank.gt(n.values[:, None] - k)] = -1.0
    # vol-normeerimine: vordne RISK, mitte vordne raha
    kaal = kaal / vol.replace(0, np.nan)
    # normaliseeri, et kogu bruto = 1
    bruto = kaal.abs().sum(axis=1).replace(0, np.nan)
    kaal = kaal.div(bruto, axis=0).fillna(0.0)
    # hoia N paeva
    if hoia > 1:
        kaal = kaal.rolling(hoia).mean().fillna(0.0)
    kaal = kaal.shift(1).fillna(0.0)          # signaal eile, kauple tana
    bruto_ret = (kaal * ret).sum(axis=1)
    kaib = (kaal - kaal.shift(1)).abs()
    kulud = (kaib * kulu).sum(axis=1)
    return (bruto_ret - kulud).fillna(0.0)


def stat(x, nimi):
    if x.std() == 0:
        return None
    sh = x.mean() / x.std() * math.sqrt(252)
    eq = (1 + x).cumprod()
    cagr = eq.iloc[-1] ** (252 / len(x)) - 1 if eq.iloc[-1] > 0 else -1
    m = len(x) // 2
    s1 = x.iloc[:m].mean() / x.iloc[:m].std() * math.sqrt(252)
    s2 = x.iloc[m:].mean() / x.iloc[m:].std() * math.sqrt(252)
    t = x.mean() / x.std() * math.sqrt(len(x))
    return dict(nimi=nimi, sh=sh, cagr=cagr, s1=s1, s2=s2, t=t,
                p=math.erfc(abs(t) / math.sqrt(2)))


tulemused = []
w("")
w("=" * 96)
w("A) RISTLÕIKE MOMENTUM — osta tugevaimad, müü nõrgimad")
w("=" * 96)
w(f"{'lookback':>9s} {'hoia':>5s} {'k':>3s} {'Sharpe':>8s} {'CAGR':>8s} "
  f"{'1.pool':>8s} {'2.pool':>8s} {'p':>9s}")
w("-" * 96)
for lb in (5, 20, 60, 120):
    for hoia in (1, 5, 20):
        for k in (2, 3, 4):
            sig = px / px.shift(lb) - 1
            x = aja(sig, hoia, k)
            r = stat(x, f"mom{lb}/h{hoia}/k{k}")
            if r is None:
                continue
            tulemused.append(r)
            mark = "  <<<" if (r["sh"] > 0.5 and r["s1"] > 0 and r["s2"] > 0) else ""
            w(f"{lb:9d} {hoia:5d} {k:3d} {r['sh']:+8.2f} {100*r['cagr']:+7.1f}% "
              f"{r['s1']:+8.2f} {r['s2']:+8.2f} {r['p']:9.4f}{mark}")

w("")
w("=" * 96)
w("B) RISTLÕIKE PÖÖRE — osta nõrgimad, müü tugevaimad")
w("=" * 96)
w(f"{'lookback':>9s} {'hoia':>5s} {'k':>3s} {'Sharpe':>8s} {'CAGR':>8s} "
  f"{'1.pool':>8s} {'2.pool':>8s} {'p':>9s}")
w("-" * 96)
for lb in (1, 2, 3, 5, 10):
    for hoia in (1, 3, 5):
        for k in (2, 3, 4):
            sig = -(px / px.shift(lb) - 1)
            x = aja(sig, hoia, k)
            r = stat(x, f"rev{lb}/h{hoia}/k{k}")
            if r is None:
                continue
            tulemused.append(r)
            mark = "  <<<" if (r["sh"] > 0.5 and r["s1"] > 0 and r["s2"] > 0) else ""
            w(f"{lb:9d} {hoia:5d} {k:3d} {r['sh']:+8.2f} {100*r['cagr']:+7.1f}% "
              f"{r['s1']:+8.2f} {r['s2']:+8.2f} {r['p']:9.4f}{mark}")

w("")
w("=" * 96)
w("KOKKUVÕTE")
w("=" * 96)
df = pd.DataFrame(tulemused)
N = len(df)
BONF = 0.05 / N
w(f"  teste kokku {N}, Bonferroni lävend p < {BONF:.6f}")
labib = df[(df["p"] < BONF) & (df["sh"] > 0)]
w(f"  Bonferroni läbib (ja positiivne): {len(labib)}")
molemad = df[(df["sh"] > 0.5) & (df["s1"] > 0) & (df["s2"] > 0)]
w(f"  Sharpe>0.5 JA mõlemad pooled +: {len(molemad)} / {N}")
w(f"  positiivseid Sharpe: {(df['sh'] > 0).sum()} / {N}")
w(f"  keskmine Sharpe: {df['sh'].mean():+.2f}")
if len(molemad):
    w("")
    w("  Kandidaadid:")
    for _, r in molemad.sort_values("sh", ascending=False).iterrows():
        w(f"     {r['nimi']:18s} Sharpe {r['sh']:+.2f}  "
          f"(1.pool {r['s1']:+.2f} / 2.pool {r['s2']:+.2f})  p={r['p']:.4f}")
w("VALMIS")
