"""
cal_engine.py — MAJANDUSKALENDRI "SURPRISE" MOOTOR (NEMSIS B1).

KUSIMUS: kas makroteate actual-vs-forecast ullatus annab FX-is korduva,
kaubeldava infoeelise?

TAHTIS — UURIMISKOOD. Ei puuduta live-faile (main_v4.py, config.py,
mt5_connector.py, strategy_meanrev.py, backtest.py).

-----------------------------------------------------------------------------
ANDMEALLIKAS
-----------------------------------------------------------------------------
TradingView economic calendar API
  https://economic-calendar.tradingview.com/events?from=...&to=...&countries=...
Taksonoomia parineb Trading Economics'ilt (standarditud indikaatorinimed).
Tasuta, ilma API-votmeta. Paring noab Origin/Referer paist; liivakastil
ei ole otseuhendust (agent-proxy 000/403), seega paring kaib kasutaja
Supabase `http` laienduse kaudu (funktsioon fetch_hdr + load_cal).

Valjad: date (ISO UTC = AVALDAMISE hetk), country, currency, title,
indicator, period, actual/forecast/previous (vormindatud) ning
actualRaw/forecastRaw/previousRaw (numbrilised), importance.

MOODETUD KATVUS (bot/data/econ_cal.csv):
  37 595 sundmust, millel on NII actual KUI forecast
  8 valuutat (USD EUR GBP JPY CHF CAD AUD NZD)
  265 indikaatorit
  2013-01-23 .. 2026-09-15

PIIRANG, MIDA EI VARJATA: see allikas EI ANNA andmeid enne 2013. Paringud
2006/2008/2010/2011/2012 kohta tagastavad {"status":"no_data"}. Seega
B1 valim on 13.6 aastat, MITTE 2008-2026 nagu soovitud.

TEINE PIIRANG: allikas ei utle, kas `actual` on ESIALGNE trukk voi
hiljem REVIDEERITUD vaartus. Seda ei saa sellest API-st kontrollida.
Riski maandame kahel viisil: (1) sisenemine toimub tunde parast teadet,
(2) raporteerime tundlikkuse sisenemisviivitusele.

-----------------------------------------------------------------------------
LOOKAHEAD-KAITSE
-----------------------------------------------------------------------------
T = release timestamp (UTC).

PAEVANE test: eeldame, et paevase baari sulgemine on 21:00 UTC.
  sisenemine = esimene paevabaar D, mille (D 21:00 UTC) > T
  => teade kell 12:30 UTC -> sisenemine SAMA paeva sulgemisel (~8.5 h hiljem)
  => teade kell 23:50 UTC -> sisenemine JARGMISE paeva sulgemisel
  21:00 on tahtlikult VARASEM kui Yahoo tegelik sulgemine => konservatiivne.

H1 test: sisenemine = esimene H1 baar, mis ALGAB hetkel >= T, selle baari
  SULGEMISHIND. Teade 12:30 -> baar 13:00 sulgeb 14:00 => sisenemine
  1.5 h parast teadet. Vahemalt uks tais tund PARAST teadet.

Uhtegi hinda ega uhtegi kalendrivalja EI kasutata enne T-d.

-----------------------------------------------------------------------------
EELREGISTREERITUD DEFINITSIOONID (kirjas ENNE esimest jooksu)
-----------------------------------------------------------------------------
ullatus:
    e = actual - forecast
    z = e / std(viimase AKEN sama (valuuta, indikaator) sundmuse e-st,
             ainult MINEVIK, min MIN_N vaatlust)
    AKEN = 20, MIN_N = 10.  Fikseeritud, mitte tulemuste jargi valitud.
    Full-sample standardiseerimist EI KASUTATA.

suund: iga indikaator kannab EELREGISTREERITUD majandusliku margi.
    +1 = korgem kui oodatud => valuuta TUGEVNEB
    -1 = korgem kui oodatud => valuuta NORGENEB (tootus, toetusnoduded)
    Margid tulevad majandusteooriast, MITTE tulemustest.

valuuta tootlus: V[c] = 1 uhiku c vaartus USD-des (7 USD-paarist).
    r_c = log-muut V[c]-s MIINUS ristloikeline keskmine
    => turuneutraalne, ja USD saab sisulise tootluse.

hupoteesid:
    A  z >= +1  => osta valuuta (marki arvestades)
    B  z <= -1  => muu valuuta (marki arvestades)
    C  |z| (magnituud) — kirjeldav: kas ennustab liikumise SUURUST

horisondid: paevane 1d / 2d / 5d;  H1 1h / 4h / 24h. Ainult need.
"""
import math
import os

