"""
d1_momentum_validation.py — D1 MOMENTUM FALSIFIKATSIOONITEST v1.

TAUST: Heat Map v1 leidis, et D1 MOMENTUM on ainus perekond, mille
RADA B agregaadi neto on positiivne: n=2678, +0.0303 R/tehing, t=+1.20.
See EI OLE toend. Siin uritakse seda TAPPA.

TAHTIS — UURIMISKOOD. Ei puuduta live-faile (main_v4.py, config.py,
mt5_connector.py, strategy_meanrev.py, backtest.py).

REEGLID ON MUUTMATA. Koik sisenemis-, valjumis-, SL-, TP-, rezhiimi- ja
kulureeglid tulevad OTSE hm_engine.py-st (import, mitte kopeerimine):
  MOMENTUM sisenemine: kontekst W1 EMA50 > EMA200 (pikk) voi < (luhike);
    sisenemisbaaril RSI(14) ristub ULES 55 ja close > EMA20 (pikk),
    RSI ristub ALLA 45 ja close < EMA20 (luhike)
  SL = 1.5 x ATR(14), TP = 2.0 R, max hoid 20 baari, uks positsioon korraga
  sisenemine JARGMISE baari avahinnaga, SL ja TP samas baaris => SL
  kulu = 2 x (spread + 0.3 bp slip) / SL-kaugus
  rezhiimid W1 eelmiselt lopetatud baarilt: HIGH/LOW_VOL (nATR vs 500-baari
    rullmediaan), TRENDING (ADX >= 25), RANGING (ADX < 20)

EELREGISTREERITUD GRUPID (maaratud ENNE tulemuste vaatamist, standardsed):
  MAJORS    7 USD-paari
  CROSSES   8 risti
  JPY       USDJPY EURJPY GBPJPY AUDJPY
  EUR       EURUSD EURGBP EURJPY EURCHF EURAUD
  COMMODITY AUDUSD NZDUSD USDCAD AUDJPY EURAUD GBPAUD AUDCAD

EELREGISTREERITUD PERIOODID:
  2006-2010, 2011-2015, 2016-2020, 2021-2026,
  TRAIN 2006-2013, VALID 2014-2017, OOS 2018-2026, ALL 2006-2026
"""
import math
import os
import sys

import numpy as np
import pandas as pd

import hm_engine as H

JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRAT = "MOMENTUM"
TF, CTX = "D1", "W"
MIN_N = 30

PERIOODID = [("2006-2010", "2006-01-01", "2010-12-31"),
             ("2011-2015", "2011-01-01", "2015-12-31"),
             ("2016-2020", "2016-01-01", "2020-12-31"),
             ("2021-2026", "2021-01-01", "2026-12-31"),
             ("TRAIN_2006_2013", "2006-01-01", "2013-12-31"),
             ("VALID_2014_2017", "2014-01-01", "2017-12-31"),
             ("OOS_2018_2026", "2018-01-01", "2026-12-31"),
             ("ALL_2006_2026", "2006-01-01", "2026-12-31")]

GRUPID = {
    "ALL": H.PAARID,
    "MAJORS": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"],
    "CROSSES": ["EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURCHF", "EURAUD",
                "GBPAUD", "AUDCAD"],
    "JPY": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"],
    "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURCHF", "EURAUD"],
    "COMMODITY": ["AUDUSD", "NZDUSD", "USDCAD", "AUDJPY", "EURAUD",
                  "GBPAUD", "AUDCAD"],
}


def andmed():
    D = {}
    for p in H.PAARID:
        d = H.lae_d1(p)
        if d is None or len(d) < 500:
            print(f"  {p}: INSUFFICIENT DATA")
            continue
        D[p] = (d, H.kontekst(d, CTX))
    return D


def tehingud(D, kulu_kordaja=1.0, slip=H.SLIP_BP):
    read = []
    for p, (d, k) in D.items():
        t = H.simuleeri(d, k, STRAT, TF, H.KULU_BP[p] * kulu_kordaja, slip_bp=slip)
        if len(t):
            t.insert(0, "paar", p)
            read.append(t)
    T = pd.concat(read, ignore_index=True)
    return T[(T["aeg"] >= pd.Timestamp("2006-01-01"))].reset_index(drop=True)


