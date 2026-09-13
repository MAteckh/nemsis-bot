"""
cot_run.py — 36 eelregistreeritud COT-varianti + baseline'id.

Variandid = 6 signaali (A/B/C x CONT/REV) x 3 hoidu (1/2/4 n) x 2 universumit.
Baseline'id: juhuslik (sama selektsioon), osta-ja-hoia, OHLC-momentum.
"""
import itertools
import json
import math

import numpy as np
import pandas as pd

import cot_engine as E

RS = np.random.RandomState(20260913)
SIGNAALID = ["A_CONT", "A_REV", "B_CONT", "B_REV", "C_CONT", "C_REV"]


# ------------------------------------------------------------ ehitusplokid -
def ehita_alus(usd_allikas="implitseeritud", sufiks="_d", puhasta=False):
    d = E.lae_cot()
    N = E.net_pct_tabel(d, usd_allikas)
    V = E.usd_vaartused(sufiks, puhasta)
    sis = E.sisenemispaevad(N.index, V.index)
    P = N.apply(E.rull_pertsentiil).reindex(sis.index)
    Nw = N.reindex(sis.index)
    # hinnad sisenemispaevadel; momentum arvutatakse AINULT minevikust
    Vw = V.reindex(sis.values)
    Vw.index = sis.index
    mom = np.log(Vw).diff(E.MOM_NADALAD)
    mom = mom.sub(mom.mean(axis=1), axis=0)        # USD saab sisu (demean)
    mom = mom.reindex(columns=P.columns)           # sama veerujarjestus kui P
    return dict(N=N, Nw=Nw, P=P, V=V, sis=sis, mom=mom)


def skoorid(al, nimi):
    """Valuutataseme soovitud positsioon (nadal x valuuta)."""
    A = E.skoor_A(al["P"])
    if nimi == "A_CONT":
        return A
    if nimi == "A_REV":
        return -A
    if nimi in ("B_CONT", "B_REV"):
        B = E.skoor_B(al["Nw"])
        return B if nimi == "B_CONT" else -B
    S = A if nimi == "C_CONT" else -A
    # jaa alles ainult seal, kus 12-nadalane momentum on SAMAS suunas
    return S.where(np.sign(al["mom"]) == S, 0.0)


def universum(nimi, V):
    if nimi == "U7":
        return E.U7, E.KULU_BASE
    paarid, kulu = [], {}
    for b, q in itertools.permutations(E.VALUUTAD, 2):
        if b + q in E.U7 or q + b in paarid:
            pass
        p = b + q
        if q + b in paarid:
            continue
        paarid.append(p)
        kulu[p] = E.KULU_BASE.get(p, E.KULU_RIST)
    return paarid, kulu


def joosta(al, sig_nimi, hoia, uni, kulu_bp=None):
    paarid, kulu_dict = universum(uni, al["V"])
    S = skoorid(al, sig_nimi)
    W = E.kaalud(S, paarid, hoia)
    H = E.nadala_hinnad(al["V"], paarid, al["sis"])
    H.index = al["sis"].index
    k = kulu_dict if kulu_bp is None else kulu_bp
    r = E.portfell(W, H, k)
    return W, H, r


# --------------------------------------------------------------- baseline --
def juhuslik_baseline(al, sig_nimi, hoia, uni, katseid=1000):
    """
    AUS NULL: tapselt sama selektsioon (samad nadalad, sama arv positsioone,
    sama hoideperiood, sama kulumudel), AINULT suund juhuslikuks tehtud.
    """
    paarid, kulu_dict = universum(uni, al["V"])
    S = skoorid(al, sig_nimi)
    H = E.nadala_hinnad(al["V"], paarid, al["sis"])
    H.index = al["sis"].index
    mask = (S != 0).values
    out_bp, out_sh = [], []
    for _ in range(katseid):
        margid = RS.choice([-1.0, 1.0], size=S.shape)
        Sj = pd.DataFrame(np.where(mask, margid, 0.0),
                          index=S.index, columns=S.columns)
        W = E.kaalud(Sj, paarid, hoia)
        r = E.portfell(W, H, kulu_dict)
        x = r["neto"].values
        out_bp.append(x.mean() * 1e4)
        sd = x.std(ddof=1)
        out_sh.append(x.mean() / sd * math.sqrt(52) if sd > 0 else 0.0)
    return np.array(out_bp), np.array(out_sh)


