"""
cot_robust.py — kas A_REV (ekstreemse positsioneerimise fade) on PARIS?

Kriitiline kusimus: kas COT annab infot, mida hinnas EI OLE?
Spekulandid jalitavad trendi, seega ekstreemne positsioon on tugevalt
korreleeritud varasema hinnaliikumisega. Kui hinnapohine analoog annab
sama tulemuse, siis COT on maskeeritud OHLC-strateegia.
"""
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R

al = R.ehita_alus()
IDX = al["sis"].index


def sh_n(x):
    x = np.asarray(x, float); x = x[np.isfinite(x)]
    sd = x.std(ddof=1)
    return x.mean() / sd if sd > 0 else 0.0


def rea(nimi, x, laius=20):
    m = E.moodikud(x, nimi)
    if m is None:
        return f"{nimi:<{laius}s}  (liiga vahe vaatlusi)"
    return (f"{nimi:<{laius}s}{m['n']:>5d}{m['keskm_bp']:>9.2f}{m['sh']:>8.2f}"
            f"{100*m['kokku']:>9.1f}{100*m['maxdd']:>8.1f}{m['pf']:>7.2f}"
            f"{m['wr']:>7.1f}{m['t']:>7.2f}{E.p_kahepoolne(m['t']):>8.3f}")


def pais(laius=20):
    return (f"{'variant':<{laius}s}{'n':>5s}{'keskm_bp':>9s}{'sharpe':>8s}"
            f"{'kokku%':>9s}{'maxdd%':>8s}{'pf':>7s}{'wr%':>7s}{'t':>7s}{'p':>8s}")


print("=" * 96)
print("R1  AUS JUHUSLIK NULL — sama selektsioon, ainult suund juhuslik")
print("=" * 96)
VAL = ("U7", "U28")
STRUKT = [(s, h, u) for u in VAL for s in ("A_CONT", "B_CONT", "C_CONT")
          for h in E.HOIUD]
KATSEID = 500
rs = np.random.RandomState(20260913)
maxid = np.zeros(KATSEID)
for s, h, u in STRUKT:
    paarid, kulu = R.universum(u, al["V"])
    S = R.skoorid(al, s)
    H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
    mask = (S != 0).values
    for i in range(KATSEID):
        Sj = pd.DataFrame(np.where(mask, rs.choice([-1.0, 1.0], size=S.shape), 0.0),
                          index=S.index, columns=S.columns)
        W = E.kaalud(Sj, paarid, h)
        x = E.portfell(W, H, kulu)["neto"].values
        maxid[i] = max(maxid[i], abs(sh_n(x)))
print(f"18 struktuuri x 2 suunda = 36 varianti, {KATSEID} juhuslikku katset")
print(f"parim-36-st juhuslik Sharpe (nadalane): "
      f"mediaan {np.median(maxid):.4f}  95% {np.quantile(maxid,0.95):.4f}  "
      f"max {maxid.max():.4f}")
paris_sh = 1.13 / math.sqrt(52)
print(f"PARIS parim (U28 A_REV h1) sh_nadal = {paris_sh:.4f}")
print(f"empiiriline p (parim-36-st null) = "
      f"{float((maxid >= paris_sh).mean()):.4f}")

print()
print("=" * 96)
print("R2  VALITUD VARIANDI juhuslik null (U28 A_REV h1, sama struktuur)")
print("=" * 96)
bp, shs = R.juhuslik_baseline(al, "A_REV", 1, "U28", katseid=500)
W, H, r = R.joosta(al, "A_REV", 1, "U28")
tegelik = 1e4 * r["neto"].mean()
print(f"juhuslik keskm_bp: mediaan {np.median(bp):+.2f}  "
      f"95% {np.quantile(bp,0.95):+.2f}  max {bp.max():+.2f}")
print(f"tegelik keskm_bp : {tegelik:+.2f}   empiiriline p = "
      f"{float((bp >= tegelik).mean()):.4f}")

