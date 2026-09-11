"""
portfolio_sim.py — UHE KONTO portfellisimulaator.

Miks vaja: strategies.simulate() annab igale jalale oma balansi. Paris
botis jagavad koik jalad UHTE kontot, nii et neli samaaegset positsiooni
riskivad koos. 214 EUR kontol, kus 0.01 lot on sunnitud miinimum, tahendab
see, et neli jalga korraga = kuni 100% kontost korraga mangus.

See simulaator:
  - uks balanss koigi jalgade peale
  - portfellitasandi riskilagi (max_portfolio_risk)
  - tehingutasandi riskilagi (max_trade_risk) - JATAB tehingu vahele,
    kui sunnitud 0.01 lot riskiks liiga palju. Instrument jaab sisse,
    aga bot ei kaupla hetkel, mil stopp on liiga lai.
  - oine finantseerimine
"""
import os
import numpy as np
import pandas as pd

MK = 0.030          # maakleri juurdehindlus
MIN_LOT = 0.01
MAX_LOT = 0.5

SPREAD = {"XAUUSD": 0.40, "SPX": 0.50, "USDJPY": 0.15, "EURUSD": 0.12}
NOTIONAL = {
    "XAUUSD": lambda lot, px: lot * 100 * px,
    "SPX":    lambda lot, px: lot * 100 * px,
    "USDJPY": lambda lot, px: lot * 100000,
    "EURUSD": lambda lot, px: lot * 100000 * px,
}


class P:
    __slots__ = ("sym", "dir", "entry", "sl", "tp", "lot", "opened", "risk", "pv")

    def __init__(self, sym, d, entry, sl, tp, lot, opened, risk, pv):
        self.sym, self.dir, self.entry, self.sl, self.tp = sym, d, entry, sl, tp
        self.lot, self.opened, self.risk, self.pv = lot, opened, risk, pv


def precompute_signals(df, signal_fn, cfg, min_hist=210, window=260):
    """Arvutab signaalid ette: kuupaev -> (suund, sl_dist, tp_dist)."""
    out = {}
    for i in range(min_hist, len(df)):
        w = df.iloc[max(0, i - window): i + 1]
        s = signal_fn(w, cfg)
        if s:
            out[df.index[i]] = s
    return out


def run(legs, rates, balance0=214.0,
        risk_pct=0.015, max_trade_risk=1.0, max_portfolio_risk=1.0,
        max_concurrent=99, sl_mult=1.0, min_lot=MIN_LOT, dead_below=20.0):
    """
    legs: list of dicts {name, df, signals, pip_value}
    max_trade_risk      : uks tehing ei tohi riskida rohkem kui see osa balansist
    max_portfolio_risk  : koik avatud positsioonid kokku ei tohi ulatada seda
    sl_mult             : stopi kauguse kordaja (0.5 = poole tihedam stopp)
    """
    dates = sorted(set().union(*[set(l["df"].index) for l in legs]))
    bal = balance0
    peak = balance0
    mdd = 0.0
    open_pos = []
    closed = []
    skipped = {l["name"]: 0 for l in legs}
    taken = {l["name"]: 0 for l in legs}
    by = {l["name"]: l for l in legs}

    for dt in dates:
        if bal <= dead_below:
            return dict(balance=0.0, mdd=mdd, trades=closed, dead=True,
                        skipped=skipped, taken=taken)

        # 1) sulge tabatud positsioonid
        still = []
        for p in open_pos:
            leg = by[p.sym]
            if dt not in leg["df"].index:
                still.append(p); continue
            bar = leg["df"].loc[dt]
            hi, lo = float(bar["high"]), float(bar["low"])
            tp_hit = hi >= p.tp if p.dir == "buy" else lo <= p.tp
            sl_hit = lo <= p.sl if p.dir == "buy" else hi >= p.sl
            if tp_hit and sl_hit:
                px, why = p.sl, "sl?"
            elif tp_hit:
                px, why = p.tp, "tp"
            elif sl_hit:
                px, why = p.sl, "sl"
            else:
                still.append(p); continue
            pnl = (px - p.entry) * p.lot * p.pv if p.dir == "buy" else (p.entry - px) * p.lot * p.pv
            days = max(1, (dt - p.opened).days)
            rr = float(rates.asof(p.opened))
            fin = NOTIONAL[p.sym](p.lot, p.entry) * (rr + MK) * days / 365.0
            bal += pnl - SPREAD[p.sym] * (p.lot / 0.01) - fin
            closed.append((p.sym, pnl, why, days))
            peak = max(peak, bal); mdd = min(mdd, bal / peak - 1)
        open_pos = still

        # 2) ava uusi
        open_risk = sum(p.risk for p in open_pos)
        for leg in legs:
            nm = leg["name"]
            if any(p.sym == nm for p in open_pos):
                continue
            if len(open_pos) >= max_concurrent:
                break
            sig = leg["signals"].get(dt)
            if not sig:
                continue
            direction, sl_dist, tp_dist = sig
            sl_dist *= sl_mult
            tp_dist *= sl_mult
            if sl_dist <= 0:
                continue
            pv = leg["pip_value"]
            px = float(leg["df"].loc[dt, "close"])
            lot = max(min_lot, min(round(bal * risk_pct / (sl_dist * pv), 3), MAX_LOT))
            risk = sl_dist * pv * lot
            # tehingutasandi lagi: kui sunnitud lot riskiks liiga palju, jata vahele
            if risk > bal * max_trade_risk:
                skipped[nm] += 1
                continue
            # portfellitasandi lagi
            if open_risk + risk > bal * max_portfolio_risk:
                skipped[nm] += 1
                continue
            sl = px - sl_dist if direction == "buy" else px + sl_dist
            tp = px + tp_dist if direction == "buy" else px - tp_dist
            open_pos.append(P(nm, direction, px, sl, tp, lot, dt, risk, pv))
            open_risk += risk
            taken[nm] += 1

    return dict(balance=bal, mdd=mdd, trades=closed, dead=False,
                skipped=skipped, taken=taken)
