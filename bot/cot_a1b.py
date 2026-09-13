"""
cot_a1b.py — A1 falsifitseerimise 7 kusimust (jatk cot_a1.py-le).
"""
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R

al = R.ehita_alus(sufiks="_d25")
IDX = al["sis"].index
PER = [("C 2006-2016", "2006-05-01", "2016-08-29"),
       ("D 2016-2026", "2016-08-30", "2026-12-31"),
       ("E 2006-2026", "2006-05-01", "2026-12-31")]
LAI = 24


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
    return (f"{'variant':<{laius}s}{'n':>5s}{'keskm_bp':>9s}{'sharpe':>8s}"
            f"{'kokku%':>9s}{'maxdd%':>8s}{'pf':>7s}{'wr%':>7s}{'t':>7s}{'p':>8s}")


def joosta(S, paarid, kulu, hoia=1):
    H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
    W = E.kaalud(S, paarid, hoia)
    return W, H, E.portfell(W, H, kulu)


S = R.skoorid(al, "A_REV")
p7, k7 = R.universum("U7", al["V"])
p28, k28 = R.universum("U28", al["V"])

print("=" * 100)
print("Q1  KAS EFEKT KAOB ENNE 2016? + kas suund POORDUB (A_CONT vs A_REV)?")
print("=" * 100)
print(pais())
for uni, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    for suund in ("A_REV", "A_CONT"):
        r = joosta(R.skoorid(al, suund), paarid, kulu)[2]["neto"].dropna()
        for nimi, a, b in PER:
            print(rea(f"{uni} {suund} {nimi[0]}", loik(r, a, b)))
    print()

print("=" * 100)
print("Q2  KAS UKS PERIOOD TEEB KOGU KASUMI?")
print("=" * 100)
for uni, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    r = joosta(S, paarid, kulu)[2]["neto"].dropna()
    kogu = r.sum()
    c = loik(r, "2006-05-01", "2016-08-29").sum()
    d = loik(r, "2016-08-30", "2026-12-31").sum()
    print(f"  {uni}: kogu logsumma {100*kogu:+.1f}%   "
          f"2006-2016 {100*c:+.1f}%   2016-2026 {100*d:+.1f}%")
    print(f"       2016-2026 osakaal koigist POSITIIVSETEST nadalatest: "
          f"{100*loik(r,'2016-08-30','2026-12-31')[lambda s: s>0].sum()/r[r>0].sum():.1f}%")

print()
print("=" * 100)
print("Q3+Q4  KONTSENTRATSIOON JA PARIMA PAARI/VALUUTA EEMALDUS, PERIOODIDE KAUPA")
print("=" * 100)
for uni, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    W, H, r = joosta(S, paarid, kulu)
    Rt = np.log(H).diff().shift(-1).reindex(W.index)
    for nimi, a, b in PER:
        Wp, Rp = loik(W, a, b), loik(Rt, a, b)
        panus = (Wp * Rp.fillna(0.0)).sum()
        kokku = panus.sum()
        jrk = panus.sort_values(ascending=False)
        vp = {c: 0.0 for c in E.VALUUTAD}
        for p, v in panus.items():
            vp[p[:3]] += v / 2.0
            vp[p[3:]] += v / 2.0
        vs = pd.Series(vp).sort_values(ascending=False)
        osa = (100 * jrk.iloc[0] / kokku) if kokku != 0 else float("nan")
        osav = (100 * vs.iloc[0] / kokku) if kokku != 0 else float("nan")
        print(f"\n  {uni} {nimi}: bruto kokku {100*kokku:+.2f}%")
        print(f"    positiivseid paare {int((panus>0).sum())}/{len(paarid)}"
              f" = {100*(panus>0).mean():.1f}%   mediaan paar {100*panus.median():+.2f}%")
        print(f"    TOP-1 paar {jrk.index[0]} {100*jrk.iloc[0]:+.2f}% = {osa:.1f}% kogusummast")
        print(f"    TOP-1 valuuta {vs.index[0]} {100*vs.iloc[0]:+.2f}% = {osav:.1f}% kogusummast")

print()
print("=" * 100)
print("Q4b  EEMALDA PARIM PAAR / PARIM VALUUTA (periood E, kogu valim)")
print("=" * 100)
print(pais())
W, H, r = joosta(S, p28, k28)
Rt = np.log(H).diff().shift(-1).reindex(W.index)
panus = (W * Rt.fillna(0.0)).sum()
vp = {c: 0.0 for c in E.VALUUTAD}
for p, v in panus.items():
    vp[p[:3]] += v / 2.0
    vp[p[3:]] += v / 2.0
pv, pp = pd.Series(vp).idxmax(), panus.idxmax()
print(rea("U28 E koik", r["neto"]))
print(rea(f"U28 E ilma {pp}", joosta(S, [q for q in p28 if q != pp], k28)[2]["neto"]))
print(rea(f"U28 E ilma valuutata {pv}",
          joosta(S, [q for q in p28 if pv not in (q[:3], q[3:])], k28)[2]["neto"]))

