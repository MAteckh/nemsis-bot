"""
cal_exec.py — B1 lopukontrollid: paevane vs H1 SAMAL aknal, voimsus, 205 EUR.
"""
import math

import numpy as np
import pandas as pd

import cal_engine as C
import cal_run as R

d, V = R.ehita()
x = d[d["z"].abs() >= C.LAVI].copy()
KULU = R.KULU
H1_ALGUS = pd.Timestamp("2023-11-27")

print("=" * 104)
print("B1.14  OUN-OUNA: paevane test SAMAL aknal, kus H1-andmed olemas")
print("=" * 104)
print(R.pais())
m = x["ts"] >= H1_ALGUS
for silt, sel in (("paevane 1d KOGU valim", x),
                  ("paevane 1d 2023-11+ aken", x[m]),
                  ("  TIER 1 2023-11+ aken", x[m & (x["tier"] == "T1")])):
    print(R.rida(C.moodikud((sel["suund"] * sel["r1"]).dropna()), silt, KULU))

print()
print("=" * 104)
print("B1.15  VOIMSUS — kas H1 null tahendab 'efekti pole' voi 'valim on vaike'?")
print("=" * 104)
r1 = (x["suund"] * x["r1"]).dropna()
sd_d = r1.std(ddof=1) * 1e4
print(f"  paevane: n={len(r1)}  keskm {1e4*r1.mean():+.2f}bp  sd {sd_d:.1f}bp  "
      f"SE {sd_d/math.sqrt(len(r1)):.2f}bp")
for n in (831, 408):
    se = sd_d / math.sqrt(n)
    print(f"  kui sama efekt (+2.72bp) motta n={n} juures: SE={se:.2f}bp  "
          f"=> oodatav t = {2.72/se:.2f}  (5% avastamistoenaosus "
          f"{'suur' if 2.72/se > 2.8 else 'VAIKE'})")
print("  => H1 null EI OLE toestus efekti puudumisest; ta on ALAVOIMSAS.")
print("     Aus jareldus: H1 aknas ei leidnud kinnitust, aga ei valista ka.")

print()
print("=" * 104)
print("B1.16  TEHINGUTE SAGEDUS JA KULUEELARVE")
print("=" * 104)
aastaid = (x["ts"].max() - x["ts"].min()).days / 365.25
t1 = x[x["tier"] == "T1"]
for silt, sel in (("koik |z|>=1", x), ("ainult TIER 1", t1)):
    n_a = len(sel) / aastaid
    m2 = C.moodikud((sel["suund"] * sel["r1"]).dropna())
    print(f"  {silt:<16s} {len(sel)} sundmust = {n_a:.0f}/aastas   "
          f"bruto {m2['keskm_bp']:+.2f}bp/tehing  "
          f"kulu {KULU:.2f}bp  =>  aastane bruto {n_a*m2['keskm_bp']/100:+.2f}% "
          f"kulu {n_a*KULU/100:.2f}%  neto {n_a*(m2['keskm_bp']-KULU)/100:+.2f}%")

print()
print("=" * 104)
print("B1.17  EFEKTI SUURUS vs KULU — NEMSIS-i kriteerium on >= 2x")
print("=" * 104)
print(f"{'variant':<28s}{'bruto_bp':>10s}{'kulu_bp':>9s}{'kordne':>9s}{'verdikt':>12s}")
for silt, sel in (("koik |z|>=1  1d", x), ("TIER 1  1d", t1),
                  ("TIER 1  5d", t1)):
    kol = "r5" if "5d" in silt else "r1"
    m2 = C.moodikud((sel["suund"] * sel[kol]).dropna())
    k = m2["keskm_bp"] / KULU
    print(f"{silt:<28s}{m2['keskm_bp']:>10.2f}{KULU:>9.2f}{k:>9.2f}"
          f"{('LABIB' if k >= 2 else 'KUKUB'):>12s}")

print()
print("=" * 104)
print("B1.18  205 EUR TAITEVUS")
print("=" * 104)
KAPITAL, UHIKUD = 205.0, 1000.0
eurusd = float(V["EUR"].iloc[-1])
R1 = C.valuuta_tootlused(V, 1)
print(f"  konto {KAPITAL:.0f} EUR, min lot 0.01 = {UHIKUD:.0f} uhikut, "
      f"EURUSD {eurusd:.4f}")
print(f"{'valuuta':<10s}{'1d sigma%':>12s}{'0.01 lot EUR':>15s}"
      f"{'1-sigma EUR':>14s}{'% kontost':>12s}")
# 0.01 lot = 1000 uhikut kaubeldava PAARI BAASvaluutat.
# EUR/GBP/AUD/NZD kaubeldakse XXXUSD (baas = XXX);
# JPY/CHF/CAD kaubeldakse USDXXX (baas = USD); USD-jalg on korv (~USD).
BAAS = {"EUR": "EUR", "GBP": "GBP", "AUD": "AUD", "NZD": "NZD",
        "JPY": "USD", "CHF": "USD", "CAD": "USD", "USD": "USD"}
read = []
for c in C.VALUUTAD:
    sig = float(R1[c].std())
    b = BAAS[c]
    nots = (UHIKUD if b == "EUR"
            else UHIKUD / eurusd if b == "USD"
            else UHIKUD * float(V[b].iloc[-1]) / eurusd)
    pnl = nots * sig
    read.append(pnl)
    print(f"{c:<10s}{100*sig:>12.2f}{nots:>15.0f}{pnl:>14.2f}"
          f"{100*pnl/KAPITAL:>12.1f}")
for risk in (0.0025, 0.0050):
    eur = KAPITAL * risk
    ok = sum(1 for p in read if p <= eur)
    print(f"  kavatsetud risk {100*risk:.2f}% = {eur:.2f} EUR -> "
          f"taidetav {ok}/8 valuutal; vajalik konto "
          f"{min(p/risk for p in read):.0f}-{max(p/risk for p in read):.0f} EUR")
