```
===============================================================================
NEMSIS HEAT MAP v1 — AUDIT
===============================================================================
  kuupaev 2026-09-15   haru claude/great-noether-um7382
  LIVE PUUTUMATA: main_v4.py, config.py, mt5_connector.py,
  strategy_meanrev.py, backtest.py EI OLE muudetud. /update EI saadetud.

===============================================================================
1. TAPSED ANDMED JA AJAVAHEMIKUD
===============================================================================

  H1  (bot/data/{PAAR}_h1.csv)  koik 15 paari
      2023-11-27 .. 2026-09-11   17 155 - 17 370 baari paari kohta
      = 2.79 aastat
  M15 (bot/data/{PAAR}_m15.csv) koik 15 paari
      2026-06-22 .. 2026-09-11   5 573 - 5 596 baari = 81 PAEVA
  D1  (bot/data/{PAAR}_d25.csv) 7 USD-paari otse
      EURUSD/GBPUSD/EURGBP/EURJPY/GBPJPY/EURCHF/NZDUSD  2003-12-01 ..
      USDCAD/USDCHF 2003-09-16 ..   USDJPY 2001-09-10 ..
      AUDUSD/AUDJPY/EURAUD/GBPAUD/AUDCAD 2006-05-15 ..  (AUDUSD piirab)
      koik kuni 2026-09-10/13, 5 271 - 6 491 baari

  KRIITILINE PIIRANG: soovitud jaotust TRAIN 2006-2013 EI OLE VOIMALIK
  taita 15-minutiliste ega tunniste andmetega — neid selles repos EI OLE
  ja Yahoo tunniandmed ulatuvad ~730 paeva tagasi. M15 (81 paeva) ei
  kanna uhtegi kolmeosalist jaotust.

  RISTIDE EHITUS D1-l: ristid, millel ei ole oma _d25 faili, arvutatakse
  USD-jalgadest XY = (X/USD)/(Y/USD) iga OHLC-valja kohta. High/low on
  seetottu LIGIKAUDSED (kahe seeria high'de jagatis ei ole risti tegelik
  high) => RADA B SL/TP tabamused on veidi optimistlikud. Seepargi on
  RADA A (paris H1 ristid) esitatud kui aus ajaraam ja RADA B kui aus
  ajalugu; kumbki uksi ei ole taielik.

  PUUDUVATE ANDMETE KASITLUS: paar, mille seeria on alla 500 baari,
  margitakse INSUFFICIENT DATA ja jaetakse valja. Uhtegi sellist ei olnud.
  NaN-idega baarid (indikaatorite soojendus) ei genereeri signaale.
  Andmeid EI TAIDETUD ega interpoleeritud.

===============================================================================
2. STRATEEGIAREEGLID (taielikud, reprodutseeritavad)
===============================================================================

  Kontekst-ajaraam annab suuna ja rezhiimi, sisenemis-ajaraam annab kaivitaja.
  RADA A: kontekst H4, sisenemine H1 (sama 1:4 suhe mis kusitud 1H:15m)
  RADA B: kontekst W1, sisenemine D1

  TREND_PULLBACK
    kontekst: EMA50 > EMA200 (pikk) voi < (luhike) JA ADX >= 25
    sisenemine: low <= EMA20 <= (pikk) JA close > EMA20 JA close > eelmine close
    peegelpilt luhikeseks

  BREAKOUT_RETEST
    20-baariline Donchian (shift(1), st eelmiste baaride max/min)
    close > hi20 => murre registreeritud, tase = hi20
    1..10 baari hiljem: low <= tase JA close > tase => pikk
    peegelpilt luhikeseks

  MEAN_REVERSION
    kontekst: ADX < 20 (AINULT range-rezhiim)
    sisenemine: close < Bollinger(20, 2.0) alumine JA RSI(14) < 30 => pikk
    close > ulemine JA RSI > 70 => luhike

  MOMENTUM
    kontekst: EMA50 > EMA200 (pikk) voi < (luhike)
    sisenemine: RSI(14) ristub ULES 55 (pikk) JA close > EMA20
    RSI ristub ALLA 45 (luhike) JA close < EMA20

  KOIGIL: SL = 1.5 x ATR(14) signaalibaaril
          TP = 2.0 R (MEAN_REVERSION 1.0 R, sest ta sihib keskmist)
          max hoid 48 baari (H1) / 20 baari (D1)
          uks positsioon korraga paari ja strateegia kohta

===============================================================================
3. REZHIIMIDEFINITSIOONID
===============================================================================

  Koik konteksti-ajaraamilt, EELMISELT LOPETATUD baarilt.

  HIGH_VOLATILITY  normaliseeritud ATR (ATR/close) >  oma 500-baarilise
                   rullmediaani
  LOW_VOLATILITY   normaliseeritud ATR <= rullmediaan
  TRENDING         ADX(14) >= 25
  RANGING          ADX(14) <  20

  HIGH/LOW on teineteist valistavad. TRENDING/RANGING samuti (ADX 20-25
  ei kuulu kumbagi). VOL- ja TREND-teljed KATTUVAD — tehing voib olla
  korraga HIGH_VOLATILITY ja TRENDING. Nii oli kusitud ja nii on ka
  raporteeritud; kattuvus on maaratud (A8: 3 942 baari EURUSD-l).

===============================================================================
4. PARAMEETRID
===============================================================================

  EMA 20 / 50 / 200        ADX 14, trend >= 25, range < 20
  ATR 14                   Bollinger 20 / 2.0
  RSI 14, 30/70, 45/55     Donchian 20, retest-aken 10
  SL 1.5 x ATR             TP 2.0 R (MR 1.0 R)
  max hoid 48 (H1) / 20 (D1)     risk 1% kapitalist tehingu kohta
  vol-rezhiimi aken 500 baari

  PARAMEETREID EI OPTIMEERITUD UHELGI PERIOODIL — ka mitte TRAIN-il.
  Need on tavaparased oppikirjanduse vaikevaartused. See on RANGEM kui
  "fitteeri TRAIN-il", sest nii ei saa TRAIN-i ulesobitada isegi kogemata.
  TRAIN-i kasutatakse AINULT vordlusaknana, mitte valikuks.

===============================================================================
5. KULUMUDEL
===============================================================================

  Alus: bot/h1engine.py KULU_RETAIL (uhesuunaline bp).
  Kolm risti puudusid originaalis ja lisati konservatiivselt sama skaala
  jargi: EURCHF 1.8, GBPAUD 2.2, AUDCAD 2.2.

  EURUSD 1.0  GBPUSD 1.2  USDJPY 1.0  AUDUSD 1.2  NZDUSD 1.8
  USDCAD 1.3  USDCHF 1.3  EURGBP 1.5  EURJPY 1.5  GBPJPY 1.8
  AUDJPY 1.8  EURCHF 1.8  EURAUD 1.8  GBPAUD 2.2  AUDCAD 2.2
  + libisemine 0.3 bp uhe suuna kohta

  kulu_R = 2 x (spread + slip) / 1e4 x sisenemishind / SL-kaugus

  MOODETUD TAGAJARG: H1-l on SL ~11 bp, seega kulu ~0.19 R TEHINGU KOHTA
  (19% riskiuhikust). D1-l on SL ~90-130 bp, seega kulu ~0.035 R.
  See on RADA A ja RADA B erinevuse peamine pohjus.

===============================================================================
6. TRAIN / VALIDATION / OOS
===============================================================================

  RADA B (D1) — TAPSELT nagu kusitud:
    TRAIN 2006-01-01 .. 2013-12-31
    VALID 2014-01-01 .. 2017-12-31
    OOS   2018-01-01 .. 2026-12-31

  RADA A (H1) — andmed katavad 2.79 aastat, seega kronoloogilised kolmandikud:
    TRAIN 2023-11-27 .. 2024-10-31
    VALID 2024-11-01 .. 2025-08-31
    OOS   2025-09-01 .. 2026-09-11

  OOS-i ei kasutatud uhegi valiku ega parameetri jaoks. Kuna parameetreid
  uldse ei otsitud, ei saanud OOS-i ka kaudselt lekkida.

===============================================================================
7. KOMBINATSIOONIDE ARV
===============================================================================

  15 paari x 4 strateegiat x 2 rada          = 120 paar-strateegia jooksu
  x (ALL + TRAIN + VALID + OOS)              = 480 pohilahtrit
  + OOS x 4 rezhiimi ja ALL x 4 rezhiimi     = kokku 1 319 tulemuserida
  tehinguid kokku                            = 27 604
    RADA A (H1) 21 315,  RADA B (D1) 6 289

===============================================================================
8. LOOKAHEAD-KAITSED (bot/hm_audit.py, 22 kontrolli, 0 viga)
===============================================================================

  A1 H1 andmed laetud                              17 268 baari         OK
  A1 koik 15 paari olemas H1-l                     puudu: -             OK
  A1 koik 15 paari olemas D1-l                     5271..6491 baari     OK
  A2 tousev seeria -> TP, bruto = +2.0 R           tapselt 2.000000     OK
  A2 langev seeria, pikk signaal -> SL = -1.0 R    tapselt -1.000000    OK
  A2 SL ja TP samas baaris -> loetakse SL          konservatiivne       OK
  A3 TREND_PULLBACK: tulevik ei muuda minevikku                         OK
  A3 BREAKOUT_RETEST: tulevik ei muuda minevikku                        OK
  A3 MEAN_REVERSION: tulevik ei muuda minevikku                         OK
  A3 MOMENTUM: tulevik ei muuda minevikku                               OK
  A4 sisenemine on ALATI jargmise baari AVAHIND    50 tehingut          OK
  A4 tehingud ei kattu (uks positsioon korraga)                         OK
  A4 valjumine ei ole kunagi enne sisenemist                            OK
  A5 kulumudel: 1.3bp / 11bp stopp = 0.23636 R                          OK
  A5 kulu on iga tehingu puhul positiivne          0.0415..0.3589 R     OK
  A6 kontekst kasutab EELMIST lopetatud baari      33.9352 = 33.9352    OK
  A7 stat: voiduprotsent = kasitsi arvutatu                             OK
  A7 stat: neto = bruto - kulu                                          OK
  A7 stat: maxdd <= 0                                                   OK
  A8 HIGH_VOL / LOW_VOL valistavad teineteist                           OK
  A8 TRENDING / RANGING valistavad teineteist                           OK
  A8 VOL- ja TREND-teljed kattuvad (nii kusitud)                        OK

  A3 test on koige tugevam: kogu seeria viimased 50 baari korrutati 3-ga
  ja koik varasemad signaalid jaid IDENTSEKS. Kui indikaator lekiks
  tulevikku, see test kukuks labi.

===============================================================================
9. MITME TESTIMISE KASITLUS
===============================================================================

  OOS-lahtreid, kus n >= 30: 92
  neist positiivse ootusega: 20
  Benjamini-Hochberg q=0.05: lavi p = 0.0146, "labis" 28 lahtrit —
  AGA neist 28-st on KOIK statistiliselt olulised KAOTAJAD (RADA A
  suured negatiivsed t-vaartused). POSITIIVSETEST lahtritest labib
  p < 0.05 TAPSELT 0.
  Bonferroni lavi 92 testi juures = 0.00054.
  Parim positiivne toores p = 0.076 (B_D1 GBPJPY MOMENTUM, t = 1.77).

  See on sama viga, mis NEMSIS-is varem tehti (Bonferroni |t| peal, mis
  luges olulisi kaotajaid labiminekuteks). Siin on see valditud:
  raporteeritakse AINULT positiivse poole labiminekud.

===============================================================================
10. LOPLIK PINGERIDA METOODIKA
===============================================================================

  Pingerida on ehitatud OOS neto oodatava vaartuse (R/tehing) jargi,
  filtriga n >= 30. Lisatingimused, mida kontrollitakse ERALDI ja mis
  EI OLE pingerea sisse peidetud:
    - VALID ja OOS peavad olema sama margiga (jarjepidevus)
    - tulemus peab jaama positiivseks spread+50% JA slip 2x juures
    - tulemus ei tohi margi vahetada SL 1.25x / 1.75x ATR juures
    - Monte Carlo (1000 permutatsiooni) 5% kvantiili maxDD

  Uhtegi kandidaati EI tosteta pingereas pelgalt uhe suure vaikese
  valimi tulemuse parast — n >= 30 filter ja VALID-kontroll on selle vastu.

===============================================================================
11. REPRODUTSEERITAVUS
===============================================================================

  python3 bot/hm_audit.py     -> 22 kontrolli, 0 viga
  python3 bot/hm_run.py       -> 27 604 tehingut, 3 CSV-d  (~10 s)
  python3 bot/hm_plot.py      -> 2 PNG-d + koik maatriksid

  Juhuslikkust kasutatakse AINULT Monte Carlo permutatsioonides,
  seemnega RandomState(20260915). Koik muu on determineeritud.
===============================================================================
```
