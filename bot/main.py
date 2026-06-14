"""
NEMSIS v2 — News-Based Trading Bot
Kaupleb Forex Factory uudiste põhjal:
1. Enne uudist — ei kauple (30 min enne)
2. Uudis tuleb — vaatab actual vs forecast
3. Kui erinevus piisavalt suur → kaupleb suunas
4. Muul ajal — tavapärane trend + RSI loogika
"""

import sys, os, json, time, logging, requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── env vars
SUPABASE_URL     = os.environ.get("SUPABASE_URL", "https://xqinzjaqorjqaexeoyqc.supabase.co")
SUPABASE_KEY     = os.environ.get("SUPABASE_KEY", "sb_secret_geYNl5euHLVWXQtone_N0g_K5nB0Zel")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "7502951774:AAFEdMlowZumpFlLm817UEP4ws40SeZtROo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7638697143")
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "60"))  # 1 min — uudiste jaoks kiirem
ACCOUNT_BALANCE  = float(os.environ.get("ACCOUNT_BALANCE", "100"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NEMSIS")
log_buffer = []

def add_log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    log_buffer.append(f"{ts}  {msg}")
    if len(log_buffer) > 60: log_buffer.pop(0)
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
            logger.warning(f"Supabase {table}: {r.status_code} {r.text[:80]}")
    except Exception as e:
        logger.error(f"Supabase error: {e}")

def sb_insert(table, data):
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), json=data, timeout=10)
        if r.status_code not in (200,201):
            logger.warning(f"Supabase insert {table}: {r.status_code}")
    except Exception as e:
        logger.error(f"Supabase insert error: {e}")

def sb_select(table, params=""):
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=sb_headers(), timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        logger.error(f"Supabase select error: {e}")
        return []

def get_balance():
    try:
        rows = sb_select("bot_state", "id=eq.1&select=balance")
        if rows and rows[0].get("balance"):
            return float(rows[0]["balance"])
    except: pass
    return ACCOUNT_BALANCE


# ─────────────────────────────────────────────────────────
#  FOREX FACTORY KALENDER
# ─────────────────────────────────────────────────────────

# Gold jaoks olulised uudised
GOLD_HIGH_IMPACT = [
    "non-farm", "nfp", "payroll",
    "cpi", "inflation", "core cpi",
    "fed", "fomc", "rate decision", "federal reserve", "powell",
    "gdp", "unemployment", "jobless",
    "pce", "ppi", "retail sales",
    "ism", "pmI"
]

_ff_cache = {"data": [], "updated": 0}

def fetch_ff_calendar():
    """Laeb Forex Factory nädala kalendri."""
    global _ff_cache
    now = time.time()
    # Cache 30 minutit
    if now - _ff_cache["updated"] < 1800 and _ff_cache["data"]:
        return _ff_cache["data"]
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        r = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        if r.status_code == 200:
            data = r.json()
            _ff_cache = {"data": data, "updated": now}
            add_log(f"📅 FF kalender uuendatud: {len(data)} sündmust")
            return data
    except Exception as e:
        logger.error(f"FF kalender error: {e}")
    return _ff_cache["data"]

def is_gold_relevant(event_title):
    """Kas uudis mõjutab kulda?"""
    title = event_title.lower()
    return any(kw in title for kw in GOLD_HIGH_IMPACT)

def get_upcoming_news(minutes_ahead=35):
    """Leiab lähima X minuti jooksul tulevad high-impact uudised."""
    calendar = fetch_ff_calendar()
    now = datetime.now(timezone.utc)
    upcoming = []
    for event in calendar:
        try:
            if event.get("impact", "").lower() != "high":
                continue
            if event.get("country", "").upper() != "USD":
                continue
            dt_str = event.get("date", "")
            if not dt_str: continue
            # FF kasutab ISO formaati
            evt_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            diff = (evt_dt - now).total_seconds() / 60
            if 0 <= diff <= minutes_ahead:
                upcoming.append({
                    "title":    event.get("title", ""),
                    "time":     evt_dt,
                    "minutes":  round(diff, 1),
                    "forecast": event.get("forecast", ""),
                    "previous": event.get("previous", ""),
                    "actual":   event.get("actual", ""),
                })
        except Exception as e:
            continue
    return upcoming

