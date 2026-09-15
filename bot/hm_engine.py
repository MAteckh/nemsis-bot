"""
hm_engine.py — NEMSIS HEAT MAP v1 mootor.

EESMARK: mootа PARIS ajaloolistel andmetel, milline strateegiaperekond
tootab millisel FX-paaril ja millises rezhiimis.

TAHTIS — UURIMISKOOD. Ei puuduta live-faile (main_v4.py, config.py,
mt5_connector.py, strategy_meanrev.py, backtest.py).

-----------------------------------------------------------------------------
ANDMED JA NENDE PIIRANGUD (mooedetud repost, mitte eeldatud)
-----------------------------------------------------------------------------
H1   15 paari, 2023-11-27 .. 2026-09-11  = 2.79 aastat, ~17 300 baari
M15  15 paari, 2026-06-22 .. 2026-09-11  = 81 PAEVA
D1   7 USD-paari paris seeriana 2006-05-15 .. 2026-09-10 (_d25),
     ristid arvutatakse USD-jalgadest (kontrollitud: sunteetiline EURJPY
     vs paris EURJPY mediaanviga 0.008%, tootluste korr 0.9946)

JARELDUS: soovitud jaotust TRAIN 2006-2013 / VALID 2014-2017 / OOS 2018-2026
EI OLE VOIMALIK 15-minutiliste ega tunniste andmetega — neid andmeid selles
repos lihtsalt EI OLE ja Yahoo tunniandmed ulatuvad ~730 paeva tagasi.
M15 (81 paeva) ei kanna uhtegi kolmeosalist jaotust.

Seetottu joostakse KAKS rada, molemad PARIS andmetel:

  RADA A (soovitud ajaraamid, luhike valim)
     sisenemised H1, rezhiimikontekst H4 (sama 1:4 suhe mis 15m:1H)
     2023-11-27 .. 2026-09-11, jaotus kronoloogiliselt kolmandikeks
  RADA B (soovitud jaotus, pikk valim)
     sisenemised D1, rezhiimikontekst W1 (nadal)
     2006-05-15 .. 2026-09-10, jaotus TRAIN 2006-2013 / VALID 2014-2017 /
     OOS 2018-2026 tapselt nagu kusitud

-----------------------------------------------------------------------------
EELREGISTREERITUD PARAMEETRID — EI OPTIMEERITUD UHELGI PERIOODIL
-----------------------------------------------------------------------------
EMA 20 / 50 / 200, ADX 14 (trend >= 25, range < 20), ATR 14,
Bollinger 20 / 2.0, RSI 14 (30/70 ekstreemid, 55/45 momentum),
Donchian 20, retest-aken 10 baari, SL = 1.5 x ATR,
TP = 2.0 R (MEAN_REVERSION 1.0 R, sest ta sihib keskmist),
max hoid 48 baari (H1) / 20 baari (D1), risk 1% kapitalist tehingu kohta.

Need on TAVAPARASED oppikirjanduse vaikevaartused. TRAIN-i peal EI TEHTUD
uhtegi parameetriotsingut — see on rangem kui "fitteeri TRAIN-il", sest
nii ei saa TRAIN-i ulesobitada isegi kogemata.

-----------------------------------------------------------------------------
LOOKAHEAD-KAITSE
-----------------------------------------------------------------------------
1. Signaal baaril i kasutab AINULT baare kuni i (kaasa arvatud).
2. Sisenemine JARGMISE baari AVAHINNAGA (i+1 open), mitte i sulgemisega.
3. SL/TP skaneeritakse alates baarist i+1.
4. Kui uhes baaris tabatakse NII SL kui TP, loetakse SL (konservatiivne).
5. Konteksti-indikaator on ALATI eelmiselt LOPETATUD konteksti-baarilt
   (shift(1) enne kaardistamist sisenemisbaaridele).
6. Korraga on avatud maksimaalselt UKS positsioon paari ja strateegia kohta.
"""
import math
import os

import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

