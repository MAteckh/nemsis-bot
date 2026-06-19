"""
NEMSIS v3 — Grid Trading Bot
Railway 24/7 | Supabase | Telegram

Strateegia: Trend-Aware Grid Trading
- Bull trend → ainult BUY grid
- Bear trend → ainult SELL grid  
- Neutral → mõlemad suunad
- Max floating loss kaitse
- Auto grid reset kui trend muutub
- Claude AI analüüs iga 30 min
"""

import sys, os, json, time, logging, requests
from datetime import datetime, timezone, timedelta
import pandas as pd
import numpy as np

# ── Env vars ─────────────────────────────────────────────
SUPABASE_URL     = os.environ.get("SUPABASE_URL", "https://xqinzjaqorjqaexeoyqc.supabase.co")
SUPABASE_KEY     = os.environ.get("SUPABASE_KEY", "sb_secret_geYNl5euHLVWXQtone_N0g_K5nB0Zel")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "7502951774:AAFEdMlowZumpFlLm817UEP4ws40SeZtROo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7638697143")
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "60"))
ACCOUNT_BALANCE  = float(os.environ.get("ACCOUNT_BALANCE", "500"))
TWELVEDATA_KEY   = os.environ.get("TWELVEDATA_KEY", "74935ad641d14749a66009b4abc84ce7")
ANTHROPIC_KEY    = os.environ.get("ANTHROPIC_KEY", "")

# ── Grid parameetrid (optimeeritud) ──────────────────────
GRID_SIZE      = 30.0
GRID_LEVELS    = 8
LOT_SIZE       = 0.01
MAX_FLOAT_LOSS = 100.0
TREND_PERIOD   = 50
TREND_THRESH   = 3.0
VOL_PERIOD     = 20
VOL_THRESH     = 1.3
VOL_BOOST      = 1.5

# ATR cache
_atr_history = []

# Claude AI cache
_claude_cache = {"bias": "neutral", "reason": "", "updated": 0}

def calc_current_atr(df):
    try:
        if len(df) < 15: return 1.0
        hl = df["high"] - df["low"]
        hc = (df["high"] - df["close"].shift()).abs()
        lc = (df["low"]  - df["close"].shift()).abs()
        tr = pd.concat([hl,hc,lc],axis=1).max(axis=1)
        atr = float(tr.tail(14).mean())
        _atr_history.append(atr)
        if len(_atr_history) > 100: _atr_history.pop(0)
        return atr
    except:
        return 1.0

def get_vol_multiplier():
    if len(_atr_history) < VOL_PERIOD: return 1.0
    avg_atr = sum(_atr_history[-VOL_PERIOD:]) / VOL_PERIOD
    current = _atr_history[-1] if _atr_history else avg_atr
    if current > avg_atr * VOL_THRESH:
        return VOL_BOOST
    return 1.0

def get_compound_lot(balance):
    base = round(max(LOT_SIZE, (balance / ACCOUNT_BALANCE) * LOT_SIZE), 3)
    vol  = get_vol_multiplier()
    return round(base * vol, 3)

def get_scaled_max_float(balance):
    return MAX_FLOAT_LOSS * (balance / ACCOUNT_BALANCE)

def get_claude_bias(price, trend, atr, session):
    """Claude AI analüüs iga 30 min."""
    global _claude_cache
    now = time.time()
    if now - _claude_cache["updated"] < 30*60:
        return _claude_cache["bias"], _claude_cache["reason"]
    if not ANTHROPIC_KEY:
        return "neutral", "Key puudub"
    try:
        prompt = f"""Oled gold trader. Analüüsi lühidalt:
Gold: ${price:.0f} | Trend: {trend} | ATR: ${atr:.1f} | Sessioon: {session}
Vasta AINULT JSON: {{"bias":"buy/sell/neutral","confidence":0-100,"reason":"eesti keeles lühidalt","avoid":true/false}}"""
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":"claude-sonnet-4-6","max_tokens":150,"messages":[{"role":"user","content":prompt}]},
            timeout=30)
        text = r.json()["content"][0]["text"].replace("```json","").replace("```","").strip()
        res  = json.loads(text)
        bias = "neutral" if res.get("avoid") else res.get("bias","neutral")
        reason = res.get("reason","")
        confidence = res.get("confidence", 50)
        _claude_cache = {"bias":bias,"reason":reason,"updated":now}
        add_log(f"🤖 Claude: {bias} ({confidence}%) — {reason[:40]}")
        send_telegram(f"🤖 <b>Claude AI Analüüs</b>\nBias: <b>{bias.upper()}</b> ({confidence}%)\n{reason}")
        return bias, reason
    except Exception as e:
        logger.error(f"Claude error: {e}")
        return "neutral", ""

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NEMSIS_GRID")
log_buffer = []

