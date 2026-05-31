"""
NEMSIS v2 — Cloud Bot
Runs on Railway 24/7, pushes signals + state to Supabase.
"""

import sys, os, json, time, logging
from datetime import datetime, timezone
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
#  SUPABASE CLIENT  (raw REST, no extra library needed)
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
#  INDICATORS  (self-contained, no local imports needed)
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
    k = df.close.rolling(14).apply(lambda x:(x[-1]-x.min())/(x.max()-x.min()+1e-10)*100)
    df["stoch_k"] = k.rolling(3).mean()
    df["stoch_d"] = df["stoch_k"].rolling(3).mean()
    return df

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
MIN_SCORE  = 62
ATR_SL     = 1.3
ATR_TP     = 2.6

def get_session():
    from datetime import datetime, timezone
    h = datetime.now(timezone.utc).hour
    wd = datetime.now(timezone.utc).weekday()
    if wd >= 5: return None, "weekend"
    if 7<=h<12: return True, "london"
    if 13<=h<17: return True, "new_york"
    if 5<=h<7:  return True, "asian_end"
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
    if bn>=0.6: return "buy",bn,detail
    if brn>=0.6: return "sell",brn,detail
    return "neutral",max(bn,brn),detail

def score_signal(direction, df, mtf_str, regime):
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
    else:
        if rsi>58:
            p=int((rsi-58)/(100-58)*20); score+=p; reasons.append(f"RSI overbought {rsi:.1f} +{p}")
        if macd<msig:
            p=min(int(abs(macd-msig)/0.05*10),15); score+=p; reasons.append(f"MACD bearish +{p}")
        if sk>75 and sk<sd: score+=10; reasons.append("StochRSI crossdown +10")
        elif sk>60: score+=5; reasons.append("StochRSI high +5")
        if c>bbu: score+=10; reasons.append("Above BB upper +10")
        elif c>last.bb_mid: score+=5; reasons.append("Above BB mid +5")

    if adx>22:
        p=min(int((adx-22)/30*15),15); score+=p; reasons.append(f"ADX {adx:.1f} +{p}")

    if "trending_bull" in regime and direction=="buy": score+=5; reasons.append("Regime bull +5")
    elif "trending_bear" in regime and direction=="sell": score+=5; reasons.append("Regime bear +5")
    elif regime=="ranging": score-=8; reasons.append("Ranging -8")

    return max(0,min(100,score)), reasons

def generate_signal(tf_data):
    in_session, session_name = get_session()
    if not in_session:
        add_log(f"— No signal: {session_name}")
        return None

    df = tf_data.get("1h") or tf_data.get(list(tf_data.keys())[-1])
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
    if bias=="buy" and rsi>65: add_log(f"— No signal: RSI {rsi:.1f} too high"); return None
    if bias=="sell" and rsi<35: add_log(f"— No signal: RSI {rsi:.1f} too low"); return None

    score, reasons = score_signal(bias, df, mtf_str, regime)
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
        "timestamp":    datetime.now(timezone.utc).isoformat(),
    }


# ─────────────────────────────────────────────────────────
#  RISK STATE  (simple, stored in Supabase)
# ─────────────────────────────────────────────────────────

RISK_PER_TRADE = 1.0
ACCOUNT_BALANCE = float(os.environ.get("ACCOUNT_BALANCE","10000"))

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
    risk_pct = RISK_PER_TRADE/100
    factor   = 0.7 + 0.3*max(0,(score-MIN_SCORE))/(100-MIN_SCORE)
    risk_amt = ACCOUNT_BALANCE * risk_pct * factor
    sl_dist  = abs(entry-sl)
    if sl_dist==0: return 0.01
    return round(max(0.01,min(5.0, risk_amt/(sl_dist*100))),2)


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
    return (
        f"{e} <b>NEMSIS v2 — XAUUSD {'📈 BUY' if d=='buy' else '📉 SELL'}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 Entry: <b>{sig['entry']}</b>\n"
        f"🛑 SL: <b>{sig['sl']}</b>\n"
        f"🎯 TP: <b>{sig['tp']}</b>\n"
        f"⚖️ R:R: <b>1:{sig['rr']}</b>  |  Lot: <b>{lot}</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📊 Score: <b>{sig['score']}/100</b> [{bar}]\n"
        f"🔎 RSI:{sig['rsi']}  ADX:{sig['adx']}  ATR:{sig['atr']}\n"
        f"🌍 {sig['regime']} · {sig['session']}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📐 MTF:\n{mtf}"
    )



