"""
NEMSIS v4 — Multi-Strategy Trading Bot
Railway 24/7 | Supabase | Telegram | cTrader ready

Strateegiad:
- XAUUSD: Trend-Aware Grid (kuld)
- AUDCAD, AUDNZD, EURGBP, EURCHF, NZDCAD: Mean Reversion
"""
import sys, os, json, time, logging, requests
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from config import INSTRUMENTS, MEANREV_CONFIG, GRID_CONFIG
from strategy_meanrev import MeanRevStrategy

# ── Env vars ─────────────────────────────────────────────
SUPABASE_URL     = os.environ.get("SUPABASE_URL", "https://xqinzjaqorjqaexeoyqc.supabase.co")
SUPABASE_KEY     = os.environ.get("SUPABASE_KEY", "sb_secret_geYNl5euHLVWXQtone_N0g_K5nB0Zel")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "7502951774:AAFEdMlowZumpFlLm817UEP4ws40SeZtROo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7638697143")
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "60"))
ACCOUNT_BALANCE  = float(os.environ.get("ACCOUNT_BALANCE", "500"))
TWELVEDATA_KEY   = os.environ.get("TWELVEDATA_KEY", "74935ad641d14749a66009b4abc84ce7")
ANTHROPIC_KEY    = os.environ.get("ANTHROPIC_KEY", "")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NEMSIS_V4")
log_buffer = []

def add_log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    log_buffer.append(f"{ts}  {msg}")
    if len(log_buffer) > 200: log_buffer.pop(0)
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
        if r.status_code not in (200,201):
            logger.warning(f"SB {table}: {r.status_code}")
    except Exception as e:
        logger.error(f"SB upsert: {e}")

def sb_insert(table, data):
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), json=data, timeout=10)
        if r.status_code not in (200,201):
            logger.warning(f"SB insert {table}: {r.status_code}")
    except Exception as e:
        logger.error(f"SB insert: {e}")

def sb_select(table, params=""):
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=sb_headers(), timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        logger.error(f"SB select: {e}")
        return []

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"},
            timeout=10
        )
    except Exception as e:
        logger.warning(f"Telegram: {e}")

def get_balance():
    rows = sb_select("bot_state", "id=eq.1&select=balance")
    if rows and rows[0].get("balance"):
        return float(rows[0]["balance"])
    return ACCOUNT_BALANCE

# ─────────────────────────────────────────────────────────
#  ANDMED — TwelveData
# ─────────────────────────────────────────────────────────

_cache = {}

def get_data(symbol_td, interval="1h", outputsize=100):
    global _cache
    now = time.time()
    cache_key = symbol_td
    if cache_key in _cache and now - _cache[cache_key]["updated"] < 300:
        return _cache[cache_key]["df"]
    try:
        r = requests.get("https://api.twelvedata.com/time_series", params={
            "symbol": symbol_td, "interval": interval,
            "outputsize": outputsize, "apikey": TWELVEDATA_KEY
        }, timeout=15)
        data = r.json()
        if data.get("status") == "error":
            logger.error(f"TwelveData {symbol_td}: {data.get('message')}")
            return _cache.get(cache_key, {}).get("df")
        values = data.get("values", [])
        if not values: return None
        rows = [{"open": float(v["open"]), "high": float(v["high"]),
                 "low": float(v["low"]), "close": float(v["close"])}
                for v in reversed(values)]
        df = pd.DataFrame(rows)
        df.index = pd.to_datetime([v["datetime"] for v in reversed(values)], utc=True)
        _cache[cache_key] = {"df": df, "updated": now}
        return df
    except Exception as e:
        logger.error(f"TwelveData {symbol_td}: {e}")
        return _cache.get(cache_key, {}).get("df")

def get_price(symbol_td):
    try:
        r = requests.get("https://api.twelvedata.com/price",
            params={"symbol": symbol_td, "apikey": TWELVEDATA_KEY}, timeout=10)
        return float(r.json().get("price", 0))
    except:
        return 0.0

# ─────────────────────────────────────────────────────────
#  GOLD GRID STRATEEGIA
# ─────────────────────────────────────────────────────────

_atr_history = []
_claude_cache = {"bias": "neutral", "reason": "", "updated": 0}

