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
        window = df.iloc[: i + 1]
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
        if grid_cfg.get("adx_filter", False) and len(window) >= 28:
            adx_ok = gold_logic.calc_adx(window["high"], window["low"], window["close"]) >= grid_cfg.get("adx_min", 20.0)

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
            if not news_blackout and not risk_halt and effective_trend != "neutral":
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
                    open_positions.append(Trade(direction, price, tp, sl, lot, now))
                    last_order_bar = i
                    del pending[level_str]

        floating = sum(
            (price - p.entry) * p.lot * pip_value if p.direction == "buy" else (p.entry - price) * p.lot * pip_value
            for p in open_positions)
        equity_points.append((now, balance + floating))
        peak_balance = max(peak_balance, balance + floating)

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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", help="OHLC CSV fail (time,open,high,low,close). Ilma selleta jookseb self-test süntetilistel andmetel.")
    ap.add_argument("--balance", type=float, default=200.0)
    ap.add_argument("--compare", action="store_true", help="Võrdle praegust (fikseeritud TP/SL+grid) vs. adaptiivset (ATR-põhine) konfiguratsiooni.")
    args = ap.parse_args()

    if args.csv:
        df = load_ohlc_csv(args.csv)
        label = f"PÄRIS ANDMED: {args.csv} ({len(df)} küünalt, {df.index[0].date()} → {df.index[-1].date()})"
    else:
        df = make_synthetic_ohlc()
        label = f"⚠️  SELF-TEST — SÜNTEETILINE hinnarida ({len(df)} küünalt). See EI VALIDEERI reaalset turukäitumist, ainult mootori enda tööd. Kasuta --csv päris ajalooliste andmetega reaalse hinnangu jaoks."
    print(label)

    current_cfg = copy.deepcopy(DEFAULT_GRID_CONFIG)
    current_cfg["dynamic_tp_sl"] = False
    current_cfg["dynamic_grid_size"] = False
    current_cfg["adx_filter"] = False

    result = simulate_gold_grid(df, grid_cfg=current_cfg, account_balance=args.balance)
    stats = compute_stats(result, args.balance)
    print_report("PRAEGUNE (fikseeritud $30/$45 TP/SL, fikseeritud grid-samm, ADX-filter väljas)", stats)

    if args.compare:
        scenarios = [
            ("+ ATR-adaptiivne TP/SL", {"dynamic_tp_sl": True}),
            ("+ ATR-adaptiivne grid-samm", {"dynamic_grid_size": True}),
            ("+ ADX choppiness-filter", {"adx_filter": True}),
            ("+ KÕIK KOLM koos", {"dynamic_tp_sl": True, "dynamic_grid_size": True, "adx_filter": True}),
        ]
        for name, overrides in scenarios:
            cfg = copy.deepcopy(current_cfg)
            cfg.update(overrides)
            res = simulate_gold_grid(df, grid_cfg=cfg, account_balance=args.balance)
            print_report(name, compute_stats(res, args.balance))

    if not args.csv:
        print(f"\n{'='*60}\nMEELESPEA: ülal olevad numbrid on süntetilistel andmetel, mitte päris")
        print("kullaturul. Enne mistahes parameetri live-kontole viimist jooksuta")
        print("sama skript päris MT5/broker ajaloo peal: --csv XAUUSD_H1.csv")
        print(f"{'='*60}")


if __name__ == "__main__":
    main()
