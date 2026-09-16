"""
cal_sub60.py — ECONOMIC CALENDAR SUB-60-SECOND EXECUTION TEST (mootor).

AINUS KUSIMUS: kas makroteate hinnahuppe saab REAALSELT puuda 0-60 sekundi
jooksul parast valjalaset?

TAUST. Immediate Execution test (commit 361732e) naitas:
  |liikumine| 0 -> +5 min mediaan 17.0 bp; 94% kogu 60-min liikumisest on
  +5 min hetkeks toimunud; M5 sisenemine (viivitus 5 min) andis bruto
  +1.22 bp vs kulu 2.19 bp => neto -0.97 bp; H1 (n=408) bruto -0.09 bp.
  0-60 SEKUNDI AKEN JAI DATA INSUFFICIENT.

TAHTIS — UURIMISKOOD. Ei puuduta live-faile (main_v4.py, config.py,
mt5_connector.py, strategy_meanrev.py, backtest.py, gold_logic.py,
strategies.py).

=============================================================================
ANDMEALLIKATE AUDIT — MIDA KONTROLLITI JA MIS ON TEGELIKULT SAADAVAL
=============================================================================
Liivakastil EI OLE otseuhendust (curl koigile allpool: HTTP 000).
Ainus valjapaas on kasutaja Supabase `http` laiendus.

  ALLIKAS                     BID/ASK   RESOLUTSIOON   PERIOOD      SAADAV?
  -------------------------   -------   ------------   ----------   -------
  Dukascopy .bi5 tick         JAH       tick           ~2003-       EI
      pohjus: fail on LZMA-pakitud BINAAR. pgsql-http tagastab
      `content` TEKSTINA; binaarne sisu rikutakse. Bytea-tagastust
      sellel laiendusel ei ole. EI SAA voltsida => EI KASUTATUD.
  HistData.com M1/tick        JAH       M1 / tick      2000-        EI
      pohjus: nouab POST-vormi tokeniga ja tagastab ZIP-i (binaar).
      Sama takistus.
  TrueFX tick                 JAH       tick           2009-        EI
      pohjus: ajalooline arhiiv nouab registreerimist ja sisselogimist.
      Kasutaja API-votit EI KUSITUD (uurimisprotokolli reegel).
  Yahoo Finance 1m            EI        M1 OHLC (mid)  ~28 paeva    JAH
      MOOEDETUD: 7-paevaste period1/period2 akendega tootavad aknad
      0-7, 7-14, 14-21 paeva tagasi; 28 ja 35 paeva tagasi tagastavad
      0 rida. Seega ~28 paeva, MITTE rohkem.
  Yahoo Finance 5m            EI        M5 OHLC (mid)  ~60 paeva    JAH
      juba laetud eelmises testis (bot/sb_m5.py)

  JARELDUS, MIS MAARAB KOGU SELLE TESTI:
    TICK ja BID/ASK EI OLE KATTESAADAVAD.
    Koige peenem, mida saab, on M1 mid-OHLC, 28 paeva.
    => 1 / 3 / 5 / 10 / 15 / 30 SEKUNDI horisonte EI SAA MOOTA.
       Neid EI INTERPOLEERITA ja EI VOLTSITA. Nad on DATA INSUFFICIENT.
    => M1 suudab moota AINULT: "sisenemine esimesel hinnal, mis on
       rangelt parast valjalaset" (viivitus <= 60 s) ja hoiud
       60 s / 120 s / 300 s.

=============================================================================
EELREGISTREERITUD ENNE ESIMEST JOOKSU
=============================================================================
ullatus     cal_engine.z_ullatus, KUTSUTAKSE OTSE (aken 20, min 10, shift(1))
universum   B1 TIER 1, 11 indikaatorit, margid muutmata
lavi        PRIMARY |z| >= 1.0; tundlikkus 1.5 ja 2.0
kaart       cal_imm.KAART, MUUTMATA (EUR->EURUSD baas, USD->EURUSD kvoot, ...)
sisenemine  D0 = esimene baar, mille SULGEMINE on RANGELT PARAST valjalaset
            (lookahead-kaitse: teated tulevad :00/:15/:30/:45, mis langevad
             tapselt kokku baaride sulgemisega)
PRIMARY     RADA M1, D0 sisenemine, hoid 60 s
kulu        paaripohine uhesuunaline bp x 2; libisemine UKS KORD sisenemisel
            0 / 1 / 2 / 3 / 5 / 10 bp — SIMULEERITUD, sest bid/ask puudub
seeme       20260916
"""
import math
import os

import numpy as np
import pandas as pd

import cal_engine as C
import cal_imm as I

DATA = C.DATA
JUUR = I.JUUR
SEEME = 20260916
N_BOOT = 2000

KAART = I.KAART
KULU_1SUUND = I.KULU_1SUUND
LAVID = I.LAVID
LIBISEMISED = I.LIBISEMISED

# --- sekundilised vorgud, eelregistreeritud -------------------------------
VIIVITUSED_S = [0, 1, 3, 5, 10, 15, 30, 60]      # sekundites
HOIUD_S = [5, 10, 15, 30, 60, 120]               # sekundites
PRIMARY_VIIVITUS_S, PRIMARY_HOID_S = 0, 60

RAJAD = {
    "M1":  dict(sufiks="_m1",  baar_s=60,   nimi="RADA M1 "),
    "M5":  dict(sufiks="_m5",  baar_s=300,  nimi="RADA M5 "),
    "M15": dict(sufiks="_m15", baar_s=900,  nimi="RADA M15"),
}


