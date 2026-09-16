"""
sub60_tick.py — ESIMENE PARIS SUB-60-SEKUNDILINE TAITMISTEST.

UURIMISKOOD. Ei puuduta live-faile.

MIDA SIIN TEHAKSE
-----------------
Voetakse 30 EELREGISTREERITUD TIER 1 |z|>=1 sundmust (tapselt needsamad,
mis bot/dukascopy_plan.py valis ja mille katvus on 30/30), ning moodetakse
PARIS Dukascopy bid/ask tickidel, kas signaali suunas kauplemine toodab
midagi 0-60 sekundi aknas.

LUKUS OLEVAD DEFINITSIOONID (mitte muuta parast tulemuste nagemist)
-------------------------------------------------------------------
z        : cal_engine.z_ullatus — e = actual - forecast, jagatud sama
           (valuuta, indikaator) viimase 20 MINEVIKU prognoosivea std-ga,
           min 10 vaatlust, shift(1). Muutmata.
mark     : cal_engine.TIER1 eelregistreeritud majanduslik mark.
suund    : cal_imm.valim — sign(z) * mark annab valuutasuuna; paarisuund
           sobitatakse selle jargi, kas valuuta on paaris BAAS.
           Muutmata, kopeeritud cal_imm-ist.
kaart    : cal_imm.KAART, valuuta -> koige likviidsem major.
filter   : |z| >= 1, TIER 1.

TAITMINE — PARIS POOLED, MITTE KESKMINE HIND
--------------------------------------------
OST : sisse ASK, valja BID
MUUK: sisse BID,  valja ASK
Uhtegi eeldatavat/fikseeritud/keskmist spreadi ei kasutata.

AJASTUS
-------
sisenemine: esimene tick, mille ts >= release + D   (side="left")
valjumine : esimene tick, mille ts >= sisenemistick + H
Interpoleerimist EI TEHTA. Eelmist ticki EI KASUTATA.
Kui ticki ei ole -> NA. NA EI OLE NULLTOOTLUS.

NB LOOKAHEAD: spetsifikatsioon utleb otsesonu "at or after", seega D=0
kasutab ticki, mis voib olla TAPSELT release'i hetkel. Raporteerime
sisenemisviivituse jaotuse, et see oleks nahtav; kui moni viivitus on
tapselt 0.000 s, on see eraldi valja toodud.
"""
import os
import numpy as np
import pandas as pd

import cal_engine as C
import cal_imm as I

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
TICKS = os.path.join(DATA, "dukascopy", "ticks")
JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALJUND = os.path.join(JUUR, "reports", "dukascopy_sub60")

# --- EELREGISTREERITUD VORE (fikseeritud enne jooksu) --------------------
VIIVITUSED_S = [0, 1, 3, 5, 10, 15, 30, 60]
HOIUD_S = [5, 10, 15, 30, 60, 120]
PRIMARY_VIIVITUS, PRIMARY_HOID = 0, 30
MID_HORISONDID = [1, 3, 5, 10, 15, 30, 60]
SEEME = 20260916
N_PERM = 10000
SIHT_SUNDMUSI = 30


def pip(sym):
    return 0.01 if "JPY" in sym else 0.0001


# ------------------------------------------------------------- ANDMED ----
def lae_tikid():
    out = {}
    import glob
    for f in sorted(glob.glob(os.path.join(TICKS, "*_ticks.csv"))):
        sym, paev = os.path.basename(f)[:-len("_ticks.csv")].split("_")
        d = pd.read_csv(f)
        d["ts_utc"] = pd.to_datetime(d["ts_utc"], utc=True)
        d = d.sort_values("ts_utc").reset_index(drop=True)
        out[(sym, paev)] = dict(
            ts=d["ts_utc"].values.astype("datetime64[ns]"),
            bid=d["bid"].to_numpy(float), ask=d["ask"].to_numpy(float))
    return out


def sundmused():
    """TAPSELT sama valik mis dukascopy_plan.py — poord-kronoloogiline."""
    d = I.valim("T1")
    d["ts"] = pd.to_datetime(d["ts"], utc=True)
    x = d[d["z"].abs() >= 1].copy()
    x["paev"] = x["ts"].dt.date
    paevad = sorted(x["paev"].unique(), reverse=True)
    sel, k = [], 0
    for p in paevad:
        sel.append(p)
        k += int((x["paev"] == p).sum())
        if k >= SIHT_SUNDMUSI:
            break
    return x[x["paev"].isin(sel)].sort_values("ts").reset_index(drop=True)


# ------------------------------------------------------------ AJASTUS ----
def esimene_alates(ts, siht):
    """Esimene indeks, mille ts >= siht. -1 kui pole."""
    i = int(np.searchsorted(ts, siht, side="left"))
    return i if i < len(ts) else -1