PAARID = ["EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "NZDUSD", "USDCAD",
          "USDCHF", "EURGBP", "EURJPY", "GBPJPY", "AUDJPY", "EURCHF",
          "EURAUD", "GBPAUD", "AUDCAD"]
STRAT = ["TREND_PULLBACK", "BREAKOUT_RETEST", "MEAN_REVERSION", "MOMENTUM"]
REZIIMID = ["HIGH_VOLATILITY", "LOW_VOLATILITY", "TRENDING", "RANGING"]

# --- eelregistreeritud parameetrid ----------------------------------------
EMA_F, EMA_M, EMA_S = 20, 50, 200
ADX_N, ADX_TREND, ADX_RANGE = 14, 25.0, 20.0
ATR_N = 14
BB_N, BB_K = 20, 2.0
RSI_N = 14
RSI_LO, RSI_HI = 30.0, 70.0
RSI_MOM_LO, RSI_MOM_HI = 45.0, 55.0
DON_N, RETEST_AKEN = 20, 10
SL_ATR = 1.5
TP_R = {"TREND_PULLBACK": 2.0, "BREAKOUT_RETEST": 2.0,
        "MEAN_REVERSION": 1.0, "MOMENTUM": 2.0}
MAX_HOID = {"H1": 48, "D1": 20}
RISK = 0.01
VOL_AKEN = 500          # normaliseeritud ATR-i rullmediaan rezhiimi jaoks

# --- kulumudel: uhesuunaline bp, NEMSIS h1engine.KULU_RETAIL alusel -------
# Kolm risti (EURCHF, GBPAUD, AUDCAD) puuduvad originaalis; lisatud
# konservatiivselt sama skaala jargi (laiem kui major, kitsam kui egzoot).
KULU_BP = {
    "EURUSD": 1.0, "GBPUSD": 1.2, "USDJPY": 1.0, "AUDUSD": 1.2,
    "NZDUSD": 1.8, "USDCAD": 1.3, "USDCHF": 1.3, "EURGBP": 1.5,
    "EURJPY": 1.5, "GBPJPY": 1.8, "AUDJPY": 1.8, "EURCHF": 1.8,
    "EURAUD": 1.8, "GBPAUD": 2.2, "AUDCAD": 2.2,
}
SLIP_BP = 0.3           # libisemine uhe suuna kohta, lisaks spreadile

# --- jaotused --------------------------------------------------------------
JAOTUS_D1 = [("TRAIN", "2006-01-01", "2013-12-31"),
             ("VALID", "2014-01-01", "2017-12-31"),
             ("OOS",   "2018-01-01", "2026-12-31")]
JAOTUS_H1 = [("TRAIN", "2023-11-27", "2024-10-31"),
             ("VALID", "2024-11-01", "2025-08-31"),
             ("OOS",   "2025-09-01", "2026-12-31")]


# ---------------------------------------------------------------- andmed ---
def lae_h1(sym):
    p = os.path.join(DATA, f"{sym}_h1.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    d = d[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce").dropna()
    return d if len(d) > 2000 else None


USD_LEG = {"EUR": ("EURUSD", False), "GBP": ("GBPUSD", False),
           "AUD": ("AUDUSD", False), "NZD": ("NZDUSD", False),
           "JPY": ("USDJPY", True), "CHF": ("USDCHF", True),
           "CAD": ("USDCAD", True)}


def _d25(sym):
    p = os.path.join(DATA, f"{sym}_d25.csv")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
    d = d[~d.index.duplicated(keep="last")]
    d.columns = [c.strip().lower() for c in d.columns]
    return d[["open", "high", "low", "close"]].apply(pd.to_numeric, errors="coerce").dropna()


