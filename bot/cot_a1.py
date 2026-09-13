"""
cot_a1.py — A1 FALSIFITSEERIMISTEST: kas COT-serv elab ule vana perioodi?

EESMARK EI OLE panna COT-i hasti valja nagema. Eesmark on teda TAPPA.
Kui 2006-2016 on negatiivne ja 2016-2026 positiivne, siis leid on
valimispetsiifiline ja COT on surnud.

MIDA EI MUUDETUD (rangelt):
  * sama COT-andmestik (6dca-aqww, legacy futures only)
  * sama signaal A_REV: net_pct 156n rullpertsentiil, lavid 0.90/0.10
  * samad hoiud 1/2/4 nadalat
  * sama valuutakonstruktsioon (USD = -keskmine)
  * sama avaldamisviive (report + >= 6 paeva, esmaspaeva sulgemine)
  * sama kulumudel (NEMSIS BASE, uhesuunaline bp kaibelt)
  * samad universumid U7 / U28
MUUTUS AINULT HINNASEERIA PIKKUS.
"""
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R

PER = [
    ("A 2006-2010", "2006-05-01", "2010-12-31"),
    ("B 2011-2016", "2011-01-01", "2016-08-29"),
    ("C 2006-2016", "2006-05-01", "2016-08-29"),
    ("D 2016-2026", "2016-08-30", "2026-12-31"),
    ("E 2006-2026", "2006-05-01", "2026-12-31"),
]
LAI = 22


def loik(x, a, b):
    return x[(x.index >= pd.Timestamp(a)) & (x.index <= pd.Timestamp(b))]


def rea(nimi, x, laius=LAI):
    m = E.moodikud(x, nimi)
    if m is None:
        return f"{nimi:<{laius}s}  (alla 20 vaatluse)"
    return (f"{nimi:<{laius}s}{m['n']:>5d}{m['keskm_bp']:>9.2f}{m['sh']:>8.2f}"
            f"{100*m['kokku']:>9.1f}{100*m['maxdd']:>8.1f}{m['pf']:>7.2f}"
            f"{m['wr']:>7.1f}{m['t']:>7.2f}{E.p_kahepoolne(m['t']):>8.3f}")


def pais(laius=LAI):
    return (f"{'periood':<{laius}s}{'n':>5s}{'keskm_bp':>9s}{'sharpe':>8s}"
            f"{'kokku%':>9s}{'maxdd%':>8s}{'pf':>7s}{'wr%':>7s}{'t':>7s}{'p':>8s}")


print("=" * 100)
print("A1.0  ANDMED")
print("=" * 100)
for suf in ("_d", "_d25"):
    V = E.usd_vaartused(suf)
    print(f"  sufiks {suf:<5s}: {V.index.min().date()} .. {V.index.max().date()}  "
          f"{len(V)} kauplemispaeva (ristuv aken ule 7 paari)")
for p in E.U7:
    s = E.lae_hind(p, "_d25")
    print(f"    {p}_d25  {len(s)} rida  {s.index.min().date()} .. {s.index.max().date()}")
d = E.lae_cot()
print(f"  COT: {len(d)} rida, {d['date'].min().date()} .. {d['date'].max().date()}")

al25 = R.ehita_alus(sufiks="_d25")
al16 = R.ehita_alus(sufiks="_d")
print(f"\n  pikk COT-nadalate seeria: {len(al25['sis'])} nadalat "
      f"{al25['sis'].index.min().date()} .. {al25['sis'].index.max().date()}")
vahe = pd.Series({k: (v - k).days for k, v in al25["sis"].items()})
print(f"  avaldamisviive: min {vahe.min()}d  mediaan {int(vahe.median())}d  "
      f"max {vahe.max()}d  (reegel: report + >= 6 paeva)")
dow = pd.DatetimeIndex(al25["sis"].values).dayofweek
print(f"  sisenemispaev esmaspaev {100*(dow==0).mean():.1f}%  "
      f"teisipaev {100*(dow==1).mean():.1f}%  muu {100*(dow>1).mean():.1f}%")