def tehing(T, r, D, H):
    """Uks sundmus, uks (viivitus, hoid). Tagastab dict voi None-vali."""
    paev = str(r["ts"].date())
    P = T.get((r["paar"], paev))
    tyhi = dict(pl_pip=np.nan, pohjus="tick-faili pole")
    if P is None:
        return tyhi
    ts = P["ts"]
    t0 = np.datetime64(r["ts"].tz_convert("UTC").tz_localize(None), "ns")

    i = esimene_alates(ts, t0 + np.timedelta64(int(D), "s"))
    if i < 0:
        return dict(pl_pip=np.nan, pohjus=f"sisenemistikki pole (D={D}s)")
    t_in = ts[i]
    j = esimene_alates(ts, t_in + np.timedelta64(int(H), "s"))
    if j < 0:
        return dict(pl_pip=np.nan, pohjus=f"valjumistikki pole (H={H}s)")

    bid_in, ask_in = P["bid"][i], P["ask"][i]
    bid_out, ask_out = P["bid"][j], P["ask"][j]
    s = int(r["suund"])
    if s > 0:                                  # OST: sisse ASK, valja BID
        pl = bid_out - ask_in
    else:                                      # MUUK: sisse BID, valja ASK
        pl = bid_in - ask_out
    jag = pip(r["paar"])
    return dict(
        pl_pip=pl / jag, pohjus="",
        sisse_ts=str(pd.Timestamp(t_in)), valja_ts=str(pd.Timestamp(ts[j])),
        viivitus_s=float((t_in - t0) / np.timedelta64(1, "s")),
        hoid_tegelik_s=float((ts[j] - t_in) / np.timedelta64(1, "s")),
        spread_sisse_pip=(ask_in - bid_in) / jag,
        spread_valja_pip=(ask_out - bid_out) / jag,
        tikke_aknas=int(j - i),
        mid_liik_pip=s * (((bid_out + ask_out) / 2
                           - (bid_in + ask_in) / 2) / jag))


def mid_liikumine(T, r, h):
    """Signaalisuunaga korrutatud KESKHINNA liikumine release'ist +h s."""
    paev = str(r["ts"].date())
    P = T.get((r["paar"], paev))
    if P is None:
        return np.nan
    ts, t0 = P["ts"], np.datetime64(r["ts"].tz_convert("UTC")
                                    .tz_localize(None), "ns")
    i = esimene_alates(ts, t0)
    j = esimene_alates(ts, t0 + np.timedelta64(int(h), "s"))
    if i < 0 or j < 0:
        return np.nan
    m0 = (P["bid"][i] + P["ask"][i]) / 2
    m1 = (P["bid"][j] + P["ask"][j]) / 2
    return int(r["suund"]) * (m1 - m0) / pip(r["paar"])


# --------------------------------------------------------- STATISTIKA ----
def t_p(t, df):
    """Kahepoolne Studenti p regulariseeritud mittetaieliku beetaga."""
    if not np.isfinite(t) or df <= 0:
        return np.nan
    x = df / (df + t * t)
    return float(_betainc(df / 2.0, 0.5, x))


def _betainc(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    import math
    lbeta = (math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b))
    front = math.exp(math.log(x) * a + math.log(1 - x) * b - lbeta) / a
    if x < (a + 1) / (a + b + 2):
        return front * _cf(a, b, x)
    return 1.0 - math.exp(math.log(1 - x) * b + math.log(x) * a - lbeta) / b \
        * _cf(b, a, 1 - x)


def _cf(a, b, x, it=300, eps=1e-12):
    """Lentzi meetod mittetaieliku beeta ahelmurru jaoks."""
    f, c, d = 1.0, 1.0, 0.0
    for i in range(it + 1):
        m = i // 2
        if i == 0:
            num = 1.0
        elif i % 2 == 0:
            num = (m * (b - m) * x) / ((a + 2 * m - 1) * (a + 2 * m))
        else:
            num = -((a + m) * (a + b + m) * x) / ((a + 2 * m) * (a + 2 * m + 1))
        d = 1.0 + num * d
        d = eps if abs(d) < eps else d
        d = 1.0 / d
        c = 1.0 + num / c
        c = eps if abs(c) < eps else c
        f *= c * d
        if abs(1.0 - c * d) < eps:
            break
    return f - 1.0


def kokkuvote(v):
    v = np.asarray([x for x in v if np.isfinite(x)], float)
    n = len(v)
    if n == 0:
        return dict(n=0)
    sd = float(v.std(ddof=1)) if n > 1 else np.nan
    t = float(v.mean() / (sd / np.sqrt(n))) if n > 1 and sd > 0 else np.nan
    vo = v[v > 0]
    ka = v[v < 0]
    return dict(n=n, keskm=float(v.mean()), mediaan=float(np.median(v)),
                kokku=float(v.sum()), voidu_osa=float((v > 0).mean()),
                sd=sd, t=t, p=t_p(t, n - 1),
                keskm_voit=float(vo.mean()) if len(vo) else np.nan,
                keskm_kaotus=float(ka.mean()) if len(ka) else np.nan,
                max_voit=float(v.max()), max_kaotus=float(v.min()))