def get_recent_news_signal(minutes_back=10):
    """
    Vaatab viimase X minuti uudiseid.
    Kui actual vs forecast erinevus on piisavalt suur → annab signaali.
    Tagastab: ("buy"/"sell"/None, uudise nimi, kirjeldus)
    """
    calendar = fetch_ff_calendar()
    now = datetime.now(timezone.utc)
    for event in calendar:
        try:
            if event.get("impact", "").lower() != "high": continue
            if event.get("country", "").upper() != "USD": continue
            actual   = event.get("actual", "")
            forecast = event.get("forecast", "")
            if not actual or not forecast: continue

            dt_str = event.get("date", "")
            if not dt_str: continue
            evt_dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            diff_min = (now - evt_dt).total_seconds() / 60
            if diff_min < 0 or diff_min > minutes_back: continue

            title = event.get("title", "")
            if not is_gold_relevant(title): continue

            # Parse numbrid
            def parse_num(s):
                if not s: return None
                s = str(s).replace("%","").replace("K","000").replace("M","000000").strip()
                try: return float(s)
                except: return None

            act = parse_num(actual)
            fct = parse_num(forecast)
            if act is None or fct is None: continue

            diff_pct = abs(act - fct) / (abs(fct) + 0.001) * 100

            # Minimaalne erinevus mis on oluline (5%)
            if diff_pct < 5: continue

            # Gold reageerib:
            # CPI kõrgem kui oodatud → inflatsioon → gold TÕUSEB → BUY
            # NFP kõrgem kui oodatud → majandus tugev → dollar tugevneb → gold LANGEB → SELL
            # Fed rate hike → dollar tugevneb → gold LANGEB → SELL

            title_lower = title.lower()
            is_inflation = any(k in title_lower for k in ["cpi","inflation","pce","ppi"])
            is_labor     = any(k in title_lower for k in ["nfp","non-farm","payroll","employment","jobless"])
            is_fed       = any(k in title_lower for k in ["fed","fomc","rate","powell"])

            direction = None
            desc = f"{title}: actual={actual} vs forecast={forecast} ({diff_pct:.1f}% erinevus)"

            if is_inflation:
                # Kõrgem inflatsioon → gold üles
                direction = "buy" if act > fct else "sell"
            elif is_labor:
                # Tugevam tööjõuturg → dollar üles → gold alla
                direction = "sell" if act > fct else "buy"
            elif is_fed:
                # Rate hike → dollar üles → gold alla
                direction = "sell" if act > fct else "buy"
            else:
                # Üldreegel: üllatavalt hea USA majandus → dollar üles → gold alla
                direction = "sell" if act > fct else "buy"

            return direction, title, desc
        except Exception as e:
            continue
    return None, None, None


# ─────────────────────────────────────────────────────────
#  TEHNILINE ANALÜÜS (backup kui uudised pole)
# ─────────────────────────────────────────────────────────

def calc_rsi(s, p=14):
    d = s.diff()
    g = d.clip(lower=0).ewm(alpha=1/p, adjust=False).mean()
    l = (-d).clip(lower=0).ewm(alpha=1/p, adjust=False).mean()
    return 100 - 100/(1+g/(l+1e-10))

def calc_atr(df, p=14):
    hl = df.high - df.low
    hc = (df.high - df.close.shift()).abs()
    lc = (df.low  - df.close.shift()).abs()
    return pd.concat([hl,hc,lc],axis=1).max(axis=1).ewm(alpha=1/p,adjust=False).mean()

