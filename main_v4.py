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
import gold_logic
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

def sb_insert(table, data, retry=True):
    """
    Tagastab True/False, kas kirje reaalselt Supabase'i jõudis.
    UUS (1 Sept 2026): varem oli see fire-and-forget - kui insert
    ebaõnnestus (nt puuduva veeru tõttu, nagu 1 Sept juhtus reaalkontol
    525854, kaks tehingut 92726307/92771116 jäid Supabase'ist puudu ja
    bot ei suutnud neid seejärel automaatselt hallata), ei saanud
    väljakutsuja sellest kunagi teada. Nüüd proovitakse üks kord uuesti
    (lühikese viivitusega, transientse võrguvea puhuks) ja tagastatakse
    selge õnnestumise/ebaõnnestumise staatus, et väljakutsuja saaks
    kasutajat hoiatada, kui PÄRIS MT5 positsioon jääb jälgimiseta.
    """
    try:
        r = requests.post(f"{SUPABASE_URL}/rest/v1/{table}", headers=sb_headers(), json=data, timeout=10)
        if r.status_code in (200,201):
            return True
        logger.warning(f"SB insert {table}: {r.status_code} — {r.text[:500]}")
    except Exception as e:
        logger.error(f"SB insert: {e}")

    if retry:
        time.sleep(2)
        return sb_insert(table, data, retry=False)
    return False

def sb_select(table, params=""):
    try:
        r = requests.get(f"{SUPABASE_URL}/rest/v1/{table}?{params}", headers=sb_headers(), timeout=10)
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        logger.error(f"SB select: {e}")
        return []

def log_trade_close(pos, pnl, close_price=None, reason="", close_time=None):
    """
    Kirjuta suletud tehingu tulemus trades-tabelisse.

    UUS (11 sept 2026): varem ei kirjutatud trades-tabelisse KUNAGI midagi —
    kõik kuus positsiooni sulgemise haru (gold TP, gold float-stop, gold
    trend-reset, gold weekend-close, ülekiht TP/SL, portfelli jala TP/SL)
    ainult märkisid signals-rea executed=True, aga tulemust (pnl, close_price)
    ei salvestanud kuhugi. Ajalugu oli seetõttu ainult signals-tabelis, kus
    pole pnl-välja — rahajälge ei saanud tagantjärele kokku panna.
    """
    ok = sb_insert("trades", {
        "ticket":      str(pos.get("mt5_ticket") or pos.get("id")),
        "direction":   pos.get("direction"),
        "entry":       pos.get("entry"),
        "sl":          pos.get("sl"),
        "tp":          pos.get("tp"),
        "lot_size":    pos.get("lot"),
        "open_time":   pos.get("created_at"),
        "close_price": round(float(close_price), 5) if close_price is not None else None,
        "close_time":  close_time or datetime.now(timezone.utc).isoformat(),
        "pnl":         round(float(pnl), 2),
        "result":      "win" if pnl > 0 else "loss",
        "regime":      pos.get("regime"),
        "session":     pos.get("session"),
    })
    if not ok:
        logger.error(f"🚨 trades insert ebaõnnestus (pos {pos.get('id')}, {reason}): pnl={pnl}")
    return ok

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

_last_telegram_update_id = 0


def _bot_dir():
    return os.path.dirname(os.path.abspath(__file__))


def do_restart(reason="käsk"):
    """
    Taaskäivita bot: asenda praegune protsess uuega, mis loeb kettalt
    värske koodi. Töötab nii Windowsil kui Linuxil.

    Lahtised positsioonid EI muutu — need on brokeri juures koos oma TP/SL-iga
    ja bot loeb need käivitumisel Supabase'ist + MT5-st uuesti sisse.
    """
    add_log(f"🔄 Taaskäivitus: {reason}")
    send_telegram(f"🔄 <b>Bot taaskäivitub</b>\nPõhjus: {reason}\nAnnan käivitumisest teada.")
    try:
        for h in logging.getLogger().handlers:
            h.flush()
    except Exception:
        pass
    time.sleep(1)  # anna Telegrami sõnumil väljuda
    os.execv(sys.executable, [sys.executable] + sys.argv)


def do_update():
    """
    Kaugdeploy: git pull + taaskäivitus.

    KRIITILINE KAITSE: pärast pull'i kontrollitakse, kas uus kood üldse
    kompileerub. Kui ei, siis EI taaskäivitata — muidu jääks bot maha ja
    seda ei saaks enam telefonist üles. Sellisel juhul jookseb vana kood
    (mälus) edasi ja Telegrami tuleb veateade.
    """
    import subprocess
    d = _bot_dir()
    send_telegram("⬇️ <b>Uuendan koodi…</b>")
    try:
        r = subprocess.run(["git", "pull"], cwd=d, capture_output=True, text=True, timeout=120)
        out = ((r.stdout or "") + (r.stderr or "")).strip()[-600:]
    except Exception as e:
        add_log(f"❌ git pull ebaõnnestus: {e}")
        send_telegram(f"❌ <b>git pull ebaõnnestus</b>\n{str(e)[:300]}\nBot jookseb vana koodiga edasi.")
        return

    if r.returncode != 0:
        add_log(f"❌ git pull viga: {out}")
        send_telegram(f"❌ <b>git pull viga</b>\n<code>{out[:300]}</code>\nBot jookseb vana koodiga edasi.")
        return

    if "Already up to date" in out or "Already up-to-date" in out:
        send_telegram(f"ℹ️ <b>Uut koodi ei olnud</b>\n<code>{out[:200]}</code>\nTaaskäivitust ei tehtud.")
        return

    # Kontrolli, et uus kood kompileerub ENNE taaskäivitust
    bad = []
    for fn in ("main_v4.py", "config.py", "gold_logic.py", "strategies.py",
               "mt5_connector.py", "strategy_meanrev.py"):
        p = os.path.join(d, fn)
        if not os.path.exists(p):
            continue
        c = subprocess.run([sys.executable, "-m", "py_compile", p],
                           capture_output=True, text=True)
        if c.returncode != 0:
            bad.append(f"{fn}: {(c.stderr or '')[-200:]}")
    if bad:
        add_log(f"🚨 Uus kood EI kompileeru, taaskäivitus tühistatud: {bad}")
        send_telegram("🚨 <b>Uus kood on katki — taaskäivitust EI tehtud</b>\n"
                      + "\n".join(f"<code>{b}</code>" for b in bad)[:600]
                      + "\n\nBot jookseb vana koodiga edasi.")
        return

    send_telegram(f"✅ <b>Kood uuendatud</b>\n<code>{out[:300]}</code>")
    do_restart("Telegrami käsk /update")