def moodikud(x, aastaid=None):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) == 0:
        return None
    sd = x.std(ddof=1) if len(x) > 1 else 0.0
    v, k = x[x > 0], x[x <= 0]
    eq = np.cumprod(1 + H.RISK * x)
    dd = 100.0 * float((eq / np.maximum.accumulate(eq) - 1).min())
    t = float(x.mean() / sd * math.sqrt(len(x))) if sd > 0 else 0.0
    sh = (float(x.mean() / sd * math.sqrt(len(x) / aastaid))
          if sd > 0 and aastaid and aastaid > 0 else np.nan)
    return dict(n=len(x), wr=100.0 * float((x > 0).mean()),
                neto=float(x.mean()), pf=(float(v.sum() / abs(k.sum()))
                                          if len(k) and k.sum() != 0 else np.inf),
                sharpe=sh, maxdd=dd, t=t, p=H.p_kahepoolne(t),
                kokku_r=float(x.sum()))


def loik(T, a, b):
    return T[(T["aeg"] >= pd.Timestamp(a)) & (T["aeg"] <= pd.Timestamp(b))]


def aastaid(x):
    if len(x) < 2:
        return np.nan
    return max((x["aeg"].max() - x["aeg"].min()).days / 365.25, 1e-9)


def rida(nimi, m, laius=26, lisa=""):
    if m is None:
        return f"{nimi:<{laius}s}  (tehinguid ei ole)"
    silt = "  INSUFFICIENT SAMPLE" if m["n"] < MIN_N else lisa
    sh = m["sharpe"]
    return (f"{nimi:<{laius}s}{m['n']:>6d}{m['wr']:>7.1f}{m['neto']:>+9.4f}"
            f"{m['pf']:>7.2f}{(sh if np.isfinite(sh) else 0):>8.2f}"
            f"{m['maxdd']:>8.1f}{m['t']:>7.2f}{m['p']:>8.3f}{silt}")


def pais(laius=26):
    return (f"{'lõige':<{laius}s}{'n':>6s}{'wr%':>7s}{'neto_R':>9s}{'PF':>7s}"
            f"{'Sharpe':>8s}{'maxDD%':>8s}{'t':>7s}{'p':>8s}")


# ------------------------------------------------------- 1. PERIOODID -----
def periood_tabel(T):
    read = []
    for nimi, a, b in PERIOODID:
        x = loik(T, a, b)
        m = moodikud(x["neto_r"], aastaid(x))
        if m is None:
            continue
        m.update(periood=nimi, algus=a, lopp=b,
                 bruto=float(x["bruto_r"].mean()), kulu=float(x["kulu_r"].mean()),
                 paare=int(x["paar"].nunique()),
                 pos_paare=int((x.groupby("paar")["neto_r"].mean() > 0).sum()))
        read.append(m)
    return pd.DataFrame(read)


# ----------------------------------------------------------- 2. PAARID ---
def paari_tabel(T):
    read = []
    for p in H.PAARID:
        for nimi, a, b in PERIOODID:
            x = loik(T[T["paar"] == p], a, b)
            m = moodikud(x["neto_r"], aastaid(x))
            if m is None:
                continue
            m.update(paar=p, periood=nimi,
                     bruto=float(x["bruto_r"].mean()),
                     kulu=float(x["kulu_r"].mean()),
                     piisav=bool(m["n"] >= MIN_N))
            read.append(m)
    return pd.DataFrame(read)


def grupi_tabel(T):
    read = []
    for g, paarid in GRUPID.items():
        for nimi, a, b in PERIOODID:
            x = loik(T[T["paar"].isin(paarid)], a, b)
            m = moodikud(x["neto_r"], aastaid(x))
            if m is None:
                continue
            m.update(grupp=g, periood=nimi, paare=len(paarid),
                     bruto=float(x["bruto_r"].mean()),
                     kulu=float(x["kulu_r"].mean()))
            read.append(m)
    return pd.DataFrame(read)


