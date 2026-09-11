"""
strategies.py — strateegia-agnostiline mootor + erinevad strateegiaperekonnad.

EI eelda grid'i ega mingit muud konkreetset lähenemist. Iga strateegia on
puhas signaalifunktsioon kujul:

    signal(window, cfg) -> None | (suund, sl_kaugus, tp_kaugus)

Mootor hoolitseb ühtemoodi kõigi eest: riskipõhine positsiooni suurus,
nädalavahetuse sulgemine, päeva/nädala circuit breaker, konservatiivne
eeldus kui TP ja SL jäävad samasse baari. Nii on strateegiad omavahel
ausalt võrreldavad — erinevus tuleb ainult signaalist, mitte erinevast
riskihaldusest.
"""
import numpy as np
import pandas as pd

import gold_logic


# ─────────────────────────────────────────────────────────
#  ABIFUNKTSIOONID
# ─────────────────────────────────────────────────────────

def _ema(series, period):
    return float(series.ewm(span=period, adjust=False).mean().iloc[-1])


# ─────────────────────────────────────────────────────────
#  STRATEEGIAD (signaalifunktsioonid)
# ─────────────────────────────────────────────────────────

def sig_donchian(w, cfg):
    """Väljamurre viimase N baari tipust/põhjast (klassikaline trendijärgimine)."""
    lb = cfg.get("lookback", 20)
    if len(w) < lb + 2:
        return None
    prior = w.iloc[-(lb + 1):-1]
    price = float(w["close"].iloc[-1])
    atr = gold_logic.calc_atr(w)
    if price > float(prior["high"].max()):
        return "buy", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 3.0) * atr
    if price < float(prior["low"].min()):
        return "sell", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 3.0) * atr
    return None


def sig_ema_cross(w, cfg):
    """Kiire EMA ristub aeglasega — sisene ristumise baaril."""
    fast_p, slow_p = cfg.get("ema_fast", 20), cfg.get("ema_slow", 50)
    if len(w) < slow_p + 3:
        return None
    f_now, s_now = _ema(w["close"], fast_p), _ema(w["close"], slow_p)
    f_prev, s_prev = _ema(w["close"].iloc[:-1], fast_p), _ema(w["close"].iloc[:-1], slow_p)
    atr = gold_logic.calc_atr(w)
    if f_prev <= s_prev and f_now > s_now:
        return "buy", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 3.0) * atr
    if f_prev >= s_prev and f_now < s_now:
        return "sell", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 3.0) * atr
    return None


def sig_ema_pullback(w, cfg):
    """
    Trend filtreeritud pika EMA-ga, sisenemine tagasitõmbel keskmisele EMA-le.
    "Osta odavamalt tõusutrendis" — mitte tipu tagaajamine.
    """
    trend_p, pull_p = cfg.get("ema_trend", 200), cfg.get("ema_pull", 50)
    if len(w) < trend_p + 3:
        return None
    price = float(w["close"].iloc[-1])
    prev = float(w["close"].iloc[-2])
    e_trend, e_pull = _ema(w["close"], trend_p), _ema(w["close"], pull_p)
    atr = gold_logic.calc_atr(w)
    if price > e_trend and prev <= e_pull and price > e_pull:
        return "buy", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 3.0) * atr
    if price < e_trend and prev >= e_pull and price < e_pull:
        return "sell", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 3.0) * atr
    return None


def sig_ts_momentum(w, cfg):
    """
    Time-series momentum — akadeemiliselt kõige püsivam toormeturu anomaalia:
    kui viimase N baari tootlus on positiivne, ole ostupoolel, vastasel juhul
    müügipoolel. Sisenemine ainult siis, kui märk MUUTUB.
    """
    lb = cfg.get("mom_lookback", 120)
    if len(w) < lb + 3:
        return None
    c = w["close"]
    now_ret = float(c.iloc[-1]) / float(c.iloc[-lb - 1]) - 1
    prev_ret = float(c.iloc[-2]) / float(c.iloc[-lb - 2]) - 1
    atr = gold_logic.calc_atr(w)
    if prev_ret <= 0 < now_ret:
        return "buy", cfg.get("sl_atr", 2.0) * atr, cfg.get("tp_atr", 4.0) * atr
    if prev_ret >= 0 > now_ret:
        return "sell", cfg.get("sl_atr", 2.0) * atr, cfg.get("tp_atr", 4.0) * atr
    return None


def sig_vol_breakout(w, cfg):
    """
    Volatiilsuse väljamurre: päeva avahinnast k×ATR kaugusel. Klassikaline
    lühiajaline muster, mis püüab järsu liikumise alguse.
    """
    if len(w) < 30:
        return None
    now = w.index[-1]
    today = w[w.index.normalize() == now.normalize()]
    if len(today) < 2:
        return None
    day_open = float(today["open"].iloc[0])
    price = float(w["close"].iloc[-1])
    atr = gold_logic.calc_atr(w)
    k = cfg.get("k_atr", 1.0)
    if price > day_open + k * atr:
        return "buy", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 3.0) * atr
    if price < day_open - k * atr:
        return "sell", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 3.0) * atr
    return None


