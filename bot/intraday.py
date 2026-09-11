"""
intraday.py — paevasisene analuus.

Miks see eraldi failis: paevasisene strateegia ei maksa OOEST
finantseerimist, mis etapis 4 tappis KOIK ulepaevased strateegiad
(-1.3% kuni -4.5% murdepunktist puudu). Kui paevasisesel on kasvoi
vaike serv, jaab see alles, sest ainus kulu on spread.
"""
import os
import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")


def load_h1(sym):
    df = pd.read_csv(os.path.join(DATA, f"{sym}_h1.csv"), parse_dates=["Date"])
    df = df.set_index("Date").sort_index()
    df = df[~df.index.duplicated(keep="last")]
    for c in ("Open", "High", "Low", "Close"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df = df.dropna()
    df = df[(df[["Open", "High", "Low", "Close"]] > 0).all(axis=1)]
    return df


def hour_profile(df, label=""):
    """Keskmine tunnitootlus kellaaja kaupa (UTC), pool/pool valideeritud."""
    r = df["Close"].pct_change()
    h = df.index.hour
    mid = len(df) // 2
    out = []
    for hh in sorted(set(h)):
        m = h == hh
        a = r[m & (np.arange(len(df)) < mid)]
        b = r[m & (np.arange(len(df)) >= mid)]
        al = r[m]
        if len(al) < 30:
            continue
        t = al.mean() / al.std() * np.sqrt(len(al)) if al.std() > 0 else 0
        out.append({
            "h": hh, "n": len(al),
            "bp": 1e4 * al.mean(),
            "bp_1pool": 1e4 * a.mean(), "bp_2pool": 1e4 * b.mean(),
            "t": t,
            "sama_margi": np.sign(a.mean()) == np.sign(b.mean()),
        })
    return pd.DataFrame(out)


def overnight_split(df):
    """Kui palju tootlusest tekib OOSEL (suletud->avatud) vs PAEVAL?"""
    d = df.copy()
    d["day"] = d.index.date
    g = d.groupby("day")
    first_open = g["Open"].first()
    last_close = g["Close"].last()
    intraday = (last_close / first_open - 1)
    overnight = (first_open / last_close.shift(1) - 1).dropna()
    return intraday, overnight