def get_trend(df):
    period = GRID_CONFIG["trend_period"]
    thresh = INSTRUMENTS["XAUUSD"]["trend_thresh"]
    if df is None or len(df) < period+2: return "neutral"
    now = float(df["close"].iloc[-1])
    ago = float(df["close"].iloc[-period-1])
    chg = (now-ago)/ago*100
    if chg > thresh: return "bull"
    if chg < -thresh: return "bear"
    return "neutral"

def calc_atr_gold(df):
    if len(df) < 15: return 1.0
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"]  - df["close"].shift()).abs()
    tr = pd.concat([hl,hc,lc],axis=1).max(axis=1)
    atr = float(tr.tail(14).mean())
    _atr_history.append(atr)
    if len(_atr_history) > 100: _atr_history.pop(0)
    return atr

def get_vol_mult():
    if len(_atr_history) < GRID_CONFIG["vol_thresh"]: return 1.0
    avg = sum(_atr_history[-20:])/20
    cur = _atr_history[-1]
    return GRID_CONFIG["vol_boost"] if cur > avg*GRID_CONFIG["vol_thresh"] else 1.0

def get_compound_lot(balance):
    base = round(max(0.01, (balance/ACCOUNT_BALANCE)*0.01), 3)
    return round(base * get_vol_mult(), 3)

def get_grid_state():
    rows = sb_select("bot_state", "id=eq.1&select=risk")
    if rows and rows[0].get("risk") and "grid" in rows[0]["risk"]:
        return rows[0]["risk"]["grid"]
    return None

def save_grid_state(state):
    try:
        rows = sb_select("bot_state", "id=eq.1&select=risk")
        risk = rows[0].get("risk", {}) if rows else {}
        risk["grid"] = state
        sb_upsert("bot_state", {"id": 1, "risk": risk})
    except Exception as e:
        logger.error(f"save_grid: {e}")

def setup_grid(center, trend):
    gs = INSTRUMENTS["XAUUSD"]["grid_size"]
    gl = GRID_CONFIG["levels"]
    p = {}
    if trend in ("bull","neutral"):
        for i in range(1, gl+1): p[str(round(center-i*gs,2))] = "buy"
    if trend in ("bear","neutral"):
        for i in range(1, gl+1): p[str(round(center+i*gs,2))] = "sell"
    return p

def get_gold_positions():
    return sb_select("signals", "executed=eq.false&regime=eq.grid&order=created_at.asc")

def get_claude_bias(price, trend, atr, session):
    global _claude_cache
    now = time.time()
    if now - _claude_cache["updated"] < 30*60:
        return _claude_cache["bias"], _claude_cache["reason"]
    if not ANTHROPIC_KEY:
        return "neutral", ""
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
        _claude_cache = {"bias":bias,"reason":reason,"updated":now}
        add_log(f"🤖 Claude: {bias} — {reason[:40]}")
        send_telegram(f"🤖 <b>Claude AI</b>\nBias: <b>{bias.upper()}</b>\n{reason}")
        return bias, reason
    except Exception as e:
        logger.error(f"Claude: {e}")
        return "neutral", ""