def hinnad(sufiks):
    return I.hinnad(sufiks)


def valim(tier="T1"):
    return I.valim(tier)


def pos_parast(idx, baar_s, sihid, range_=True):
    """
    Esimene baar, mille SULGEMINE (label + baar_s) on sihi juures voi jarel.

    range_=True  (SISENEMINE): sulgemine peab olema RANGELT PARAST sihti.
        Teated tulevad :00/:15/:30/:45 ja langevad TAPSELT kokku baaride
        sulgemisega (audit 4b: 6/6 EURUSD-sundmusel). Selle baari sulgemine
        on TERVIKUNA teate-EELNE hind => vordus oleks LOOKAHEAD.
    range_=False (VALJUMINE): vordus on LUBATUD. Baar, mis sulgeb tapselt
        siht-ajal, annab hinna, mis ON siht-ajal teada. Range reegel
        pikendaks 60 s hoidu 120 s peale ilma pohjuseta (audit leidis).
    """
    sulg = (np.asarray(idx.values, dtype="datetime64[ns]")
            + np.timedelta64(int(baar_s), "s"))
    s = np.asarray(sihid, dtype="datetime64[ns]")
    pos = np.searchsorted(sulg, s, side="right" if range_ else "left")
    return np.where(pos < len(sulg), pos, -1)


def tehingud(d, Hp, baar_s, viivitus_s, hoid_s, max_lunk_s=None):
    """Uks rida = uks sundmus. Sekundipohine ajastus."""
    if max_lunk_s is None:
        max_lunk_s = 2 * baar_s
    read = []
    for paar, x in d.groupby("paar"):
        P = Hp.get(paar)
        if P is None:
            continue
        idx = P.index
        sulg = pd.DatetimeIndex(idx) + pd.Timedelta(seconds=baar_s)
        siht = pd.DatetimeIndex(x["ts"]) + pd.Timedelta(seconds=viivitus_s)
        pin = pos_parast(idx, baar_s, siht.values)
        for kk, (_, r) in enumerate(x.iterrows()):
            i = int(pin[kk])
            if i < 0:
                continue
            t_in = sulg[i]
            if (t_in - siht[kk]).total_seconds() > max_lunk_s:
                continue
            siht_out = t_in + pd.Timedelta(seconds=hoid_s)
            j = int(pos_parast(idx, baar_s,
                               np.array([siht_out.to_datetime64()]),
                               range_=False)[0])
            if j < 0 or j <= i:
                continue
            t_out = sulg[j]
            if (t_out - siht_out).total_seconds() > max_lunk_s:
                continue
            p_in, p_out = float(P["close"].iloc[i]), float(P["close"].iloc[j])
            if not (np.isfinite(p_in) and np.isfinite(p_out)
                    and p_in > 0 and p_out > 0):
                continue
            read.append((r["algne_idx"], r["cur"], r["indicator"], r["ts"],
                         paar, int(r["suund"]), float(r["z"]), t_in, t_out,
                         p_in, p_out, float(r["kulu_1suund_bp"]),
                         int(r["suund"]) * math.log(p_out / p_in),
                         (t_in - pd.Timestamp(r["ts"])).total_seconds(),
                         (t_out - t_in).total_seconds()))
    T = pd.DataFrame(read, columns=[
        "algne_idx", "cur", "indicator", "ts", "paar", "suund", "z",
        "sisse_aeg", "valja_aeg", "p_in", "p_out", "kulu_1suund_bp",
        "bruto", "viivitus_s", "hoid_s"])
    if len(T):
        T["kulu"] = 2.0 * T["kulu_1suund_bp"] / 1e4
        T["neto"] = T["bruto"] - T["kulu"]
    return T.sort_values("ts").reset_index(drop=True)


def signed_profiil(d, Hp, baar_s, sekundid):
    """
    MARGIGA tootlus valjalaske-EELSEST ankrust kuni T + s sekundit.
    Ankur = viimane sulgemine <= T. Loik 0 -> esimene punkt sisaldab hupet
    ja EI OLE kaubeldav.
    """
    out = {}
    for paar, x in d.groupby("paar"):
        P = Hp.get(paar)
        if P is None:
            continue
        idx = P.index
        sulg = (np.asarray(idx.values, dtype="datetime64[ns]")
                + np.timedelta64(int(baar_s), "s"))
        ts = np.asarray(pd.DatetimeIndex(x["ts"]).values, dtype="datetime64[ns]")
        a = np.searchsorted(sulg, ts, side="right") - 1
        for kk, ii in enumerate(a):
            if ii < 0:
                continue
            p0 = float(P["close"].iloc[ii])
            sg = int(x["suund"].iloc[kk])
            rida = {}
            for s in sekundid:
                j = int(pos_parast(idx, baar_s,
                                   np.array([ts[kk] + np.timedelta64(s, "s")]),
                                   range_=False)[0])
                rida[s] = (sg * math.log(float(P["close"].iloc[j]) / p0)
                           if j >= 0 and p0 > 0 else np.nan)
            out[(paar, x["ts"].iloc[kk], kk)] = rida
    return pd.DataFrame(out).T


def moot(T, libisemine_bp=0.0):
    return I.moot(T, libisemine_bp)


def juhuslik_baas(T, seeme=SEEME, katseid=N_BOOT):
    return I.juhuslik_baas(T, seeme, katseid)


def bootstrap_ci(x, seeme=SEEME, katseid=N_BOOT):
    return I.bootstrap_ci(x, seeme, katseid)


PAIS = I.PAIS
rida = I.rida
