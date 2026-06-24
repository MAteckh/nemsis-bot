"""
NEMSIS v4 — Mean Reversion Strategy
Forex cross-paarid: AUDCAD, AUDNZD, EURGBP, EURCHF, NZDCAD
Bollinger + RSI + ADX + Aasia sessioon
"""
import numpy as np
import pandas as pd
from datetime import datetime, timezone

def is_asian_session(now):
    h = now.hour
    return h >= 23 or h < 7

def calc_bollinger(closes, period=20, std=2.0):
    if len(closes) < period: return None, None, None
    s = pd.Series(closes[-period:])
    ma = float(s.mean())
    sd = float(s.std())
    return ma - std*sd, ma, ma + std*sd

def calc_rsi(closes, period=14):
    if len(closes) < period+1: return 50.0
    deltas = np.diff(closes[-(period+1):])
    gains  = deltas[deltas > 0].sum() / period
    losses = -deltas[deltas < 0].sum() / period
    if losses == 0: return 100.0
    return 100 - (100 / (1 + gains/losses))

def calc_adx(highs, lows, closes, period=14):
    if len(closes) < period*2: return 50.0
    h = np.array(highs[-period*2:])
    l = np.array(lows[-period*2:])
    c = np.array(closes[-period*2:])
    tr    = np.maximum(h[1:]-l[1:], np.maximum(abs(h[1:]-c[:-1]), abs(l[1:]-c[:-1])))
    up    = h[1:] - h[:-1]
    down  = l[:-1] - l[1:]
    dmp   = np.where((up > down) & (up > 0), up, 0.0)[-period:]
    dmm   = np.where((down > up) & (down > 0), down, 0.0)[-period:]
    atr   = tr[-period:].mean()
    if atr == 0: return 50.0
    dip   = 100 * dmp.mean() / atr
    dim   = 100 * dmm.mean() / atr
    if dip + dim == 0: return 50.0
    return 100 * abs(dip - dim) / (dip + dim)