import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

AKEN = 20
MIN_N = 10
LAVI = 1.0                 # |z| lavi hupoteesidele A ja B
PAEVA_SULG_UTC = 21        # eeldatav paevabaari sulgemisaeg
VALUUTAD = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD"]

# TIER 1 — majanduslikult koige tahtsamad, mark uheselt selge
TIER1 = {
    "Inflation Rate": +1, "Core Inflation Rate": +1, "Inflation Rate Mom": +1,
    "Unemployment Rate": -1,
    "GDP Growth Rate": +1, "GDP Annual Growth Rate": +1,
    "Retail Sales MoM": +1, "Retail Sales YoY": +1,
    "Interest Rate": +1,
    "Employment Change": +1, "Non Farm Payrolls": +1,
}
# TIER 2 — tahtsuselt jargmised
TIER2 = {
    "Producer Price Inflation MoM": +1, "Producer Prices Change": +1,
    "Consumer Confidence": +1, "Business Confidence": +1,
    "Industrial Production Mom": +1, "Industrial Production": +1,
    "Current Account": +1, "Balance of Trade": +1,
    "Building Permits MoM": +1, "House Price Index MoM": +1,
    "Wage Growth": +1, "Leading Economic Index": +1,
    "Labor Force Participation Rate": +1,
}
MARGID = dict(TIER1, **TIER2)

# kulud: uhesuunaline bp, sama tase mis v5_engine/cot_engine KULU["BASE"]
KULU_1SUUND_BP = 1.25      # 7 USD-paari keskmine (1.0-1.8)

TRAIN_LOPP = pd.Timestamp("2017-12-31")
VALID_LOPP = pd.Timestamp("2020-12-31")


# ---------------------------------------------------------------- andmed ---
def lae_kalender(tasemed=("T1", "T2")):
    d = pd.read_csv(os.path.join(DATA, "econ_cal.csv"), parse_dates=["ts"])
    d = d[d["cur"].isin(VALUUTAD)]
    lubatud = {}
    if "T1" in tasemed:
        lubatud.update(TIER1)
    if "T2" in tasemed:
        lubatud.update(TIER2)
    d = d[d["indicator"].isin(lubatud)].copy()
    d["mark"] = d["indicator"].map(lubatud)
    d["tier"] = np.where(d["indicator"].isin(TIER1), "T1", "T2")
    return d.sort_values("ts").reset_index(drop=True)