def lae_d1(sym):
    """
    Paevane OHLC. USD-paarid tulevad otse _d25 failist. Ristid arvutatakse
    USD-jalgadest: XY = (X/USD) / (Y/USD), iga OHLC-valja kohta eraldi.
    High/low on LIGIKAUDSED (kahe seeria high'de jagatis ei ole risti tegelik
    high), seetottu on RADA B tulemus veidi optimistlik SL/TP tabamuste osas.
    See on ausalt raporteeritud ja seepargi on RADA A (paris H1 ristid)
    primaarne ajaraam.
    """
    otse = _d25(sym)
    if otse is not None:
        return otse
    b, q = sym[:3], sym[3:]
    read = {}
    for c in (b, q):
        if c == "USD":
            read[c] = None
            continue
        s, inv = USD_LEG.get(c, (None, None))
        if s is None:
            return None
        d = _d25(s)
        if d is None:
            return None
        read[c] = (1.0 / d[["open", "low", "high", "close"]].rename(
            columns={"low": "high", "high": "low"})) if inv else d
    ix = None
    for d in read.values():
        if d is None:
            continue
        ix = d.index if ix is None else ix.intersection(d.index)
    out = {}
    for k in ("open", "high", "low", "close"):
        bv = pd.Series(1.0, index=ix) if read[b] is None else read[b][k].reindex(ix)
        qv = pd.Series(1.0, index=ix) if read[q] is None else read[q][k].reindex(ix)
        out[k] = bv / qv
    return pd.DataFrame(out).dropna()


