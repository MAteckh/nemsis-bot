"""
cot_regime_run2.py — sabad (0.25/0.75), aastad, walk-forward, REV vs CONT.
"""
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R
import cot_regime as G
from cot_regime_run import moodikud, rida, pais

al = R.ehita_alus(sufiks="_d25")
M = G.rezhiimi_pertsentiilid(al)
KAH, SAB = G.seisund(M)
POOL = pd.Timestamp("2016-08-30")
NETO = {u: G.tulemused(al, u)["neto"].dropna() for u in ("U7", "U28")}
CONT = {u: G.tulemused(al, u, suund="A_CONT")["neto"].dropna()
        for u in ("U7", "U28")}

print("=" * 104)
print("G5  SEKUNDAARNE JAOTUS — sabad 0.25 / 0.75 (eelregistreeritud)")
print("=" * 104)
read2 = []
for u in ("U7", "U28"):
    print(f"\n--- {u} ---")
    print(pais())
    r = NETO[u]
    for c in G.REZIIMID:
        st = SAB[c].reindex(r.index)
        hi, lo = r[st == "HIGH"], r[st == "LOW"]
        mh, ml = moodikud(hi), moodikud(lo)
        tv, pv = G.t_vahe(hi.values, lo.values)
        if mh:
            print(rida(mh, f"  {c} HIGH (top 25%)"))
        if ml:
            print(rida(ml, f"  {c} LOW (bot 25%)"))
        if mh and ml:
            print(f"  {'-> HIGH miinus LOW':<24s}{'':>6s}"
                  f"{mh['bp']-ml['bp']:>10.2f}{'':>25s}{tv:>7.2f}{pv:>8.3f}")
        read2.append(dict(uni=u, rez=c, p=pv if np.isfinite(pv) else 1.0))
pv2 = [x["p"] for x in read2]
lavi2, labi2 = E.bh(pv2, 0.05)
print(f"\n  BH q=0.05 ule {len(read2)} sabatesti: labis {len(labi2)}, "
      f"parim toores p = {min(pv2):.4f}")

print()
print("=" * 104)
print("G6  KAS REZHIIM LIHTSALT JARGIB AEGA? (HIGH-osakaal perioodi kaupa)")
print("=" * 104)
print(f"{'rezhiim':<12s}{'HIGH% 2006-2016':>18s}{'HIGH% 2016-2026':>18s}"
      f"{'vahe':>8s}{'hinnang':>28s}")
for c in G.REZIIMID:
    st = KAH[c].reindex(NETO["U28"].index)
    a = st[st.index < POOL].dropna()
    b = st[st.index >= POOL].dropna()
    pa = 100 * float((a == "HIGH").mean()) if len(a) else np.nan
    pb = 100 * float((b == "HIGH").mean()) if len(b) else np.nan
    vahe = pb - pa
    hin = ("JARGIB AEGA (vahe > 40pp)" if abs(vahe) > 40 else
           "osaliselt ajaline" if abs(vahe) > 20 else "ajast soltumatu")
    print(f"{c:<12s}{pa:>18.1f}{pb:>18.1f}{vahe:>8.1f}{hin:>28s}")

print()
print("=" * 104)
print("G7  AASTATE KAUPA — parim kandidaat USDTREND (U28), mediaanjaotus")
print("=" * 104)
c = "USDTREND"
r = NETO["U28"]
st = KAH[c].reindex(r.index)
print(f"{'aasta':<7s}{'domin. rezhiim':>16s}{'HIGH%':>8s}{'n':>6s}"
      f"{'COT bp/n':>10s}{'aasta%':>9s}{'HIGH bp':>10s}{'LOW bp':>10s}")
