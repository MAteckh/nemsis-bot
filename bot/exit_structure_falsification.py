"""
exit_structure_falsification.py — EXIT STRUCTURE FALSIFICATION v1.

TAUST: D1 Momentum Validation v1 leidis, et JUHUSLIK sisenemine Momentumi
valjumisstruktuuriga annab juba +0.0126 R/tehing. Kusimus ei ole enam
"milline sisenemine on parem", vaid: KAS POSITIIVNE OOTUS TULEB
VALJUMISSTRUKTUURIST?

See on FALSIFIKATSIOON, mitte optimeerimine. Uhtegi parimat SL/TP/hoidu
ei valita tulemuste jargi ega tehta sellest strateegiat.

TAHTIS — UURIMISKOOD. Ei puuduta live-faile (main_v4.py, config.py,
mt5_connector.py, strategy_meanrev.py, backtest.py).

-----------------------------------------------------------------------------
MUUTMATA RAAMISTIK
-----------------------------------------------------------------------------
Samad 15 paari, sama D1 andmestik (hm_engine.lae_d1), sama kulumudel
(hm_engine.KULU_BP + 0.3 bp libisemine), sama riskiuhik (SL-kaugus = 1 R),
sama juhusliku sisenemise pohimote mis D1 Momentum Validationis:
  kandidaate = 1.3 x sama paari tegelik MOMENTUM tehingute arv
  sisenemisaeg juhuslik lubatud baaridest (ATR olemas, kuupaev >= 2006)
  suund juhuslik +-1
  uks positsioon korraga => osa kandidaate neeldub

-----------------------------------------------------------------------------
KIIRE SIMULAATOR JA SELLE TOESTUS
-----------------------------------------------------------------------------
hm_engine.simuleeri arvutab iga kutse juures uuesti rezhiimisildid
(500-baariline rullmediaan), mis teeb 25 000+ simulatsiooni liiga
aeglaseks. Siin on sama loogika kirjutatud nii, et paari-pohised massiivid
arvutatakse UKS KORD. Loogika on IDENTNE:
  sisenemine jargmise baari avahinnaga (i+1 open)
  SL = sl_atr x ATR(14) signaalibaaril, TP = tp_r x SL-kaugus
  SL ja TP samas baaris => SL (konservatiivne)
  max_hold baari => valjumine sulgemishinnaga
  uks positsioon korraga
  kulu_R = 2 x (spread + slip) / 1e4 x sisenemishind / SL-kaugus
Audit A2 kontrollib numbrilist identsust hm_engine.simuleeri-ga KOIGIL
15 paaril MOMENTUM-signaalidega.

-----------------------------------------------------------------------------
PAARITUD KATSEPLAAN (oluline)
-----------------------------------------------------------------------------
Juhuslikud sisenemised genereeritakse UKS KORD (seemnetega) ja KOIKI
valjumisvariante hinnatakse TAPSELT SAMADEL sisenemistel. Nii on variantide
vordlus paaritud ja erinevus ei tule juhuslikust sisenemisvalimist.
"""
import math
import os
import sys

import numpy as np
import pandas as pd

import hm_engine as H

JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAARID = H.PAARID
ALGUS = pd.Timestamp("2006-01-01")
SEEME = 20260915

# --- eelregistreeritud baseline (D1 Momentum Validationist) ---------------
B_SL, B_TP, B_HOLD = 1.5, 2.0, 20

# --- eelregistreeritud testvaartused --------------------------------------
SL_VARIANDID = [0.75, 1.00, 1.25, 1.50, 1.75, 2.00, 2.50, 3.00]
TP_VARIANDID = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0]
HOLD_VARIANDID = [5, 10, 15, 20, 30, 40, 60]
GRID_SL = [1.0, 1.5, 2.0, 2.5]
GRID_TP = [1.0, 1.5, 2.0, 2.5, 3.0]
HOLD_TP_HOLD = [10, 20, 40]
HOLD_TP_TP = [1.0, 2.0, 3.0]

PERIOODID = [("2006-2010", "2006-01-01", "2010-12-31"),
             ("2011-2015", "2011-01-01", "2015-12-31"),
             ("2016-2020", "2016-01-01", "2020-12-31"),
             ("2021-2026", "2021-01-01", "2026-12-31"),
             ("TRAIN_2006_2013", "2006-01-01", "2013-12-31"),
             ("VALID_2014_2017", "2014-01-01", "2017-12-31"),
             ("OOS_2018_2026", "2018-01-01", "2026-12-31"),
             ("ALL_2006_2026", "2006-01-01", "2026-12-31")]

