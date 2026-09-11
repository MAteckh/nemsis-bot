"""
OTSUSTAV TEST: kas leitud lead-lag seosed on KAUBELDAVAD või ainult
ajavööndi artefakt?

Hüpotees: SPX(eile) -> JP225(täna) seos tekib sellest, et Jaapani turg
avaneb PÄRAST USA sulgemist ja avanemishind juba sisaldab USA liikumist.
Kui nii, siis:
  - SPX ennustab JP225 AVANEMISLÜNKA (open/prev_close)   <- EI SAA KAUBELDA
  - SPX EI ennusta JP225 PÄEVASISEST (close/open)         <- SEDA SAAKS KAUBELDA

run_gapcheck.py kinnitas varem, et JP225/SPX/NAS100/GER40 on
kassaindeksid, millel on PÄRIS avanemis-/sulgemisaken - seega see
lahutus on nende puhul kehtiv (erinevalt FX-ist).
"""
import warnings; warnings.filterwarnings("ignore")
import os
import math
import numpy as np, pandas as pd
import research as R

def pearson(x, y):
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x)
    if n < 3: return 0.0, 1.0
    xm, ym = x - x.mean(), y - y.mean()
    den = math.sqrt((xm**2).sum() * (ym**2).sum())
    if den == 0: return 0.0, 1.0
    r = max(-0.999999, min(0.999999, float((xm*ym).sum()/den)))
    t = r * math.sqrt((n-2)/(1-r*r))
    return r, math.erfc(abs(t)/math.sqrt(2))

def load(sym):
    d = pd.read_csv(os.path.join(R.DATA, f"{sym}_d.csv"), parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    for c in ("Open","High","Low","Close"): d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()

# ainult PÄRIS avanemisaknaga kassaindeksid (run_gapcheck.py kinnitus)
CLEAN = ["SPX", "NAS100", "GER40", "JP225", "UK100"]
data = {s: load(s) for s in CLEAN}

print("=" * 104)
print("SEOSE LAHUTUS: AVANEMISLÜNK (ei saa kaubelda) vs PÄEVASISENE (saab kaubelda)")
print("=" * 104)
print(f"{'seos':22s} {'kogu (C->C)':>12s} {'LÜNK (O/prevC)':>15s} {'PÄEVASISENE (C/O)':>18s}")
print("-" * 104)

TESTS = [("SPX","JP225"), ("NAS100","JP225"), ("GER40","JP225"),
         ("SPX","GER40"), ("SPX","UK100"), ("NAS100","GER40"),
         ("JP225","GER40"), ("JP225","SPX")]

for a, b in TESTS:
    da, db = data[a], data[b]
    idx = da.index.intersection(db.index)
    da2, db2 = da.reindex(idx), db.reindex(idx)

    ra_cc = (da2["Close"]/da2["Close"].shift(1) - 1).shift(1)   # eilne A (close-to-close)
    rb_cc = db2["Close"]/db2["Close"].shift(1) - 1              # tänane B kogu
    rb_gap = db2["Open"]/db2["Close"].shift(1) - 1              # tänane B lünk
    rb_intr = db2["Close"]/db2["Open"] - 1                      # tänane B päevasisene

    out = []
    for target in (rb_cc, rb_gap, rb_intr):
        m = ra_cc.notna() & target.notna()
        m &= (ra_cc.abs() < 0.25) & (target.abs() < 0.25)
        r, p = pearson(ra_cc[m], target[m])
        out.append((r, p))
    (r_cc,p_cc), (r_gap,p_gap), (r_in,p_in) = out
    def fmt(r, p):
        star = "*" if p < 0.001 else (" " if p < 0.05 else " ")
        return f"{r:+.3f}{star}"
    print(f"  {a+' -> '+b:20s} {fmt(r_cc,p_cc):>12s} {fmt(r_gap,p_gap):>15s} {fmt(r_in,p_in):>18s}")

print("-" * 104)
print("  * = p < 0.001")
print()
print("  TÕLGENDUS: kui LÜNK on tugev aga PÄEVASISENE ~0, siis seos on")
print("  ajavööndi artefakt — info on avanemishinnas juba sees ja seda")
print("  EI SAA kaubelda. Kui PÄEVASISENE oleks tugev, oleks see päris serv.")