def osta_hoia(al, uni):
    paarid, kulu_dict = universum(uni, al["V"])
    H = E.nadala_hinnad(al["V"], paarid, al["sis"])
    H.index = al["sis"].index
    W = pd.DataFrame(1.0 / len(paarid), index=H.index, columns=paarid)
    return E.portfell(W, H, kulu_dict)


def ohlc_baseline(al, hoia, uni):
    """Juba testitud perekond: 12-nadalane ristloikeline hinnamomentum."""
    m = al["mom"]
    r = m.rank(axis=1, ascending=False)
    n = m.notna().sum(axis=1)
    S = ((r.le(2) & m.notna()).astype(float)
         - (r.gt(n.values[:, None] - 2) & m.notna()).astype(float))
    paarid, kulu_dict = universum(uni, al["V"])
    W = E.kaalud(S, paarid, hoia)
    H = E.nadala_hinnad(al["V"], paarid, al["sis"])
    H.index = al["sis"].index
    return E.portfell(W, H, kulu_dict)


# ------------------------------------------------------------------ main ---
def rida(m, lisa=""):
    return (f"{m['nimi']:<18s}{m['n']:>5d}{m['keskm_bp']:>9.2f}"
            f"{m['sh']:>8.2f}{100*m['kokku']:>9.1f}{100*m['maxdd']:>8.1f}"
            f"{m['pf']:>7.2f}{m['wr']:>7.1f}{m['t']:>7.2f}"
            f"{E.p_kahepoolne(m['t']):>8.3f}  {lisa}")


def pais():
    return ("variant              n  keskm_bp   sharpe   kokku%   maxdd%"
            "     pf    wr%      t       p")


if __name__ == "__main__":
    al = ehita_alus()
    print(f"COT nadalaid: {len(al['sis'])}  "
          f"{al['sis'].index.min().date()} .. {al['sis'].index.max().date()}")
    print(f"esimene kauplemispaev {al['sis'].iloc[0].date()}  "
          f"viimane {al['sis'].iloc[-1].date()}\n")

    read = []
    print("=" * 100)
    print("36 EELREGISTREERITUD VARIANTI — kulu = NEMSIS BASE (uhesuunaline bp)")
    print("=" * 100)
    print(pais())
    for uni in ("U7", "U28"):
        for s in SIGNAALID:
            for h in E.HOIUD:
                W, H, r = joosta(al, s, h, uni)
                m = E.moodikud(r["neto"], f"{uni} {s} h{h}")
                if m is None:
                    continue
                mb = E.moodikud(r["bruto"], "")
                m["bruto_bp"] = mb["keskm_bp"]
                m["kulu_bp"] = 1e4 * r["kulu"].mean()
                m["uni"], m["sig"], m["hoia"] = uni, s, h
                read.append(m)
                print(rida(m, f"bruto {m['bruto_bp']:+.2f}bp kulu {m['kulu_bp']:.2f}bp"))
        print("-" * 100)

    # --- mitme testi korrektsioon ------------------------------------------
    pv = [E.p_kahepoolne(m["t"]) for m in read]
    lavi, labi = E.bh(pv, 0.05)
    print(f"\nBenjamini-Hochberg q=0.05 ule {len(read)} variandi: "
          f"lavi p={lavi:.4f}, labis {len(labi)}")
    for i in labi:
        print(f"   {read[i]['nimi']}  p={pv[i]:.4f}  keskm {read[i]['keskm_bp']:+.2f}bp")
    pos = [i for i in labi if read[i]["keskm_bp"] > 0]
    print(f"   nendest POSITIIVSEID: {len(pos)}")

    parim = max(read, key=lambda m: m["sh"])
    sh_n = parim["sh"] / math.sqrt(52)          # vaatluse kohta, mitte aastas
    koik_n = np.array([m["sh"] for m in read]) / math.sqrt(52)
    ds = E.deflated_sharpe(sh_n, koik_n.std(ddof=1), parim["n"], len(read))
    print(f"\nParim Sharpe: {parim['nimi']} sh_aasta={parim['sh']:.2f} "
          f"sh_nadal={sh_n:.4f} n={parim['n']}")
    print(f"   36 variandi Sharpe std (nadalane) = {koik_n.std(ddof=1):.4f}")
    print(f"   Deflated Sharpe p={ds:.4f}  (vaja > 0.95)")

    json.dump([{k: (float(v) if isinstance(v, (int, float, np.floating)) else v)
                for k, v in m.items()} for m in read],
              open("cot_tulemused.json", "w"), indent=1)
    print("\nsalvestatud: cot_tulemused.json")
