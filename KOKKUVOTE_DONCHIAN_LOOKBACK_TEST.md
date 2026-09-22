===============================================================
BACKTEST: DONCHIAN LOOKBACK 50 (praegune live) VS 20 (luhem)
===============================================================
  AINULT TEST. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD.
  Test jooksis eraldi skriptina /tmp scratchpad'is, importis
  ainult olemasolevaid bot/gold_logic.py + bot/strategies.py
  funktsioone loetuna. git status naitab repos 0 muudatust.

---------------------------------------------------------------
SEADED (tapselt samad, mis config.py live's on)
---------------------------------------------------------------
  Instrument:        XAUUSD, paevabaar (portfolio_interval=1d)
  Signaal:            donchian breakout (sig_donchian)
  Konto:              214 EUR (praegune live balance)
  risk_pct:            1.5% (portfolio_risk_pct)
  SL-kova lagi:        45 EUR (portfolio_max_loss_eur)
  max lot:              0.5 (risk_lot_max)
  min lot:             0.01
  pip_value:            100
  Andmed:              Supabase market_bars, XAUUSD_d,
                        2016-09-12 .. 2026-09-11 (10 aastat,
                        2513 paevabaari)

  AINUS erinevus kahe testi vahel: lookback 50 vs 20 paeva.

---------------------------------------------------------------
TULEMUS — 10 AASTAT (2016-2026)
---------------------------------------------------------------
  naitaja                    lookback=50(LIVE)   lookback=20
  -------------------------  -----------------   -----------
  tehinguid kokku                    95                153
  netto P&L (EUR)                +2417.18           +2005.66
  tootlus algkapitalilt          +1129.5%            +937.2%
  voiduprotsent                     51.6%              41.8%
  max drawdown                      -38.6%             -69.2%
  madalaim konto (EUR)              212.40             159.86
  suurim uksik kahjum (EUR)         -45.00             -45.00
  suurim uksik voit (EUR)          +231.60            +231.60

---------------------------------------------------------------
TULEMUS — VIIMASED ~2 AASTAT (2024-08 .. 2026-09)
---------------------------------------------------------------
  naitaja                    lookback=50(LIVE)   lookback=20
  -------------------------  -----------------   -----------
  tehinguid                          28                 40
  netto P&L (EUR)                +1988.78           +1691.38

---------------------------------------------------------------
JARELDUS
---------------------------------------------------------------
  Luhem lookback (20) kauplebki tihedamini — 153 vs 95 tehingut
  10 aasta peale ehk ligi 1.6x rohkem, mis vastab tundele
  "peaks rohkem kauplema".

  AGA see EI OLE parem tulemus:
  - Madalam netokasum (+2005 vs +2417 EUR)
  - Madalam voiduprotsent (41.8% vs 51.6%)
  - OLULISELT sygavam drawdown (-69.2% vs -38.6%) — konto
    oleks kaigus ulatunud 160 EUR-ni (praeguselt 214 EUR-lt),
    peaaegu -25% miinuses, versus praeguse 50-paeva seadega
    -1% (212.40 EUR)

  See kinnitab varem raporteeritud mustrit (KOKKUVOTE_MASTER_
  EDGE_MAP.md): rohkem tehinguid selle strateegia peal EI
  tahenda rohkem raha — see toob rohkem valeväljamurdeid, mis
  soovad tihedamalt kahjumisse.

  95 tehingut 10 aasta peale = keskmiselt ~9.5 tehingut aastas
  ehk uks tehing iga ~5-6 nadala tagant. SEDA arvestades on
  11 vaikset paeva jarjest TAVAPARANE, mitte viga.

---------------------------------------------------------------
PIIRANGUD
---------------------------------------------------------------
  - Andmed lopevad 11.09.2026 (Supabase market_bars pole
    varskendatud) — viimased 11 paeva pole selles testis sees.
  - See test EI kasuta portfolio_max_open_total=1 (yks
    positsioon KOKKU portfellis) piirangut, sest praegu on
    portfellis ainult XAUUSD jalg niikuinii — piirang ei
    mojutaks tulemust.
  - Uudiste-blackout on sees, aga paevabaaril mojub see
    minimaalselt (mojutab pigem H1/M15 kaubeldavust).
  - See on AINULT strateegia enda simulatsioon — ei arvesta
    spread/komisjoni/swap kulusid (samamoodi nagu enamik
    varasemaid teste selles repos).
===============================================================