for y in sorted(set(r.index.year)):
    m = r.index.year == y
    x, s = r[m], st[m]
    hi, lo = x[s == "HIGH"], x[s == "LOW"]
    ph = 100 * float((s == "HIGH").mean()) if s.notna().any() else np.nan
    dom = "HIGH" if ph >= 50 else ("LOW" if ph >= 0 else "n/a")
    print(f"{y:<7d}{dom:>16s}{ph:>8.0f}{len(x):>6d}{1e4*x.mean():>10.2f}"
          f"{100*(np.exp(x.sum())-1):>9.2f}"
          f"{(1e4*hi.mean() if len(hi) else float('nan')):>10.2f}"
          f"{(1e4*lo.mean() if len(lo) else float('nan')):>10.2f}")

print()
print("=" * 104)
print("G8  WALK-FORWARD — TRAIN 2006-2013 / VALID 2014-2017 / OOS 2018-2026")
print("=" * 104)
AKNAD = [("TRAIN", "2006-01-01", "2013-12-31"),
         ("VALID", "2014-01-01", "2017-12-31"),
         ("OOS",   "2018-01-01", "2026-12-31")]
print("  Protokoll: vali TRAIN-i pealt parim rezhiim (suurim HIGH-LOW),")
print("  fikseeri definitsioon, siis vaata VALID ja OOS.")
print()
for u in ("U7", "U28"):
    r = NETO[u]
    skoor = {}
    for c in G.REZIIMID:
        st = KAH[c].reindex(r.index)
        m = (r.index >= "2006-01-01") & (r.index <= "2013-12-31")
        hi, lo = r[m & (st == "HIGH")], r[m & (st == "LOW")]
        mh, ml = moodikud(hi), moodikud(lo)
        if mh and ml:
            skoor[c] = mh["bp"] - ml["bp"]
    if not skoor:
        print(f"  {u}: TRAIN-is ei ole piisavalt andmeid uhelgi rezhiimil")
        continue
    val = max(skoor, key=lambda k: abs(skoor[k]))
    suund = "HIGH" if skoor[val] > 0 else "LOW"
    print(f"  {u}: TRAIN valib rezhiimi {val}, kauple seisundis {suund} "
          f"(TRAIN HIGH-LOW = {skoor[val]:+.2f} bp)")
    print(f"     kandidaadid TRAIN-is: " +
          ", ".join(f"{k} {v:+.1f}" for k, v in
                    sorted(skoor.items(), key=lambda x: -abs(x[1]))))
    st = KAH[val].reindex(r.index)
    print("     " + pais(20))
    for silt, a, b in AKNAD:
        m = (r.index >= a) & (r.index <= b)
        print("     " + rida(moodikud(r[m & (st == suund)]),
                             f"{silt} {val}={suund}", 20))
        print("     " + rida(moodikud(r[m]), f"{silt} FILTRITA", 20))
    print()

print("=" * 104)
print("G9  REV vs CONT — kas rezhiim utleb, KUMB suund sobib?")
print("=" * 104)
print("  A_CONT = -A_REV konstruktsiooni jargi, seega tabel naitab, kas")
print("  mingis seisundis on CONT (negatiivne A_REV) susteemselt parem.")
print(f"{'universum':<6s}{'rezhiim':<11s}{'HIGH: parem suund':>20s}"
      f"{'LOW: parem suund':>20s}{'kas rezhiim eristab?':>24s}")
for u in ("U7", "U28"):
    r = NETO[u]
    for c in G.REZIIMID:
        st = KAH[c].reindex(r.index)
        hi, lo = r[st == "HIGH"], r[st == "LOW"]
        if len(hi) < 20 or len(lo) < 20:
            continue
        sh = "REV" if hi.mean() > 0 else "CONT"
        sl = "REV" if lo.mean() > 0 else "CONT"
        tv, pv = G.t_vahe(hi.values, lo.values)
        eri = "JAH (p<0.05)" if pv < 0.05 else f"ei (p={pv:.2f})"
        print(f"{u:<6s}{c:<11s}{sh+f' ({1e4*hi.mean():+.1f}bp)':>20s}"
              f"{sl+f' ({1e4*lo.mean():+.1f}bp)':>20s}{eri:>24s}")