def get_trend(df_4h, df_wk):
    """Lihtne trend: hind vs 50 küünalt tagasi."""
    if df_4h is None or len(df_4h) < 55: return "neutral"
    now = float(df_4h["close"].iloc[-1])
    ago = float(df_4h["close"].iloc[-51])
    chg = (now - ago) / ago * 100
    t4h = "bull" if chg > 2 else "bear" if chg < -2 else "neutral"

    t_wk = "neutral"
    if df_wk is not None and len(df_wk) >= 13:
        now_w = float(df_wk["close"].iloc[-1])
        ago_w = float(df_wk["close"].iloc[-13])
        chg_w = (now_w - ago_w) / ago_w * 100
        t_wk = "bull" if chg_w > 3 else "bear" if chg_w < -3 else "neutral"

    if t4h == "bull" and t_wk in ("bull","neutral"): return "bull"
    if t4h == "bear" and t_wk in ("bear","neutral"): return "bear"
    if t_wk != "neutral": return t_wk
    return "neutral"

def get_technical_signal(tf_data):
    """
    Tehniline signaal ainult kui:
    1. Selge trend (4h + weekly nõustuvad)
    2. RSI pullback trendis (RSI<45 bull, RSI>55 bear)
    """
    df_1h = tf_data.get("1h")
    df_4h = tf_data.get("4h")
    df_wk = tf_data.get("1wk")

    if df_1h is None or len(df_1h) < 50: return None, None

    df_1h = df_1h.copy()
    df_1h["rsi"] = calc_rsi(df_1h["close"])
    df_1h["atr"] = calc_atr(df_1h)

    trend = get_trend(df_4h, df_wk)
    if trend == "neutral": return None, None

    rsi = float(df_1h["rsi"].iloc[-1])
    atr = float(df_1h["atr"].iloc[-1])

    if trend == "bull" and rsi < 45:
        return "buy", f"Trend bull + RSI pullback {rsi:.1f}"
    elif trend == "bear" and rsi > 55:
        return "sell", f"Trend bear + RSI tõus {rsi:.1f}"

    return None, None


# ─────────────────────────────────────────────────────────
#  ANDMED
# ─────────────────────────────────────────────────────────

_tf_cache = {"data": {}, "updated": 0}

def load_data():
    global _tf_cache
    now = time.time()
    if now - _tf_cache["updated"] < 300:  # 5 min cache
        return _tf_cache["data"]
    try:
        import yfinance as yf
        result = {}
        for tf, iv, per in [("1h","1h","30d"),("4h","4h","60d"),("1wk","1wk","1y")]:
            df = yf.Ticker("GC=F").history(interval=iv, period=per, auto_adjust=True)
            if df is not None and not df.empty:
                df.columns = [c.lower() for c in df.columns]
                if "volume" not in df.columns: df["volume"] = 0
                df = df[["open","high","low","close","volume"]].dropna()
                result[tf] = df
        _tf_cache = {"data": result, "updated": now}
        return result
    except Exception as e:
        logger.error(f"Data error: {e}")
        return _tf_cache["data"]

def get_price():
    try:
        import yfinance as yf
        df = yf.Ticker("GC=F").history(interval="1m", period="1d", auto_adjust=True)
        if df is not None and not df.empty:
            return float(df["Close"].iloc[-1])
    except: pass
    return 0.0


# ─────────────────────────────────────────────────────────
#  RISK
# ─────────────────────────────────────────────────────────

MAX_OPEN   = 1
RISK_PCT   = 0.01
ATR_SL     = 1.5
ATR_TP     = 4.5
EXPIRY_H   = 8
SPREAD     = 0.35

def get_risk_state():
    try:
        rows = sb_select("bot_state", "id=eq.1&select=risk_state")
        if rows and rows[0].get("risk_state"):
            return rows[0]["risk_state"]
    except: pass
    return {"daily_loss": 0.0, "daily_reset": "", "loss_streak": 0, "paused_until": None}

def save_risk(state):
    sb_upsert("bot_state", {"id": 1, "risk_state": state})