def check_telegram_commands():
    """
    Kontrolli Telegramis uusi sõnumeid — võimaldab kaugjuhtimisega
    kauplemise taasalustamist otse telefonist, ilma arvutit avamata.
    AINULT konfigureeritud TELEGRAM_CHAT_ID-st tulevad käsud arvestatakse.

    /reset või /resume — eemaldab nii circuit breaker'i kui päevalimiidi
                          peatuse, kaupleb kohe jälle edasi
    /status             — saadab hetke balance + equity
    /restart            — taaskäivitab boti (võtab kettal oleva koodi kasutusele)
    /update             — git pull + taaskäivitus (kaugdeploy telefonist)
    /help               — käskude nimekiri
    Kaitsemehhanismid ise (circuit breaker, päevalimiit) jäävad täielikult
    alles — see ainult annab mugava viisi neid vajadusel käsitsi lähtestada.
    """
    global _last_telegram_update_id
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        r = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
            params={"offset": _last_telegram_update_id + 1, "timeout": 0},
            timeout=10
        )
        if r.status_code != 200:
            return
        updates = r.json().get("result", [])
        for upd in updates:
            _last_telegram_update_id = max(_last_telegram_update_id, upd["update_id"])
            msg = upd.get("message", {})
            chat_id = str(msg.get("chat", {}).get("id", ""))
            text = (msg.get("text") or "").strip().lower()

            if chat_id != str(TELEGRAM_CHAT_ID):
                continue  # ignoreeri kõiki teisi saatjaid

            if text in ("/reset", "/resume"):
                rows = sb_select("bot_state", "id=eq.1&select=risk")
                risk = rows[0].get("risk", {}) if rows else {}
                had_pause = bool(risk.get("circuit", {}).get("paused_until_day") or
                                  risk.get("circuit", {}).get("paused_until_week") or
                                  risk.get("daily_gold_halt"))
                risk.pop("circuit", None)
                risk.pop("daily_gold_halt", None)
                sb_upsert("bot_state", {"id": 1, "risk": risk})
                if had_pause:
                    send_telegram("✅ Kauplemine taasalustatud — kõik pausid (circuit breaker, päevalimiit) eemaldatud.")
                    add_log("🔓 Kaugjuhtimisega reset tehtud Telegrami käsuga")
                else:
                    send_telegram("ℹ️ Ühtegi aktiivset pausi ei leitud — bot juba kaupleb.")

            elif text == "/status":
                bal = get_balance()
                eq  = get_account_equity()
                send_telegram(f"📊 <b>Staatus</b>\nBalance: {bal:.2f}€\nEquity: {eq:.2f}€")

            elif text == "/help":
                send_telegram(
                    "🤖 <b>Käsud</b>\n"
                    "/status — balance ja equity\n"
                    "/reset — eemalda pausid (circuit breaker, päevalimiit)\n"
                    "/restart — taaskäivita bot (kettal olev kood)\n"
                    "/update — tõmba GitHubist uus kood ja taaskäivita\n"
                    "/help — see nimekiri"
                )

            elif text == "/restart":
                do_restart("Telegrami käsk /restart")

            elif text == "/update":
                do_update()

    except Exception as e:
        logger.error(f"Telegram commands check: {e}")

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
_price_history = []  # viimased hinnad — külmunud andmevoo tuvastamiseks
_price_frozen_alerted = False

def check_price_frozen(price, window=10):
    """
    Tuvasta kui MT5 hinnavoog on külmunud — kui viimased `window` hinda on
    kõik täpselt identsed, on see ebatavaline (isegi rahulikul turul liigub
    kuld iga minuti jooksul vähemalt murdosa senti). Avastati 12.08 päris
    juhtum: hind jäi täpselt samaks ~56 järjestikust scanni (~56 min).
    Saadab Telegram-hoiatuse ainult üks kord episoodi kohta, mitte iga scanni.
    Tagastab True kui hind on külmunud (kaubeldamine tuleks vahele jätta).
    """
    global _price_history, _price_frozen_alerted
    _price_history.append(price)
    if len(_price_history) > window:
        _price_history.pop(0)

    if len(_price_history) < window:
        return False

    frozen = all(p == _price_history[0] for p in _price_history)

    if frozen and not _price_frozen_alerted:
        add_log(f"🧊 HOIATUS: hind ${price:.2f} pole muutunud {window} järjestikuse scanni jooksul — MT5 andmevoog võib olla külmunud")
        send_telegram(
            f"🧊 <b>Hinnavoog võib olla külmunud</b>\n"
            f"Gold hind ${price:.2f} pole muutunud {window} scanni jooksul.\n"
            f"Kontrolli MT5 ühendust VPS-il — kauplemine on peatatud, kuni hind uuesti liigub."
        )
        _price_frozen_alerted = True
    elif not frozen:
        _price_frozen_alerted = False

    return frozen

def get_trend(df):
    period = GRID_CONFIG["trend_period"]
    thresh = INSTRUMENTS["XAUUSD"]["trend_thresh"]
    return gold_logic.get_trend(df, period, thresh)

def calc_atr_gold(df):
    atr = gold_logic.calc_atr(df, period=14)
    _atr_history.append(atr)
    if len(_atr_history) > 100: _atr_history.pop(0)
    return atr

def get_vol_mult():
    return gold_logic.get_vol_mult(_atr_history, GRID_CONFIG)