print()
print("=" * 100)
print("Q5  KAS PIKEM VALIM NORGENDAB OLULISUST?")
print("=" * 100)
print(f"{'universum':<12s}{'periood':<14s}{'n':>6s}{'keskm_bp':>10s}{'t':>8s}{'p':>9s}")
for uni, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    r = joosta(S, paarid, kulu)[2]["neto"].dropna()
    for nimi, a, b in PER:
        x = loik(r, a, b)
        sd = x.std(ddof=1)
        t = x.mean() / sd * math.sqrt(len(x))
        print(f"{uni:<12s}{nimi:<14s}{len(x):>6d}{1e4*x.mean():>10.2f}"
              f"{t:>8.2f}{E.p_kahepoolne(t):>9.3f}")

print()
print("=" * 100)
print("Q6  KULUTUNDLIKKUS PERIOODIL E (kas kulu on sussi?)")
print("=" * 100)
print(pais())
for uni, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    W, H, _ = joosta(S, paarid, kulu)
    for k in (0.0, 1.0, 2.0, 3.0):
        print(rea(f"{uni} E kulu {k:.0f}bp", E.portfell(W, H, k)["neto"]))
    print(rea(f"{uni} E NEMSIS BASE", E.portfell(W, H, kulu)["neto"]))

print()
print("=" * 100)
print("Q7  KAS 2016-2026 OLI LIHTSALT VALIMISPETSIIFILINE?")
print("=" * 100)
rs = np.random.RandomState(20260913)
for uni, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    r = joosta(S, paarid, kulu)[2]["neto"].dropna()
    d_tegelik = 1e4 * loik(r, "2016-08-30", "2026-12-31").mean()
    # kui pikk seeria on mureta kohin, kui sageli annab SUVALINE 522-nadalane
    # kate keskmise >= tegeliku 2016-2026 tulemuse? (block bootstrap seeriast)
    x = r.values
    n = 522
    kate = np.array([x[i:i + n].mean() for i in range(len(x) - n + 1)])
    print(f"  {uni}: koik {len(kate)} 522-nadalast liikuvat akent kogu valimis")
    print(f"     mediaan {1e4*np.median(kate):+.2f}bp  min {1e4*kate.min():+.2f}bp  "
          f"max {1e4*kate.max():+.2f}bp   tegelik 2016-2026 {d_tegelik:+.2f}bp")
    print(f"     tegelik on {100*(kate <= d_tegelik/1e4).mean():.1f}. protsentiil")
    # juhuslik null PIKAL valimil
    bp = []
    Smask = (S != 0).values
    H = E.nadala_hinnad(al["V"], paarid, al["sis"]); H.index = IDX
    for _ in range(300):
        Sj = pd.DataFrame(np.where(Smask, rs.choice([-1.0, 1.0], size=S.shape), 0.0),
                          index=S.index, columns=S.columns)
        bp.append(1e4 * E.portfell(E.kaalud(Sj, paarid, 1), H, kulu)["neto"].mean())
    bp = np.array(bp)
    tegelik_e = 1e4 * r.mean()
    print(f"     juhuslik null (E, 300 katset): mediaan {np.median(bp):+.2f}bp  "
          f"95% {np.quantile(bp,0.95):+.2f}bp   tegelik E {tegelik_e:+.2f}bp  "
          f"p = {float((bp >= tegelik_e).mean()):.3f}")

print()
print("=" * 100)
print("LISA  2008 KRIISIAASTA MOJU (kas C on negatiivne ainult 2008 parast?)")
print("=" * 100)
print(pais())
for uni, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    r = joosta(S, paarid, kulu)[2]["neto"].dropna()
    c = loik(r, "2006-05-01", "2016-08-29")
    print(rea(f"{uni} C 2006-2016", c))
    print(rea(f"{uni} C ilma 2008", c[c.index.year != 2008]))
    print(rea(f"{uni} C ilma 2008-2009", c[~c.index.year.isin([2008, 2009])]))

print()
print("=" * 100)
print("LISA2  ANDMEKVALITEET — kas 2006-2016 negatiivsus tuleb katkistest baaridest?")
print("=" * 100)
print("lipuga paevad (|r|>=5% JA jargmisel paeval peaaegu taielik tagasipoore):")
kokku_lipp = 0
for p in E.U7:
    x, n = E.puhasta_spike(E.lae_hind(p, "_d25"))
    kokku_lipp += n
    if n:
        s = E.lae_hind(p, "_d25")
        d = (x / s - 1).abs()
        d = d[d > 1e-9]
        print(f"  {p}: {n} paeva  "
              + ", ".join(f"{k.date()}({100*v:.1f}%)" for k, v in d.items()))
print(f"  KOKKU {kokku_lipp} katkist baari; paris hupped (SNB 2011/2015, "
      f"Brexit 2016, GFC AUD) jaid puutumata")

alp = R.ehita_alus(sufiks="_d25", puhasta=True)
print()
print(pais())
for uni, paarid, kulu in (("U7", p7, k7), ("U28", p28, k28)):
    r_raw = joosta(S, paarid, kulu)[2]["neto"].dropna()
    Sp = R.skoorid(alp, "A_REV")
    Hp = E.nadala_hinnad(alp["V"], paarid, alp["sis"]); Hp.index = alp["sis"].index
    r_puh = E.portfell(E.kaalud(Sp, paarid, 1), Hp, kulu)["neto"].dropna()
    for nimi, a, b in PER:
        print(rea(f"{uni} {nimi[0]} toores", loik(r_raw, a, b)))
        print(rea(f"{uni} {nimi[0]} puhastatud", loik(r_puh, a, b)))
