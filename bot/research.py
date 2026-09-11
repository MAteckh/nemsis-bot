"""
research.py — mitme-instrumendi portfellimootor uute strateegiaperekondade
testimiseks.

Erinevus senisest: siin ei simuleerita üksikuid ordereid ühel sümbolil, vaid
hoitakse KAALUMAATRIKSIT (kuupäev x instrument). See lubab testida asju, mida
orderipõhine simulaator ei suuda:
  - volatiilsuse sihtimine (positsioon ~ 1/vol)
  - ristlõikeline momentum (järjesta 21 instrumenti, osta parimad)
  - ansambel (mitu lookbacki hääletavad)
  - riskipariteet

Konventsioon: kaal w[t] on teada päeva t sulgemisel ja teenib tootluse r[t+1].
"""
import os
import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

# Ühesuunaline tehingukulu baaspunktides (konservatiivne retail-CFD hinnang).
COST_BP = {
    "EURUSD": 1.0, "GBPUSD": 1.2, "USDJPY": 1.0, "AUDUSD": 1.2,
    "USDCAD": 1.3, "USDCHF": 1.3, "NZDUSD": 1.8, "EURJPY": 1.5,
    "XAUUSD": 1.5, "XAGUSD": 4.0, "COPPER": 4.0,
    "WTI": 3.0, "NGAS": 5.0,
    "SPX": 1.5, "NAS100": 1.5, "GER40": 2.0, "JP225": 3.0, "UK100": 2.5,
    "US10Y": 1.5,
    "BTCUSD": 8.0, "ETHUSD": 12.0,
}

GROUP = {
    "EURUSD": "FX", "GBPUSD": "FX", "USDJPY": "FX", "AUDUSD": "FX",
    "USDCAD": "FX", "USDCHF": "FX", "NZDUSD": "FX", "EURJPY": "FX",
    "XAUUSD": "METAL", "XAGUSD": "METAL", "COPPER": "METAL",
    "WTI": "ENERGY", "NGAS": "ENERGY",
    "SPX": "EQUITY", "NAS100": "EQUITY", "GER40": "EQUITY",
    "JP225": "EQUITY", "UK100": "EQUITY",
    "US10Y": "BOND",
    "BTCUSD": "CRYPTO", "ETHUSD": "CRYPTO",
}


def load_panel(symbols=None, start="2016-09-12"):
    """Loeb kõik CSV-d ja tagastab joondatud sulgemishindade paneeli."""
    symbols = symbols or sorted(COST_BP)
    cols = {}
    for s in symbols:
        p = os.path.join(DATA, f"{s}_d.csv")
        if not os.path.exists(p):
            continue
        df = pd.read_csv(p, parse_dates=["Date"]).set_index("Date").sort_index()
        df = df[~df.index.duplicated(keep="last")]
        c = pd.to_numeric(df["Close"], errors="coerce")
        c = c[c > 0]
        cols[s] = c
    px = pd.DataFrame(cols).sort_index()
    px = px[px.index >= pd.Timestamp(start)]
    # ainult päevad, mil vähemalt pool universumist kaupleb (välistab pühad)
    live = px.notna().sum(axis=1)
    px = px[live >= max(3, int(0.5 * px.shape[1]))]
    px = px.ffill()
    return px


def returns(px):
    return px.pct_change().fillna(0.0).replace([np.inf, -np.inf], 0.0)


def ex_ante_vol(rets, span=60):
    """Eelnevalt teadaolev volatiilsus (annualiseeritud), nihutatud et vältida lookaheadi."""
    v = rets.ewm(span=span, min_periods=20).std() * np.sqrt(252)
    return v.shift(1).replace(0.0, np.nan)


# ---------------------------------------------------------------- strateegiad

def w_tsmom(px, rets, lookback=126, vol_span=60, cap=2.0):
    """Klassikaline time-series momentum: märk minevikutootlusest, vol-skaleeritud."""
    sig = np.sign(px.pct_change(lookback)).shift(1).fillna(0.0)
    v = ex_ante_vol(rets, vol_span)
    w = sig * (0.10 / v)          # iga jalg sihib 10% aastavolatiilsust
    return w.clip(-cap, cap).fillna(0.0)


def w_tsmom_ensemble(px, rets, lookbacks=(21, 63, 126, 252), vol_span=60, cap=2.0):
    """ANSAMBEL: mitu lookbacki hääletavad. Nii teevad päris CTA-d -
    üks lookback on ülesobitatud, keskmine on robustne."""
    votes = sum(np.sign(px.pct_change(lb)) for lb in lookbacks) / len(lookbacks)
    sig = votes.shift(1).fillna(0.0)
    v = ex_ante_vol(rets, vol_span)
    w = sig * (0.10 / v)
    return w.clip(-cap, cap).fillna(0.0)


