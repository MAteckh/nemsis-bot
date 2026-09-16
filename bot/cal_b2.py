"""
cal_b2.py — B2 EVENT-TIME PROFILE mootor (majanduskalendri viivitatud reaktsioon).

KUSIMUS. B1 leidis paevasel horisondil TIER 1 bruto +4.27 bp (t=4.97), aga
H1-aknas +1h -0.66 bp, +4h -0.17 bp, +24h -0.62 bp. B1 raporti O3 naitas,
et SAMAL aknal ja SAMADEL sundmustel annab paevane test +7.28 bp ja H1 test
-0.24 bp — erinevus EI OLE valimi suurus, vaid AKEN. Paevane test motab
sulgemisest sulgemiseni, mis on umbkaudu T+8h .. T+32h.

B2 HUPOTEES (eelregistreeritud, kirjutatud ENNE esimest jooksu):
  Kui B1 efekt on reaalne, aga ei realiseeru kohe, siis tekib positiivne
  drift teate JAREL, umbes 8-32 tunni jooksul.

B2 EI OTSI parimat exitit. Event-time grid on FIKSEERITUD ja kogu profiil
on KIRJELDAV. AINUS jareldav test on eelregistreeritud T+8h -> T+32h.

TAHTIS — UURIMISKOOD. Ei puuduta live-faile (main_v4.py, config.py,
mt5_connector.py, strategy_meanrev.py, backtest.py, gold_logic.py,
strategies.py).

-----------------------------------------------------------------------------
B1-ST MUUTMATA (kontrollitud koodist, mitte eeldatud)
-----------------------------------------------------------------------------
z            (actual - forecast) / rull-std(20 VARASEMAT sama (valuuta,
             indikaator) prognoosiviga, min 10), shift(1) enne rolling'ut.
             cal_engine.z_ullatus — kutsutakse otse, mitte kopeeritakse.
suund        sign(z) * eelregistreeritud majanduslik mark (cal_engine.TIER1).
universum    TIER 1, 11 indikaatorit. Liikmeid EI MUUDETA.
lavi         |z| >= 1.0 (cal_engine.LAVI). Uut lavet EI OTSITA.
tootlus      valuuta log-tootlus MIINUS ristloikeline keskmine (8 valuutat).
kulu         1.25 bp uhesuunaline, 2.50 bp edasi-tagasi (cal_engine).

-----------------------------------------------------------------------------
B2 UUS OSA — AJASTUS
-----------------------------------------------------------------------------
H1-baar on margistatud AVAMISAJAGA; ta sulgub margis + 1 h (sama eeldus mis
cal_engine.h1_sisenemine ja cal_audit A3).

Hind hetkel tau = VIIMANE baar, mille SULGEMINE on <= tau. See on rangelt
pohjuslik: hetkel tau ei saa teada hilisemat hinda. Kui lahim sulgemine on
vanem kui TOLERANTS tundi (nadalavahetus, andmeauk), on sundmus sellel
horisondil VALJA JAETUD ja loendatud eraldi — proksit EI ASENDATA.

ANKUR (profiili nullpunkt) = viimane sulgemine <= T. See on teate-EELNE
hind. Seetottu sisaldab loik 0h -> 1h teatehupet ennast ja EI OLE
kaubeldav — see on markitud igal pool eraldi. Loigud alates 1h -> 2h on
kaubeldavad.

KAKS AJAARVESTUST, molemad eelregistreeritud, molemad raporteeritud:
  SEINAKELL (primaarne)  horisont = T + h tundi, tolerants 4 h.
                         See on tapselt see, mida B2 kusib.
  BAARILUGEMINE (teisene) horisont = ankur + h baari, nagu B1 H1-test
                         (LOG.diff(k)). FX-baare on ainult kauplemisajal,
                         seega nadalavahetus hupatakse vahele.

-----------------------------------------------------------------------------
EELREGISTREERITUD JAOTUS (H1-aken, kalendriaasta-pohine, MITTE tulemuspohine)
-----------------------------------------------------------------------------
TRAIN      .. 2024-12-31
VALID      2025-01-01 .. 2025-12-31
FINAL OOS  2026-01-01 ..
B1 enda jaotus (TRAIN<=2017, VALID<=2020) EI OLE siin kasutatav: kogu
H1-aken 2023-11-27+ langeb tervikuna B1 FINAL OOS-i sisse.
"""
import math
import os

