"""
paar_config.py — PDF-i "Forex: paaripohised trading-strateegiad" punkt 3,
sisestatud MUUTMATA kujul.

Need EI OLE minu valitud parameetrid. Need on dokumendi hupoteesid.
Dokument ise utleb (punkt 3): "Need seadistused on stardihupoteesid,
mitte loplikud optimaalsed vaartused." Just sellepolikult ma siin midagi
ei "paranda" ega optimeeri — testin tapselt seda, mis kirjas on.

Kus dokument annab VAHEMIKU (nt SL ATR x 1.3-1.7), testime moLEMAID
otsi ja keskpunkti. Kus annab uhe vaartuse, kasutame seda.

REZIIMID:
  trend_pullback   — EMA joondus + ADX + tagasitomme + RSI kinnitus
  breakout_retest  — N-baari vahemiku murre + EMA suund + kinnitus
  mean_reversion   — madal ADX + BB aare + RSI aare
  regime_switch    — ADX otsustab, kumba ulal kahest kasutada

SESSIOONID on UTC-tundides (andmed on UTC):
  Tokyo   00-08     London 07-16     NY 13-21
  LN_NY   13-16 (kattuvus)
"""

# sessiooniaknad UTC-tundides (algus kaasa arvatud, lopp valja arvatud)
SESS = {
    "Tokyo":     (0, 8),
    "London":    (7, 16),
    "NY":        (13, 21),
    "London_NY": (7, 21),
    "LN_NY":     (13, 16),
    "Asia_LN":   (0, 16),
    "koik":      (0, 24),
}

PAARID = {
    # ── PDF lk 2 ────────────────────────────────────────────────
    "EURUSD": dict(
        rezim="trend_pullback", sess="London_NY",
        ema=(20, 50, 200), adx_min=(20, 22, 25),
        rsi_long=(45, 65), rsi_short=(35, 55),
        atr_sl=(1.3, 1.5, 1.7), tp_r=(1.8, 2.2, 2.5)),
    "GBPUSD": dict(
        rezim="breakout_retest", sess="LN_NY",
        ema=(20, 50, None), adx_min=(0,),
        murre_lb=20, retest=True,
        atr_sl=(1.5, 1.75, 2.0), tp_r=(2.0, 2.5, 3.0)),
    "USDJPY": dict(
        rezim="trend_pullback", sess="London_NY",
        ema=(20, 50, 200), adx_min=(22,),
        rsi_long=(52, 100), rsi_short=(0, 48),
        atr_sl=(1.5, 1.75, 2.0), tp_r=(2.0, 2.5, 3.0)),
    "AUDUSD": dict(
        rezim="regime_switch", sess="Asia_LN",
        ema=(20, 50, None), adx_madal=(18, 20), adx_korge=(22,),
        murre_lb=20,
        atr_sl_range=(1.2, 1.35, 1.5), atr_sl_murre=(1.5, 1.65, 1.8),
        tp_r=(1.5, 2.0, 2.5)),
    # ── PDF lk 3 ────────────────────────────────────────────────
    "NZDUSD": dict(
        rezim="trend_pullback", sess="Asia_LN",
        ema=(20, 50, None), adx_min=(20,),
        rsi_long=(45, 60), rsi_short=(40, 55),
        atr_sl=(1.4, 1.6, 1.8), tp_r=(2.0, 2.25, 2.5)),
    "USDCAD": dict(
        rezim="breakout_retest", sess="NY",
        ema=(20, 50, None), adx_min=(0,),
        murre_lb=20, retest=True, atr_ule_mediaani=True,
        atr_sl=(1.5, 1.75, 2.0), tp_r=(2.0, 2.5, 3.0)),
    "USDCHF": dict(
        rezim="mean_reversion", sess="koik",
        adx_max=(18, 20), bb=(20, 2.0),
        rsi_ost=30, rsi_muuk=70,
        atr_sl=(1.2, 1.35, 1.5), tp_r=(1.3, 1.65, 2.0)),
    "EURGBP": dict(
        rezim="regime_switch", sess="London",
        ema=(20, 50, None), adx_madal=(18, 20), adx_korge=(22,),
        murre_lb=20, bb=(20, 2.0),
        atr_sl_range=(1.1, 1.35, 1.6), atr_sl_murre=(1.1, 1.35, 1.6),
        tp_r=(1.5, 1.85, 2.2)),
    "EURJPY": dict(
        rezim="trend_pullback", sess="London_NY",
        ema=(20, 50, 200), adx_min=(22,),
        rsi_long=(50, 100), rsi_short=(0, 50),
        atr_sl=(1.5, 1.75, 2.0), tp_r=(2.0, 2.5, 3.0)),
    # ── PDF lk 4 ────────────────────────────────────────────────
    "GBPJPY": dict(
        rezim="breakout_retest", sess="koik",
        ema=(20, 50, None), adx_min=(25,),
        murre_lb=20, retest=True,
        atr_sl=(1.8, 2.05, 2.3), tp_r=(2.0, 2.5, 3.0)),
    "AUDJPY": dict(
        rezim="trend_pullback", sess="Asia_LN",
        ema=(20, 50, 200), adx_min=(22,),
        rsi_long=(50, 100), rsi_short=(0, 50),
        atr_sl=(1.5, 1.75, 2.0), tp_r=(2.0, 2.5, 3.0)),
    "EURCHF": dict(
        rezim="mean_reversion", sess="koik",
        adx_max=(18, 20), bb=(20, 2.0),
        rsi_ost=30, rsi_muuk=70,
        atr_sl=(1.0, 1.2, 1.4), tp_r=(1.2, 1.5, 1.8)),
    "EURAUD": dict(
        rezim="breakout_retest", sess="Asia_LN",
        ema=(50, 200, None), adx_min=(22,),
        murre_lb=20, retest=True,
        atr_sl=(1.6, 1.85, 2.1), tp_r=(2.0, 2.5, 3.0)),
    "GBPAUD": dict(
        rezim="breakout_retest", sess="koik",
        ema=(20, 50, None), adx_min=(25,),
        murre_lb=20, retest=True, atr_ule_mediaani=True,
        atr_sl=(1.8, 2.1, 2.4), tp_r=(2.0, 2.5, 3.0)),
    # ── PDF lk 5 ────────────────────────────────────────────────
    "AUDCAD": dict(
        rezim="regime_switch", sess="koik",
        ema=(20, 50, None), adx_madal=(20,), adx_korge=(22,),
        murre_lb=20,
        atr_sl_range=(1.3, 1.55, 1.8), atr_sl_murre=(1.3, 1.55, 1.8),
        tp_r=(1.5, 2.0, 2.5)),
}
