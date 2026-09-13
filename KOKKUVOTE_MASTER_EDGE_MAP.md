===============================================================================
NEMSIS MASTER EDGE RESEARCH MAP
13. september 2026 | 205 EUR | MAteckh/nemsis-bot | RESEARCH ONLY
Live-faile EI MUUDETUD. /update EI saadetud. Midagi ei deploy'itud.
===============================================================================

===============================================================================
1. EXECUTIVE SUMMARY
===============================================================================

KUSIMUS: kui palju pariselt erinevat ja teaduslikult usutavat
edge-uurimist on veel jarel?

VASTUS: 55 kategooriast on 31 TESTITUD, 9 OSALISELT TESTITUD,
8 TESTIMATA-AGA-TESTITAV, 7 TESTIMATU praeguste andmetega.

Ausalt: PARISELT ERINEVAID ja TESTITAVAID suundi on jarel 5.
Koik ulejaanud "testimata" kategooriad on kas (a) juba testitud teise
nime all, (b) vajavad andmeid, mida ei ole, voi (c) on 205 EUR kontol
nagunii teostamatud.

VIIS ALLESJAANUD SUUNDA (tahtsuse jarjekorras):
  1. CFTC COT positsioneerimine       — tasuta avalik, nadalane, dokumenteeritud
  2. Intressivahe MUUTUS (mitte tase) — andmed JUBA OLEMAS (BIS)
  3. Keskpanga poliitika divergents   — andmed JUBA OLEMAS (BIS)
  4. Kvartali/aasta lopu sesoonsus    — andmed JUBA OLEMAS
  5. Majanduskalender (CPI/FOMC/ECB)  — vajab valist andmestikku

Neist 2, 3 ja 4 saab testida ILMA uue andmestikuta, tana.

KRIITILINE HOIATUS: kolm neist viiest (2, 3, 4) on madala eeldatava
mojuga ja korge andmekaevandamise riskiga, sest need on sama
"hinnapohise faktori" perekonna variandid, mille bruto-serv on juba
moodetud ~0. Ainult 1 (COT) ja 5 (kalender) toovad PARISELT uue
informatsiooniallika, mida hinnaseerias ei ole.

205 EUR PIIRANG jaab kehtima koigi jaoks: miinimum-lot 0.01 tahendab,
et iga mitmepositsiooniline strateegia noiab 10-20x voimendust.

===============================================================================
2. OLEMASOLEVA UURIMISTOO INVENTUUR
===============================================================================

MAHT (repost loetud, mitte malust):
  commit'e                    139
  uurimisskripte              114
  H1-andmefaile               31
  M15-andmefaile              15
  paevaandmefaile             34
  kokkuvottefaile             7 (KOKKUVOTE*.md, UURINGUD.md)
  teste kokku                 ~11 650

ANDMESTIK:
  H1    31 instrumenti (22 FX + 9 indeksit/metalli/krüpto)
        2023-11-27 .. 2026-09-13, ~17 280 baari paari kohta
  M15   15 FX-paari, 60 paeva, ~5 590 baari
  PAEV  34 seeriat, 2016-2026, ~2 600 baari
  ERI   bot/data/policy_rates.csv  BIS keskpankade poliitikamaarad
                                   2016-01..2026-08, 8 valuutat
        bot/data/RATES_m.csv       uks intressiseeria
  PUUDU bid/ask, tick, maht, majanduskalender, optsioonid, COT

VOORUDE KAUPA:

 VOOR  MIDA TESTITI                          TESTE   TULEMUS
 ----  ------------------------------------  ------  ------------------------
 v4    10 strateegiaperekonda, 24 instr.     10 156  1 labija, seegi pikk pos.
       rezhiimiraamistik 7x10x14                 61  rezhiimiluliti OOS 0/14
       turustruktuur (BOS/CHOCH/sweep)           ~5  serva ei ole
       PDF-i 15 paaripohist konfi               252  ausas baseline'is 0/15
       S/R tagasilukkamine                      190  halvem kui juhuslik
       kuunlamustrid                            157  serva ei ole
       signaalikorv                              634  ringtoestus
       backtest-engine'i audit                    16  16/16 OK
 v5    14 eelregistreeritud huopoteesi            14  koik FAIL
       valuutatugevuse faktor                      -  korrektne, aga ei teeni
       ETF-carry                                   -  LOOKAHEAD-ARTEFAKT
 v6    paris carry (BIS-i maarad)                  5  serv paris, 3 tapjat
       NFP makrosundmus                            8  0.13%/aastas
       mikrostruktuur                              -  UNTESTABLE
 v7    selektiivsus (kvaliteediskoor)        33 784  TOP-detsiil -3.02bp
       multi-paar portfell A/B/C                   7  C ei loo A ega B
 v7.1  kulutundlikkus majoritel               1 289  OTSUS D, artefakt
 IMP   impulsi jatkuvus/poordumine               108  parim +0.71bp bruto