def can_trade():
    open_sigs = sb_select("signals", "executed=eq.false&select=id")
    if len(open_sigs) >= MAX_OPEN:
        return False, f"Max {MAX_OPEN} avatud signaal"
    risk = get_risk_state()
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if risk.get("daily_reset") != today:
        risk["daily_loss"] = 0.0; risk["daily_reset"] = today
        save_risk(risk)
    paused = risk.get("paused_until")
    if paused and datetime.now(timezone.utc) < datetime.fromisoformat(paused):
        return False, "Loss streak paus"
    daily_loss_pct = abs(float(risk.get("daily_loss",0))) / ACCOUNT_BALANCE * 100
    if daily_loss_pct >= 3.0:
        return False, f"Daily loss {daily_loss_pct:.1f}%"
    return True, ""

def calc_lot(balance, sl_dist):
    lot = (balance * RISK_PCT) / (sl_dist * 100)
    return round(max(0.01, min(0.5, lot)), 2)

def check_open_signals():
    """Kontrollib kas avatud signaalid on saavutanud TP/SL."""
    try:
        sigs = sb_select("signals", "executed=eq.false&order=created_at.desc&limit=5")
        for sig in sigs:
            created = datetime.fromisoformat(sig["created_at"].replace("Z","+00:00"))
            age_h   = (datetime.now(timezone.utc) - created).total_seconds() / 3600
            entry   = float(sig.get("entry",0))
            tp      = float(sig.get("tp",0))
            sl      = float(sig.get("sl",0))
            atr     = float(sig.get("atr",5))
            direction = sig.get("direction","buy")
            sig_id  = sig.get("id")
            be      = sig.get("breakeven", False)
            eff_sl  = entry if be else sl

            if age_h >= EXPIRY_H:
                sb_upsert("signals", {"id": sig_id, "executed": True})
                add_log(f"⏰ Aegunud: {direction.upper()} @ {entry}")
                send_telegram(f"⏰ Signaal aegunud: {direction.upper()} @ {entry}")
                continue

            price = get_price()
            if price == 0: continue

            # Breakeven
            if not be:
                if direction=="buy"  and price >= entry + atr:
                    sb_upsert("signals", {"id": sig_id, "breakeven": True, "sl": entry})
                    add_log(f"🔒 Breakeven: BUY @ {entry}")
                    send_telegram(f"🔒 Breakeven aktiveeritud — BUY @ {entry}")
                    eff_sl = entry; be = True
                elif direction=="sell" and price <= entry - atr:
                    sb_upsert("signals", {"id": sig_id, "breakeven": True, "sl": entry})
                    add_log(f"🔒 Breakeven: SELL @ {entry}")
                    send_telegram(f"🔒 Breakeven aktiveeritud — SELL @ {entry}")
                    eff_sl = entry; be = True

            # TP/SL kontroll
            hit = None
            if direction=="buy":
                if price >= tp: hit = "TP"
                elif price <= eff_sl: hit = "SL"
            else:
                if price <= tp: hit = "TP"
                elif price >= eff_sl: hit = "SL"

            if hit:
                balance  = get_balance()
                lot      = float(sig.get("lot", 0.01))
                pnl_pts  = abs(tp-entry) if hit=="TP" else -abs(eff_sl-entry)
                pnl_eur  = round(pnl_pts * lot * 100, 2)
                new_bal  = round(balance + pnl_eur, 2)
                sb_upsert("signals", {"id": sig_id, "executed": True})
                sb_upsert("bot_state", {"id": 1, "balance": new_bal})
                risk = get_risk_state()
                if pnl_eur < 0:
                    risk["daily_loss"] = float(risk.get("daily_loss",0)) + abs(pnl_eur)
                    risk["loss_streak"] = int(risk.get("loss_streak",0)) + 1
                    if risk["loss_streak"] >= 3:
                        risk["paused_until"] = (datetime.now(timezone.utc)+timedelta(hours=24)).isoformat()
                        add_log("⛔ 3 kaotust järjest — 24h paus")
                else:
                    risk["loss_streak"] = 0
                save_risk(risk)
                add_log(f"{'✅' if hit=='TP' else '❌'} {hit} @ {price:.2f}  PnL: {pnl_eur:+.2f}€  Bal: {new_bal:.2f}€")
                send_telegram(
                    f"{'✅' if hit=='TP' else '❌'} <b>{hit}</b>\n"
                    f"{direction.upper()} @ {entry} → {hit} @ {price:.2f}\n"
                    f"PnL: <b>{pnl_eur:+.2f}€</b>  |  Balance: <b>{new_bal:.2f}€</b>"
                )
    except Exception as e:
        logger.error(f"check_open_signals error: {e}")