import numpy as np
import pandas as pd

import cal_engine as C
import h1engine as H

DATA = C.DATA
JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- eelregistreeritud B2 konstandid --------------------------------------
HORISONDID = [1, 2, 4, 8, 12, 16, 24, 32, 48]      # tundides, FIKSEERITUD
LOIGUD = [(1, 2), (2, 4), (4, 8), (8, 12), (12, 16),
          (16, 24), (24, 32), (32, 48)]
PRIMARY_SISSE, PRIMARY_VALJA = 8, 32               # AINUS jareldav test
TOLERANTS_H = 4.0                                  # max hinna vanus tundides
KULU_RT_BP = 2.0 * C.KULU_1SUUND_BP                # 2.50 bp edasi-tagasi
KULU_TASEMED = [0.0, 0.5, 1.0, 1.25, 1.5, 2.0]     # uhesuunaline bp
N_PERM = 500
SEEME = 20260915

B2_TRAIN_LOPP = pd.Timestamp("2024-12-31 23:59:59")
B2_VALID_LOPP = pd.Timestamp("2025-12-31 23:59:59")

VALUUTAD = C.VALUUTAD
PAARID = {"EUR": ("EURUSD", False), "GBP": ("GBPUSD", False),
          "AUD": ("AUDUSD", False), "NZD": ("NZDUSD", False),
          "JPY": ("USDJPY", True), "CHF": ("USDCHF", True),
          "CAD": ("USDCAD", True)}


# ------------------------------------------------------------ H1 ANDMED ---
def h1_valuutad():
    """1 uhiku valuuta vaartus USD-des, H1-baaridel. USD = 1.0."""
    h = {}
    for c, (sym, inv) in PAARID.items():
        d = H.lae(sym)
        if d is None:
            continue
        h[c] = (1.0 / d["close"]) if inv else d["close"]
    ix = None
    for s in h.values():
        ix = s.index if ix is None else ix.intersection(s.index)
    HV = pd.DataFrame({c: s.reindex(ix) for c, s in h.items()})
    HV["USD"] = 1.0
    return HV[VALUUTAD].dropna().sort_index()


# -------------------------------------------------------------- AJASTUS ---
def pos_hetkel(idx, sihid, tolerants=TOLERANTS_H):
    """
    Viimane baar, mille SULGEMINE (label + 1h) on <= siht.
    Tagastab -1, kui sellist baari ei ole voi ta on vanem kui `tolerants`.
    Rangelt pohjuslik: tulevikku ei vaadata kunagi.
    """
    sulg = np.asarray(idx.values, dtype="datetime64[ns]") + np.timedelta64(1, "h")
    s = np.asarray(sihid, dtype="datetime64[ns]")
    pos = np.searchsorted(sulg, s, side="right") - 1
    ok = pos >= 0
    pk = np.clip(pos, 0, len(sulg) - 1)
    vanus = np.where(ok, (s - sulg[pk]) / np.timedelta64(1, "h"), 1e9)
    return np.where(ok & (vanus <= tolerants), pos, -1), vanus


def pos_horisont(idx, ts, h, reziim="SEINAKELL", ankur=None):
    """Horisondi h positsioon. reziim: SEINAKELL (T + h tundi) voi BAARE."""
    if reziim == "SEINAKELL":
        siht = np.asarray(ts, dtype="datetime64[ns]") + np.timedelta64(int(h * 60), "m")
        p, _ = pos_hetkel(idx, siht)
        return p
    p = np.where(ankur >= 0, ankur + int(h), -1)
    return np.where((p >= 0) & (p < len(idx)), p, -1)