def lae_hind(sym, sufiks="_d25"):
    p = os.path.join(DATA, f"{sym}{sufiks}.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    return pd.to_numeric(d["close"], errors="coerce").dropna()


USD_LEG = {"EUR": ("EURUSD", False), "GBP": ("GBPUSD", False),
           "AUD": ("AUDUSD", False), "NZD": ("NZDUSD", False),
           "JPY": ("USDJPY", True), "CHF": ("USDCHF", True),
           "CAD": ("USDCAD", True)}


def valuuta_vaartused(sufiks="_d25"):
    """1 uhiku valuuta vaartus USD-des; USD = 1.0. Ainult ristuv aken."""
    v = {}
    for c, (sym, inv) in USD_LEG.items():
        s = lae_hind(sym, sufiks)
        if s is None:
            continue
        v[c] = (1.0 / s) if inv else s
    ix = None
    for s in v.values():
        ix = s.index if ix is None else ix.intersection(s.index)
    out = {c: s.reindex(ix) for c, s in v.items()}
    out["USD"] = pd.Series(1.0, index=ix)
    return pd.DataFrame(out)[VALUUTAD].dropna()


def valuuta_tootlused(V, k):
    """k-sammuline log-tootlus, ristloikeliselt tsentreeritud (turuneutraalne)."""
    r = np.log(V).diff(k).shift(-k)          # t -> t+k, joondatud t peale
    return r.sub(r.mean(axis=1), axis=0)


# --------------------------------------------------------------- ullatus ---
def z_ullatus(d, aken=AKEN, min_n=MIN_N):
    """
    z = (actual - forecast) / rull-std(sama (valuuta, indikaator) varasemate
    prognoosivigade seast). AINULT MINEVIK: shift(1) enne rolling'ut.
    """
    d = d.copy()
    d["viga"] = d["actual"] - d["forecast"]
    g = d.groupby(["cur", "indicator"])["viga"]
    sd = g.transform(lambda s: s.shift(1).rolling(aken, min_periods=min_n).std())
    n = g.transform(lambda s: s.shift(1).rolling(aken, min_periods=1).count())
    d["sd"] = sd
    d["n_ajalugu"] = n
    d["z"] = d["viga"] / sd.replace(0.0, np.nan)
    return d


# -------------------------------------------------------------- ajastus ----
def paevane_sisenemine(ts, hinna_ix, sulg_utc=PAEVA_SULG_UTC, max_nihe=5):
    """
    Esimene paevabaar, mille sulgemine on PARAST teadet.
    Tagastab positsiooni hinna_ix sees voi -1.
    """
    hi = pd.DatetimeIndex(hinna_ix)
    sulg = hi + pd.Timedelta(hours=sulg_utc)
    pos = np.searchsorted(sulg.values, np.asarray(ts, dtype="datetime64[ns]"),
                          side="right")
    ok = (pos < len(hi))
    pos = np.where(ok, pos, -1)
    vahe = np.where(pos >= 0,
                    (hi.values[np.clip(pos, 0, len(hi) - 1)]
                     - np.asarray(ts, dtype="datetime64[ns]"))
                    / np.timedelta64(1, "D"), 99.0)
    return np.where((pos >= 0) & (vahe <= max_nihe), pos, -1)


def h1_sisenemine(ts, hinna_ix, max_tunde=48):
    """Esimene H1 baar, mis ALGAB hetkel >= T; sisenemine selle SULGEMISEL."""
    hi = pd.DatetimeIndex(hinna_ix)
    pos = np.searchsorted(hi.values, np.asarray(ts, dtype="datetime64[ns]"),
                          side="left")
    ok = pos < len(hi)
    pos = np.where(ok, pos, -1)
    vahe = np.where(pos >= 0,
                    (hi.values[np.clip(pos, 0, len(hi) - 1)]
                     - np.asarray(ts, dtype="datetime64[ns]"))
                    / np.timedelta64(1, "h"), 999.0)
    return np.where((pos >= 0) & (vahe <= max_tunde), pos, -1)


# ------------------------------------------------------------- statistika --
def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def p_kahepoolne(t):
    return 2.0 * (1.0 - ncdf(abs(t)))


def moodikud(x, nimi=""):
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 20:
        return None
    sd = x.std(ddof=1)
    v, k = x[x > 0], x[x <= 0]
    return dict(nimi=nimi, n=len(x), keskm_bp=float(x.mean() * 1e4),
                wr=100.0 * float((x > 0).mean()),
                v_bp=float(v.mean() * 1e4) if len(v) else 0.0,
                k_bp=float(k.mean() * 1e4) if len(k) else 0.0,
                pf=float(v.sum() / abs(k.sum())) if len(k) and k.sum() != 0 else float("inf"),
                t=float(x.mean() / sd * math.sqrt(len(x))) if sd > 0 else 0.0,
                sd_bp=float(sd * 1e4))


def jaota(ts):
    return (ts <= TRAIN_LOPP,
            (ts > TRAIN_LOPP) & (ts <= VALID_LOPP),
            ts > VALID_LOPP)