# ---------------------------------------------------------- 3. REZHIIM ---
def rezhiimi_tabel(T):
    read = []
    for rz in H.REZIIMID:
        x = T[T[rz]]
        m = moodikud(x["neto_r"], aastaid(x))
        if m:
            m.update(tase="KOIK PAARID", paar="-", rezhiim=rz)
            read.append(m)
        oos = loik(x, "2018-01-01", "2026-12-31")
        m2 = moodikud(oos["neto_r"], aastaid(oos))
        if m2:
            m2.update(tase="KOIK PAARID OOS", paar="-", rezhiim=rz)
            read.append(m2)
        for p in H.PAARID:
            y = x[x["paar"] == p]
            m3 = moodikud(y["neto_r"], aastaid(y))
            if m3:
                m3.update(tase="PAAR", paar=p, rezhiim=rz)
                read.append(m3)
    return pd.DataFrame(read)


# -------------------------------------------- 4. JUHUSLIK SISENEMINE -----
def juhuslik_benchmark(D, T, katseid=1000, seeme=20260915):
    """
    AUS NULL: samad instrumendid, sama periood, sama tehingute arv paari
    kohta, SAMA SL/TP/valjumine/kulu (kasutab sama H.simuleeri koodi).
    AINUS erinevus: sisenemissignaal on juhuslik (aeg ja suund).
    """
    rs = np.random.RandomState(seeme)
    n_paar = T.groupby("paar").size().to_dict()
    alg = H.signaalid
    read = []
    try:
        for i in range(katseid):
            koik = []
            for p, (d, k) in D.items():
                n = n_paar.get(p, 0)
                if n == 0:
                    continue
                # lubatud on baarid, kus ATR on olemas ja kuupaev >= 2006
                a = H.atr(d).values
                lubatud = np.where(np.isfinite(a) & (a > 0) &
                                   (d.index >= pd.Timestamp("2006-01-01")))[0]
                lubatud = lubatud[lubatud < len(d) - 2]
                if len(lubatud) < n:
                    continue
                # kalibreerimine: uks-positsioon-korraga reegel neelab osa
                # signaalidest, seega votame veidi rohkem kandidaate, et
                # LOPLIK tehingute arv oleks ligikaudu sama mis tegelikul
                # MOMENTUM-il (nouetes: "sama trade frequency ligikaudu")
                valitud = rs.choice(lubatud, size=min(int(n * 1.3), len(lubatud)),
                                    replace=False)
                sg = pd.Series(0, index=d.index, dtype=int)
                sg.iloc[valitud] = rs.choice([-1, 1], size=len(valitud))
                H.signaalid = (lambda dd, kk, nn, _s=sg: _s)
                t = H.simuleeri(d, k, STRAT, TF, H.KULU_BP[p])
                if len(t):
                    koik.append(t["neto_r"].values)
            if not koik:
                continue
            x = np.concatenate(koik)
            read.append((len(x), float(x.mean())))
    finally:
        H.signaalid = alg
    B = pd.DataFrame(read, columns=["n", "neto_per_teh"])
    return B


# -------------------------------------------------- 5. KULUSTRESS --------
def kulustress(D):
    variandid = [("BASE", 1.0, H.SLIP_BP), ("spread +25%", 1.25, H.SLIP_BP),
                 ("spread +50%", 1.50, H.SLIP_BP),
                 ("slippage 2x", 1.0, H.SLIP_BP * 2),
                 ("spread +50% & slip 2x", 1.50, H.SLIP_BP * 2),
                 ("spread +100%", 2.0, H.SLIP_BP),
                 ("kulu = 0 (ainult bruto)", 0.0, 0.0)]
    read = []
    for nimi, km, sl in variandid:
        T = tehingud(D, kulu_kordaja=km, slip=sl)
        for silt, a, b in (("ALL_2006_2026", "2006-01-01", "2026-12-31"),
                           ("OOS_2018_2026", "2018-01-01", "2026-12-31")):
            x = loik(T, a, b)
            m = moodikud(x["neto_r"], aastaid(x))
            m.update(variant=nimi, lõige=silt,
                     kulu=float(x["kulu_r"].mean()))
            read.append(m)
    return pd.DataFrame(read)


# --------------------------------------- 6. PARAMEETRI PERTURBATSIOON ----
PARAM = [("EMA_F", "EMA_F", 20, int), ("EMA_M", "EMA_M", 50, int),
         ("EMA_S", "EMA_S", 200, int), ("RSI_MOM_HI", "RSI_MOM_HI", 55.0, float),
         ("RSI_MOM_LO", "RSI_MOM_LO", 45.0, float),
         ("SL_ATR", "SL_ATR", 1.5, float), ("MAX_HOID", "MAX_HOID", 20, int),
         ("TP_R", "TP_R", 2.0, float), ("RSI_N", "RSI_N", 14, int),
         ("ATR_N", "ATR_N", 14, int)]