def add_log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    log_buffer.append(f"{ts}  {msg}")
    if len(log_buffer) > 100: log_buffer.pop(0)
    logger.info(msg)


# ─────────────────────────────────────────────────────────
#  SUPABASE
# ─────────────────────────────────────────────────────────

def sb_headers():
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }

def sb_upsert(table, data):
    try:
        h = sb_headers(); h["Prefer"] = "resolution=merge-duplicates"
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=h, json=data, timeout=10)
        if r.status_code not in (200, 201):
            logger.warning(f"Supabase {table}: {r.status_code}")
    except Exception as e:
        logger.error(f"Supabase upsert error: {e}")

def sb_insert(table, data):
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), json=data, timeout=10)
        if r.status_code not in (200, 201):
            logger.warning(f"Supabase insert {table}: {r.status_code}")
        else:
            return r.json() if r.text else None
    except Exception as e:
        logger.error(f"Supabase insert error: {e}")

def sb_select(table, params=""):
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=sb_headers(), timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        logger.error(f"Supabase select error: {e}")
        return []

def sb_delete(table, params):
    try:
        r = requests.delete(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=sb_headers(), timeout=10)
        return r.status_code in (200, 204)
    except Exception as e:
        logger.error(f"Supabase delete error: {e}")
        return False


# ─────────────────────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────────────────────

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        logger.warning(f"Telegram error: {e}")


# ─────────────────────────────────────────────────────────
#  ANDMED
# ─────────────────────────────────────────────────────────

_data_cache = {"df": None, "updated": 0}
_price_cache = {"price": 0.0, "updated": 0}

def get_gold_data():
    global _data_cache
    now = time.time()
    if now - _data_cache["updated"] < 300 and _data_cache["df"] is not None:
        return _data_cache["df"]
    try:
        url = f"https://api.twelvedata.com/time_series"
        params = {
            "symbol":     "XAU/USD",
            "interval":   "1h",
            "outputsize": 100,
            "apikey":     TWELVEDATA_KEY,
        }
        r = requests.get(url, params=params, timeout=15)
        data = r.json()
        if data.get("status") == "error":
            logger.error(f"TwelveData error: {data.get('message')}")
            return _data_cache["df"]
        values = data.get("values", [])
        if not values:
            return _data_cache["df"]
        rows = []
        for v in reversed(values):
            rows.append({
                "open":   float(v["open"]),
                "high":   float(v["high"]),
                "low":    float(v["low"]),
                "close":  float(v["close"]),
                "volume": 0,
            })
        df = pd.DataFrame(rows)
        df.index = pd.to_datetime([v["datetime"] for v in reversed(values)], utc=True)
        _data_cache = {"df": df, "updated": now}
        add_log(f"📡 TwelveData: {len(df)} küünalt laetud")
        return df
    except Exception as e:
        logger.error(f"TwelveData data error: {e}")
        return _data_cache["df"]

def get_current_price():
    global _price_cache
    now = time.time()
    if now - _price_cache["updated"] < 60 and _price_cache["price"] > 0:
        return _price_cache["price"]
    try:
        url = f"https://api.twelvedata.com/price"
        params = {"symbol": "XAU/USD", "apikey": TWELVEDATA_KEY}
        r = requests.get(url, params=params, timeout=10)
        data = r.json()
        price = float(data.get("price", 0))
        if price > 0:
            _price_cache = {"price": price, "updated": now}
            return price
    except Exception as e:
        logger.error(f"TwelveData price error: {e}")
    return _price_cache["price"]


# ─────────────────────────────────────────────────────────
#  TREND
# ─────────────────────────────────────────────────────────

def get_trend(df):
    if df is None or len(df) < TREND_PERIOD + 2:
        return "neutral"
    now = float(df["close"].iloc[-1])
    ago = float(df["close"].iloc[-TREND_PERIOD-1])
    chg = (now - ago) / ago * 100
    if chg >  TREND_THRESH: return "bull"
    if chg < -TREND_THRESH: return "bear"
    return "neutral"


# ─────────────────────────────────────────────────────────
#  GRID STATE (Supabase'is)
# ─────────────────────────────────────────────────────────

def get_grid_state():
    rows = sb_select("bot_state", "id=eq.1&select=risk")
    if rows and rows[0].get("risk"):
        state = rows[0]["risk"]
        if "grid" in state:
            return state["grid"]
    return None