# ----------------------------------------------------------- indikaatorid --
def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def atr(d, n=ATR_N):
    pc = d["close"].shift(1)
    tr = pd.concat([d["high"] - d["low"], (d["high"] - pc).abs(),
                    (d["low"] - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1.0 / n, adjust=False).mean()


def adx(d, n=ADX_N):
    up = d["high"].diff()
    dn = -d["low"].diff()
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    a = atr(d, n).replace(0, np.nan)
    pdi = 100 * pd.Series(plus, index=d.index).ewm(alpha=1.0/n, adjust=False).mean() / a
    mdi = 100 * pd.Series(minus, index=d.index).ewm(alpha=1.0/n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return dx.ewm(alpha=1.0 / n, adjust=False).mean()


def rsi(s, n=RSI_N):
    d = s.diff()
    up = d.clip(lower=0).ewm(alpha=1.0/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1.0/n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn.replace(0, np.nan))


def resample_ctx(d, reegel):
    o = d["open"].resample(reegel).first()
    h = d["high"].resample(reegel).max()
    l = d["low"].resample(reegel).min()
    c = d["close"].resample(reegel).last()
    return pd.DataFrame({"open": o, "high": h, "low": l, "close": c}).dropna()


def kontekst(d, reegel):
    """
    Konteksti-indikaatorid, kaardistatud sisenemisbaaridele nii, et
    kasutatakse AINULT eelmist LOPETATUD konteksti-baari (shift(1)).
    """
    c = resample_ctx(d, reegel)
    k = pd.DataFrame(index=c.index)
    k["ema_m"] = ema(c["close"], EMA_M)
    k["ema_s"] = ema(c["close"], EMA_S)
    k["adx"] = adx(c)
    k["natr"] = atr(c) / c["close"]
    k = k.shift(1)                       # ainult lopetatud baar
    return k.reindex(d.index, method="ffill")


# ----------------------------------------------------------- strateegiad --
def signaalid(d, k, nimi):
    """
    Tagastab Series {-1,0,+1} — signaal baaril i, kasutades AINULT baare
    kuni i. Sisenemine toimub hiljem baari i+1 AVAHINNAGA.
    """
    c, h, l = d["close"], d["high"], d["low"]
    e20, e50 = ema(c, EMA_F), ema(c, EMA_M)
    r = rsi(c)
    tousev = (k["ema_m"] > k["ema_s"])
    langev = (k["ema_m"] < k["ema_s"])
    trend = k["adx"] >= ADX_TREND
    rng = k["adx"] < ADX_RANGE
    s = pd.Series(0, index=d.index, dtype=int)

    if nimi == "TREND_PULLBACK":
        # kontekst annab suuna ja trendi, sisenemisbaar annab tagasitoumbe
        pikk = tousev & trend & (l <= e20) & (c > e20) & (c > c.shift(1))
        luhike = langev & trend & (h >= e20) & (c < e20) & (c < c.shift(1))
        s[pikk] = 1
        s[luhike] = -1

    elif nimi == "BREAKOUT_RETEST":
        hi20 = h.rolling(DON_N).max().shift(1)
        lo20 = l.rolling(DON_N).min().shift(1)
        murd_yles = (c > hi20)
        murd_alla = (c < lo20)
        # tase, mis viimati labi murti, ja mitu baari sellest on moodas
        tase_y = hi20.where(murd_yles).ffill()
        vanus_y = (~murd_yles).groupby(murd_yles.cumsum()).cumcount()
        tase_a = lo20.where(murd_alla).ffill()
        vanus_a = (~murd_alla).groupby(murd_alla.cumsum()).cumcount()
        pikk = (murd_yles.cumsum() > 0) & (vanus_y.between(1, RETEST_AKEN)) & \
               (l <= tase_y) & (c > tase_y)
        luhike = (murd_alla.cumsum() > 0) & (vanus_a.between(1, RETEST_AKEN)) & \
                 (h >= tase_a) & (c < tase_a)
        s[pikk.fillna(False)] = 1
        s[luhike.fillna(False)] = -1

    elif nimi == "MEAN_REVERSION":
        mid = c.rolling(BB_N).mean()
        sd = c.rolling(BB_N).std(ddof=0)
        alumine, ulemine = mid - BB_K * sd, mid + BB_K * sd
        pikk = rng & (c < alumine) & (r < RSI_LO)
        luhike = rng & (c > ulemine) & (r > RSI_HI)
        s[pikk] = 1
        s[luhike] = -1

    elif nimi == "MOMENTUM":
        pikk = tousev & (r > RSI_MOM_HI) & (r.shift(1) <= RSI_MOM_HI) & (c > e20)
        luhike = langev & (r < RSI_MOM_LO) & (r.shift(1) >= RSI_MOM_LO) & (c < e20)
        s[pikk] = 1
        s[luhike] = -1

    else:
        raise ValueError(nimi)
    return s.fillna(0).astype(int)


def rezhiim_sildid(d, k):
    """
    Rezhiim signaali hetkel, AINULT eelmisest lopetatud konteksti-baarist.
    Neli silti KATTUVAD (tehing voib olla korraga HIGH_VOL ja TRENDING) —
    nii on kusitud ja nii ka raporteeritakse.
    """
    natr = k["natr"]
    med = natr.rolling(VOL_AKEN, min_periods=100).median()
    return pd.DataFrame({
        "HIGH_VOLATILITY": natr > med,
        "LOW_VOLATILITY": natr <= med,
        "TRENDING": k["adx"] >= ADX_TREND,
        "RANGING": k["adx"] < ADX_RANGE,
    }, index=d.index).fillna(False)


# --------------------------------------------------------- simulatsioon ---
def simuleeri(d, k, nimi, tf, kulu_bp, slip_bp=SLIP_BP):
    """
    Uks positsioon korraga. Sisenemine i+1 avahinnaga, SL/TP skaneeritakse
    alates i+1. Kui uhes baaris tabatakse molemad, loetakse SL.
    Tagastab DataFrame tehingutest.
    """
    sg = signaalid(d, k, nimi).values
    a = atr(d).values
    o, h, l, c = (d[x].values for x in ("open", "high", "low", "close"))
    idx = d.index
    rez = rezhiim_sildid(d, k)
    maxh = MAX_HOID[tf]
    tp_r = TP_R[nimi]
    n = len(d)
    kulu_uks = (kulu_bp + slip_bp) / 1e4      # uhesuunaline, osakaaluna
    read = []
    i = 0
    while i < n - 2:
        if sg[i] == 0 or not np.isfinite(a[i]) or a[i] <= 0:
            i += 1
            continue
        suund = sg[i]
        j = i + 1                              # sisenemisbaar
        sisse = o[j]
        if not np.isfinite(sisse) or sisse <= 0:
            i += 1
            continue
        sl_d = SL_ATR * a[i]
        if sl_d <= 0:
            i += 1
            continue
        sl = sisse - suund * sl_d
        tp = sisse + suund * tp_r * sl_d
        valja, pohjus, lopp = None, None, None
        for t in range(j, min(j + maxh, n)):
            if suund > 0:
                if l[t] <= sl:
                    valja, pohjus, lopp = sl, "SL", t
                    break
                if h[t] >= tp:
                    valja, pohjus, lopp = tp, "TP", t
                    break
            else:
                if h[t] >= sl:
                    valja, pohjus, lopp = sl, "SL", t
                    break
                if l[t] <= tp:
                    valja, pohjus, lopp = tp, "TP", t
                    break
        if valja is None:
            lopp = min(j + maxh - 1, n - 1)
            valja, pohjus = c[lopp], "AEG"
        bruto_r = suund * (valja - sisse) / sl_d
        kulu_r = 2.0 * kulu_uks * sisse / sl_d      # sisse + valja
        read.append(dict(
            aeg=idx[j], lopuaeg=idx[lopp], strateegia=nimi, suund=int(suund),
            sisse=sisse, valja=valja, sl=sl, tp=tp, pohjus=pohjus,
            baare=int(lopp - j + 1), bruto_r=bruto_r, kulu_r=kulu_r,
            neto_r=bruto_r - kulu_r,
            **{c2: bool(rez[c2].iloc[i]) for c2 in REZIIMID}))
        i = lopp + 1                            # uks positsioon korraga
    return pd.DataFrame(read)


# ------------------------------------------------------------ statistika --
def stat(t, aastaid, risk=RISK):
    """Tehingute nimekirjast moodikud. R-uhikutes ja 1%-riski equity peal."""
    if t is None or len(t) == 0:
        return None
    b = t["bruto_r"].values
    x = t["neto_r"].values
    v, k = x[x > 0], x[x <= 0]
    eq = np.cumprod(1 + risk * x)
    dd = float((eq / np.maximum.accumulate(eq) - 1).min())
    sd = x.std(ddof=1) if len(x) > 1 else 0.0
    teh_a = len(x) / aastaid if aastaid > 0 else np.nan
    return dict(
        n=len(x), wr=100.0 * float((x > 0).mean()),
        bruto_r=float(b.sum()), neto_r=float(x.sum()),
        oodatav=float(x.mean()),
        pf=float(v.sum() / abs(k.sum())) if len(k) and k.sum() != 0 else float("inf"),
        sharpe=float(x.mean() / sd * math.sqrt(teh_a)) if sd > 0 and teh_a > 0 else 0.0,
        maxdd=100.0 * dd,
        avg_win=float(v.mean()) if len(v) else 0.0,
        avg_loss=float(k.mean()) if len(k) else 0.0,
        avg_r=float(x.mean()),
        kokku=100.0 * float(eq[-1] - 1),
        # aastastamine on mottetu, kui aken on alla poole aasta -> NaN
        aastane=(100.0 * float(eq[-1] ** (1 / aastaid) - 1)
                 if aastaid >= 0.5 and eq[-1] > 0 else np.nan),
        t=float(x.mean() / sd * math.sqrt(len(x))) if sd > 0 else 0.0,
        teh_aastas=teh_a)


def ncdf(x):
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def p_kahepoolne(t):
    return 2.0 * (1.0 - ncdf(abs(t)))


def bh(pvals, q=0.05):
    m = len(pvals)
    jrk = sorted(range(m), key=lambda i: pvals[i])
    lavi = 0.0
    for r, i in enumerate(jrk, 1):
        if pvals[i] <= q * r / m:
            lavi = pvals[i]
    return lavi, [i for i in range(m) if lavi > 0 and pvals[i] <= lavi]
