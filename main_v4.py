"""
NEMSIS v4 — Multi-Strategy Trading Bot
Railway 24/7 | Supabase | Telegram | cTrader ready

Strateegiad:
- XAUUSD: Trend-Aware Grid (kuld)
- AUDCAD, AUDNZD, EURGBP, EURCHF, NZDCAD: Mean Reversion
"""
from dotenv import load_dotenv
load_dotenv()
import sys, os, json, time, logging, requests
from datetime import datetime, timezone
import pandas as pd
import numpy as np

from config import INSTRUMENTS, MEANREV_CONFIG, GRID_CONFIG
from strategy_meanrev import MeanRevStrategy
import mt5_connector as ct

# ── Env vars ─────────────────────────────────────────────
SUPABASE_URL     = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY     = os.environ.get("SUPABASE_KEY", "")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "60"))
ACCOUNT_BALANCE  = float(os.environ.get("ACCOUNT_BALANCE", "200"))
TWELVEDATA_KEY   = os.environ.get("TWELVEDATA_KEY", "")
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
            logger.warning(f"SB {table}: {r.status_code} — {r.text[:500]}")
    except Exception as e:
        logger.error(f"SB upsert: {e}")

def sb_insert(table, data):
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), json=data, timeout=10)
        if r.status_code not in (200,201):
            # Logi PÄRIS veateade (Supabase/PostgREST vastuse sisu), mitte ainult
            # staatuskoodi — muidu ei tea kunagi, MIKS päring tagasi lükati.
            logger.warning(f"SB insert {table}: {r.status_code} — {r.text[:500]}")
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
    mt5_balance = ct.get_account_balance()
    if mt5_balance and mt5_balance > 0:
        return float(mt5_balance)
    rows = sb_select("bot_state", "id=eq.1&select=balance")
    if rows and rows[0].get("balance"):
        return float(rows[0]["balance"])
    return ACCOUNT_BALANCE

# ─────────────────────────────────────────────────────────
#  CIRCUIT BREAKER
# ─────────────────────────────────────────────────────────

def get_circuit_state():
    """Loe circuit breaker olek Supabase-st."""
    rows = sb_select("bot_state", "id=eq.1&select=risk")
    if rows and rows[0].get("risk"):
        return rows[0]["risk"].get("circuit", {})
    return {}

def save_circuit_state(state):
    """Salvesta circuit breaker olek."""
    try:
        rows = sb_select("bot_state", "id=eq.1&select=risk")
        risk = rows[0].get("risk", {}) if rows else {}
        risk["circuit"] = state
        sb_upsert("bot_state", {"id": 1, "risk": risk})
    except Exception as e:
        logger.error(f"save_circuit: {e}")

def check_circuit_breaker(balance, now):
    """
    Kontrolli circuit breaker tingimusi EQUITY põhjal (mitte balance).
    Equity = balance + lahtiste positsioonide floating P&L.
    Tagastab True kui kauplema võib, False kui peab pausima.
    """
    # Kasuta equity-t — see näitab tegelikku drawdown-i reaalajas
    equity = get_account_equity()
    circuit = get_circuit_state()
    today = now.strftime("%Y-%m-%d")
    week  = now.strftime("%Y-W%W")

    # Initsialiseeri nädala algus
    if circuit.get("week") != week:
        circuit = {
            "week":              week,
            "week_start_balance": balance,
            "day":               today,
            "day_start_balance": balance,
            "paused_until_week": None,
            "paused_until_day":  None,
        }
        save_circuit_state(circuit)
        return True

    # Uuenda päeva algus kui uus päev
    if circuit.get("day") != today:
        circuit["day"] = today
        circuit["day_start_balance"] = balance
        circuit["paused_until_day"] = None
        save_circuit_state(circuit)

    # Kontrolli nädalane paus
    if circuit.get("paused_until_week") == week:
        add_log("⏸ Circuit breaker: nädalane paus aktiivselt")
        return False

    # Kontrolli päevane paus
    if circuit.get("paused_until_day") == today:
        add_log("⏸ Circuit breaker: päevane paus aktiivselt")
        return False

    week_start = float(circuit.get("week_start_balance", balance))
    day_start  = float(circuit.get("day_start_balance", balance))

    # Nädalane drawdown > 15% EQUITY järgi → paus ülejäänud nädalaks
    if week_start > 0 and (week_start - equity) / week_start > 0.15:
        circuit["paused_until_week"] = week
        save_circuit_state(circuit)
        msg = f"🛑 CIRCUIT BREAKER: equity -15% nädalas ({week_start:.2f}€ → equity {equity:.2f}€) — paus kuni nädala lõpuni!"
        add_log(msg)
        send_telegram(f"🛑 <b>CIRCUIT BREAKER AKTIVEERITUD</b>\n{msg}")
        return False

    # Päevane drawdown > 10% EQUITY järgi → paus ülejäänud päevaks
    if day_start > 0 and (day_start - equity) / day_start > 0.10:
        circuit["paused_until_day"] = today
        save_circuit_state(circuit)
        msg = f"⏸ Circuit breaker: equity -10% päevas ({day_start:.2f}€ → equity {equity:.2f}€) — paus tänaseks"
        add_log(msg)
        send_telegram(f"⏸ <b>Päevane paus</b>\n{msg}")
        return False

    return True

