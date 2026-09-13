"""
cot_robust2.py — kontsentratsioon, kulud, ajastus, lavid, tehingutasand.
"""
import itertools
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R

al = R.ehita_alus()
IDX = al["sis"].index
LAI = 26


def rea(nimi, x, laius=LAI):
    m = E.moodikud(x, nimi)
    if m is None:
        return f"{nimi:<{laius}s}  (liiga vahe vaatlusi)"
    return (f"{nimi:<{laius}s}{m['n']:>5d}{m['keskm_bp']:>9.2f}{m['sh']:>8.2f}"
            f"{100*m['kokku']:>9.1f}{100*m['maxdd']:>8.1f}{m['pf']:>7.2f}"
            f"{m['wr']:>7.1f}{m['t']:>7.2f}{E.p_kahepoolne(m['t']):>8.3f}")


def pais(laius=LAI):
    return (f"{'variant':<{laius}s}{'n':>5s}{'keskm_bp':>9s}{'sharpe':>8s}"
            f"{'kokku%':>9s}{'maxdd%':>8s}{'pf':>7s}{'wr%':>7s}{'t':>7s}{'p':>8s}")


def joosta_paaridega(S, paarid, kulu, hoia):
    H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
    W = E.kaalud(S, paarid, hoia)
    return W, H, E.portfell(W, H, kulu)


S_AREV = R.skoorid(al, "A_REV")

print("=" * 100)
print("R8  KONTSENTRATSIOON — kas kogu kasum tuleb uhest paarist/valuutast?")
print("=" * 100)
for uni in ("U7", "U28"):
    paarid, kulu = R.universum(uni, al["V"])
    W, H, r = joosta_paaridega(S_AREV, paarid, kulu, 1)
    Rt = np.log(H).diff().shift(-1).reindex(W.index)
    panus = (W * Rt.fillna(0.0)).sum() * 1e4 * len(W) / len(W)   # summa bp
    panus = (W * Rt.fillna(0.0)).sum()                            # kogupanus
    kokku = panus.sum()
    jrk = panus.sort_values(ascending=False)
    kasum = jrk[jrk > 0].sum()
    print(f"\n{uni}: {len(paarid)} paari, kogu bruto {100*kokku:.2f}%")
    print(f"  positiivseid paare {int((panus>0).sum())}/{len(paarid)} "
          f"= {100*(panus>0).mean():.1f}%")
    print(f"  mediaan paar {100*panus.median():+.2f}%")
    print(f"  TOP-1 {jrk.index[0]} {100*jrk.iloc[0]:+.2f}% = "
          f"{100*jrk.iloc[0]/kokku:.1f}% kogukasumist")
    print(f"  TOP-3 {', '.join(jrk.index[:3])} = "
          f"{100*jrk.iloc[:3].sum()/kokku:.1f}% kogukasumist")
    # valuutapanus: iga paar jaguneb kahe valuuta vahel
    vp = {c: 0.0 for c in E.VALUUTAD}
    for p, v in panus.items():
        vp[p[:3]] += v / 2.0
        vp[p[3:]] += v / 2.0
    vs = pd.Series(vp).sort_values(ascending=False)
    print("  valuutapanus: " + "  ".join(f"{c} {100*v:+.1f}%" for c, v in vs.items()))
    print(f"  TOP-1 valuuta {vs.index[0]} = {100*vs.iloc[0]/kokku:.1f}% kogukasumist")

print()
print("=" * 100)
print("R9  EEMALDA PARIM VALUUTA / PARIM PAAR")
print("=" * 100)
print(pais())
paarid28, kulu28 = R.universum("U28", al["V"])
W, H, r = joosta_paaridega(S_AREV, paarid28, kulu28, 1)
Rt = np.log(H).diff().shift(-1).reindex(W.index)
panus = (W * Rt.fillna(0.0)).sum()
vp = {c: 0.0 for c in E.VALUUTAD}
for p, v in panus.items():
    vp[p[:3]] += v / 2.0
    vp[p[3:]] += v / 2.0
parim_val = pd.Series(vp).idxmax()
parim_paar = panus.idxmax()
print(rea("U28 A_REV h1 (koik)", r["neto"]))
ilma_p = [p for p in paarid28 if p != parim_paar]
print(rea(f"ilma paarita {parim_paar}",
          joosta_paaridega(S_AREV, ilma_p, kulu28, 1)[2]["neto"]))
for v in E.VALUUTAD:
    jaa = [p for p in paarid28 if v not in (p[:3], p[3:])]
    print(rea(f"ilma valuutata {v}",
              joosta_paaridega(S_AREV, jaa, kulu28, 1)[2]["neto"]))
print()
paarid7, kulu7 = R.universum("U7", al["V"])
print(rea("U7 A_REV h1 (koik)", joosta_paaridega(S_AREV, paarid7, kulu7, 1)[2]["neto"]))
for p in paarid7:
    jaa = [q for q in paarid7 if q != p]
    print(rea(f"U7 ilma {p}", joosta_paaridega(S_AREV, jaa, kulu7, 1)[2]["neto"]))