KOLM KESKSET MOODETUD FAKTI:

  1. BRUTO-SERV ON ~0 IGAS PEREKONNAS (v4, H1, 8h horisont)
     perekond              BRUTO     NETO    kulu
     F surve->murre        +1.42    -1.59    3.01   <- ainus, mis eristub
     E CHOCH               +0.47    -2.58    3.05
     C Donchian 24h        +0.31    -2.69    3.00
     E BOS                 +0.15    -2.87    3.02
     A trend EMA20/50      +0.06    -2.92    2.99
     B momentum 24h        -0.29    -3.28    2.99
     D poore BB20          -0.48    -3.48    2.99
     E likv. puhkimine     -0.55    -3.56    3.01
     E ebaonn. murre       -0.87    -3.87    3.00
     E noudl./pakkumine    -0.87    -3.91    3.04

  2. KULU KASVAB SAGEDUSEGA, SERV EI KASVA
     teh/aastas    teste   parim BRUTO   kulu/aastas   parim NETO
     < 100           152      +35.9 bp         3.8 %     +29.9 bp
     100-300        5878      +42.1 bp         8.5 %     +36.1 bp
     300-700        2011      +21.5 bp        23.3 %     +18.5 bp
     700-1500       1362      +18.2 bp        52.9 %     +13.3 bp
     1500-4000       421      +13.9 bp        93.1 %     +10.9 bp
     > 4000          332       +6.3 bp       285.2 %      +2.7 bp

  3. 205 EUR MIINIMUM-LOT PIIRANG
     keskmine SL 0.01 lotiga FX-is   1.5-2.3 EUR = 0.7-1.1% kontost
     0.25% riskiga taidetavaid       0 / 22 paari
     piirang kaob taielikult         2000 EUR juures

===============================================================================
3. TAIELIK EDGE-TAKSONOOMIA — 55 KATEGOORIAT
===============================================================================

