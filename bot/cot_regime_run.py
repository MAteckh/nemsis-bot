"""
cot_regime_run.py — 9 eelregistreeritud rezhiimi x 2 universumit = 18 testi.
"""
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R
import cot_regime as G

al = R.ehita_alus(sufiks="_d25")
M = G.rezhiimi_pertsentiilid(al)
KAH, SAB = G.seisund(M)
POOL = pd.Timestamp("2016-08-30")     # A1 murdepunkt


def moodikud(x, nimi=""):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    if len(x) < 20:
        return None
    sd = x.std(ddof=1)
    eq = np.cumprod(1 + x)
    dd = float((eq / np.maximum.accumulate(eq) - 1).min())
    return dict(nimi=nimi, n=len(x), bp=float(x.mean() * 1e4),
                sh=float(x.mean() / sd * math.sqrt(52)) if sd > 0 else 0.0,
                kokku=float(eq[-1] - 1), dd=dd,
                t=float(x.mean() / sd * math.sqrt(len(x))) if sd > 0 else 0.0)


def rida(m, nimi, laius=26):
    if m is None:
        return f"{nimi:<{laius}s}  (alla 20 nadala)"
    return (f"{nimi:<{laius}s}{m['n']:>6d}{m['bp']:>10.2f}{m['sh']:>8.2f}"
            f"{100*m['kokku']:>9.1f}{100*m['dd']:>8.1f}{m['t']:>7.2f}"
            f"{E.p_kahepoolne(m['t']):>8.3f}")


def pais(laius=26):
    return (f"{'REGIME':<{laius}s}{'N':>6s}{'AVG BP':>10s}{'SHARPE':>8s}"
            f"{'TOTAL%':>9s}{'MAXDD%':>8s}{'T':>7s}{'P':>8s}")


NETO = {u: G.tulemused(al, u)["neto"].dropna() for u in ("U7", "U28")}
BRUTO = {u: G.tulemused(al, u)["bruto"].dropna() for u in ("U7", "U28")}
KULU = {u: G.tulemused(al, u)["kulu"].dropna() for u in ("U7", "U28")}

print("=" * 104)
print("G0  BASELINE (muutmata A_REV, kontrollitud A1 vastu)")
print("=" * 104)
print(pais())
for u in ("U7", "U28"):
    r = NETO[u]
    print(rida(moodikud(r), f"{u} KOIK 2006-2026"))
    print(rida(moodikud(r[r.index < POOL]), f"  {u} 2006-2016"))
    print(rida(moodikud(r[r.index >= POOL]), f"  {u} 2016-2026"))

print()
print("=" * 104)
print("G1  PEATEST — 9 rezhiimi x 2 universumit, mediaanjaotus (lavi 0.50)")
print("=" * 104)
read = []
for u in ("U7", "U28"):
    r = NETO[u]
    print(f"\n--- {u} ---")
    print(pais())
    print(rida(moodikud(r), "ALL"))
    for c in G.REZIIMID:
        st = KAH[c].reindex(r.index)
        hi = r[st == "HIGH"]
        lo = r[st == "LOW"]
        mh, ml = moodikud(hi), moodikud(lo)
        tv, pv = G.t_vahe(hi.values, lo.values)
        print(rida(mh, f"  {c} HIGH"))
        print(rida(ml, f"  {c} LOW"))
        print(f"  {'-> HIGH miinus LOW':<24s}"
              f"{'':>6s}{(mh['bp']-ml['bp']) if mh and ml else float('nan'):>10.2f}"
              f"{'':>8s}{'':>9s}{'':>8s}{tv:>7.2f}{pv:>8.3f}")
        read.append(dict(uni=u, rez=c, hi=mh, lo=ml, t=tv, p=pv))

print()
print("=" * 104)
print("G2  MULTIPLE TESTING — Benjamini-Hochberg ule 18 rezhiimitesti")
print("=" * 104)
pv = [x["p"] for x in read]
pv = [1.0 if not np.isfinite(p) else p for p in pv]
lavi, labi = E.bh(pv, 0.05)
print(f"  testitud hupoteese: {len(read)} (9 rezhiimi x 2 universumit)")
print(f"  BH q=0.05 lavi p = {lavi:.4f}, labis {len(labi)}")
for i in labi:
    x = read[i]
    print(f"    {x['uni']} {x['rez']:<10s} HIGH-LOW = "
          f"{x['hi']['bp']-x['lo']['bp']:+.2f} bp  p = {pv[i]:.4f}")