# ─────────────────────────────────────────────────────────
#  TELEGRAM
# ─────────────────────────────────────────────────────────

def send_telegram(text):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID: return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data={"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode":"HTML"},
            timeout=10
        )
    except Exception as e:
        logger.warning(f"Telegram error: {e}")


# ─────────────────────────────────────────────────────────
#  SIGNAAL GENEREERIMINE
# ─────────────────────────────────────────────────────────

_last_news_signal_time = None
_last_tech_signal_time = None

def generate_and_send_signal(direction, reason, signal_type, tf_data):
    """Genereerib signaali ja saadab Telegrami."""
    global _last_news_signal_time, _last_tech_signal_time

    df_1h = tf_data.get("1h")
    if df_1h is None or len(df_1h) < 20: return

    df_1h = df_1h.copy()
    df_1h["atr"] = calc_atr(df_1h)
    atr   = float(df_1h["atr"].iloc[-1])
    price = get_price()
    if price == 0: price = float(df_1h["close"].iloc[-1])

    balance = get_balance()
    sl = round(price - atr*ATR_SL - SPREAD if direction=="buy"
               else price + atr*ATR_SL + SPREAD, 2)
    tp = round(price + atr*ATR_TP if direction=="buy"
               else price - atr*ATR_TP, 2)
    sl_dist = abs(price - sl)
    if sl_dist == 0: return

    lot = calc_lot(balance, sl_dist)
    rr  = round(ATR_TP/ATR_SL, 1)

    icon = "📰" if signal_type == "news" else "📊"
    add_log(f"🔔 {signal_type.upper()} SIGNAAL: {direction.upper()} @ {price:.2f}  R:R 1:{rr}")

    sb_insert("signals", {
        "direction":  direction,
        "entry":      round(price,2),
        "sl":         sl,
        "tp":         tp,
        "rr":         rr,
        "atr":        round(atr,2),
        "lot":        lot,
        "score":      0,
        "regime":     signal_type,
        "session":    reason[:50],
        "executed":   False,
        "breakeven":  False,
    })

    send_telegram(
        f"{icon} <b>NEMSIS — XAUUSD {'📈 BUY' if direction=='buy' else '📉 SELL'}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Entry: <b>{price:.2f}</b>\n"
        f"🛑 SL: <b>{sl}</b>\n"
        f"🎯 TP: <b>{tp}</b>\n"
        f"⚖️ R:R: <b>1:{rr}</b>  |  Lot: <b>{lot}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{'📰 Uudis' if signal_type=='news' else '📊 Tehniline'}: {reason}\n"
        f"💼 Balance: <b>{balance:.2f}€</b>"
    )

    if signal_type == "news":
        _last_news_signal_time = datetime.now(timezone.utc)
    else:
        _last_tech_signal_time = datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────
#  PEAMINE LOOP
# ─────────────────────────────────────────────────────────