def get_compound_lot(balance):
    # KAITSE: lot ülempiir — varem kasvas see piiramatult koos balance'iga,
    # mis 19 Aug backtestis (päris H1 andmed, 2a) oli reaalne põhjus, miks
    # vanad parameetrid (trend_thresh=0.1%) konto lõpuks tühjaks tegid, mitte
    # grid-strateegia enda loogika. Fikseeritud lot'iga sama strateegia oli
    # kasumlik ja stabiilne mõlemal poolel train/test jaotusest.
    return gold_logic.get_compound_lot(balance, ACCOUNT_BALANCE, _atr_history, GRID_CONFIG)

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
    Kui MT5-s on positsioon suletud (TP/SL tabas), märgi Supabase-s executed=True
    JA logi päris tulemus trades-tabelisse (varem ei salvestatud kunagi P&L-i).
    Kui MT5-s on positsioon, mida Supabase üldse ei jälgi, lisa see jälgimisele.
    Tagastab MT5-s lahti olevate ticketite seti.

    UUS (11 sept 2026): varem vaadati ainult regime=grid — portfelli
    (regime=portfolio) ja tuumik-ülekihi (regime=core_overlay) positsioonid
    jäid sünkroniseerimisest täiesti välja. Kasutaja avatud tehing oli
    seetõttu dashboardil "0 avatud positsiooni" kõrval, kuigi floating P&L
    näitas raha — sync ei teadnud sellest positsioonist üldse.

    Tundmatute positsioonide leidmiseks kasutatakse get_all_positions()'i
    (KÕIK positsioonid, sõltumata magic-numbrist), mitte get_open_positions()'i
    (magic=MAGIC filtriga) — käsitsi MT5 terminalis avatud tehingud kannavad
    tavaliselt magic=0 ja jäid muidu samamoodi nähtamatuks kui bot omal ajal
    Supabase'ist puudu jäänud positsioonid.
    """
    try:
        mt5_open = ct.get_open_positions()
        mt5_tickets = {p["ticket"] for p in mt5_open}

        all_open = ct.get_all_positions()
        all_by_ticket = {p["ticket"]: p for p in all_open}
        all_tickets = set(all_by_ticket)

        # Loe Supabase-st KÕIK lahti positsioonid, kõigist režiimidest.
        sb_open = sb_select("signals", "executed=eq.false&regime=in.(grid,portfolio,core_overlay,recovered)")
        tracked_tickets = {int(p["mt5_ticket"]) for p in sb_open if p.get("mt5_ticket") is not None}

        closed_found = False
        for pos in sb_open:
            ticket = pos.get("mt5_ticket")
            if ticket is None:
                continue  # vanad positsioonid ilma ticketita — jäta rahule
            if int(ticket) not in mt5_tickets:
                # MT5-s suletud aga Supabase-s lahti — too PÄRIS tulemus
                # tehinguajaloost ja logi trades-tabelisse.
                deal = ct.get_closed_deal_pnl(ticket)
                sb_upsert("signals", {"id": pos["id"], "executed": True})
                if deal:
                    ok = log_trade_close(pos, deal["pnl"], deal["close_price"],
                                         "sync", deal["close_time"])
                    add_log(f"🔄 Sync: {ticket} suletud, tulemus {deal['pnl']:+.2f}€"
                            f"{'' if ok else ' (trades salvestus ebaõnnestus!)'}")
                else:
                    add_log(f"🔄 Sync: positsioon {ticket} suletud MT5 poolt → Supabase uuendatud (P&L ei leitud)")
                closed_found = True

        # MT5-s avatud (SÕLTUMATA magic-numbrist — kaasa arvatud käsitsi
        # avatud tehingud), aga Supabase-s tundmatu positsioon — varem
        # täiesti nähtamatu. Loo jälgitav kirje, et dashboard ja järgmine
        # sync sellest edaspidi teaksid. Bot ei halda seda (ei sule, ei
        # muuda TP/SL) — ainult jälgib ja logib tulemuse, kui see sulgub.
        for ticket in (all_tickets - tracked_tickets):
            p = all_by_ticket[ticket]
            own = p.get("magic") == ct.MAGIC
            sb_insert("signals", {
                "direction":  p["direction"],
                "entry":      p["price_open"],
                "tp":         p["tp"],
                "sl":         p["sl"],
                "lot":        p["volume"],
                "regime":     "recovered",
                "session":    f"recovered_{p['symbol']}",
                "executed":   False,
                "breakeven":  False,
                "atr":        0,
                "score":      0,
                "mt5_ticket": ticket,
            })
            kirjeldus = "boti oma, kadunud Supabase'ist" if own else "käsitsi/muu, magic pole boti"
            add_log(f"⚠️ Sync: MT5-s tundmatu positsioon {ticket} ({p['symbol']}, {kirjeldus}) leitud — lisatud jälgimisele")
            send_telegram(f"⚠️ <b>Tundmatu positsioon leitud</b>\n{p['symbol']} #{ticket} ({kirjeldus})\nLisati jälgimisele — bot ei sule seda automaatselt.")

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
    return gold_logic.get_swing_levels(df, lookback)


def calc_gold_tp_sl(direction, level, atr, swing_low, swing_high):
    return gold_logic.calc_gold_tp_sl(direction, level, atr, swing_low, swing_high, GRID_CONFIG)


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

def get_core_position():
    """Tuumikpositsioon (osta ja hoia) — session='core'."""
    rows = sb_select("signals", "executed=eq.false&session=eq.core&limit=1")
    return rows[0] if rows else None


def get_overlay_positions():
    return sb_select("signals", "executed=eq.false&session=eq.overlay&order=created_at.asc")


def run_gold_core_overlay(price, high, low, now, df):
    """
    TUUMIK + ÜLEKIHT (config: strategy_mode="core_overlay").

    Tuumik: üks ostupositsioon, mida hoitakse. Ei suleta nädalavahetuseks —
            see on teadlik valik (muidu pole see hoidmine), aga tähendab
            reaalset gap-riski.
    Ülekiht: donchian väljamurre mõlemas suunas, ATR-põhine SL/TP, riskipõhine
            lot. Ülekiht võib minna lühikeseks, tuumik mitte.

    Kaitsed, mis jäävad kehtima: päevalimiit, circuit breaker (main loop'is),
    uudiste-aken ülekihi sisenemistele.
    """
    cfg = GRID_CONFIG

    # ── TUUMIK ──
    if cfg.get("core_enabled", True) and now.weekday() < 5:
        core = get_core_position()
        if core is None and not gold_logic.is_news_blackout(now):
            lot = float(cfg.get("core_lot", 0.01))
            res = ct.place_order("buy", "XAUUSD", lot)
            if "error" in res:
                add_log(f"❌ Tuumiku avamine ebaõnnestus: {res['error']}")
            else:
                ok = sb_insert("signals", {
                    "direction": "buy", "entry": round(price, 2), "tp": None, "sl": None,
                    "lot": lot, "regime": "core_overlay", "session": "core",
                    "executed": False, "breakeven": False, "atr": 0, "score": 0,
                    "mt5_ticket": res.get("orderId"),
                })
                add_log(f"🟢 TUUMIK avatud @ {price:.2f} lot={lot} (ticket {res.get('orderId')})")
                send_telegram(f"🟢 <b>Tuumikpositsioon avatud</b>\nBUY {lot} @ {price:.2f}\nSeda hoitakse — TP/SL puudub.")
                if not ok:
                    logger.error(f"🚨 KRIITILINE: tuumik {res.get('orderId')} täitus, Supabase salvestus ebaõnnestus — JÄLGIMATA!")
                    send_telegram(f"🚨 <b>KRIITILINE</b>\nTuumik {res.get('orderId')} täitus MT5-l, aga andmebaasi ei jõudnud. Kontrolli käsitsi!")

    if not cfg.get("overlay_enabled", True):
        return

    # ── ÜLEKIHT: sulgemiste kontroll ──
    balance = get_balance()
    for pos in get_overlay_positions():
        entry, d = float(pos.get("entry", 0)), pos.get("direction", "buy")
        tp, sl = pos.get("tp"), pos.get("sl")
        hit = None
        if tp is not None and ((high >= float(tp)) if d == "buy" else (low <= float(tp))):
            hit = ("TP", float(tp))
        elif sl is not None and ((low <= float(sl)) if d == "buy" else (high >= float(sl))):
            hit = ("SL", float(sl))
        if not hit:
            continue
        label, level = hit
        lot = float(pos.get("lot") or 0.01)
        pnl = (level - entry) * lot * 100 if d == "buy" else (entry - level) * lot * 100
        sb_upsert("signals", {"id": pos["id"], "executed": True})
        log_trade_close(pos, pnl, level, f"overlay_{label.lower()}")
        add_log(f"{'✅' if pnl > 0 else '🛑'} Ülekiht {label}: {d.upper()} {entry:.2f}→{level:.2f}  {pnl:+.2f}€")
        send_telegram(f"{'✅' if pnl > 0 else '🛑'} <b>Ülekiht {label}</b>\n{d.upper()} {entry:.2f}→{level:.2f}\n{pnl:+.2f}€")

    # ── ÜLEKIHT: uus signaal ──
    if now.weekday() >= 5 or gold_logic.is_news_blackout(now):
        return
    open_ov = get_overlay_positions()
    if len(open_ov) >= int(cfg.get("overlay_max_pos", 1)):
        return
    if df is None:
        return
    atr_val = _atr_history[-1] if _atr_history else gold_logic.calc_atr(df)
    sig = gold_logic.donchian_signal(df, int(cfg.get("bo_lookback", 20)), atr_val, cfg)
    if sig is None:
        return
    direction, sl_dist, tp_dist = sig
    if open_ov and open_ov[0].get("direction") != direction:
        return  # ei ava hedge ülekihi sees
    lot = gold_logic.get_risk_based_lot(balance, sl_dist, 100.0,
                                        cfg.get("risk_pct", 0.015),
                                        max_lot=cfg.get("risk_lot_max", 0.5))
    tp = round(price + tp_dist if direction == "buy" else price - tp_dist, 2)
    sl = round(price - sl_dist if direction == "buy" else price + sl_dist, 2)
    res = ct.place_order(direction, "XAUUSD", lot, tp=tp, sl=sl)
    if "error" in res:
        add_log(f"❌ Ülekihi order ebaõnnestus: {res['error']}")
        return
    ok = sb_insert("signals", {
        "direction": direction, "entry": round(price, 2), "tp": tp, "sl": sl,
        "lot": lot, "regime": "core_overlay", "session": "overlay",
        "executed": False, "breakeven": False, "atr": round(atr_val, 2), "score": 0,
        "mt5_ticket": res.get("orderId"),
    })
    add_log(f"📊 Ülekiht {direction.upper()} @ {price:.2f} lot={lot} TP:{tp:.2f} SL:{sl:.2f}")
    send_telegram(f"📊 <b>Ülekiht {direction.upper()}</b>\n@ {price:.2f} lot={lot}\nTP {tp:.2f} | SL {sl:.2f}")
    if not ok:
        logger.error(f"🚨 KRIITILINE: ülekiht {res.get('orderId')} täitus, Supabase salvestus ebaõnnestus — JÄLGIMATA!")
        send_telegram(f"🚨 <b>KRIITILINE</b>\nÜlekiht {res.get('orderId')} täitus MT5-l, aga andmebaasi ei jõudnud. Kontrolli käsitsi!")


# ─────────────────────────────────────────────────────────
#  HAJUTATUD PORTFELL
# ─────────────────────────────────────────────────────────

_symbol_cache = {}


def resolve_broker_symbol(candidates):
    """
    Leia, millise nime all broker instrumenti pakub. Eri brokerid kutsuvad
    indekseid erinevalt (US500 / SPX500 / USA500 ...), seega proovime
    kandidaadid läbi ja jätame meelde esimese, mis andmeid tagastab.
    Tagastab None, kui ükski ei tööta.
    """
    key = tuple(candidates)
    if key in _symbol_cache:
        return _symbol_cache[key]
    for cand in candidates:
        try:
            df = ct.get_candles(cand, interval="1d", count=5)
            if df is not None and not df.empty:
                _symbol_cache[key] = cand
                add_log(f"🔎 Sümbol lahendatud: {cand}")
                return cand
        except Exception:
            continue
    _symbol_cache[key] = None
    add_log(f"⚠️ Ühtegi sümbolit ei leitud: {candidates} — see jalg jäetakse vahele")
    return None


def _portfolio_signal_fn(kind):
    import strategies as S
    return {
        "donchian":       S.sig_donchian,
        "donchian_trend": S.sig_donchian_trendfiltered,
        "bollinger_fade": S.sig_bollinger_reversion,
        "ts_momentum":    S.sig_ts_momentum,
        "ema_cross":      S.sig_ema_cross,
    }.get(kind)


def run_portfolio_leg(leg, now):
    """Üks portfelli jalg: sulge tabatud positsioonid, ava uus signaali korral."""
    name = leg["name"]
    pv = float(leg.get("pip_value", 100.0))
    sym = resolve_broker_symbol(leg["symbol_candidates"])
    if sym is None:
        return

    interval = GRID_CONFIG.get("portfolio_interval", "1d")
    df = get_data(sym, interval=interval, outputsize=300)
    if df is None or len(df) < 60:
        add_log(f"⚠️ {name}: andmeid liiga vähe")
        return
    price = get_price(sym)
    if price <= 0:
        price = float(df["close"].iloc[-1])
    high = float(df["high"].iloc[-1])
    low = float(df["low"].iloc[-1])

    session = f"pf_{name}"
    open_pos = sb_select("signals", f"executed=eq.false&session=eq.{session}&order=created_at.asc")

    # ── sulgemised ──
    for pos in open_pos:
        entry, d = float(pos.get("entry", 0)), pos.get("direction", "buy")
        tp, sl = pos.get("tp"), pos.get("sl")
        hit = None
        if tp is not None and ((high >= float(tp)) if d == "buy" else (low <= float(tp))):
            hit = ("TP", float(tp))
        elif sl is not None and ((low <= float(sl)) if d == "buy" else (high >= float(sl))):
            hit = ("SL", float(sl))
        if not hit:
            continue
        label, level = hit
        lot = float(pos.get("lot") or 0.01)
        pnl = (level - entry) * lot * pv if d == "buy" else (entry - level) * lot * pv
        sb_upsert("signals", {"id": pos["id"], "executed": True})
        log_trade_close(pos, pnl, level, f"portfolio_{label.lower()}")
        add_log(f"{'✅' if pnl > 0 else '🛑'} {name} {label}: {d.upper()} {entry:.4f}→{level:.4f}  {pnl:+.2f}€")
        send_telegram(f"{'✅' if pnl > 0 else '🛑'} <b>{name} {label}</b>\n{d.upper()} {entry:.4f}→{level:.4f}\n{pnl:+.2f}€")

    # ── uus signaal ──
    if now.weekday() >= 5 or gold_logic.is_news_blackout(now):
        return
    if [p for p in open_pos if not p.get("executed")]:
        return  # üks positsioon korraga jala kohta
    # Backtestis sai iga baar anda MAX ÜHE sisenemise. Live skaneerib aga iga
    # minut, nii et sama päevabaari signaal käivituks ikka ja jälle (ka kohe
    # pärast TP/SL sulgemist). Seepärast: üks sisenemine päevas jala kohta.
    today_iso = now.strftime("%Y-%m-%d")
    if sb_select("signals", f"session=eq.{session}&created_at=gte.{today_iso}&limit=1"):
        return
    fn = _portfolio_signal_fn(leg.get("signal"))
    if fn is None:
        add_log(f"⚠️ {name}: tundmatu signaal {leg.get('signal')}")
        return
    sig = fn(df, dict(leg.get("params", {})))
    if sig is None:
        return
    direction, sl_dist, tp_dist = sig
    if sl_dist <= 0:
        return

    balance = get_balance()
    lot = gold_logic.get_risk_based_lot(balance, sl_dist, pv,
                                        GRID_CONFIG.get("portfolio_risk_pct", 0.015),
                                        max_lot=GRID_CONFIG.get("risk_lot_max", 0.5))
    tp = round(price + tp_dist if direction == "buy" else price - tp_dist, 5)
    sl = round(price - sl_dist if direction == "buy" else price + sl_dist, 5)
    res = ct.place_order(direction, sym, lot, tp=tp, sl=sl)
    if "error" in res:
        add_log(f"❌ {name} order ebaõnnestus: {res['error']}")
        return
    ok = sb_insert("signals", {
        "direction": direction, "entry": round(price, 5), "tp": tp, "sl": sl,
        "lot": lot, "regime": "portfolio", "session": session,
        "executed": False, "breakeven": False, "atr": 0, "score": 0,
        "mt5_ticket": res.get("orderId"),
    })
    add_log(f"📊 {name} {direction.upper()} @ {price:.4f} lot={lot} TP:{tp} SL:{sl}")
    send_telegram(f"📊 <b>{name} {direction.upper()}</b>\n@ {price:.4f} lot={lot}\nTP {tp} | SL {sl}")
    if not ok:
        logger.error(f"🚨 KRIITILINE: {name} order {res.get('orderId')} täitus, Supabase salvestus ebaõnnestus — JÄLGIMATA!")
        send_telegram(f"🚨 <b>KRIITILINE</b>\n{name} {res.get('orderId')} täitus MT5-l, aga andmebaasi ei jõudnud. Kontrolli käsitsi!")


def run_portfolio(now):
    for leg in GRID_CONFIG.get("portfolio_legs", []):
        try:
            run_portfolio_leg(leg, now)
        except Exception as e:
            add_log(f"❌ Portfell {leg.get('name')}: {e}")


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
                close_ok = False
                if ticket:
                    close_ok = ct.close_position(int(ticket))
                    if not close_ok:
                        add_log(f"⚠️ Weekend sulgemine: MT5 positsioon {ticket} sulgemine ebaõnnestus")
                else:
                    # UUS: puuduva mt5_ticket puhul enam ei märgita vaikimisi
                    # suletuks (vt trendipöörde plokk allpool, sama parandus).
                    add_log(f"⚠️ Weekend sulgemine: positsioonil {pos.get('id')} puudub mt5_ticket — vajab käsitsi kontrolli!")
                    send_telegram(f"⚠️ <b>TÄHELEPANU:</b> nädalavahetuse sulgemisel puudus positsioonil mt5_ticket. Kontrolli MT5-l käsitsi!")
                if close_ok:
                    balance = round(balance+fl, 2)
                    sb_upsert("signals", {"id": pos["id"], "executed": True})
                    sb_upsert("bot_state", {"id": 1, "balance": balance})
                    log_trade_close(pos, fl, price, "weekend")
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

    # ATR-põhine adaptiivne grid-samm — vaikimisi väljas, vt config.py
    effective_gs = gold_logic.get_dynamic_grid_size(atr_val, GRID_CONFIG) if GRID_CONFIG.get("dynamic_grid_size") else gs

    # Uudiste-aken (Fed/NFP) — blokeerib ainult UUTE positsioonide avamist,
    # olemasolevate TP/SL/float-stop/trendipöörde haldus jätkub tavapäraselt.
    news_blackout = GRID_CONFIG.get("news_filter", True) and gold_logic.is_news_blackout(now)

    # ADX choppiness-filter — blokeerib ainult UUE grid'i avamist, mitte
    # olemasoleva haldust. Vt config.py kommentaar: backtest näitas
    # trend_reset'i (grid avatud, trend kohe ümber pööranud) suurimaks
    # üksikuks kahjumi-allikaks madala-trendi (chop) turul.
    adx_ok = True
    if GRID_CONFIG.get("adx_filter", False) and df is not None and len(df) >= 28:
        adx_ok = gold_logic.calc_adx(df["high"], df["low"], df["close"]) >= GRID_CONFIG.get("adx_min", 20.0)

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
        if effective_trend == "neutral" or news_blackout or not adx_ok: return
        center  = round(price/effective_gs)*effective_gs
        pending = gold_logic.setup_grid(center, effective_trend, effective_gs, gl)
        save_grid_state({"center":center,"trend":effective_trend,"pending":pending})
        add_log(f"🔲 Gold grid initsialiseeritud @ ${center:.0f} | {effective_trend}")
        # Saada XTrend signaalid käsitsi sisestamiseks
        send_grid_signals(center, effective_trend, effective_gs, 30.0, 45.0, get_compound_lot(balance))
        return

    pending    = grid_state.get("pending", {})
    grid_trend = grid_state.get("trend", "neutral")
    grid_center = grid_state.get("center", grid_state.get("grid", {}).get("center", price))

    # Auto-reset kui hind on liiga kaugel grid keskusest (3x grid size)
    if abs(price - grid_center) > effective_gs * 3 and len(ct.get_open_positions("XAUUSD")) == 0 and adx_ok:
        new_c = round(price/effective_gs)*effective_gs
        reset_trend = effective_trend if effective_trend != "neutral" else grid_trend
        save_grid_state({"center":new_c,"trend":reset_trend,"pending":gold_logic.setup_grid(new_c, reset_trend, effective_gs, gl)})
        add_log(f"🔄 Grid auto-reset: hind ${price:.0f} kaugel keskusest ${grid_center:.0f}")
        send_grid_signals(new_c, reset_trend, effective_gs, 30.0, 45.0, get_compound_lot(balance))
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
            close_ok = False
            if ticket:
                close_ok = ct.close_position(int(ticket))
                if not close_ok:
                    add_log(f"⚠️ Trend reset: MT5 positsioon {ticket} sulgemine ebaõnnestus — proovin uuesti järgmisel scannil")
            else:
                # UUS: varem oli see vaikimisi True ehk "suletud", mis TÄHENDAS,
                # et kui mt5_ticket väli oli mingil põhjusel tühi, märkis bot
                # Supabase's positsiooni suletuks ILMA MT5-l reaalselt midagi
                # sulgemata - konto sisemine arvestus lahknes reaalsest MT5
                # seisust, ilma et keegi seda märganud oleks (juhtus 28 Aug 2026).
                add_log(f"⚠️ Trend reset: positsioonil {pos.get('id')} puudub mt5_ticket — EI sule automaatselt, vajab käsitsi kontrolli MT5-l!")
                send_telegram(f"⚠️ <b>TÄHELEPANU:</b> positsioonil puudub mt5_ticket, trendipööre ei saanud seda sulgeda automaatselt. Kontrolli MT5-l käsitsi!")
            if close_ok:
                balance = round(balance+fl, 2)
                sb_upsert("signals", {"id":pos["id"],"executed":True})
                sb_upsert("bot_state", {"id":1,"balance":balance})
                log_trade_close(pos, fl, price, "trend_reset")
        if adx_ok:
            new_c = round(price/effective_gs)*effective_gs
            save_grid_state({"center":new_c,"trend":effective_trend,"pending":gold_logic.setup_grid(new_c, effective_trend, effective_gs, gl)})
            add_log(f"🔄 Gold grid reset: {grid_trend}→{effective_trend}")
            send_grid_signals(new_c, effective_trend, effective_gs, 30.0, 45.0, get_compound_lot(balance))
        else:
            # ADX liiga madal uue grid'i jaoks — sulge vastutrendi positsioonid
            # (juba tehtud ülal), aga ÄRA ava uut suunda enne kui trend
            # reaalselt kinnitub (ADX tõuseb). Järgmine scan proovib uuesti.
            save_grid_state(None)
            add_log(f"⏸ Gold grid: {grid_trend}→{effective_trend} suletud, uut ei avata (ADX liiga madal / chop)")
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
            log_trade_close(pos, pnl, tp, "gold_tp")
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
            close_ok = False
            if ticket:
                close_ok = ct.close_position(int(ticket))
                if not close_ok:
                    add_log(f"⚠️ Float stop: MT5 positsioon {ticket} sulgemine ebaõnnestus — proovin uuesti järgmisel scannil")
            else:
                add_log(f"⚠️ Float stop: positsioonil {pid} puudub mt5_ticket — vajab käsitsi kontrolli!")
                send_telegram(f"⚠️ <b>TÄHELEPANU:</b> float-stop käivitus, aga positsioonil puudus mt5_ticket. Kontrolli MT5-l käsitsi!")
            if close_ok:
                balance = round(balance+fl, 2)
                sb_upsert("signals", {"id":pid,"executed":True})
                sb_upsert("bot_state", {"id":1,"balance":balance})
                log_trade_close(pos, fl, price, "float_stop")
                add_log(f"🛡 Gold float stop: {d.upper()} @ {entry:.0f}  {fl:+.2f}€")

    triggered = []
    for level_str, direction in ([] if news_blackout else list(pending.items())):
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
        if GRID_CONFIG.get("dynamic_tp_sl"):
            swing_low, swing_high = gold_logic.get_swing_levels(df, lookback=20)
            tp, sl = gold_logic.calc_gold_tp_sl(direction, price, atr_val, swing_low, swing_high, GRID_CONFIG)
        else:
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
        sb_ok = sb_insert("signals", {
            "direction":direction,"entry":price,"tp":tp,
            "sl":sl,
            "lot":lot,"regime":"grid","session":f"gold_{effective_trend}",
            "executed":False,"breakeven":False,"atr":effective_gs,"score":0,"rr":3.0,
            "mt5_ticket": order_result.get("orderId"),
        })
        triggered.append(level_str)
        add_log(f"📊 Gold order: {direction.upper()} @ {price:.0f}  TP:{tp:.0f} (ticket:{order_result.get('orderId')})")
        send_telegram(f"📊 <b>Gold Grid Order</b>\n{direction.upper()} @ <b>{price:.0f}</b>\nTP: <b>{tp:.0f}</b> | {effective_trend}")
        if not sb_ok:
            # KRIITILINE: PÄRIS MT5 positsioon on olemas, aga bot ei tea
            # sellest oma andmebaasis - keegi peab käsitsi jälgima/sulgema,
            # kuna trendipööre/nädalavahetuse-sulgemine/float-stop ei
            # suuda seda automaatselt hallata.
            logger.error(f"🚨 KRIITILINE: order {order_result.get('orderId')} täitus MT5-l, aga Supabase salvestus ebaõnnestus kahel katsel - positsioon on JÄLGIMATA!")
            send_telegram(f"🚨 <b>KRIITILINE HOIATUS</b>\nTicket <b>{order_result.get('orderId')}</b> ({direction.upper()} @ {price:.0f}) täitus MT5-l, aga andmebaasi salvestus ebaõnnestus.\nBot EI SAA seda positsiooni automaatselt hallata (trendipööre/nädalavahetus/float-stop ei toimi sellel).\n<b>Kontrolli ja halda MT5-l käsitsi!</b>")

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
            # UUS (2 Sept 2026): range-lävi tõstetud $10 -> $20, TP/SL vahetatud
            # $10/$15 (60,0% vajalik võiduprotsent, sai 59,5% - matemaatiliselt
            # kaotav) -> $12/$25 (67,6% vajalik, testitud 69,9% M5 reaalandmetel,
            # märts-august 2026, kasumlik mõlemal poolaastal eraldi, ei läinud
            # kordagi miinusesse). Serv on ikka õhuke - jälgi jätkuvalt.
            if range5 > 20 and not news_blackout:
                scalp_positions = [p for p in get_gold_positions() if p.get("session","").startswith("scalp")]
                if len(scalp_positions) < 2:  # max 2 scalp positsiooni
                    lot_scalp = round(round(max(0.01, (balance/ACCOUNT_BALANCE)*0.01) / 0.01) * 0.01, 2)

                    if effective_trend == "bull" and l5 < price - 5:
                        # TP/SL arvutatakse PÄRIS hetkehinna (price) pealt, mitte vana
                        # l5 (5min madalpunkt) pealt — order on market order, mis täitub
                        # kohese turuhinnaga, mistõttu vana l5-põhine TP oli tihti juba
                        # peaaegu käes enne kui order üldse täitus (nt +0,90€ 18 sek pärast).
                        tp_scalp = round(price + 12, 2)
                        sl_scalp = round(price - 25, 2)
                        scalp_result = ct.place_order("buy", "XAUUSD", lot_scalp, tp=tp_scalp, sl=sl_scalp)
                        if "error" not in scalp_result:
                            sb_ok = sb_insert("signals", {
                                "direction":"buy","entry":round(price,2),"tp":tp_scalp,
                                "sl":sl_scalp,"lot":lot_scalp,"regime":"grid",
                                "session":"scalp_bull","executed":False,"breakeven":False,
                                "atr":range5,"score":1,"rr":0.67,
                                "mt5_ticket": scalp_result.get("orderId"),
                            })
                            add_log(f"⚡ Scalp BUY @ {price:.0f} TP:{tp_scalp:.0f}")
                            if not sb_ok:
                                logger.error(f"🚨 KRIITILINE: scalp order {scalp_result.get('orderId')} täitus MT5-l, aga Supabase salvestus ebaõnnestus - positsioon on JÄLGIMATA!")
                                send_telegram(f"🚨 <b>KRIITILINE HOIATUS</b>\nScalp ticket <b>{scalp_result.get('orderId')}</b> (BUY @ {price:.0f}) täitus MT5-l, aga andmebaasi salvestus ebaõnnestus.\n<b>Kontrolli ja halda MT5-l käsitsi!</b>")
                        else:
                            add_log(f"❌ Scalp BUY ebaõnnestus: {scalp_result['error']}")

                    elif effective_trend == "bear" and h5 > price + 5:
                        # Sama parandus mis BUY harus — price, mitte vana h5
                        tp_scalp = round(price - 12, 2)
                        sl_scalp = round(price + 25, 2)
                        scalp_result = ct.place_order("sell", "XAUUSD", lot_scalp, tp=tp_scalp, sl=sl_scalp)
                        if "error" not in scalp_result:
                            sb_ok = sb_insert("signals", {
                                "direction":"sell","entry":round(price,2),"tp":tp_scalp,
                                "sl":sl_scalp,"lot":lot_scalp,"regime":"grid",
                                "session":"scalp_bear","executed":False,"breakeven":False,
                                "atr":range5,"score":1,"rr":0.67,
                                "mt5_ticket": scalp_result.get("orderId"),
                            })
                            add_log(f"⚡ Scalp SELL @ {price:.0f} TP:{tp_scalp:.0f}")
                            if not sb_ok:
                                logger.error(f"🚨 KRIITILINE: scalp order {scalp_result.get('orderId')} täitus MT5-l, aga Supabase salvestus ebaõnnestus - positsioon on JÄLGIMATA!")
                                send_telegram(f"🚨 <b>KRIITILINE HOIATUS</b>\nScalp ticket <b>{scalp_result.get('orderId')}</b> (SELL @ {price:.0f}) täitus MT5-l, aga andmebaasi salvestus ebaõnnestus.\n<b>Kontrolli ja halda MT5-l käsitsi!</b>")
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

            # ── TELEGRAM KAUGKÄSUD (/reset, /status) ──
            # Kontrolli ENNE circuit breaker'it — muidu ei jõuaks /reset
            # käsk kunagi kohale, kui bot on juba pausil (continue allpool
            # katkestaks selle scanni enne käsu kontrollimist).
            check_telegram_commands()

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
                        if check_price_frozen(price_gold):
                            add_log(f"🧊 Hind endiselt külmunud ${price_gold:.2f} — kauplemine peatatud")
                        else:
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
                            if GRID_CONFIG.get("strategy_mode", "grid") == "core_overlay":
                                if df_gold is not None:
                                    calc_atr_gold(df_gold)
                                run_gold_core_overlay(price_gold, high_gold, low_gold, now, df_gold)
                            else:
                                run_gold_grid(price_gold, high_gold, low_gold, now)
                    else:
                        add_log("⚠️ Gold: hind puudub cTrader-ist")
                except Exception as e:
                    add_log(f"❌ Gold error: {e}")

            # ── HAJUTATUD PORTFELL ──
            if GRID_CONFIG.get("portfolio_enabled", False):
                try:
                    run_portfolio(now)
                except Exception as e:
                    add_log(f"❌ Portfelli viga: {e}")

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
            equity  = get_account_equity()
            open_all = sb_select("signals", "executed=eq.false")
            gold_pos  = [p for p in open_all if p.get("regime")=="grid"]
            forex_pos = [p for p in open_all if p.get("regime")=="meanrev"]
            # regime="portfolio" (hajutatud portfell) ja "core_overlay" ei
            # mahtunud kumbagi ülemisse ämbrisse — ilma selleta ei näidanud
            # dashboard neid ÜLDSE, ka siis kui nad reaalselt kauplesid.
            pf_pos = [p for p in open_all if p.get("regime") in ("portfolio", "core_overlay")]

            # Detailne positsioonide nimekiri dashboard'i jaoks — päris
            # entry/TP/SL/suund + hetke floating vahe, mitte ainult arv.
            # Portfelli jalgade hinnad on eri instrumentidel, seega floating'ut
            # ei saa arvutada kulla hinnast — need näidatakse ilma selleta.
            positions_detail = []
            for p in gold_pos:
                entry = float(p.get("entry", 0) or 0)
                direction = p.get("direction", "buy")
                floating = (price_gold - entry) if direction == "buy" else (entry - price_gold)
                positions_detail.append({
                    "direction":     direction,
                    "entry":         entry,
                    "tp":            p.get("tp"),
                    "sl":            p.get("sl"),
                    "floating_diff": round(floating, 2),
                    "mt5_ticket":    p.get("mt5_ticket"),
                    "session":       p.get("session"),
                })
            for p in pf_pos:
                positions_detail.append({
                    "direction":     p.get("direction", "buy"),
                    "entry":         float(p.get("entry", 0) or 0),
                    "tp":            p.get("tp"),
                    "sl":            p.get("sl"),
                    "floating_diff": None,
                    "mt5_ticket":    p.get("mt5_ticket"),
                    "session":       p.get("session"),
                })

            # Aktiivsed instrumendid — mida bot PÄRISELT kaupleb, mitte kogu
            # INSTRUMENTS nimekiri (seal on 10 väljalülitatud forex-paari).
            if GRID_CONFIG.get("portfolio_enabled"):
                active_syms = [l["name"] for l in GRID_CONFIG.get("portfolio_legs", [])]
            else:
                active_syms = [k for k, v in INSTRUMENTS.items() if v.get("enabled")]

            sb_upsert("bot_state", {
                "id": 1, "updated_at": now.isoformat(),
                # Ülemine "balance" väli varem kirjutati ainult grid- ja
                # nädalavahetuse-harudes, mis on portfellirežiimis välja
                # lülitatud — see jäi külmunuks samal ajal kui stats.balance
                # allpool oli värske. Kirjuta see nüüd IGA skanni lõpus,
                # sõltumata režiimist, et üks ega teine väli enam lahku ei läheks.
                "balance": round(float(balance), 2) if balance else balance,
                "last_scan": now.strftime("%H:%M:%S UTC"),
                "log": log_buffer[-30:],
                "stats": {
                    "balance":         balance,
                    "equity":          round(equity, 2) if equity else balance,
                    "gold_positions":  len(gold_pos),
                    "forex_positions": len(forex_pos),
                    "portfolio_positions": len(pf_pos),
                    "positions_detail": positions_detail,
                    "scan":            scan_count,
                    "claude_bias":     _claude_cache.get("bias", "neutral"),
                    "claude_reason":   _claude_cache.get("reason", ""),
                    "price":           round(price_gold if price_gold > 0 else 0, 2),
                    "mode":            "portfell" if GRID_CONFIG.get("portfolio_enabled") else GRID_CONFIG.get("strategy_mode", "grid"),
                    "instruments":     active_syms,
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
