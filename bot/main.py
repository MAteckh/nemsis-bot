"""
NEMSIS v2 — Cloud Bot
Runs on Railway 24/7, pushes signals + state to Supabase.
"""

import sys, os, json, time, logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

# ── env vars (set in Railway dashboard)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://xqinzjaqorjqaexeoyqc.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "sb_secret_geYNl5euHLVWXQtone_N0g_K5nB0Zel")
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN",   "7502951774:AAFEdMlowZumpFlLm817UEP4ws40SeZtROo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7638697143")
SCAN_INTERVAL    = int(os.environ.get("SCAN_INTERVAL", "300"))
GNEWS_KEY        = os.environ.get("GNEWS_KEY", "f40bd5ed637296a902fe080a21d964dc")
CLAUDE_KEY       = os.environ.get("CLAUDE_KEY", "")
ANALYSIS_INTERVAL = int(os.environ.get("ANALYSIS_INTERVAL", "1800"))
_last_analysis   = 0

# ── logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("NemsisCLOUD")

# ── imports
import requests
import pandas as pd
import numpy as np

log_buffer = []

def add_log(msg):
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    entry = f"{ts}  {msg}"
    log_buffer.append(entry)
    if len(log_buffer) > 60:
        log_buffer.pop(0)
    logger.info(msg)


# ─────────────────────────────────────────────────────────
#  SUPABASE CLIENT
# ─────────────────────────────────────────────────────────

def sb_headers():
    return {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "return=minimal"
    }

def sb_insert(table: str, data: dict):
    try:
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=sb_headers(),
            json=data, timeout=10
        )
        if r.status_code not in (200, 201):
            logger.warning(f"Supabase insert {table}: {r.status_code} {r.text[:100]}")
    except Exception as e:
        logger.error(f"Supabase insert error: {e}")

def sb_upsert(table: str, data: dict):
    try:
        h = sb_headers()
        h["Prefer"] = "resolution=merge-duplicates"
        r = requests.post(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=h,
            json=data, timeout=10
        )
        if r.status_code not in (200, 201):
            logger.warning(f"Supabase upsert {table}: {r.status_code} {r.text[:100]}")
    except Exception as e:
        logger.error(f"Supabase upsert error: {e}")

def sb_select(table: str, params: str = "") -> list:
    try:
        r = requests.get(
            f"{SUPABASE_URL}/rest/v1/{table}?{params}",
            headers=sb_headers(), timeout=10
        )
        return r.json() if r.status_code == 200 else []
    except Exception as e:
        logger.error(f"Supabase select error: {e}")
        return []


# ─────────────────────────────────────────────────────────
#  DYNAMIC BALANCE
# ─────────────────────────────────────────────────────────

_BALANCE_DEFAULT = float(os.environ.get("ACCOUNT_BALANCE", "100"))

def get_account_balance() -> float:
    try:
        rows = sb_select("bot_state", "id=eq.1&select=balance")
        if rows and rows[0].get("balance"):
            bal = float(rows[0]["balance"])
            if bal > 0:
                return bal
    except Exception as e:
        logger.warning(f"Balance fetch error: {e}")
    return _BALANCE_DEFAULT


# ─────────────────────────────────────────────────────────
#  RISK PROTECTION — 4 kaitset
# ─────────────────────────────────────────────────────────

MAX_DAILY_LOSS_PCT  = 3.0   # 3% päevakahjum → stop
MAX_DRAWDOWN_PCT    = 10.0  # 10% kogu langus → stop
MAX_OPEN_SIGNALS    = 1     # korraga max 1 avatud signaal
MAX_LOSS_STREAK     = 3     # 3 kaotust järjest → 24h paus

def get_risk_state() -> dict:
    """
    Loeb risk state Supabase'ist.
    Tagastab: daily_loss, drawdown, loss_streak, paused_until
    """
    try:
        rows = sb_select("bot_state", "id=eq.1&select=risk_state")
        if rows and rows[0].get("risk_state"):
            return rows[0]["risk_state"]
    except Exception as e:
        logger.warning(f"Risk state fetch error: {e}")
    return {
        "daily_loss":    0.0,
        "daily_reset":   datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "loss_streak":   0,
        "paused_until":  None,
    }

def save_risk_state(state: dict):
    sb_upsert("bot_state", {"id": 1, "risk_state": state})

def check_risk_limits() -> tuple[bool, str]:
    """
    Kontrollib kõiki 4 kaitset.
    Tagastab (can_trade: bool, reason: str)
    """
    balance     = get_account_balance()
    risk_state  = get_risk_state()
    now         = datetime.now(timezone.utc)

    # ── Reset daily loss kell 00:00 UTC
    today = now.strftime("%Y-%m-%d")
    if risk_state.get("daily_reset") != today:
        risk_state["daily_loss"]  = 0.0
        risk_state["daily_reset"] = today
        save_risk_state(risk_state)
        add_log("🔄 Daily loss counter reset")

    # ── Kaitse 1: Pause streak
    paused_until = risk_state.get("paused_until")
    if paused_until:
        pause_dt = datetime.fromisoformat(paused_until)
        if now < pause_dt:
            remaining = int((pause_dt - now).total_seconds() / 3600)
            return False, f"Loss streak pause — {remaining}h remaining"
        else:
            risk_state["paused_until"] = None
            risk_state["loss_streak"]  = 0
            save_risk_state(risk_state)
            add_log("✅ Loss streak pause lifted")

    # ── Kaitse 2: Daily loss limit
    daily_loss = abs(float(risk_state.get("daily_loss", 0)))
    daily_loss_pct = (daily_loss / _BALANCE_DEFAULT) * 100
    if daily_loss_pct >= MAX_DAILY_LOSS_PCT:
        return False, f"Daily loss limit {daily_loss_pct:.1f}% >= {MAX_DAILY_LOSS_PCT}% — waiting for reset"

    # ── Kaitse 3: Max drawdown
    drawdown_pct = (1 - balance / _BALANCE_DEFAULT) * 100
    if drawdown_pct >= MAX_DRAWDOWN_PCT:
        return False, f"Max drawdown {drawdown_pct:.1f}% >= {MAX_DRAWDOWN_PCT}% — trading stopped"

    # ── Kaitse 4: Max open signals
    open_signals = sb_select("signals", "executed=eq.false&select=id")
    if len(open_signals) >= MAX_OPEN_SIGNALS:
        return False, f"Max open signals ({MAX_OPEN_SIGNALS}) reached — waiting for close"

    return True, ""