def sea_param(nimi, vaartus):
    if nimi == "MAX_HOID":
        H.MAX_HOID = dict(H.MAX_HOID, D1=int(vaartus))
    elif nimi == "TP_R":
        H.TP_R = dict(H.TP_R, MOMENTUM=float(vaartus))
    elif nimi == "RSI_N":
        H.rsi.__defaults__ = (int(vaartus),)
    elif nimi == "ATR_N":
        H.atr.__defaults__ = (int(vaartus),)
    else:
        setattr(H, nimi, vaartus)


def parameetri_robustsus(D):
    read = []
    algsed = {n: (H.MAX_HOID["D1"] if n == "MAX_HOID" else
                  H.TP_R["MOMENTUM"] if n == "TP_R" else
                  H.rsi.__defaults__[0] if n == "RSI_N" else
                  H.atr.__defaults__[0] if n == "ATR_N" else getattr(H, n))
              for n, _, _, _ in PARAM}
    for nimi, attr, base, tp in PARAM:
        for silt, kord in (("-10%", 0.9), ("baseline", 1.0), ("+10%", 1.1)):
            v = tp(round(base * kord)) if tp is int else tp(base * kord)
            if tp is int and v == base and silt != "baseline":
                v = base - 1 if kord < 1 else base + 1
            sea_param(nimi, v)
            # kontekst tuleb uuesti arvutada, kui EMA/ADX/ATR muutub
            Dx = {p: (d, H.kontekst(d, CTX)) for p, (d, _) in D.items()}
            T = tehingud(Dx)
            m = moodikud(T["neto_r"], aastaid(T))
            m.update(parameeter=nimi, variant=silt, vaartus=v,
                     baseline=base)
            read.append(m)
            sea_param(nimi, algsed[nimi])
    return pd.DataFrame(read)


# ------------------------------------------------- 7. WALK-FORWARD -------
def walk_forward(T, train_a=5, test_a=2, algus=2006, lopp=2026):
    """
    Parameetreid EI FITTITA (neid ei otsitudki). TRAIN-i kasutatakse
    OTSUSEKS: kaupelda jargmises TEST-aknas ainult neid paare, mille
    TRAIN-i ootus oli positiivne. TEST-i ei kasutata uhekski valikuks.
    """
    read = []
    y = algus
    while y + train_a + test_a - 1 <= lopp:
        ta, tb = f"{y}-01-01", f"{y+train_a-1}-12-31"
        sa, sb = f"{y+train_a}-01-01", f"{y+train_a+test_a-1}-12-31"
        tr = loik(T, ta, tb)
        te = loik(T, sa, sb)
        if len(tr) < MIN_N or len(te) < MIN_N:
            y += test_a
            continue
        valitud = [p for p, g in tr.groupby("paar") if g["neto_r"].mean() > 0]
        te_v = te[te["paar"].isin(valitud)]
        mtr = moodikud(tr["neto_r"], aastaid(tr))
        mte = moodikud(te["neto_r"], aastaid(te))
        mtv = moodikud(te_v["neto_r"], aastaid(te_v)) if len(te_v) else None
        read.append(dict(
            train=f"{y}-{y+train_a-1}", test=f"{y+train_a}-{y+train_a+test_a-1}",
            train_n=mtr["n"], train_ood=mtr["neto"],
            test_n=mte["n"], test_ood=mte["neto"], test_pf=mte["pf"],
            test_sharpe=mte["sharpe"], test_dd=mte["maxdd"],
            valitud_paare=len(valitud),
            test_valitud_n=(mtv["n"] if mtv else 0),
            test_valitud_ood=(mtv["neto"] if mtv else np.nan),
            test_valitud_pf=(mtv["pf"] if mtv else np.nan)))
        y += test_a
    return pd.DataFrame(read)


