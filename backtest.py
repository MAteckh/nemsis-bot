"""
backtest.py — NEMSIS Gold Grid backtest, offline, andmepõhine.

KASUTAB TÄPSELT SAMU FUNKTSIOONE, MIS PÄRIS BOTIS (gold_logic.py) —
mitte lahknevat "backtest-versiooni" strateegiast. main_v4.py ei ole
Linuxil/Macil importitav (MetaTrader5 pakett on Windows-only), seetõttu
gold_logic.py sisaldab kõiki puhtaid arvutusi ja seda saab siin otse
korduskasutada.

KASUTUS (päris ajaloolised andmed):
    python backtest.py --csv XAUUSD_H1.csv

CSV peab sisaldama veerge: time,open,high,low,close (UTC).
MT5-st saad selle: History Center → XAUUSD → H1 → paremklõps → Export.
cTrader/TradingView/broker platvormidelt samuti CSV export võimalik.

KASUTUS (self-test, ilma päris andmeteta):
    python backtest.py
See genereerib SÜNTEETILISE hinnarea ja kontrollib, et mootor ise ei
crash'i ning tulemused on loogilised. SEE POLE TURU VALIDATSIOON —
ainult mootori enda korrektsuse kontroll. Reaalsete tulemuste jaoks
on vaja päris ajaloolisi andmeid (vt ülal).

Võrdlus (praegune vs. ATR-adaptiivne konfiguratsioon):
    python backtest.py --csv XAUUSD_H1.csv --compare
"""
import argparse
import copy
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd

import gold_logic
from config import GRID_CONFIG as DEFAULT_GRID_CONFIG, INSTRUMENTS


# ─────────────────────────────────────────────────────────
#  ANDMETE LAADIMINE
# ─────────────────────────────────────────────────────────

def load_ohlc_csv(path):
    """
    Loeb OHLC CSV faili. Tunneb ära levinumad veeru-nimed (MT5 export
    kasutab suuri tähti / eestikeelseid nimesid, TradingView teistsuguseid).
    """
    df = pd.read_csv(path)
    df.columns = [c.strip().lower() for c in df.columns]
    rename = {
        "date": "time", "datetime": "time", "timestamp": "time",
        "<date>": "time", "<time>": "time_extra",
        "open": "open", "high": "high", "low": "low", "close": "close",
        "<open>": "open", "<high>": "high", "<low>": "low", "<close>": "close",
    }
    df = df.rename(columns=rename)
    if "time_extra" in df.columns:
        # MT5 export: eraldi date + time veerud
        df["time"] = df["time"].astype(str) + " " + df["time_extra"].astype(str)
        df = df.drop(columns=["time_extra"])
    if "time" not in df.columns:
        raise ValueError(f"CSV veerud {list(df.columns)} — ei leidnud aja veergu (time/date/datetime)")
    if pd.api.types.is_numeric_dtype(df["time"]):
        # Unix epoch — tuvasta kas ms või s (nt broker/andmeteenuse eksport,
        # mitte inimloetav kuupäev).
        unit = "ms" if df["time"].iloc[0] > 1e11 else "s"
        df["time"] = pd.to_datetime(df["time"], unit=unit, utc=True)
    else:
        df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("time").sort_index()
    for col in ("open", "high", "low", "close"):
        if col not in df.columns:
            raise ValueError(f"CSV veerud {list(df.columns)} — puudub '{col}'")
        df[col] = df[col].astype(float)
    return df[["open", "high", "low", "close"]]


def make_synthetic_ohlc(n=8000, seed=42, start_price=2000.0):
    """
    SÜNTEETILINE H1 hinnarida (geomeetriline juhuslik walk + volatiilsuse
    klasterdumine) — AINULT mootori enda testimiseks, EI kujuta reaalset
    kullaturgu. Ei kasutata kunagi reaalsete tulemuste väitmiseks.
    """
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2025-01-06", periods=n, freq="h", tz="utc")
    # Kalibreeritud nii, et tunni-ATR jääks reaalse XAUUSD H1 suurusjärku
    # ($5-15) — puhtalt selleks, et self-test läbiks kõik mootori harud
    # (grid init/reset/TP/SL/max-positions), mitte turu simuleerimiseks.
    vol = 0.0032 * (1 + 0.6 * np.abs(np.sin(np.arange(n) / 180.0)))
    shocks = rng.normal(0, 1, n) * vol
    trend = np.cumsum(rng.normal(0, 0.0009, n))
    log_ret = shocks + np.diff(np.concatenate([[0], trend]))
    close = start_price * np.exp(np.cumsum(log_ret))
    high = close * (1 + np.abs(rng.normal(0, 0.0018, n)))
    low = close * (1 - np.abs(rng.normal(0, 0.0018, n)))
    open_ = np.concatenate([[start_price], close[:-1]])
    df = pd.DataFrame({"open": open_, "high": high, "low": low, "close": close}, index=idx)
    # nädalavahetused välja (laup/püha)
    return df[df.index.dayofweek < 5]


# ─────────────────────────────────────────────────────────
#  SIMULATSIOON — peegeldab main_v4.run_gold_grid() otsuseloogikat
# ─────────────────────────────────────────────────────────

