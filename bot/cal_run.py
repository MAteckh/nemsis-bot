"""
cal_run.py — B1 pohitestid: kas makrоullatus ennustab FX-liikumist?
Koik definitsioonid on cal_engine.py-s, kirjutatud ENNE esimest jooksu.
"""
import math

import numpy as np
import pandas as pd

import cal_engine as C

RS = np.random.RandomState(20260915)
HOR_D = (1, 2, 5)


def ehita(tasemed=("T1", "T2"), sufiks="_d25"):
    d = C.z_ullatus(C.lae_kalender(tasemed))
    V = C.valuuta_vaartused(sufiks)
    pos = C.paevane_sisenemine(d["ts"].values, V.index)
    d = d.assign(bar=pos)
    d = d[(d["bar"] >= 0) & d["z"].notna()].copy()
    d["sisenemine"] = V.index[d["bar"].values]
    for k in HOR_D:
        R = C.valuuta_tootlused(V, k)
        # tootlus sisenemisbaarilt k paeva edasi, selle valuuta jaoks
        d[f"r{k}"] = [R.iloc[b][c] if b < len(R) else np.nan
                      for b, c in zip(d["bar"].values, d["cur"].values)]
    d["suund"] = np.sign(d["z"]) * d["mark"]
    return d, V


def rida(m, nimi, kulu_bp=0.0, laius=30):
    if m is None:
        return f"{nimi:<{laius}s}  (alla 20 sundmuse)"
    neto = m["keskm_bp"] - kulu_bp
    return (f"{nimi:<{laius}s}{m['n']:>7d}{m['keskm_bp']:>10.2f}"
            f"{kulu_bp:>8.2f}{neto:>9.2f}{m['wr']:>8.1f}{m['pf']:>7.2f}"
            f"{m['t']:>7.2f}{C.p_kahepoolne(m['t']):>8.3f}")


def pais(laius=30):
    return (f"{'test':<{laius}s}{'n':>7s}{'bruto_bp':>10s}{'kulu':>8s}"
            f"{'neto_bp':>9s}{'wr%':>8s}{'pf':>7s}{'t':>7s}{'p':>8s}")


KULU = 2.0 * C.KULU_1SUUND_BP      # edasi-tagasi uhel valuutajalal