# -------------------------------------------------- 8. MONTE CARLO -------
def monte_carlo(T, katseid=10000, seeme=20260915):
    """
    KAKS MEETODIT, sest uksi jarjekorra permutatsioon EI SAA vastata
    kusimusele "P(lopptulemus < 0)":

    (a) JARJEKORRA PERMUTATSIOON (nagu kusitud). Fikseeritud
        protsendiriski juures on lopp-equity prod(1 + risk*R_i) ja
        KORRUTAMINE ON KOMMUTATIIVNE — lopptulemus on IGAS permutatsioonis
        TAPSELT SAMA. Varieerub ainult drawdown. See ei ole viga, vaid
        matemaatiline fakt, ja seetottu on "5%/1% lopptulemus" ja
        "P(<0)" selle meetodi puhul sisutud.
    (b) BOOTSTRAP TAGASIPANEKUGA: n tehingut tommatakse tagasipanekuga
        tegelikust jaotusest. See annab PARIS lopptulemuse jaotuse.
    """
    rs = np.random.RandomState(seeme)
    x = T["neto_r"].values
    n = len(x)
    read = {"perm_lopp_pct": np.empty(katseid), "perm_maxdd_pct": np.empty(katseid),
            "boot_lopp_pct": np.empty(katseid), "boot_maxdd_pct": np.empty(katseid)}
    for i in range(katseid):
        y = x[rs.permutation(n)]
        eq = np.cumprod(1 + H.RISK * y)
        read["perm_lopp_pct"][i] = 100.0 * (eq[-1] - 1)
        read["perm_maxdd_pct"][i] = 100.0 * float((eq / np.maximum.accumulate(eq) - 1).min())
        z = x[rs.randint(0, n, n)]
        eqb = np.cumprod(1 + H.RISK * z)
        read["boot_lopp_pct"][i] = 100.0 * (eqb[-1] - 1)
        read["boot_maxdd_pct"][i] = 100.0 * float((eqb / np.maximum.accumulate(eqb) - 1).min())
    return pd.DataFrame(read)


