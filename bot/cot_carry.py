"""
cot_carry.py — KRIITILINE KONTROLL: kas A_REV maksab negatiivset carry't?

Spekulandid on tuupiliselt PIKAD korge intressiga valuutades (AUD, NZD)
ja LUHIKESED madala intressiga valuutades (JPY, CHF). A_REV teeb vastupidi:
shordib rahvamassi lemmikut. Seega A_REV on struktuurilt SHORT CARRY.

Backtestis on AINULT spot-tootlus. Live-kauplemises makstakse swap'i iga oo.
Kui swap soob serva ara, ei ole strateegia elujouline, hoolimata t=3.6-st.

Intressiallikas: bot/data/policy_rates.csv (BIS WS_CBPOL, kuine, kasutatud
juba NEMSIS v6 carry-uurimises). Keskpanga maar EI OLE sama mis brokeri swap,
seepargi arvutame ka brokeri juurdehindluse murdepunkti.
"""
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R

al = R.ehita_alus()
IDX = al["sis"].index
S = R.skoorid(al, "A_REV")

rates = pd.read_csv("data/policy_rates.csv")
rates["Month"] = pd.PeriodIndex(rates["Month"], freq="M")
rates = rates.set_index("Month").ffill().bfill()
kuu = pd.PeriodIndex(IDX, freq="M")
Rk = rates.reindex(kuu)
Rk.index = IDX
Rk = Rk.reindex(columns=al["P"].columns)

print("=" * 96)
print("R19  CARRY-KONTROLL — mis intressivahet A_REV tegelikult kannab?")
print("=" * 96)
print("keskmine keskpanga maar 2016-2026 (%):")
print("  " + "  ".join(f"{c} {Rk[c].mean():.2f}" for c in Rk.columns))

for nimi, paarid, kulu in (("U7", *R.universum("U7", al["V"])[::1]),
                           ("U28", *R.universum("U28", al["V"])[::1])):
    W = E.kaalud(S, paarid, 1)
    H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
    r = E.portfell(W, H, kulu)
    # paari intressivahe = baas - kvoot (aastas, %)
    diff = pd.DataFrame({p: Rk[p[:3]] - Rk[p[3:]] for p in paarid}, index=IDX)
    carry_a = (W * diff).sum(axis=1)            # %/aastas portfelli kohta
    carry_n = carry_a / 52.0 / 100.0            # nadalane tootlus
    x = r["neto"].dropna()
    c = carry_n.reindex(x.index)
    print(f"\n{nimi} A_REV h1")
    print(f"   spot neto            {1e4*x.mean():+7.2f} bp/nadal")
    print(f"   keskpanga carry      {1e4*c.mean():+7.2f} bp/nadal "
          f"({c.mean()*5200:+.2f} %/aastas)")
    print(f"   spot + carry         {1e4*(x+c).mean():+7.2f} bp/nadal")
    y = (x + c).dropna()
    print(f"   sharpe carry'ga      {y.mean()/y.std(ddof=1)*math.sqrt(52):+7.2f}"
          f"   t={y.mean()/y.std(ddof=1)*math.sqrt(len(y)):+.2f}")
    # brokeri juurdehindlus: broker maksab vahem ja kusib rohkem
    # kulu = markup% aastas * gross exposure (sum|w| = 1) molemal jalal
    kaive = float(W.abs().sum(axis=1).mean())
    for mk in (0.5, 1.0, 1.5, 2.0):
        lisa = mk / 100.0 / 52.0 * kaive        # %/a -> nadalane
        z = (x + c - lisa)
        print(f"   markup {mk:.1f}%/a/jalg -> {1e4*z.mean():+7.2f} bp/nadal   "
              f"t={z.mean()/z.std(ddof=1)*math.sqrt(len(z)):+.2f}")
    murd = 1e4 * (x + c).mean() / (1.0 / 52.0 * kaive) / 100.0
    print(f"   MURDEPUNKT: brokeri juurdehindlus {murd:.2f} %/aastas/jalg")

print()
print("=" * 96)
print("R20  SUMMEETRILINE TRIM — kas efekt on ainult sabades?")
print("=" * 96)
for nimi, paarid, kulu in (("U7", *R.universum("U7", al["V"])[::1]),
                           ("U28", *R.universum("U28", al["V"])[::1])):
    W = E.kaalud(S, paarid, 1)
    H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
    x = E.portfell(W, H, kulu)["neto"].dropna().sort_values()
    print(f"\n{nimi}  taielik keskm {1e4*x.mean():+.2f}bp   "
          f"mediaan {1e4*x.median():+.2f}bp")
    for n in (5, 10, 20, 40):
        y = x.iloc[n:-n]
        print(f"   trim +-{n:>2d} nadalat: {1e4*y.mean():+6.2f}bp   "
              f"t={y.mean()/y.std(ddof=1)*math.sqrt(len(y)):+.2f}")
    # vordlus: osta-ja-hoia sama trimmiga (kalibreerimine)
    bh = R.osta_hoia(al, nimi)["neto"].dropna().sort_values()
    print(f"   [vordlus] osta-ja-hoia taielik {1e4*bh.mean():+.2f}bp, "
          f"trim +-20 {1e4*bh.iloc[20:-20].mean():+.2f}bp")
