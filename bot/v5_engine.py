"""
v5_engine.py — NEMSIS v5 edge discovery raamistik.

ERINEVUS v4-st: v4 kusis "milline strateegia tootab EURUSD-l". v5 kusib
"milline NAHTUS esineb mitmel soltumatul paaril". Seetottu on siin
keskmes VALUUTA, mitte paar.

PHASE 5 — ANDMEJAOTUS (fikseeritud, ei muudeta kunagi):
  TRAIN       2016-09-12 .. 2021-12-31   (huopoteeside loomine)
  VALIDATION  2022-01-01 .. 2024-12-31   (parameetrite valik)
  FINAL OOS   2025-01-01 .. 2026-09-11   (EI KASUTATA loomisel ega valikul)

PHASE 6 — KULUMUDEL, kolm taset. Kui serv kaob LOW -> BASE juures,
margitakse FRAGILE.

PHASE 4 — iga huopotees registreeritakse ENNE testimist (vt v5_registry.py).
"""
import os, math
import numpy as np, pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

TRAIN_LOPP = pd.Timestamp("2021-12-31")
VALID_LOPP = pd.Timestamp("2024-12-31")

# 8 valuutat, mille tugevust saab tuletada olemasolevatest paaridest
VALUUTAD = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "NZD", "CAD"]

# paar -> (baas, kvoot). EURUSD = mitu USD uhe EUR eest => baas EUR
PAARID = {
    "EURUSD": ("EUR", "USD"), "GBPUSD": ("GBP", "USD"),
    "AUDUSD": ("AUD", "USD"), "NZDUSD": ("NZD", "USD"),
    "USDJPY": ("USD", "JPY"), "USDCHF": ("USD", "CHF"),
    "USDCAD": ("USD", "CAD"), "EURJPY": ("EUR", "JPY"),
}

# Uhesuunaline kulu baaspunktides, kolm taset (PHASE 6)
KULU = {
    "LOW":  {"EURUSD":.35,"GBPUSD":.40,"AUDUSD":.45,"NZDUSD":.60,
             "USDJPY":.35,"USDCHF":.45,"USDCAD":.45,"EURJPY":.55},
    "BASE": {"EURUSD":1.0,"GBPUSD":1.2,"AUDUSD":1.2,"NZDUSD":1.8,
             "USDJPY":1.0,"USDCHF":1.3,"USDCAD":1.3,"EURJPY":1.5},
    "HIGH": {"EURUSD":2.0,"GBPUSD":2.4,"AUDUSD":2.4,"NZDUSD":3.6,
             "USDJPY":2.0,"USDCHF":2.6,"USDCAD":2.6,"EURJPY":3.0},
}