LEGEND:
  T   = TESTITUD
  OT  = OSALISELT TESTITUD
  TT  = TESTIMATA, AGA TESTITAV
  TM  = TESTIMATU praeguste andmetega
  MP  = MADAL PRIORITEET
  KP  = KORGE PRIORITEET

 #   KATEGOORIA                    STAT  POHJENDUS
 --  ----------------------------  ----  -----------------------------------
  1  PRICE ACTION                   T    157 kuunlamustri testi, serva ei ole
  2  MOMENTUM                       T    TS+CS, 1/5/20/60/120 horisonti
  3  TREND FOLLOWING                T    EMA, Donchian, ADX, mitu akent
  4  BREAKOUT                       T    Donchian, ORB, sessioon, vol-surve
  5  MEAN REVERSION                 T    BB, z-skoor, RSI, 504 testi
  6  STAT. MEAN REVERSION           OT   kolmnurk ja AUD/NZD testitud;
                                         laiem stat-arb mitte
  7  VOLATILITY                     T    ATR-rezhiimid, protsentiilid
  8  VOLATILITY REGIMES             T    7 rezhiimi x 10 perekonda x 14 instr
  9  MOMENTUM + VOLATILITY          T    surve->murre, parim bruto +1.42bp
 10  REGIME DETECTION               T    rezhiimiluliti OOS 0/14, -3.65bp
 11  CROSS-SECTIONAL MOMENTUM       T    v5 H01-H04, koik negatiivsed
 12  TIME-SERIES MOMENTUM           T    v5 H07, -0.77/-1.13/-1.44 bp
 13  RELATIVE STRENGTH              T    v7 filtrina, +0.10bp bruto
 14  CURRENCY STRENGTH              T    latentne faktor, valideeritud,
                                         aga ukski strateegia ei teeni
 15  CARRY                          T    BIS poliitikamaarad, Sharpe 0.42,
                                         kolm tapjat (markup/JPY/205EUR)
 16  CENTRAL BANK POLICY            OT   maarade TASE testitud;
                                         DIVERGENTS ja SUURPRIIS mitte
 17  INTEREST-RATE DIFFERENTIALS    OT   tase testitud; MUUTUS mitte
 18  MACRO DATA                     TT   ainult NFP; CPI/PPI/GDP mitte
 19  ECONOMIC EVENTS                TT   FOMC/ECB/BoE/BoJ kuupaevad puuduvad
 20  NEWS REACTION                  OT   NFP tehtud (+8.9bp/-17.1bp 10x slip)
 21  POST-NEWS DRIFT                OT   NFP +24h tehtud; muud mitte
 22  PRE-EVENT POSITIONING          TT   vajab kalendrit
 23  SESSION EFFECTS                T    Aasia/London/NY/kattuvus
 24  TIME-OF-DAY                    T    24 tundi, z-skoor 1.1-3.5 vs mura 1.9
 25  DAY-OF-WEEK                    T    E+1.01 T+0.77 K+1.33 N-0.14 R-2.27 bp
 26  MONTH-END                      T    kuu lopp +0.79bp vs kulu 2.6bp
 27  QUARTER-END                    TT   andmed olemas, testimata
 28  YEAR-END                       TT   andmed olemas, testimata
 29  OPEN/CLOSE EFFECTS             T    c2o +0.43bp, o2c -0.04bp
 30  WEEKEND EFFECTS                OT   overnight tehtud; nadalavahetuse
                                         gap eraldi mitte
 31  GAP EFFECTS                    OT   sama mis 30
 32  LIQUIDITY                      TM   vajab mahtu voi spreadi ajalugu
 33  SPREAD BEHAVIOR                TM   spread-ajalugu puudub
 34  TRANSACTION-COST EFFECTS       T    laialdaselt; 3 kulutaset, sweepid
 35  MARKET MICROSTRUCTURE          TM   tick/bid-ask puudub
 36  ORDER FLOW                     TM   tick puudub; sunteetilist EI loodud
 37  BID/ASK IMBALANCE              TM   bid/ask puudub
 38  TICK DATA                      TM   puudub
 39  LEAD-LAG                       T    2 680 testi, sh US10Y/VIX/BTC
 40  PAIR RELATIONSHIPS             T    22 paari, ristloige
 41  CORRELATION                    T    portfelli exposure-filter
 42  COINTEGRATION                  OT   2 paari testitud, laiem mitte
 43  STATISTICAL ARBITRAGE          OT   sama mis 42
 44  RELATIVE VALUE                 OT   sama mis 42
 45  MULTI-TIMEFRAME SIGNALS        T    H1 trend + M15 entry (60 paeva)
 46  MULTI-PAIR SIGNALS             T    v7, 22 paari, C ei loo A ega B
 47  CROSS-ASSET SIGNALS            OT   lead-lag'is osaliselt;
                                         susteemselt mitte
 48  DXY / USD EFFECTS              OT   valuutatugevuses sees;
                                         DXY-indeksina mitte
 49  GOLD                           T    Donchian, drift vs edge, Phase 10
 50  OIL                            OT   WTI instrumendina; CAD-mojuna mitte
 51  BONDS / YIELDS                 OT   US10Y lead-lag'is; tootluskover mitte
 52  EQUITIES                       OT   SPX/NAS100 lead-lag'is
 53  RISK-ON / RISK-OFF             OT   VIX lead-lag'is; rezhiimina mitte
 54  OPTIONS-RELATED INFO           TM   optsiooniandmed puuduvad
 55  POSITIONING                    TT   CFTC COT — tasuta, avalik, TESTIMATA
 56  SENTIMENT                      MP   andmekvaliteet kahtlane
 57  SEASONALITY                    OT   kuu lopp tehtud; kvartal/aasta mitte
 58  VOLATILITY RISK PREMIUM        TM   vajab implied vol'i (optsioonid)
 59  LIQUIDITY REGIMES              TM   vajab mahtu/spreadi
 60  EVENT VOLATILITY               OT   NFP vol 1.78-1.98x tehtud
 61  PORTFOLIO CONSTRUCTION         T    v7, equal/TOP-N/exposure-filter
 62  ENSEMBLE STRATEGIES            T    634 kandidaati, korv, ringtoestus
 63  ADAPTIVE REGIME STRATEGIES     T    rezhiimiluliti, OOS 0/14
 64  TAIL / EXTREME-MOVE            T    impulsi test, 108 varianti