if __name__ == "__main__":
    d, V = ehita()
    print("=" * 104)
    print("B1.0  VALIM")
    print("=" * 104)
    print(f"  sundmusi z-ga ja hinnaga: {len(d)}")
    print(f"  periood: {d['ts'].min().date()} .. {d['ts'].max().date()}")
    print(f"  |z| >= {C.LAVI}: {int((d['z'].abs() >= C.LAVI).sum())} sundmust")
    print(f"  kulu eeldus: {KULU:.2f} bp edasi-tagasi (1 valuutajalg, "
          f"{C.KULU_1SUUND_BP} bp uhesuunaline)")

    print()
    print("=" * 104)
    print("B1.1  PEAHUPOTEESID A ja B (|z| >= 1), paevane horisont")
    print("=" * 104)
    print(pais())
    for k in HOR_D:
        x = d[d["z"].abs() >= C.LAVI]
        r = (x["suund"] * x[f"r{k}"]).dropna()
        print(rida(C.moodikud(r), f"A+B koos  {k}d", KULU))
        a = x[x["z"] >= C.LAVI]
        print(rida(C.moodikud((a["suund"] * a[f"r{k}"]).dropna()),
                   f"  A positiivne ullatus {k}d", KULU))
        b = x[x["z"] <= -C.LAVI]
        print(rida(C.moodikud((b["suund"] * b[f"r{k}"]).dropna()),
                   f"  B negatiivne ullatus {k}d", KULU))
        print()

    print("=" * 104)
    print("B1.2  PIDEV VERSIOON — korrelatsioon z ja tootluse vahel")
    print("=" * 104)
    print(f"{'horisont':<12s}{'n':>8s}{'korr(z*mark, r)':>18s}{'t':>9s}"
          f"{'beeta bp per 1z':>18s}")
    for k in HOR_D:
        x = d.dropna(subset=[f"r{k}"])
        zz = (x["z"] * x["mark"]).values
        rr = x[f"r{k}"].values
        ok = np.isfinite(zz) & np.isfinite(rr)
        zz, rr = np.clip(zz[ok], -5, 5), rr[ok]
        kor = np.corrcoef(zz, rr)[0, 1]
        b = np.cov(zz, rr, ddof=1)[0, 1] / np.var(zz, ddof=1)
        t = kor * math.sqrt(len(zz) - 2) / math.sqrt(max(1 - kor ** 2, 1e-12))
        print(f"{str(k)+'d':<12s}{len(zz):>8d}{kor:>18.4f}{t:>9.2f}"
              f"{1e4*b:>18.2f}")

    print()
    print("=" * 104)
    print("B1.3  HUPOTEES C — kas |z| ennustab liikumise SUURUST? (kirjeldav)")
    print("=" * 104)
    print(f"{'horisont':<12s}{'korr(|z|, |r|)':>18s}{'|r| kui |z|<1':>16s}"
          f"{'|r| kui |z|>=2':>17s}")
    for k in HOR_D:
        x = d.dropna(subset=[f"r{k}"])
        az, ar = x["z"].abs().clip(0, 5), x[f"r{k}"].abs()
        print(f"{str(k)+'d':<12s}{az.corr(ar):>18.4f}"
              f"{1e4*ar[az < 1].mean():>16.1f}{1e4*ar[az >= 2].mean():>17.1f}")

    print()
    print("=" * 104)
    print("B1.4  TRAIN / VALIDATION / FINAL OOS (1d horisont, |z|>=1)")
    print("=" * 104)
    print(f"  TRAIN .. {C.TRAIN_LOPP.date()}   VALID .. {C.VALID_LOPP.date()}"
          f"   FINAL OOS {C.VALID_LOPP.date()} ..")
    print(pais())
    x = d[d["z"].abs() >= C.LAVI]
    tr, va, oos = C.jaota(x["ts"])
    for k in HOR_D:
        for nimi, m in (("TRAIN", tr), ("VALID", va), ("FINAL OOS", oos)):
            print(rida(C.moodikud((x[m]["suund"] * x[m][f"r{k}"]).dropna()),
                       f"{nimi} {k}d", KULU))
        print()

    print("=" * 104)
    print("B1.5  AASTATE KAUPA (1d, |z|>=1)")
    print("=" * 104)
    print(f"{'aasta':<8s}{'n':>7s}{'bruto_bp':>10s}{'neto_bp':>9s}{'wr%':>8s}{'t':>7s}")
    pos_a = 0
    aastad = sorted(x["ts"].dt.year.unique())
    for y in aastad:
        xx = x[x["ts"].dt.year == y]
        m = C.moodikud((xx["suund"] * xx["r1"]).dropna())
        if m is None:
            continue
        pos_a += (m["keskm_bp"] - KULU) > 0
        print(f"{y:<8d}{m['n']:>7d}{m['keskm_bp']:>10.2f}"
              f"{m['keskm_bp']-KULU:>9.2f}{m['wr']:>8.1f}{m['t']:>7.2f}")
    print(f"\npositiivseid aastaid (neto): {pos_a}/{len(aastad)}")

    print()
    print("=" * 104)
    print("B1.6  VALUUTA KAUPA (1d, |z|>=1)")
    print("=" * 104)
    print(pais(14))
    pos_v = 0
    for c in C.VALUUTAD:
        xx = x[x["cur"] == c]
        m = C.moodikud((xx["suund"] * xx["r1"]).dropna())
        if m is None:
            continue
        pos_v += (m["keskm_bp"] - KULU) > 0
        print(rida(m, c, KULU, 14))
    print(f"\npositiivseid valuutasid (neto): {pos_v}/8")

    print()
    print("=" * 104)
    print("B1.7  TIER ja INDIKAATOR (1d, |z|>=1)")
    print("=" * 104)
    print(pais())
    for t in ("T1", "T2"):
        xx = x[x["tier"] == t]
        print(rida(C.moodikud((xx["suund"] * xx["r1"]).dropna()),
                   f"TIER {t}", KULU))
    print()
    read = []
    for ind in sorted(x["indicator"].unique()):
        xx = x[x["indicator"] == ind]
        m = C.moodikud((xx["suund"] * xx["r1"]).dropna())
        if m:
            read.append((ind, m))
    read.sort(key=lambda r: -r[1]["keskm_bp"])
    for ind, m in read:
        print(rida(m, f"  {ind}", KULU))
    pos_i = sum(1 for _, m in read if m["keskm_bp"] - KULU > 0)
    print(f"\npositiivseid indikaatoreid (neto): {pos_i}/{len(read)}")

    print()
    print("=" * 104)
    print("B1.8  KULUTUNDLIKKUS (1d, |z|>=1)")
    print("=" * 104)
    print(pais())
    r1 = (x["suund"] * x["r1"]).dropna()
    m = C.moodikud(r1)
    for k in (0.0, 1.0, 2.0, 3.0):
        print(rida(m, f"kulu {k:.0f} bp uhesuunaline", 2 * k))
    print(rida(m, "NEMSIS BASE (1 jalg)", KULU))
    print(rida(m, "NEMSIS BASE + korvi hedge", 2 * KULU))
