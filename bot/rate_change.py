"""
rate_change.py — NEMSIS INTEREST-RATE DIFFERENTIAL CHANGE TEST (mootor).

KUSIMUS: kas FX-paari tootlust ennustab mitte intressimaarade TASE, vaid
see, KUIDAS kahe valuuta intressidiferentsiaal MUUTUB?

MIKS SEE ON UUS MEHHANISM. NEMSIS v6 (bot/v6_carry.py) testis TASET:
CARRY_REL = maar vs korvi keskmine, LONG top-2 / SHORT bottom-2 valuutat,
kuine/nadalane rebalanss. Tulemus: Sharpe 0.42, kolm tapjat (brokeri
markup, JPY-kontsentratsioon, 205 EUR konto). MUUTUST ei ole kunagi
testitud — MASTER EDGE MAP rida 17: "tase testitud; MUUTUS mitte".

TAHTIS — UURIMISKOOD. Ei puuduta live-faile (main_v4.py, config.py,
mt5_connector.py, strategy_meanrev.py, backtest.py, gold_logic.py,
strategies.py).

-----------------------------------------------------------------------------
EELREGISTREERITUD ENNE ESIMEST JOOKSU — EI MUUDETA TULEMUSTE PARAST
-----------------------------------------------------------------------------
andmed        bot/data/policy_rates.csv — BIS WS_CBPOL, keskpankade
              ametlikud poliitikamaarad, KUU LOPU seis, 2016-01..2026-08,
              8 valuutat. Neid EI REVIDEERITA.
nihe          kuu M maar kehtib alates kuust M+1 (shift(1)). TAPSELT
              sama reegel mis v6_carry.py. Konservatiivne.
universum     koik 28 unikaalset paari 8 valuutast (USD EUR GBP JPY CHF
              CAD AUD NZD). Uhtegi paari EI EEMALDATA tulemuste jargi.
D(t)          R_baas(t) - R_kvoot(t), protsenti aastas
PRIMARY       CHANGE_D(t) = D(t) - D(t - 4 nadalat)
signaal       +1 kui CHANGE_D > 0 (LONG baas), -1 kui < 0, 0 kui = 0
              MAGNITUUDI EI FILTREERITA
vaatlus       nadalane, reede sulgemine
sisenemine    JARGMISE kauplemispaeva AVAHIND (rangelt parast signaali)
hoid          4 nadalat = 20 kauplemispaeva
tootlus       log(P_valja / P_sisse) * signaal
kulu          cot_engine.KULU_BASE / KULU_RIST, uhesuunaline bp;
              edasi-tagasi = 2 x uhesuunaline
jaotus        TRAIN .. 2020-12-31
              VALID 2021-01-01 .. 2023-12-31
              FINAL OOS 2024-01-01 ..
              kalendriaasta-pohine, valitud ENNE tulemusi
permutatsioon 500, seeme 20260916

MIDA SEE TEST EI TEE
  ei testi teisi lookback'e (1W/2W/8W/12W/6M) enne primary klassifitseerimist
  ei testi teisi hoideperioode
  ei kombineeri TASET ja MUUTUST primary strateegiaks
  ei filtreeri CHANGE_D suurust
  ei ehita poordsignaalist live-kandidaati
"""
import itertools
import math
import os

import numpy as np
import pandas as pd

import cot_engine as E

DATA = E.DATA
JUUR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

VALUUTAD = E.VALUUTAD                       # USD EUR GBP JPY CHF CAD AUD NZD
LOOKBACK_N = 4                              # nadalat  — PRIMARY
HOID_N = 4                                  # nadalat  — PRIMARY
HOID_PAEVI = 20                             # 4 nadalat kauplemispaevades
N_PERM = 500
SEEME = 20260916

# Poliitikamaarad on noteeritud 3 kohaga (0.375, -0.75, 4.35). IEEE-754
# lahutamine jatab muutumatu vahe korral jaagi suurusjargus 1e-16, mille
# sign() teeb ekslikult +-1 signaaliks. Diagnostika leidis 24 sellist
# "tehingut" (|CHANGE_D| = 1.1e-16), mis andsid keskmiselt +128.93 bp.
# TOLERANTS on numbriline korrektsus, mitte filtreerimine: 1e-9 on
# vaiksem kui ukski tegelik maaramuutus (vaikseim on 0.05 pp).
TOLERANTS = 1e-9