def main():
    global _last_news_signal_time, _last_tech_signal_time

    add_log("🚀 NEMSIS v2 — News + Technical Bot started")
    add_log(f"📰 Forex Factory kalender: AKTIIVNE")
    add_log(f"📊 Tehniline backup: Trend + RSI")
    add_log(f"⚖️ R:R: 1:{ATR_TP/ATR_SL:.0f}  SL: {ATR_SL}x ATR  TP: {ATR_TP}x ATR")

    balance = get_balance()
    add_log(f"💼 Balance: {balance:.2f}€")

    send_telegram(
        f"🚀 <b>NEMSIS v2</b> started\n"
        f"📰 News-based trading: <b>AKTIIVNE</b>\n"
        f"💼 Balance: <b>{balance:.2f}€</b>\n"
        f"⚖️ R:R: <b>1:{ATR_TP/ATR_SL:.0f}</b>"
    )

    rows = sb_select("bot_state", "id=eq.1&select=balance")
    if not rows or not rows[0].get("balance"):
        sb_upsert("bot_state", {"id": 1, "balance": balance})

    while True:
        try:
            now = datetime.now(timezone.utc)
            add_log("⏱ Scanning...")

            # Kontrolli avatud signaale
            check_open_signals()

            # Kas saab kaupleda?
            ok, reason = can_trade()
            if not ok:
                add_log(f"🛡 {reason}")
                time.sleep(SCAN_INTERVAL)
                continue

            # ── UUDISTE REŽIIM ──────────────────────────

            # 1. Kas tulemas on high-impact uudis?
            upcoming = get_upcoming_news(minutes_ahead=35)
            if upcoming:
                next_news = upcoming[0]
                mins = next_news["minutes"]
                add_log(f"📅 Uudis tulemas {mins:.0f} min pärast: {next_news['title']}")

                if mins <= 30:
                    # Ära kauple 30 min enne uudist
                    add_log(f"⏸ Ootan uudist ({next_news['title']}) — {mins:.0f} min")
                    time.sleep(SCAN_INTERVAL)
                    continue

            # 2. Kas just tuli high-impact uudis? (viimased 10 min)
            news_dir, news_title, news_desc = get_recent_news_signal(minutes_back=10)

            if news_dir:
                # Cooldown — max 1 uudissignaal per 30 min
                if _last_news_signal_time:
                    cooldown = (now - _last_news_signal_time).total_seconds() / 60
                    if cooldown < 30:
                        add_log(f"⏸ News cooldown {cooldown:.0f}/30 min")
                        time.sleep(SCAN_INTERVAL)
                        continue

                add_log(f"📰 UUDIS: {news_desc}")
                tf_data = load_data()
                generate_and_send_signal(news_dir, news_desc, "news", tf_data)
                time.sleep(SCAN_INTERVAL)
                continue

            # ── TEHNILINE REŽIIM (kui uudiseid pole) ───

            # Sessioon filter
            h = now.hour; wd = now.weekday()
            in_session = wd < 5 and ((7 <= h < 12) or (13 <= h < 17))
            if not in_session:
                add_log(f"— Off session ({h}:00 UTC)")
                time.sleep(SCAN_INTERVAL)
                continue

            # Tehniline signaal
            tf_data = load_data()
            tech_dir, tech_reason = get_technical_signal(tf_data)

            if tech_dir:
                # Cooldown — max 1 tehniline signaal per 4 tundi
                if _last_tech_signal_time:
                    cooldown = (now - _last_tech_signal_time).total_seconds() / 3600
                    if cooldown < 4:
                        add_log(f"— Tech cooldown {cooldown:.1f}/4h")
                        time.sleep(SCAN_INTERVAL)
                        continue

                add_log(f"📊 Tehniline: {tech_reason}")
                generate_and_send_signal(tech_dir, tech_reason, "technical", tf_data)
            else:
                add_log("— No signal this cycle")

            # Uuenda dashboard
            price = get_price()
            balance = get_balance()
            risk = get_risk_state()
            sb_upsert("bot_state", {
                "id": 1,
                "updated_at": now.isoformat(),
                "price": round(price,2),
                "last_scan": now.strftime("%H:%M:%S UTC"),
                "log": log_buffer[-20:],
                "risk": {
                    "balance": balance,
                    "daily_loss_pct": round(abs(float(risk.get("daily_loss",0)))/ACCOUNT_BALANCE*100,1),
                    "loss_streak": risk.get("loss_streak",0),
                    "paused": risk.get("paused_until") is not None,
                }
            })

        except Exception as e:
            add_log(f"❌ Error: {e}")
            logger.exception(e)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