def w_xsmom(px, rets, lookback=126, k=5, vol_span=60, cap=2.0):
    """RISTLÕIKELINE momentum: järjesta kõik instrumendid, osta k parimat,
    müü k halvimat. Täiesti eri perekond kui time-series."""
    mom = px.pct_change(lookback).shift(1)
    v = ex_ante_vol(rets, vol_span)
    # riskiga korrigeeritud järjestus - muidu domineerib krüpto
    score = mom / v
    rank = score.rank(axis=1, ascending=False)
    n = score.notna().sum(axis=1)
    long = (rank <= k).astype(float)
    short = (rank > (n.values[:, None] - k)).astype(float)
    sig = long - short
    w = sig * (0.10 / v)
    return w.clip(-cap, cap).fillna(0.0)


def w_long_only_trend(px, rets, lookback=200, vol_span=60, cap=2.0):
    """Faber-tüüpi taktikaline allokatsioon: hoia ainult siis, kui üle MA-200.
    Ei lühikest. Osta-ja-hoia, millelt on drawdown maha lõigatud."""
    ma = px.rolling(lookback).mean()
    sig = (px > ma).astype(float).shift(1).fillna(0.0)
    v = ex_ante_vol(rets, vol_span)
    w = sig * (0.10 / v)
    return w.clip(0, cap).fillna(0.0)


def w_breakout(px, rets, lookback=126, vol_span=60, cap=2.0):
    """Donchian mitmel instrumendil, vol-skaleeritud."""
    hi = px.rolling(lookback).max()
    lo = px.rolling(lookback).min()
    raw = pd.DataFrame(0.0, index=px.index, columns=px.columns)
    raw[px >= hi] = 1.0
    raw[px <= lo] = -1.0
    sig = raw.replace(0.0, np.nan).ffill().fillna(0.0).shift(1)
    v = ex_ante_vol(rets, vol_span)
    w = sig * (0.10 / v)
    return w.clip(-cap, cap).fillna(0.0)


def w_carry_proxy(px, rets, lookback=252, vol_span=60, cap=2.0):
    """Carry lähend: pikaajaline trend on FX-s suuresti intressivahe.
    Eraldi perekond, aeglasem kui momentum."""
    return w_tsmom(px, rets, lookback=lookback, vol_span=vol_span, cap=cap)


def w_equal_long(px, rets, vol_span=60, cap=2.0):
    """Riskipariteediga osta-ja-hoia: võrdne RISK igasse instrumenti."""
    v = ex_ante_vol(rets, vol_span)
    w = pd.DataFrame(1.0, index=px.index, columns=px.columns) * (0.10 / v)
    return w.clip(0, cap).fillna(0.0)


# ---------------------------------------------------------------- hindamine

def vol_target(w, rets, target=0.15, span=60, cap=3.0, lookback=60):
    """Portfellitasandi volatiilsuse sihtimine - kirjanduse kõige robustsem võte."""
    gross = (w.shift(1) * rets).sum(axis=1)
    realised = gross.rolling(lookback, min_periods=20).std() * np.sqrt(252)
    scale = (target / realised.replace(0, np.nan)).shift(1).clip(0, cap).fillna(1.0)
    return w.mul(scale, axis=0)


def evaluate(w, rets, cost_bp=None, label=""):
    cost_bp = cost_bp or COST_BP
    w = w.reindex(columns=rets.columns).fillna(0.0)
    gross = (w.shift(1) * rets).sum(axis=1)
    turn = (w - w.shift(1)).abs().fillna(0.0)
    cb = pd.Series({c: cost_bp.get(c, 3.0) for c in rets.columns}) / 10000.0
    cost = (turn * cb).sum(axis=1)
    net = gross - cost
    eq = (1 + net).cumprod()
    yrs = len(net) / 252.0
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1.0
    vol = net.std() * np.sqrt(252)
    sharpe = net.mean() / net.std() * np.sqrt(252) if net.std() > 0 else 0.0
    dd = (eq / eq.cummax() - 1).min()
    calmar = cagr / abs(dd) if dd else float("inf")
    yearly = net.groupby(net.index.year).apply(lambda s: (1 + s).prod() - 1)
    return {
        "label": label, "cagr": cagr, "vol": vol, "sharpe": sharpe,
        "maxdd": dd, "calmar": calmar, "eq": eq, "net": net,
        "yearly": yearly, "pos_years": int((yearly > 0).sum()), "n_years": len(yearly),
        "turnover": turn.sum(axis=1).mean(), "cost_drag": cost.mean() * 252,
    }


def show(r):
    print(f"{r['label']:38s} CAGR {100*r['cagr']:+6.1f}%  vol {100*r['vol']:5.1f}%  "
          f"Sharpe {r['sharpe']:5.2f}  maxDD {100*r['maxdd']:6.1f}%  "
          f"Calmar {r['calmar']:5.2f}  +aastaid {r['pos_years']}/{r['n_years']}  "
          f"kulu {100*r['cost_drag']:4.1f}%")


# ---------------------------------------------------------------- kaeibe ohjamine