def lae(sym, veerg="close"):
    p = os.path.join(DATA, f"{sym}_d.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    for c in ("open", "high", "low", "close"):
        if c in d.columns:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    return d.dropna()


def paarid_df():
    """{paar: OHLC DataFrame}, ainult ristuv ajavahemik."""
    out = {}
    for p in PAARID:
        d = lae(p)
        if d is not None and len(d) > 1500:
            out[p] = d
    ix = None
    for d in out.values():
        ix = d.index if ix is None else ix.intersection(d.index)
    return {k: v.reindex(ix).dropna() for k, v in out.items()}, ix


def valuuta_tootlused(P):
    """
    PHASE 2C — LATENTNE VALUUTATUGEVUS.

    Iga paar annab uhe vorrandi: log(baas) - log(kvoot) = log(paari tootlus).
    8 valuutat, 8 paari => ulemaaratud susteem. Lahendame vahimruutude
    meetodil, lisades kitsenduse "summa = 0" (ainult SUHTELINE tugevus on
    tuvastatav, absoluutne mitte).

    Tagastab DataFrame: paev x valuuta, iga lahtris selle valuuta
    paevatootlus vastu valuutakorvi keskmist.
    """
    r = {p: np.log(d["close"]).diff() for p, d in P.items()}
    R = pd.DataFrame(r).dropna()
    n = len(VALUUTAD)
    idx = {c: i for i, c in enumerate(VALUUTAD)}
    A = np.zeros((len(PAARID) + 1, n))
    for j, (p, (b, q)) in enumerate(PAARID.items()):
        A[j, idx[b]] = 1.0
        A[j, idx[q]] = -1.0
    A[-1, :] = 1.0                      # kitsendus: summa = 0
    pinv = np.linalg.pinv(A)
    Y = np.column_stack([R[p].values for p in PAARID] + [np.zeros(len(R))])
    S = Y @ pinv.T
    return pd.DataFrame(S, index=R.index, columns=VALUUTAD)


def carry_diff():
    """
    PHASE 2I — intressivahe ETF-idest (adjclose, dividendid sees).

    PIIRANG, mis on MOODETUD ja mida ei tohi varjata: absoluutne tase on
    nihkes (uhtlane ~+3% ule koigi valuutade, tuleneb ETF-i ja Yahoo
    spot-seeria erinevast sulgemisajast). JARJESTUS kattub paris
    keskpankade maaradega. Seetottu kasutame AINULT ristloikelist
    jarjestust, kus uhtlane nihe taandub.
    """
    ETF = {"EUR":"FXEA","GBP":"FXBA","JPY":"FXYA",
           "AUD":"FXAA","CHF":"FXFA","CAD":"FXCA"}
    SPOT = {"EUR":("EURUSD",False),"GBP":("GBPUSD",False),
            "JPY":("USDJPY",True),"AUD":("AUDUSD",False),
            "CHF":("USDCHF",True),"CAD":("USDCAD",True)}
    out = {}
    for v, ef in ETF.items():
        e = lae(ef)
        s = lae(SPOT[v][0])
        if e is None or s is None:
            continue
        ec, sc = e["close"], s["close"]
        if SPOT[v][1]:
            sc = 1.0 / sc
        ix = ec.index.intersection(sc.index)
        out[v] = (ec.reindex(ix).pct_change() - sc.reindex(ix).pct_change())
    C = pd.DataFrame(out).dropna()
    C["USD"] = 0.0                       # baasvaluuta
    C["NZD"] = np.nan                    # ETF puudub
    return C


def jaota(x):
    """Tagastab (train, validation, final_oos) ajaliselt."""
    return (x[x.index <= TRAIN_LOPP],
            x[(x.index > TRAIN_LOPP) & (x.index <= VALID_LOPP)],
            x[x.index > VALID_LOPP])


def sharpe(x, per_aastas=252):
    x = np.asarray(x, dtype=float); x = x[np.isfinite(x)]
    if len(x) < 60 or x.std() == 0:
        return 0.0
    return float(x.mean() / x.std() * math.sqrt(per_aastas))


def deflated_sharpe(sh, n_obs, n_katseid, skew=0.0, kurt=3.0):
    """
    Bailey & Lopez de Prado deflated Sharpe. Korrigeerib SELLE JARGI,
    mitu strateegiat on katsetatud — tapselt see, mida 11 500 testi jarel
    vaja on.
    """
    if n_obs < 60 or n_katseid < 1:
        return 0.0
    from math import sqrt, log, exp, pi
    try:
        from scipy.stats import norm
    except Exception:
        return float("nan")
    e = 0.5772156649
    # oodatav MAKSIMAALNE Sharpe n_katseid soltumatust juhuslikust katsest
    sh_max = (norm.ppf(1 - 1.0/n_katseid) * (1 - e)
              + norm.ppf(1 - 1.0/(n_katseid * exp(1))) * e)
    sd = sqrt((1 - skew*sh + (kurt-1)/4.0*sh**2) / (n_obs - 1))
    if sd <= 0:
        return 0.0
    return float(norm.cdf((sh - sh_max) / sd))


def moodikud(x, nimi="", kulu_aasta=0.0):
    """PHASE 8 — kapitali efektiivsus, mitte ainult kasum."""
    x = np.asarray(x, dtype=float); x = x[np.isfinite(x)]
    if len(x) < 60:
        return None
    eq = np.cumprod(1 + x)
    dd = float((eq / np.maximum.accumulate(eq) - 1).min())
    v, k = x[x > 0], x[x <= 0]
    aastaid = len(x) / 252
    return dict(
        nimi=nimi, n=len(x), keskm=float(x.mean()), sh=sharpe(x),
        sortino=float(x.mean()/k.std()*math.sqrt(252)) if len(k) and k.std()>0 else 0.0,
        kokku=float(eq[-1] - 1),
        cagr=float(eq[-1]**(1/aastaid) - 1) if aastaid > 0 else 0.0,
        maxdd=dd, taastumis=float((eq[-1]-1)/abs(dd)) if dd < 0 else np.inf,
        pf=float(v.sum()/abs(k.sum())) if len(k) and k.sum() != 0 else np.inf,
        wr=100*float((x > 0).mean()),
        tstat=float(x.mean()/x.std()*math.sqrt(len(x))) if x.std() > 0 else 0.0)