===============================================================================
4. TESTITUD KATEGOORIAD (31)
===============================================================================

1 Price action | 2 Momentum | 3 Trend following | 4 Breakout
5 Mean reversion | 7 Volatility | 8 Volatility regimes
9 Momentum+volatility | 10 Regime detection | 11 Cross-sectional momentum
12 Time-series momentum | 13 Relative strength | 14 Currency strength
15 Carry | 23 Session effects | 24 Time-of-day | 25 Day-of-week
26 Month-end | 29 Open/close | 34 Transaction costs | 39 Lead-lag
40 Pair relationships | 41 Correlation | 45 Multi-timeframe
46 Multi-pair | 49 Gold | 61 Portfolio construction
62 Ensemble | 63 Adaptive regime | 64 Tail/extreme-move

Neid EI TOHI uuesti testida ilma uue andmestiku voi pariselt uue
mehhanismita.

===============================================================================
5. OSALISELT TESTITUD KATEGOORIAD (9)
===============================================================================

 KATEGOORIA                MIS ON TEHTUD          MIS ON TEGEMATA
 ------------------------  ---------------------  -----------------------
 6  Stat. mean reversion   kolmnurk, AUD/NZD      laiem paaride ristloige
 16 Central bank policy    maarade TASE           divergents, suurpriis
 17 Rate differentials     tase                   MUUTUS (carry momentum)
 20 News reaction          NFP                    CPI, FOMC, ECB, BoE, BoJ
 21 Post-news drift        NFP +24h               muud sundmused
 30 Weekend/gap effects    overnight c2o/o2c      nadalavahetuse gap eraldi
 42 Cointegration          2 paari                laiem otsing
 47 Cross-asset signals    lead-lag'is            susteemne raamistik
 57 Seasonality            kuu lopp               kvartali ja aasta lopp

===============================================================================
6. TESTIMATA, AGA TESTITAVAD KATEGOORIAD (8)
===============================================================================

 KATEGOORIA                 ANDMED OLEMAS?   MARKUS
 -------------------------  ---------------  --------------------------
 55 CFTC COT positioning    EI (tasuta saab) nadalane, dokumenteeritud
 17 Rate diff MUUTUS        JAH (BIS)        testitav TANA
 16 Policy divergents       JAH (BIS)        testitav TANA
 27 Quarter-end             JAH              testitav TANA
 28 Year-end                JAH              testitav TANA
 18 Macro data (CPI/PPI)    EI               vajab kalendrit
 19 Economic events         EI               vajab kalendrit
 22 Pre-event positioning   EI               vajab kalendrit

===============================================================================
7. TESTIMATUD PRAEGUSTE ANDMETEGA (7)
===============================================================================

 KATEGOORIA                    PUUDUV ANDMESTIK
 ---------------------------   ----------------------------------------
 32 Liquidity                   maht voi spread-ajalugu
 33 Spread behavior             spread-ajalugu (tick voi 1-min bid/ask)
 35 Market microstructure       tick-andmed
 36 Order flow                  tick-andmed
 37 Bid/ask imbalance           bid/ask kvoodid
 38 Tick data                   tick-andmed
 54 Options-related info        optsioonide implied vol / skew
 58 Volatility risk premium     implied vol (optsioonid)
 59 Liquidity regimes           maht/spread

TAHTIS: neid EI OLE "FAIL". Neid EI SAA otsustada ilma oigete andmeteta.
Sunteetilist order flow'd EI LOODUD ega looda.

===============================================================================
8. ANDMELUNGAD — TAPSED NOUDED
===============================================================================

 VAJALIK ANDMESTIK        MILLEKS              KATTESAADAVUS       HIND
 -----------------------  -------------------  ------------------  --------
 CFTC COT (nadalane)      positsioneerimine    cftc.gov, tasuta    0 EUR
 Majanduskalender         sundmused, drift     mitu allikat        0-30 EUR/kuu
 Tick / bid-ask ajalugu   mikrostruktuur       Dukascopy tasuta    0 EUR
                                               (aga suur maht)
 Optsioonide implied vol  vol risk premium     Bloomberg/CME       kallis
 Maht (FX futuurid)       likviidsus           CME, osaliselt      0 EUR
 DXY indeks               USD-efekt            Yahoo (^DXY)        0 EUR
 Tootluskover (2y/10y)    makro                osaliselt Yahoo     0 EUR