TRAIN_LOPP = pd.Timestamp("2020-12-31")
VALID_LOPP = pd.Timestamp("2023-12-31")

KULU_TASEMED = [0.0, 0.5, 1.0, 1.25, 1.5, 2.0]   # uhesuunaline bp, tundlikkus

USD_JALG = {"EUR": ("EURUSD", False), "GBP": ("GBPUSD", False),
            "AUD": ("AUDUSD", False), "NZD": ("NZDUSD", False),
            "JPY": ("USDJPY", True), "CHF": ("USDCHF", True),
            "CAD": ("USDCAD", True)}


def paarid_28():
    """
    Koik 28 unikaalset paari 8 valuutast.

    ORIENTATSIOON: seitsme majori puhul kasutatakse TURUKONVENTSIOONI
    (EURUSD, mitte USDEUR; USDJPY, mitte JPYUSD), sest kulutabel
    cot_engine.KULU_BASE on selles orientatsioonis. Ristidel jaab
    esimene esinemine. Orientatsioon ei muuda testi sisu — signaal ja
    tootlus poorduvad koos —, kuid ta MUUDAB kulu, ja vale orientatsioon
    annaks majoritele risti kulu 2.2 bp asemel 1.0-1.8 bp.
    Audit D1 kontrollib seda.
    """
    out = []
    for b, q in itertools.combinations(VALUUTAD, 2):
        out.append((q + b) if (q + b) in E.KULU_BASE else (b + q))
    return out


def kulu_bp(paar):
    return E.KULU_BASE.get(paar, E.KULU_RIST)


# ------------------------------------------------------------- HINNAD -----
def _ohlc(sym, sufiks="_d25"):
    p = os.path.join(DATA, f"{sym}{sufiks}.csv")
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    return d[["open", "close"]].apply(pd.to_numeric, errors="coerce").dropna()


def valuuta_vaartused(sufiks="_d25"):
    """
    1 uhiku valuuta vaartus USD-des, AVA- ja SULGEMISHINNAL. USD = 1.0.
    Ainult ristuv kuupaevavahemik, et paarid oleksid sunkroonsed.
    """
    o, c = {}, {}
    for val, (sym, poord) in USD_JALG.items():
        d = _ohlc(sym, sufiks)
        o[val] = (1.0 / d["open"]) if poord else d["open"]
        c[val] = (1.0 / d["close"]) if poord else d["close"]
    ix = None
    for s in c.values():
        ix = s.index if ix is None else ix.intersection(s.index)
    O = pd.DataFrame({v: s.reindex(ix) for v, s in o.items()})
    C = pd.DataFrame({v: s.reindex(ix) for v, s in c.items()})
    O["USD"] = 1.0
    C["USD"] = 1.0
    O, C = O[VALUUTAD].dropna(), C[VALUUTAD].dropna()
    # Yahoo FX-seerias on horeda kauplemisega PUHAPAEVASED osabaarid
    # (turg avaneb ~21-22 UTC puhapaeval). Need ei ole taisbaarid ja nad
    # rikuvad nii nadala vaatluspaeva valikut kui ka "20 kauplemispaeva"
    # sammu. Audit E5/E6 leidis selle ENNE tulemuste arvutamist.
    # Eemaldatakse laupaevad ja puhapaevad.
    argi = O.index.dayofweek <= 4
    return O[argi], C[C.index.dayofweek <= 4]


def paari_hind(M, paar):
    """P = V_baas / V_kvoot. USDJPY = 1 / (1/USDJPY) — orientatsioon kontrollitud."""
    return M[paar[:3]] / M[paar[3:]]