print()
print("=" * 100)
print("A1.1  JARJEPIDEVUSKONTROLL — kas uus hinnaseeria annab 2016-2026 sama vastuse?")
print("=" * 100)
print(pais())
for uni in ("U7", "U28"):
    r_vana = R.joosta(al16, "A_REV", 1, uni)[2]["neto"].dropna()
    r_uus = R.joosta(al25, "A_REV", 1, uni)[2]["neto"].dropna()
    print(rea(f"{uni} _d   2016-2026", loik(r_vana, "2016-08-30", "2026-12-31")))
    print(rea(f"{uni} _d25 2016-2026", loik(r_uus, "2016-08-30", "2026-12-31")))

print()
print("=" * 100)
print("A1.2  PERIOODID A-E, MUUTMATA REEGLID (A_REV, kulu = NEMSIS BASE)")
print("=" * 100)
read = {}
for uni in ("U7", "U28"):
    for h in E.HOIUD:
        r = R.joosta(al25, "A_REV", h, uni)[2]
        read[(uni, h)] = r
    print(f"\n--- {uni} ---")
    for h in E.HOIUD:
        print(pais() + f"   (hoid {h} nadalat)")
        for nimi, a, b in PER:
            print(rea(nimi, loik(read[(uni, h)]["neto"].dropna(), a, b)))
        print()

print("=" * 100)
print("A1.3  NOUTUD VORDLUSTABEL (h1, neto, kulu = NEMSIS BASE)")
print("=" * 100)
print(f"{'PERIOOD':<14s}{'NADALAID':>9s}{'TEHINGUID':>11s}{'BRUTO_bp':>10s}"
      f"{'KULU_bp':>9s}{'NETO_bp':>9s}{'KOKKU%':>9s}{'SHARPE':>8s}{'T-STAT':>8s}")
for uni in ("U7", "U28"):
    paarid, kulu = R.universum(uni, al25["V"])
    S = R.skoorid(al25, "A_REV")
    sg = pd.DataFrame({p: np.sign(S[p[:3]] - S[p[3:]]) for p in paarid}, index=S.index)
    r = read[(uni, 1)]
    print(f"  --- {uni} ---")
    for nimi, a, b in PER:
        x = loik(r["neto"].dropna(), a, b)
        if len(x) < 20:
            continue
        br = loik(r["bruto"], a, b).reindex(x.index)
        ku = loik(r["kulu"], a, b).reindex(x.index)
        teh = int((loik(sg, a, b) != 0).sum().sum())
        eq = np.cumprod(1 + x.values)
        sd = x.std(ddof=1)
        print(f"{nimi:<14s}{len(x):>9d}{teh:>11d}{1e4*br.mean():>10.2f}"
              f"{1e4*ku.mean():>9.2f}{1e4*x.mean():>9.2f}{100*(eq[-1]-1):>9.1f}"
              f"{x.mean()/sd*math.sqrt(52):>8.2f}"
              f"{x.mean()/sd*math.sqrt(len(x)):>8.2f}")

print()
print("=" * 100)
print("A1.4  AASTATE KAUPA (A_REV h1, neto)")
print("=" * 100)
r7 = read[("U7", 1)]["neto"].dropna()
r28 = read[("U28", 1)]["neto"].dropna()
print(f"{'aasta':<8s}{'U7 bp/n':>10s}{'U7 aasta%':>12s}"
      f"{'U28 bp/n':>10s}{'U28 aasta%':>12s}{'nadalaid':>10s}")
pos7 = pos28 = 0
for y in sorted(set(r28.index.year)):
    a, b = r7[r7.index.year == y], r28[r28.index.year == y]
    pos7 += a.mean() > 0
    pos28 += b.mean() > 0
    print(f"{y:<8d}{1e4*a.mean():>10.2f}{100*(np.exp(a.sum())-1):>12.2f}"
          f"{1e4*b.mean():>10.2f}{100*(np.exp(b.sum())-1):>12.2f}{len(b):>10d}")
n_a = len(set(r28.index.year))
print(f"\npositiivseid aastaid: U7 {pos7}/{n_a}   U28 {pos28}/{n_a}")