MIDA NEMSIS-IL JUBA ON:
  OHLC H1 31 instrumendil, M15 15 paaril, paev 34 seerial
  BIS keskpankade poliitikamaarad 8 valuutale 2016-2026
  CurrencyShares ETF-id (adjclose) 6 valuutale

MIDA EI OLE JA MIDA EI TOHI VALJA MOELDA:
  bid/ask, tick, maht, order flow, optsioonid, kalender, COT

===============================================================================
9. UELELIIGSED KATEGOORIAD — MIDA MITTE TESTIDA
===============================================================================

Need on SAMA MEHHANISM erineva nime all. Neid EI hakata eraldi testima:

 "UUS" IDEE                    ON TEGELIKULT           JUBA TESTITUD
 ---------------------------   ---------------------   ------------------
 EMA/RSI/MACD kombinatsioonid  trend + poore           v4 (10 156 testi)
 "bid/ask imbalance" kerest    hinnamuutus             momentum
 "quote intensity" ulatusest   volatiilsus             vol-rezhiimid
 "likviidsusshokk" baarist     vol-hupe                "ebanormaalne" rezhiim
 supply/demand tsoonid         S/R                     190 varianti
 order block / FVG             S/R + gap               S/R + overnight
 harmoonilised mustrid         kuunlamustrid           157 testi
 Fibonacci tasemed             S/R                     190 varianti
 Elliott laine                 trendijargimine         v4
 uus timeframe sama reegliga   sama mehhanism          v4-v7
 uus parameeter samas reeglis  parameetri optimeerimine KEELATUD

REEGEL: enne iga uut testi kusi — KAS SEE ON UUS INFORMATSIOONIALLIKAS
VOI SAMA INFO UUE NIMEGA? Kui viimane, ara testi.

===============================================================================
10. KORGE PRIORITEET — 2 SUUNDA
===============================================================================

 KOHT  SUUND                     MIKS KORGE PRIORITEET
 ----  ------------------------  ---------------------------------------
   1   CFTC COT POSITSIONEERIMINE
       Mehhanism        suurte spekulantide positsioonid ennustavad
                        poordeid ekstreemumites (dokumenteeritud)
       MIKS ERINEV      see EI OLE hinnainfo. See on AINUS taiesti uus
                        informatsiooniallikas, mis on tasuta kattesaadav.
                        Koik 11 650 senist testi kasutasid hinda.
       Andmed           cftc.gov, nadalane, alates 1986, tasuta
       Sagedus          nadalane => madal kulu (v4 tabel: <100 teh/a
                        on parim kulukategooria)
       205 EUR sobivus  HEA: nadalane, 1-2 positsiooni, pikk hoidmisaeg
       Ulesobitamise ri MADAL: uks muutuja, vahe vabadusastmeid
       Oodatav moju     vaike-keskmine, aga PARIS uus info

   2   MAJANDUSKALENDER (CPI, FOMC, ECB, BoE, BoJ)
       Mehhanism        sundmused muudavad volatiilsust, trendi pusivust,
                        poordetoenaosust — mitte "BUY FOMC"
       MIKS ERINEV      NFP andis +8.9bp bruto; teisi sundmusi pole
                        uldse testitud. Ka teine uus informatsiooniallikas.
       Andmed           vajab valist kalendrit (tasuta allikaid on)
       205 EUR sobivus  KESKMINE: sundmusi ~50-100/aastas, 1 positsioon
       Ulesobitamise ri KESKMINE: mitu sundmusetuupi, mitu horisonti
       HOIATUS          NFP andis konservatiivse slippage'iga +1.1bp
                        ehk 0.13%/aastas. Eeldatav moju VAIKE.

