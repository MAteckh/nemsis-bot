"""
sub60_tick_audit.py — mootori kontroll ENNE tulemuste vaatamist.

Iga kontroll on kas PASS voi FAIL. Tulemusi ei tohi vaadata enne, kui
koik on PASS.
"""
import numpy as np
import pandas as pd

import sub60_tick as S

OK = []


def kontroll(nimi, tingimus, info=""):
    OK.append(bool(tingimus))
    print(f"{'PASS' if tingimus else 'FAIL'}  {nimi:<52s}{info}")


if __name__ == "__main__":
    print("=" * 104)
    print("SUB-60 MOOTORI AUDIT — enne tulemuste vaatamist")
    print("=" * 104)

    T = S.lae_tikid()
    x = S.sundmused()

    # --- A. VALIM -------------------------------------------------------
    print("\nA  VALIM")
    kontroll("A1 tapselt 30 sundmust", len(x) == 30, f"n={len(x)}")
    kontroll("A2 koik TIER 1", (x["tier"] == "T1").all())
    kontroll("A3 koik |z| >= 1", (x["z"].abs() >= 1).all(),
             f"min|z|={x['z'].abs().min():.3f}")
    kontroll("A4 suund on ainult +1/-1", set(x["suund"].unique()) <= {-1, 1},
             f"{sorted(x['suund'].unique())}")
    kontroll("A5 suund = sign(z)*mark, baasi jargi poordega",
             bool((x["suund"] == np.where(x["baas"],
                                          np.sign(x["z"]) * x["mark"],
                                          -np.sign(x["z"]) * x["mark"])
                   ).all()))
    kontroll("A6 paar vastab KAART-ile",
             bool(x["paar"].eq(x["cur"].map(lambda c: S.I.KAART[c][0])).all()))
    kl = x.groupby([x["ts"], x["paar"]]).ngroups
    kontroll("A7 klastrid loetud (ts,paar)", kl > 0,
             f"{kl} unikaalset (ts,paar) 30 sundmuse kohta")

    # --- B. AJASTUS -----------------------------------------------------
    print("\nB  AJASTUS JA LOOKAHEAD")
    ts = np.array(["2026-01-01T12:00:00.000", "2026-01-01T12:00:01.000",
                   "2026-01-01T12:00:05.000"], dtype="datetime64[ns]")
    kontroll("B1 esimene_alates valib >= sihi (mitte eelmise)",
             S.esimene_alates(ts, np.datetime64("2026-01-01T12:00:00.500")) == 1)
    kontroll("B2 tapne kokkulangevus valitakse (at or after)",
             S.esimene_alates(ts, np.datetime64("2026-01-01T12:00:01.000")) == 1)
    kontroll("B3 uleval piiril -1",
             S.esimene_alates(ts, np.datetime64("2026-01-01T13:00:00.000")) == -1)

    # iga tegelik sisenemine peab olema >= release + D
    halb = 0
    for _, r in x.iterrows():
        for D in S.VIIVITUSED_S:
            t = S.tehing(T, r, D, 30)
            if np.isfinite(t.get("pl_pip", np.nan)) and t["viivitus_s"] < D:
                halb += 1
    kontroll("B4 ukski sisenemine ei ole enne release+D", halb == 0,
             f"rikkumisi={halb}")

    halb2 = 0
    for _, r in x.iterrows():
        t = S.tehing(T, r, 0, 30)
        if np.isfinite(t.get("pl_pip", np.nan)) and t["hoid_tegelik_s"] < 30:
            halb2 += 1
    kontroll("B5 ukski hoid ei ole lubatust luhem", halb2 == 0,
             f"rikkumisi={halb2}")

    # --- C. TAITMINE ----------------------------------------------------
    print("\nC  TAITMINE (paris bid/ask)")

    class F:                       # tehislik tick-seeria teadaoleva vastusega
        pass
    tt = np.array(["2026-01-01T12:00:00.000", "2026-01-01T12:00:30.000"],
                  dtype="datetime64[ns]")
    Tk = {("EURUSD", "2026-01-01"): dict(
        ts=tt, bid=np.array([1.10000, 1.10100]),
        ask=np.array([1.10010, 1.10110]))}
    r_ost = pd.Series(dict(ts=pd.Timestamp("2026-01-01 12:00", tz="UTC"),
                           paar="EURUSD", suund=1))
    r_muuk = pd.Series(dict(ts=pd.Timestamp("2026-01-01 12:00", tz="UTC"),
                            paar="EURUSD", suund=-1))
    o = S.tehing(Tk, r_ost, 0, 30)
    m = S.tehing(Tk, r_muuk, 0, 30)
    # OST: valja BID 1.10100 - sisse ASK 1.10010 = +0.00090 = +9.0 pip
    kontroll("C1 OST = valja BID - sisse ASK",
             abs(o["pl_pip"] - 9.0) < 1e-9, f"{o['pl_pip']:.4f} pip")
    # MUUK: sisse BID 1.10000 - valja ASK 1.10110 = -0.00110 = -11.0 pip
    kontroll("C2 MUUK = sisse BID - valja ASK",
             abs(m["pl_pip"] + 11.0) < 1e-9, f"{m['pl_pip']:.4f} pip")
    kontroll("C3 spread lahutatakse molemas suunas (summa < 0)",
             o["pl_pip"] + m["pl_pip"] < 0,
             f"summa={o['pl_pip'] + m['pl_pip']:.2f} pip = -2x spread")
    kontroll("C4 sisenemisspread moodetud tickist",
             abs(o["spread_sisse_pip"] - 1.0) < 1e-9)

    # JPY pip
    tj = np.array(["2026-01-01T12:00:00.000", "2026-01-01T12:00:30.000"],
                  dtype="datetime64[ns]")
    Tj = {("USDJPY", "2026-01-01"): dict(
        ts=tj, bid=np.array([150.000, 150.100]),
        ask=np.array([150.010, 150.110]))}
    rj = pd.Series(dict(ts=pd.Timestamp("2026-01-01 12:00", tz="UTC"),
                        paar="USDJPY", suund=1))
    kontroll("C5 JPY pip = 0.01 (mitte 0.0001)",
             abs(S.tehing(Tj, rj, 0, 30)["pl_pip"] - 9.0) < 1e-9,
             f"{S.tehing(Tj, rj, 0, 30)['pl_pip']:.4f} pip")
    kontroll("C6 pip-konventsioon", S.pip("USDJPY") == 0.01
             and S.pip("EURUSD") == 0.0001)

    # --- D. PUUDUVAD ANDMED ---------------------------------------------
    print("\nD  PUUDUVAD ANDMED")
    Tp = {("EURUSD", "2026-01-01"): dict(
        ts=np.array(["2026-01-01T12:00:00.000"], dtype="datetime64[ns]"),
        bid=np.array([1.1]), ask=np.array([1.1001]))}
    t = S.tehing(Tp, r_ost, 0, 30)
    kontroll("D1 puuduv valjumistick -> NaN, MITTE null",
             np.isnan(t["pl_pip"]) and t["pl_pip"] != 0,
             f"pohjus='{t['pohjus']}'")
    kontroll("D2 kokkuvote jatab NaN-i valja, ei loe nulliks",
             S.kokkuvote([1.0, np.nan, 3.0])["n"] == 2
             and abs(S.kokkuvote([1.0, np.nan, 3.0])["keskm"] - 2.0) < 1e-9)

    # teadaolev auk peab olema nahtav
    r97 = x[(x["ts"] == pd.Timestamp("2026-09-07 09:00", tz="UTC"))]
    kontroll("D3 2026-09-07 EURUSD on ikka valimis", len(r97) == 1)

    # --- E. DETERMINISM -------------------------------------------------
    print("\nE  DETERMINISM")
    a = [S.tehing(T, r, 0, 30)["pl_pip"] for _, r in x.iterrows()]
    b = [S.tehing(T, r, 0, 30)["pl_pip"] for _, r in x.iterrows()]
    kontroll("E1 kaks jooksu annavad identsed tulemused",
             np.allclose(np.nan_to_num(a, nan=-999),
                         np.nan_to_num(b, nan=-999)))
    kontroll("E2 seeme fikseeritud koodis", S.SEEME == 20260916,
             f"seeme={S.SEEME}")

    # --- F. STATISTIKA --------------------------------------------------
    print("\nF  STATISTIKA")
    kontroll("F1 t-jaotuse p klapib teadaoleva vaartusega",
             abs(S.t_p(2.045, 29) - 0.05) < 0.002, f"p={S.t_p(2.045, 29):.5f}")
    k = S.kokkuvote([2.0, -1.0, 3.0, -2.0])
    kontroll("F2 voidu_osa oige", abs(k["voidu_osa"] - 0.5) < 1e-9)
    kontroll("F3 kokku = summa", abs(k["kokku"] - 2.0) < 1e-9)

    print()
    print("=" * 104)
    print(f"{len(OK)} kontrolli, {len(OK) - sum(OK)} FAIL")
    print("=" * 104)
