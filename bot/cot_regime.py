"""
cot_regime.py — kas COT A_REV on REZIIMIPOHINE serv?

TAUST: A1 naitas, et A_REV on 2006-2016 NEGATIIVNE (-9.41 bp U7) ja
2016-2026 POSITIIVNE (+9.70 bp U7). Uus hupotees EI OLE "leiame paremad
parameetrid", vaid: kas murdepunkti seletab mingi OBJEKTIIVNE, ENNE
TEHINGUT TEADA OLEV tururezhiim?

TAHTIS — UURIMISKOOD. Ei puuduta live-faile.

-----------------------------------------------------------------------------
BASELINE ON MUUTMATA
-----------------------------------------------------------------------------
Kasutame TAPSELT sama A_REV signaali mis A1-s (cot_engine.py):
  net_pct, 156-nadalane rullpertsentiil, lavid 0.90 / 0.10,
  USD = -(7 valuuta keskmine), hoiud 1/2/4 nadalat,
  release-viive >= 6 paeva, NEMSIS BASE kulud, U7 ja U28.
Uhtegi neist EI MUUDETA. Rezhiim on AINULT filter tulemuse peal.

-----------------------------------------------------------------------------
EELREGISTREERITUD REZHIIMIKANDIDAADID (9 tukki, kirjas ENNE tulemusi)
-----------------------------------------------------------------------------
  R1 FXVOL    FX koguvolatiilsus: 7 USD-paari 12-nadalase nadalatootluse
              standardhalbe keskmine
  R2 USDTREND |USD-korvi 26-nadalane log-muut| (trend vs ranging USD-s)
  R3 FXTREND  ristloikeline keskmine |26-nadalane tsentreeritud
              valuutamomentum| (trend vs ranging FX-is laiemalt)
  R4 VIX      VIX 12-nadalane keskmine (risk-off proxy)
  R5 SPXTR    S&P 500 26-nadalane log-tootlus (risk-on/off, margiga)
  R6 DISP     valuutatootluste ristloikeline standardhalve (dispersioon)
  R7 RATE     USA 3-kuu T-bill (^IRX) 12-nadalane keskmine
              (korge vs madal intressikeskkond)
  R8 RATECHG  ^TNX 26-nadalane muut (intressid tousevad vs langevad)
  R9 COTBRE   COT-i laius: mitu valuutat on sel nadalal ekstreemis

REZHIIMI SEISUND: 156-nadalane rullpertsentiil (sama konventsioon mis
COT-signaalil), lavi 0.50 (PRIMAARNE, mediaanjaotus) ja 0.25/0.75
(SEKUNDAARNE, sabad). Lavisid EI OPTIMEERITA — need on fikseeritud ette.

LOOKAHEAD: koik rezhiimimuutujad arvutatakse hindadest kuni SISENEMISE
sulgemiseni (kaasa arvatud) — see on tapselt see hind, millega positsioon
avatakse, seega teada. COT-muutujad kuni avaldatud aruandeni. Uhtegi
tulevast tootlust, tulevast volatiilsust ega full-sample statistikut
EI KASUTATA.
"""
import math

import numpy as np
import pandas as pd

import cot_engine as E
import cot_run as R

REZ_AKEN = 156          # sama kui COT-signaali pertsentiiliaken
LAVI_MED = 0.50
LAVI_ALA, LAVI_YLA = 0.25, 0.75

REZIIMID = ["FXVOL", "USDTREND", "FXTREND", "VIX", "SPXTR",
            "DISP", "RATE", "RATECHG", "COTBRE"]