===============================================================================
11. KESKMINE PRIORITEET — 3 SUUNDA
===============================================================================

 KOHT  SUUND                     MARKUS
 ----  ------------------------  ---------------------------------------
   3   INTRESSIVAHE MUUTUS       Andmed JUBA OLEMAS (BIS). Carry TASE
       (carry momentum)          on testitud (Sharpe 0.42, 3 tapjat).
                                 MUUTUS on eraldi mehhanism: valuuta,
                                 mille maar TOUSEB, tugevneb enne kui
                                 tase joutakse jarele.
                                 MIKS ERINEV: tase vs muutus on
                                 majanduslikult eri asi.
                                 RISK: sama andmestik, mis juba andis
                                 negatiivse vastuse. Voib olla sama
                                 efekt teise nurga alt.
                                 TESTITAV TANA, ilma uue andmestikuta.

   4   KESKPANGA DIVERGENTS      Andmed JUBA OLEMAS. Mitte maara tase,
                                 vaid KAHE keskpanga suuna erinevus
                                 (uks tostab, teine langetab).
                                 RISK: korgelt korreleeritud punktiga 3.
                                 Kui 3 ebaonnestub, ara testi 4.

   5   KVARTALI / AASTA LOPP     Andmed JUBA OLEMAS. Kuu lopp andis
                                 +0.79bp vs kulu 2.6bp. Kvartali lopp
                                 on mehhanismina tugevam (fondide
                                 rebalanss, aastaaruanded).
                                 RISK: kuu lopu tulemus oli 3x alla kulu.
                                 Kvartal peaks olema 3-4x tugevam et
                                 uldse kulubarjaarini jouda.
                                 ODAV TESTIDA: 1 skript, 1 tund.

===============================================================================
12. MADAL PRIORITEET
===============================================================================

 SUUND                    MIKS MADAL
 -----------------------  ----------------------------------------------
 Laiem kointegratsioon    2 paari testitud, molemad FAIL. Laiem otsing
                          on 231 paarikombinatsiooni = andmekaevandamine.
 Cross-asset susteemne    Lead-lag tegi juba 2 680 testi sh US10Y/VIX/BTC.
 DXY indeksina            Valuutatugevuse faktor katab sama info.
 Nadalavahetuse gap       Overnight tehtud, gap on selle alamosa.
 Sentiment                Andmekvaliteet kahtlane, mehhanism nork.
 Risk-on/risk-off rezhiim Rezhiimidetektor andis OOS 0/14.

===============================================================================
13. UNIVERSAALNE UURIMISPROTOKOLL
===============================================================================

IGA tulevane NEMSIS-eksperiment PEAB jargima seda. Ilma erandita.

SAMM 1 — EELREGISTREERIMINE (enne uhtegi arvutust)
  [ ] huopoteesi ID ja kuupaev
  [ ] MAJANDUSLIK MEHHANISM: miks see peaks tootama?
      Kui mehhanismi ei suuda uhe lausega seletada, ARA TESTI.
  [ ] tapne reegel: entry, exit, filtrid, parameetrid
  [ ] oodatav efekt ja suund KIRJA ENNE testi
  [ ] mitu varianti testitakse (see arv laheb Bonferronisse)
  [ ] mis andmed, mis periood

SAMM 2 — ANDMEAUDIT
  [ ] kas andmed on olemas? Kui ei — STOP, margi TESTIMATU
  [ ] duplikaadid, OHLC-loogika, sunteetiline Open
  [ ] kas andmed on revideeritavad? (makroandmed on, hinnad ei ole)
  [ ] EI LOODA sunteetilisi andmeid

SAMM 3 — LOOKAHEAD-AUDIT (kohustuslik, ENNE testi)
  [ ] juhuslikul jalutuskaigul peab tulemus olema TAPSELT -kulu
  [ ] positiivne kontroll: tahtlik tuleviku info peab paistma
  [ ] koik indikaatorid .shift(1) kus kahtlus
  [ ] entry = jargmise baari AVANEMINE
  [ ] jarjestus/normaliseerimine ei tohi kasutada tulevikku
  [ ] makroandmed nihutatud avaldamisviivituse vorra

SAMM 4 — KULUMUDEL
  [ ] LOW / BASE / HIGH kolm taset
  [ ] spread + komisjon + slippage + swap
  [ ] kui serv kaob LOW->BASE juures: FRAGIILNE
  [ ] kui serv < 2.0bp round-trip: EI OLE KAUBELDAV, lopeta

SAMM 5 — VALIDEERIMINE
  [ ] TRAIN / VALIDATION / FINAL OOS, ajaliselt
  [ ] FINAL OOS-i EI KASUTATA uhegi valiku tegemiseks
  [ ] walk-forward, libisev aken
  [ ] kui serv on ainult uhes aknas: FAIL