class Trade:
    __slots__ = ("direction", "entry", "tp", "sl", "lot", "opened_at", "closed_at", "pnl", "reason")

    def __init__(self, direction, entry, tp, sl, lot, opened_at):
        self.direction = direction
        self.entry = entry
        self.tp = tp
        self.sl = sl
        self.lot = lot
        self.opened_at = opened_at
        self.closed_at = None
        self.pnl = None
        self.reason = None


def simulate_gold_grid(df, grid_cfg=None, instrument_cfg=None, account_balance=200.0,
                        pip_value=100.0, max_positions=3, min_history=30):
    """
    Simuleerib gold grid strateegiat H1 (või muu ühtlase intervalliga) OHLC
    andmete peal, kasutades TÄPSELT samu gold_logic funktsioone, mis päris
    bot kasutab. Tagastab dict: trades (list[Trade]), equity_curve (Series),
    stats (dict).

    Lihtsustused päris botiga võrreldes (loetletud ausalt, mitte varjatult):
    - Iga bar'i high/low kasutatakse intrabar liikumise proxy'na (nagu ka
      päris bot kasutab viimase 1-2 küünla high/low't scalp/TP-kontrolliks).
    - Kui nii TP kui SL jäävad sama bar'i range'i sisse, eeldatakse
      KONSERVATIIVSELT, et SL käivitub esimesena (halvim juhtum, mitte
      optimistlik).
    - Order täitub täpselt `price` peal (spread/slippage'i ei modelleerita
      eraldi — reaalsuses veidi halvem tulemus kui siin näidatud).
    - cooldown (8 min) teisendatakse baaride arvuks vastavalt andmete
      intervallile; H1 andmetel on cooldown alati täidetud (1 bar = 60 min).
    """
    grid_cfg = copy.deepcopy(grid_cfg or DEFAULT_GRID_CONFIG)
    instrument_cfg = instrument_cfg or INSTRUMENTS["XAUUSD"]
    gs_static = instrument_cfg["grid_size"]
    trend_period = grid_cfg["trend_period"]
    trend_thresh = instrument_cfg["trend_thresh"]
    levels = grid_cfg["levels"]

    if len(df) < min_history + 5:
        raise ValueError(f"Liiga vähe andmeid ({len(df)} rida) — vaja vähemalt {min_history + 5}")

    # cooldown baarides (8 min reaalajas)
    bar_minutes = max(1, int((df.index[1] - df.index[0]).total_seconds() // 60))
    cooldown_bars = max(0, -(-8 // bar_minutes))  # ceil

    atr_history = []
    trend_history = []
    balance = account_balance
    peak_balance = account_balance
    grid_state = None  # {"center", "trend", "pending": {level: dir}}
    open_positions = []  # list[Trade]
    closed_trades = []
    equity_points = []
    last_order_bar = -10 ** 9

    # Circuit breaker olek — peegeldab main_v4.check_circuit_breaker():
    # nädalane -15% / päevane -10% drawdown balance-ankrust blokeerib UUE
    # positsiooni avamise (olemasolevad TP/SL-id jäävad kehtima, sest
    # päris broker täidab neid otse, sõltumata boti scan-tsüklist).
    # Ilma selle piirdeta näitas backtest ekslikult -100%+ drawdown'e,
    # mida reaalne konto kunagi ei koge — bot peatab end ise enne seda.
    day_key = None
    week_key = None
    day_start_balance = balance
    week_start_balance = balance
    paused_day = False
    paused_week = False

    for i in range(min_history, len(df)):
        # Piiratud (mitte kasvav) aken — kõik allolevad funktsioonid vajavad
        # max ~28 baari ajalugu (ADX). Kasvav df.iloc[:i+1] tegi backtest'i
        # O(n^2)-ks (iga baar arvutas terve senise ajaloo läbi uuesti) ja
        # muutis mitmesaja kombinatsiooniga sweep'i praktiliselt jooksmatuks.
        window = df.iloc[max(0, i - 249): i + 1]
        bar = df.iloc[i]
        now = df.index[i]
        price, high, low = float(bar["close"]), float(bar["high"]), float(bar["low"])

        atr_val = gold_logic.calc_atr(window, period=14)
        atr_history.append(atr_val)

        # ── weekend sulgemine ──
        if now.weekday() == 4 and now.hour >= 21:
            for pos in open_positions:
                pnl = (price - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - price) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "weekend"
                balance += pnl
                closed_trades.append(pos)
            open_positions = []
            equity_points.append((now, balance))
            continue
        if now.weekday() in (5, 6):
            equity_points.append((now, balance))
            continue

        cur_day, cur_week = now.strftime("%Y-%m-%d"), now.strftime("%Y-W%W")
        if cur_week != week_key:
            week_key, week_start_balance, paused_week = cur_week, balance, False
        if cur_day != day_key:
            day_key, day_start_balance, paused_day = cur_day, balance, False

        trend = gold_logic.get_trend(window, trend_period, trend_thresh)
        trend_history.append(trend)
        if len(trend_history) > 3:
            trend_history.pop(0)
        effective_trend = trend if len(trend_history) == 3 and all(t == trend_history[0] for t in trend_history) else "neutral"

        news_blackout = grid_cfg.get("news_filter", True) and gold_logic.is_news_blackout(now)
        effective_gs = gold_logic.get_dynamic_grid_size(atr_val, grid_cfg) if grid_cfg.get("dynamic_grid_size") else gs_static
        lot = gold_logic.get_compound_lot(balance, account_balance, atr_history, grid_cfg)
        adx_ok = True
        entry_adx_ok = True
        if (grid_cfg.get("adx_filter", False) or grid_cfg.get("adx_max_filter", False)) and len(window) >= 28:
            adx_val_cur = gold_logic.calc_adx(window["high"], window["low"], window["close"])
            if grid_cfg.get("adx_filter", False):
                adx_ok = adx_val_cur >= grid_cfg.get("adx_min", 20.0)
            if grid_cfg.get("adx_max_filter", False):
                # Nädalate analüüs (2a H1) näitas: grid on FADE-mehhanism (kitsas
                # $30 TP) — see teenib rahulikus/külgsuunalises turus ja kaotab
                # just tugeva trendiga nädalatel. Seega blokeeri SISENEMINE,
                # kui trend on liiga tugev, mitte liiga nõrk.
                entry_adx_ok = adx_val_cur <= grid_cfg.get("adx_max", 45.0)

        # ── TP/SL kontroll olemasolevatel positsioonidel ──
        still_open = []
        for pos in open_positions:
            tp_hit = (high >= pos.tp) if pos.direction == "buy" else (low <= pos.tp)
            sl_hit = (low <= pos.sl) if pos.direction == "buy" else (high >= pos.sl)
            if tp_hit and sl_hit:
                # konservatiivne eeldus — halvim juhtum
                pnl = (pos.sl - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - pos.sl) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "sl(ambiguous_bar)"
                balance += pnl
                closed_trades.append(pos)
            elif tp_hit:
                pnl = (pos.tp - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - pos.tp) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "tp"
                balance += pnl
                closed_trades.append(pos)
            elif sl_hit:
                pnl = (pos.sl - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - pos.sl) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "sl"
                balance += pnl
                closed_trades.append(pos)
            else:
                still_open.append(pos)
        open_positions = still_open

        # ── max floating loss (master float stop) ──
        max_float = grid_cfg["max_float"] * (balance / account_balance)
        still_open = []
        for pos in open_positions:
            fl = (price - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                else (pos.entry - price) * pos.lot * pip_value
            if fl < -max_float:
                pos.closed_at, pos.pnl, pos.reason = now, fl, "float_stop"
                balance += fl
                closed_trades.append(pos)
            else:
                still_open.append(pos)
        open_positions = still_open

        cur_equity = balance + sum(
            (price - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - price) * p.lot * pip_value
            for p in open_positions)
        if not paused_week and week_start_balance > 0 and (week_start_balance - cur_equity) / week_start_balance > 0.15:
            paused_week = True
        if not paused_day and day_start_balance > 0 and (day_start_balance - cur_equity) / day_start_balance > 0.10:
            paused_day = True
        risk_halt = paused_day or paused_week

        # ── grid init / reset ──
        if grid_state is None:
            if effective_trend != "neutral" and not news_blackout and not risk_halt and adx_ok:
                center = round(price / effective_gs) * effective_gs
                grid_state = {"center": center, "trend": effective_trend,
                              "pending": gold_logic.setup_grid(center, effective_trend, effective_gs, levels)}
            equity_points.append((now, balance + sum(
                (price - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - price) * p.lot * pip_value
                for p in open_positions)))
            continue

        grid_center = grid_state["center"]
        grid_trend = grid_state["trend"]

        if abs(price - grid_center) > effective_gs * 3 and not open_positions and adx_ok:
            new_c = round(price / effective_gs) * effective_gs
            reset_trend = effective_trend if effective_trend != "neutral" else grid_trend
            grid_state = {"center": new_c, "trend": reset_trend,
                          "pending": gold_logic.setup_grid(new_c, reset_trend, effective_gs, levels)}
        elif effective_trend != grid_trend and effective_trend != "neutral":
            for pos in open_positions:
                pnl = (price - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - price) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "trend_reset"
                balance += pnl
                closed_trades.append(pos)
            open_positions = []
            if adx_ok:
                new_c = round(price / effective_gs) * effective_gs
                grid_state = {"center": new_c, "trend": effective_trend,
                              "pending": gold_logic.setup_grid(new_c, effective_trend, effective_gs, levels)}
            else:
                grid_state = None
        else:
            # ── pending taseme päästikud ──
            if not news_blackout and not risk_halt and entry_adx_ok and effective_trend != "neutral":
                pending = grid_state["pending"]
                for level_str in list(pending.keys()):
                    direction = pending[level_str]
                    level = float(level_str)
                    if effective_trend == "bull" and direction == "sell": continue
                    if effective_trend == "bear" and direction == "buy": continue
                    hit = (direction == "buy" and low <= level) or (direction == "sell" and high >= level)
                    if not hit:
                        continue
                    same_dir = [p for p in open_positions if p.direction == direction]
                    if len(same_dir) >= levels:
                        continue
                    if len(open_positions) >= max_positions:
                        continue
                    if open_positions and open_positions[0].direction != direction:
                        continue  # ei ava hedge
                    if i - last_order_bar < cooldown_bars:
                        continue
                    if grid_cfg.get("dynamic_tp_sl"):
                        swing_low, swing_high = gold_logic.get_swing_levels(window, lookback=20)
                        tp, sl = gold_logic.calc_gold_tp_sl(direction, price, atr_val, swing_low, swing_high, grid_cfg)
                    else:
                        tp = round(price + 30.0 if direction == "buy" else price - 30.0, 2)
                        sl = round(price - 45.0 if direction == "buy" else price + 45.0, 2)
                    if grid_cfg.get("risk_based_lot"):
                        order_lot = gold_logic.get_risk_based_lot(
                            balance, abs(price - sl), pip_value,
                            grid_cfg.get("risk_pct", 0.015), max_lot=grid_cfg.get("risk_lot_max", 0.5))
                    else:
                        order_lot = lot
                    open_positions.append(Trade(direction, price, tp, sl, order_lot, now))
                    last_order_bar = i
                    del pending[level_str]

        floating = sum(
            (price - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - price) * p.lot * pip_value
            for p in open_positions)
        equity_points.append((now, balance + floating))
        peak_balance = max(peak_balance, balance + floating)

    equity = pd.Series({t: v for t, v in equity_points}).sort_index()
    return {"trades": closed_trades, "equity": equity, "final_balance": balance}


def simulate_scalp_layer(df5, grid_cfg=None, instrument_cfg=None, account_balance=200.0, pip_value=100.0):
    """
    Simuleerib SCALPING LAYER'it (main_v4.run_gold_grid() lõpuosa) M5
    andmete peal. Trendi jaoks kasutab TUNNI-graafiku lähendust, mis
    ehitatakse SAMAST M5 reast (tunni kese täieneb küünal-küünla kaupa,
    ilma tuleviku andmeid kasutamata — praegu pooleliolev tund kasutab
    ainult selle tunni juba nähtud M5 küünlaid, mitte terve tunni lõplikku
    OHLC-d).

    Ausad lihtsustused (võrreldes päris botiga):
    - Signaal loetakse bar[i] high/low järgi, POSITSIOON avatakse bar[i+1]
      open hinnaga — see väldib look-ahead viga (bar[i] close kasutamine
      korraga nii signaali kui täitmishinnana oleks optimistlik).
    - Bot ise kasutab signaali jaoks bar[i] high/low't, aga võrdleb seda
      HETKE LIVE tick-hinnaga (mis jõuab kohale mõni sekund hiljem) —
      järgmise bar'i open on sellele lähim proxy, mis meil 5-min
      andmetest võtta on.
    """
    grid_cfg = copy.deepcopy(grid_cfg or DEFAULT_GRID_CONFIG)
    instrument_cfg = instrument_cfg or INSTRUMENTS["XAUUSD"]
    trend_period = grid_cfg["trend_period"]
    trend_thresh = instrument_cfg["trend_thresh"]

    h1_closes = []          # lõpetatud tundide sulgemishinnad
    cur_hour = None
    cur_hour_close = None
    trend_history = []
    balance = account_balance
    open_positions = []
    closed_trades = []
    equity_points = []

    warmup = (trend_period + 3) * 12  # ~ piisavalt M5 baare mitme tunni jaoks

    for i in range(warmup, len(df5) - 1):
        bar = df5.iloc[i]
        now = df5.index[i]
        high, low, close = float(bar["high"]), float(bar["low"]), float(bar["close"])

        hour_key = now.floor("h")
        if cur_hour is None:
            cur_hour = hour_key
        elif hour_key != cur_hour:
            h1_closes.append(cur_hour_close)
            if len(h1_closes) > trend_period + 5:
                h1_closes.pop(0)
            cur_hour = hour_key
        cur_hour_close = close

        # ── nädalavahetus ──
        if now.weekday() == 4 and now.hour >= 21:
            for pos in open_positions:
                pnl = (close - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - close) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "weekend"
                balance += pnl
                closed_trades.append(pos)
            open_positions = []
            equity_points.append((now, balance))
            continue
        if now.weekday() in (5, 6):
            equity_points.append((now, balance))
            continue

        closes_for_trend = h1_closes + [cur_hour_close]
        if len(closes_for_trend) < trend_period + 2:
            trend = "neutral"
        else:
            now_c, ago_c = closes_for_trend[-1], closes_for_trend[-trend_period - 1]
            chg = (now_c - ago_c) / ago_c * 100
            trend = "bull" if chg > trend_thresh else "bear" if chg < -trend_thresh else "neutral"
        trend_history.append(trend)
        if len(trend_history) > 3:
            trend_history.pop(0)
        effective_trend = trend if len(trend_history) == 3 and all(t == trend_history[0] for t in trend_history) else "neutral"

        news_blackout = grid_cfg.get("news_filter", True) and gold_logic.is_news_blackout(now)

        # ── TP/SL kontroll ──
        still_open = []
        for pos in open_positions:
            tp_hit = (high >= pos.tp) if pos.direction == "buy" else (low <= pos.tp)
            sl_hit = (low <= pos.sl) if pos.direction == "buy" else (high >= pos.sl)
            if tp_hit and sl_hit:
                pnl = (pos.sl - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - pos.sl) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "sl(ambiguous_bar)"
                balance += pnl; closed_trades.append(pos)
            elif tp_hit:
                pnl = (pos.tp - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - pos.tp) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "tp"
                balance += pnl; closed_trades.append(pos)
            elif sl_hit:
                pnl = (pos.sl - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - pos.sl) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "sl"
                balance += pnl; closed_trades.append(pos)
            else:
                still_open.append(pos)
        open_positions = still_open

        # ── uus scalp-signaal (täitub JÄRGMISE baari open hinnaga) ──
        range5 = high - low
        min_range = grid_cfg.get("scalp_min_range", 20.0)
        scalp_tp = grid_cfg.get("scalp_tp", 12.0)
        scalp_sl = grid_cfg.get("scalp_sl", 25.0)
        offset = grid_cfg.get("scalp_offset", 5.0)
        if range5 > min_range and not news_blackout and len(open_positions) < 2:
            if grid_cfg.get("risk_based_lot"):
                lot = gold_logic.get_risk_based_lot(
                    balance, scalp_sl, pip_value,
                    grid_cfg.get("risk_pct", 0.015), max_lot=grid_cfg.get("risk_lot_max", 0.5))
            else:
                lot = max(0.01, (balance / account_balance) * 0.01)
                lot = round(round(lot / 0.01) * 0.01, 2)
            next_open = float(df5.iloc[i + 1]["open"])
            if effective_trend == "bull" and low < close - offset:
                tp, sl = round(next_open + scalp_tp, 2), round(next_open - scalp_sl, 2)
                open_positions.append(Trade("buy", next_open, tp, sl, lot, df5.index[i + 1]))
            elif effective_trend == "bear" and high > close + offset:
                tp, sl = round(next_open - scalp_tp, 2), round(next_open + scalp_sl, 2)
                open_positions.append(Trade("sell", next_open, tp, sl, lot, df5.index[i + 1]))

        floating = sum(
            (close - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - close) * p.lot * pip_value
            for p in open_positions)
        equity_points.append((now, balance + floating))

    equity = pd.Series({t: v for t, v in equity_points}).sort_index()
    return {"trades": closed_trades, "equity": equity, "final_balance": balance}


# ─────────────────────────────────────────────────────────
#  MITME-REZIIMI PROTOTÜÜP — trend vs range, candlestick, S/R,
#  trailing SL, uudiste-järgne kinnitus. Puhas UURIMISTÖÖ — seda ei
#  ole main_v4.py-sse ühendatud, ainult testitud siin päris andmete peal.
# ─────────────────────────────────────────────────────────

DEFAULT_REGIME_CFG = {
    "trend_period": 10, "trend_thresh": 0.3,
    "adx_trend_min": 25.0, "adx_range_max": 18.0,
    "rsi_period": 14, "rsi_ob": 70, "rsi_os": 30,
    "sr_lookback": 20, "sr_zone_atr": 0.5,   # "lähedal S/R-le" = ATR × see kordaja
    "pullback_lookback": 5,                  # lühem aken trendi-tagasitõmbe tuvastamiseks (mitte struktuurne S/R)
    "require_candlestick": True,
    "use_trailing_sl": True,
    "trail_activate_atr": 1.0, "trail_distance_atr": 1.5, "trail_breakeven_buf": 2.0,
    "fixed_tp_atr_mult": 2.0,                 # kui trailing väljas
    "range_tp_atr_mult": 1.5,                 # range-tehingu TP (vastasserva suunas)
    "sl_atr_mult": 1.5,
    "news_confirm_bars": 2,                   # mitu järjestikust sama-suunalist baari uudiste JÄREL enne uut trade'i
    "news_filter": True,
    "max_positions": 2,
    "risk_pct": 0.015,
    "risk_lot_max": 0.5,
}


def simulate_regime_strategy(df, cfg=None, account_balance=200.0, pip_value=100.0):
    """
    Reziim ADX järgi ('trend' vs 'range' vs 'transition' — ei kaubelda):
      - TREND: kauple `get_trend()` suunas, AGA ainult kui hind on
        tagasitõmbel lähedal viimase `sr_lookback` swing-tasemele (mitte
        kohe iga trendi peale) JA candlestick kinnitab pöörde — täpselt
        kasutaja idee: "vaata kuhu trend, oota kinnitust, tradi kaasa".
        TP asemel (vaikimisi) trailing SL — lase kasumil joosta.
      - RANGE: RSI mean-reversion tugi/vastupanu vahel — osta toe juures
        kui RSI ülemüüdud + candlestick kinnitab, target vastasserv.
      - TRANSITION: ei kaubelda üldse (kumbki loogika pole usaldusväärne).
      - Uudised: blackout ajal ei avata; blackout LÕPUS nõuab
        `news_confirm_bars` järjestikust sama-suunalist baari, enne kui
        uuesti tradib (mitte kohe esimesel baaril pärast akent).
    """
    cfg = {**DEFAULT_REGIME_CFG, **(cfg or {})}
    trend_period, trend_thresh = cfg["trend_period"], cfg["trend_thresh"]

    balance = account_balance
    open_positions = []
    closed_trades = []
    equity_points = []
    atr_history = []

    day_key = week_key = None
    day_start_balance = week_start_balance = balance
    paused_day = paused_week = False

    was_blackout = False
    news_confirm_left = 0
    news_direction = None

    min_history = 60
    for i in range(min_history, len(df)):
        window = df.iloc[max(0, i - 249): i + 1]
        bar = df.iloc[i]
        now = df.index[i]
        price, high, low = float(bar["close"]), float(bar["high"]), float(bar["low"])

        if now.weekday() == 4 and now.hour >= 21:
            for pos in open_positions:
                pnl = (price - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - price) * pos.lot * pip_value
                pos.closed_at, pos.pnl, pos.reason = now, pnl, "weekend"
                balance += pnl
                closed_trades.append(pos)
            open_positions = []
            equity_points.append((now, balance))
            continue
        if now.weekday() in (5, 6):
            equity_points.append((now, balance))
            continue

        cur_day, cur_week = now.strftime("%Y-%m-%d"), now.strftime("%Y-W%W")
        if cur_week != week_key:
            week_key, week_start_balance, paused_week = cur_week, balance, False
        if cur_day != day_key:
            day_key, day_start_balance, paused_day = cur_day, balance, False

        atr_val = gold_logic.calc_atr(window, period=14)
        atr_history.append(atr_val)
        adx_val = gold_logic.calc_adx(window["high"], window["low"], window["close"])
        regime = gold_logic.detect_regime(adx_val, cfg["adx_trend_min"], cfg["adx_range_max"])
        trend = gold_logic.get_trend(window, trend_period, trend_thresh)
        rsi = gold_logic.calc_rsi(window["close"].values, cfg["rsi_period"])
        swing_low, swing_high = gold_logic.get_swing_levels(window, lookback=cfg["sr_lookback"])
        news_blackout = cfg.get("news_filter", True) and gold_logic.is_news_blackout(now)

        # ── uudiste-järgne kinnituse ootamine ──
        if was_blackout and not news_blackout:
            news_confirm_left = cfg["news_confirm_bars"]
            news_direction = None
        was_blackout = news_blackout
        news_wait = False
        if news_confirm_left > 0 and not news_blackout:
            d = "up" if price > float(df.iloc[i - 1]["close"]) else "down"
            if news_direction is None or news_direction == d:
                news_direction = d
                news_confirm_left -= 1
            else:
                news_confirm_left = cfg["news_confirm_bars"]  # katkes, alusta otsast
                news_direction = d
            news_wait = news_confirm_left > 0

        # ── TP/SL + trailing kontroll olemasolevatel positsioonidel ──
        still_open = []
        for pos in open_positions:
            if cfg.get("use_trailing_sl") and pos.reason != "range":
                pos.sl = gold_logic.update_trailing_sl(pos.direction, pos.entry, price, pos.sl, atr_val, cfg)
            tp_hit = (high >= pos.tp) if pos.direction == "buy" else (low <= pos.tp)
            sl_hit = (low <= pos.sl) if pos.direction == "buy" else (high >= pos.sl)
            if tp_hit and sl_hit:
                pnl = (pos.sl - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - pos.sl) * pos.lot * pip_value
                pos.closed_at, pos.pnl = now, pnl
                pos.reason = pos.reason + "_sl(ambiguous)"
                balance += pnl; closed_trades.append(pos)
            elif tp_hit:
                pnl = (pos.tp - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - pos.tp) * pos.lot * pip_value
                pos.closed_at, pos.pnl = now, pnl
                pos.reason = pos.reason + "_tp"
                balance += pnl; closed_trades.append(pos)
            elif sl_hit:
                pnl = (pos.sl - pos.entry) * pos.lot * pip_value if pos.direction == "buy" \
                    else (pos.entry - pos.sl) * pos.lot * pip_value
                pos.closed_at, pos.pnl = now, pnl
                pos.reason = pos.reason + "_sl"
                balance += pnl; closed_trades.append(pos)
            else:
                still_open.append(pos)
        open_positions = still_open

        cur_equity = balance + sum(
            (price - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - price) * p.lot * pip_value
            for p in open_positions)
        if not paused_week and week_start_balance > 0 and (week_start_balance - cur_equity) / week_start_balance > 0.15:
            paused_week = True
        if not paused_day and day_start_balance > 0 and (day_start_balance - cur_equity) / day_start_balance > 0.10:
            paused_day = True
        risk_halt = paused_day or paused_week

        can_open = (not news_blackout and not news_wait and not risk_halt
                    and len(open_positions) < cfg["max_positions"] and swing_low is not None)
        if can_open and open_positions and open_positions[0].direction not in (None,):
            pass  # hedge-kontroll teostatakse allpool suuna võrdlusega

        if can_open:
            sr_zone = cfg["sr_zone_atr"] * atr_val
            direction = None
            entry_kind = None

            if regime == "trend" and trend in ("bull", "bear"):
                # Tagasitõmbe tuvastamine kasutab LÜHEMAT akent kui struktuurne
                # S/R (sr_lookback=20) — tugevas trendis on 20-baari swing juba
                # kaugel maas/üleval, "lähedal toele" ei läheks kunagi tõeks.
                pb_low, pb_high = gold_logic.get_swing_levels(window, lookback=cfg["pullback_lookback"])
                near_support = pb_low is not None and (price - pb_low) <= sr_zone
                near_resist = pb_high is not None and (pb_high - price) <= sr_zone
                if trend == "bull" and near_support:
                    direction, entry_kind = "buy", "trend"
                elif trend == "bear" and near_resist:
                    direction, entry_kind = "sell", "trend"
            elif regime == "range":
                near_support = swing_low is not None and (price - swing_low) <= sr_zone
                near_resist = swing_high is not None and (swing_high - price) <= sr_zone
                if rsi < cfg["rsi_os"] and near_support:
                    direction, entry_kind = "buy", "range"
                elif rsi > cfg["rsi_ob"] and near_resist:
                    direction, entry_kind = "sell", "range"

            if direction and (not cfg["require_candlestick"] or gold_logic.candlestick_confirms(window, direction)):
                if not (open_positions and open_positions[0].direction != direction):
                    sl_dist = cfg["sl_atr_mult"] * atr_val
                    sl = round(price - sl_dist, 2) if direction == "buy" else round(price + sl_dist, 2)
                    if entry_kind == "range":
                        tp = round(swing_high, 2) if direction == "buy" else round(swing_low, 2)
                    else:
                        tp_dist = cfg["fixed_tp_atr_mult"] * atr_val
                        tp = round(price + tp_dist, 2) if direction == "buy" else round(price - tp_dist, 2)
                    lot = gold_logic.get_risk_based_lot(balance, abs(price - sl), pip_value,
                                                         cfg["risk_pct"], max_lot=cfg["risk_lot_max"])
                    pos = Trade(direction, price, tp, sl, lot, now)
                    pos.reason = entry_kind
                    open_positions.append(pos)

        floating = sum(
            (price - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - price) * p.lot * pip_value
            for p in open_positions)
        equity_points.append((now, balance + floating))

    equity = pd.Series({t: v for t, v in equity_points}).sort_index()
    return {"trades": closed_trades, "equity": equity, "final_balance": balance}


# ─────────────────────────────────────────────────────────
#  STATISTIKA
# ─────────────────────────────────────────────────────────

def compute_stats(result, account_balance=200.0):
    trades = result["trades"]
    equity = result["equity"]
    n = len(trades)
    if n == 0:
        return {"trades": 0}
    wins = [t for t in trades if t.pnl > 0]
    losses = [t for t in trades if t.pnl <= 0]
    gross_win = sum(t.pnl for t in wins)
    gross_loss = -sum(t.pnl for t in losses)
    running_max = equity.cummax()
    drawdown = (equity - running_max) / running_max.replace(0, np.nan)
    max_dd = float(drawdown.min()) if len(drawdown) else 0.0

    by_reason = {}
    for t in trades:
        by_reason.setdefault(t.reason, []).append(t.pnl)

    by_session = {"asia": [], "london": [], "new_york": []}
    for t in trades:
        h = t.opened_at.hour
        key = "london" if 7 <= h < 13 else "new_york" if 13 <= h < 20 else "asia"
        by_session[key].append(t.pnl)

    by_dow = {}
    for t in trades:
        by_dow.setdefault(t.opened_at.strftime("%a"), []).append(t.pnl)

    days = max(1.0, (equity.index[-1] - equity.index[0]).total_seconds() / 86400)

    return {
        "trades": n,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate_pct": round(100 * len(wins) / n, 1),
        "net_pnl": round(result["final_balance"] - account_balance, 2),
        "return_pct": round(100 * (result["final_balance"] - account_balance) / account_balance, 1),
        "profit_factor": round(gross_win / gross_loss, 2) if gross_loss > 0 else float("inf"),
        "max_drawdown_pct": round(max_dd * 100, 1),
        "trades_per_month": round(n / (days / 30.4), 1),
        "avg_win": round(np.mean([t.pnl for t in wins]), 2) if wins else 0.0,
        "avg_loss": round(np.mean([t.pnl for t in losses]), 2) if losses else 0.0,
        "by_reason": {k: {"n": len(v), "sum": round(sum(v), 2)} for k, v in by_reason.items()},
        "by_session": {k: {"n": len(v), "sum": round(sum(v), 2)} for k, v in by_session.items() if v},
        "by_weekday": {k: {"n": len(v), "sum": round(sum(v), 2)} for k, v in by_dow.items()},
    }


def print_report(name, stats):
    print(f"\n{'='*60}\n{name}\n{'='*60}")
    if stats.get("trades", 0) == 0:
        print("  Ühtegi tehingut ei avatud selle perioodi/konfiguratsiooniga.")
        return
    print(f"  Tehinguid:        {stats['trades']}  ({stats['trades_per_month']}/kuu)")
    print(f"  Võiduprotsent:    {stats['win_rate_pct']}%  ({stats['wins']}W / {stats['losses']}L)")
    print(f"  Net P&L:          {stats['net_pnl']:+.2f}  ({stats['return_pct']:+.1f}%)")
    print(f"  Profit factor:    {stats['profit_factor']}")
    print(f"  Max drawdown:     {stats['max_drawdown_pct']}%")
    print(f"  Keskmine võit:    {stats['avg_win']:+.2f}   Keskmine kaotus: {stats['avg_loss']:+.2f}")
    print("  Sulgemise põhjus:")
    for reason, v in sorted(stats["by_reason"].items()):
        print(f"    {reason:20s}  n={v['n']:4d}  sum={v['sum']:+.2f}")
    print("  Sessiooni järgi (avamishetk):")
    for s, v in stats["by_session"].items():
        print(f"    {s:10s}  n={v['n']:4d}  sum={v['sum']:+.2f}")
    print("  Nädalapäeva järgi:")
    for d, v in sorted(stats["by_weekday"].items(), key=lambda kv: kv[1]["sum"]):
        print(f"    {d:5s}  n={v['n']:4d}  sum={v['sum']:+.2f}")


def resample_to_h1(df5):
    """M5 -> H1 agregeerimine (grid-strateegia jaoks, mis töötab tunnigraafikul)."""
    h1 = df5.resample("1h", label="left", closed="left").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last"})
    return h1.dropna()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="OHLC CSV fail (time,open,high,low,close). Ilma selleta jookseb self-test süntetilistel andmetel.")
    ap.add_argument("--balance", type=float, default=200.0)
    ap.add_argument("--compare", action="store_true", help="Võrdle praegust (fikseeritud TP/SL+grid) vs. adaptiivset (ATR-põhine) konfiguratsiooni.")
    ap.add_argument("--m5", action="store_true", help="--csv sisaldab M5 andmeid: agregeeri H1-ks grid jaoks JA jooksuta scalp-kihi backtest otse M5 peal.")
    args = ap.parse_args()

    if args.csv:
        raw = load_ohlc_csv(args.csv)
        if args.m5:
            df = resample_to_h1(raw)
            label = f"PÄRIS ANDMED (M5 -> H1 agregeeritud): {args.csv} ({len(raw)} M5 küünalt -> {len(df)} H1 küünalt, {df.index[0].date()} → {df.index[-1].date()})"
        else:
            df = raw
            label = f"PÄRIS ANDMED: {args.csv} ({len(df)} küünalt, {df.index[0].date()} → {df.index[-1].date()})"
    else:
        raw = None
        df = make_synthetic_ohlc()
        label = f"⚠️  SELF-TEST — SÜNTEETILINE hinnarida ({len(df)} küünalt). See EI VALIDEERI reaalset turukäitumist, ainult mootori enda tööd. Kasuta --csv päris ajalooliste andmetega reaalse hinnangu jaoks."
    print(label)

    current_cfg = copy.deepcopy(DEFAULT_GRID_CONFIG)
    current_cfg["dynamic_tp_sl"] = False
    current_cfg["dynamic_grid_size"] = False
    current_cfg["adx_filter"] = False

    result = simulate_gold_grid(df, grid_cfg=current_cfg, account_balance=args.balance)
    stats = compute_stats(result, args.balance)
    print_report("GRID — PRAEGUNE (fikseeritud $30/$45 TP/SL, fikseeritud grid-samm, ADX-filter väljas)", stats)

    if args.compare:
        scenarios = [
            ("GRID — + ATR-adaptiivne TP/SL", {"dynamic_tp_sl": True}),
            ("GRID — + ATR-adaptiivne grid-samm", {"dynamic_grid_size": True}),
            ("GRID — + ADX choppiness-filter", {"adx_filter": True}),
            ("GRID — + KÕIK KOLM koos", {"dynamic_tp_sl": True, "dynamic_grid_size": True, "adx_filter": True}),
        ]
        for name, overrides in scenarios:
            cfg = copy.deepcopy(current_cfg)
            cfg.update(overrides)
            res = simulate_gold_grid(df, grid_cfg=cfg, account_balance=args.balance)
            print_report(name, compute_stats(res, args.balance))

    if args.m5 and raw is not None:
        scalp_cfg_off = copy.deepcopy(DEFAULT_GRID_CONFIG)
        scalp_cfg_off["news_filter"] = False
        res_off = simulate_scalp_layer(raw, grid_cfg=scalp_cfg_off, account_balance=args.balance)
        print_report("SCALP (M5) — uudiste-filter VÄLJAS (vana käitumine)", compute_stats(res_off, args.balance))

        scalp_cfg_on = copy.deepcopy(DEFAULT_GRID_CONFIG)
        scalp_cfg_on["news_filter"] = True
        res_on = simulate_scalp_layer(raw, grid_cfg=scalp_cfg_on, account_balance=args.balance)
        print_report("SCALP (M5) — uudiste-filter SEES (uus, vaikimisi)", compute_stats(res_on, args.balance))

    if not args.csv:
        print(f"\n{'='*60}\nMEELESPEA: ülal olevad numbrid on süntetilistel andmetel, mitte päris")
        print("kullaturul. Enne mistahes parameetri live-kontole viimist jooksuta")
        print("sama skript päris MT5/broker ajaloo peal: --csv XAUUSD_H1.csv")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