if not labi:
    print("    MITTE UKSKI rezhiim ei labi mitme testi korrektsiooni.")
print(f"  parim toores p = {min(pv):.4f}  "
      f"(Bonferroni lavi {0.05/len(read):.4f})")

print()
print("=" * 104)
print("G3  OTSUSTAV TEST — kas rezhiim tootab MOLEMAS pooles eraldi?")
print("=" * 104)
print("  Kui rezhiim on paris, peab HIGH-LOW vahe olema SAMA MARGIGA")
print("  nii 2006-2016 kui 2016-2026 sees. Kui ta tootab ainult kogu")
print("  valimil, siis ta lihtsalt JARGIB AEGA ega seleta midagi.")
print()
print(f"{'universum':<6s}{'rezhiim':<11s}{'kogu HIGH-LOW':>15s}{'p':>8s}"
      f"{'2006-2016':>12s}{'p':>8s}{'2016-2026':>12s}{'p':>8s}{'sama mark?':>12s}")
sama_loend = 0
for x in read:
    u, c = x["uni"], x["rez"]
    r = NETO[u]
    st = KAH[c].reindex(r.index)
    rida_out = [f"{u:<6s}{c:<11s}"]
    margid = []
    for silt, sel in (("kogu", slice(None)),):
        pass
    kogu_d = x["hi"]["bp"] - x["lo"]["bp"] if x["hi"] and x["lo"] else np.nan
    rida_out.append(f"{kogu_d:>15.2f}{x['p']:>8.3f}")
    for a, b in ((None, POOL), (POOL, None)):
        m = pd.Series(True, index=r.index)
        if a is not None:
            m &= r.index >= a
        if b is not None:
            m &= r.index < b
        hi = r[m & (st == "HIGH")]
        lo = r[m & (st == "LOW")]
        mh, ml = moodikud(hi), moodikud(lo)
        if mh and ml:
            dd = mh["bp"] - ml["bp"]
            tv, pp = G.t_vahe(hi.values, lo.values)
            margid.append(np.sign(dd))
            rida_out.append(f"{dd:>12.2f}{pp:>8.3f}")
        else:
            margid.append(np.nan)
            rida_out.append(f"{'n/a':>12s}{'':>8s}")
    sama = (len(margid) == 2 and np.isfinite(margid[0]) and np.isfinite(margid[1])
            and margid[0] == margid[1] and np.isfinite(kogu_d)
            and np.sign(kogu_d) == margid[0])
    sama_loend += sama
    rida_out.append(f"{'JAH' if sama else 'ei':>12s}")
    print("".join(rida_out))
print(f"\n  rezhiime, kus HIGH-LOW mark on SAMA molemas pooles ja kogu "
      f"valimil: {sama_loend}/{len(read)}")

print()
print("=" * 104)
print("G4  BRUTO / KULU / NETO (parim rezhiim mediaanjaotuses, U28)")
print("=" * 104)
best = max([x for x in read if x["uni"] == "U28" and x["hi"] and x["lo"]],
           key=lambda x: (x["hi"]["bp"] - x["lo"]["bp"]))
c = best["rez"]
print(f"  suurima HIGH-LOW vahega rezhiim U28-s: {c}")
print(f"{'variant':<24s}{'N':>6s}{'BRUTO bp':>10s}{'KULU bp':>9s}{'NETO bp':>9s}"
      f"{'SHARPE':>8s}{'T':>7s}")
for u in ("U7", "U28"):
    st = KAH[c].reindex(NETO[u].index)
    for silt, sel in (("ALL", pd.Series(True, index=NETO[u].index)),
                      (f"{c} HIGH", st == "HIGH"), (f"{c} LOW", st == "LOW")):
        n = NETO[u][sel]
        b = BRUTO[u].reindex(n.index)
        kk = KULU[u].reindex(n.index)
        m = moodikud(n)
        if m is None:
            continue
        print(f"{u+' '+silt:<24s}{m['n']:>6d}{1e4*b.mean():>10.2f}"
              f"{1e4*kk.mean():>9.2f}{m['bp']:>9.2f}{m['sh']:>8.2f}{m['t']:>7.2f}")
