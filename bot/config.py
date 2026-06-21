"""
NEMSIS v4 — Instrument Configuration
Kuld: trend grid | Forex: mean reversion
"""

INSTRUMENTS = {
    "XAUUSD": {
        "strategy":   "grid",
        "lot":        0.01,
        "grid_size":  30.0,
        "trend_thresh": 3.0,
        "pip_value":  100,      # gold: $1 per pip per 0.01 lot
        "symbol_td":  "XAU/USD",
        "enabled":    True,
    },
    "AUDCAD": {
        "strategy":   "meanrev",
        "lot":        0.01,
        "session":    "asia",   # kaupleb ainult Aasia sessioonis
        "adx_filter": False,
        "pip_value":  100000,
        "symbol_td":  "AUD/CAD",
        "enabled":    True,
    },
    "AUDNZD": {
        "strategy":   "meanrev",
        "lot":        0.01,
        "session":    "all",
        "adx_filter": True,     # ADX < 23 filter
        "pip_value":  100000,
        "symbol_td":  "AUD/NZD",
        "enabled":    True,
    },
    "EURGBP": {
        "strategy":   "meanrev",
        "lot":        0.01,
        "session":    "all",
        "adx_filter": True,
        "pip_value":  100000,
        "symbol_td":  "EUR/GBP",
        "enabled":    True,
    },
    "EURCHF": {
        "strategy":   "meanrev",
        "lot":        0.01,
        "session":    "asia",
        "adx_filter": False,
        "pip_value":  100000,
        "symbol_td":  "EUR/CHF",
        "enabled":    True,
    },
    "NZDCAD": {
        "strategy":   "meanrev",
        "lot":        0.01,
        "session":    "asia",
        "adx_filter": False,
        "pip_value":  100000,
        "symbol_td":  "NZD/CAD",
        "enabled":    True,
    },
}

# Mean reversion parameetrid (kõigile forex paaridele)
MEANREV_CONFIG = {
    "bb_period":  20,
    "bb_std":     2.0,
    "rsi_period": 14,
    "rsi_ob":     65,   # overbought → sell
    "rsi_os":     35,   # oversold → buy
    "adx_max":    23,   # max ADX ranging jaoks
    "max_pos":    3,    # max positsioone per paar
    "master_sl":  0.08, # 8% master stop-loss
}

# Grid parameetrid (kullale)
GRID_CONFIG = {
    "levels":     8,
    "max_float":  100.0,
    "trend_period": 50,
    "vol_thresh": 1.3,
    "vol_boost":  1.5,
}