def rebalance(w, freq="W-FRI"):
    """Uuenda kaale ainult perioodi lõpus, muidu hoia. Vähendab käivet järsult."""
    marks = pd.Series(w.index, index=w.index).groupby(
        [w.index.to_period({"W-FRI": "W", "M": "M", "2W": "W"}.get(freq, "M"))]
    ).transform("max")
    keep = w.index == marks.values
    out = w.where(pd.Series(keep, index=w.index), other=np.nan)
    return out.ffill().fillna(0.0)


def buffer(w, band=0.20):
    """Kauplemispuhver: liigu uue sihtkaalu poole ainult siis, kui erinevus
    ületab `band` osa sihtkaalu tüüpilisest suurusest. Standardvõte CTA-des."""
    w = w.fillna(0.0)
    scale = w.abs().mean().replace(0, np.nan).fillna(1.0)
    out = np.zeros(w.shape)
    prev = np.zeros(w.shape[1])
    vals = w.values
    thr = (band * scale).values
    for i in range(len(w)):
        tgt = vals[i]
        move = np.abs(tgt - prev) > thr
        prev = np.where(move, tgt, prev)
        out[i] = prev
    return pd.DataFrame(out, index=w.index, columns=w.columns)


# ---------------------------------------------------------------- finantseerimine

# Aktsiaindeksite hinnaindeksid EI sisalda dividende; CFD-l krediteeritakse
# need pikale positsioonile. Ligikaudne aastane dividenditootlus.
DIVI = {"SPX": 0.013, "NAS100": 0.008, "GER40": 0.0, "JP225": 0.019, "UK100": 0.037}
# GER40 (^GDAXI) ON juba tootlusindeks - dividendid hinnas sees.


def load_rates(index):
    """Lühiajaline baasintress (T-bill), päevaseks laiendatud."""
    p = os.path.join(DATA, "RATES_m.csv")
    r = pd.read_csv(p, parse_dates=["Date"]).set_index("Date")["Rate"] / 100.0
    return r.reindex(index.union(r.index)).ffill().reindex(index).ffill().bfill()


def financing(w, rates, markup=0.030, divi=None):
    """Päevane finantseerimiskulu CFD-portfellile.

    Pikk maksab (r + markup), lühike saab (r - markup):
        neto = r * (L - S) + markup * (L + S)
    ehk intress rakendub NETO-, juurdehindlus BRUTO-positsioonile.
    Lisaks: aktsiaindeksi pikk positsioon saab dividendid, lühike maksab.
    """
    divi = DIVI if divi is None else divi
    net_exp = w.sum(axis=1)
    gross_exp = w.abs().sum(axis=1)
    cost = (rates * net_exp + markup * gross_exp) / 252.0
    dv = pd.Series({c: divi.get(c, 0.0) for c in w.columns})
    cost = cost - (w * dv).sum(axis=1) / 252.0
    return cost


def evaluate_full(w, rets, rates, markup=0.030, cost_bp=None, label=""):
    """Täisarvestus: spread + öine finantseerimine + dividendid."""
    cost_bp = cost_bp or COST_BP
    w = w.reindex(columns=rets.columns).fillna(0.0)
    gross = (w.shift(1) * rets).sum(axis=1)
    turn = (w - w.shift(1)).abs().fillna(0.0)
    cb = pd.Series({c: cost_bp.get(c, 3.0) for c in rets.columns}) / 10000.0
    spread = (turn * cb).sum(axis=1)
    fin = financing(w.shift(1).fillna(0.0), rates, markup)
    net = gross - spread - fin
    eq = (1 + net).cumprod()
    yrs = len(net) / 252.0
    cagr = eq.iloc[-1] ** (1 / yrs) - 1 if eq.iloc[-1] > 0 else -1.0
    dd = (eq / eq.cummax() - 1).min()
    yearly = net.groupby(net.index.year).apply(lambda s: (1 + s).prod() - 1)
    return {
        "label": label, "cagr": cagr, "vol": net.std() * np.sqrt(252),
        "sharpe": net.mean() / net.std() * np.sqrt(252) if net.std() > 0 else 0.0,
        "maxdd": dd, "calmar": cagr / abs(dd) if dd else float("inf"),
        "eq": eq, "net": net, "yearly": yearly,
        "pos_years": int((yearly > 0).sum()), "n_years": len(yearly),
        "turnover": turn.sum(axis=1).mean(),
        "cost_drag": spread.mean() * 252, "fin_drag": fin.mean() * 252,
        "gross": w.abs().sum(axis=1).mean(), "net_exp": w.sum(axis=1).mean(),
    }


def show_full(r):
    print(f"{r['label']:34s} CAGR {100*r['cagr']:+6.1f}%  Sharpe {r['sharpe']:5.2f}  "
          f"maxDD {100*r['maxdd']:6.1f}%  Calmar {r['calmar']:5.2f}  "
          f"+a {r['pos_years']:2d}/{r['n_years']}  "
          f"bruto {r['gross']:4.2f}x neto {r['net_exp']:+5.2f}x  "
          f"spread {100*r['cost_drag']:4.1f}%  fin {100*r['fin_drag']:+5.1f}%")