def update_risk_after_trade(pnl_eur: float):
    """Uuendab risk state pärast tehingu sulgemist."""
    risk_state = get_risk_state()
    now        = datetime.now(timezone.utc)

    if pnl_eur < 0:
        # Kahjum
        risk_state["daily_loss"]  = float(risk_state.get("daily_loss", 0)) + abs(pnl_eur)
        risk_state["loss_streak"] = int(risk_state.get("loss_streak", 0)) + 1
        streak = risk_state["loss_streak"]
        add_log(f"📉 Loss streak: {streak}/{MAX_LOSS_STREAK}")

        if streak >= MAX_LOSS_STREAK:
            pause_until = (now + timedelta(hours=24)).isoformat()
            risk_state["paused_until"] = pause_until
            add_log(f"⛔ {MAX_LOSS_STREAK} kaotust järjest — 24h paus aktiveeritud")
            send_telegram(
                f"⛔ <b>NEMSIS — 24h paus aktiveeritud</b>\n"
                f"{MAX_LOSS_STREAK} kaotust järjest.\n"
                f"Kauplemisel paus kuni: {pause_until[:16]} UTC"
            )
    else:
        # Kasum — reset streak
        risk_state["loss_streak"] = 0

    save_risk_state(risk_state)


# ─────────────────────────────────────────────────────────
#  ECONOMIC CALENDAR FILTER
# ─────────────────────────────────────────────────────────

HIGH_IMPACT_KEYWORDS = [
    "fed", "fomc", "federal reserve", "interest rate", "rate decision",
    "cpi", "inflation", "nfp", "non-farm", "payroll", "gdp",
    "powell", "unemployment", "pce"
]

def check_high_impact_news():
    try:
        now = datetime.now(timezone.utc)
        h = now.hour
        m = now.minute
        wd = now.weekday()

        if wd == 4 and now.day <= 7:
            if 10 <= h <= 14:
                return True, "NFP Friday — high volatility window"
        if wd == 2 and 16 <= h <= 20:
            return True, "Potential FOMC window — avoiding signal"
        if wd in [1, 2] and 7 <= now.day <= 14 and 12 <= h <= 14:
            return True, "Potential CPI window — avoiding signal"
        if 13 <= h < 14 and m < 30:
            return True, "US market open — high spread window"

        return False, ""
    except Exception as e:
        logger.error(f"Calendar check error: {e}")
        return False, ""


# ─────────────────────────────────────────────────────────
#  DXY CORRELATION FILTER
# ─────────────────────────────────────────────────────────

def get_dxy_bias():
    try:
        import yfinance as yf
        df = yf.Ticker("DX-Y.NYB").history(interval="1h", period="3d", auto_adjust=True)
        if df is None or df.empty or len(df) < 10:
            return "neutral_dxy"
        df.columns = [c.lower() for c in df.columns]
        closes = df["close"].dropna()
        if len(closes) < 10:
            return "neutral_dxy"
        ema10 = closes.ewm(span=10, adjust=False).mean().iloc[-1]
        ema20 = closes.ewm(span=20, adjust=False).mean().iloc[-1]
        last  = float(closes.iloc[-1])
        change_pct = (last - float(closes.iloc[-6])) / float(closes.iloc[-6]) * 100
        if ema10 > ema20 and change_pct > 0.15:
            return "bullish_dxy"
        elif ema10 < ema20 and change_pct < -0.15:
            return "bearish_dxy"
        return "neutral_dxy"
    except Exception as e:
        logger.error(f"DXY fetch error: {e}")
        return "neutral_dxy"


# ─────────────────────────────────────────────────────────
#  INDICATORS
# ─────────────────────────────────────────────────────────

def calc_rsi(s, p=14):
    d = s.diff()
    g = d.clip(lower=0).ewm(alpha=1/p, adjust=False).mean()
    l = (-d).clip(lower=0).ewm(alpha=1/p, adjust=False).mean()
    return 100 - 100/(1+g/(l+1e-10))

def calc_macd(s):
    m = s.ewm(span=12,adjust=False).mean() - s.ewm(span=26,adjust=False).mean()
    sig = m.ewm(span=9,adjust=False).mean()
    return m, sig

def calc_atr(df, p=14):
    hl = df.high-df.low
    hc = (df.high-df.close.shift()).abs()
    lc = (df.low-df.close.shift()).abs()
    return pd.concat([hl,hc,lc],axis=1).max(axis=1).ewm(alpha=1/p,adjust=False).mean()