# ------------------------------------------------------------- TOOTLUS ----
def neutraalne(LOGV, i1, i2, cur_idx):
    """
    Ristloikeliselt tsentreeritud log-tootlus i1 -> i2 antud valuuta jaoks.
    SAMA definitsioon mis cal_engine.valuuta_tootlused, aga sundmusepohiselt.
    """
    out = np.full(len(i1), np.nan)
    m = (i1 >= 0) & (i2 >= 0)
    if not m.any():
        return out
    d = LOGV[i2[m]] - LOGV[i1[m]]
    d = d - d.mean(axis=1, keepdims=True)
    out[m] = d[np.arange(d.shape[0]), cur_idx[m]]
    return out


# --------------------------------------------------------------- VALIM ----
def valim(tier="T1", lavi=C.LAVI):
    """
    TIER 1 sundmused, millel on z ja mis jaavad H1-aknasse.
    z arvutatakse KOGU kalendri peal (T1+T2), nagu B1-s, ja alles siis
    filtreeritakse tier — nii on z-ajalugu identne B1-ga.
    """
    d = C.z_ullatus(C.lae_kalender(("T1", "T2")))
    d = d[d["z"].notna()].copy()
    d["algne_idx"] = d.index          # (ts,cur,indicator) EI OLE unikaalne
    if tier:
        d = d[d["tier"] == tier].copy()
    d["suund"] = np.sign(d["z"]) * d["mark"]
    HV = h1_valuutad()
    ank, vanus = pos_hetkel(HV.index, d["ts"].values)
    d["ankur"] = ank
    d["ankur_vanus_h"] = vanus
    d = d[d["ankur"] >= 0].copy()
    d["cur_idx"] = d["cur"].map({c: i for i, c in enumerate(VALUUTAD)}).astype(int)
    return d.sort_values("ts").reset_index(drop=True), HV


def lisa_horisondid(d, HV, reziim="SEINAKELL"):
    """Lisab veerud h{H} (tootlus ankrust horisondini) ja p{H} (positsioon)."""
    LOGV = np.log(HV.values)
    ts = d["ts"].values
    ank = d["ankur"].values
    ci = d["cur_idx"].values
    for h in HORISONDID:
        p = pos_horisont(HV.index, ts, h, reziim, ank)
        d[f"p{h}"] = p
        d[f"h{h}"] = neutraalne(LOGV, ank, p, ci)
    return d


# ---------------------------------------------------------- STATISTIKA ----
def moot(x, kulu_bp=0.0):
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 20:
        return None
    sd = x.std(ddof=1)
    bp = 1e4 * float(x.mean())
    t = float(x.mean() / sd * math.sqrt(len(x))) if sd > 0 else 0.0
    return dict(n=len(x), bruto_bp=bp, med_bp=1e4 * float(np.median(x)),
                neto_bp=bp - kulu_bp, wr=100.0 * float((x > 0).mean()),
                sd_bp=1e4 * float(sd), t=t, p=C.p_kahepoolne(t),
                kum_bruto=float(np.exp(x.sum()) - 1.0),
                kum_neto=float(np.exp(x.sum() - len(x) * kulu_bp / 1e4) - 1.0))


def bh(ps, q=0.05):
    ps = np.asarray(ps, float)
    n = len(ps)
    lavi = 0.0
    for r, i in enumerate(np.argsort(ps), start=1):
        if ps[i] <= q * r / n:
            lavi = ps[i]
    return (ps <= lavi) if lavi > 0 else np.zeros(n, bool), lavi


PAIS = (f"{'test':<30s}{'n':>7s}{'bruto':>9s}{'med':>8s}{'neto':>8s}"
        f"{'wr%':>7s}{'t':>7s}{'p':>8s}")


def rida(nimi, m, w=30):
    if m is None:
        return f"{nimi:<{w}s}      (alla 20 sundmuse)"
    return (f"{nimi:<{w}s}{m['n']:>7d}{m['bruto_bp']:>+9.2f}{m['med_bp']:>+8.2f}"
            f"{m['neto_bp']:>+8.2f}{m['wr']:>7.1f}{m['t']:>7.2f}{m['p']:>8.3f}")