def sig_orb(w, cfg):
    """
    Sessiooni avavahemiku väljamurre (Opening Range Breakout). Kulla
    sessioonistruktuur on tugev — London (07 UTC) ja NY (13 UTC) avamine
    toovad päeva suurimad liikumised.
    """
    if len(w) < 30:
        return None
    now = w.index[-1]
    sess_start = cfg.get("orb_hour", 13)
    if now.hour < sess_start + cfg.get("orb_bars", 1) or now.hour > sess_start + cfg.get("orb_window", 4):
        return None
    today = w[(w.index.normalize() == now.normalize()) & (w.index.hour >= sess_start)]
    if len(today) < cfg.get("orb_bars", 1) + 1:
        return None
    opening = today.iloc[:cfg.get("orb_bars", 1)]
    or_high, or_low = float(opening["high"].max()), float(opening["low"].min())
    price = float(w["close"].iloc[-1])
    atr = gold_logic.calc_atr(w)
    if price > or_high:
        return "buy", cfg.get("sl_atr", 1.0) * atr, cfg.get("tp_atr", 2.0) * atr
    if price < or_low:
        return "sell", cfg.get("sl_atr", 1.0) * atr, cfg.get("tp_atr", 2.0) * atr
    return None


def sig_bollinger_reversion(w, cfg):
    """Mean reversion: fade 2σ äärmused (vastupidine trendijärgimisele)."""
    p = cfg.get("bb_period", 20)
    if len(w) < p + 3:
        return None
    s = w["close"].tail(p)
    ma, sd = float(s.mean()), float(s.std())
    if sd == 0:
        return None
    price = float(w["close"].iloc[-1])
    atr = gold_logic.calc_atr(w)
    n = cfg.get("bb_std", 2.0)
    if price < ma - n * sd:
        return "buy", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 1.5) * atr
    if price > ma + n * sd:
        return "sell", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 1.5) * atr
    return None


def sig_rsi_reversion(w, cfg):
    """RSI äärmused — sinu forex-moodulis juba kasutusel, siin kullal testitud."""
    if len(w) < cfg.get("rsi_period", 14) + 3:
        return None
    rsi = gold_logic.calc_rsi(w["close"].values, cfg.get("rsi_period", 14))
    atr = gold_logic.calc_atr(w)
    if rsi < cfg.get("rsi_os", 30):
        return "buy", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 1.5) * atr
    if rsi > cfg.get("rsi_ob", 70):
        return "sell", cfg.get("sl_atr", 1.5) * atr, cfg.get("tp_atr", 1.5) * atr
    return None


def sig_donchian_trendfiltered(w, cfg):
    """Donchian väljamurre AINULT pika EMA suunas — vähendab valeväljamurdeid."""
    trend_p = cfg.get("ema_trend", 200)
    if len(w) < trend_p + 3:
        return None
    base = sig_donchian(w, cfg)
    if base is None:
        return None
    direction, sl, tp = base
    e_trend = _ema(w["close"], trend_p)
    price = float(w["close"].iloc[-1])
    if direction == "buy" and price > e_trend:
        return base
    if direction == "sell" and price < e_trend:
        return base
    return None


STRATEGIES = {
    "donchian20": (sig_donchian, {"lookback": 20}),
    "donchian50": (sig_donchian, {"lookback": 50}),
    "donchian20+ema200": (sig_donchian_trendfiltered, {"lookback": 20, "ema_trend": 200}),
    "ema_cross_20_50": (sig_ema_cross, {"ema_fast": 20, "ema_slow": 50}),
    "ema_pullback_200_50": (sig_ema_pullback, {"ema_trend": 200, "ema_pull": 50}),
    "ts_momentum_120": (sig_ts_momentum, {"mom_lookback": 120}),
    "vol_breakout_1atr": (sig_vol_breakout, {"k_atr": 1.0}),
    "orb_ny": (sig_orb, {"orb_hour": 13, "orb_bars": 1, "orb_window": 4}),
    "orb_london": (sig_orb, {"orb_hour": 7, "orb_bars": 1, "orb_window": 4}),
    "bollinger_fade": (sig_bollinger_reversion, {}),
    "rsi_fade": (sig_rsi_reversion, {}),
}


# ─────────────────────────────────────────────────────────
#  ÜHTNE MOOTOR
# ─────────────────────────────────────────────────────────

class Pos:
    __slots__ = ("direction", "entry", "tp", "sl", "lot", "opened_at", "closed_at", "pnl", "reason")

    def __init__(self, direction, entry, tp, sl, lot, opened_at):
        self.direction, self.entry, self.tp, self.sl = direction, entry, tp, sl
        self.lot, self.opened_at = lot, opened_at
        self.closed_at = self.pnl = self.reason = None