def calc_adx(df, p=14):
    pdm = df.high.diff().clip(lower=0)
    mdm = (-df.low.diff()).clip(lower=0)
    atr = calc_atr(df, p)
    pdi = 100*pdm.ewm(alpha=1/p,adjust=False).mean()/(atr+1e-10)
    mdi = 100*mdm.ewm(alpha=1/p,adjust=False).mean()/(atr+1e-10)
    dx  = 100*(pdi-mdi).abs()/(pdi+mdi+1e-10)
    return dx.ewm(alpha=1/p,adjust=False).mean(), pdi, mdi

def calc_bb(s, w=20, n=2):
    m = s.rolling(w).mean()
    std = s.rolling(w).std()
    return m, m+n*std, m-n*std

def calc_sr_levels(df, lookback=50):
    highs = df['high'].tail(lookback)
    lows = df['low'].tail(lookback)
    levels = []
    for i in range(2, len(highs)-2):
        if highs.iloc[i] > highs.iloc[i-1] and highs.iloc[i] > highs.iloc[i+1] and \
           highs.iloc[i] > highs.iloc[i-2] and highs.iloc[i] > highs.iloc[i+2]:
            levels.append(float(highs.iloc[i]))
        if lows.iloc[i] < lows.iloc[i-1] and lows.iloc[i] < lows.iloc[i+1] and \
           lows.iloc[i] < lows.iloc[i-2] and lows.iloc[i] < lows.iloc[i+2]:
            levels.append(float(lows.iloc[i]))
    return sorted(set([round(l, 1) for l in levels]))

def get_nearest_sr(price, levels, atr):
    if not levels: return None, None, 0
    nearest = min(levels, key=lambda x: abs(x - price))
    dist = abs(nearest - price)
    bonus = max(0, int((1 - dist/(atr*2)) * 15)) if dist < atr*2 else 0
    above = nearest > price
    return nearest, above, bonus

def calc_hurst(s, max_lag=30):
    prices = np.array(s.dropna())
    if len(prices) < max_lag+5: return 0.5
    tau = [(lag, np.std(np.subtract(prices[lag:],prices[:-lag]))) for lag in range(2,max_lag) if np.std(np.subtract(prices[lag:],prices[:-lag]))>0]
    if len(tau)<3: return 0.5
    m = np.polyfit(np.log([t[0] for t in tau]), np.log([t[1] for t in tau]), 1)
    return float(m[0]/2.0)

def add_indicators(df):
    df = df.copy()
    df["ema20"]  = df.close.ewm(span=20,adjust=False).mean()
    df["ema50"]  = df.close.ewm(span=50,adjust=False).mean()
    df["ema100"] = df.close.ewm(span=100,adjust=False).mean()
    df["rsi"]    = calc_rsi(df.close)
    df["macd"],df["macd_sig"] = calc_macd(df.close)
    df["atr"]    = calc_atr(df)
    df["adx"],df["pdi"],df["mdi"] = calc_adx(df)
    df["bb_mid"],df["bb_up"],df["bb_lo"] = calc_bb(df.close)
    k = df['close'].rolling(14).apply(lambda x:(x.iloc[-1]-x.min())/(x.max()-x.min()+1e-10)*100, raw=False)
    df["stoch_k"] = k.rolling(3).mean()
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()
    df["vol_ma"] = df["volume"].rolling(20).mean()
    df["vol_ratio"] = df["volume"] / (df["vol_ma"] + 1e-10)
    return df

def detect_candle_pattern(df):
    if len(df) < 3: return None, 0
    c = df.iloc[-1]
    p = df.iloc[-2]
    pp = df.iloc[-3]
    body = abs(c.close - c.open)
    full = c.high - c.low + 1e-10
    upper_wick = c.high - max(c.close, c.open)
    lower_wick = min(c.close, c.open) - c.low
    body_ratio = body / full
    if c.close > c.open and p.close < p.open:
        if c.open < p.close and c.close > p.open:
            return "bullish_engulfing", 15
    if c.close < c.open and p.close > p.open:
        if c.open > p.close and c.close < p.open:
            return "bearish_engulfing", 15
    if lower_wick > body * 2 and lower_wick > upper_wick * 2 and body_ratio < 0.4:
        return "bullish_pinbar", 12
    if upper_wick > body * 2 and upper_wick > lower_wick * 2 and body_ratio < 0.4:
        return "bearish_pinbar", 12
    if c.high < p.high and c.low > p.low:
        return "inside_bar", 5
    return None, 0

def get_regime(df):
    h = calc_hurst(df.close.tail(60))
    adx = df.adx.iloc[-1] if "adx" in df.columns else 20
    pdi = df.pdi.iloc[-1] if "pdi" in df.columns else 0
    mdi = df.mdi.iloc[-1] if "mdi" in df.columns else 0
    if h>0.55 and adx>22:
        return ("trending_bull" if pdi>mdi else "trending_bear"), min(100,adx*2)
    if h<0.45 or adx<18: return "ranging", 60
    return "transitioning", 50


# ─────────────────────────────────────────────────────────
#  DATA  (yfinance)
# ─────────────────────────────────────────────────────────

TIMEFRAMES = {
    "15m": ("15m","5d"),
    "30m": ("30m","10d"),
    "1h":  ("1h","30d"),
    "4h":  ("4h","60d"),
}