def get_risk_based_lot(balance, atr_dist, pip_value=100000, risk_pct=0.015):
    """
    Risk-põhine lot sizing: riski max 1.5% kontost per tehing.
    atr_dist: stop distance (price units)
    pip_value: 100000 forex, 100 gold
    """
    if atr_dist <= 0: return 0.01
    risk_amount = balance * risk_pct
    lot = risk_amount / (atr_dist * pip_value)
    return max(0.01, min(round(lot, 3), 0.10))

# ─────────────────────────────────────────────────────────
#  ANDMED — yfinance (tasuta, ei vaja API key)
# ─────────────────────────────────────────────────────────

_cache = {}
_scalp_cache = {"df": None, "updated": 0}

def get_data(symbol_td, interval="1h", outputsize=100):
    """Hangi ajaloolised andmed MT5-st — 30s timeout."""
    global _cache
    now = time.time()
    cache_key = f"{symbol_td}_{interval}"
    if cache_key in _cache and now - _cache[cache_key]["updated"] < 300:
        return _cache[cache_key]["df"]

    import threading
    result = [None]
    def _fetch():
        try:
            result[0] = ct.get_candles(symbol_td, interval, outputsize)
        except Exception as e:
            logger.error(f"get_candles viga: {e}")

    t = threading.Thread(target=_fetch, daemon=True)
    t.start()
    t.join(timeout=30)
    if t.is_alive():
        logger.error(f"MT5 andmepäring timeout ({symbol_td} {interval}) — kasutan cache")
        return _cache.get(cache_key, {}).get("df")

    df = result[0]
    if df is not None and not df.empty:
        _cache[cache_key] = {"df": df, "updated": now}
        return df

    return _cache.get(cache_key, {}).get("df")

def get_scalp_data():
    """Laeb Gold 5min andmeid scalping jaoks — 30s timeout."""
    global _scalp_cache
    now = time.time()
    if now - _scalp_cache["updated"] < 300 and _scalp_cache["df"] is not None:
        return _scalp_cache["df"]
    try:
        import threading
        result = [None]
        def _fetch():
            try:
                result[0] = ct.get_candles("XAU/USD", interval="5m", count=288)
            except Exception: pass
        t = threading.Thread(target=_fetch, daemon=True)
        t.start()
        t.join(timeout=30)
        if t.is_alive():
            logger.error("get_scalp_data timeout — kasutan cache")
            return _scalp_cache["df"]
        df = result[0]
        if df is None or df.empty: return _scalp_cache["df"]
        _scalp_cache = {"df": df, "updated": now}
        return df
    except Exception as e:
        logger.error(f"Scalp data: {e}")
        return _scalp_cache["df"]

def get_price(symbol_td):
    """Hangi hind — cTrader esimesena, TwelveData fallback."""
    try:
        price = ct.get_price_ctrader(symbol_td)
        if price > 0:
            return price
    except:
        pass
    # TwelveData fallback
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
_last_order_time = 0
_trend_history = []  # viimased trendid — vahetus vajab 3x kinnitust

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
    base = round(max(0.01, (balance/ACCOUNT_BALANCE)*0.01), 2)
    return round(base * get_vol_mult(), 2)

def get_scaled_max_float(balance):
    """Max floating loss skaleerub koos kontoga."""
    return GRID_CONFIG["max_float"] * (balance / ACCOUNT_BALANCE)

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