# -------------------------------------------------------------- MAARAD ----
def maarad_paevas(hinna_ix):
    """
    BIS kuu lopu maarad, NIHUTATUD 1 kuu (kuu M maar kehtib kuus M+1),
    seejarel ffill paevasele indeksile. TAPSELT v6_carry.py reegel.

    See on konservatiivne: paris bot teaks maara muutust kohe, kui
    keskpank selle valja kuulutab; siin teab ta seda alles jargmise kuu
    algusest.
    """
    R = pd.read_csv(os.path.join(DATA, "policy_rates.csv"))
    R["Month"] = pd.to_datetime(R["Month"] + "-01")
    R = R.set_index("Month").sort_index()
    R = R.shift(1)                              # LOOKAHEAD-KAITSE
    paevad = pd.date_range(R.index[0], hinna_ix[-1], freq="D")
    Rd = R.reindex(paevad).ffill()
    return Rd.reindex(hinna_ix).ffill()[VALUUTAD]


def diferentsiaal(Rd, paarid):
    """D(t) = R_baas(t) - R_kvoot(t), % aastas."""
    return pd.DataFrame({p: Rd[p[:3]] - Rd[p[3:]] for p in paarid},
                        index=Rd.index)


# ------------------------------------------------------------- SIGNAAL ----
def nadala_vaatlused(ix):
    """
    Iga ISO-nadala VIIMANE kauplemispaev (reede, pyha korral neljapaev).
    Nadalavahetuse baarid on juba valuuta_vaartused'es eemaldatud.
    """
    s = pd.Series(ix, index=ix)
    nad = s.index.isocalendar()
    grp = nad["year"].astype(str) + "-" + nad["week"].astype(str)
    return pd.DatetimeIndex(s.groupby(grp.values).last().sort_values().values)


def tehingud(O, C, D, paarid, lookback=LOOKBACK_N, hoid_paevi=HOID_PAEVI,
             signaal_alus="CHANGE", mark=+1):
    """
    Uks rida = uks tehing.

    signaal_alus  CHANGE = sign(D(t) - D(t - lookback nadalat))   PRIMARY
                  LEVEL  = sign(D(t))                             kontroll
    mark          +1 primary, -1 poordkontroll (ei ole live-kandidaat)

    AJASTUS, rangelt pohjuslik:
      t       nadala viimane kauplemispaev; D(t) on selleks hetkeks teada
              (BIS kuu lopu maar, nihutatud 1 kuu)
      sisse   JARGMISE kauplemispaeva AVAHIND
      valja   hoid_paevi kauplemispaeva hiljem, AVAHIND
    """
    ix = C.index
    vaatlus = nadala_vaatlused(ix)
    pos = pd.Series(np.arange(len(ix)), index=ix)
    read = []
    for p in paarid:
        d = D[p]
        Pa = paari_hind(O, p)                # avahinnad
        for t in vaatlus:
            if t not in d.index or not np.isfinite(d.loc[t]):
                continue
            if signaal_alus == "CHANGE":
                t0 = t - pd.Timedelta(weeks=lookback)
                eel = d.loc[:t0]
                if len(eel) == 0 or not np.isfinite(eel.iloc[-1]):
                    continue
                sig_v = float(d.loc[t] - eel.iloc[-1])
            else:
                sig_v = float(d.loc[t])
            if abs(sig_v) < TOLERANTS:
                continue                      # muutust EI OLE (vt TOLERANTS)
            s = int(np.sign(sig_v)) * mark
            i = int(pos.loc[t])
            if i + 1 + hoid_paevi >= len(ix):
                continue
            p_in, p_out = Pa.iloc[i + 1], Pa.iloc[i + 1 + hoid_paevi]
            if not (np.isfinite(p_in) and np.isfinite(p_out)
                    and p_in > 0 and p_out > 0):
                continue
            read.append((p, t, ix[i + 1], ix[i + 1 + hoid_paevi], sig_v, s,
                         s * float(np.log(p_out / p_in)), kulu_bp(p)))
    T = pd.DataFrame(read, columns=["paar", "vaatlus", "sisse", "valja",
                                    "signaal_vaartus", "suund", "bruto",
                                    "kulu_1suund_bp"])
    T["kulu"] = 2.0 * T["kulu_1suund_bp"] / 1e4
    T["neto"] = T["bruto"] - T["kulu"]
    return T.sort_values(["vaatlus", "paar"]).reset_index(drop=True)


