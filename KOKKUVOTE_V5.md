NEMSIS v5 — EDGE DISCOVERY, LOPPRAPORT
13. september 2026 | BlackBull 525854 LIVE | 205 EUR | MAteckh/nemsis-bot

===============================================================================
LOPPVASTUS
===============================================================================

  A. ROBUST EDGE FOUND — 205 EUR FEASIBLE ........ EI
  B. ROBUST EDGE FOUND — CAPITAL TOO SMALL ....... osaliselt (ainult kuld)
  C. NO ROBUST EDGE FOUND ........................ JAH, FX-i osas

FX: 14 eelregistreeritud huopoteesi, 3 soltumatut ajaakent, 3 kulutaset,
multiple-testing korrektsioon 11 514 katse peale. MITTE UKS ei ole
positiivne isegi FINAL OOS-is ENNE korrektsiooni.

KULD: edge eksisteerib statistiliselt (73/100), aga jaab alla osta-ja-hoia
risk-adjusted tulemusele. See EI OLE universaalne trading edge, vaid kulla
struktuurne drift, mida Donchian osaliselt puuab — halvemini kui hoidmine.

===============================================================================
1. MIDA MA TEGIN (uus, mida v4-s ei olnud)
===============================================================================

UUS ANDMEALLIKAS
  CurrencyShares ETF-id: FXE (EUR), FXB (GBP), FXY (JPY), FXA (AUD),
  FXF (CHF), FXC (CAD). 2514 paeva, 2016-2026.
  Need fondid hoiavad valisvaluuta hoiust, mis TEENIB kohalikku intressi.
  Nende tootluse ja spot-kursi vahe ANNAB intressivahe — andmetest, mitte
  minu malust.

UUS SQL-FUNKTSIOON: load_yahoo_adj()
  Olemasolev load_yahoo_bars() loeb quote[0].close ehk KORRIGEERIMATA
  sulgemishinna. CurrencyShares maksab intressi DIVIDENDIDENA valja,
  seega hinnatootlus EI SISALDA seda uldse — carry-tuletus andis nulli.
  Uus funktsioon loeb adjclose. Olemasolevat EI muudetud.

UUS FAKTOR: latentne valuutatugevus
  8 valuutat (USD EUR GBP JPY CHF AUD NZD CAD) tuletatud 8 paarist
  vahimruutudega, kitsendus "summa = 0".
  KONTROLL 1: read summeeruvad nulli masinataspusega (2.2e-17)
  KONTROLL 2: vastab makropildile —
     2022 tugevaim USD (+6.9%), norgim JPY (-7.5%)  [Fed kiireim tsukkel]
     2023-2025 norgim JPY                            [BoJ jai maha]
     2020 norgim USD (-5.7%)                         [COVID, Fed nulli]
  Faktor on KORREKTNE. Aga ukski sellel pohinev strateegia ei teeni.

HUPOTEESIREGISTER (Phase 4)
  v5_registry.py — 14 huopoteesi kirjas ENNE testimist:
  ID, kuupaev, pohjendus, features, entry, exit, oodatav efekt.
  Registrit ei taiendatud tagantjarele tulemuse ilustamiseks.

ANDMEJAOTUS (Phase 5), fikseeritud ja muutmata
  TRAIN       2016-09-12 .. 2021-12-31   (huopoteeside loomine)
  VALIDATION  2022-01-01 .. 2024-12-31   (parameetrite valik)
  FINAL OOS   2025-01-01 .. 2026-09-11   (EI KASUTATUD uhegi valiku jaoks)

===============================================================================
2. KOIGE OLULISEM: LEIDSIN ARTEFAKTI, MIS OLEKS ANDNUD VALE VASTUSE
===============================================================================

CS-CARRY andis esimesel jooksul:
  TRAIN +12.49 bp (Sharpe 4.41) | VALID +13.34 (4.78) | FINAL OOS +8.32 (3.34)
  Robustne KOIGIL kolmel kulutasemel. See oleks olnud "PASS".

Paris FX carry Sharpe on kirjanduses 0.4-0.8. Sain 4.4 — kuus korda liiga
hea. Seega otsisin viga.