SAMM 6 — ROBUSTSUS
  [ ] koik paarid vs ainult majorid
  [ ] eemalda parim paar; eemalda kaks parimat
  [ ] aastate kaupa
  [ ] parameetriplatoo (mitte uksik tipp)
  [ ] KONTSENTRATSIOON: kui uks paar annab >50% kasumist, FAIL

SAMM 7 — STATISTIKA
  [ ] t, p, tehingute arv
  [ ] Bonferroni voi Benjamini-Hochberg TEHTUD variantide arvu jargi
  [ ] Deflated Sharpe, arvestades ~11 650 varasemat testi
  [ ] vordlus JUHUSLIKU sisenemisega, mis labib SAMA valikuprotsessi
  [ ] t-jaotuse kuju: kui keskmine t on negatiivne, on parim tulemus mura

SAMM 8 — 205 EUR TEOSTATAVUS
  [ ] miinimum-lot 0.01, lot-samm 0.01
  [ ] risk tehingu kohta <= 0.50% (siht 0.25%)
  [ ] KUI LOT EI MAHU: TRADE = REJECTED. MITTE umardada ules.
  [ ] mitu % signaalidest on taidetav?
  [ ] marginaal, max samaaegseid positsioone
  [ ] VOIMENDUST EI SUURENDATA piirangu lahendamiseks

SAMM 9 — PASS / FAIL
  PASS noiab KOIKI:
    1. NETO ootus > 0 realistlike kuludega
    2. FINAL OOS > 0
    3. FINAL OOS ei soltu uhest paarist
    4. parima paari eemaldamine ei havita serva
    5. serv talub BASE-kulusid (mitte ainult LOW)
    6. >= 200 tehingut
    7. risk <= 0.50% tehingu kohta
    8. >= 20% signaalidest taidetav 205 EUR kontol
    9. positiivne rohkem kui uhes ajaaknas
   10. labib multiple-testing korrektsiooni
   11. majanduslik mehhanism on kaitstav

  Kui mitte KOIK: FAIL. LOPETA. Ara optimeeri edasi.

SAMM 10 — LOPETAMISE REEGEL
  [ ] uks huopotees = uks primary spetsifikatsioon
  [ ] kui FAIL, EI tehta "v2" sama mehhanismiga
  [ ] kui FAIL, EI lisata indikaatoreid tulemuse parandamiseks
  [ ] kui FAIL, minnakse JARGMISE MEHHANISMI juurde voi lopetatakse

===============================================================================
14. 205 EUR TEOSTATAVUSE PIIRANG
===============================================================================

MOODETUD FAKT (v7, 22 FX-paari):
  keskmine SL 0.01 lotiga        1.76 EUR = 0.9% 205 EUR kontost
  maksimaalne SL 0.01 lotiga     2.26 EUR = 1.1% kontost

TAIDETAVAD SIGNAALID:
  kapital    0.25%    0.5%   0.75%    1.0%
   205 EUR    0/22    1/22    3/22   10/22
   250 EUR    0/22    2/22    4/22   15/22
   300 EUR    0/22    3/22   13/22   19/22
   500 EUR    2/22   15/22   21/22   22/22
  1000 EUR   15/22   22/22   22/22   22/22
  2000 EUR   22/22   22/22   22/22   22/22

MILLISED KATEGOORIAD SOBIVAD 205 EUR KONTOLE:

 SOBIB (madal sagedus, 1-2 positsiooni, pikk hoidmisaeg):
   CFTC COT positsioneerimine     nadalane
   Kvartali/aasta lopp            4-12 korda aastas
   Keskpanga sundmused            8-12 korda aastas

 EI SOBI (noiab mitut positsiooni voi korget sagedust):
   Multi-paar portfell            4 positsiooni = 21.5x voimendus
   Carry                          4 positsiooni = 21.5x voimendus
   Impulsi jatkuvus               3 860 teh/aastas
   Mikrostruktuur                 korge sagedus

JARELDUS: 205 EUR konto surub uurimise AUTOMAATSELT madala sageduse ja
uhe positsiooni suunas. See kattub v4 sageduse tabeliga, mis naitas, et
<100 teh/aastas on parim kulukategooria. See ei ole juhus.