def run_gold_grid(price, high, low, now):
    cfg    = INSTRUMENTS["XAUUSD"]
    gs     = cfg["grid_size"]
    gl     = GRID_CONFIG["levels"]
    mfl    = GRID_CONFIG["max_float"]

    df     = get_data(cfg["symbol_td"])
    if df is None: return
    calc_atr_gold(df)
    trend  = get_trend(df)

    # Claude AI
    atr_val = _atr_history[-1] if _atr_history else 20.0
    session = "london" if 7 <= now.hour < 13 else "new_york" if 13 <= now.hour < 20 else "asia"
    bias, _ = get_claude_bias(price, trend, atr_val, session)
    effective_trend = "bull" if bias=="buy" and trend=="neutral" else \
                      "bear" if bias=="sell" and trend=="neutral" else trend

    balance    = get_balance()
    grid_state = get_grid_state()

    if grid_state is None:
        if effective_trend == "neutral": return
        center  = round(price/gs)*gs
        pending = setup_grid(center, effective_trend)
        save_grid_state({"center":center,"trend":effective_trend,"pending":pending})
        add_log(f"🔲 Gold grid initsialiseeritud @ ${center:.0f} | {effective_trend}")
        return

    pending    = grid_state.get("pending", {})
    grid_trend = grid_state.get("trend", "neutral")

    if effective_trend != grid_trend and effective_trend != "neutral":
        open_pos = get_gold_positions()
        for pos in open_pos:
            entry = float(pos.get("entry",0))
            d     = pos.get("direction","buy")
            fl    = (price-entry)*get_compound_lot(balance)*100 if d=="buy" else (entry-price)*get_compound_lot(balance)*100
            if fl < 0:
                balance = round(balance+fl, 2)
                sb_upsert("signals", {"id":pos["id"],"executed":True})
                sb_upsert("bot_state", {"id":1,"balance":balance})
        new_c = round(price/gs)*gs
        save_grid_state({"center":new_c,"trend":effective_trend,"pending":setup_grid(new_c, effective_trend)})
        add_log(f"🔄 Gold grid reset: {grid_trend}→{effective_trend}")
        return

    open_pos = get_gold_positions()
    for pos in open_pos:
        entry = float(pos.get("entry",0))
        tp    = float(pos.get("tp",0))
        d     = pos.get("direction","buy")
        pid   = pos.get("id")
        lot   = get_compound_lot(balance)

        if (high>=tp if d=="buy" else low<=tp):
            pnl     = gs*lot*100
            balance = round(balance+pnl, 2)
            sb_upsert("signals", {"id":pid,"executed":True})
            sb_upsert("bot_state", {"id":1,"balance":balance})
            add_log(f"✅ Gold TP: {d.upper()} @ {entry:.0f}→{tp:.0f}  +{pnl:.2f}€")
            send_telegram(f"✅ <b>Gold TP!</b>\n{d.upper()} @ {entry:.0f}→{tp:.0f}\n+<b>{pnl:.2f}€</b> | {balance:.2f}€")
            opp = "sell" if d=="buy" else "buy"
            if not (effective_trend=="bull" and opp=="sell") and not (effective_trend=="bear" and opp=="buy"):
                pending[str(tp)] = opp
                grid_state["pending"] = pending
                save_grid_state(grid_state)
            continue

        fl = (price-entry)*lot*100 if d=="buy" else (entry-price)*lot*100
        if fl < -mfl*(balance/ACCOUNT_BALANCE):
            balance = round(balance+fl, 2)
            sb_upsert("signals", {"id":pid,"executed":True})
            sb_upsert("bot_state", {"id":1,"balance":balance})
            add_log(f"🛡 Gold float stop: {d.upper()} @ {entry:.0f}  {fl:+.2f}€")

    triggered = []
    for level_str, direction in list(pending.items()):
        level = float(level_str)
        if effective_trend=="bull" and direction=="sell": continue
        if effective_trend=="bear" and direction=="buy":  continue
        hit = (direction=="buy" and low<=level) or (direction=="sell" and high>=level)
        if not hit: continue
        same = [p for p in get_gold_positions() if p.get("direction")==direction]
        if len(same) >= gl: continue
        lot = get_compound_lot(balance)
        tp  = round(level+gs if direction=="buy" else level-gs, 2)
        sb_insert("signals", {
            "direction":direction,"entry":level,"tp":tp,
            "sl":round(level-gs*3 if direction=="buy" else level+gs*3,2),
            "lot":lot,"regime":"grid","session":f"gold_{effective_trend}",
            "executed":False,"breakeven":False,"atr":gs,"score":0,"rr":3.0,
        })
        triggered.append(level_str)
        add_log(f"📊 Gold order: {direction.upper()} @ {level:.0f}  TP:{tp:.0f}")
        send_telegram(f"📊 <b>Gold Grid Order</b>\n{direction.upper()} @ <b>{level:.0f}</b>\nTP: <b>{tp:.0f}</b> | {effective_trend}")

    for ls in triggered:
        if ls in pending: del pending[ls]
    if triggered:
        grid_state["pending"] = pending
        save_grid_state(grid_state)

# ─────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────