OTSUSTAV TEST — nihutasin skoori ajas tagasi:
  nihe   0 paeva:  +12.03 bp
  nihe   1 paev:   -1.89 bp   <-- kogu serv kadus UHE paevaga
  nihe   2 paeva:  -2.46 bp
  nihe   5 paeva:  -2.12 bp
  nihe  20 paeva:  -1.06 bp
  nihe 120 paeva:  -1.92 bp

Intressimaar EI MUUTU paevaga — keskpank muudab kord kvartalis. Paris
carry ei tohiks lukkamisest peaaegu uldse muutuda.

POHJUS: ETF sulgub 16:00 ET, Yahoo FX-noteering hiljem. Nende VAHE
sisaldab tukki jargmise paeva liikumisest. See on ajastuse
mitteuhtivusest tulenev lookahead.

KONTROLL: aasta vanune intressivahe (ei saa sisaldada hiljutist hinda):
  +0.28 bp, Sharpe +0.10 = NULL.

Kui ma poleks seda kontrollinud, oleksin sulle muunud strateegia, mis
live'is kaotab.

===============================================================================
3. KOIK 14 HUPOTEESI (bp/paev, BASE-kulud)
===============================================================================

 ID   huopotees           TRAIN    VALID  FINAL OOS   verdikt
 ---  -----------------  ------   ------  ---------   -------
 H01  CS-MOM-1D           -5.19    -5.22      -7.66   FAIL
 H02  CS-MOM-5D           -3.27    -2.16      -4.32   FAIL
 H03  CS-MOM-20D          -0.74    -1.18      -3.84   FAIL
 H04  CS-MOM-60D          -1.79    -2.33      -0.63   FAIL
 H05  CS-CARRY (lag 1p)   -2.20    -1.06      -2.47   FAIL
 H06  CS-CARRY+MOM        -1.67    -1.46      -5.24   FAIL
 H07  TS-MOM-MULTI        -0.77    -1.13      -1.44   FAIL
 H08  MOM-ACCEL           -0.10    -0.38      -5.10   FAIL
 H09  MOM-PERSIST         -1.37    -0.56      -4.56   FAIL
 H10  OVERNIGHT         c->o +0.43bp vs kulu 2.6bp    FAIL
 H11  WEEKDAY           parim K +1.33bp vs kulu 2.6   FAIL
 H12  MONTHEND          kuu lopp +0.79bp vs kulu 2.6  FAIL
 H13  RELVAL-TRI        andmeid liiga vahe            INCONCLUSIVE
 H14  RELVAL-AUDNZD       -0.40    +0.65      -1.67   FAIL

H10 detail (bp/paev, ILMA kuludeta):
  keskmine close->open  +0.43 bp
  keskmine open->close  -0.04 bp
  edasi-tagasi kulu      2.60 bp   => kumbki ei kata kulu

H11/H12 detail (bp/paev, ILMA kuludeta):
  E +1.01 | T +0.77 | K +1.33 | N -0.14 | R -2.27
  kuu viimased 3 +0.79 | kuu esimesed 3 -2.07
  edasi-tagasi kulu 2.60 bp => ukski ei kata kulu

===============================================================================
4. MULTIPLE TESTING (Phase 4)
===============================================================================

 ID   huopotees            t     p(uhep.)  BH lavend  Defl.Sharpe  labib?
 ---  -----------------  ------  --------  ---------  -----------  ------
 H08  MOM-ACCEL          -1.16    0.8772     0.0056      0.000       ei
 H03  CS-MOM-20D         -1.51    0.9341     0.0111      0.000       ei
 H04  CS-MOM-60D         -1.89    0.9708     0.0167      0.000       ei
 H09  MOM-PERSIST        -2.06    0.9805     0.0222      0.000       ei
 H05  CS-CARRY           -2.34    0.9905     0.0278      0.000       ei
 H06  CS-CARRY+MOM       -2.67    0.9963     0.0333      0.000       ei
 H07  TS-MOM-MULTI       -3.27    0.9995     0.0389      0.000       ei
 H02  CS-MOM-5D          -3.44    0.9997     0.0444      0.000       ei
 H01  CS-MOM-1D          -6.42    1.0000     0.0500      0.000       ei

 Benjamini-Hochberg labijad: MITTE UKSKI
 Deflated Sharpe > 0.95 (arvestab 11 514 katset): MITTE UKSKI

 Iga t-statistik on NEGATIIVNE. Ukski ei lahene isegi korrigeerimata
 0.05 lavendile.