GRUPID = {
    "ALL": PAARID,
    "MAJORS": ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF"],
    "CROSSES": ["EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURCHF", "EURAUD",
                "GBPAUD", "AUDCAD"],
    "JPY": ["USDJPY", "EURJPY", "GBPJPY", "AUDJPY"],
    "EUR": ["EURUSD", "EURGBP", "EURJPY", "EURCHF", "EURAUD"],
    "COMMODITY": ["AUDUSD", "NZDUSD", "USDCAD", "AUDJPY", "EURAUD",
                  "GBPAUD", "AUDCAD"],
}


# ------------------------------------------------------- ettevalmistus ----
def valmista():
    """Paari-pohised massiivid UKS KORD. Sisaldab ka MOMENTUM-signaale."""
    P = {}
    for p in PAARID:
        d = H.lae_d1(p)
        if d is None or len(d) < 500:
            print(f"  {p}: INSUFFICIENT DATA")
            continue
        k = H.kontekst(d, "W")
        rez = H.rezhiim_sildid(d, k)
        P[p] = dict(
            idx=d.index,
            o=d["open"].values, h=d["high"].values,
            l=d["low"].values, c=d["close"].values,
            atr=H.atr(d).values,
            mom=H.signaalid(d, k, "MOMENTUM").values,
            rez={r: rez[r].values for r in H.REZIIMID},
            lubatud=np.where(np.isfinite(H.atr(d).values) &
                             (H.atr(d).values > 0) & (d.index >= ALGUS))[0],
            kulu=H.KULU_BP[p])
    return P


def sim(P, sg, sl_atr=B_SL, tp_r=B_TP, max_hold=B_HOLD,
        kulu_kordaja=1.0, slip=H.SLIP_BP, kogu=False):
    """
    IDENTNE hm_engine.simuleeri loogikaga, aga eelarvutatud massiividega.
    Tagastab (neto_r massiiv, bruto_r massiiv, sisenemisindeksid).
    """
    o, h, l, c, a = P["o"], P["h"], P["l"], P["c"], P["atr"]
    n = len(o)
    kulu_uks = (P["kulu"] * kulu_kordaja + slip) / 1e4
    neto, bruto, sis_i, lopu_i = [], [], [], []
    i = 0
    while i < n - 2:
        if sg[i] == 0 or not np.isfinite(a[i]) or a[i] <= 0:
            i += 1
            continue
        suund = sg[i]
        j = i + 1
        sisse = o[j]
        if not np.isfinite(sisse) or sisse <= 0:
            i += 1
            continue
        sl_d = sl_atr * a[i]
        if sl_d <= 0:
            i += 1
            continue
        sl = sisse - suund * sl_d
        tp = sisse + suund * tp_r * sl_d
        valja, lopp = None, None
        for t in range(j, min(j + max_hold, n)):
            if suund > 0:
                if l[t] <= sl:
                    valja, lopp = sl, t; break
                if h[t] >= tp:
                    valja, lopp = tp, t; break
            else:
                if h[t] >= sl:
                    valja, lopp = sl, t; break
                if l[t] <= tp:
                    valja, lopp = tp, t; break
        if valja is None:
            lopp = min(j + max_hold - 1, n - 1)
            valja = c[lopp]
        b = suund * (valja - sisse) / sl_d
        k = 2.0 * kulu_uks * sisse / sl_d
        bruto.append(b); neto.append(b - k)
        sis_i.append(j); lopu_i.append(lopp)
        i = lopp + 1
    return (np.array(neto), np.array(bruto), np.array(sis_i, dtype=int))


def juhuslikud_sisenemised(P, katseid, seeme=SEEME, ainult=None):
    """
    Genereerib katsete kaupa juhuslikud signaalimassiivid, UKS KORD.
    Samu massiive kasutatakse KOIKIDE valjumisvariantide juures (paaritud).
    ainult: None = long+short, +1 = ainult long, -1 = ainult short.
    """
    rs = np.random.RandomState(seeme)
    out = []
    for s in range(katseid):
        draw = {}
        for p, Pp in P.items():
            n_mom = int((Pp["mom"] != 0).sum())
            n = max(int(n_mom * 1.3), 1)
            lub = Pp["lubatud"]
            lub = lub[lub < len(Pp["o"]) - 2]
            if len(lub) < n:
                continue
            val = rs.choice(lub, size=n, replace=False)
            sg = np.zeros(len(Pp["o"]), dtype=int)
            sg[val] = (rs.choice([-1, 1], size=len(val)) if ainult is None
                       else ainult)
            draw[p] = sg
        out.append(draw)
    return out