def get_data(interval, period):
    try:
        import yfinance as yf
        df = yf.Ticker("GC=F").history(interval=interval, period=period, auto_adjust=True)
        if df is None or df.empty: return None
        df.columns = [c.lower() for c in df.columns]
        if "volume" not in df.columns: df["volume"]=0
        df = df[["open","high","low","close","volume"]].dropna()
        return df
    except Exception as e:
        logger.error(f"yfinance error {interval}: {e}")
        return None

def load_mtf():
    result = {}
    for tf,(iv,per) in TIMEFRAMES.items():
        df = get_data(iv, per)
        if df is not None and len(df)>=50:
            result[tf] = df
    return result

def get_price():
    try:
        import yfinance as yf
        df = yf.Ticker("GC=F").history(period="1d",interval="1m",auto_adjust=True)
        if df is not None and not df.empty:
            p = float(df["Close"].iloc[-1])
            return p, p+0.30
    except: pass
    return 0.0, 0.0


# ─────────────────────────────────────────────────────────
#  SIGNAL GENERATION
# ─────────────────────────────────────────────────────────

TF_WEIGHTS = {"15m":0.10,"30m":0.20,"1h":0.30,"4h":0.40}
MIN_SCORE  = 55
ATR_SL     = 1.3
ATR_TP     = 2.6

def get_session():
    h = datetime.now(timezone.utc).hour
    wd = datetime.now(timezone.utc).weekday()
    if wd >= 5: return None, "weekend"
    if 7<=h<12: return True, "london"
    if 13<=h<17: return True, "new_york"
    if 5<=h<7:  return True, "asian_end"
    if 3<=h<5:  return True, "asian_early"
    return False, f"off-session ({h}:00 UTC)"

def get_mtf_bias(tf_data):
    bull_w = bear_w = total_w = 0
    detail = {}
    for tf,df in tf_data.items():
        if df is None or len(df)<60: continue
        w = TF_WEIGHTS.get(tf,0.25)
        d = add_indicators(df)
        e20,e50,e100 = d.ema20.iloc[-1],d.ema50.iloc[-1],d.ema100.iloc[-1]
        macd,msig = d.macd.iloc[-1],d.macd_sig.iloc[-1]
        c = d.close.iloc[-1]
        if e20>e50>e100 and c>e20 and macd>msig:
            bull_w+=w; detail[tf]="↑ bull"
        elif e20<e50<e100 and c<e20 and macd<msig:
            bear_w+=w; detail[tf]="↓ bear"
        else:
            detail[tf]="→ neutral"
        total_w+=w
    if total_w==0: return "neutral",0,detail
    bn,brn = bull_w/total_w, bear_w/total_w
    if bn>=0.4: return "buy",bn,detail
    if brn>=0.4: return "sell",brn,detail
    return "neutral",max(bn,brn),detail

def score_signal(direction, df, mtf_str, regime, dxy_bias):
    score = 0; reasons = []
    last = df.iloc[-1]
    rsi,macd,msig = last.rsi,last.macd,last.macd_sig
    adx,sk,sd = last.adx,last.stoch_k,last.stoch_d
    c,bbu,bblo = last.close,last.bb_up,last.bb_lo

    pts = int(mtf_str*30); score+=pts; reasons.append(f"MTF alignment +{pts}")

    if direction=="buy":
        if rsi<42:
            p=int((42-rsi)/42*20); score+=p; reasons.append(f"RSI oversold {rsi:.1f} +{p}")
        if macd>msig:
            p=min(int(abs(macd-msig)/0.05*10),15); score+=p; reasons.append(f"MACD bullish +{p}")
        if sk<25 and sk>sd: score+=10; reasons.append("StochRSI crossup +10")
        elif sk<40: score+=5; reasons.append("StochRSI low +5")
        if c<bblo: score+=10; reasons.append("Below BB lower +10")
        elif c<last.bb_mid: score+=5; reasons.append("Below BB mid +5")
        if dxy_bias == "bearish_dxy":
            score += 10; reasons.append("DXY falling — bullish gold +10")
        elif dxy_bias == "bullish_dxy":
            score -= 8; reasons.append("DXY rising — bearish gold -8")
    else:
        if rsi>58:
            p=int((rsi-58)/(100-58)*20); score+=p; reasons.append(f"RSI overbought {rsi:.1f} +{p}")
        if macd<msig:
            p=min(int(abs(macd-msig)/0.05*10),15); score+=p; reasons.append(f"MACD bearish +{p}")
        if sk>75 and sk<sd: score+=10; reasons.append("StochRSI crossdown +10")
        elif sk>60: score+=5; reasons.append("StochRSI high +5")
        if c>bbu: score+=10; reasons.append("Above BB upper +10")
        elif c>last.bb_mid: score+=5; reasons.append("Above BB mid +5")
        if dxy_bias == "bullish_dxy":
            score += 10; reasons.append("DXY rising — bearish gold +10")
        elif dxy_bias == "bearish_dxy":
            score -= 8; reasons.append("DXY falling — bullish gold -8")

    vol_ratio = float(last.vol_ratio) if "vol_ratio" in df.columns else 1.0
    if vol_ratio > 1.5:
        score += 10; reasons.append(f"High volume +10")
    elif vol_ratio > 1.2:
        score += 5; reasons.append(f"Above avg volume +5")
    elif vol_ratio < 0.7:
        score -= 5; reasons.append(f"Low volume -5")

    pattern, pat_bonus = detect_candle_pattern(df)
    if pattern and pat_bonus > 0:
        if direction=="buy" and "bullish" in pattern:
            score += pat_bonus; reasons.append(f"{pattern} +{pat_bonus}")
        elif direction=="sell" and "bearish" in pattern:
            score += pat_bonus; reasons.append(f"{pattern} +{pat_bonus}")
        elif pattern == "inside_bar":
            score += pat_bonus; reasons.append(f"inside_bar +{pat_bonus}")

    if adx>22:
        p=min(int((adx-22)/30*15),15); score+=p; reasons.append(f"ADX {adx:.1f} +{p}")

    if "trending_bull" in regime and direction=="buy": score+=5; reasons.append("Regime bull +5")
    elif "trending_bear" in regime and direction=="sell": score+=5; reasons.append("Regime bear +5")
    elif regime=="ranging": score-=8; reasons.append("Ranging -8")

    levels = calc_sr_levels(df)
    sr_level, sr_above, sr_bonus = get_nearest_sr(float(last.close), levels, float(last.atr))
    if sr_bonus > 0:
        if direction=="buy" and not sr_above:
            score += sr_bonus; reasons.append(f"Near support +{sr_bonus}")
        elif direction=="sell" and sr_above:
            score += sr_bonus; reasons.append(f"Near resistance +{sr_bonus}")

    return max(0,min(100,score)), reasons