print()
print("=" * 100)
print("R10  KULUTUNDLIKKUS (uhesuunaline bp kaibelt)")
print("=" * 100)
print(pais())
for uni, paarid, kbase in (("U7", paarid7, kulu7), ("U28", paarid28, kulu28)):
    W, H, _ = joosta_paaridega(S_AREV, paarid, kbase, 1)
    kaive = W.diff().abs().sum(axis=1).mean()
    print(f"  {uni}: keskmine nadalane kaive sum|dw| = {kaive:.3f} "
          f"=> 1bp kulu = {1e4*kaive/1e4:.2f}bp nadalas")
    for k in (0.0, 1.0, 2.0, 3.0, 5.0, 8.0):
        print(rea(f"{uni} A_REV h1 kulu {k:.0f}bp",
                  E.portfell(W, H, k)["neto"]))
    print(rea(f"{uni} A_REV h1 NEMSIS BASE", E.portfell(W, H, kbase)["neto"]))
    khigh = {p: 2.0 * v for p, v in kbase.items()}
    print(rea(f"{uni} A_REV h1 NEMSIS HIGH", E.portfell(W, H, khigh)["neto"]))
    print()

print("=" * 100)
print("R11  SISENEMISE AJASTUS — kas serv soltub sellest, kui kiiresti siseneme?")
print("=" * 100)
print(pais())
d = E.lae_cot()
N = E.net_pct_tabel(d)
Pfull = N.apply(E.rull_pertsentiil)
for viive, silt in ((3, "reede (release-paev)"), (6, "esmaspaev (NEMSIS)"),
                    (7, "teisipaev +1p"), (9, "kolmapaev +3p"),
                    (13, "jargmine esmaspaev")):
    sis = E.sisenemispaevad(N.index, al["V"].index, viive=viive, max_nihe=viive + 8)
    P2 = Pfull.reindex(sis.index)
    S2 = -E.skoor_A(P2)
    H2 = E.nadala_hinnad(al["V"], paarid28, sis); H2.index = sis.index
    W2 = E.kaalud(S2, paarid28, 1)
    print(rea(f"U28 viive {viive}d {silt}", E.portfell(W2, H2, kulu28)["neto"]))

print()
print("=" * 100)
print("R12  LAVITUNDLIKKUS (EI ole optimeerimine — robustsuskontroll)")
print("=" * 100)
print(pais())
for yla, ala in ((0.95, 0.05), (0.90, 0.10), (0.85, 0.15), (0.80, 0.20), (0.75, 0.25)):
    S3 = -((al["P"] >= yla).astype(float) - (al["P"] <= ala).astype(float))
    print(rea(f"U28 lavi {ala:.2f}/{yla:.2f}",
              joosta_paaridega(S3, paarid28, kulu28, 1)[2]["neto"]))

print()
print("=" * 100)
print("R13  MUUD DEFINITSIOONID — USD-skoor, toorne netopositsioon, aken")
print("=" * 100)
print(pais())
alx = R.ehita_alus(usd_allikas="USDX")
print(rea("U28 USD=USDX futuur",
          R.joosta(alx, "A_REV", 1, "U28")[2]["neto"]))
Nraw = d.pivot_table(index="date", columns="cur", values="net").sort_index()
muud = [c for c in E.VALUUTAD if c != "USD"]
Nraw["USD"] = -Nraw[muud].mean(axis=1)
Nraw = Nraw[[c for c in E.VALUUTAD]]
Praw = Nraw.apply(E.rull_pertsentiil).reindex(IDX)
print(rea("U28 toorne net (mitte /OI)",
          joosta_paaridega(-E.skoor_A(Praw), paarid28, kulu28, 1)[2]["neto"]))
for aken in (104, 156, 260):
    Pa = N.apply(lambda s: E.rull_pertsentiil(s, aken)).reindex(IDX)
    print(rea(f"U28 pertsentiiliaken {aken}n",
              joosta_paaridega(-E.skoor_A(Pa), paarid28, kulu28, 1)[2]["neto"]))

print()
print("=" * 100)
print("R14  USD-JALG vs RISTID — kust efekt tuleb?")
print("=" * 100)
print(pais())
S_noUSD = S_AREV.copy(); S_noUSD["USD"] = 0.0
print(rea("U7  USD-skoor nulliks", joosta_paaridega(S_noUSD, paarid7, kulu7, 1)[2]["neto"]))
print(rea("U28 USD-skoor nulliks", joosta_paaridega(S_noUSD, paarid28, kulu28, 1)[2]["neto"]))
ristid = [p for p in paarid28 if "USD" not in p]
print(rea(f"ainult {len(ristid)} risti (ei USD)",
          joosta_paaridega(S_AREV, ristid, kulu28, 1)[2]["neto"]))

print()
print("=" * 100)
print("R15  AASTATE KAUPA (U28 A_REV h1, neto)")
print("=" * 100)
r28 = R.joosta(al, "A_REV", 1, "U28")[2]["neto"]
r7 = R.joosta(al, "A_REV", 1, "U7")[2]["neto"]
print(f"{'aasta':<8s}{'U28 bp/n':>10s}{'U28 aasta%':>12s}"
      f"{'U7 bp/n':>10s}{'U7 aasta%':>12s}{'nadalaid':>10s}")
for y in sorted(set(r28.index.year)):
    a, b = r28[r28.index.year == y], r7[r7.index.year == y]
    print(f"{y:<8d}{1e4*a.mean():>10.2f}{100*(np.exp(a.sum())-1):>12.2f}"
          f"{1e4*b.mean():>10.2f}{100*(np.exp(b.sum())-1):>12.2f}{len(a):>10d}")