def save_grid_state(state):
    try:
        rows = sb_select("bot_state", "id=eq.1&select=risk")
        existing_risk = {}
        if rows and rows[0].get("risk"):
            existing_risk = rows[0]["risk"]
        existing_risk["grid"] = state
        sb_upsert("bot_state", {"id": 1, "risk": existing_risk})
    except Exception as e:
        logger.error(f"save_grid_state error: {e}")
        sb_upsert("bot_state", {"id": 1, "risk": {"grid": state}})

def get_open_positions():
    return sb_select("signals", "executed=eq.false&order=created_at.asc")

def get_balance():
    rows = sb_select("bot_state", "id=eq.1&select=balance")
    if rows and rows[0].get("balance"):
        return float(rows[0]["balance"])
    return ACCOUNT_BALANCE

def setup_grid(center, trend):
    pending = {}
    if trend in ("bull", "neutral"):
        for i in range(1, GRID_LEVELS + 1):
            level = round(center - i * GRID_SIZE, 2)
            pending[str(level)] = "buy"
    if trend in ("bear", "neutral"):
        for i in range(1, GRID_LEVELS + 1):
            level = round(center + i * GRID_SIZE, 2)
            pending[str(level)] = "sell"
    return pending


# ─────────────────────────────────────────────────────────
#  GRID LOOGIKA
# ─────────────────────────────────────────────────────────