# ─────────────────────────────────────────────────────────
#  MT5 POSITSIOONIDE SÜNKRONISEERIMINE
# ─────────────────────────────────────────────────────────

def sync_mt5_positions():
    """
    Sünkroniseeri MT5 päris positsioonid Supabase signals-tabeliga.
    Kui MT5-s on positsioon suletud (TP/SL tabas), märgi Supabase-s executed=True.
    Tagastab MT5-s lahti olevate ticketite seti.
    """
    try:
        mt5_open = ct.get_open_positions()
        mt5_tickets = {p["ticket"] for p in mt5_open}

        # Loe Supabase-st kõik lahti positsioonid (executed=False)
        sb_open = sb_select("signals", "executed=eq.false&regime=eq.grid")
        if not sb_open:
            return mt5_tickets

        closed_found = False
        for pos in sb_open:
            ticket = pos.get("mt5_ticket")
            if ticket is None:
                continue  # vanad positsioonid ilma ticketita — jäta rahule
            if int(ticket) not in mt5_tickets:
                # MT5-s suletud aga Supabase-s lahti — märgi suletuks
                sb_upsert("signals", {"id": pos["id"], "executed": True})
                add_log(f"🔄 Sync: positsioon {ticket} suletud MT5 poolt → Supabase uuendatud")
                closed_found = True

        if closed_found:
            # Positsioon suleti broker'i enda TP/SL kaudu, enne kui bot ise jõudis
            # seda tuvastada — see haru ei arvutanud kunagi P&L-i balance'ile.
            # Sünkroniseeri balance otse päris MT5 kontoseisuga (juba kasutuses
            # ja tõestatud get_balance() funktsioonis), et dashboard ei jääks
            # vananenud numbrit näitama.
            real_balance = ct.get_account_balance()
            if real_balance and real_balance > 0:
                sb_upsert("bot_state", {"id": 1, "balance": round(float(real_balance), 2)})
                add_log(f"🔄 Sync: balance uuendatud päris MT5 väärtusega {real_balance:.2f}€")

        return mt5_tickets
    except Exception as e:
        logger.error(f"sync_mt5_positions viga: {e}")
        return set()


def get_account_equity():
    """Tagasta MT5 equity (balance + lahtiste positsioonide floating P&L)."""
    equity = ct.get_account_equity()
    if equity and equity > 0:
        return float(equity)
    # Fallback: balance (halvem aga parem kui 0)
    return get_balance()


def get_swing_levels(df, lookback=20):
    """
    Tagasta viimase `lookback` küünla swing low ja swing high.
    Kasutatakse SL-i paigutamiseks päris tugi/vastupanu taseme taha.
    """
    try:
        if df is None or len(df) < lookback:
            return None, None
        recent = df.tail(lookback)
        return float(recent["low"].min()), float(recent["high"].max())
    except Exception:
        return None, None


def calc_gold_tp_sl(direction, level, atr, swing_low, swing_high):
    """
    ATR-põhine TP + swing-põhine SL.
    TP = 2x ATR (min $30, max $100)
    SL = swing tase + $10 puhver, max $80 kaugusel
    """
    tp_dist = max(30.0, min(100.0, 2.0 * atr))
    sl_max  = 80.0
    buf     = 10.0

    if direction == "buy":
        tp = round(level + tp_dist, 2)
        if swing_low is not None and level - swing_low + buf <= sl_max and swing_low < level:
            sl = round(swing_low - buf, 2)
        else:
            sl = round(level - sl_max, 2)
    else:
        tp = round(level - tp_dist, 2)
        if swing_high is not None and swing_high - level + buf <= sl_max and swing_high > level:
            sl = round(swing_high + buf, 2)
        else:
            sl = round(level + sl_max, 2)
    return tp, sl