print()
print("=" * 96)
print("R3/R4  BASELINE'ID — osta-ja-hoia ja juba testitud OHLC-momentum")
print("=" * 96)
print(pais())
for u in VAL:
    bh = R.osta_hoia(al, u)
    print(rea(f"{u} osta-ja-hoia", bh["neto"]))
for u in VAL:
    for h in E.HOIUD:
        o = R.ohlc_baseline(al, h, u)
        print(rea(f"{u} px-mom h{h}", o["neto"]))
        print(rea(f"{u} px-mom REV h{h}", -o["bruto"] - o["kulu"]))

print()
print("=" * 96)
print("R5  KAS SEE ON MASKEERITUD OHLC? — identne masinavark, hinnapohine sisend")
print("=" * 96)
Vw = al["V"].reindex(al["sis"].values); Vw.index = IDX
for lag in (12, 26, 52):
    m = np.log(Vw).diff(lag)
    m = m.sub(m.mean(axis=1), axis=0).reindex(columns=al["P"].columns)
    Ppx = m.apply(E.rull_pertsentiil)          # sama 156n rullpertsentiil
    Spx = -E.skoor_A(Ppx)                      # sama REV-suund
    for u in ("U28",):
        paarid, kulu = R.universum(u, al["V"])
        H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
        for h in (1,):
            rr = E.portfell(E.kaalud(Spx, paarid, h), H, kulu)
            print(rea(f"{u} PX{lag}_REV h{h}", rr["neto"]))
# korrelatsioon COT-pertsentiili ja hinnamomentumi-pertsentiili vahel
m26 = np.log(Vw).diff(26); m26 = m26.sub(m26.mean(axis=1), axis=0)
P26 = m26.reindex(columns=al["P"].columns).apply(E.rull_pertsentiil)
kor = {c: al["P"][c].corr(P26[c]) for c in al["P"].columns}
print("\nCOT-pertsentiil vs 26n hinnamomentumi-pertsentiil, korrelatsioon:")
print("  " + "  ".join(f"{c} {kor[c]:+.2f}" for c in kor))
print(f"  keskmine {np.nanmean(list(kor.values())):+.3f}")

print()
print("=" * 96)
print("R6  ORTOGONALISEERIMINE — kas COT-l on ALFA hinnapohise variandi jarel?")
print("=" * 96)
Spx26 = -E.skoor_A(P26)
paarid, kulu = R.universum("U28", al["V"])
H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
r_px = E.portfell(E.kaalud(Spx26, paarid, 1), H, kulu)["neto"]
r_cot = R.joosta(al, "A_REV", 1, "U28")[2]["neto"]
ix = r_cot.index.intersection(r_px.index)
y, x = r_cot.reindex(ix).values, r_px.reindex(ix).values
ok = np.isfinite(y) & np.isfinite(x)
y, x = y[ok], x[ok]
b = np.cov(y, x, ddof=1)[0, 1] / np.var(x, ddof=1)
a = y.mean() - b * x.mean()
res = y - (a + b * x)
se = res.std(ddof=2) / math.sqrt(len(y))
print(f"r_COT = alfa + beeta * r_PX26REV")
print(f"  beeta       {b:+.3f}")
print(f"  alfa        {1e4*a:+.2f} bp/nadal   t = {a/se:+.2f}   "
      f"p = {E.p_kahepoolne(a/se):.4f}")
print(f"  korr(COT,PX){np.corrcoef(y,x)[0,1]:+.3f}")

print()
print("=" * 96)
print("R7  TRAIN / VALIDATION / FINAL OOS")
print("=" * 96)
print(f"TRAIN  .. {E.TRAIN_LOPP.date()}   VALID .. {E.VALID_LOPP.date()}   "
      f"FINAL OOS {E.VALID_LOPP.date()} ..")
print(pais(24))
for u in VAL:
    for h in E.HOIUD:
        rr = R.joosta(al, "A_REV", h, u)[2]["neto"]
        tr, va, oos = E.jaota(rr)
        for nm, x in (("TRAIN", tr), ("VALID", va), ("OOS", oos)):
            print(rea(f"{u} A_REV h{h} {nm}", x, 24))
        print()