def check_and_trade(price, high, low, trend):
    """
    Peamine grid loogika:
    1. Kontrolli kas pending order triggerdus
    2. Kontrolli kas avatud positsioon sai TP
    3. Kontrolli floating loss kaitset
    4. Trend muutus → reseta grid
    """
    grid_state = get_grid_state()
    balance    = get_balance()
    now        = datetime.now(timezone.utc)

    if grid_state is None:
        if trend == "neutral":
            add_log(f"⏳ Ootan selget trendi... (praegu neutral)")
            return
        center = round(price / GRID_SIZE) * GRID_SIZE
        pending = setup_grid(center, trend)
        grid_state = {
            "center":        center,
            "trend":         trend,
            "pending":       pending,
            "initialized_at": now.isoformat(),
        }
        save_grid_state(grid_state)
        add_log(f"🔲 Grid initsialiseeritud @ ${center:.0f} | trend: {trend}")
        send_telegram(
            f"🔲 <b>NEMSIS Grid initsialiseeritud</b>\n"
            f"Keskpunkt: <b>${center:.0f}</b>\n"
            f"Trend: <b>{trend}</b>\n"
            f"Grid: ${GRID_SIZE} sammud | {GRID_LEVELS} taset\n"
            f"Balance: <b>{balance:.2f}€</b>"
        )
        return

    pending      = grid_state.get("pending", {})
    grid_trend   = grid_state.get("trend", "neutral")

    if trend != grid_trend and trend != "neutral":
        add_log(f"🔄 Trend muutus {grid_trend} → {trend} — resetan gridi")
        open_pos = get_open_positions()
        closed_count = 0
        for pos in open_pos:
            entry     = float(pos.get("entry", 0))
            direction = pos.get("direction", "buy")
            fl = (price-entry)*LOT_SIZE*100 if direction=="buy" else (entry-price)*LOT_SIZE*100
            if fl < 0:
                balance = round(balance + fl, 2)
                sb_upsert("signals", {"id": pos["id"], "executed": True})
                sb_upsert("bot_state", {"id": 1, "balance": balance})
                closed_count += 1
                add_log(f"❌ Trend sulgemine: {direction.upper()} @ {entry:.0f}  PnL: {fl:+.2f}€")
        new_center = round(price / GRID_SIZE) * GRID_SIZE
        new_pending = setup_grid(new_center, trend)
        grid_state = {
            "center":  new_center,
            "trend":   trend,
            "pending": new_pending,
            "reset_at": now.isoformat(),
        }
        save_grid_state(grid_state)
        send_telegram(
            f"🔄 <b>Grid reset — trend muutus</b>\n"
            f"{grid_trend.upper()} → {trend.upper()}\n"
            f"Uus keskpunkt: ${new_center:.0f}\n"
            f"Suletud kahjumlikud: {closed_count}\n"
            f"Balance: {balance:.2f}€"
        )
        return

    open_pos = get_open_positions()
    for pos in open_pos:
        entry     = float(pos.get("entry", 0))
        tp        = float(pos.get("tp", 0))
        direction = pos.get("direction", "buy")
        pos_id    = pos.get("id")

        tp_hit = (high >= tp) if direction=="buy" else (low <= tp)
        if tp_hit:
            lot = get_compound_lot(balance)
            pnl = GRID_SIZE * lot * 100
            balance = round(balance + pnl, 2)
            sb_upsert("signals", {"id": pos_id, "executed": True})
            sb_upsert("bot_state", {"id": 1, "balance": balance})
            add_log(f"✅ TP: {direction.upper()} @ {entry:.0f} → {tp:.0f}  lot:{lot}  +{pnl:.2f}€  Bal: {balance:.2f}€")
            send_telegram(
                f"✅ <b>Grid TP!</b>\n"
                f"{direction.upper()} @ {entry:.0f} → {tp:.0f}\n"
                f"Lot: <b>{lot}</b>  PnL: <b>+{pnl:.2f}€</b>  |  Balance: <b>{balance:.2f}€</b>"
            )
            opp = "sell" if direction=="buy" else "buy"
            if trend=="bull" and opp=="sell": pass
            elif trend=="bear" and opp=="buy": pass
            else:
                pending[str(tp)] = opp
                grid_state["pending"] = pending
                save_grid_state(grid_state)
            continue

        fl = (price-entry)*LOT_SIZE*100 if direction=="buy" else (entry-price)*LOT_SIZE*100
        scaled_max = get_scaled_max_float(balance)
        if fl < -scaled_max:
            balance = round(balance + fl, 2)
            sb_upsert("signals", {"id": pos_id, "executed": True})
            sb_upsert("bot_state", {"id": 1, "balance": balance})
            add_log(f"🛡 Float stop: {direction.upper()} @ {entry:.0f}  {fl:+.2f}€")
            send_telegram(
                f"🛡 <b>Float stop</b>\n"
                f"{direction.upper()} @ {entry:.0f}  PnL: <b>{fl:+.2f}€</b>\n"
                f"Balance: <b>{balance:.2f}€</b>"
            )

    triggered_levels = []
    for level_str, direction in list(pending.items()):
        level = float(level_str)
        if trend=="bull" and direction=="sell": continue
        if trend=="bear" and direction=="buy":  continue
        hit = (direction=="buy" and low<=level) or (direction=="sell" and high>=level)
        if not hit: continue
        open_same = [p for p in get_open_positions() if p.get("direction")==direction]
        if len(open_same) >= GRID_LEVELS:
            add_log(f"— Max {GRID_LEVELS} {direction} positsiooni — ei ava")
            continue
        tp_level = round(level + GRID_SIZE if direction=="buy" else level - GRID_SIZE, 2)
        sb_insert("signals", {
            "direction":  direction,
            "entry":      level,
            "sl":         round(level - GRID_SIZE*3 if direction=="buy" else level + GRID_SIZE*3, 2),
            "tp":         tp_level,
            "rr":         3.0,
            "atr":        GRID_SIZE,
            "lot":        get_compound_lot(balance),
            "score":      0,
            "regime":     "grid",
            "session":    f"grid_{trend}",
            "executed":   False,
            "breakeven":  False,
        })
        triggered_levels.append(level_str)
        add_log(f"📊 Grid order: {direction.upper()} @ {level:.0f}  TP: {tp_level:.0f}")
        send_telegram(
            f"📊 <b>Grid order avatud</b>\n"
            f"{direction.upper()} @ <b>{level:.0f}</b>\n"
            f"TP: <b>{tp_level:.0f}</b>  (+${GRID_SIZE:.0f})\n"
            f"Trend: {trend} | Balance: {balance:.2f}€"
        )

    for level_str in triggered_levels:
        if level_str in pending:
            del pending[level_str]

    if triggered_levels:
        grid_state["pending"] = pending
        save_grid_state(grid_state)


# ─────────────────────────────────────────────────────────
#  STATS
# ─────────────────────────────────────────────────────────

def get_stats():
    trades = sb_select("trades", "order=created_at.desc&limit=100")
    if not trades: return {"total": 0, "net_pnl": 0}
    pnls = [float(t.get("pnl", 0) or 0) for t in trades]
    wins = [p for p in pnls if p > 0]
    return {
        "total":      len(trades),
        "wins":       len(wins),
        "net_pnl":    round(sum(pnls), 2),
        "win_rate":   round(len(wins)/len(trades)*100, 1) if trades else 0,
    }


# ─────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────