def send_grid_signals(center, trend, gs, tp_dist, sl_dist, lot):
    """
    Saada Telegrami valmis grid tasemed XTrend käsitsi sisestamiseks.
    Iga tase: BUY LIMIT hind / TP hind / SL hind / lot
    Kõik absoluuthinnad — kopeeri otse XTrend Price väljadesse.
    """
    gl = GRID_CONFIG["levels"]
    lines = [f"🎯 <b>NEMSIS GRID — {trend.upper()}</b>", f"Kese: ${center:.2f} | Lot: {lot}", ""]

    if trend == "bull":
        lines.append("<b>BUY LIMIT orderid</b> (kopeeri XTrend Price väljadesse):")
        for i in range(1, gl+1):
            entry = round(center - i*gs, 2)
            tp    = round(entry + tp_dist, 2)
            sl    = round(entry - sl_dist, 2)
            lines.append(f"{i}. Entry <b>{entry}</b> / TP <b>{tp}</b> / SL <b>{sl}</b>")
    elif trend == "bear":
        lines.append("<b>SELL LIMIT orderid</b> (kopeeri XTrend Price väljadesse):")
        for i in range(1, gl+1):
            entry = round(center + i*gs, 2)
            tp    = round(entry - tp_dist, 2)
            sl    = round(entry + sl_dist, 2)
            lines.append(f"{i}. Entry <b>{entry}</b> / TP <b>{tp}</b> / SL <b>{sl}</b>")

    lines.append("")
    lines.append("⚠️ Sisesta Price väljadesse (mitte Pips). Profit väli näitab ≈ kinnitust.")
    lines.append("💡 Testiks pane esmalt 1 order, vaata et täitub, siis ülejäänud.")
    send_telegram("\n".join(lines))

def get_daily_halt_state():
    rows = sb_select("bot_state", "id=eq.1&select=risk")
    if rows and rows[0].get("risk") and "daily_gold_halt" in rows[0]["risk"]:
        return rows[0]["risk"]["daily_gold_halt"]
    return {"day": "", "equity": 0.0}

def save_daily_halt_state(state):
    try:
        rows = sb_select("bot_state", "id=eq.1&select=risk")
        risk = rows[0].get("risk", {}) if rows else {}
        risk["daily_gold_halt"] = state
        sb_upsert("bot_state", {"id": 1, "risk": risk})
    except Exception as e:
        logger.error(f"save_daily_halt: {e}")

def check_daily_equity_halt():
    """
    Peata kulla kauplemine kui päeva equity kahjum > 10%.
    Olek salvestatakse Supabase's (mitte mälu-globaalis), et püsiks
    bot restardi üle — varem lähtestus see iga restardiga, mis
    nõrgendas kaitset vaikselt just siis kui restart toimus halval päeval.
    """
    eq = ct.get_account_equity()
    if not eq: return False
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    state = get_daily_halt_state()
    if state.get("day") != today:
        state = {"day": today, "equity": eq}
        save_daily_halt_state(state)
        return False
    start = state.get("equity", 0)
    if start > 0 and (start - eq) / start > 0.10:
        add_log(f"🛑 PÄEVALIMIIT: equity {eq:.2f} on -10% päeva algusest {start:.2f} — kauplemine peatatud")
        return True
    return False