def generate_signal(tf_data):
    in_session, session_name = get_session()
    if not in_session:
        add_log(f"— No signal: {session_name}")
        return None

    is_risky, risk_reason = check_high_impact_news()
    if is_risky:
        add_log(f"— No signal: {risk_reason}")
        return None

    # ── Risk protection check
    can_trade, risk_reason = check_risk_limits()
    if not can_trade:
        add_log(f"🛡 Risk limit: {risk_reason}")
        return None

    df = tf_data.get("1h")
    if df is None:
        keys = list(tf_data.keys())
        df = tf_data.get(keys[-1]) if keys else None
    if df is None or len(df)<100: return None

    df = add_indicators(df)

    bias, mtf_str, mtf_detail = get_mtf_bias(tf_data)
    if bias=="neutral":
        add_log("— No signal: neutral MTF")
        return None

    regime, reg_str = get_regime(df)
    if regime=="ranging" and reg_str>80:
        add_log(f"— No signal: strong ranging ({reg_str:.0f})")
        return None

    last = df.iloc[-1]
    rsi = last.rsi
    if bias=="buy" and rsi>72: add_log(f"— No signal: RSI {rsi:.1f} too high"); return None
    if bias=="sell" and rsi<28: add_log(f"— No signal: RSI {rsi:.1f} too low"); return None

    dxy_bias = get_dxy_bias()
    if dxy_bias != "neutral_dxy":
        add_log(f"📊 DXY: {dxy_bias}")

    score, reasons = score_signal(bias, df, mtf_str, regime, dxy_bias)
    if score < MIN_SCORE:
        add_log(f"— No signal: score {score} < {MIN_SCORE}")
        return None

    atr   = float(last.atr)
    price = float(last.close)
    sl    = round(price - atr*ATR_SL if bias=="buy" else price + atr*ATR_SL, 2)
    tp    = round(price + atr*ATR_TP if bias=="buy" else price - atr*ATR_TP, 2)
    rr    = round(abs(tp-price)/abs(sl-price), 2)

    return {
        "direction":    bias,
        "entry":        round(price,2),
        "sl":           sl,
        "tp":           tp,
        "rr":           rr,
        "atr":          round(atr,2),
        "score":        score,
        "score_reasons": reasons,
        "regime":       regime,
        "session":      session_name,
        "rsi":          round(float(rsi),1),
        "macd":         round(float(last.macd),4),
        "adx":          round(float(last.adx),1),
        "smc_bonus":    0,
        "mtf_detail":   mtf_detail,
        "dxy_bias":     dxy_bias,
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────
#  TRADE MANAGEMENT
# ─────────────────────────────────────────────────────────

RISK_PER_TRADE = 1.0

def check_signal_results():
    try:
        signals = sb_select("signals", "executed=eq.false&order=created_at.desc&limit=20")
        for sig in signals:
            created = datetime.fromisoformat(sig["created_at"].replace("Z","+00:00"))
            age_hours = (datetime.now(timezone.utc) - created).total_seconds() / 3600
            if age_hours < 1:
                continue

            entry     = float(sig.get("entry", 0))
            tp        = float(sig.get("tp", 0))
            sl        = float(sig.get("sl", 0))
            atr       = float(sig.get("atr", 5.0))
            direction = sig.get("direction", "buy")
            sig_id    = sig.get("id")

            prices = sb_select("bot_state", "id=eq.1")
            if not prices: continue
            current = float(prices[0].get("price", 0))
            if current == 0: continue

            # Breakeven loogika
            breakeven = sig.get("breakeven", False)
            if not breakeven:
                if direction == "buy" and current >= entry + atr:
                    sb_upsert("signals", {"id": sig_id, "breakeven": True, "sl": entry})
                    add_log(f"🔒 Breakeven: BUY {entry} → SL = entry")
                    send_telegram(f"🔒 <b>Breakeven aktiveeritud</b>\nBUY @ {entry} — SL liigutati entry peale")
                    continue
                elif direction == "sell" and current <= entry - atr:
                    sb_upsert("signals", {"id": sig_id, "breakeven": True, "sl": entry})
                    add_log(f"🔒 Breakeven: SELL {entry} → SL = entry")
                    send_telegram(f"🔒 <b>Breakeven aktiveeritud</b>\nSELL @ {entry} — SL liigutati entry peale")
                    continue

            effective_sl = entry if breakeven else sl

            if direction == "buy":
                result = "TP" if current >= tp else "SL" if current <= effective_sl else None
                pnl_pts = abs(tp-entry) if result=="TP" else -abs(effective_sl-entry) if result=="SL" else None
            else:
                result = "TP" if current <= tp else "SL" if current >= effective_sl else None
                pnl_pts = abs(entry-tp) if result=="TP" else -abs(entry-effective_sl) if result=="SL" else None

            if result:
                balance = get_account_balance()
                lot     = float(sig.get("lot", 0.01))
                pnl_eur = round(pnl_pts * lot * 100, 2)

                sb_upsert("trades", {
                    "signal_id": sig_id,
                    "direction": direction,
                    "entry":     entry,
                    "sl":        effective_sl,
                    "tp":        tp,
                    "lot":       lot,
                    "result":    result,
                    "pnl":       pnl_eur,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                })
                sb_upsert("signals", {"id": sig_id, "executed": True})

                new_balance = round(balance + pnl_eur, 2)
                sb_upsert("bot_state", {"id": 1, "balance": new_balance})

                # Uuenda risk state
                update_risk_after_trade(pnl_eur)

                add_log(f"📊 Trade closed: {result}  PnL: {pnl_eur:+.2f}€  Balance: {new_balance:.2f}€")
                send_telegram(
                    f"{'✅' if result=='TP' else '❌'} <b>Tehing suletud: {result}</b>\n"
                    f"{'BUY' if direction=='buy' else 'SELL'} @ {entry}\n"
                    f"PnL: <b>{pnl_eur:+.2f}€</b>  |  Balance: <b>{new_balance:.2f}€</b>"
                )
    except Exception as e:
        logger.error(f"check_signal_results error: {e}")

def get_stats_from_supabase():
    trades = sb_select("trades","result=not.is.null&order=created_at.desc&limit=100")
    if not trades: return {"total":0}
    wins   = [t for t in trades if t.get("result")=="TP"]
    pnls   = [float(t.get("pnl",0) or 0) for t in trades]
    gp     = sum(p for p in pnls if p>0)
    gl     = abs(sum(p for p in pnls if p<0))
    return {
        "total":         len(trades),
        "wins":          len(wins),
        "win_rate":      round(len(wins)/len(trades)*100,1),
        "profit_factor": round(gp/gl,2) if gl>0 else 0,
        "net_pnl":       round(sum(pnls),2),
    }

def calc_lot(entry, sl, score):
    balance  = get_account_balance()
    risk_pct = RISK_PER_TRADE / 100
    factor   = 1.0 + 0.3 * max(0, (score - MIN_SCORE)) / (100 - MIN_SCORE)
    risk_amt = balance * risk_pct * factor
    sl_dist  = abs(entry - sl)
    if sl_dist == 0: return 0.01
    lot = risk_amt / (sl_dist * 100)
    return round(max(0.01, min(0.5, lot)), 2)


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

def format_signal_msg(sig, lot):
    d = sig["direction"]
    e = "🟢" if d=="buy" else "🔴"
    bar = "█"*(sig["score"]//10) + "░"*(10-sig["score"]//10)
    mtf = "\n".join(f"  {tf}: {v}" for tf,v in sig.get("mtf_detail",{}).items())
    dxy = sig.get("dxy_bias","neutral_dxy").replace("_dxy","").upper()
    balance  = get_account_balance()
    risk_eur = round(balance * RISK_PER_TRADE / 100, 2)
    risk_state = get_risk_state()
    streak   = risk_state.get("loss_streak", 0)
    daily_loss = abs(float(risk_state.get("daily_loss", 0)))
    return (
        f"{e} <b>NEMSIS v2 — XAUUSD {'📈 BUY' if d=='buy' else '📉 SELL'}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Entry: <b>{sig['entry']}</b>\n"
        f"🛑 SL: <b>{sig['sl']}</b>\n"
        f"🎯 TP: <b>{sig['tp']}</b>\n"
        f"⚖️ R:R: <b>1:{sig['rr']}</b>  |  Lot: <b>{lot}</b>\n"
        f"💼 Balance: <b>{balance:.2f}€</b>  |  Risk: <b>{risk_eur:.2f}€</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Score: <b>{sig['score']}/100</b> [{bar}]\n"
        f"🔎 RSI:{sig['rsi']}  ADX:{sig['adx']}  ATR:{sig['atr']}\n"
        f"💵 DXY: <b>{dxy}</b>\n"
        f"🌍 {sig['regime']} · {sig['session']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🛡 Streak: {streak}/{MAX_LOSS_STREAK}  |  Daily loss: {daily_loss:.2f}€/{round(_BALANCE_DEFAULT*MAX_DAILY_LOSS_PCT/100,2)}€\n"
        f"📐 MTF:\n{mtf}"
    )


# ─────────────────────────────────────────────────────────
#  MARKET ANALYSIS
# ─────────────────────────────────────────────────────────

def fetch_gold_news():
    try:
        url = f"https://gnews.io/api/v4/search?q=gold+XAUUSD+price&lang=en&max=6&token={GNEWS_KEY}"
        r = requests.get(url, timeout=15)
        data = r.json()
        articles = data.get("articles", [])
        if not articles:
            return [], ""
        bull_kw = ["rise","rally","surge","gain","jump","high","bullish","strong","increase","support"]
        bear_kw = ["fall","drop","decline","crash","low","bearish","weak","decrease","pressure","sell"]
        news_out = []
        headlines = []
        for a in articles[:6]:
            t = (a.get("title","") + " " + a.get("description","")).lower()
            bs = sum(1 for k in bull_kw if k in t)
            brs = sum(1 for k in bear_kw if k in t)
            s = "bull" if bs > brs else "bear" if brs > bs else "neutral"
            mins = int((datetime.now(timezone.utc) - datetime.fromisoformat(a["publishedAt"].replace("Z","+00:00"))).total_seconds() / 60)
            news_out.append({"title": a.get("title",""), "sentiment": s, "mins_ago": mins, "url": a.get("url","")})
            headlines.append(a.get("title",""))
        return news_out, "\n".join(headlines[:4])
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        return [], ""


def run_ai_analysis(headlines, tf_data=None):
    if not CLAUDE_KEY:
        logger.warning("CLAUDE_KEY not set — skipping AI analysis")
        return None
    try:
        heatmap = {}
        if tf_data:
            for tf, df in tf_data.items():
                if df is None or len(df) < 50: continue
                d = add_indicators(df)
                last = d.iloc[-1]
                rsi = float(last.rsi)
                macd = float(last.macd)
                msig = float(last.macd_sig)
                ema20 = float(last.ema20)
                ema50 = float(last.ema50)
                adx = float(last.adx)
                stoch = float(last.stoch_k) if hasattr(last, "stoch_k") else 50.0
                bb_pos = float((last.close - last.bb_lo) / (last.bb_up - last.bb_lo + 0.001) * 100)
                def cell_class(v, typ):
                    if typ == "rsi":
                        if v < 35: return "sb"
                        if v < 45: return "b"
                        if v > 65: return "sbr"
                        if v > 55: return "br"
                        return "n"
                    if typ == "bool": return "b" if v else "br"
                    if typ == "adx":
                        if v > 35: return "sb"
                        if v > 22: return "b"
                        return "n"
                    if typ == "bb":
                        if v < 20: return "b"
                        if v > 80: return "br"
                        return "n"
                    if typ == "stoch":
                        if v < 25: return "b"
                        if v > 75: return "br"
                        return "n"
                    return "n"
                heatmap[tf] = {
                    "RSI":   cell_class(rsi, "rsi"),
                    "MACD":  cell_class(macd > msig, "bool"),
                    "EMA":   cell_class(ema20 > ema50, "bool"),
                    "ADX":   cell_class(adx, "adx"),
                    "BB":    cell_class(bb_pos, "bb"),
                    "STOCH": cell_class(stoch, "stoch"),
                }
        bull_c = sum(1 for tf in heatmap.values() for v in tf.values() if v in ("sb","b"))
        bear_c = sum(1 for tf in heatmap.values() for v in tf.values() if v in ("sbr","br"))
        total  = bull_c + bear_c + 1
        bull_pct = round(bull_c / total * 100)
        bear_pct = round(bear_c / total * 100)
        prompt = f"""You are an elite XAUUSD gold trader. Analyze this market data and give a brief outlook.

Recent gold news:
{headlines or "No recent news available"}

Technical indicators summary:
Bull signals: {bull_c}, Bear signals: {bear_c}
Overall bias: {"bullish" if bull_c > bear_c else "bearish" if bear_c > bull_c else "neutral"}

Respond ONLY in this JSON format, nothing else:
{{"verdict":"BULLISH","confidence":75,"summary":"2 concise sentences about current gold outlook.","key_factor":"main driver in 4 words"}}"""

        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json", "x-api-key": CLAUDE_KEY, "anthropic-version": "2023-06-01"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": 200, "messages": [{"role": "user", "content": prompt}]},
            timeout=20
        )
        data = resp.json()
        text = data.get("content",[])[0].get("text","") if data.get("content") else ""
        try:
            analysis = json.loads(text.replace("","").strip())
        except Exception:
            analysis = {"verdict": "NEUTRAL", "confidence": 50, "summary": text[:200] or "Analysis unavailable.", "key_factor": "No data"}
        analysis["bull_pct"]     = bull_pct
        analysis["bear_pct"]     = bear_pct
        analysis["heatmap_data"] = heatmap
        return analysis
    except Exception as e:
        logger.error(f"AI analysis error: {e}")
        return None