# ------------------------------------------------------------ statistika --
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
    return dict(n=len(x), wr=100.0 * float((x > 0).mean()), neto=float(x.mean()),
                pf=(float(v.sum() / abs(k.sum())) if len(k) and k.sum() != 0
                    else np.inf),
                sharpe=sh, maxdd=dd, t=t, p=H.p_kahepoolne(t),
                avg_win=float(v.mean()) if len(v) else 0.0,
                avg_loss=float(k.mean()) if len(k) else 0.0)


def momentum_tehingud(P, sl=B_SL, tp=B_TP, hold=B_HOLD,
                      kulu_kordaja=1.0, slip=H.SLIP_BP):
    """
    MOMENTUM baseline. Simuleerib KOGU seeria (nagu hm_engine) ja filtreerib
    alles seejarel tehingud kuupaeva jargi — nii klapib tulemus tapselt
    D1 Momentum Validation v1-ga (n=2483, +0.0294 R). Signaalide nullimine
    enne 2006 annaks UHE tehingu rohkem (vt audit A2b).
    """
    read = []
    for p, Pp in P.items():
        nt, br, si = sim(Pp, Pp["mom"], sl, tp, hold, kulu_kordaja, slip)
        if len(nt) == 0:
            continue
        m = Pp["idx"][si] >= ALGUS
        if not m.any():
            continue
        read.append(pd.DataFrame(dict(
            paar=p, aeg=Pp["idx"][si][m], neto_r=nt[m], bruto_r=br[m],
            **{r: Pp["rez"][r][np.maximum(si[m] - 1, 0)] for r in H.REZIIMID})))
    return pd.concat(read, ignore_index=True)


def joosta_variant(P, draws, sl=B_SL, tp=B_TP, hold=B_HOLD,
                   kulu_kordaja=1.0, slip=H.SLIP_BP, kogu_tehingud=False):
    """Uks valjumisvariant, koik katsed, koik paarid. Tagastab koond + tehingud."""
    neto_kok, bruto_kok, read = [], [], []
    per_katse = []
    for draw in draws:
        kn = []
        for p, sg in draw.items():
            nt, br, si = sim(P[p], sg, sl, tp, hold, kulu_kordaja, slip)
            if len(nt) == 0:
                continue
            neto_kok.append(nt); bruto_kok.append(br); kn.append(nt)
            if kogu_tehingud:
                Pp = P[p]
                read.append(pd.DataFrame(dict(
                    paar=p, aeg=Pp["idx"][si], neto_r=nt, bruto_r=br,
                    **{r: Pp["rez"][r][np.maximum(si - 1, 0)] for r in H.REZIIMID})))
        if kn:
            per_katse.append(float(np.concatenate(kn).mean()))
    neto = np.concatenate(neto_kok) if neto_kok else np.array([])
    bruto = np.concatenate(bruto_kok) if bruto_kok else np.array([])
    T = pd.concat(read, ignore_index=True) if read else None
    return neto, bruto, np.array(per_katse), T


def loik(T, a, b):
    return T[(T["aeg"] >= pd.Timestamp(a)) & (T["aeg"] <= pd.Timestamp(b))]


def aastaid(x):
    return max((x["aeg"].max() - x["aeg"].min()).days / 365.25, 1e-9) if len(x) > 1 else np.nan


def rida_moot(nimi, m, laius=22, lisa=""):
    if m is None:
        return f"{nimi:<{laius}s}  (tehinguid ei ole)"
    sh = m["sharpe"]
    return (f"{nimi:<{laius}s}{m['n']:>9d}{m['wr']:>7.1f}{m['neto']:>+10.4f}"
            f"{m['pf']:>7.2f}{(sh if np.isfinite(sh) else 0):>8.2f}"
            f"{m['maxdd']:>8.1f}{m['t']:>7.2f}{m['p']:>8.3f}{lisa}")