def rezhiimi_pertsentiilid(al):
    """
    Iga rezhiimimuutuja arvutatakse OMA PIKIMAL loomulikul indeksil ja
    pertsentiil votetakse SEAL, alles siis sammutakse sisenemisnadalatele.

    MIKS: 156-nadalane pertsentiiliaken soob muidu 3 aastat valimist ara
    just seal, kus seda koige rohkem vaja on (2006-2009). VIX/SPX/IRX/TNX
    ulatuvad 2001. aastasse ja COT 2000. aastasse, seega neil ei pea
    soojendust valimi seest votma. FX-pohised muutujad (FXVOL, USDTREND,
    FXTREND, DISP) soltuvad FX-hinnast, mis algab 2006-05-15 — neil
    EI OLE voimalik katvust parandada ja see on ausalt raporteeritud.

    Paevased aknad: 12 nadalat = 60 kauplemispaeva, 26 n = 130 p,
    pertsentiiliaken 156 n = 780 kauplemispaeva.
    """
    sis = al["sis"]
    idx = sis.index
    P12, P26, PP = 60, 130, 780

    out = {}

    # --- FX-pohised: loomulik indeks on paevane FX (2006-05-15 ->) --------
    V = al["V"]
    logV = np.log(V)
    rd = logV.diff()
    rc = rd.sub(rd.mean(axis=1), axis=0)
    paarid = list(E.U7)
    Pp = pd.DataFrame({p: np.log(E.paari_hind(V, p)) for p in paarid}).diff()
    fx = pd.DataFrame(index=V.index)
    fx["FXVOL"] = Pp.rolling(P12).std().mean(axis=1)
    usd_korv = -logV[[c for c in E.VALUUTAD if c != "USD"]].mean(axis=1)
    fx["USDTREND"] = usd_korv.diff(P26).abs()
    m26 = logV.diff(P26)
    m26 = m26.sub(m26.mean(axis=1), axis=0)
    fx["FXTREND"] = m26.abs().mean(axis=1)
    fx["DISP"] = rc.rolling(P12).std().mean(axis=1)
    for c in fx.columns:
        out[c] = E.rull_pertsentiil(fx[c].dropna(), PP).reindex(
            V.index).ffill().reindex(sis.values)

    # --- makro: loomulik indeks on paevane VIX/SPX/IRX/TNX (2001-09 ->) ---
    makro = {"VIX": ("VIX", lambda s: s.rolling(P12).mean()),
             "SPXTR": ("SPX", lambda s: np.log(s).diff(P26)),
             "RATE": ("IRX", lambda s: s.rolling(P12).mean()),
             "RATECHG": ("TNX", lambda s: s.diff(P26))}
    for nimi, (sym, f) in makro.items():
        s = E.lae_hind(sym, "_d25")
        if s is None:
            out[nimi] = pd.Series(np.nan, index=sis.values)
            continue
        x = f(s).dropna()
        out[nimi] = E.rull_pertsentiil(x, PP).reindex(
            s.index).ffill().reindex(sis.values, method="ffill")

    # --- COT laius: loomulik indeks on nadalane COT (2000-01 ->) ----------
    d = E.lae_cot()
    N = E.net_pct_tabel(d)
    Pn = N.apply(E.rull_pertsentiil)
    bre = (E.skoor_A(Pn) != 0).sum(axis=1).astype(float)
    out["COTBRE"] = E.rull_pertsentiil(bre.dropna(), REZ_AKEN).reindex(
        N.index).ffill().reindex(sis.index)

    M = pd.DataFrame({k: np.asarray(v) for k, v in out.items()}, index=idx)
    return M[REZIIMID]


def seisund(pct, lavi_med=LAVI_MED, ala=LAVI_ALA, yla=LAVI_YLA):
    """
    Valmis pertsentiilidest -> 2 seisundit.
      kahene: 'HIGH' kui pct >= 0.50, muidu 'LOW'
      sabad : 'HIGH' kui pct >= 0.75, 'LOW' kui <= 0.25, muidu None
    """
    kahene = pct.apply(lambda s: np.where(s.isna(), None,
                                          np.where(s >= lavi_med, "HIGH", "LOW")))
    sabad = pct.apply(lambda s: np.where(s.isna(), None,
                                         np.where(s >= yla, "HIGH",
                                                  np.where(s <= ala, "LOW", None))))
    return kahene, sabad


def tulemused(al, uni, suund="A_REV", hoia=1):
    """Nadalane neto tootlusseeria, MUUTMATA baseline."""
    paarid, kulu = R.universum(uni, al["V"])
    S = R.skoorid(al, suund)
    W = E.kaalud(S, paarid, hoia)
    H = E.nadala_hinnad(al["V"], paarid, al["sis"])
    H.index = al["sis"].index
    return E.portfell(W, H, kulu)


def t_vahe(a, b):
    """Welchi t kahe keskmise vahele."""
    a = np.asarray(a, float); a = a[np.isfinite(a)]
    b = np.asarray(b, float); b = b[np.isfinite(b)]
    if len(a) < 20 or len(b) < 20:
        return float("nan"), float("nan")
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    if va + vb <= 0:
        return float("nan"), float("nan")
    t = (a.mean() - b.mean()) / math.sqrt(va + vb)
    return t, E.p_kahepoolne(t)
