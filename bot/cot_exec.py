"""
cot_exec.py — tehingutasandi statistika, tugevusproovid ja 205 EUR taitevus.
"""
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R

al = R.ehita_alus()
IDX = al["sis"].index
S = R.skoorid(al, "A_REV")
p7, k7 = R.universum("U7", al["V"])
p28, k28 = R.universum("U28", al["V"])


def nw_t(x, lag=4):
    """Newey-West korrigeeritud t-statistik (autokorrelatsiooni vastu)."""
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    n = len(x); m = x.mean(); e = x - m
    g0 = (e @ e) / n
    s = g0
    for L in range(1, lag + 1):
        g = (e[L:] @ e[:-L]) / n
        s += 2 * (1 - L / (lag + 1)) * g
    return m / math.sqrt(s / n) if s > 0 else 0.0


print("=" * 96)
print("R16  TEHINGUTASAND — mitu signaali, mitu tehingut, oodatav vaartus")
print("=" * 96)
for nimi, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    sg = pd.DataFrame({p: np.sign(S[p[:3]] - S[p[3:]]) for p in paarid}, index=S.index)
    H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
    Rt = np.log(H).diff().shift(-1).reindex(sg.index)
    for hoia in E.HOIUD:
        # tehing = (nadal, paar), kus signaal != 0; hoitakse `hoia` nadalat
        Rh = np.log(H).shift(-hoia) - np.log(H)
        m = sg != 0
        teh = (sg * Rh)[m].stack().dropna()
        kl = pd.Series({p: kulu[p] for p in paarid})
        neto = teh - pd.Series(
            [2 * kl[p] / 1e4 for _, p in teh.index], index=teh.index)
        v, k = neto[neto > 0], neto[neto <= 0]
        aastaid = (IDX[-1] - IDX[0]).days / 365.25
        print(f"\n{nimi} h{hoia}: signaale {int(m.sum().sum())}  "
              f"tehinguid {len(teh)}  ({len(teh)/aastaid:.0f}/aastas)")
        print(f"   voiduprotsent  {100*len(v)/len(neto):.1f}%")
        print(f"   keskm voit     {1e4*v.mean():+8.1f} bp")
        print(f"   keskm kaotus   {1e4*k.mean():+8.1f} bp")
        print(f"   oodatav vaartus{1e4*neto.mean():+8.1f} bp/tehing (neto)")
        print(f"   bruto          {1e4*teh.mean():+8.1f} bp/tehing")
        print(f"   kulu           {1e4*(teh.mean()-neto.mean()):8.1f} bp/tehing")
        print(f"   profit factor  {v.sum()/abs(k.sum()):8.2f}")