def main():
    add_log("🚀 NEMSIS v3 — Grid Trading Bot started")
    add_log(f"📐 Grid: ${GRID_SIZE} sammud | {GRID_LEVELS} taset | Lot: {LOT_SIZE}")
    add_log(f"🛡 Max float loss: ${MAX_FLOAT_LOSS}€ per positsioon")
    add_log(f"🤖 Claude AI: {'AKTIIVNE' if ANTHROPIC_KEY else 'PUUDUB'}")

    balance = get_balance()
    add_log(f"💼 Balance: {balance:.2f}€")

    send_telegram(
        f"🚀 <b>NEMSIS v3 Grid Bot</b> started!\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📐 Grid: <b>${GRID_SIZE:.0f}</b> sammud | <b>{GRID_LEVELS}</b> taset\n"
        f"🎯 TP: +${GRID_SIZE:.0f} per tehing\n"
        f"🛡 Max float: <b>{MAX_FLOAT_LOSS}€</b>\n"
        f"🤖 Claude AI: <b>{'AKTIIVNE' if ANTHROPIC_KEY else 'PUUDUB'}</b>\n"
        f"💼 Balance: <b>{balance:.2f}€</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Strateegia: Trend-Aware Grid + Claude AI"
    )

    rows = sb_select("bot_state", "id=eq.1&select=balance")
    if not rows or not rows[0].get("balance"):
        sb_upsert("bot_state", {"id": 1, "balance": balance})

    scan_count = 0

    while True:
        try:
            scan_count += 1
            now = datetime.now(timezone.utc)
            add_log(f"⏱ Scan #{scan_count}...")

            df = get_gold_data()
            if df is None or len(df) < 10:
                add_log("⚠️ Andmed puuduvad, ootan...")
                time.sleep(SCAN_INTERVAL)
                continue

            price = get_current_price()
            if price == 0:
                price = float(df["close"].iloc[-1])

            calc_current_atr(df)
            vol_mult = get_vol_multiplier()
            if vol_mult > 1.0:
                add_log(f"⚡ Kõrge volatiilsus — lot {vol_mult}x")

            high = float(df["high"].iloc[-1])
            low  = float(df["low"].iloc[-1])
            trend = get_trend(df)

            add_log(f"💰 Gold: ${price:.2f} | Trend: {trend} | H: {high:.2f} L: {low:.2f}")

            # Claude AI analüüs iga 30 min
            atr_val = float(_atr_history[-1]) if _atr_history else 20.0
            session = "london" if 7 <= now.hour < 13 else "new_york" if 13 <= now.hour < 20 else "asia"
            claude_bias, _ = get_claude_bias(price, trend, atr_val, session)

            # Kui Claude ütleb buy/sell ja trend on neutral → kasuta Claude bias
            effective_trend = trend
            if claude_bias in ("buy", "sell") and trend == "neutral":
                effective_trend = "bull" if claude_bias == "buy" else "bear"
                add_log(f"🤖 Claude override: neutral → {effective_trend}")

            # Grid loogika
            check_and_trade(price, high, low, effective_trend)

            balance = get_balance()
            open_pos = get_open_positions()
            floating = sum(
                (price-float(p.get("entry",0)))*LOT_SIZE*100
                if p.get("direction")=="buy"
                else (float(p.get("entry",0))-price)*LOT_SIZE*100
                for p in open_pos
            )

            sb_upsert("bot_state", {
                "id":         1,
                "updated_at": now.isoformat(),
                "price":      round(price, 2),
                "last_scan":  now.strftime("%H:%M:%S UTC"),
                "scanning":   False,
                "log":        log_buffer[-20:],
                "stats": {
                    "balance":       balance,
                    "equity":        round(balance + floating, 2),
                    "floating":      round(floating, 2),
                    "open_positions": len(open_pos),
                    "trend":         trend,
                    "claude_bias":   claude_bias,
                    "price":         round(price, 2),
                }
            })

            # Päevane kokkuvõte kell 8:00 UTC
            if now.hour == 8 and now.minute == 0:
                send_telegram(
                    f"🌅 <b>NEMSIS Päevane kokkuvõte</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💼 Balance: <b>{balance:.2f}€</b>\n"
                    f"📊 Equity: <b>{round(balance+floating,2):.2f}€</b>\n"
                    f"📉 Floating: <b>{floating:+.2f}€</b>\n"
                    f"🔓 Avatud: <b>{len(open_pos)}</b>\n"
                    f"💰 Gold: <b>${price:.2f}</b>\n"
                    f"📊 Trend: <b>{trend}</b>\n"
                    f"🤖 Claude: <b>{claude_bias}</b>\n"
                    f"⏰ {now.strftime('%d.%m.%Y')} UTC"
                )

        except Exception as e:
            add_log(f"❌ Error: {e}")
            logger.exception(e)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
