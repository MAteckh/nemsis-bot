"""
gold_logic.py — Kulla (XAUUSD) strateegia PUHTAD funktsioonid.

Eraldatud main_v4.py-st, et neid saaks testida ilma MT5/Supabase/Telegram
sõltuvusteta (MetaTrader5 pakett töötab ainult Windowsil, mistõttu
main_v4.py ei ole Linuxil/Macil üldse importitav). backtest.py kasutab
täpselt samu funktsioone, mis päris botis jooksevad — nii ei saa
backtest ja reaalne kauplemine kunagi lahku minna.

Ei tee ise ühtegi võrgupäringut ega loe globaalset olekut.
"""
import numpy as np
import pandas as pd


def get_trend(df, period, thresh):
    """Trend % hinnamuutuse järgi `period` küünla peale tagasi."""
    if df is None or len(df) < period + 2:
        return "neutral"
    now = float(df["close"].iloc[-1])
    ago = float(df["close"].iloc[-period - 1])
    chg = (now - ago) / ago * 100
    if chg > thresh:
        return "bull"
    if chg < -thresh:
        return "bear"
    return "neutral"


def calc_atr(df, period=14):
    """True Range keskmine viimase `period` küünla peale. Puhas, globaalset olekut ei muuda."""
    if df is None or len(df) < period + 1:
        return 1.0
    hl = df["high"] - df["low"]
    hc = (df["high"] - df["close"].shift()).abs()
    lc = (df["low"] - df["close"].shift()).abs()
    tr = pd.concat([hl, hc, lc], axis=1).max(axis=1)
    return float(tr.tail(period).mean())


def get_vol_mult(atr_history, cfg):
    """Volatiilsuse kordaja — kui hetke ATR on tunduvalt üle 20-perioodi keskmise, boost'i lot."""
    if len(atr_history) < cfg["vol_thresh"]:
        return 1.0
    avg = sum(atr_history[-20:]) / min(len(atr_history), 20)
    cur = atr_history[-1]
    if avg == 0:
        return 1.0
    return cfg["vol_boost"] if cur > avg * cfg["vol_thresh"] else 1.0


def get_compound_lot(balance, account_balance, atr_history, cfg):
    """Astmeline (või fikseeritud) lot balance'i järgi + volatiilsuse boost."""
    vol_mult = get_vol_mult(atr_history, cfg)
    if "lot_tiers" in cfg:
        tier_lot = cfg["lot_tiers"][0][1]
        for threshold, l in cfg["lot_tiers"]:
            if balance >= threshold:
                tier_lot = l
        return round(tier_lot * vol_mult, 2)
    base = round(max(0.01, (balance / account_balance) * 0.01), 2)
    lot = round(base * vol_mult, 2)
    return min(lot, cfg["max_lot"])


def get_dynamic_grid_size(atr, cfg):
    """
    Grid-sammu skaleerimine ATR järgi — vaikimisi VÄLJAS (grid_cfg["dynamic_grid_size"]).
    Rahulikul turul on fikseeritud $15 samm liiga tihe (positsioonid koonduvad
    ühte ja samasse liikumisse = korreleeritud risk), kiirel turul liiga lai
    (jääb kasumlikest tagasitõmmetest ilma). Piiratud min/max vahemikuga, et
    grid ei saaks liiga hõre ega liiga tihe olla.
    """
    gs = atr * cfg.get("grid_atr_mult", 0.75)
    return round(max(cfg.get("grid_size_min", 10.0), min(cfg.get("grid_size_max", 30.0), gs)), 2)


def get_swing_levels(df, lookback=20):
    """Viimase `lookback` küünla swing low/high — struktuuripõhise SL jaoks."""
    try:
        if df is None or len(df) < lookback:
            return None, None
        recent = df.tail(lookback)
        return float(recent["low"].min()), float(recent["high"].max())
    except Exception:
        return None, None


def calc_gold_tp_sl(direction, level, atr, swing_low, swing_high, cfg):
    """
    ATR-põhine TP + swing-põhine SL (varem defineeritud main_v4.py-s, aga
    kunagi tegelikult kasutusele ei võetud — order placement kasutas alati
    fikseeritud $30/$45, ükskõik mis ATR parasjagu oli). Nüüd konfigureeritav
    ja pandud tegelikult käiku (grid_cfg["dynamic_tp_sl"]).

    TP = atr_tp_mult × ATR, piiratud [tp_min, tp_max] vahele
    SL = swing tase + puhver, piiratud sl_max kaugusega; kui swing pole
         kasutatav (puudub / vale suunas / liiga kaugel), fallback fikseeritud
         sl_max kaugusele.
    """
    tp_dist = max(cfg.get("tp_min", 30.0), min(cfg.get("tp_max", 100.0), cfg.get("tp_atr_mult", 2.0) * atr))
    sl_max = cfg.get("sl_max", 80.0)
    buf = cfg.get("sl_buffer", 10.0)

    if direction == "buy":
        tp = round(level + tp_dist, 2)
        if swing_low is not None and swing_low < level and (level - swing_low + buf) <= sl_max:
            sl = round(swing_low - buf, 2)
        else:
            sl = round(level - sl_max, 2)
    else:
        tp = round(level - tp_dist, 2)
        if swing_high is not None and swing_high > level and (swing_high - level + buf) <= sl_max:
            sl = round(swing_high + buf, 2)
        else:
            sl = round(level + sl_max, 2)
    return tp, sl


def calc_adx(highs, lows, closes, period=14):
    """
    Trendi tugevus (0-100). Sama valem, mis varem oli duplikaadina
    strategy_meanrev.py's — siia toodud, et gold grid saaks sedasama
    kasutada (backtest näitas: enamik kahjumit tuli trend_reset'idest
    trendituul turul, kus 3-scan kinnitus üksi ei filtreerinud müra välja).
    """
    if len(closes) < period * 2:
        return 50.0
    h = np.array(highs[-period * 2:])
    l = np.array(lows[-period * 2:])
    c = np.array(closes[-period * 2:])
    tr = np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))
    up = h[1:] - h[:-1]
    down = l[:-1] - l[1:]
    dmp = np.where((up > down) & (up > 0), up, 0.0)[-period:]
    dmm = np.where((down > up) & (down > 0), down, 0.0)[-period:]
    atr = tr[-period:].mean()
    if atr == 0:
        return 50.0
    dip = 100 * dmp.mean() / atr
    dim = 100 * dmm.mean() / atr
    if dip + dim == 0:
        return 50.0
    return 100 * abs(dip - dim) / (dip + dim)


def setup_grid(center, trend, grid_size, levels):
    p = {}
    if trend in ("bull", "neutral"):
        for i in range(1, levels + 1):
            p[str(round(center - i * grid_size, 2))] = "buy"
    if trend in ("bear", "neutral"):
        for i in range(1, levels + 1):
            p[str(round(center + i * grid_size, 2))] = "sell"
    return p


def is_news_blackout(now):
    """
    Uudiste-aken, mil uusi positsioone EI avata (olemasolevaid hallatakse
    endiselt). Sama loogika, mis strategy_meanrev.py's forexile juba
    kasutusel — kuld reageerib Fed'ile/NFP-le vähemalt sama tugevalt kui
    forex ristpaarid (dollari intress/reaaltootluse kanal), aga grid
    strateegial seni üldse uudiste-filtrit polnud.
    """
    if now.weekday() == 2 and 18 <= now.hour < 19:
        return True  # Fed rate decision (kolmapäev)
    if now.weekday() == 4 and now.day <= 7 and 12 <= now.hour < 14:
        return True  # NFP (kuu esimene reede)
    return False