===============================================================================
15. SOOVITATAV UURIMISJARJEKORD
===============================================================================

 JARK  MIDA                        MIKS SELLES JARJEKORRAS        AEG
 ----  --------------------------  -----------------------------  ------
  0    KULUANDMED: sinu MT5        Enne kui midagi uut testida,    15 min
       swap-tabel ja spreadid      on vaja teada PARIS kulu.       (sinu
       (sina vaatad, mitte mina)   Koik senised kulud on MUDEL.    poolt)
                                   See UKS number muudab iga
                                   jargneva testi lavendit.

  1    KVARTALI/AASTA LOPP         Odavaim test. Andmed olemas.    1 tund
                                   Kui kuu lopp andis +0.79bp,
                                   naeme kohe kas kvartal on
                                   3-4x tugevam. Kui ei, on kogu
                                   sesoonsuse suund surnud.

  2    INTRESSIVAHE MUUTUS         Andmed olemas. Pariselt eri     2 tundi
                                   mehhanism kui carry tase.
                                   Kui FAIL, ara testi divergentsi.

  3    CFTC COT POSITSIONEERIMINE  AINUS taiesti uus info-         1 paev
                                   allikas, mis on tasuta.        (+ andmete
                                   Noiab andmete hankimist.        hankimine)

  4    MAJANDUSKALENDER            Teine uus infoallikas.          1-2 paeva
                                   Noiab valist kalendrit.

  5    STOP                        Kui 1-4 on FAIL, on
                                   hinnapohine ja avalikult
                                   kattesaadav info ammendatud.

MIDA MITTE TEHA JARKUDE VAHEL:
  - mitte optimeerida ebaonnestunud jarku
  - mitte lisada indikaatoreid
  - mitte proovida sama mehhanismi teise timeframe'iga

===============================================================================
16. MIS ON JAREL, ENNE KUI SAAB AUSALT OELDA "AMMENDATUD"
===============================================================================

TAPNE VASTUS:

 KATEGOORIAID KOKKU                          55 (+ 9 alamkategooriat = 64)
 TESTITUD                                    31
 OSALISELT TESTITUD                           9
 TESTIMATA AGA TESTITAV                       8
 TESTIMATU praeguste andmetega                7
 MADAL PRIORITEET / ueleliigne                9

 PARISELT ERINEVAID JA TESTITAVAID SUUNDI     5
   millest ILMA uue andmestikuta               3  (kvartali lopp,
                                                   intressivahe muutus,
                                                   keskpanga divergents)
   millest vajab TASUTA valist andmestikku     2  (CFTC COT, kalender)
   millest vajab TASULIST andmestikku          0

 TESTIMATUKS jaab PUSIVALT (ilma tick/optsioonideta)  7 kategooriat

AUS HINNANG NENDE 5 KOHTA:

  3 neist (kvartali lopp, intressivahe muutus, keskpanga divergents)
  kasutavad andmeid, mis on JUBA OLEMAS ja mille lahedased variandid
  on JUBA ANDNUD negatiivse vastuse. Eeldatav tulemus: FAIL.
  Aga nad on ODAVAD testida (1-2 tundi kokku) ja siis on see suund
  ausalt kinni.

  2 neist (COT, kalender) toovad PARISELT UUE INFORMATSIOONIALLIKA.
  Need on ainsad, mille puhul on ausalt pohjust arvata, et tulemus
  voib olla teistsugune — sest koik 11 650 senist testi kasutasid
  AINULT HINDA.

  Kui need 5 on tehtud ja koik on FAIL, siis on ausalt oeldud:
  "avalikult kattesaadava informatsiooniga ja 205 EUR kontoga ei ole
  FX-is leitav robustne edge."

  Sel hetkel jaaks ainult kolm teed:
    (a) hankida tick/bid-ask andmed ja testida mikrostruktuuri
    (b) suurendada kapitali 2000 EUR-ni, et miinimum-lot piirang kaoks
        (aga see EI LOO serva, ainult lubab teda kaubelda)
    (c) lopetada

MIDA MA EI TEE: ma ei ehita uut strateegiat. See fail on kaart,
mitte strateegia. Ootan sinu otsust, millist suunda votta.

===============================================================================
SEIS
===============================================================================
  Live-failid main_v4.py, config.py, mt5_connector.py EI MUUDETUD.
  /update EI saadetud. Midagi ei deploy'itud.
  Juur ja bot/ sunkroonis. Koik kompileerub.
  Bot ootab /update-i — ara saada.
