"""
NEMSIS v4 — Instrument Configuration
Kuld: trend grid | Forex: mean reversion
7 forex paari → 15min | NZDCAD → 1h | XAUUSD → 1h
"""

INSTRUMENTS = {
    "XAUUSD": {
        "strategy":     "grid",
        "lot":          0.01,
        "grid_size":    30.0,
        "trend_thresh": 3.0,
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
        "enabled":      True,
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
        "enabled":      True,
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
        "enabled":      True,
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
        "enabled":      True,
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
        "enabled":      True,
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
        "enabled":      True,
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
        "enabled":      True,
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
        "enabled":      True,
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
    }
}

# Grid parameetrid (kullale)
GRID_CONFIG = {
    "levels":      8,
    "max_float":   100.0,
    "trend_period": 50,
    "vol_thresh":  1.3,
    "vol_boost":   1.5,
}
