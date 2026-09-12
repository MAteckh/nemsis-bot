"""
MIKS serv puudub 2016-2021 ja on olemas 2021-2026?

Kaks TAIESTI erinevat seletust, millel on vastupidised jareldused:

  (A) REGIIMIMUUTUS: seos ise tekkis alles hiljuti (nt Nikkei
      koosseis muutus tehnoloogiaraskemaks). Jareldus: seos voib
      sama aekki KADUDA. Ei saa usaldada.

  (B) KULUDE SUHE: seos on KOGU AEG sama tugev, aga JP225
      paevasisene volatiilsus kasvas, nii et sama korrelatsioon
      hakkas katma 6bp tehingukulu. Jareldus: serv pusib niikaua,
      kui volatiilsus pusib — ja see on MOODETAV ette.

Test: mootame korrelatsiooni ja volatiilsust eraldi poolte kaupa.
Kui r on stabiilne ja ainult vol kasvas => (B).
Kui r ise kasvas => (A).
"""
import warnings; warnings.filterwarnings("ignore")
import os, math
import numpy as np, pandas as pd
import research as R

def load(s):
    d = pd.read_csv(os.path.join(R.DATA, f"{s}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

def corr_p(a, b):
    m = a.notna() & b.notna(); a, b = a[m], b[m]; n = len(a)
    if n < 30: return 0.0, 1.0, n
    r = float(np.corrcoef(a, b)[0,1])
    t = r*math.sqrt((n-2)/max(1-r*r, 1e-12))
    return r, math.erfc(abs(t)/math.sqrt(2)), n

jp, spx = load("JP225"), load("SPX")
ix = jp.index.intersection(spx.index); jp, spx = jp.reindex(ix), spx.reindex(ix)
y = jp["Close"]/jp["Open"]-1; y = y[y.abs() < 0.25]
r = spx["Close"]/spx["Close"].shift(1)-1
z = (r/r.rolling(60).std()).shift(1).reindex(y.index)
COST = 6/1e4

print("=" * 100)
print("1) ON SEE REGIIMIMUUTUS (A) VÕI KULUDE SUHE (B)?")
print("=" * 100)
print(f"  {'periood':22s} {'r(z, päevasisene)':>19s} {'p':>11s} {'JP225 vol':>11s} "
      f"{'kulu/vol':>10s} {'signaal/kulu':>13s}")
print("  " + "-" * 92)
n = len(y); q = n//4
segs = [("2016-2018", slice(0,q)), ("2018-2021", slice(q,2*q)),
        ("2021-2024", slice(2*q,3*q)), ("2024-2026", slice(3*q,None))]
for lbl, sl in segs:
    yy, zz = y.iloc[sl], z.iloc[sl]
    rr, pp, _ = corr_p(yy, zz)
    vol = float(yy.std())
    # oodatav tootlus tehingu kohta ~ r * vol (uhikdispersiooniga signaalil)
    edge = abs(rr)*vol
    print(f"  {lbl:22s} {rr:+19.3f} {pp:11.2e} {100*vol:10.2f}% "
          f"{100*COST/vol:9.2f}% {edge/COST:13.2f}x")

print()
print("=" * 100)
print("2) SAMA, POOLTE KAUPA (nagu robustsustestis)")
print("=" * 100)
mid = n//2
for lbl, sl in [("1. pool 2016-2021", slice(0,mid)), ("2. pool 2021-2026", slice(mid,None))]:
    yy, zz = y.iloc[sl], z.iloc[sl]
    rr, pp, nn = corr_p(yy, zz)
    vol = float(yy.std())
    print(f"  {lbl:22s} r={rr:+.3f}  p={pp:.2e}  n={nn}  "
          f"JP225 vol {100*vol:.2f}%  serv/kulu {abs(rr)*vol/COST:.2f}x")

print()
print("=" * 100)
print("3) KAS SEOS ISE ON BONFERRONI-KINDEL? (441 paari otsiti algses skannis)")
print("=" * 100)
rr, pp, nn = corr_p(y, z)
print(f"  kogu periood: r={rr:+.3f}  p={pp:.3e}  n={nn}")
print(f"  Bonferroni 441 testi kohta: lävend p < {0.05/441:.2e}")
print(f"  => seos ise {'LÄBIB' if pp < 0.05/441 else 'EI LÄBI'} "
      f"({pp/(0.05/441):.1e}x lävendist {'väiksem' if pp < 0.05/441 else 'suurem'})")
r1, p1, _ = corr_p(y.iloc[:mid], z.iloc[:mid])
print(f"\n  1. pool eraldi: r={r1:+.3f}  p={p1:.2e}  "
      f"{'LÄBIB' if p1 < 0.05/441 else 'EI LÄBI'} Bonferroni")
r2, p2, _ = corr_p(y.iloc[mid:], z.iloc[mid:])
print(f"  2. pool eraldi: r={r2:+.3f}  p={p2:.2e}  "
      f"{'LÄBIB' if p2 < 0.05/441 else 'EI LÄBI'} Bonferroni")

print()
print("=" * 100)
print("4) JP225 PÄEVASISENE VOLATIILSUS AJAS (kas praegu on kõrge või madal?)")
print("=" * 100)
rv = y.rolling(252).std()*100
for yr in sorted(set(y.index.year)):
    sub = rv[rv.index.year == yr].dropna()
    if len(sub) == 0: continue
    bar = "#"*int(sub.mean()*12)
    print(f"  {yr}  {sub.mean():5.2f}%  {bar}")
cur = float(rv.dropna().iloc[-1]); hist = float(rv.dropna().median())
print(f"\n  praegune 252p vol: {cur:.2f}%   ajalooline mediaan: {hist:.2f}%")
print(f"  serv/kulu praegu: {abs(rr)*cur/100/COST:.2f}x   "
      f"(alla 1.0x = kulud söövad serva ära)")
print(f"\n  KRIITILINE LÄVEND: vol peab olema üle "
      f"{100*COST/abs(rr):.2f}%, et serv kataks kulud.")