===============================================================================
5. KULUTUNDLIKKUS (Phase 6)
===============================================================================

 ID   huopotees      BRUTO     LOW     BASE     HIGH   hinnang
 ---  ------------  ------  ------  -------  -------  --------
 H01  CS-MOM-1D      -1.78   -3.12    -5.61    -9.45  kaotaja
 H02  CS-MOM-5D      -1.29   -1.93    -3.11    -4.93  kaotaja
 H03  CS-MOM-20D     -0.46   -0.79    -1.40    -2.33  kaotaja
 H04  CS-MOM-60D     -1.16   -1.37    -1.76    -2.35  kaotaja

 Isegi BRUTO (enne kulusid) on koigil negatiivne. Probleem ei ole
 kuludes — signaalis ei ole infot.

===============================================================================
6. PHASE 10 — KULD: EDGE VOI DRIFT?
===============================================================================

 a) SUUNA KAUPA (lookback 50, kuludega)
      ainult LONG    49 tehingut   +2062.56 EUR   55.1% voitu
      ainult SHORT   16 tehingut     +85.80 EUR   31.2% voitu
      molemad        65 tehingut   +2148.36 EUR   49.2% voitu
      => 96% kasumist on PIKK positsioon

 b) PERIOODIDE KAUPA
      2020-2021   12 teh    -31.91 EUR    (kuld +18.0%)
      2022-2023   18 teh   +251.72 EUR    (kuld +14.6%)
      2024        10 teh   +228.97 EUR    (kuld +27.4%)
      2025-2026   25 teh  +1699.58 EUR    (kuld +65.1%)
      => 79% kasumist kahest aastast, mil kuld tousis 65%

 c) WALK-FORWARD lookbacki valikul
      TRAIN valis lookback 100 (MITTE 50)
      TRAIN       8 teh    -26.14 EUR
      VALID      26 teh   +239.71 EUR
      FINAL OOS  21 teh  +1485.46 EUR
      => strateegia EI OLE vaartusetu, OOS on positiivne

 d) RISK-ADJUSTED VORDLUS
                             NETO     maxDD   tulu/DD
      Donchian 50        +2148.36    -47.3%     22.15
      osta-ja-hoia 1 unts +2615.60    -25.1%     50.91
      => osta-ja-hoia on 2.3x PAREM risk-adjusted

 JARELDUS: sinu enda reegli jargi ("kui buy-and-hold annab parema
 risk-adjusted tulemuse, ARA nimeta Donchianit edge'iks") — ma ei nimeta.

===============================================================================
7. EDGE SCORE /100 (Phase 12)
===============================================================================

 kandidaat          OOS  stat  kulu  par  paar  rez   DD  205EUR  KOKKU
                    (25)  (15)  (10) (10)  (10) (10) (10)   (10)
 ----------------   ----  ----  ---- ----  ---- ---- ----  -----  -----
 FX parim (H07)        0     0     0    0     0    0    5      5     10
 XAUUSD Donchian      25     8    10   10    10   10    0      0     73

 PASS-reeglid: OOS > 0  JA  205 EUR teostatav  JA  serv jaab kuludega.
   FX parim:        OOS -1.44 bp          => FAIL (OOS negatiivne)
   XAUUSD Donchian: OOS +1485 EUR, aga
                    205 EUR teostatavus 22.0%,
                    maxDD -47.3%          => FAIL (kapital + drawdown)

===============================================================================
8. PHASE 7 — 205 EUR TEOSTATAVUS
===============================================================================

 Noue: risk tehingu kohta 0.25-1.0%. Brokeri miinimum-lot 0.01.

 kandidaat              instrument      SL vaartus   % 205-st   0.25-1%?
 --------------------   ------------    ----------   --------   --------
 CS-korv (4 positsiooni) FX korv            6.40 EUR     3.1%    EI
 CS-korv (2 paari)       2 FX paari         3.20 EUR     1.6%    1-2%
 XAUUSD Donchian         XAUUSD paev       45.00 EUR    22.0%    EI

 CS-korv noiab k=2 => 4 positsiooni korraga lahti. Iga positsioon on
 miinimum 0.01 lot.

===============================================================================
9. MIS TOOTAB / MIS EI TOOTA
===============================================================================

TOOTAB (tehniliselt, mitte rahaliselt):
  + Backtest-engine on auditeeritud ja korrektne (16 sunteetilist testi)
  + Latentne valuutatugevus tuleneb korrektselt ja vastab makropildile
  + Carry-tuletus ETF-idest annab OIGE JARJESTUSE (tase on nihkes)
  + Kulumudel (spread + komisjon + slippage + swap) on paigas
  + Hupoteesiregister ja multiple-testing raamistik toimivad
  + XAUUSD Donchian annab ajaloolist kasumit ja labib walk-forwardi

EI TOOTA:
  - Ristloikeline valuutamomentum (koik horisondid 1d/5d/20d/60d)
  - Carry, kui ta on korrektselt lukatud
  - Carry + momentum kombinatsioon
  - Time-series momentum mitme horisondiga
  - Momentumi kiirendus ja pusivus
  - Overnight-efekt (FX on 24h turg — nagu ennustatud)
  - Nadalapaeva ja kuu vahetuse efektid
  - Relative value AUD/NZD spreadil
  - MITTE UKSKI neist ei kata edasi-tagasi kulu 2.6 bp

EI OLE EDGE, KUIGI TEENIB:
  - XAUUSD Donchian: 96% pikast positsioonist, 79% kahest aastast,
    risk-adjusted halvem kui osta-ja-hoia

===============================================================================
10. MIS JAI TESTIMATA (aus nimekiri)
===============================================================================

  - CARRY PARIS intressiandmetega. ETF-tuletus on TASEMENA kasutuskolbmatu
    (uhtlane ~+3% nihe). Vaja oleks keskpankade maarasid voi forward-punkte.
  - H13 kolmnurk (EURUSD/GBPUSD/EURGBP) — paevaandmed ei ristunud piisavalt.
  - Makrosundmused (CPI, NFP, FOMC, ECB, BoE, BoJ) — kalendrit ei ole.
  - Tick-andmed ja PARIS spread — koik kulud on mudel, mitte moodetud.
  - M15 pikem ajalugu (Yahoo annab 60 paeva).

===============================================================================
11. SOOVITUS
===============================================================================

  1. ARA pane 205 EUR praeguse konfiguratsiooniga tooale.
     Risk of ruin 8.8-9.9%, risk tehingu kohta 22%.

  2. Kui tahad XAUUSD strateegiat kaubelda, vajad 500-1000 EUR.
     500 juures ruin 0.1%, 1000 juures 0.0%.
     AGA: tea, et ostad sisuliselt kulda, mitte strateegiat — ja
     osta-ja-hoia on risk-adjusted 2.3x parem.

  3. FX-i osas on vastus lopik: serva ei ole. Mitte 10 156 v4 testis
     ega 14 v5 eelregistreeritud huopoteesis.

  4. MITTE teha: suurendada sagedust, suurendada voimendust, lisada
     indikaatoreid. Bruto-serv on null ja indikaator ei muuda seda.

===============================================================================
SEIS
===============================================================================

Live-faile main_v4.py, config.py, mt5_connector.py, strategy_meanrev.py,
backtest.py EI OLE muudetud. Juur ja bot/ on sunkroonis. Koik kompileerub.
Bot ootab endiselt /update-i VPS-il — ja ma ei soovita seda saata.

Uus kood: v5_engine.py, v5_registry.py, v5_run.py, v5_final.py,
v5_score.py, v5_carry_check.py, v5_carry_debug.py, sb_daily.py,
kulumudel.py, audit_engine.py, audit_t1.py