class MeanRevStrategy:
    def __init__(self, symbol, cfg, mr_cfg, logger, add_log, send_telegram,
                 sb_select, sb_insert, sb_upsert, get_balance):
        self.symbol       = symbol
        self.cfg          = cfg
        self.mr_cfg       = mr_cfg
        self.logger       = logger
        self.add_log      = add_log
        self.send_telegram = send_telegram
        self.sb_select    = sb_select
        self.sb_insert    = sb_insert
        self.sb_upsert    = sb_upsert
        self.get_balance  = get_balance
        self.highs        = []
        self.lows         = []
        self.closes       = []
        self.peak_balance = None

    def update_data(self, high, low, close):
        self.highs.append(high)
        self.lows.append(low)
        self.closes.append(close)
        if len(self.highs) > 200:
            self.highs.pop(0)
            self.lows.pop(0)
            self.closes.pop(0)

    def get_open_positions(self):
        return self.sb_select("signals",
            f"executed=eq.false&session=eq.{self.symbol}&order=created_at.asc")

    def run(self, price, high, low, now):
        self.update_data(high, low, price)
        if len(self.closes) < 25: return

        # ── SPREAD FILTER ──────────────────────────────────
        # Kõrge spread = ära kauple (öösel, uudiste ajal)
        spread = high - low
        avg_spread = float(np.mean([abs(self.highs[i]-self.lows[i]) for i in range(-20,0)])) if len(self.highs) >= 20 else spread
        if avg_spread > 0 and spread > avg_spread * 2.5:
            return  # spread liiga kõrge

        # ── WEEKEND SULGEMINE ──────────────────────────────
        # Reede 21:00 UTC — sulge kõik positsioonid
        if now.weekday() == 4 and now.hour >= 21:
            open_pos = self.get_open_positions()
            if open_pos:
                balance = self.get_balance()
                for pos in open_pos:
                    fl = (price - float(pos["entry"])) * self.cfg["lot"] * self.cfg["pip_value"]                          if pos["direction"] == "buy"                          else (float(pos["entry"]) - price) * self.cfg["lot"] * self.cfg["pip_value"]
                    new_bal = round(balance + fl, 2)
                    self.sb_upsert("signals", {"id": pos["id"], "executed": True})
                    self.sb_upsert("bot_state", {"id": 1, "balance": new_bal})
                    balance = new_bal
                self.add_log(f"🔒 {self.symbol} weekend sulgemine")
            return

        # ── ESMASPÄEV — ei kauple kell 00:00-01:00 (gap risk) ──
        if now.weekday() == 0 and now.hour < 1:
            return

        # ── UUDISTE FILTER ─────────────────────────────────
        # Ei kauple kolmapäev 18:00-19:00 UTC (Fed) ja
        # esimene reede kuus 12:00-13:30 UTC (NFP)
        if now.weekday() == 2 and 18 <= now.hour < 19:
            return  # Fed rate decision
        if now.weekday() == 4 and now.day <= 7 and 12 <= now.hour < 14:
            return  # NFP (esimene reede kuus)

        balance = self.get_balance()
        if self.peak_balance is None:
            self.peak_balance = balance

        # Master stop-loss
        open_pos = self.get_open_positions()
        floating = sum(
            (price - float(p["entry"])) * self.cfg["lot"] * self.cfg["pip_value"]
            if p["direction"] == "buy"
            else (float(p["entry"]) - price) * self.cfg["lot"] * self.cfg["pip_value"]
            for p in open_pos
        )
        equity = balance + floating

        if self.peak_balance > 0:
            dd = (self.peak_balance - equity) / self.peak_balance
            if dd > self.mr_cfg["master_sl"] and open_pos:
                for pos in open_pos:
                    fl = (price - float(pos["entry"])) * self.cfg["lot"] * self.cfg["pip_value"] \
                         if pos["direction"] == "buy" \
                         else (float(pos["entry"]) - price) * self.cfg["lot"] * self.cfg["pip_value"]
                    new_bal = round(balance + fl, 2)
                    self.sb_upsert("signals", {"id": pos["id"], "executed": True})
                    self.sb_upsert("bot_state", {"id": 1, "balance": new_bal})
                    balance = new_bal
                self.add_log(f"🛑 {self.symbol} master SL — drawdown {round(dd*100,1)}%")
                self.send_telegram(f"🛑 <b>{self.symbol} Master Stop-Loss</b>\nDrawdown: {round(dd*100,1)}%")
                self.peak_balance = balance
                return

        # TP kontroll
        open_pos = self.get_open_positions()
        for pos in open_pos:
            entry     = float(pos["entry"])
            tp        = float(pos["tp"])
            direction = pos["direction"]
            tp_hit = (high >= tp) if direction == "buy" else (low <= tp)
            if tp_hit:
                atr_val  = np.mean([abs(self.highs[i]-self.lows[i]) for i in range(-14,0)]) if len(self.highs) >= 14 else 0.001
                pnl      = atr_val * self.cfg["lot"] * self.cfg["pip_value"]
                new_bal  = round(balance + pnl, 2)
                self.sb_upsert("signals", {"id": pos["id"], "executed": True})
                self.sb_upsert("bot_state", {"id": 1, "balance": new_bal})
                balance  = new_bal
                if new_bal > self.peak_balance: self.peak_balance = new_bal
                self.add_log(f"✅ {self.symbol} TP: {direction.upper()} @ {entry:.5f} → {tp:.5f}  +{pnl:.2f}€")
                self.send_telegram(
                    f"✅ <b>{self.symbol} TP!</b>\n"
                    f"{direction.upper()} @ {entry:.5f} → {tp:.5f}\n"
                    f"PnL: <b>+{pnl:.2f}€</b> | Balance: <b>{balance:.2f}€</b>"
                )

        # Sessioon filter
        session = self.cfg.get("session", "all")
        if session == "asia" and not is_asian_session(now):
            return

        # ADX filter
        if self.cfg.get("adx_filter", False):
            adx = calc_adx(self.highs, self.lows, self.closes)
            if adx > self.mr_cfg["adx_max"]:
                return  # trending → ei kauple

        # Bollinger + RSI
        lower, ma, upper = calc_bollinger(self.closes, self.mr_cfg["bb_period"], self.mr_cfg["bb_std"])
        if lower is None: return
        rsi = calc_rsi(self.closes, self.mr_cfg["rsi_period"])

        # RSI per paar — optimeeritud seadistused
        rsi_per_pair = self.mr_cfg.get("rsi_per_pair", {})
        rsi_ob, rsi_os = rsi_per_pair.get(self.symbol, (self.mr_cfg["rsi_ob"], self.mr_cfg["rsi_os"]))

        open_pos = self.get_open_positions()
        if len(open_pos) >= self.mr_cfg["max_pos"]: return

        atr_val = np.mean([abs(self.highs[i]-self.lows[i]) for i in range(-14,0)]) if len(self.highs) >= 14 else 0.001
        # Risk-based lot: riski max 1.5% kontost per tehing
        balance = self.get_balance()
        risk_amount = balance * 0.015
        pip_value = self.cfg["pip_value"]
        sl_dist = atr_val * 1.5  # SL = 1.5× ATR
        lot = risk_amount / (sl_dist * pip_value) if sl_dist > 0 else self.cfg["lot"]
        lot = max(0.01, min(round(lot, 3), 0.10))  # min 0.01, max 0.10

        # SELL — hind üle ülemise bändi + overbought
        if high >= upper and rsi > rsi_ob:
            exists = any(p["direction"]=="sell" and abs(float(p["entry"])-price) < atr_val for p in open_pos)
            if not exists:
                tp = round(price - atr_val, 5)
                sl = round(price + atr_val*3, 5)
                self.sb_insert("signals", {
                    "direction": "sell", "entry": round(price,5), "tp": tp,
                    "sl": sl,
                    "lot": lot, "session": self.symbol,
                    "regime": "meanrev", "executed": False, "breakeven": False,
                    "atr": round(atr_val, 6), "score": int(rsi),
                })
                # Päris cTrader order
                try:
                    import ctrader as ct
                    ct.place_order("sell", self.symbol, lot, tp=tp, sl=sl)
                except Exception as e:
                    self.logger.error(f"cTrader order {self.symbol}: {e}")
                self.add_log(f"📊 {self.symbol} SELL @ {price:.5f} | RSI:{rsi:.0f} | BB upper")

        # BUY — hind alla alumise bändi + oversold
        if low <= lower and rsi < rsi_os:
            exists = any(p["direction"]=="buy" and abs(float(p["entry"])-price) < atr_val for p in open_pos)
            if not exists:
                tp = round(price + atr_val, 5)
                sl = round(price - atr_val*3, 5)
                self.sb_insert("signals", {
                    "direction": "buy", "entry": round(price,5), "tp": tp,
                    "sl": sl,
                    "lot": lot, "session": self.symbol,
                    "regime": "meanrev", "executed": False, "breakeven": False,
                    "atr": round(atr_val, 6), "score": int(rsi),
                })
                # Päris cTrader order
                try:
                    import ctrader as ct
                    ct.place_order("buy", self.symbol, lot, tp=tp, sl=sl)
                except Exception as e:
                    self.logger.error(f"cTrader order {self.symbol}: {e}")
                self.add_log(f"📊 {self.symbol} BUY @ {price:.5f} | RSI:{rsi:.0f} | BB lower")