def run_gold_grid(price, high, low, now):
    # ── NÄDALAVAHETUS — reede 21:00 UTC sulge kõik, lau/püha ei kauple üldse ──
    # (sama muster mis strategy_meanrev.py-s forexile juba olemas —
    #  kuld seda seni ei omanud, mis põhjustas SL-tabamusi nädalavahetuse
    #  gap/thin-liquidity liikumisest)
    if now.weekday() == 4 and now.hour >= 21:
        open_pos = get_gold_positions()
        if open_pos:
            balance = get_balance()
            for pos in open_pos:
                entry = float(pos.get("entry", 0))
                d     = pos.get("direction", "buy")
                lot   = get_compound_lot(balance)
                fl    = (price-entry)*lot*100 if d == "buy" else (entry-price)*lot*100
                ticket = pos.get("mt5_ticket")
                close_ok = True
                if ticket:
                    close_ok = ct.close_position(int(ticket))
                    if not close_ok:
                        add_log(f"⚠️ Weekend sulgemine: MT5 positsioon {ticket} sulgemine ebaõnnestus")
                if close_ok:
                    balance = round(balance+fl, 2)
                    sb_upsert("signals", {"id": pos["id"], "executed": True})
                    sb_upsert("bot_state", {"id": 1, "balance": balance})
            add_log(f"🔒 Gold weekend sulgemine — {len(open_pos)} positsiooni suletud")
            send_telegram(f"🔒 <b>Gold weekend sulgemine</b>\n{len(open_pos)} positsiooni suletud enne nädalavahetust")
        return
    if now.weekday() in (5, 6):
        return

    if check_daily_equity_halt(): return
    cfg    = INSTRUMENTS["XAUUSD"]
    gs     = cfg["grid_size"]
    gl     = GRID_CONFIG["levels"]
    mfl    = GRID_CONFIG["max_float"]

    # Trend arvutus — kasuta df kui saadaval, muidu kasuta price liikumist
    df = get_data(cfg["symbol_td"])
    if df is not None:
        calc_atr_gold(df)
        trend = get_trend(df)
    else:
        trend = "neutral"  # fallback kui yfinance ei tööta

    # Claude AI
    atr_val = _atr_history[-1] if _atr_history else 20.0
    session = "london" if 7 <= now.hour < 13 else "new_york" if 13 <= now.hour < 20 else "asia"
    bias = "neutral"  # Claude AI väljas — puhas tehniline trend
    # KAITSE: trend loeb alles siis kui 3 järjestikust scanni sama — väldib flip-flop müra
    global _trend_history
    _trend_history.append(trend)
    if len(_trend_history) > 3: _trend_history.pop(0)
    if len(_trend_history) == 3 and all(t == _trend_history[0] for t in _trend_history):
        effective_trend = trend
    else:
        effective_trend = "neutral"  # pole kinnitatud — ära tee midagi

    balance    = get_balance()
    grid_state = get_grid_state()
    add_log(f"🔍 Grid state: {grid_state is not None} | trend:{effective_trend} | pending:{len(grid_state.get('pending',{})) if grid_state else 0}")

    if grid_state is None:
        if effective_trend == "neutral": return
        center  = round(price/gs)*gs
        pending = setup_grid(center, effective_trend)
        save_grid_state({"center":center,"trend":effective_trend,"pending":pending})
        add_log(f"🔲 Gold grid initsialiseeritud @ ${center:.0f} | {effective_trend}")
        # Saada XTrend signaalid käsitsi sisestamiseks
        send_grid_signals(center, effective_trend, gs, 30.0, 45.0, get_compound_lot(balance))
        return

    pending    = grid_state.get("pending", {})
    grid_trend = grid_state.get("trend", "neutral")
    grid_center = grid_state.get("center", grid_state.get("grid", {}).get("center", price))

    # Auto-reset kui hind on liiga kaugel grid keskusest (3x grid size)
    if abs(price - grid_center) > gs * 3 and len(ct.get_open_positions("XAUUSD")) == 0:
        new_c = round(price/gs)*gs
        save_grid_state({"center":new_c,"trend":effective_trend if effective_trend != "neutral" else grid_trend,"pending":setup_grid(new_c, effective_trend if effective_trend != "neutral" else grid_trend)})
        add_log(f"🔄 Grid auto-reset: hind ${price:.0f} kaugel keskusest ${grid_center:.0f}")
        send_grid_signals(new_c, effective_trend if effective_trend != "neutral" else grid_trend, gs, 30.0, 45.0, get_compound_lot(balance))
        return

    if effective_trend != grid_trend and effective_trend != "neutral":
        open_pos = get_gold_positions()
        for pos in open_pos:
            entry = float(pos.get("entry",0))
            d     = pos.get("direction","buy")
            fl    = (price-entry)*get_compound_lot(balance)*100 if d=="buy" else (entry-price)*get_compound_lot(balance)*100
            # Sulge PÄRIS MT5 positsioon ENNE Supabase uuendust — KÕIK vastutrendi
            # positsioonid (kaotuses JA kasumis). Backtest (30 juhuslikku hinnateed)
            # näitas seda paremaks kui ainult kaotuses olevate sulgemist: kasumis
            # positsioon jäetuna lahti samasse vastutrendi, mis kaotusi tekitab,
            # ei ole reaalselt kaitstud kasum, vaid ohus paberkasum.
            ticket = pos.get("mt5_ticket")
            close_ok = True
            if ticket:
                close_ok = ct.close_position(int(ticket))
                if not close_ok:
                    add_log(f"⚠️ Trend reset: MT5 positsioon {ticket} sulgemine ebaõnnestus — proovin uuesti järgmisel scannil")
            if close_ok:
                balance = round(balance+fl, 2)
                sb_upsert("signals", {"id":pos["id"],"executed":True})
                sb_upsert("bot_state", {"id":1,"balance":balance})
        new_c = round(price/gs)*gs
        save_grid_state({"center":new_c,"trend":effective_trend,"pending":setup_grid(new_c, effective_trend)})
        add_log(f"🔄 Gold grid reset: {grid_trend}→{effective_trend}")
        send_grid_signals(new_c, effective_trend, gs, 30.0, 45.0, get_compound_lot(balance))
        return

    open_pos = get_gold_positions()
    for pos in open_pos:
        entry = float(pos.get("entry",0))
        tp    = float(pos.get("tp",0))
        d     = pos.get("direction","buy")
        pid   = pos.get("id")
        lot   = get_compound_lot(balance)

        if (high>=tp if d=="buy" else low<=tp):
            pnl     = abs(tp-entry)*lot*100
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
        if fl < -get_scaled_max_float(balance):
            # Sulge PÄRIS MT5 positsioon
            ticket = pos.get("mt5_ticket")
            close_ok = True
            if ticket:
                close_ok = ct.close_position(int(ticket))
                if not close_ok:
                    add_log(f"⚠️ Float stop: MT5 positsioon {ticket} sulgemine ebaõnnestus — proovin uuesti järgmisel scannil")
            if close_ok:
                balance = round(balance+fl, 2)
                sb_upsert("signals", {"id":pid,"executed":True})
                sb_upsert("bot_state", {"id":1,"balance":balance})
                add_log(f"🛡 Gold float stop: {d.upper()} @ {entry:.0f}  {fl:+.2f}€")

    triggered = []
    for level_str, direction in list(pending.items()):
        level = float(level_str)
        if effective_trend == "neutral": continue
        if effective_trend=="bull" and direction=="sell": continue
        if effective_trend=="bear" and direction=="buy":  continue
        hit = (direction=="buy" and low<=level) or (direction=="sell" and high>=level)
        if not hit: continue
        same = [p for p in get_gold_positions() if p.get("direction")==direction]
        if len(same) >= gl: continue
        lot = get_compound_lot(balance)
        # TP/SL arvutatakse PÄRIS hetkehinna (price) pealt, mitte vana
        # pending-taseme (level) pealt — order on market order, mis täitub
        # kohese turuhinnaga, mis võib vanast level'ist kaugel olla, kui
        # pending tase jäi Supabase'i seisma (nt bot restart vahepeal).
        tp = round(price + 30.0 if direction=="buy" else price - 30.0, 2)
        sl = round(price - 45.0 if direction=="buy" else price + 45.0, 2)
        # KAITSE 1: max 3 lahtist positsiooni (variant C — backtest +422€/kuu)
        open_now = ct.get_open_positions("XAUUSD")
        if len(open_now) >= 3:
            continue
        # KAITSE 6: ei ava hedge (BUY+SELL korraga)
        if open_now:
            existing_dir = open_now[0].get("direction", "")
            if existing_dir and existing_dir != direction:
                continue
        # KAITSE 2: cooldown 8 min viimasest orderist
        global _last_order_time
        if time.time() - _last_order_time < 480:
            continue
        # Saada KÕIGEPEALT päris order MT5-sse, kontrolli tulemust
        order_result = ct.place_order(direction, "XAUUSD", lot, tp=tp, sl=sl)
        if "error" not in order_result:
            _last_order_time = time.time()
        if "error" in order_result:
            add_log(f"❌ Gold order ebaõnnestus: {order_result['error']}")
            continue
        # Alles pärast edukat orderit salvesta Supabase-sse.
        # entry = PÄRIS täitmishind (price), mitte vana pending-tase (level) —
        # muidu on kõik hilisemad P&L arvutused (TP-kontroll, float-stop,
        # trendi-pöördumine) selle positsiooni peal valed, kuna order täitub
        # market order'ina hetkehinnaga, mitte vana level'iga.
        sb_insert("signals", {
            "direction":direction,"entry":price,"tp":tp,
            "sl":sl,
            "lot":lot,"regime":"grid","session":f"gold_{effective_trend}",
            "executed":False,"breakeven":False,"atr":gs,"score":0,"rr":3.0,
            "mt5_ticket": order_result.get("orderId"),
        })
        triggered.append(level_str)
        add_log(f"📊 Gold order: {direction.upper()} @ {price:.0f}  TP:{tp:.0f} (ticket:{order_result.get('orderId')})")
        send_telegram(f"📊 <b>Gold Grid Order</b>\n{direction.upper()} @ <b>{price:.0f}</b>\nTP: <b>{tp:.0f}</b> | {effective_trend}")

    for ls in triggered:
        if ls in pending: del pending[ls]
    if triggered:
        grid_state["pending"] = pending
        save_grid_state(grid_state)

    # ── SCALPING LAYER ───────────────────────────────────
    # 5min küünlatel põhinev lisasignaal trendi suunas
    try:
        df5 = get_scalp_data()
        if df5 is not None and len(df5) >= 5:
            last5 = df5.iloc[-1]
            h5 = float(last5["high"]); l5 = float(last5["low"])
            range5 = h5 - l5

            # Scalp ainult kui liikumine on piisavalt suur (>$10)
            if range5 > 10:
                scalp_positions = [p for p in get_gold_positions() if p.get("session","").startswith("scalp")]
                if len(scalp_positions) < 2:  # max 2 scalp positsiooni
                    lot_scalp = round(round(max(0.01, (balance/ACCOUNT_BALANCE)*0.01) / 0.01) * 0.01, 2)

                    if effective_trend == "bull" and l5 < price - 5:
                        # TP/SL arvutatakse PÄRIS hetkehinna (price) pealt, mitte vana
                        # l5 (5min madalpunkt) pealt — order on market order, mis täitub
                        # kohese turuhinnaga, mistõttu vana l5-põhine TP oli tihti juba
                        # peaaegu käes enne kui order üldse täitus (nt +0,90€ 18 sek pärast).
                        tp_scalp = round(price + 10, 2)
                        sl_scalp = round(price - 15, 2)
                        scalp_result = ct.place_order("buy", "XAUUSD", lot_scalp, tp=tp_scalp, sl=sl_scalp)
                        if "error" not in scalp_result:
                            sb_insert("signals", {
                                "direction":"buy","entry":round(price,2),"tp":tp_scalp,
                                "sl":sl_scalp,"lot":lot_scalp,"regime":"grid",
                                "session":"scalp_bull","executed":False,"breakeven":False,
                                "atr":range5,"score":1,"rr":0.67,
                                "mt5_ticket": scalp_result.get("orderId"),
                            })
                            add_log(f"⚡ Scalp BUY @ {price:.0f} TP:{tp_scalp:.0f}")
                        else:
                            add_log(f"❌ Scalp BUY ebaõnnestus: {scalp_result['error']}")

                    elif effective_trend == "bear" and h5 > price + 5:
                        # Sama parandus mis BUY harus — price, mitte vana h5
                        tp_scalp = round(price - 10, 2)
                        sl_scalp = round(price + 15, 2)
                        scalp_result = ct.place_order("sell", "XAUUSD", lot_scalp, tp=tp_scalp, sl=sl_scalp)
                        if "error" not in scalp_result:
                            sb_insert("signals", {
                                "direction":"sell","entry":round(price,2),"tp":tp_scalp,
                                "sl":sl_scalp,"lot":lot_scalp,"regime":"grid",
                                "session":"scalp_bear","executed":False,"breakeven":False,
                                "atr":range5,"score":1,"rr":0.67,
                                "mt5_ticket": scalp_result.get("orderId"),
                            })
                            add_log(f"⚡ Scalp SELL @ {price:.0f} TP:{tp_scalp:.0f}")
                        else:
                            add_log(f"❌ Scalp SELL ebaõnnestus: {scalp_result['error']}")
    except Exception as e:
        logger.error(f"Scalp error: {e}")