# =========================================================== MAIN =========
if __name__ == "__main__":
    kiire = "--kiire" in sys.argv
    print("=== ANDMED ===")
    D = andmed()
    T = tehingud(D)
    print(f"  paare {len(D)}, tehinguid 2006+ {len(T)}, "
          f"{T['aeg'].min().date()} .. {T['aeg'].max().date()}")
    m0 = moodikud(T["neto_r"], aastaid(T))
    print(f"  BASELINE: n={m0['n']}  bruto {T['bruto_r'].mean():+.4f}  "
          f"kulu {T['kulu_r'].mean():.4f}  neto {m0['neto']:+.4f} R  "
          f"t={m0['t']:.2f}  p={m0['p']:.3f}")

    print("\n=== 1. PERIOODID ===")
    P = periood_tabel(T)
    P.to_csv(os.path.join(JUUR, "D1_MOMENTUM_PERIOD_RESULTS.csv"), index=False)
    print(pais(20))
    for _, r in P.iterrows():
        print(rida(r["periood"], r.to_dict(), 20,
                   f"  bruto {r['bruto']:+.4f} kulu {r['kulu']:.4f} "
                   f"pos.paare {int(r['pos_paare'])}/{int(r['paare'])}"))

    print("\n=== 2. PAARID (ALL_2006_2026) ===")
    PR = paari_tabel(T)
    PR.to_csv(os.path.join(JUUR, "D1_MOMENTUM_PAIR_RESULTS.csv"), index=False)
    print(pais(20))
    a = PR[PR["periood"] == "ALL_2006_2026"].sort_values("neto", ascending=False)
    for _, r in a.iterrows():
        print(rida(r["paar"], r.to_dict(), 20,
                   f"  bruto {r['bruto']:+.4f}"))
    print(f"\n  positiivseid paare: {int((a['neto']>0).sum())}/{len(a)}   "
          f"mediaan {a['neto'].median():+.4f} R   "
          f"kui suur osa kogukasumist tuleb parimast paarist: ", end="")
    pk = a[a["neto"] > 0]
    tot = (a["neto"] * a["n"]).sum()
    print(f"{100*(a['neto'].iloc[0]*a['n'].iloc[0])/tot:.1f}%" if tot else "n/a")

    print("\n=== 2b. GRUPID ===")
    G = grupi_tabel(T)
    G.to_csv(os.path.join(JUUR, "D1_MOMENTUM_GROUP_RESULTS.csv"), index=False)
    print(pais(28))
    for g in GRUPID:
        for per in ("ALL_2006_2026", "OOS_2018_2026"):
            r = G[(G["grupp"] == g) & (G["periood"] == per)]
            if len(r):
                print(rida(f"{g} {per}", r.iloc[0].to_dict(), 28))

    print("\n=== 3. REZHIIMID ===")
    RZ = rezhiimi_tabel(T)
    RZ.to_csv(os.path.join(JUUR, "D1_MOMENTUM_REGIME_RESULTS.csv"), index=False)
    print(pais(28))
    for _, r in RZ[RZ["tase"].str.startswith("KOIK")].iterrows():
        print(rida(f"{r['rezhiim']} [{r['tase'][12:] or 'ALL'}]",
                   r.to_dict(), 28))

    print("\n=== 4. JUHUSLIK SISENEMINE (aus null) ===")
    katseid = 100 if kiire else 1000
    B = juhuslik_benchmark(D, T, katseid=katseid)
    B.to_csv(os.path.join(JUUR, "D1_MOMENTUM_RANDOM_BENCHMARK.csv"), index=False)
    teg = m0["neto"]
    pct = 100.0 * float((B["neto_per_teh"] < teg).mean())
    print(f"  katseid {len(B)}, keskm tehinguid katses {B['n'].mean():.0f}")
    print(f"  juhuslik: keskmine {B['neto_per_teh'].mean():+.4f} R, "
          f"sd {B['neto_per_teh'].std(ddof=1):.4f}")
    print(f"  juhuslik 95% kvantiil {B['neto_per_teh'].quantile(0.95):+.4f} R, "
          f"max {B['neto_per_teh'].max():+.4f} R")
    print(f"  TEGELIK MOMENTUM {teg:+.4f} R  =>  protsentiil {pct:.1f}, "
          f"empiiriline p = {1 - pct/100:.4f}")

    print("\n=== 5. KULUSTRESS ===")
    K = kulustress(D)
    K.to_csv(os.path.join(JUUR, "D1_MOMENTUM_COST_STRESS.csv"), index=False)
    print(f"{'variant':<26s}{'lõige':<16s}{'n':>6s}{'kulu_R':>9s}"
          f"{'neto_R':>9s}{'PF':>7s}{'t':>7s}")
    for _, r in K.iterrows():
        print(f"{r['variant']:<26s}{r['lõige']:<16s}{int(r['n']):>6d}"
              f"{r['kulu']:>9.4f}{r['neto']:>+9.4f}{r['pf']:>7.2f}{r['t']:>7.2f}")

    print("\n=== 6. PARAMEETRI PERTURBATSIOON ===")
    PP = parameetri_robustsus(D)
    PP.to_csv(os.path.join(JUUR, "D1_MOMENTUM_PARAMETER_ROBUSTNESS.csv"),
              index=False)
    print(f"{'parameeter':<14s}{'variant':<11s}{'vaartus':>9s}{'n':>7s}"
          f"{'neto_R':>10s}{'PF':>7s}{'t':>7s}")
    for _, r in PP.iterrows():
        print(f"{r['parameeter']:<14s}{r['variant']:<11s}{r['vaartus']:>9.2f}"
              f"{int(r['n']):>7d}{r['neto']:>+10.4f}{r['pf']:>7.2f}{r['t']:>7.2f}")

    print("\n=== 7. WALK-FORWARD (TRAIN 5a / TEST 2a, samm 2a) ===")
    W = walk_forward(T)
    W.to_csv(os.path.join(JUUR, "D1_MOMENTUM_WALK_FORWARD.csv"), index=False)
    print(f"{'train':<11s}{'test':<11s}{'tr_n':>6s}{'tr_ood':>9s}"
          f"{'te_n':>6s}{'te_ood':>9s}{'te_PF':>7s}{'te_Shrp':>9s}"
          f"{'te_DD%':>8s}{'val.paare':>10s}{'val_ood':>9s}")
    for _, r in W.iterrows():
        print(f"{r['train']:<11s}{r['test']:<11s}{int(r['train_n']):>6d}"
              f"{r['train_ood']:>+9.4f}{int(r['test_n']):>6d}"
              f"{r['test_ood']:>+9.4f}{r['test_pf']:>7.2f}"
              f"{r['test_sharpe']:>9.2f}{r['test_dd']:>8.1f}"
              f"{int(r['valitud_paare']):>10d}{r['test_valitud_ood']:>+9.4f}")
    pos_te = int((W["test_ood"] > 0).sum())
    pos_val = int((W["test_valitud_ood"] > 0).sum())
    print(f"\n  TEST-aknaid positiivseid: {pos_te}/{len(W)} (filtrita), "
          f"{pos_val}/{len(W)} (TRAIN-i valikuga)")
    print(f"  korr(train_ood, test_ood) = "
          f"{W['train_ood'].corr(W['test_ood']):+.3f}")

    print("\n=== 8. MONTE CARLO ===")
    mc_n = 1000 if kiire else 10000
    MC = monte_carlo(T, katseid=mc_n)
    MC.to_csv(os.path.join(JUUR, "D1_MOMENTUM_MONTE_CARLO.csv"), index=False)
    print(f"  simulatsioone {len(MC)}, risk {100*H.RISK:.0f}% tehingu kohta, "
          f"{m0['n']} tehingut, {aastaid(T):.1f} aastat")
    for eesliide, silt in (("perm", "(a) JARJEKORRA PERMUTATSIOON"),
                           ("boot", "(b) BOOTSTRAP TAGASIPANEKUGA")):
        L = MC[f"{eesliide}_lopp_pct"]
        DD = MC[f"{eesliide}_maxdd_pct"]
        print(f"  {silt}")
        print(f"     lopptulemus  mediaan {L.median():+.1f}%   "
              f"5% {L.quantile(0.05):+.1f}%   1% {L.quantile(0.01):+.1f}%")
        print(f"     maxDD        mediaan {DD.median():.1f}%   "
              f"95% kvantiil {DD.quantile(0.05):.1f}%")
        print(f"     P(lopptulemus < 0)  = {100*float((L<0).mean()):.1f}%")
        print(f"     P(maxDD > 20%)      = {100*float((DD<-20).mean()):.1f}%")
        if eesliide == "perm":
            print(f"     NB: lopptulemuse hajuvus on {L.std(ddof=1):.2e} — "
                  f"korrutamine on kommutatiivne, seega lopptulemus on "
                  f"permutatsiooni suhtes MUUTUMATU. Ainult DD varieerub.")

    print("\n=== 9. MITME TESTIMISE ARVESTUS ===")
    kk = PR[PR["piisav"]]
    pv = list(kk["p"].values)
    lavi, labi = H.bh(pv, 0.05)
    pos_sig = sum(1 for i in labi if kk.iloc[i]["neto"] > 0)
    print(f"  paare {len(H.PAARID)} x perioode {len(PERIOODID)} = "
          f"{len(H.PAARID)*len(PERIOODID)} paar-perioodi lahtrit")
    print(f"  neist n >= {MIN_N}: {len(kk)}")
    print(f"  rezhiime 4, gruppe {len(GRUPID)}, kulustressi variante "
          f"{K['variant'].nunique()}, parameetriteste {len(PP)}, "
          f"walk-forward aknaid {len(W)}")
    print(f"  BH q=0.05 ule {len(kk)} paar-perioodi: labis {len(labi)}, "
          f"NEIST POSITIIVSEID {pos_sig}")
    print(f"  parim positiivne toores p: "
          f"{kk[kk['neto']>0]['p'].min() if (kk['neto']>0).any() else float('nan'):.4f}")
    print(f"  Bonferroni lavi: {0.05/max(len(kk),1):.5f}")

    print("\nfailid kirjutatud:")
    for f in ("D1_MOMENTUM_PERIOD_RESULTS.csv", "D1_MOMENTUM_PAIR_RESULTS.csv",
              "D1_MOMENTUM_GROUP_RESULTS.csv", "D1_MOMENTUM_REGIME_RESULTS.csv",
              "D1_MOMENTUM_RANDOM_BENCHMARK.csv", "D1_MOMENTUM_COST_STRESS.csv",
              "D1_MOMENTUM_PARAMETER_ROBUSTNESS.csv",
              "D1_MOMENTUM_WALK_FORWARD.csv", "D1_MOMENTUM_MONTE_CARLO.csv"):
        p = os.path.join(JUUR, f)
        print(f"  {f}  {os.path.getsize(p)/1024:.0f} KB")