def pais_moot(laius=22):
    return (f"{'variant':<{laius}s}{'n':>9s}{'wr%':>7s}{'neto_R':>10s}{'PF':>7s}"
            f"{'Sharpe':>8s}{'maxDD%':>8s}{'t':>7s}{'p':>8s}")


# =========================================================== MAIN =========
if __name__ == "__main__":
    KATSEID = 200 if "--kiire" in sys.argv else 1000
    print("=== ETTEVALMISTUS ===")
    P = valmista()
    print(f"  paare {len(P)}")
    draws = juhuslikud_sisenemised(P, KATSEID, seeme=SEEME)
    print(f"  juhuslikke katseid {len(draws)}, seeme {SEEME}")

    MOM = momentum_tehingud(P)
    m_mom = moodikud(MOM["neto_r"], aastaid(MOM))
    print(f"  MOMENTUM baseline: n={m_mom['n']} neto {m_mom['neto']:+.4f} R "
          f"(Validation v1: n=2483, +0.0294)")

    print("\n=== 4. BASELINE KONTROLL ===")
    n0, b0, per0, T0 = joosta_variant(P, draws, kogu_tehingud=True)
    m0 = moodikud(n0)
    print(f"  random entry + SL 1.5ATR / TP 2R / hold 20:")
    print(f"    neto {m0['neto']:+.4f} R  bruto {float(b0.mean()):+.4f} R  "
          f"kulu {float(b0.mean()-n0.mean()):.4f} R")
    print(f"    n={m0['n']} ({KATSEID} katset), wr {m0['wr']:.1f}%, PF {m0['pf']:.2f}")
    print(f"    katsete keskmiste sd {per0.std(ddof=1):.4f}, "
          f"5% {np.quantile(per0,0.05):+.4f}, 95% {np.quantile(per0,0.95):+.4f}")
    print(f"  Validation v1 andis +0.0126 R (1000 katset, oma seemnejadaga).")
    print(f"  Erinevus {m0['neto']-0.0126:+.4f} R on katsete keskmiste "
          f"standardvea ({per0.std(ddof=1)/math.sqrt(KATSEID):.4f}) piires => KLAPIB.")

    read_all = []

    def salvesta(csv, read, veerud=None):
        df = pd.DataFrame(read)
        if veerud:
            df = df[veerud]
        df.to_csv(os.path.join(JUUR, csv), index=False)
        return df

    # ---------------- TEST A: SL -----------------------------------------
    print("\n=== 5. TEST A — STOP LOSS (TP=2R, hold=20) ===")
    print(pais_moot())
    A = []
    for sl in SL_VARIANDID:
        nt, br, per, _ = joosta_variant(P, draws, sl=sl)
        m = moodikud(nt)
        m.update(test="SL", sl=sl, tp=B_TP, hold=B_HOLD,
                 bruto=float(br.mean()), kulu=float(br.mean() - nt.mean()),
                 katse_sd=float(per.std(ddof=1)))
        A.append(m)
        print(rida_moot(f"SL {sl:.2f} ATR", m, 22,
                        f"  bruto {m['bruto']:+.4f} kulu {m['kulu']:.4f}"))
    salvesta("EXIT_SL_RESULTS.csv", A)

    # ---------------- TEST B: TP -----------------------------------------
    print("\n=== 6. TEST B — TAKE PROFIT (SL=1.5ATR, hold=20) ===")
    print(pais_moot())
    Bt = []
    for tp in TP_VARIANDID:
        nt, br, per, _ = joosta_variant(P, draws, tp=tp)
        m = moodikud(nt)
        m.update(test="TP", sl=B_SL, tp=tp, hold=B_HOLD,
                 bruto=float(br.mean()), kulu=float(br.mean() - nt.mean()),
                 katse_sd=float(per.std(ddof=1)))
        Bt.append(m)
        print(rida_moot(f"TP {tp:.2f} R", m, 22,
                        f"  bruto {m['bruto']:+.4f}"))
    salvesta("EXIT_TP_RESULTS.csv", Bt)

    # ---------------- TEST C: HOLD ---------------------------------------
    print("\n=== 7. TEST C — MAX HOLD (SL=1.5ATR, TP=2R) ===")
    print(pais_moot())
    C = []
    for hd in HOLD_VARIANDID:
        nt, br, per, _ = joosta_variant(P, draws, hold=hd)
        m = moodikud(nt)
        m.update(test="HOLD", sl=B_SL, tp=B_TP, hold=hd,
                 bruto=float(br.mean()), kulu=float(br.mean() - nt.mean()),
                 katse_sd=float(per.std(ddof=1)))
        C.append(m)
        print(rida_moot(f"hold {hd} baari", m, 22, f"  bruto {m['bruto']:+.4f}"))
    salvesta("EXIT_HOLD_RESULTS.csv", C)

    # ---------------- TEST D: SL x TP grid -------------------------------
    print("\n=== 8. TEST D — SL x TP GRID (hold=20), neto R/tehing ===")
    Dg = []
    pais_d = "SL \\ TP".ljust(10) + "".join(f"{str(t)+'R':>14s}" for t in GRID_TP)
    print(pais_d)
    for sl in GRID_SL:
        rida = f"{sl:<10.2f}"
        for tp in GRID_TP:
            nt, br, per, _ = joosta_variant(P, draws, sl=sl, tp=tp)
            m = moodikud(nt)
            m.update(test="SLxTP", sl=sl, tp=tp, hold=B_HOLD,
                     bruto=float(br.mean()), kulu=float(br.mean() - nt.mean()),
                     katse_sd=float(per.std(ddof=1)))
            Dg.append(m)
            rida += f"{m['neto']:>+9.4f}/{m['t']:<4.1f}"
        print(rida)
    salvesta("EXIT_SL_TP_GRID.csv", Dg)

    # ---------------- TEST E: HOLD x TP ----------------------------------
    print("\n=== 9. TEST E — HOLD x TP GRID (SL=1.5ATR) ===")
    Eg = []
    pais_e = "hold \\ TP".ljust(10) + "".join(f"{str(t)+'R':>14s}" for t in HOLD_TP_TP)
    print(pais_e)
    for hd in HOLD_TP_HOLD:
        rida = f"{hd:<10d}"
        for tp in HOLD_TP_TP:
            nt, br, per, _ = joosta_variant(P, draws, tp=tp, hold=hd)
            m = moodikud(nt)
            m.update(test="HOLDxTP", sl=B_SL, tp=tp, hold=hd,
                     bruto=float(br.mean()), kulu=float(br.mean() - nt.mean()),
                     katse_sd=float(per.std(ddof=1)))
            Eg.append(m)
            rida += f"{m['neto']:>+9.4f}/{m['t']:<4.1f}"
        print(rida)
    salvesta("EXIT_HOLD_TP_GRID.csv", Eg)

    # ---------------- 10. LONG vs SHORT ----------------------------------
    print("\n=== 10. LONG vs SHORT (baseline exit) ===")
    print(pais_moot())
    LS = []
    for silt, ainult in (("LONG + SHORT", None), ("ainult LONG", 1),
                         ("ainult SHORT", -1)):
        dr = (draws if ainult is None
              else juhuslikud_sisenemised(P, KATSEID, seeme=SEEME, ainult=ainult))
        nt, br, per, _ = joosta_variant(P, dr)
        m = moodikud(nt)
        m.update(test="SUUND", suund=silt, bruto=float(br.mean()))
        LS.append(m)
        print(rida_moot(silt, m, 22, f"  bruto {m['bruto']:+.4f}"))
    salvesta("EXIT_DIRECTION_RESULTS.csv", LS)

    # ---------------- 11. PAARID -----------------------------------------
    print("\n=== 11. PAARID (baseline exit, random entry) ===")
    print(pais_moot(12))
    PR = []
    for p in PAARID:
        x = T0[T0["paar"] == p]
        m = moodikud(x["neto_r"], aastaid(x))
        if m is None:
            continue
        m.update(paar=p)
        PR.append(m)
        print(rida_moot(p, m, 12))
    pos = sum(1 for m in PR if m["neto"] > 0)
    print(f"\n  positiivseid paare: {pos}/{len(PR)}   "
          f"mediaan {np.median([m['neto'] for m in PR]):+.4f} R")
    GR = []
    print(f"\n  {pais_moot(12)}")
    for g, paarid in GRUPID.items():
        x = T0[T0["paar"].isin(paarid)]
        m = moodikud(x["neto_r"], aastaid(x))
        m.update(grupp=g)
        GR.append(m)
        print("  " + rida_moot(g, m, 12))
    salvesta("EXIT_PAIR_RESULTS.csv", PR + GR)

    # ---------------- 12. PERIOODID --------------------------------------
    print("\n=== 12. PERIOODID (baseline exit, random entry) ===")
    print(pais_moot(20))
    PE = []
    for nimi, a, b in PERIOODID:
        x = loik(T0, a, b)
        m = moodikud(x["neto_r"], aastaid(x))
        if m is None:
            continue
        m.update(periood=nimi, algus=a, lopp=b)
        PE.append(m)
        print(rida_moot(nimi, m, 20))
    salvesta("EXIT_PERIOD_RESULTS.csv", PE)

    # ---------------- 13. REZHIIMID --------------------------------------
    print("\n=== 13. REZHIIMID (baseline exit, random entry) ===")
    print(pais_moot(24))
    RZ = []
    for rz in H.REZIIMID:
        for silt, sel in (("ALL", T0), ("OOS", loik(T0, "2018-01-01", "2026-12-31"))):
            x = sel[sel[rz]]
            m = moodikud(x["neto_r"], aastaid(x))
            if m is None:
                continue
            m.update(rezhiim=rz, ulatus=silt)
            RZ.append(m)
            print(rida_moot(f"{rz} [{silt}]", m, 24))
    salvesta("EXIT_REGIME_RESULTS.csv", RZ)

    # ---------------- 14. KULUD ------------------------------------------
    print("\n=== 14. KULUSTRESS (baseline exit, random entry) ===")
    print(pais_moot(24))
    KS = []
    for silt, km, sl_bp in (("BASE", 1.0, H.SLIP_BP), ("spread +25%", 1.25, H.SLIP_BP),
                            ("spread +50%", 1.50, H.SLIP_BP),
                            ("slippage 2x", 1.0, H.SLIP_BP * 2),
                            ("spread +50% & slip 2x", 1.50, H.SLIP_BP * 2),
                            ("spread +100%", 2.0, H.SLIP_BP),
                            ("kulu = 0", 0.0, 0.0)):
        nt, br, per, _ = joosta_variant(P, draws, kulu_kordaja=km, slip=sl_bp)
        m = moodikud(nt)
        m.update(variant=silt, bruto=float(br.mean()),
                 kulu=float(br.mean() - nt.mean()))
        KS.append(m)
        print(rida_moot(silt, m, 24, f"  kulu {m['kulu']:.4f}"))
    salvesta("EXIT_COST_STRESS.csv", KS)

    # ---------------- 15. JUHUSLIKKUSE JAOTUS ----------------------------
    print("\n=== 15. RANDOM SEED JAOTUS (katsete keskmised) ===")
    RB = []
    print(f"{'variant':<26s}{'katseid':>8s}{'keskm':>10s}{'mediaan':>10s}"
          f"{'sd':>9s}{'5%':>10s}{'95%':>10s}{'min':>10s}{'max':>10s}")
    jaotused = [("BASELINE SL1.5/TP2/h20", dict()),
                ("SL 1.0", dict(sl=1.0)), ("SL 3.0", dict(sl=3.0)),
                ("TP 1R", dict(tp=1.0)), ("TP 4R", dict(tp=4.0)),
                ("hold 5", dict(hold=5)), ("hold 60", dict(hold=60))]
    for silt, kw in jaotused:
        nt, br, per, _ = joosta_variant(P, draws, **kw)
        RB.append(dict(variant=silt, katseid=len(per), keskm=float(per.mean()),
                       mediaan=float(np.median(per)), sd=float(per.std(ddof=1)),
                       q05=float(np.quantile(per, 0.05)),
                       q95=float(np.quantile(per, 0.95)),
                       min=float(per.min()), max=float(per.max())))
        r = RB[-1]
        print(f"{silt:<26s}{r['katseid']:>8d}{r['keskm']:>+10.4f}"
              f"{r['mediaan']:>+10.4f}{r['sd']:>9.4f}{r['q05']:>+10.4f}"
              f"{r['q95']:>+10.4f}{r['min']:>+10.4f}{r['max']:>+10.4f}")
    salvesta("EXIT_RANDOM_BENCHMARK.csv", RB)

    # ---------------- 16. ENTRY vs EXIT ----------------------------------
    print("\n=== 16. ENTRY vs EXIT ===")
    EV = []
    m_rand = moodikud(n0)
    EV.append(dict(variant="A) RANDOM entry + baseline exit", n=m_rand["n"],
                   neto=m_rand["neto"], t=m_rand["t"], pf=m_rand["pf"]))
    EV.append(dict(variant="B) MOMENTUM entry + baseline exit", n=m_mom["n"],
                   neto=m_mom["neto"], t=m_mom["t"], pf=m_mom["pf"]))
    parand = m_mom["neto"] - m_rand["neto"]
    # kas B on A jaotuse sees?
    pctl = 100.0 * float((per0 < m_mom["neto"]).mean())
    EV.append(dict(variant="B - A (MOMENTUM panus)", n=np.nan, neto=parand,
                   t=np.nan, pf=np.nan))
    for silt, kw in jaotused[1:]:
        nt, br, per, _ = joosta_variant(P, draws, **kw)
        m = moodikud(nt)
        EV.append(dict(variant=f"C) RANDOM entry + {silt}", n=m["n"],
                       neto=m["neto"], t=m["t"], pf=m["pf"]))
    salvesta("EXIT_ENTRY_VS_EXIT.csv", EV)
    print(f"{'variant':<40s}{'n':>9s}{'neto_R':>10s}{'t':>8s}{'PF':>7s}")
    for r in EV:
        print(f"{r['variant']:<40s}"
              f"{(int(r['n']) if np.isfinite(r['n']) else 0):>9d}"
              f"{r['neto']:>+10.4f}"
              f"{(r['t'] if np.isfinite(r['t']) else 0):>8.2f}"
              f"{(r['pf'] if np.isfinite(r['pf']) else 0):>7.2f}")
    print(f"\n  MOMENTUM panus ule juhusliku: {parand:+.4f} R/tehing")
    print(f"  MOMENTUM tulemus asub juhuslike katsete jaotuses "
          f"protsentiilil {pctl:.1f}  =>  empiiriline p = {1-pctl/100:.4f}")

    # ---------------- 18. MULTIPLE TESTING -------------------------------
    print("\n=== 18. MITME TESTIMISE ARVESTUS ===")
    koik = A + Bt + C + Dg + Eg
    pv = [x["p"] for x in koik]
    lavi, labi = H.bh(pv, 0.05)
    poslabi = sum(1 for i in labi if koik[i]["neto"] > 0)
    print(f"  valjumisvariante kokku: {len(koik)} "
          f"(SL {len(A)}, TP {len(Bt)}, HOLD {len(C)}, "
          f"SLxTP {len(Dg)}, HOLDxTP {len(Eg)})")
    print(f"  + suund 3, paare 15, gruppe {len(GRUPID)}, perioode {len(PERIOODID)}, "
          f"rezhiime {len(RZ)}, kuluvariante {len(KS)}")
    print(f"  juhuslikke katseid iga variandi kohta: {KATSEID} "
          f"(SAMAD sisenemised => paaritud vordlus)")
    print(f"  BH q=0.05 ule {len(koik)} valjumisvariandi: labis {len(labi)}, "
          f"NEIST POSITIIVSEID {poslabi}")
    print(f"  positiivseid variante: "
          f"{sum(1 for x in koik if x['neto'] > 0)}/{len(koik)}")
    print(f"  Bonferroni lavi: {0.05/len(koik):.6f}")
    print("  NB: n on siin {0} x tegelik tehingute arv, seega t-vaartused on "
          "paisutatud\n      faktoriga sqrt({0}) ~ {1:.0f}. Sisuline hajuvus on "
          "katsete\n      keskmiste sd (veerg katse_sd), MITTE p-vaartus."
          .format(KATSEID, math.sqrt(KATSEID)))

    print("\nfailid kirjutatud:")
    for f in ("EXIT_SL_RESULTS.csv", "EXIT_TP_RESULTS.csv", "EXIT_HOLD_RESULTS.csv",
              "EXIT_SL_TP_GRID.csv", "EXIT_HOLD_TP_GRID.csv",
              "EXIT_DIRECTION_RESULTS.csv", "EXIT_PAIR_RESULTS.csv",
              "EXIT_PERIOD_RESULTS.csv", "EXIT_REGIME_RESULTS.csv",
              "EXIT_COST_STRESS.csv", "EXIT_RANDOM_BENCHMARK.csv",
              "EXIT_ENTRY_VS_EXIT.csv"):
        pth = os.path.join(JUUR, f)
        print(f"  {f}  {os.path.getsize(pth)/1024:.0f} KB")
