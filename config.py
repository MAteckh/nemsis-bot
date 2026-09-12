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
        "enabled":      False,
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

    # ── STAATILINE grid TP/SL (12 Sept 2026) ─────────────────
    # Kui dynamic_tp_sl = False (praegune seis), kasutab grid FIKSEERITUD
    # TP/SL kaugust. Need olid varem koodi sisse kirjutatud literaalidena
    # kolmes kohas (main_v4.py order placement + send_grid_signals kutsed,
    # backtest.py simulaator), mistõttu ülalolevad tp_min/tp_max/sl_max
    # EI MÕJUTANUD gridi kuidagi — ma keerasin neid ja backtest andis
    # täpselt sama tulemuse, sest grid ei lugenud neid kunagi.
    #
    # Nüüd on nad siin ja config juhib päriselt.
    # VÄÄRTUSED ON TÄPSELT SAMAD, mis olid koodi sees => käitumine EI MUUTU.
    #
    # HOIATUS ENNE KEERAMIST: testisin 14 erinevat TP/SL suhet
    # (bot/run_grid_tpsl.py) ja KÕIK 14 sõid 200€ konto tühjaks.
    # Vastuoluliselt on "paremad" suhted HALVEMAD: TP 60 / SL 30 (vajab
    # ainult 33% võite) andis -812€, halvima tulemuse kogu testis, sest
    # laiem TP hoiab positsioone kauem lahti ja float_stop/trend_reset
    # tulevad tihedamini peale (tehinguid 289 -> 413).
    # Praegune 30/45 vajab 60% võite; ajalugu andis 62.6%.
    "grid_tp_usd":    30.0,
    "grid_sl_usd":    45.0,

    # ── trend_reset'i lüliti (12 Sept 2026) ──────────────────
    # trend_reset sulgeb KÕIK lahtised positsioonid TURUHINNAGA, kui trend
    # pöördub. Diagnoos (bot/run_grid_windows.py) näitas, et see + float_stop
    # on koos suurim kahjumi-allikas: viimasel 2 aastal võttis float_stop
    # -409€ (177 korda) ja trend_reset -210€ (17 korda), kokku -618€ — samal
    # ajal kui TP/SL tuum oli VÕIDUS (võiduprotsent 65.7%, vajalik 60.0%).
    # main_v4.py enda kommentaar real ~1129 nimetab trend_reset'i juba varem
    # "suurimaks üksikuks kahjumi-allikaks chop-turul".
    #
    # True  = praegune käitumine (sulge kõik trendipöördel)
    # False = jäta positsioonid lahti, las nad jõuavad oma TP/SL-ini.
    #         Grid ise re-tsentreeritakse ikka (see osa jääb tööle).
    #
    # VAIKIMISI True => käitumine EI MUUTU.
    # Matemaatika, mida kaaluda: trend_reset'i keskmine on -12.57$, SL on
    # -45$. Lahti jättes kaotavad kaotajad 3.5x rohkem, aga osa neist
    # muutub +30$ võitjaks. Tasuvuspiir on ~43% — kui üle 43% neist oleks
    # TP-ni jõudnud, on väljalülitamine parem. Seda testib
    # bot/run_grid_noprotect.py.
    "trend_reset_close": True,

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

    # ── Risk-põhine lot-suurus (10 Sept 2026) ───────────────
    # get_compound_lot() lot-põrand (0.01, madalaim lot_tiers aste) EI VÄHENE
    # kunagi, ükskõik kui palju kontot on kaotatud — balti/nädala circuit
    # breaker peatab UUE positsiooni avamise ajutiselt, aga ei vähenda riski
    # järgmisel korral, kui kauplemine jätkub. Reaalsel 2026 märts-august
    # XAUUSD andmestikul viis see korduva kaotusseeria korral konto
    # mitmekordse "ruumini" (drawdown >100%, mis reaalses kontos tähendaks
    # marginikõnet ammu enne seda). See lülitab riski % kontost tehingu
    # kohta (samamoodi nagu strategy_meanrev.py-l juba ammu on), nii et
    # lot väheneb koos balance'iga, mitte ei jää fikseerituks.
    # VAIKIMISI VÄLJAS, kuni backtest (bot/backtest.py) kinnitab.
    "risk_based_lot": False,
    "risk_pct":       0.015,
    "risk_lot_max":   0.5,

    # ── STRATEEGIA REŽIIM (11 Sept 2026) ────────────────────
    # "grid"         = vana trend-grid + scalp (see, mis seni live's jooksis)
    # "core_overlay" = tuumikpositsioon (osta ja hoia) + donchian väljamurde
    #                  ülekiht, mis võib minna mõlemale poole
    #
    # Miks: 7 aasta päevaandmetel (2020-2026, kulud sees, 200 EUR konto)
    #   ainult grid, praegused parameetrid ....  +61 EUR   drawdown -81%
    #   osta ja hoia ........................  +2840 EUR   drawdown -61%
    #   tuumik + donchian20 ülekiht .........  +4834 EUR   drawdown -70%
    # Live kinnitas grid'i numbrit: konto liikus 2 kuuga +2,35 EUR.
    #
    # AUSAD PIIRANGUD, mida peab teadma enne live'i lülitamist:
    #  - Tuumikut EI SULETA nädalavahetuseks (muidu pole see "hoidmine") —
    #    seega nädalavahetuse gap-risk on reaalne ja uus.
    #  - 2021 (kuld -6%) kaotasid MÕLEMAD jalad: tuumik -117, ülekiht -126.
    #    See ei ole langusekindel strateegia, vaid rohkem eksponeeringut.
    #  - Testitud päevabaaridel; live skaneerib tunnibaaridel.
    "strategy_mode": "grid",

    "core_enabled":   True,    # tuumikpositsioon sisse (ainult core_overlay režiimis)
    "core_lot":       0.01,
    "overlay_enabled": True,   # donchian ülekiht sisse
    "bo_lookback":    20,
    "bo_sl_atr":      1.5,
    "bo_tp_atr":      3.0,
    "overlay_max_pos": 1,

    # ── HAJUTATUD PORTFELL (11 Sept 2026) ───────────────────
    # Lülita sisse: portfolio_enabled = True. Töötab gold-režiimist SÕLTUMATULT
    # (võid jätta kulla grid'i käima või panna selle enabled=False).
    #
    # Miks need paarid: 42 instrument x strateegia kombinatsiooni testist
    # (2020-2026 päevaandmed, kulud sees) jäid alles need, mis olid kasumlikud
    # >=70% aastatest. Strateegia sobivus on INSTRUMENDIPÕHINE — mean reversion
    # on kullal selgelt kahjumlik (-1389), aga S&P 500-l parim (+1293).
    #
    # Jalgade omavaheline korrelatsioon on praktiliselt null (-0.02..+0.16),
    # mis annab portfellile drawdown -36.6% vs -63.0% sama kapitali puhul
    # ainult kullas. Kasumlik KÕIGIL 7 testitud aastal (ainus konfiguratsioon,
    # mis seda saavutas).
    "portfolio_enabled": True,
    "portfolio_risk_pct": 0.015,
    "portfolio_interval": "1d",     # testitud päevabaaridel — ära muuda ilma uue backtestita
    "portfolio_legs": [
        {"name": "XAUUSD", "symbol_candidates": ["XAUUSD"],
         "signal": "donchian", "params": {"lookback": 50}, "pip_value": 100.0},

        # ── SPX / USDJPY / EURUSD EEMALDATUD 12. sept 2026 ──────
        # Kasutaja otsus. Testitulemused, mille pealt see tehti
        # (bot/run_legs_exact.py, TÄPSELT need seaded, mis siin olid,
        #  200€ konto, lot 0.01, 10 aastat päevabaare):
        #
        #   jalg    signaal         teh    P&L     võit%  madalaim konto
        #   SPX     bollinger_fade  122 +1369.53€  54.9%   -45.46€ (!)
        #   USDJPY  donchian_trend   62  +156.24€  38.7%    94.60€
        #   EURUSD  ts_momentum_60   35  +136.50€  40.0%   165.80€
        #
        #   Poolte-test:
        #   SPX     +372.01€ -> +892.93€   läbib
        #   USDJPY   -77.40€ ->  +60.87€   EI läbi
        #   EURUSD    +7.20€ ->  +86.20€   läbib
        #
        # Miks nad siiski välja läksid:
        #  SPX     — teenis kõige rohkem, AGA konto läks -45.46€ ehk
        #            OTSA. Üks tehing = 53% riski 205€ kontost.
        #  USDJPY  — ei läbi poolte-testi, risk 16% tehingu kohta.
        #  EURUSD  — risk on ainus korralik (4.1%), aga serv on ÜKS AASTA:
        #            2023 üksi +125.40€ = 92% kogu 10 aasta kasumist,
        #            ilma 2023-ta +11.10€ üheksa aasta peale,
        #            5/10 positiivset aastat, 2026 praegu -55.40€.
        #
        # ⚠️ HOIATUS ALLESJÄÄNUD JALA KOHTA: XAUUSD on nelja hulgast
        # KÕIGE SUUREMA riskiga. Ühe miinimum-loti (0.01) SL = 2 x ATR
        # = ~139€, mis on 205€ kontol 68% — mitte portfolio_risk_pct
        # lubatud 1.5%. Põhjus: get_risk_based_lot arvutab õige loti,
        # aga see tuleb alla 0.01 ja tagastatakse miinimum.
        # Circuit breaker (-10% päevas) EI päästa, sest ta peatab ainult
        # UUED tehingud — avatud positsioon sõidab oma SL-ini.
        # Kaks kaotust järjest ≈ konto otsas.
        # Ajaloos käis see jalg 200€-lt 60.34€-ni (-70%).
    ],

    # ── Scalp-kihi parameetrid (10 Sept 2026) ───────────────
    # Toodud config'i, et neid saaks backtest.py's testida ilma koodi
    # muutmata (varem olid need hard-coded main_v4.py sees).
    "scalp_min_range": 20.0,
    "scalp_tp":         12.0,
    "scalp_sl":         25.0,
    "scalp_offset":      5.0,
}
