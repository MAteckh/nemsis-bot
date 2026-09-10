"""
NEMSIS v4 — Instrument Configuration
Kuld: trend grid | Forex: mean reversion
7 forex paari → 15min | NZDCAD → 1h | XAUUSD → 1h
"""

INSTRUMENTS = {
    "XAUUSD": {
        "strategy":     "grid",
        "lot":          0.01,
        "grid_size":    15.0,
        "trend_thresh": 0.3,
        "pip_value":    100,
        "symbol_td":    "XAU/USD",
        "interval":     "1h",
        "enabled":      True,
    },
    "AUDCAD": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "asia",
        "adx_filter":   False,
        "pip_value":    100000,
        "symbol_td":    "AUD/CAD",
        "interval":     "15min",
        "rsi_ob":     60,
        "rsi_os":     40,
        "enabled":      False,
    },
    "AUDNZD": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "all",
        "adx_filter":   True,
        "pip_value":    100000,
        "symbol_td":    "AUD/NZD",
        "interval":     "15min",
        "rsi_ob":     60,
        "rsi_os":     40,
        "enabled":      False,
    },
    "EURGBP": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "all",
        "adx_filter":   True,
        "pip_value":    100000,
        "symbol_td":    "EUR/GBP",
        "interval":     "15min",
        "rsi_ob":     60,
        "rsi_os":     40,
        "enabled":      False,
    },
    "EURCHF": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "asia",
        "adx_filter":   False,
        "pip_value":    100000,
        "symbol_td":    "EUR/CHF",
        "interval":     "15min",
        "rsi_ob":     72,
        "rsi_os":     28,
        "enabled":      False,
    },
    "NZDCAD": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "asia",
        "adx_filter":   False,
        "pip_value":    100000,
        "symbol_td":    "NZD/CAD",
        "interval":     "1h",
        "rsi_ob":     60,
        "rsi_os":     40,
        "enabled":      False,
    },
    "EURAUD": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "asia",
        "adx_filter":   False,
        "pip_value":    100000,
        "symbol_td":    "EUR/AUD",
        "interval":     "15min",
        "rsi_ob":     68,
        "rsi_os":     32,
        "enabled":      False,
    },
    "GBPCAD": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "all",
        "adx_filter":   True,
        "pip_value":    100000,
        "symbol_td":    "GBP/CAD",
        "interval":     "15min",
        "rsi_ob":     60,
        "rsi_os":     40,
        "enabled":      False,
    },
    "CADCHF": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "all",
        "adx_filter":   True,
        "pip_value":    100000,
        "symbol_td":    "CAD/CHF",
        "interval":     "15min",
        "rsi_ob":     60,
        "rsi_os":     40,
        "enabled":      False,
    },
    "EURNZD": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "all",
        "adx_filter":   True,
        "pip_value":    100000,
        "symbol_td":    "EUR/NZD",
        "interval":     "15min",
        "rsi_ob":       60,
        "rsi_os":       40,
        "enabled":      False,
    },
    "GBPNZD": {
        "strategy":     "meanrev",
        "lot":          0.01,
        "session":      "all",
        "adx_filter":   True,
        "pip_value":    100000,
        "symbol_td":    "GBP/NZD",
        "interval":     "15min",
        "rsi_ob":       60,
        "rsi_os":       40,
        "enabled":      False,
    },
}

# Mean reversion parameetrid
MEANREV_CONFIG = {
    "bb_period":  20,
    "bb_std":     2.0,
    "rsi_period": 14,
    "rsi_ob":     65,   # default (override per paar)
    "rsi_os":     35,   # default (override per paar)
    "adx_max":    23,
    "max_pos":    3,
    "master_sl":  0.08,
    # RSI per paar (override)
    "rsi_per_pair": {
        "AUDCAD": (60, 40),
        "EURAUD": (68, 32),
        "AUDNZD": (60, 40),
        "GBPCAD": (60, 40),
        "EURGBP": (60, 40),
        "CADCHF": (60, 40),
        "EURCHF": (72, 28),
        "NZDCAD": (60, 40),
        "EURNZD": (60, 40),
        "GBPNZD": (60, 40),
    }
}