def main():
    add_log("🚀 NEMSIS v4 — Multi-Strategy Bot")
    add_log(f"📊 Instrumendid: {', '.join(k for k,v in INSTRUMENTS.items() if v['enabled'])}")
    add_log(f"🤖 Claude AI: {'ON' if ANTHROPIC_KEY else 'OFF'}")

    balance = get_balance()
    add_log(f"💼 Balance: {balance:.2f}€")

    send_telegram(
        f"🚀 <b>NEMSIS v4 käivitus!</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Instrumendid: <b>{len([v for v in INSTRUMENTS.values() if v['enabled']])}</b>\n"
        f"🥇 Gold: Trend Grid\n"
        f"💱 Forex: Mean Reversion (5 paari)\n"
        f"🤖 Claude AI: <b>{'ON' if ANTHROPIC_KEY else 'OFF'}</b>\n"
        f"💼 Balance: <b>{balance:.2f}€</b>"
    )

    rows = sb_select("bot_state", "id=eq.1&select=balance")
    if not rows or not rows[0].get("balance"):
        sb_upsert("bot_state", {"id":1,"balance":balance})

    # Initsialiseeri mean reversion strateegiad
    mr_strategies = {}
    for symbol, cfg in INSTRUMENTS.items():
        if cfg["strategy"] == "meanrev" and cfg["enabled"]:
            mr_strategies[symbol] = MeanRevStrategy(
                symbol=symbol, cfg=cfg, mr_cfg=MEANREV_CONFIG,
                logger=logger, add_log=add_log, send_telegram=send_telegram,
                sb_select=sb_select, sb_insert=sb_insert, sb_upsert=sb_upsert,
                get_balance=get_balance,
            )
            add_log(f"✅ {symbol} mean reversion strateegia valmis")

    scan_count = 0

    while True:
        try:
            scan_count += 1
            now = datetime.now(timezone.utc)
            add_log(f"⏱ Scan #{scan_count} — {now.strftime('%H:%M')} UTC")

            # ── GOLD GRID ──
            if INSTRUMENTS["XAUUSD"]["enabled"]:
                try:
                    df_gold = get_data("XAU/USD")
                    price_gold = get_price("XAU/USD")
                    if price_gold == 0 and df_gold is not None:
                        price_gold = float(df_gold["close"].iloc[-1])
                    if price_gold > 0 and df_gold is not None:
                        high_gold = float(df_gold["high"].iloc[-1])
                        low_gold  = float(df_gold["low"].iloc[-1])
                        add_log(f"🥇 Gold: ${price_gold:.2f}")
                        run_gold_grid(price_gold, high_gold, low_gold, now)
                except Exception as e:
                    add_log(f"❌ Gold error: {e}")

            # ── FOREX MEAN REVERSION ──
            for symbol, strategy in mr_strategies.items():
                try:
                    cfg = INSTRUMENTS[symbol]
                    interval = cfg.get("interval", "1h")
                    outputsize = 200 if interval == "15min" else 100
                    df  = get_data(cfg["symbol_td"], interval=interval, outputsize=outputsize)
                    price = get_price(cfg["symbol_td"])
                    if price == 0 and df is not None:
                        price = float(df["close"].iloc[-1])
                    if price > 0 and df is not None:
                        high = float(df["high"].iloc[-1])
                        low  = float(df["low"].iloc[-1])
                        add_log(f"💱 {symbol}: {price:.5f}")
                        strategy.run(price, high, low, now)
                except Exception as e:
                    add_log(f"❌ {symbol} error: {e}")

            # Dashboard uuendus
            balance = get_balance()
            open_all = sb_select("signals", "executed=eq.false")
            gold_pos  = [p for p in open_all if p.get("regime")=="grid"]
            forex_pos = [p for p in open_all if p.get("regime")=="meanrev"]

            sb_upsert("bot_state", {
                "id": 1, "updated_at": now.isoformat(),
                "last_scan": now.strftime("%H:%M:%S UTC"),
                "stats": {
                    "balance":       balance,
                    "gold_positions":  len(gold_pos),
                    "forex_positions": len(forex_pos),
                    "scan":          scan_count,
                }
            })

            # Päevane kokkuvõte 8:00 UTC
            if now.hour == 8 and now.minute == 0:
                send_telegram(
                    f"🌅 <b>NEMSIS v4 Päevane kokkuvõte</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💼 Balance: <b>{balance:.2f}€</b>\n"
                    f"🥇 Gold positsioonid: <b>{len(gold_pos)}</b>\n"
                    f"💱 Forex positsioonid: <b>{len(forex_pos)}</b>\n"
                    f"⏰ {now.strftime('%d.%m.%Y')} UTC"
                )

        except Exception as e:
            add_log(f"❌ Main error: {e}")
            logger.exception(e)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