def run_market_analysis(tf_data=None):
    global _last_analysis
    now = time.time()
    if now - _last_analysis < ANALYSIS_INTERVAL:
        return
    add_log("📰 Running market analysis...")
    news, headlines = fetch_gold_news()
    analysis = run_ai_analysis(headlines, tf_data)
    if analysis is None:
        heatmap = {}
        if tf_data:
            for tf, df in tf_data.items():
                if df is None or len(df) < 50: continue
                d = add_indicators(df)
                last = d.iloc[-1]
                rsi = float(last.rsi)
                macd = float(last.macd)
                msig = float(last.macd_sig)
                ema20 = float(last.ema20)
                ema50 = float(last.ema50)
                adx = float(last.adx)
                stoch = float(last.stoch_k) if "stoch_k" in d.columns else 50.0
                bb_pos = float((last.close - last.bb_lo) / (last.bb_up - last.bb_lo + 0.001) * 100)
                def cc(v, t):
                    if t=="rsi": return "sb" if v<35 else "b" if v<45 else "sbr" if v>65 else "br" if v>55 else "n"
                    if t=="bool": return "b" if v else "br"
                    if t=="adx": return "sb" if v>35 else "b" if v>22 else "n"
                    if t=="bb": return "b" if v<20 else "br" if v>80 else "n"
                    if t=="stoch": return "b" if v<25 else "br" if v>75 else "n"
                    return "n"
                heatmap[tf] = {"RSI": cc(rsi,"rsi"), "MACD": cc(macd>msig,"bool"), "EMA": cc(ema20>ema50,"bool"), "ADX": cc(adx,"adx"), "BB": cc(bb_pos,"bb"), "STOCH": cc(stoch,"stoch")}
        bull_c = sum(1 for tf in heatmap.values() for v in tf.values() if v in ("sb","b"))
        bear_c = sum(1 for tf in heatmap.values() for v in tf.values() if v in ("sbr","br"))
        total = bull_c + bear_c + 1
        analysis = {"verdict": "NEUTRAL", "confidence": 50,
                    "summary": "AI analysis unavailable — set CLAUDE_KEY in Railway Variables.",
                    "key_factor": "No API key",
                    "bull_pct": round(bull_c/total*100),
                    "bear_pct": round(bear_c/total*100),
                    "heatmap_data": heatmap}
    sb_upsert("market_analysis", {
        "id":           1,
        "updated_at":   datetime.now(timezone.utc).isoformat(),
        "verdict":      analysis.get("verdict", "NEUTRAL"),
        "confidence":   analysis.get("confidence", 50),
        "summary":      analysis.get("summary", ""),
        "key_factor":   analysis.get("key_factor", ""),
        "bull_pct":     analysis.get("bull_pct", 50),
        "bear_pct":     analysis.get("bear_pct", 50),
        "heatmap_data": analysis.get("heatmap_data", {}),
        "news":         news,
    })
    _last_analysis = now
    add_log(f"✅ Analysis: {analysis.get('verdict')} ({analysis.get('confidence')}% confidence)")


