"""
OTSUSTAV TEST: kas JP225 ja SPX paevabaarid on OIGESTI joondatud?

MIKS SEE ON KRIITILINE:
run_jp225_integrity.py test 4 naitas, et signaal tootab ka siis, kui
votta SPX TANANE liikumine (Sharpe +1.54) — mis on tulevikuinfo.
Kaks voimalikku seletust:
  (a) PARIS: JP225 sessioon (00-06 UTC) EELNEB SPX sessioonile (13:30-20
      UTC) samal kuupaeval, seega on nad samal paeval kaasliikuvad. See
      ei riku lag-1 tulemust.
  (b) VIGA: kuupaevasildid on uhe voera nihkes ja lag-1 "serv" on
      tegelikult sama-paeva kaasliikumine, mida EI SAA kaubelda.

KUIDAS VAHET TEHA — FUUSIKA:
JP225 AVANEMISLUNK (Open_D / Close_{D-1}) tekib ajal, mil Jaapani turg
on KINNI. Sel ajal juhtus tapselt uks asi: SPX sessioon paeval D-1.
Seega PEAB lunk korreleeruma SPX paeva D-1 tootlusega ja MITTE
paeva D omaga (mis pole veel juhtunud).

Kui lunga korrelatsiooni tipp on lag=1 --> kuupaevad on OIGED.
Kui tipp on lag=0 --> andmed on nihkes ja kogu tulemus on prugi.
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import research as R

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open", "High", "Low", "Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

def corr_p(a, b):
    m = a.notna() & b.notna()
    a, b = a[m], b[m]
    n = len(a)
    if n < 30: return 0.0, 1.0, n
    r = float(np.corrcoef(a, b)[0, 1])
    if abs(r) >= 1: return r, 0.0, n
    t = r * math.sqrt((n - 2) / (1 - r * r))
    p = math.erfc(abs(t) / math.sqrt(2))
    return r, p, n

jp, spx, nas = load("JP225"), load("SPX"), load("NAS100")
ix = jp.index.intersection(spx.index).intersection(nas.index)
jp, spx, nas = jp.reindex(ix), spx.reindex(ix), nas.reindex(ix)

jp_gap = jp["Open"] / jp["Close"].shift(1) - 1
jp_intr = jp["Close"] / jp["Open"] - 1
spx_r = spx["Close"] / spx["Close"].shift(1) - 1
spx_intr = spx["Close"] / spx["Open"] - 1

print("=" * 100)
print("1) JP225 AVANEMISLÜNK vs SPX — kus on korrelatsiooni tipp?")
print("=" * 100)
print("   Lünk tekib ÖÖSEL, kui Jaapani turg on kinni. Füüsika nõuab tippu lag=1 juures.")
print()
print(f"   {'nihe':>22s} {'r':>8s} {'p':>12s} {'n':>6s}")
print("   " + "-" * 50)
for lag in (-1, 0, 1, 2, 3):
    lbl = {(-1): "lag=-1 (SPX HOMME)", 0: "lag=0  (SPX TÄNA)",
           1: "lag=1  (SPX EILE)", 2: "lag=2  (2 p tagasi)",
           3: "lag=3  (3 p tagasi)"}[lag]
    r, p, n = corr_p(jp_gap, spx_r.shift(lag))
    star = " <== TIPP" if lag == 1 else ""
    print(f"   {lbl:>22s} {r:+8.3f} {p:12.2e} {n:6d}{star}")

print()
print("=" * 100)
print("2) SAMA, PÄEVASISESE osa peal (see, mida kaupleme)")
print("=" * 100)
print(f"   {'nihe':>22s} {'r':>8s} {'p':>12s} {'n':>6s}")
print("   " + "-" * 50)
for lag in (-1, 0, 1, 2, 3):
    lbl = {(-1): "lag=-1 (SPX HOMME)", 0: "lag=0  (SPX TÄNA)",
           1: "lag=1  (SPX EILE)", 2: "lag=2  (2 p tagasi)",
           3: "lag=3  (3 p tagasi)"}[lag]
    r, p, n = corr_p(jp_intr, spx_r.shift(lag))
    print(f"   {lbl:>22s} {r:+8.3f} {p:12.2e} {n:6d}")

print()
print("=" * 100)
print("3) VASTUPIDINE SUUND — kas JP225 päevasisene ennustab SAMA PÄEVA SPX-i?")
print("=" * 100)
print("   Kui JA, siis lag=0 'tulevikuefekt' on lihtsalt Aasia->USA kaasliikumine")
print("   (JP225 sessioon LÕPEB 06 UTC, SPX ALGAB 13:30 UTC — Aasia on EES).")
print()
r, p, n = corr_p(spx_intr, jp_intr)
print(f"   SPX päevasisene (täna)  vs  JP225 päevasisene (täna):  r={r:+.3f}  p={p:.2e}")
r, p, n = corr_p(spx_intr, jp_intr.shift(-1))
print(f"   SPX päevasisene (täna)  vs  JP225 päevasisene (HOMME): r={r:+.3f}  p={p:.2e}")

print()
print("=" * 100)
print("4) SPX_h1 KONTROLL — mis kellaaegadel SPX päevabaar tegelikult jookseb?")
print("=" * 100)
try:
    h1 = pd.read_csv(os.path.join(R.DATA, "SPX_h1.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    hrs = sorted(set(h1.index.hour))
    print(f"   SPX_h1 tunnid andmetes (UTC): {hrs}")
    print(f"   vahemik: {h1.index[0]} .. {h1.index[-1]}")
    d0 = h1.index.normalize()
    first = h1.groupby(d0).head(1)
    last = h1.groupby(d0).tail(1)
    print(f"   esimene baar päevas: kõige sagedasem tund = {pd.Series(first.index.hour).mode().iloc[0]}")
    print(f"   viimane baar päevas: kõige sagedasem tund = {pd.Series(last.index.hour).mode().iloc[0]}")
    # kas paevabaari Close vastab h1 viimasele Close'ile samal kuupaeval?
    lc = last["Close"].copy(); lc.index = last.index.normalize()
    cmp_ = pd.concat([spx["Close"].rename("d"), lc.rename("h")], axis=1).dropna()
    if len(cmp_) > 20:
        diff = (cmp_["d"] / cmp_["h"] - 1).abs()
        print(f"   päevabaari Close vs h1 viimane Close samal kuupäeval: "
              f"mediaan erinevus {1e4*diff.median():.1f}bp  (n={len(cmp_)})")
        print(f"   --> kui ~0bp, siis päevabaari kuupäev = sama kalendripäev nagu h1-l")
except Exception as e:
    print(f"   SPX_h1 kontroll ebaõnnestus: {e}")

print()
print("=" * 100)
print("5) KOKKUVÕTE")
print("=" * 100)
rg1, pg1, _ = corr_p(jp_gap, spx_r.shift(1))
rg0, pg0, _ = corr_p(jp_gap, spx_r.shift(0))
if abs(rg1) > abs(rg0) * 1.5 and pg1 < 1e-10:
    print("   [OK] Lünga korrelatsiooni tipp on lag=1 juures, nagu füüsika nõuab.")
    print("        => kuupäevad on ÕIGESTI joondatud, lag-1 signaal on PÄRIS ja kaubeldav.")
    print(f"        lünk vs SPX eile: r={rg1:+.3f}   lünk vs SPX täna: r={rg0:+.3f}")
else:
    print("   [!!] Lünga tipp EI OLE lag=1 juures — andmed võivad olla nihkes.")
    print(f"        lünk vs SPX eile: r={rg1:+.3f}   lünk vs SPX täna: r={rg0:+.3f}")