# ─────────────────────────────────────────────────────────
#  STATISTIKA
# ─────────────────────────────────────────────────────────

def get_stats():
    """Konto statistika — wins, kaotused, net P&L."""
    try:
        trades = sb_select("signals", "executed=eq.true&order=created_at.desc&limit=100")
        if not trades: return {"total": 0, "wins": 0, "net_pnl": 0.0, "win_rate": 0}
        wins = [t for t in trades if float(t.get("tp") or 0) > 0]
        return {
            "total":    len(trades),
            "wins":     len(wins),
            "net_pnl":  round(get_balance() - ACCOUNT_BALANCE, 2),
            "win_rate": round(len(wins)/len(trades)*100, 1) if trades else 0,
        }
    except Exception as e:
        logger.error(f"get_stats: {e}")
        return {"total": 0, "wins": 0, "net_pnl": 0.0, "win_rate": 0}

def sb_delete(table, params):
    """Kustutab ridu Supabase tabelist."""
    try:
        r = requests.delete(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=sb_headers(), timeout=10)
        return r.status_code in (200, 204)
    except Exception as e:
        logger.error(f"SB delete: {e}")
        return False

# ─────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────

def main():
    add_log("🚀 NEMSIS v4 — Multi-Strategy Bot")
    add_log(f"📊 Instrumendid: {', '.join(k for k,v in INSTRUMENTS.items() if v['enabled'])}")
    add_log(f"🤖 Claude AI: {'ON' if ANTHROPIC_KEY else 'OFF'}")

    balance = get_balance()
    add_log(f"💼 Balance: {balance:.2f}€")

    # MT5 käivitamine
    ct.start()
    if ct.is_connected():
        add_log("🔗 MT5: ÜHENDATUD")
    else:
        add_log("⚠️ MT5: ühendus ebaõnnestus — kontrolli VPS-i")

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

            # ── CIRCUIT BREAKER KONTROLL ──
            balance = get_balance()
            if not check_circuit_breaker(balance, now):
                time.sleep(SCAN_INTERVAL)
                continue

            # ── MT5 POSITSIOONIDE SÜNKRONISEERIMINE ──
            sync_mt5_positions()

            # ── GOLD GRID ──
            price_gold = 0
            if INSTRUMENTS["XAUUSD"]["enabled"]:
                try:
                    price_gold = get_price("XAU/USD")
                    # Kui hind veel ei tulnud, oota ja proovi uuesti (max 10 sek)
                    retry = 0
                    while price_gold == 0 and retry < 10:
                        time.sleep(1)
                        price_gold = get_price("XAU/USD")
                        retry += 1
                    if price_gold > 0:
                        # Gold grid ei vaja BB/RSI — ainult hind ja trend
                        # high/low: kasuta ±0.5% hinnast kui df puudub
                        df_gold = get_data("XAU/USD")
                        if df_gold is not None and len(df_gold) > 2:
                            # Kasuta viimase 2 küünla high/low — katab ~2h liikumise
                            # nii ei jää grid tabamised vahele 15min scannil
                            high_gold = float(df_gold["high"].iloc[-2:].max())
                            low_gold  = float(df_gold["low"].iloc[-2:].min())
                        else:
                            # Fallback: kasuta ±0.5% hinnast
                            high_gold = round(price_gold * 1.005, 2)
                            low_gold  = round(price_gold * 0.995, 2)
                        add_log(f"🥇 Gold: ${price_gold:.2f}")
                        run_gold_grid(price_gold, high_gold, low_gold, now)
                    else:
                        add_log("⚠️ Gold: hind puudub cTrader-ist")
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
                "log": log_buffer[-30:],
                "stats": {
                    "balance":         balance,
                    "gold_positions":  len(gold_pos),
                    "forex_positions": len(forex_pos),
                    "scan":            scan_count,
                    "claude_bias":     _claude_cache.get("bias", "neutral"),
                    "claude_reason":   _claude_cache.get("reason", ""),
                    "price":           round(price_gold if price_gold > 0 else 0, 2),
                    "instruments":     list(INSTRUMENTS.keys()),
                }
            })

            # Päevane kokkuvõte 8:00 UTC
            if now.hour == 8 and now.minute == 0:
                stats = get_stats()
                trend = _claude_cache.get("bias", "neutral")
                send_telegram(
                    f"🌅 <b>NEMSIS v4 Päevane kokkuvõte</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"💼 Balance: <b>{balance:.2f}€</b>\n"
                    f"📈 Net P&L: <b>{stats['net_pnl']:+.2f}€</b>\n"
                    f"🎯 Win rate: <b>{stats['win_rate']}%</b> ({stats['wins']}/{stats['total']})\n"
                    f"🥇 Gold pos: <b>{len(gold_pos)}</b>\n"
                    f"💱 Forex pos: <b>{len(forex_pos)}</b>\n"
                    f"🤖 Claude: <b>{trend.upper()}</b>\n"
                    f"💰 Gold: <b>${price_gold:.2f}</b>\n"
                    f"⏰ {now.strftime('%d.%m.%Y')} UTC"
                )

        except Exception as e:
            add_log(f"❌ Main error: {e}")
            logger.exception(e)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        send_telegram("⏹ <b>NEMSIS peatatud</b>\nKasutaja peatas boti käsitsi.")
    except Exception as e:
        send_telegram(f"🚨 <b>NEMSIS CRASH</b>\nViga: {str(e)[:200]}\nBot on maas — palun taaskäivita!")
        raise