# Grid parameetrid (kullale)
GRID_CONFIG = {
    "levels":      8,
    "max_float":   80.0,
    "trend_period": 10,
    "vol_thresh":  1.3,
    "vol_boost":   1.5,
    # Lot suuruse ülempiir compounding jaoks (get_compound_lot()). Varem
    # polnud piiri üldse — lot kasvas piiramatult balance/ACCOUNT_BALANCE
    # järgi, mis 19 Aug backtestis oli see, mis vanade parameetritega
    # (trend_thresh=0.1%) konto reaalselt tappis, mitte grid-loogika ise.
    "max_lot":     0.02,
    # Astmeline lot-kasv (Design A), merge'itud 21 Aug 2026 VPS main'ile
    # (commit b7634d9). Kui see võti on olemas, kasutab get_compound_lot()
    # seda, mitte fikseeritud max_lot väärtust ülal. See on PRAEGU LIVE
    # deployed konfiguratsioon reaalkontol 525854.
    "lot_tiers": [
        (200,  0.01),
        (400,  0.02),
        (800,  0.03),
        (1600, 0.05),
        (3200, 0.08),
        (6400, 0.13),
    ],

    # ── Uudiste filter (10 Sept 2026) ────────────────────────
    # Forex mean reversion strateegial oli Fed/NFP blackout juba ammu olemas,
    # gold grid'il seni üldse mitte — kuld reageerib dollari intressiotsustele
    # vähemalt sama tugevalt. Puhas riskimaandus, ei muuda signaali loogikat,
    # ainult ei ava UUSI positsioone teadaolevas kõrge-volatiilsuse aknas.
    "news_filter": True,

    # ── ATR-põhine adaptiivne TP/SL (10 Sept 2026) ───────────
    # calc_gold_tp_sl() eksisteeris main_v4.py-s juba varem, aga polnud
    # KUNAGI reaalselt kasutusel — order placement kasutas alati fikseeritud
    # $30 TP / $45 SL, sõltumata sellest, kas ATR oli $8 (vaikne turg) või
    # $35 (uudiste järgne volatiilsus). VAIKIMISI VÄLJAS, kuni on testitud
    # päris ajaloolistel andmetel (vt bot/backtest.py) — see muudab reaalset
    # kauplemiskäitumist ja seda ei tohi lülitada sisse ilma backtestita.
    "dynamic_tp_sl":  False,
    "tp_atr_mult":    2.0,
    "tp_min":         30.0,
    "tp_max":         100.0,
    "sl_buffer":      10.0,
    "sl_max":         80.0,

    # ── ATR-põhine adaptiivne grid-samm (10 Sept 2026) ───────
    # Fikseeritud $15 samm on rahulikul turul liiga tihe (positsioonid
    # koonduvad samasse liikumisse = korreleeritud risk) ja kiirel turul
    # liiga lai. VAIKIMISI VÄLJAS samal põhjusel kui eespool — muudab
    # kauplemissagedust/riski otseselt, vajab backtest-kinnitust enne live'i.
    "dynamic_grid_size": False,
    "grid_atr_mult":     0.75,
    "grid_size_min":     10.0,
    "grid_size_max":     30.0,

    # ── ADX choppiness-filter (10 Sept 2026) ─────────────────
    # Backtest (bot/backtest.py) näitas, et suurim üksik kahjumi-allikas
    # on trend_reset — grid avatakse ühes suunas, hind keerab kohe ümber,
    # positsioon suletakse kahjumis, uus grid avatakse vastassuunas, jne.
    # See on täpselt see, mida ADX mõõdab (trendi TUGEVUS, mitte suund) —
    # forex mean reversion strateegial on ADX-filter juba ammu kasutusel
    # (vastupidises suunas: ADX kõrge = ei kaubelda, sest see on
    # trend-strateegiale mean-reversion vaenulik). Kullale on loogika
    # vastupidine: trend-grid vajab PÄRIS trendi, mitte müra — seega
    # blokeeri uue grid'i avamine, kui ADX on liiga madal (chop).
    # VAIKIMISI VÄLJAS, kuni backtest päris ajalooliste andmetega kinnitab.
    "adx_filter": False,
    "adx_min":    20.0,
}