print()
print("=" * 96)
print("R17  TUGEVUSPROOVID — kas efekt on vaheses uksikus episoodis?")
print("=" * 96)
for nimi, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    W = E.kaalud(S, paarid, 1)
    H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
    x = E.portfell(W, H, kulu)["neto"].dropna()
    print(f"\n{nimi} A_REV h1  n={len(x)}")
    print(f"   keskm {1e4*x.mean():+.2f}bp   t={x.mean()/x.std(ddof=1)*math.sqrt(len(x)):+.2f}"
          f"   Newey-West t (4 lag)={nw_t(x):+.2f}")
    print(f"   nadalase tootluse skew {float(pd.Series(x).skew()):+.2f}  "
          f"kurtoos {float(pd.Series(x).kurt()):+.2f}")
    for n in (5, 10, 20):
        y = x.sort_values().iloc[:-n]
        print(f"   ilma {n:>2d} parima nadalata: {1e4*y.mean():+.2f}bp  "
              f"t={y.mean()/y.std(ddof=1)*math.sqrt(len(y)):+.2f}")
    ilma20 = x[x.index.year != 2020]
    print(f"   ilma 2020 aastata:      {1e4*ilma20.mean():+.2f}bp  "
          f"t={ilma20.mean()/ilma20.std(ddof=1)*math.sqrt(len(ilma20)):+.2f}")
    pool1, pool2 = x.iloc[:len(x)//2], x.iloc[len(x)//2:]
    print(f"   esimene pool {1e4*pool1.mean():+.2f}bp   "
          f"teine pool {1e4*pool2.mean():+.2f}bp")
    pos_a = sum(1 for y in sorted(set(x.index.year))
                if x[x.index.year == y].mean() > 0)
    print(f"   positiivseid aastaid {pos_a}/{len(set(x.index.year))}")

print()
print("=" * 96)
print("R18  205 EUR TAITEVUS — miinimumlot 0.01, kavatsetud risk 0.25% ja 0.50%")
print("=" * 96)
KAPITAL = 205.0
LOT_MIN = 0.01
UHIKUD = 100_000 * LOT_MIN          # 0.01 lot = 1000 uhikut baasvaluutat
V = al["V"]
eurusd = float(V["EUR"].iloc[-1])   # 1 EUR = X USD

# nadalane volatiilsus paari kohta (sisenemispaevade seerial)
H7 = E.nadala_hinnad(V, p7, al["sis"]); H7.index = IDX
sig = np.log(H7).diff().std()

print(f"konto {KAPITAL:.0f} EUR   min lot {LOT_MIN}   1 lot = 100 000 uhikut")
print(f"EURUSD = {eurusd:.4f}\n")
print(f"{'paar':<9s}{'nadala sigma%':>15s}{'0.01 lot notsionaal EUR':>26s}"
      f"{'1-sigma PnL EUR':>18s}{'% kontost':>12s}")
read = []
for p in p7:
    b = p[:3]
    # 0.01 lot = 1000 uhikut BAASvaluutat -> vaartus EUR-des
    if b == "USD":
        nots_eur = UHIKUD / eurusd
    elif b == "EUR":
        nots_eur = UHIKUD
    else:
        nots_eur = UHIKUD * float(V[b].iloc[-1]) / eurusd
    pnl = nots_eur * float(sig[p])
    read.append((p, float(sig[p]), nots_eur, pnl, 100 * pnl / KAPITAL))
    print(f"{p:<9s}{100*sig[p]:>15.2f}{nots_eur:>26.0f}{pnl:>18.2f}"
          f"{100*pnl/KAPITAL:>12.1f}")

print()
for risk in (0.0025, 0.0050):
    eur = KAPITAL * risk
    ok = sum(1 for _, _, _, pnl, _ in read if pnl <= eur)
    print(f"kavatsetud risk {100*risk:.2f}% = {eur:.2f} EUR/positsioon "
          f"-> taidetav {ok}/{len(read)} paaril")
    vaja = [pnl / risk for _, _, _, pnl, _ in read]
    print(f"   vajalik konto, et 0.01 lot = {100*risk:.2f}% risk: "
          f"min {min(vaja):.0f} EUR, mediaan {np.median(vaja):.0f} EUR, "
          f"max {max(vaja):.0f} EUR")

# portfell: mitu positsiooni korraga
sg7 = pd.DataFrame({p: np.sign(S[p[:3]] - S[p[3:]]) for p in p7}, index=S.index)
n_pos = (sg7 != 0).sum(axis=1)
print(f"\nsamaaegseid positsioone U7: keskmine {n_pos.mean():.1f}  "
      f"mediaan {int(n_pos.median())}  max {int(n_pos.max())}")
sg28 = pd.DataFrame({p: np.sign(S[p[:3]] - S[p[3:]]) for p in p28}, index=S.index)
n28 = (sg28 != 0).sum(axis=1)
print(f"samaaegseid positsioone U28: keskmine {n28.mean():.1f}  "
      f"mediaan {int(n28.median())}  max {int(n28.max())}")

kesk_nots = np.mean([r[2] for r in read])
print(f"\nminimaalne portfelli notsionaal (mediaan {int(n_pos.median())} "
      f"positsiooni x 0.01 lot): {int(n_pos.median())*kesk_nots:.0f} EUR")
print(f"see on {int(n_pos.median())*kesk_nots/KAPITAL:.1f}x konto suurus "
      f"=> vajalik voimendus {int(n_pos.median())*kesk_nots/KAPITAL:.0f}:1")
print(f"marginaal 1:30 juures: "
      f"{int(n_pos.median())*kesk_nots/30:.0f} EUR ({100*int(n_pos.median())*kesk_nots/30/KAPITAL:.0f}% kontost)")
print(f"marginaal 1:500 juures: "
      f"{int(n_pos.median())*kesk_nots/500:.0f} EUR ({100*int(n_pos.median())*kesk_nots/500/KAPITAL:.0f}% kontost)")

print(f"\nportfelli 1-sigma nadalane PnL miinimumlottidega: "
      f"{math.sqrt(sum((r[3])**2 for r in read[:int(n_pos.median())])):.2f} EUR "
      f"= {100*math.sqrt(sum((r[3])**2 for r in read[:int(n_pos.median())]))/KAPITAL:.1f}% kontost")
print("(eeldab, et paarid on soltumatud; tegelikult korreleeritud => veel suurem)")

for eesmark in (0.0025, 0.0050):
    vaja_k = max(r[3] for r in read) / eesmark
    print(f"\nkonto, kus KOIK 7 paari mahuvad {100*eesmark:.2f}% riski sisse: "
          f"{vaja_k:.0f} EUR")