# ---------------------------------------------------------- STATISTIKA ----
def moot(x, kulu=None):
    """
    Tehingupohised moodikud. TAHELEPANEK: siin EI arvutata maxDD-d.
    Tehingud on KATTUVAD (iga nadal avatakse uus 4-nadalane positsioon),
    seega nende jarjestikune korrutamine EI OLE aktsiakover ja annaks
    tolgendamatu -99% arvu. Drawdown arvutatakse ainult mittekattuvatel
    kohortidel, vt kohordid().
    """
    x = np.asarray(x, float)
    x = x[np.isfinite(x)]
    if len(x) < 20:
        return None
    sd = x.std(ddof=1)
    t = float(x.mean() / sd * math.sqrt(len(x))) if sd > 0 else 0.0
    d = dict(n=len(x), bruto_bp=1e4 * float(x.mean()),
             med_bp=1e4 * float(np.median(x)), wr=100.0 * float((x > 0).mean()),
             sd_bp=1e4 * float(sd), t=t, p=E.p_kahepoolne(t))
    d["neto_bp"] = (d["bruto_bp"] - 1e4 * float(np.mean(kulu))
                    if kulu is not None else np.nan)
    return d


def kohordid(T, veerg="neto", hoid=HOID_N):
    """
    MITTEKATTUVAD kohordid. Iga nadal avatakse uus 4-nadalane korv, seega
    korraga on avatud 4 korvi. Uks kohort = iga 4. vaatlusnadal => tema
    positsioonid ei kattu omavahel ja tema tootluste korrutis ON paris
    aktsiakover.

    Faasi EI VALITA tulemuse jargi: koik 4 faasi arvutatakse ja
    raporteeritakse nende keskmine ning vahemik.
    """
    nad = T.groupby("vaatlus")[veerg].mean().sort_index()
    out = []
    for faas in range(hoid):
        y = nad.iloc[faas::hoid]
        if len(y) < 10:
            continue
        eq = np.cumprod(1.0 + y.values)
        dd = 100.0 * float((eq / np.maximum.accumulate(eq) - 1).min())
        sd = y.std(ddof=1)
        out.append(dict(faas=faas, n=len(y), keskm_bp=1e4 * float(y.mean()),
                        kum=float(eq[-1] - 1.0), maxdd=dd,
                        sharpe=(float(y.mean() / sd * math.sqrt(52.0 / hoid))
                                if sd > 0 else np.nan)))
    return pd.DataFrame(out)


def portfell_nadalas(T, veerg="neto"):
    """Vordkaaluline portfell: iga vaatlusnadala keskmine tehingutootlus."""
    return T.groupby("vaatlus")[veerg].mean()


def sharpe_aastas(s, per_aastas=52.0, hoid=HOID_N):
    """
    Kattuvad positsioonid: nadalas avatakse uus 4-nadalane positsioon.
    Sharpe arvutatakse MITTEKATTUVATEL loikudel (iga 4. nadal), et
    autokorrelatsioon ei paisutaks t-d.
    """
    x = np.asarray(s.dropna(), float)
    if len(x) < 30:
        return np.nan
    y = x[::hoid]
    if len(y) < 10 or y.std(ddof=1) == 0:
        return np.nan
    return float(y.mean() / y.std(ddof=1) * math.sqrt(per_aastas / hoid))


PAIS = (f"{'test':<28s}{'n':>7s}{'bruto':>9s}{'med':>8s}{'neto':>8s}"
        f"{'wr%':>7s}{'sd_bp':>8s}{'t':>7s}{'p':>8s}")


def rida(nimi, m, w=28):
    if m is None:
        return f"{nimi:<{w}s}      (alla 20 tehingu)"
    return (f"{nimi:<{w}s}{m['n']:>7d}{m['bruto_bp']:>+9.2f}{m['med_bp']:>+8.2f}"
            f"{m.get('neto_bp', np.nan):>+8.2f}{m['wr']:>7.1f}"
            f"{m['sd_bp']:>8.1f}{m['t']:>7.2f}{m['p']:>8.3f}")