# ─────────────────────────────────────────────────────────
#  MARKET ANALYSIS (news + AI) — runs every 30 min
# ─────────────────────────────────────────────────────────

def fetch_gold_news():
    """Fetch latest gold news from GNews API."""
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
            news_out.append({
                "title": a.get("title",""),
                "sentiment": s,
                "mins_ago": mins,
                "url": a.get("url","")
            })
            headlines.append(a.get("title",""))
        
        return news_out, "\n".join(headlines[:4])
    except Exception as e:
        logger.error(f"News fetch error: {e}")
        return [], ""


def run_ai_analysis(headlines, tf_data=None):
    """Run Claude AI analysis on gold news headlines."""
    if not CLAUDE_KEY:
        logger.warning("CLAUDE_KEY not set — skipping AI analysis")
        return None
    
    try:
        # Build heatmap data from tf_data
        heatmap = {}
        if tf_data:
            for tf, df in tf_data.items():
                if df is None or len(df) < 50:
                    continue
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
        
        # Bull/bear count from heatmap
        bull_c = sum(1 for tf in heatmap.values() for v in tf.values() if v in ("sb","b"))
        bear_c = sum(1 for tf in heatmap.values() for v in tf.values() if v in ("sbr","br"))
        total  = bull_c + bear_c + 1
        bull_pct = round(bull_c / total * 100)
        bear_pct = round(bear_c / total * 100)
        
        # Claude API call
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
            headers={
                "Content-Type": "application/json",
                "x-api-key": CLAUDE_KEY,
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-haiku-4-5-20251001",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}]
            },
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
    """Fetch news + run AI analysis + push to Supabase."""
    global _last_analysis
    now = time.time()
    
    if now - _last_analysis < ANALYSIS_INTERVAL:
        return  # Not time yet
    
    add_log("📰 Running market analysis...")
    news, headlines = fetch_gold_news()
    analysis = run_ai_analysis(headlines, tf_data)
    
    if analysis is None:
        analysis = {"verdict": "NEUTRAL", "confidence": 50,
                    "summary": "AI analysis unavailable — set CLAUDE_KEY in Railway Variables.",
                    "key_factor": "No API key", "bull_pct": 50, "bear_pct": 50, "heatmap_data": {}}
    
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
    add_log(f"✅ Analysis: {analysis.get("verdict")} ({analysis.get("confidence")}% confidence)")

# ─────────────────────────────────────────────────────────
#  MAIN LOOP
# ─────────────────────────────────────────────────────────

def main():
    add_log("🚀 NEMSIS v2 Cloud Bot started")
    send_telegram("🚀 <b>NEMSIS v2</b> — Cloud bot started\nSignal-only mode | XAUUSD")

    while True:
        try:
            add_log("⏱ Scanning...")

            bid, ask = get_price()
            tf_data  = load_mtf()
            # Market analysis (news + AI) every 30 min
            run_market_analysis(tf_data)
            
            sig      = generate_signal(tf_data)
            stats    = get_stats_from_supabase()

            risk = {
                "balance":       ACCOUNT_BALANCE,
                "can_trade":     True,
                "daily_pnl":     0,
                "drawdown_pct":  0,
                "daily_loss_pct":0,
            }

            # Push state to Supabase
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
                add_log(f"🔔 SIGNAL {sig['direction'].upper()} @ {sig['entry']}  score:{sig['score']}  lot:{lot}")

                # Save signal to Supabase
                sb_insert("signals", {
                    "direction":    sig["direction"],
                    "entry":        sig["entry"],
                    "sl":           sig["sl"],
                    "tp":           sig["tp"],
                    "rr":           sig["rr"],
                    "score":        sig["score"],
                    "rsi":          sig["rsi"],
                    "adx":          sig["adx"],
                    "atr":          sig["atr"],
                    "regime":       sig["regime"],
                    "session":      sig["session"],
                    "smc_bonus":    sig.get("smc_bonus",0),
                    "mtf_detail":   sig.get("mtf_detail",{}),
                    "score_reasons":sig.get("score_reasons",[]),
                    "executed":     False,
                })

                # Telegram notification
                send_telegram(format_signal_msg(sig, lot))
            else:
                add_log("— No signal this cycle")

        except Exception as e:
            add_log(f"❌ Error: {e}")
            logger.exception(e)

        time.sleep(SCAN_INTERVAL)

if __name__ == "__main__":
    main()