# ─────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────

def main():
    add_log("🚀 NEMSIS v2 Cloud Bot started")
    balance = get_account_balance()
    add_log(f"💼 Starting balance: {balance:.2f}€")
    add_log(f"🛡 Risk limits: daily={MAX_DAILY_LOSS_PCT}%  drawdown={MAX_DRAWDOWN_PCT}%  max_open={MAX_OPEN_SIGNALS}  streak={MAX_LOSS_STREAK}")
    send_telegram(
        f"🚀 <b>NEMSIS v2</b> — Cloud bot started\n"
        f"Signal-only mode | XAUUSD\n"
        f"💼 Balance: <b>{balance:.2f}€</b>\n"
        f"🛡 Daily loss limit: <b>{MAX_DAILY_LOSS_PCT}%</b>  |  Max drawdown: <b>{MAX_DRAWDOWN_PCT}%</b>"
    )

    rows = sb_select("bot_state", "id=eq.1&select=balance")
    if not rows or not rows[0].get("balance"):
        sb_upsert("bot_state", {"id": 1, "balance": balance})

    while True:
        try:
            add_log("⏱ Scanning...")

            bid, ask  = get_price()
            tf_data   = load_mtf()
            run_market_analysis(tf_data)
            check_signal_results()
            sig       = generate_signal(tf_data)
            stats     = get_stats_from_supabase()
            balance   = get_account_balance()
            risk_state = get_risk_state()

            drawdown_pct = round((1 - balance / _BALANCE_DEFAULT) * 100, 1) if balance < _BALANCE_DEFAULT else 0.0
            daily_loss   = abs(float(risk_state.get("daily_loss", 0)))
            loss_streak  = int(risk_state.get("loss_streak", 0))
            paused       = risk_state.get("paused_until") is not None

            risk = {
                "balance":        balance,
                "can_trade":      not paused and drawdown_pct < MAX_DRAWDOWN_PCT and (daily_loss / _BALANCE_DEFAULT * 100) < MAX_DAILY_LOSS_PCT,
                "daily_pnl":      stats.get("net_pnl", 0),
                "drawdown_pct":   drawdown_pct,
                "daily_loss_pct": round(daily_loss / _BALANCE_DEFAULT * 100, 1),
                "loss_streak":    loss_streak,
                "paused":         paused,
            }

            sb_upsert("bot_state", {
                "id":         1,
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "price":      round(bid,2),
                "spread":     round(ask-bid,2),
                "last_scan":  datetime.now(timezone.utc).strftime("%H:%M:%S UTC"),
                "scanning":   False,
                "risk":       risk,
                "stats":      stats,
                "log":        log_buffer[-20:],
            })

            if sig:
                lot = calc_lot(sig["entry"], sig["sl"], sig["score"])
                add_log(f"🔔 SIGNAL {sig['direction'].upper()} @ {sig['entry']}  score:{sig['score']}  lot:{lot}  balance:{balance:.2f}€")

                sb_insert("signals", {
                    "direction":     sig["direction"],
                    "entry":         sig["entry"],
                    "sl":            sig["sl"],
                    "tp":            sig["tp"],
                    "rr":            sig["rr"],
                    "score":         sig["score"],
                    "rsi":           sig["rsi"],
                    "adx":           sig["adx"],
                    "atr":           sig["atr"],
                    "lot":           lot,
                    "regime":        sig["regime"],
                    "session":       sig["session"],
                    "smc_bonus":     sig.get("smc_bonus", 0),
                    "mtf_detail":    sig.get("mtf_detail", {}),
                    "score_reasons": sig.get("score_reasons", []),
                    "executed":      False,
                    "breakeven":     False,
                })

                send_telegram(format_signal_msg(sig, lot))
            else:
                add_log("— No signal this cycle")

        except Exception as e:
            add_log(f"❌ Error: {e}")
            logger.exception(e)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