def simulate(df, signal_fn, cfg=None, account_balance=200.0, pip_value=100.0):
    cfg = dict(cfg or {})
    risk_pct = cfg.get("risk_pct", 0.015)
    max_pos = cfg.get("max_positions", 1)
    cooldown = cfg.get("cooldown_bars", 1)
    min_hist = cfg.get("min_history", 210)

    balance = account_balance
    open_pos, closed, eq_points = [], [], []
    day_key = week_key = None
    day_start = week_start = balance
    paused_day = paused_week = False
    last_entry_bar = -10 ** 9

    for i in range(min_hist, len(df)):
        w = df.iloc[max(0, i - 260): i + 1]
        bar = df.iloc[i]
        now = df.index[i]
        price, high, low = float(bar["close"]), float(bar["high"]), float(bar["low"])

        if now.weekday() == 4 and now.hour >= 21:
            for p in open_pos:
                pnl = (price - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - price) * p.lot * pip_value
                p.closed_at, p.pnl, p.reason = now, pnl, "weekend"
                balance += pnl; closed.append(p)
            open_pos = []
            eq_points.append((now, balance)); continue
        if now.weekday() in (5, 6):
            eq_points.append((now, balance)); continue

        d, wk = now.strftime("%Y-%m-%d"), now.strftime("%Y-W%W")
        if wk != week_key:
            week_key, week_start, paused_week = wk, balance, False
        if d != day_key:
            day_key, day_start, paused_day = d, balance, False

        still = []
        for p in open_pos:
            tp_hit = (high >= p.tp) if p.direction == "buy" else (low <= p.tp)
            sl_hit = (low <= p.sl) if p.direction == "buy" else (high >= p.sl)
            if tp_hit and sl_hit:
                exit_px, reason = p.sl, "sl(ambiguous)"
            elif tp_hit:
                exit_px, reason = p.tp, "tp"
            elif sl_hit:
                exit_px, reason = p.sl, "sl"
            else:
                still.append(p); continue
            pnl = (exit_px - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - exit_px) * p.lot * pip_value
            p.closed_at, p.pnl, p.reason = now, pnl, reason
            balance += pnl; closed.append(p)
        open_pos = still

        equity = balance + sum(
            (price - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - price) * p.lot * pip_value
            for p in open_pos)
        if not paused_week and week_start > 0 and (week_start - equity) / week_start > 0.15:
            paused_week = True
        if not paused_day and day_start > 0 and (day_start - equity) / day_start > 0.10:
            paused_day = True

        if (not paused_day and not paused_week and len(open_pos) < max_pos
                and i - last_entry_bar >= cooldown):
            sig = signal_fn(w, cfg)
            if sig:
                direction, sl_dist, tp_dist = sig
                if sl_dist > 0 and not (open_pos and open_pos[0].direction != direction):
                    sl = price - sl_dist if direction == "buy" else price + sl_dist
                    tp = price + tp_dist if direction == "buy" else price - tp_dist
                    lot = gold_logic.get_risk_based_lot(balance, sl_dist, pip_value, risk_pct,
                                                        max_lot=cfg.get("max_lot", 0.5))
                    open_pos.append(Pos(direction, price, round(tp, 2), round(sl, 2), lot, now))
                    last_entry_bar = i

        floating = sum(
            (price - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - price) * p.lot * pip_value
            for p in open_pos)
        eq_points.append((now, balance + floating))

    equity = pd.Series({t: v for t, v in eq_points}).sort_index()
    return {"trades": closed, "equity": equity, "final_balance": balance}


def stats(res, account_balance=200.0, cost_per_001=0.0):
    trades = res["trades"]
    if not trades:
        return {"trades": 0}
    pnls = [t.pnl - cost_per_001 * (t.lot / 0.01) for t in trades]
    wins = [p for p in pnls if p > 0]
    losses = [p for p in pnls if p <= 0]
    eq = res["equity"]
    dd = (eq - eq.cummax()) / eq.cummax().replace(0, np.nan)
    gross_w, gross_l = sum(wins), -sum(losses)
    return {
        "trades": len(trades),
        "win_rate": round(100 * len(wins) / len(trades), 1),
        "net": round(sum(pnls), 2),
        "return_pct": round(100 * sum(pnls) / account_balance, 1),
        "pf": round(gross_w / gross_l, 2) if gross_l > 0 else float("inf"),
        "max_dd": round(float(dd.min()) * 100, 1) if len(dd) else 0.0,
    }


def buy_and_hold(df, account_balance=200.0, pip_value=100.0, lot=0.01):
    """Võrdlusalus: osta alguses, hoia lõpuni. Iga strateegia peab selle lööma."""
    move = float(df["close"].iloc[-1]) - float(df["close"].iloc[0])
    pnl = move * lot * pip_value
    eq = account_balance + (df["close"] - float(df["close"].iloc[0])) * lot * pip_value
    dd = (eq - eq.cummax()) / eq.cummax().replace(0, np.nan)
    return {"trades": 1, "win_rate": 100.0 if pnl > 0 else 0.0, "net": round(pnl, 2),
            "return_pct": round(100 * pnl / account_balance, 1), "pf": float("inf") if pnl > 0 else 0.0,
            "max_dd": round(float(dd.min()) * 100, 1)}
