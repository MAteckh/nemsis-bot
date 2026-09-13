"""
KOMBINEERI KOIK ELLUJAANUD SIGNAALID — Medallioni pohimotte test.

Medallion ei kasuta uht tugevat signaali. Ta kasutab tuhandeid norku,
millest ukski uksinda ei kolba, aga mis koos annavad Sharpe ~2.

Matemaatika: N soltumatut signaali Sharpe S annab kokku S*sqrt(N).
  2 x Sharpe 0.5  =>  0.71
  4 x Sharpe 0.5  =>  1.00
  9 x Sharpe 0.5  =>  1.50
AGA see kehtib AINULT siis, kui nad on omavahel korreleerimata.

Kogume kokku koik, mis selle projekti jooksul ellu jai, ja vaatame
korrelatsioonimaatriksit.

AUS HOIATUS, mis kehtib kogu selle faili kohta:
need signaalid on VALITUD paljude testitute hulgast. Valitud voitjate
kombineerimine ULEHINDAB tulemust — sama mitmese testimise probleem,
mis on terve projekti jooksul kandidaate tapnud. Tulemust tuleb
lugeda ULEMISE PIIRINA, mitte ootusena.
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import strategies as S
import research as R

OUT = "combine_tulemus.txt"

def w(s):
    print(s, flush=True)
    with open(OUT, "a", encoding="utf-8") as f:
        f.write(s + "\n")

open(OUT, "w", encoding="utf-8").close()


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
    return d.dropna()


sig = {}

# ── 1. JP225 paevasisene, SPX signaal, |z|>1.0, 3% stopp ──────────
jp, spx = load("JP225"), load("SPX")
ix = jp.index.intersection(spx.index)
jp2, spx2 = jp.reindex(ix), spx.reindex(ix)
o, h, l, c = jp2["open"], jp2["high"], jp2["low"], jp2["close"]
rr = spx2["close"] / spx2["close"].shift(1) - 1
z = (rr / rr.rolling(60).std()).shift(1)
wz = (np.sign(z) * (z.abs() > 1.0)).fillna(0.0)
STOP = 0.03
ls, ss = (l / o - 1) <= -STOP, (h / o - 1) >= STOP
ret = np.where(wz > 0, np.where(ls, -STOP, c / o - 1),
      np.where(wz < 0, np.where(ss, -STOP, 1 - c / o), 0.0))
ret = pd.Series(ret, index=o.index).where(lambda s_: s_.abs() < 0.25, 0.0)
sig["JP225 päevasisene"] = (ret - (wz != 0).astype(float) * 6 / 1e4).fillna(0.0)

# ── 2. GER40 -> JP225 paevasisene ─────────────────────────────────
ger = load("GER40")
ix2 = jp.index.intersection(ger.index)
jp3, ger2 = jp.reindex(ix2), ger.reindex(ix2)
y3 = (jp3["close"] / jp3["open"] - 1).where(lambda s_: s_.abs() < 0.25, 0.0)
rg = ger2["close"] / ger2["close"].shift(1) - 1
zg = (rg / rg.rolling(60).std()).shift(1)
wg = (np.sign(zg) * (zg.abs() > 1.0)).fillna(0.0)
sig["GER40→JP225"] = (wg * y3 - (wg != 0).astype(float) * 6 / 1e4).fillna(0.0)

# ── 3. USDCAD -> XAUUSD paevasisene ───────────────────────────────
xau, cad = load("XAUUSD"), load("USDCAD")
ix3 = xau.index.intersection(cad.index)
xau2, cad2 = xau.reindex(ix3), cad.reindex(ix3)
y4 = (xau2["close"] / xau2["open"] - 1).where(lambda s_: s_.abs() < 0.25, 0.0)
rc = cad2["close"] / cad2["close"].shift(1) - 1
zc = (rc / rc.rolling(60).std()).shift(1)
wc = (np.sign(zc) * (zc.abs() > 1.0)).fillna(0.0)
sig["USDCAD→XAUUSD"] = (wc * y4 - (wc != 0).astype(float) * 3 / 1e4).fillna(0.0)

# ── 4. Ristloike momentum (lb20/h20/k3) ───────────────────────────
XS = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF",
      "EURJPY", "XAUUSD", "WTI", "COPPER", "BTCUSD", "ETHUSD"]
CB = {"EURUSD": .5, "GBPUSD": .6, "USDJPY": .6, "AUDUSD": .9, "NZDUSD": 1.3,
      "USDCAD": .9, "USDCHF": .9, "EURJPY": .8, "XAUUSD": .4, "WTI": 1.5,
      "COPPER": 1.2, "BTCUSD": 1.6, "ETHUSD": .9}
px = pd.DataFrame({s_: load(s_)["close"] for s_ in XS}).ffill().dropna()
rx = px.pct_change()
kx = pd.Series({s_: 2 * CB[s_] / 1e4 for s_ in px.columns})
vol = rx.rolling(60).std()
sg = px / px.shift(20) - 1
rank = sg.rank(axis=1, ascending=False)
nn = sg.notna().sum(axis=1)
kaal = pd.DataFrame(0.0, index=sg.index, columns=sg.columns)
kaal[rank.le(3)] = 1.0
kaal[rank.gt(nn.values[:, None] - 3)] = -1.0
kaal = kaal / vol.replace(0, np.nan)
kaal = kaal.div(kaal.abs().sum(axis=1).replace(0, np.nan), axis=0).fillna(0.0)
kaal = kaal.rolling(20).mean().fillna(0.0).shift(1).fillna(0.0)
sig["ristlõike momentum"] = ((kaal * rx).sum(axis=1)
                             - ((kaal - kaal.shift(1)).abs() * kx).sum(axis=1)).fillna(0.0)

# ── 5. XAUUSD donchian(50) — praegune live-strateegia ─────────────
rd = S.simulate(load("XAUUSD"), S.sig_donchian, cfg={"lookback": 50},
                account_balance=200.0, pip_value=100.0)
eq = rd["equity"]
sig["XAUUSD donchian50"] = eq.pct_change().fillna(0.0)


def sharpe(x):
    x = x[x.notna()]
    return x.mean() / x.std() * math.sqrt(252) if x.std() > 0 else 0.0


w("=" * 92)
w("1) ÜKSIKUD SIGNAALID")
w("=" * 92)
w(f"{'signaal':24s} {'päevi':>7s} {'Sharpe':>8s} {'1.pool':>8s} {'2.pool':>8s}")
w("-" * 60)
for nimi, x in sig.items():
    m = len(x) // 2
    w(f"{nimi:24s} {len(x):7d} {sharpe(x):+8.2f} "
      f"{sharpe(x.iloc[:m]):+8.2f} {sharpe(x.iloc[m:]):+8.2f}")

# joonda uhele kalendrile
D = pd.DataFrame(sig).dropna(how="all").fillna(0.0)
D = D.loc[D.index >= max(s_.dropna().index[0] for s_ in sig.values())]

w("")
w("=" * 92)
w("2) KORRELATSIOONIMAATRIKS — see otsustab kõik")
w("=" * 92)
C = D.corr()
w("     " + " ".join(f"{n[:9]:>10s}" for n in C.columns))
for i, n in enumerate(C.index):
    w(f"{n[:16]:16s} " + " ".join(f"{C.iloc[i, j]:+10.2f}" for j in range(len(C.columns))))
kesk = (C.values[np.triu_indices_from(C.values, 1)]).mean()
w("")
w(f"   keskmine paariskorrelatsioon: {kesk:+.3f}")
w(f"   (mida lähemal nullile, seda rohkem kombineerimine aitab)")

w("")
w("=" * 92)
w("3) KOMBINATSIOON — võrdne RISK igale signaalile")
w("=" * 92)
Z = D / D.std()                      # vordne vol
komb = Z.mean(axis=1)
m = len(komb) // 2
parim = max(sharpe(D[c_]) for c_ in D.columns)
w(f"   parim üksik signaal      : Sharpe {parim:+.2f}")
w(f"   KOMBINATSIOON (kõik {len(D.columns)})   : Sharpe {sharpe(komb):+.2f}")
w(f"      1. pool {sharpe(komb.iloc[:m]):+.2f}   2. pool {sharpe(komb.iloc[m:]):+.2f}")
teoor = math.sqrt(sum(sharpe(D[c_])**2 for c_ in D.columns))
w(f"   teoreetiline maksimum (korrelatsioon 0): {teoor:+.2f}")
w("")
w("   Kombinatsioon ilma tugevaimata (kas nõrgad kannavad?):")
ilma = [c_ for c_ in D.columns if sharpe(D[c_]) < 1.0]
if ilma:
    k2 = (D[ilma] / D[ilma].std()).mean(axis=1)
    w(f"      {len(ilma)} nõrka signaali koos: Sharpe {sharpe(k2):+.2f}")
    for c_ in ilma:
        w(f"         {c_:24s} üksi {sharpe(D[c_]):+.2f}")

w("")
w("=" * 92)
w("4) AUS HOIATUS")
w("=" * 92)
w("   Need signaalid on VALITUD paljude testitute hulgast. Valitud")
w("   võitjate kombineerimine ÜLEHINDAB tulemust. Loe seda ÜLEMISE")
w("   PIIRINA, mitte ootusena.")
w("VALMIS")
