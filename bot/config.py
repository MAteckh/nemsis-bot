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
    # UUS (28 Aug 2026): astmeline lot-kasv (Design A stiilis), testitud
    # koos trailing SL strateegiaga. Kui see võti on olemas, kasutab
    # get_compound_lot() seda, mitte fikseeritud max_lot väärtust ülal.
    # (max_lot jääb alles kui fallback/dokumentatsioon, kui lot_tiers
    # eemaldataks tagasi.)
    "lot_tiers": [
        (200,  0.01),
        (400,  0.02),
        (800,  0.03),
        (1600, 0.05),
        (3200, 0.08),
        (6400, 0.13),
    ],
}

# UUS: trailing SL parameetrid (bot_trailing haru). Backtest 28 Aug 2026
# (kuludega, poolitusel robustne): €16,776 kahe aasta peale trail_start=15/
# trail_dist=10 kombinatsiooniga — kiirem trailing aktiveerumine kaitseb
# kasumit varem fake-out'ide vastu paremini kui laiem SL (vt /areas/nemsis.md).
TRAILING_CONFIG = {
    "initial_sl":  45.0,  # alg-SL kaugus positsiooni avamisel ($)
    "trail_start": 15.0,  # kasumi tase, millest trailing aktiveerub ($)
    "trail_dist":  10.0,  # SL kaugus parimast saavutatud hinnast pärast aktiveerumist ($)
}
