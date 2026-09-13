```
===============================================================================
NEMSIS — COT A1: HINNAAJALOO PIKENDUS 2006-2016 (FALSIFITSEERIMISTEST)
===============================================================================
  kuupaev 2026-09-13   haru claude/great-noether-um7382
  LIVE PUUTUMATA: main_v4.py / config.py / mt5_connector.py /
  strategy_meanrev.py / backtest.py EI OLE muudetud. /update EI saadetud.
  A2, A3, A4, A5 EI OLE alustatud.

===============================================================================
1. KOKKUVOTE JUHILE
===============================================================================

  KUSIMUS: kas COT-serv, mis 2016-2026 andis +10 bp/nadal ja t = 3.58,
  eksisteerib ka varasemal perioodil?

  VASTUS: EI. Serv ei ole enne 2016 mitte ainult puudu — ta on
  NEGATIIVNE, ja suund on VASTUPIDINE.

     U7  A_REV  2006-2016   -9.41 bp/nadal   Sharpe -0.57   t = -1.83
     U7  A_REV  2016-2026   +9.70 bp/nadal   Sharpe +0.77   t = +2.45
     U7  A_REV  2006-2026   +0.00 bp/nadal   Sharpe  0.00   t = +0.00

     U28 A_REV  2006-2016   -4.64 bp/nadal   Sharpe -0.27   t = -0.88
     U28 A_REV  2016-2026  +10.09 bp/nadal   Sharpe +1.13   t = +3.58
     U28 A_REV  2006-2026   +2.62 bp/nadal   Sharpe +0.19   t = +0.87

  Kogu 21-aastase valimi peal on U7 tulemus TAPSELT NULL (0.00 bp) ja
  U28 tulemus +2.62 bp, mis EI OLE statistiliselt oluline (p = 0.386).

  Tapp-argument: 2016-2026 aken asub KOIGI 539 liikuva 522-nadalase
  akna seas 99.1. (U7) ja 99.3. (U28) protsentiilis. See on tapselt
  see, mida "ma valisin parima kumnendi" valja naeb.

  A1 RESULT: FAIL
  COT STATUS: SAMPLE-DEPENDENT

===============================================================================
2. ANDMED
===============================================================================

  HINNAD
    allikas       Yahoo Finance `=X` paevane close, laetud SAMA funktsiooni
                  load_yahoo_bars() kaudu Supabase `http` laienduse abil.
                  ANDMEALLIKAS EI MUUTU perioodide vahel — ainult range
                  parameeter on '25y' senise '10y' asemel.
    sumbolid      EURUSD=X GBPUSD=X AUDUSD=X NZDUSD=X USDJPY=X
                  USDCHF=X USDCAD=X
    tabel         market_bars, sumbolid *_d25
    konverter     bot/sb_d25.py -> bot/data/{PAAR}_d25.csv
    hinnavali     close (sama mis algses COT-toos)
    timeframe     1 paev (sama)

    paar       ridu   algus        lopp
    ----       ----   -----        ----
    EURUSD     5912   2003-12-01   2026-09-11
    GBPUSD     5924   2003-12-01   2026-09-11
    AUDUSD     5288   2006-05-15   2026-09-13   <- SIDUV PIIRANG
    NZDUSD     5913   2003-12-01   2026-09-13
    USDJPY     6491   2001-09-10   2026-09-11
    USDCHF     5978   2003-09-16   2026-09-13
    USDCAD     5980   2003-09-16   2026-09-13

    RISTUV AKEN ule 7 paari: 2006-05-15 .. 2026-09-10, 5 265 kauplemispaeva.

    TAHTIS AUS TAPSUSTUS: soovitud algus oli 2004-01-01, aga Yahoo
    AUDUSD=X ajalugu ALGAB 2006-05-15. Kuna valuutakonstruktsioon
    noab KOIKI 8 valuutat korraga (reeglit ei muudetud), algab
    tegelik valim 2006-05. PERIOOD A on seega 2006-05..2010-12,
    MITTE 2004-01..2010-12. AUD-i valjajatmine oleks reeglimuudatus
    ja seda EI TEHTUD.

  COT
    sama andmestik: CFTC Socrata 6dca-aqww, Legacy Futures Only.
    Tabelist cot_legacy eksporditi uuesti KOGU ajalugu (varem 2004+):
    bot/data/cot_legacy.csv = 12 160 rida, 2000-01-04 .. 2026-09-08.
    Pohjus: 156-nadalane rullpertsentiil vajab 2006-05 alguseks
    andmeid alates 2003-05. Andmed, allikas ja tootlus identsed.

  PUUDUVAD VAATLUSED
    2006-2016 aknas 3 puuduvat net_pct vaartust (NZD), 2016-2026 aknas 0.
    Signaalitihedus praktiliselt identne: 26.3% vs 26.4% nadal-valuuta
    lahtritest kannab signaali (|skoor| = 1).

===============================================================================
3. MIDA EI MUUDETUD
===============================================================================

  sama COT-andmestik (6dca-aqww)                    JAH
  sama signaal A_REV (net_pct, 156n pertsentiil)    JAH
  samad lavid 0.90 / 0.10                           JAH
  samad hoiud 1 / 2 / 4 nadalat                     JAH
  sama valuutakonstruktsioon (USD = -keskmine)      JAH
  sama avaldamisviive (report + >= 6 paeva)         JAH
  sama kulumudel (NEMSIS BASE)                      JAH
  samad universumid U7 / U28                        JAH
  MUUTUS AINULT: hinnaseeria pikkus                 JAH

  Uhtegi parameetrit EI muudetud parast 2006-2016 tulemuse nagemist.
  Uhtegi paari, valuutat ega perioodi EI valitud tulemuste jargi.

===============================================================================
4. NO-LOOKAHEAD AUDIT PIKAL VALIMIL
===============================================================================

  cot_audit.py: 16 kontrolli, 0 viga (parast CSV-ootuste uuendamist
  12 160 reale ja algusele 2000-01-04).

  Pika seeria ajastuskontroll:
    COT-nadalaid          1 061   (2006-05-02 .. 2026-09-01)
    avaldamisviive        min 6d, mediaan 6d, max 13d
    sisenemispaev         esmaspaev 99.1%, teisipaev 0.5%, muu 0.5%

  Reegel kehtib kogu pikal valimil identselt.

===============================================================================
5. JARJEPIDEVUSKONTROLL — kas uus hinnaseeria annab sama vastuse?
===============================================================================

  Kriitiline: kui _d25 annaks 2016-2026 teistsuguse tulemuse kui _d,
  ei saaks perioode vorrelda.

  variant                n   keskm_bp  sharpe  kokku%  maxdd%     t      p
  -------                -   --------  ------  ------  ------     -      -
  U7  _d    2016-2026  522      +9.80    0.78   +63.3   -11.6   2.48  0.013
  U7  _d25  2016-2026  522      +9.70    0.77   +62.4   -11.6   2.45  0.014
  U28 _d    2016-2026  522     +10.09    1.13   +67.4    -5.0   3.58  0.000
  U28 _d25  2016-2026  522     +10.09    1.13   +67.5    -5.0   3.58  0.000

  U28 on IDENTNE. U7 erineb 0.10 bp vorra (kaks eri Yahoo tombamist
  annavad moneti erinevaid paevaseid sulgemisi). Seeriad on vorreldavad.

===============================================================================
6. NOUTUD VORDLUSTABEL (A_REV h1, neto, kulu = NEMSIS BASE)
===============================================================================

  U7 (7 paris USD-paari)
  PERIOOD         NADALAID  TEHINGUID  BRUTO_bp  KULU_bp  NETO_bp  KOKKU%  SHARPE  T-STAT
  -------         --------  ---------  --------  -------  -------  ------  ------  ------
  A 2006-2010          243        747    -10.14     0.70   -10.85   -25.1   -0.55   -1.18
  B 2011-2016          295        833     -7.67     0.55    -8.22   -22.6   -0.62   -1.47
  C 2006-2016          538       1580     -8.79     0.62    -9.41   -42.0   -0.57   -1.83
  D 2016-2026          522       1518    +10.23     0.52    +9.70   +62.4   +0.77   +2.45
  E 2006-2026         1060       3098     +0.58     0.57    +0.00    -5.8    0.00    0.00

  U28 (28 paari, ristid USD-jalgadest)
  PERIOOD         NADALAID  TEHINGUID  BRUTO_bp  KULU_bp  NETO_bp  KOKKU%  SHARPE  T-STAT
  -------         --------  ---------  --------  -------  -------  ------  ------  ------
  A 2006-2010          243       2996     -5.87     1.14    -7.01   -17.9   -0.34   -0.73
  B 2011-2016          295       3070     -1.67     1.02    -2.68    -8.8   -0.20   -0.49
  C 2006-2016          538       6066     -3.56     1.07    -4.64   -25.1   -0.27   -0.88
  D 2016-2026          522       5922    +10.99     0.90   +10.09   +67.5   +1.13   +3.58
  E 2006-2026         1060      11988     +3.60     0.99    +2.62   +25.4   +0.19   +0.87

  KASUMLIKUD PERIOODID: 1 / 4 (ainult D). A, B ja C on koik negatiivsed.

  KOIK HOIUD (1/2/4 nadalat) annavad sama pildi:

  U7  hoid 2n:  A -9.93  B -8.90  C -9.37  D +8.73  E -0.45
  U7  hoid 4n:  A -6.41  B -10.06 C -8.41  D +7.23  E -0.71
  U28 hoid 2n:  A -8.59  B -4.18  C -6.17  D +9.61  E +1.60
  U28 hoid 4n:  A -4.46  B -6.49  C -5.57  D +8.20  E +1.21

  Uhelgi hoiul ei ole periood C positiivne. Kummalgi universumil ei ole
  periood E statistiliselt oluline.

===============================================================================
7. FALSIFITSEERIMISKUSIMUSED 1-7
===============================================================================

  Q1  KAS EFEKT KAOB ENNE 2016?

  JAH — ja mis hullem, SUUND POORDUB.

  variant           n   keskm_bp  sharpe   kokku%     t      p
  -------           -   --------  ------   ------     -      -
  U7  A_REV  C    538      -9.41   -0.57    -42.0  -1.83  0.068
  U7  A_REV  D    522      +9.70   +0.77    +62.4  +2.45  0.014
  U7  A_REV  E   1060      +0.00    0.00     -5.8  +0.00  0.999
  U7  A_CONT C    538      +8.17   +0.49    +49.3  +1.58  0.113
  U7  A_CONT D    522     -10.75   -0.86    -44.2  -2.71  0.007
  U7  A_CONT E   1060      -1.15   -0.08    -16.6  -0.35  0.726
  U28 A_REV  C    538      -4.64   -0.27    -25.1  -0.88  0.379
  U28 A_REV  D    522     +10.09   +1.13    +67.5  +3.58  0.000
  U28 A_REV  E   1060      +2.62   +0.19    +25.4  +0.87  0.386
  U28 A_CONT C    538      +2.49   +0.15     +9.8  +0.47  0.637
  U28 A_CONT D    522     -11.88   -1.33    -46.8  -4.21  0.000
  U28 A_CONT E   1060      -4.59   -0.34    -41.6  -1.52  0.129

  2006-2016 tootas JATKUMINE (A_CONT, U7 +8.17 bp).
  2016-2026 tootas POORDUMINE (A_REV, U7 +9.70 bp).
  See on klassikaline signatuur, mis utleb: PARIS EFEKTI EI OLE.
  Kui mehhanism oleks reaalne (rahvamass on sunnitud likvideerima),
  ei pooraks ta suunda kumnendi vahetusel.

  Q2  KAS UKS PERIOOD TEEB KOGU KASUMI?

  JAH, taielikult.
  U7 : kogu logsumma +0.0%  =  2006-2016 (-50.6%) + 2016-2026 (+50.7%)
  U28: kogu logsumma +27.7% =  2006-2016 (-24.9%) + 2016-2026 (+52.7%)

  Kogu kasum ja rohkemgi tuleb uhest kumnendist. Teine kumnend soob
  selle tapselt ara (U7) voi peaaegu ara (U28).

  Q3  KAS UKS VALUUTA TEEB KOGU KASUMI?

  periood            positiivseid paare  mediaan paar  TOP-1 paar  TOP-1 valuuta
  -------            ------------------  ------------  ----------  -------------
  U7  C 2006-2016           2/7 = 28.6%       -5.39%   USDCHF          CHF
  U7  D 2016-2026           7/7 = 100%        +6.93%   NZDUSD 33.5%    USD 50.0%
  U7  E 2006-2026           4/7 = 57.1%       +0.98%   USDCAD 180.3%   CAD 90.2%
  U28 C 2006-2016          13/28 = 46.4%      -0.44%   GBPAUD          CHF
  U28 D 2016-2026          28/28 = 100%       +1.55%   JPYAUD 10.9%    JPY 21.5%
  U28 E 2006-2026          21/28 = 75.0%      +1.64%   JPYAUD 14.9%    AUD 25.3%

  Periood E U7: TOP-1 paar annab 180.3% kogusummast — ehk ULEJAANUD
  KUUS PAARI ON KOKKU NEGATIIVSED. Uks paar kannab kogu tulemuse
  ja rohkemgi. See uksi diskvalifitseeriks strateegia.

  Q4  KAS PARIMA PAARI EEMALDAMINE HAVITAB TULEMUSE? (periood E)

  variant                      n  keskm_bp  sharpe  kokku%  maxdd%     t      p
  -------                      -  --------  ------  ------  ------     -      -
  U28 E koik                1060     +2.62    0.19   +25.4   -27.6   0.87  0.386
  U28 E ilma JPYAUD         1060     +2.09    0.16   +19.1   -28.9   0.72  0.470
  U28 E ilma valuutata AUD  1060     +0.85    0.06    +4.1   -33.7   0.28  0.777

  AUD eemaldamine viib E-tulemuse praktiliselt nulli (+0.85 bp, t = 0.28).
  Kuna E ise ei ole niigi oluline, on see akadeemiline — aga naitab,
  et alles jaanud +2.62 bp on samuti habras.

  Q5  KAS PIKEM VALIM NORGENDAB OLULISUST?

  JAH, dramaatiliselt.
  universum  periood          n  keskm_bp      t       p
  ---------  -------          -  --------      -       -
  U7         C 2006-2016    538     -9.41  -1.83   0.068
  U7         D 2016-2026    522     +9.70  +2.45   0.014
  U7         E 2006-2026   1060     +0.00  +0.00   0.999
  U28        C 2006-2016    538     -4.64  -0.88   0.379
  U28        D 2016-2026    522    +10.09  +3.58   0.000
  U28        E 2006-2026   1060     +2.62  +0.87   0.386

  t langeb 3.58 -> 0.87 (U28) ja 2.45 -> 0.00 (U7). Valimi kahekordis-
  tamine oleks TOSTNUD t-d ~1.4x, kui efekt oleks paris. Selle asemel
  see KUKKUS. See on definitsiooni jargi valimispetsiifiline leid.

  Q6  KAS EFEKT ELAB ULE REALISTLIKUD KULUD? (periood E)

  variant                n   keskm_bp  sharpe   kokku%     t      p
  -------                -   --------  ------   ------     -      -
  U7  E kulu 0bp      1060      +0.58    0.04     +0.1   0.18  0.861
  U7  E kulu 1bp      1060      +0.11    0.01     -4.8   0.03  0.973
  U7  E kulu 2bp      1060      -0.36   -0.02     -9.3  -0.11  0.913
  U7  E kulu 3bp      1060      -0.82   -0.06    -13.7  -0.25  0.801
  U7  E NEMSIS BASE   1060      +0.00    0.00     -5.8   0.00  0.999
  U28 E kulu 0bp      1060      +3.60    0.26    +39.2   1.19  0.233
  U28 E kulu 1bp      1060      +3.13    0.23    +32.4   1.04  0.300
  U28 E kulu 2bp      1060      +2.66    0.20    +26.0   0.88  0.378
  U28 E kulu 3bp      1060      +2.19    0.16    +19.9   0.73  0.467
  U28 E NEMSIS BASE   1060      +2.62    0.19    +25.4   0.87  0.386

  Kulu EI OLE probleem — BRUTO serv on juba nulli lahedal (U7 +0.58 bp,
  U28 +3.60 bp) ja mitte kummalgi juhul oluline. Probleem ei ole kulus,
  probleem on selles, et servi ei ole.

  Q7  KAS 2016-2026 OLI LIHTSALT VALIMISPETSIIFILINE?

  KOIGE OTSUSTAVAM TEST. Arvutasin KOIK 539 liikuvat 522-nadalast akent
  kogu 1 060-nadalases valimis ja vaatasin, kuhu tegelik 2016-2026
  tulemus nende seas paigutub.

  universum  koik 539 akent                      tegelik 2016-2026  protsentiil
  ---------  ---------------                     -----------------  -----------
  U7         mediaan -1.43bp  min -10.60  max +9.93     +9.70 bp      99.1.
  U28        mediaan +3.15bp  min  -5.37  max +10.36   +10.09 bp      99.3.

  2016-2026 on LIGIKAUDU KOGU VALIMI PARIM VOIMALIK 10-AASTANE AKEN.
  Mediaanne 10-aastane aken annab U7-l -1.43 bp ja U28-l +3.15 bp.

  Aus juhuslik null PIKAL valimil (300 katset, sama selektsioon,
  ainult suund juhuslik):
    U7 : juhuslik mediaan -0.98bp, 95% +4.23bp; tegelik E +0.00bp, p = 0.353
    U28: juhuslik mediaan -2.78bp, 95% +1.53bp; tegelik E +2.62bp, p = 0.013

  U28 labib pikal valimil juhusliku nulli (p = 0.013), AGA tulemus on
  +2.62 bp Sharpe 0.19 maxDD -27.6%, mis on kaubeldamatu, ja ta kaob
  AUD-i eemaldamisel (+0.85 bp). U7 ei labi (p = 0.353).

===============================================================================
8. KAS SUUDI ON VANADE ANDMETE KVALITEEDIS? (ei ole)
===============================================================================

  Kontrollisin, kas 2006-2016 negatiivne tulemus tuleb Yahoo katkistest
  baaridest. Leidsin PARIS vigu: umberpoorduvad hupped 2008-2009.

  Mehaaniline ja summeetriline puhastusreegel (kirjas cot_engine.py-s):
     lipp, kui |r_t| >= 5% JA |r_t + r_(t+1)| <= 30% * |r_t|
  (uhepaevane hupe, mis jargmisel paeval peaaegu taielikult tagasi tuleb)

  LIPUGA PAEVAD — 9 tukki 5 265-st (0.17%), koik 2008-2009:
    EURUSD  2008-01-08 (5.8%), 2008-02-08 (6.9%), 2008-09-07 (5.6%),
            2008-10-07 (9.1%), 2008-12-08 (14.1%)
    USDJPY  2008-04-07 (5.6%), 2008-10-07 (8.7%), 2008-12-08 (15.3%)
    USDCHF  2009-02-06 (8.0%)

  PARIS sundmused jaid PUUTUMATA (nad ei poordu tagasi):
    USDCHF 2011-09-06 +9.2% (SNB porand), 2015-01-16 -17.6% (porand kadus)
    GBPUSD 2016-06-26 -7.9% (Brexit), AUDUSD oktoober 2008 (GFC)

  TULEMUS PARAST PUHASTAMIST — muutub peaaegu mitte midagi:

  variant                    n   keskm_bp  sharpe   kokku%     t      p
  -------                    -   --------  ------   ------     -      -
  U7  C toores             538      -9.41   -0.57    -42.0  -1.83  0.068
  U7  C puhastatud         538      -9.03   -0.55    -40.8  -1.77  0.076
  U7  E toores            1060      +0.00    0.00     -5.8  +0.00  0.999
  U7  E puhastatud        1060      +0.20   +0.01     -3.8  +0.06  0.952
  U28 C toores             538      -4.64   -0.27    -25.1  -0.88  0.379
  U28 C puhastatud         538      -4.48   -0.29    -23.9  -0.95  0.343
  U28 E toores            1060      +2.62   +0.19    +25.4  +0.87  0.386
  U28 E puhastatud        1060      +2.70   +0.21    +27.4  +0.97  0.332

  ANDMEKVALITEET EI OLE SELETUS. Negatiivne 2006-2016 jaab alles.

  Taiendav tervisekontroll (hind toimib, COT toimib):
    osta-ja-hoia   U7  C -1.22bp / D +0.17bp;  U28 C -1.64bp / D +1.12bp
    px-momentum    U7  C -0.06bp / D -1.76bp;  U28 C -2.33bp / D -4.26bp
    signaalitihedus C 26.3%  vs  D 26.4%   (praktiliselt identne)
    puuduvaid net_pct: C 3, D 0

===============================================================================
9. AASTATE KAUPA (A_REV h1, neto)
===============================================================================

  aasta   U7 bp/n   U7 aasta%   U28 bp/n   U28 aasta%   nadalaid
  -----   -------   ---------   --------   ----------   --------
  2006      +2.16       +0.76      -7.47        -2.58         35
  2007      -5.55       -2.90      -5.78        -3.02         53
  2008     -35.85      -16.71     -33.62       -15.75         51
  2009      -9.78       -4.96     +17.75        +9.67         52
  2010      -1.53       -0.79      -6.62        -3.39         52
  2011     -11.98       -6.04      +0.22        +0.11         52
  2012      +2.14       +1.14      +0.16        +0.09         53
  2013      -5.89       -3.02     -12.78        -6.43         52
  2014     -11.60       -5.85      -1.48        -0.77         52
  2015     -11.85       -5.98      +1.81        +0.95         52
  2016     -13.79       -6.92      -2.74        -1.42         52
  -----------------------------------------------------------------
  2017     +13.66       +7.36     +12.10        +6.49         52
  2018      +5.51       +2.96      +9.81        +5.34         53
  2019      +8.81       +4.69     +13.92        +7.51         52
  2020      -2.88       -1.49      +4.32        +2.27         52
  2021     +15.39       +8.33     +14.68        +7.93         52
  2022     +13.19       +7.10     +17.20        +9.36         52
  2023     +15.32       +8.29      +1.32        +0.69         52
  2024     +11.08       +6.05      +7.51        +4.06         53
  2025     +16.73       +9.09     +15.15        +8.19         52
  2026     +10.00       +3.46      +6.95        +2.39         34

  positiivseid aastaid kokku:  U7 11/21   U28 14/21
  2006-2016 (11 aastat):       U7  2/11   U28 4/11
  2017-2026 (10 aastat):       U7  9/10   U28 10/10

  Joon on terav ja see jookseb tapselt seal, kus algne valim algas.

  LISA: 2008 EI OLE seletus.
    U7  C 2006-2016 taielik -9.41bp; ilma 2008 -6.64bp; ilma 2008-09 -6.26bp
    U28 C 2006-2016 taielik -4.64bp; ilma 2008 -1.60bp; ilma 2008-09 -3.91bp
    Ka ilma kriisiaastateta jaab C negatiivseks.

===============================================================================
10. OTSUSEREEGEL JA KLASSIFIKATSIOON
===============================================================================

  Sinu etteantud reegel:
  "If the older period is negative and the recent period is positive,
   explicitly classify the COT edge as SAMPLE-DEPENDENT / NOT ROBUST"

  vanem periood C 2006-2016   NEGATIIVNE   (U7 -9.41 bp, U28 -4.64 bp)
  uuem periood  D 2016-2026   POSITIIVNE   (U7 +9.70 bp, U28 +10.09 bp)

  => tingimus taidetud sonasonalt.

  A1 RESULT:   FAIL

  COT STATUS:  SAMPLE-DEPENDENT

===============================================================================
11. MIDA SEE PRAKTIKAS TAHENDAB
===============================================================================

  1. KOKKUVOTE_COT.md klassifikatsioon "PROMISING BUT NOT PROVEN" tuleb
     alandada. A1 oli taielikult otsustav ja see oli kaigu odavaim test
     (30 min andmetombeks, 8 s arvutuseks).

  2. A2 (TFF-aruanne), A3 (Deflated Sharpe), A4 (ortogonaalne komponent)
     ja A5 (taitevus suuremal kontol) on nuud MOTTETUD. Nad koik
     eeldasid, et alusefekt on paris. Ei ole.

  3. Kolm asja, mida see uurimisring ikkagi ANDIS ja mis jaavad alles:
     - toimiv CFTC-andmetee (Supabase http -> cot_legacy -> CSV)
     - auditeeritud nadalane portfellimootor no-lookahead ajastusega
     - mehaaniline hinnaspike-puhasti, mis leidis Yahoo seeriast 9
       katkist baari 2008-2009 (EURUSD, USDJPY, USDCHF)
     Need on taaskasutatavad mis tahes nadalase valise infoallika jaoks,
     sealhulgas majanduskalendri kategooria jaoks.

  4. Uldine ope, mis laheb master-kaardile: iga tulevane leid TULEB
     kohe testida pikimal saadaoleval valimil ENNE robustsustestide
     kirjutamist. Ma kirjutasin 9 skripti ja 832 rida kokkuvotet
     efektile, mille 8-sekundiline test oleks tapnud.

  5. NEMSIS-i uldseis EI MUUTU: endiselt ei ole leitud uhtegi robustset
     serva. Testide koguarv tousis ~11 650 -> ~11 700.

  MIDA EI TEHTUD:
     live-faile ei muudetud, /update ei saadetud, strateegiat ei
     optimeeritud, A2-A5 ei alustatud.

===============================================================================
KOOD JA ANDMED
===============================================================================
  bot/sb_d25.py             pikkade _d25 seeriate konverter
  bot/cot_a1.py             perioodid A-E, jarjepidevuskontroll
  bot/cot_a1b.py            falsifitseerimiskusimused Q1-Q7
  bot/cot_engine.py         + sufiks-lyliti, + puhasta_spike()
  bot/cot_run.py            + sufiks/puhasta parameetrid
  bot/data/{PAAR}_d25.csv   7 paari, 2003-2026 (gitignore'itud)
  bot/data/cot_legacy.csv   12 160 rida, 2000-2026 (commititud)
===============================================================================
```
