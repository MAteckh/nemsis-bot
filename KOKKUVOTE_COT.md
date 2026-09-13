```
===============================================================================
NEMSIS — CFTC COT POSITSIONEERIMISE UURING
===============================================================================
  kuupaev 2026-09-13   koodiharu claude/great-noether-um7382
  LIVE PUUTUMATA: main_v4.py / config.py / mt5_connector.py /
  strategy_meanrev.py / backtest.py EI OLE muudetud. /update EI saadetud.

===============================================================================
1. KOKKUVOTE JUHILE
===============================================================================

  KUSIMUS: kas avalik CFTC COT positsioneerimine sisaldab FX-tootluste kohta
  infot, mida OHLC-hinnas EI OLE?

  VASTUS: JAH, tousb esimest korda 11 650 senise testi jarel noore ule.

  Ekstreemse spekulatiivse positsioneerimise FADE (A_REV) — shordi valuutat,
  mille suured spekulandid on ostnud oma 3 aasta korgeima detsiili sisse,
  ja osta seda, mille nad on muunud madalaima detsiili sisse — annab

     U28 (28 paari) +10.09 bp/nadal neto, Sharpe 1.13, t = 3.58, p = 0.0004
     U7  (7 paari)   +9.80 bp/nadal neto, Sharpe 0.78, t = 2.48, p = 0.013

  ja labib peaaegu koik NEMSIS-i robustsuskontrollid: 11/11 aastat positiivne,
  koik kolm TRAIN/VALID/OOS akent positiivsed, 28/28 paari positiivsed,
  TOP-1 paar ainult 10.9% kasumist, elab ule iga valuuta eemaldamise,
  elab ule 8bp kulu, carry-lohk praktiliselt null.

  AGA: strateegia EI OLE 205 EUR kontol teostatav. Miinimumlot 0.01 annab
  0/7 paaril kavatsetud 0.25% riski ja 0/7 paaril isegi 0.50% riski.
  Vajalik konto on 2 903 EUR (0.50% risk) kuni 5 806 EUR (0.25% risk).

  Lisaks kukub labi kaks statistilist tugevusproovi: Deflated Sharpe
  p = 0.0755 (vaja > 0.95) ja hinnast TAIELIKULT ortogonaliseeritud
  komponent annab t = 1.87 (ei ulata 5% lavini).

  OTSUS: PROMISING BUT NOT PROVEN.
  See ei ole roheline tuli. See on esimene kandidaat, mis vaarib
  jargmist uurimisringi — ja mida EI SAA sellel kontol kaubelda.

===============================================================================
2. TAPNE ANDMEALLIKAS
===============================================================================

  dataset      CFTC Public Reporting Environment, Socrata "6dca-aqww"
               "Commitments of Traders - Legacy Futures Only"
  URL          https://publicreporting.cftc.gov/resource/6dca-aqww.json
  tee          liivakastil pole otseuhendust cftc.gov-iga (agent-proxy 403,
               kinnitatud: connect_rejected publicreporting.cftc.gov:443).
               Kasutaja Supabase'i `http` laiendus tegi paringu; tulemus
               laeti tabelisse cot_legacy ja eksporditi CSV-ks.
  konverter    bot/sb_cot.py -> bot/data/cot_legacy.csv
  ridu         10 565 (2004-01-06 .. 2026-09-08)
  sagedus      nadalane
  tuup         FUTUURIPOSITSIOONID (CME), MITTE spot-FX positsioonid
  kauplejate   noncommercial (suured spekulandid) — primaarne
  kategooriad  commercial (hedgerid) — laetud, kasutamata
               nonreportable (vaikesed) — laetud, kasutamata

  kontraktid ja ajalugu (koik kuni 2026-09-08):

  valuuta   CFTC kood   nimi                   vaatlusi   algus
  -------   ---------   ----                   --------   -----
  EUR       099741      EURO FX                    1393   1986-01-15
  GBP       096742      BRITISH POUND              1393   1988-04-29
  JPY       097741      JAPANESE YEN               1393   1986-01-15
  CHF       092741      SWISS FRANC                1391   1986-01-15
  CAD       090741      CANADIAN DOLLAR            1393   1986-01-15
  AUD       232741      AUSTRALIAN DOLLAR          1366   1987-01-30
  NZD       112741      NZ DOLLAR                  1112   1999-01-05
  MXN       095741      MEXICAN PESO               1393   1995-05-23
  USDX      098662      USD INDEX                  1328   1992-05-29

  PUUDUVAD VAATLUSED (kogu ajalugu): CHF 2, AUD 2, NZD 86, ulejaanud 0.
  Kauplemisaknas (2016-09 .. 2026-09) on puuduvaid vaatlusi 0 — koik
  NZD augud on enne 2016. Rullpertsentiil viskab NaN-id enne akna
  moodustamist valja (vt bot/cot_engine.py rull_pertsentiil).

  MXN VALJA JAETUD: kettal ei ole USDMXN hinnaseeriat. Ei leiutatud.
  USDX kasutatud AINULT robustsusvariandina (vt sektsioon 13).

  HINNAANDMED
    bot/data/*_d.csv, Yahoo Finance paevased sulgemishinnad
    2016-09-12 .. 2026-09-11, 2 601 kauplemispaeva = 523 COT-nadalat
    7 paari paris seeriaga: EURUSD GBPUSD AUDUSD NZDUSD USDJPY USDCHF USDCAD

  KASUTATAV VAHEMIK on seega 2016-09 .. 2026-09 (10.00 aastat), sest
  HINNASEERIA on luhem kui COT-ajalugu. COT-ajalugu 2004-st kasutatakse
  AINULT 156-nadalase rullpertsentiili soojenduseks — seetottu on signaal
  taielik juba esimesest kauplemisnadalast (2016-09-12), ilma et kaotaks
  3 aastat valimit.

===============================================================================
3. AVALDAMISE AJASTUS — NO-LOOKAHEAD METOODIKA
===============================================================================

  CFTC reeglid:
    vaatlusaeg  = TEISIPAEV, turu sulgemine
    avaldamine  = sama nadala REEDE 15:30 ET
    st info on avalik 3 paeva PARAST vaatlust

  NEMSIS-i valik: esimene kaubeldav hind = ESMASPAEVA sulgemine,
  st report_date + vahemalt 6 kalendripaeva.

  See on KONSERVATIIVSEM kui noutav. Reede 15:30 ET oleks juba lubatud
  (FX on lahti kuni 17:00 ET), aga esmaspaev valistab koik
  pupliseerimisviivituse-, ajavoondi- ja suikeaja-kusimused.

  Pyhade tottu on 21/1393 aruannet nihkes (esmaspaev voi kolmapaev).
  Seetottu EI kasutata fikseeritud nadalapaeva, vaid
  "esimene kauplemispaev alates report_date + 6 paeva".

  MOODETUD (audit A2): viive min 6 paeva, mediaan 6 paeva, max 13 paeva.
  Sisenemispaev on esmaspaev 99.6% juhtudest.

  KAITSE: sisenemispaevad, mille jaoks ei leidu hinnapaeva 14 paeva
  jooksul, VISATAKSE VALJA. Ilma selleta seotaks koik 2004-2016 aruanded
  esimese olemasoleva hinnapaevaga ja tekiks vale signaal. (See viga oli
  esimeses versioonis olemas — audit A2 naitas mediaanviivet 496 paeva —
  ja parandati enne uhtegi tulemust.)

  AJASTUSE TUNDLIKKUS (U28 A_REV h1, neto):

  viive   sisenemine              keskm_bp   sharpe      t
  -----   ----------              --------   ------      -
   3 d    reede (release-paev)       +8.34     0.96    3.05
   6 d    esmaspaev (NEMSIS)        +10.09     1.13    3.58
   7 d    teisipaev +1p              +8.76     0.98    3.11
   9 d    kolmapaev +3p              +8.85     1.02    3.23
  13 d    jargmine esmaspaev         +7.28     0.77    2.45

  JARELDUS: serv EI SOLTU sellest, kui kiiresti siseneme. See on tugev
  argument SELLE VASTU, et tegu oleks lookahead-artefaktiga — artefakt
  kaoks kohe, kui viivet suurendada.

===============================================================================
4. SIGNAALIDE TAPSED DEFINITSIOONID (eelregistreeritud)
===============================================================================

  Koik parameetrid on kirjas bot/cot_engine.py paises ENNE esimest jooksu.

  positsioonimoot:
      net_pct(c,t) = (noncomm_long - noncomm_short) / open_interest

  standardiseerimine:
      P(c,t) = osakaal viimase 156 nadala (3 a) vaatlustest, mis on
               VAIKSEMAD kui kaesolev. Aken lopeb kaesoleva reaga =>
               kasutab ainult minevikku + kaesolevat avaldatud vaatlust.

  A) EXTREME POSITIONING
      skoor(c,t) = +1  kui P >= 0.90      (korgeim detsiil)
                   -1  kui P <= 0.10      (madalaim detsiil)
                    0  muidu
      Lavid 0.90/0.10 on FIKSEERITUD ette, mitte tulemuste jargi valitud.

  B) POSITIONING CHANGE
      d(c,t) = net_pct(c,t) - net_pct(c,t-1)
      ristloikeline jarjestus 8 valuuta seas:
      skoor = +1 kahele suurimale tousule, -1 kahele suurimale langusele.

  C) EXTREME + PRICE CONFIRMATION
      A-signaal jaab alles AINULT seal, kus 12-nadalane hinnamomentum
      (ristloikeliselt tsentreeritud) on SAMAS suunas kui kavandatud
      tehing. Uks eelregistreeritud hinnakomponent, mitte indikaatorigrid.

  D) SUUND — MOLEMAD testitud, kumbki ei olnud ette eeldatud
      CONT = mine positsioneerimisega kaasa
      REV  = mine positsioneerimise vastu

  hoideperioodid: 1, 2, 4 nadalat. Ainult need. Rohkem ei optimeeritud.

  KOKKU: 6 signaali x 3 hoidu x 2 universumit = 36 varianti.

  USD-SKOOR. USD-l ei ole CME-s oma FX-futuuri koigi valuutade vastu.
  Koik CME FX-kontraktid on kvoteeritud USD vastu, seega pikk EUR-futuur
  ON luhike USD. Eelregistreeritud primaarne definitsioon:
      net_pct(USD) = - (7 ulejaanud valuuta net_pct keskmine)
  Robustsusvariant kasutab USD-indeksi futuuri (098662) — vt sektsioon 13.

===============================================================================
5. FX-PAARIDE KONSTRUKTSIOON
===============================================================================

  paari signaal:
      sig(XXXYYY) = sign( skoor(XXX) - skoor(YYY) )

  Nait: kui EUR on ekstreemselt pikk (skoor +1, REV => -1) ja USD on
  ekstreemselt luhike (skoor -1, REV => +1), siis
  sig(EURUSD) = sign(-1 - (+1)) = -1 => SHORDI EURUSD.

  kaalud hoideperioodiga h:
      W = h viimase nadala sig keskmine (kattuvad positsioonid),
      normeeritud nii et sum|W| = 1 (bruto ekspositsioon = 1x konto)

  UNIVERSUMID
    U7  = 7 paari, mille hinnaseeria on kettal PARIS kujul
          EURUSD GBPUSD AUDUSD NZDUSD USDJPY USDCHF USDCAD
          => PRIMAARNE universum, paris hinnad, paris spread'id
    U28 = koik 28 paari 8 valuuta seast. Ristid (nt EURJPY) on
          arvutatud USD-jalgadest: hind(XY) = V(X)/V(Y), kus V(c) on
          1 uhiku c vaartus USD-des.

  U28 EI OLE "rohkem infot" — 8 valuutat annavad 7 soltumatut
  riskitegurit, seega U28 on sisuliselt sama info SILUTUD kaaludega.
  Ta on parem hajutus, aga 28 paari kauplemine on vaikesel kontol
  fusiliselt voimatu. Seepargi on U7 aus primaarne tulemus.

  SUNTEETILISE RISTI KONTROLL (audit A4): sunteetiline EURJPY vs PARIS
  EURJPY_d seeria — mediaan hinnaviga 0.008%, paevatootluste
  korrelatsioon 0.9946. Konstruktsioon on korrektne.

===============================================================================
6. NO-LOOKAHEAD AUDIT — 16 kontrolli, 0 viga
===============================================================================

  kood: bot/cot_audit.py   (jooksutatav: python3 cot_audit.py)

  A1  COT ridu                               10 565 rida, 9 valuutat      OK
  A1  vahemik                                2004-01-06 .. 2026-09-08     OK
  A1  net_pct vahemikus [-1,1]               max|net_pct| = 0.863         OK
  A1  puuduvad vaatlused loendatud           CHF 2, AUD 2, NZD 86         OK
  A2  sisenemine >= report + 6 paeva         min 6d, med 6d, max 13d      OK
  A2  sisenemispaev on nadala algus          esmaspaev 99.6%              OK
  A3  kasvav seeria -> pertsentiil 1.0                                    OK
  A3  kahanev seeria -> pertsentiil 0.0                                   OK
  A3  TULEVIKU MUUTMINE EI MUUDA MINEVIKKU                                OK
  A3  warmup NaN kuni aken taidetud                                       OK
  A4  sunteetiline EURJPY ~ paris EURJPY     viga 0.008%, korr 0.9946     OK
  A5  +1%/nadal, kaal +1 -> log(1.01)        0.00995033 = 0.00995033      OK
  A5  kaalu margi pooramine pooral tootluse                               OK
  A6  0bp: neto == bruto                                                  OK
  A6  1bp, |dw|=2 -> kulu 2bp nadalas        2.0000 bp                    OK
  A7  teisipaeva aruanne -> esmaspaev        2024-03-05 -> 2024-03-11     OK

  KAKS VIGA LEITI JA PARANDATI ENNE TULEMUSTE VAATAMIST:
    1. sisenemispaevade sidumine ilma max_nihe piiranguta seoks koik
       2004-2016 aruanded esimese hinnapaevaga (mediaanviive 496 paeva)
    2. portfelli tootlus luges puuduva tootlusega rea nulliks, mitte
       NaN-iks (A5 andis 0.00978 oodatud 0.00995 asemel)

  KOLMAS VIGA leiti hiljem ja parandati: Deflated Sharpe valemis puudus
  katsete-ulene Sharpe standardhalve tegur, mis andis absurdse SR* = 2.15
  nadalas. Parandatud valem: SR* = sd(SR) * [(1-y)Z(1-1/N) + y Z(1-1/Ne)].

===============================================================================
7. KOIK 36 EELREGISTREERITUD VARIANTI (neto, NEMSIS BASE kulud)
===============================================================================

  variant           n   keskm_bp  sharpe   kokku%  maxdd%     pf    wr%      t      p
  -------           -   --------  ------   ------  ------     --    ---      -      -
  U7 A_CONT h1    522     -10.84   -0.86    -44.4   -46.1   0.70   38.3  -2.73  0.006
  U7 A_CONT h2    522      -9.64   -0.79    -40.8   -42.2   0.73   40.4  -2.50  0.012
  U7 A_CONT h4    522      -7.98   -0.69    -35.3   -35.9   0.77   42.1  -2.18  0.029
  U7 A_REV  h1    522      +9.80   +0.78    +63.3   -11.6   1.39   46.9  +2.48  0.013
  U7 A_REV  h2    522      +8.80   +0.72    +55.1   -14.5   1.33   49.6  +2.28  0.022
  U7 A_REV  h4    522      +7.36   +0.63    +44.2   -17.7   1.27   52.7  +2.01  0.044
  U7 B_CONT h1    522      -1.06   -0.10     -6.8   -17.0   0.96   48.1  -0.31  0.756
  U7 B_CONT h2    522      -0.37   -0.03     -3.7   -14.4   0.99   47.3  -0.10  0.918
  U7 B_CONT h4    522      -1.86   -0.16    -10.8   -19.5   0.94   44.1  -0.52  0.606
  U7 B_REV  h1    522      -1.93   -0.18    -11.0   -20.5   0.93   48.7  -0.57  0.569
  U7 B_REV  h2    522      -2.07   -0.18    -11.8   -20.6   0.93   51.0  -0.57  0.566
  U7 B_REV  h4    522      +0.26   +0.02     -0.4   -15.5   1.01   54.2  +0.07  0.943
  U7 C_CONT h1    522      -4.55   -0.42    -22.4   -24.3   0.83   32.2  -1.32  0.187
  U7 C_CONT h2    522      -6.22   -0.55    -29.0   -31.4   0.80   35.8  -1.75  0.080
  U7 C_CONT h4    522      -6.22   -0.55    -29.0   -30.8   0.81   39.7  -1.75  0.080
  U7 C_REV  h1    522      +7.21   +0.67    +43.5    -9.5   1.47   23.9  +2.14  0.033
  U7 C_REV  h2    522      +9.93   +0.82    +64.6    -9.6   1.51   31.0  +2.59  0.010
  U7 C_REV  h4    522      +9.96   +0.78    +64.5    -9.9   1.42   37.7  +2.46  0.014
  U28 A_CONT h1   522     -11.87   -1.33    -46.8   -48.2   0.59   36.2  -4.21  0.000
  U28 A_CONT h2   522     -10.97   -1.24    -44.2   -45.8   0.62   38.9  -3.93  0.000
  U28 A_CONT h4   522      -9.25   -1.09    -38.9   -41.0   0.66   40.8  -3.46  0.001
  U28 A_REV  h1   522     +10.09   +1.13    +67.4    -5.0   1.57   48.3  +3.58  0.000
  U28 A_REV  h2   522      +9.59   +1.08    +63.2    -5.6   1.53   50.6  +3.43  0.001
  U28 A_REV  h4   522      +8.24   +0.97    +52.2    -4.4   1.44   53.4  +3.07  0.002
  U28 B_CONT h1   522      -4.72   -0.67    -22.3   -26.6   0.78   45.6  -2.13  0.033
  U28 B_CONT h2   522      -6.13   -0.78    -28.0   -30.9   0.74   44.1  -2.49  0.013
  U28 B_CONT h4   522      -5.37   -0.75    -25.0   -28.0   0.76   44.6  -2.39  0.017
  U28 B_REV  h1   522      -0.10   -0.01     -1.2   -11.5   0.99   49.2  -0.05  0.963
  U28 B_REV  h2   522      +1.92   +0.25     +9.6    -7.6   1.10   52.1  +0.78  0.437
  U28 B_REV  h4   522      +2.58   +0.36    +13.6    -7.1   1.14   52.7  +1.15  0.252
  U28 C_CONT h1   522      -6.82   -0.83    -30.6   -31.0   0.70   31.2  -2.62  0.009
  U28 C_CONT h2   522      -7.37   -0.85    -32.7   -33.0   0.70   35.6  -2.69  0.007
  U28 C_CONT h4   522      -7.20   -0.85    -32.0   -32.7   0.72   40.0  -2.69  0.007
  U28 C_REV  h1   522      +4.77   +0.61    +27.2    -6.6   1.41   23.9  +1.93  0.053
  U28 C_REV  h2   522      +6.41   +0.75    +38.4    -6.7   1.44   32.2  +2.37  0.018
  U28 C_REV  h4   522      +6.61   +0.73    +39.6    -4.9   1.38   38.9  +2.30  0.021

  MIDA SEE UTLEB
    A (ekstreemne tase)  : TUGEV ja jarjekindel, REV-suunas, koigil hoidudel
    B (nadalane muutus)  : EI TOOTA kummaski suunas (koik |t| < 2.5, enamik <1)
    C (A + hinnakinnitus): tootab, AGA HALVEMINI kui puhas A
                           => hinnakinnitus EI PARANDA, vaid KAHJUSTAB.
                           See on omaette tahtis tulemus: serv EI TULE hinnast.
    D (suund)            : REV on oige suund, CONT on peegelpilt ja kaotab.

===============================================================================
8. PARIMA VARIANDI TAISSTATISTIKA
===============================================================================

                              U7 A_REV h1        U28 A_REV h1
  ------------------------    -----------        ------------
  vaatlusi (nadalat)                  522                 522
  aastaid                           10.00               10.00
  signaale (nadal x paar)            1518                5922
  tehinguid                          1517                5915
  tehinguid aastas                    152                 591
  voiduprotsent                     52.5%               51.2%
  keskmine voit                   +90.3 bp            +87.9 bp
  keskmine kaotus                 -87.6 bp            -81.6 bp
  oodatav vaartus / tehing         +5.8 bp             +5.2 bp
  bruto / tehing                   +8.3 bp             +9.3 bp
  kulu / tehing                     2.5 bp              4.2 bp
  keskm nadalane BRUTO            +10.32 bp           +10.98 bp
  keskm nadalane KULU              -0.52 bp            -0.89 bp
  keskm nadalane NETO              +9.80 bp           +10.09 bp
  kogutootlus BRUTO                 +71.4%              +77.4%
  kogutootlus NETO                  +63.3%              +67.4%
  CAGR (neto)                        5.02%               5.29%
  Sharpe (aastastatud)                0.78                1.13
  max drawdown                      -11.6%               -5.0%
  profit factor                       1.39                1.57
  t-statistik                        +2.48               +3.58
  p (kahepoolne)                     0.013              0.0004
  Newey-West t (4 lag)               +2.72               +3.99
  skew / kurtoos                +0.97 / 5.58       +0.52 / 2.58
  nadalane kaive sum|dw|             0.409               0.423

  Hoiuga 2 ja 4 nadalat on tehingutasandi ootus SUUREM (U7 h4: +41.1 bp
  tehingu kohta), sest kulu jaguneb pikemale hoiule. Portfellitasandil on
  h1 siiski parim, sest kattuvus vahendab hajutust.

===============================================================================
9. KULUTUNDLIKKUS
===============================================================================

  Kaive on VAIKE: sum|dw| = 0.41-0.42 nadalas. Seega 1bp uhesuunalist kulu
  maksab ainult ~0.42 bp nadalas. See on COT-strateegia suur eelis
  H1-strateegiate ees, kus kaive oli 50-200x suurem.

  kulu (uhesuunaline bp)   U7 keskm_bp   U7 sharpe   U28 keskm_bp  U28 sharpe    t(U28)
  ----------------------   -----------   ---------   ------------  ----------    ------
   0 bp                         +10.32        0.82         +10.98        1.23      3.89
   1 bp                          +9.91        0.79         +10.56        1.18      3.74
   2 bp                          +9.50        0.76         +10.13        1.13      3.59
   3 bp                          +9.09        0.72          +9.71        1.09      3.44
   5 bp                          +8.27        0.66          +8.86        0.99      3.14
   8 bp                          +7.04        0.56          +7.59        0.85      2.69
  NEMSIS BASE (paaripohine)      +9.80        0.78         +10.09        1.13      3.58
  NEMSIS HIGH (2x BASE)          +9.28        0.74          +9.19        1.03      3.26

  JARELDUS: kulu EI OLE selle strateegia surm. Isegi 8bp uhesuunalise
  spread'iga (= 16bp edasi-tagasi, oluliselt halvem kui BlackBulli
  tegelik retail-spread) jaab t = 2.69.

  CARRY (bot/data/policy_rates.csv, BIS WS_CBPOL, 2016-2026):
    keskpanga carry U7  -0.40 bp/nadal = -0.21 %/aastas
    keskpanga carry U28 -0.11 bp/nadal = -0.06 %/aastas
    spot + carry U28    +9.98 bp/nadal, Sharpe 1.11, t = 3.53
    MURDEPUNKT brokeri juurdehindlus: 5.68 %/a/jalg (U7), 6.03 %/a/jalg (U28)

  See on TAHTIS ja OOTAMATU. A_REV shordib rahvamassi lemmikut, mis on
  tavaliselt korge intressiga valuuta => oodata voiks tugevat negatiivset
  carry't. Tegelikult on see praktiliselt null, sest positsioonid on
  ristloikeliselt tasakaalus. Vordluseks: NEMSIS v6 carry-strateegia
  murdepunkt oli 1.49 %/a/jalg ja kukkus labi. Siin on varu 4x suurem.

===============================================================================
10. TRAIN / VALIDATION / FINAL OOS
===============================================================================

  TRAIN      2016-09-12 .. 2020-08-31   209 nadalat
  VALIDATION 2020-09-01 .. 2023-08-31   157 nadalat
  FINAL OOS  2023-09-01 .. 2026-09-07   156 nadalat

  FINAL OOS-i avati UKS KORD. Uhtegi parameetrit ei valitud selle jargi —
  koik (156n aken, 0.90/0.10 lavid, 12n momentum, hoiud 1/2/4, 6p viive)
  olid kirjas cot_engine.py-s enne esimest jooksu.

  variant             periood   n   keskm_bp  sharpe      t      p
  -------             -------   -   --------  ------      -      -
  U7  A_REV h1        TRAIN   209      +6.80    0.53   1.06  0.290
  U7  A_REV h1        VALID   157      +8.46    0.65   1.13  0.259
  U7  A_REV h1        OOS     156     +15.17    1.30   2.26  0.024
  U7  A_REV h2        TRAIN   209      +9.63    0.77   1.55  0.122
  U7  A_REV h2        VALID   157      +1.73    0.14   0.24  0.808
  U7  A_REV h2        OOS     156     +14.81    1.27   2.19  0.028
  U7  A_REV h4        TRAIN   209      +6.05    0.53   1.06  0.291
  U7  A_REV h4        VALID   157      +1.83    0.15   0.25  0.800
  U7  A_REV h4        OOS     156     +14.68    1.37   2.37  0.018
  U28 A_REV h1        TRAIN   209     +11.52    1.16   2.33  0.020
  U28 A_REV h1        VALID   157      +7.79    0.87   1.51  0.131
  U28 A_REV h1        OOS     156     +10.47    1.40   2.43  0.015
  U28 A_REV h2        TRAIN   209     +13.38    1.41   2.83  0.005
  U28 A_REV h2        VALID   157      +4.70    0.53   0.92  0.356
  U28 A_REV h2        OOS     156      +9.44    1.19   2.06  0.040
  U28 A_REV h4        TRAIN   209      +9.83    1.07   2.15  0.032
  U28 A_REV h4        VALID   157      +5.33    0.64   1.11  0.265
  U28 A_REV h4        OOS     156      +9.03    1.17   2.03  0.042

  KOIK 18 LAHTRIT POSITIIVSED. Koik 6 FINAL OOS lahtrit statistiliselt
  olulised (p < 0.05). VALID on norgim perioodid (2020-2023) — see on
  jarjekindlalt norgem aken, mitte juhuslik kohin.

  AASTATE KAUPA (neto, A_REV h1):

  aasta   U28 bp/n   U28 aasta%   U7 bp/n   U7 aasta%   nadalaid
  -----   --------   ----------   -------   ---------   --------
  2016       +1.01        +0.18    -15.25       -2.71         18
  2017      +12.09        +6.49    +13.66       +7.36         52
  2018       +9.82        +5.34     +5.53       +2.97         53
  2019      +13.92        +7.51     +8.80       +4.68         52
  2020       +4.32        +2.27     -2.88       -1.48         52
  2021      +14.68        +7.93    +15.39       +8.33         52
  2022      +17.21        +9.36    +13.20       +7.10         52
  2023       +1.33        +0.69    +15.32       +8.29         52
  2024       +7.51        +4.06    +11.08       +6.05         53
  2025      +15.14        +8.19    +16.73       +9.09         52
  2026       +6.94        +2.39     +9.99       +3.46         34

  U28: 11/11 aastat positiivne.  U7: 9/11 (2016 osaline, 2020 negatiivne).

===============================================================================
11. JUHUSLIK BASELINE — SAMA SELEKTSIOON
===============================================================================

  See on NEMSIS-i koige tahtsam kontroll. Varasemas toos tehti just siin
  koige suurem viga (best-of-252 vordlemine UHE juhusliku sisenemisega).

  Meetod: SAMAD nadalad, SAMA arv positsioone, SAMA hoideperiood, SAMA
  kulumudel, SAMAD paarid — AINULT SUUND on juhuslik (Rademacher).

  R2  valitud variandi null (U28 A_REV h1, 500 katset):
      juhuslik mediaan  -2.08 bp
      juhuslik 95%      +2.30 bp
      juhuslik max      +5.19 bp
      TEGELIK          +10.09 bp
      empiiriline p = 0.0000  (0/500 juhuslikku ulatas tegelikuni)

  R1  AUS best-of-36 null (18 struktuuri x 2 suunda, 500 katset):
      Iga katse jaoks arvutati KOIGI 18 struktuuri juhuslik Sharpe ja
      voeti maksimum absoluutvaartuselt — tapselt see valik, mille MINA
      tegin.
      juhuslik parim-36-st mediaan  0.1040 (nadalane Sharpe)
      juhuslik parim-36-st 95%      0.1473
      juhuslik parim-36-st max      0.2168
      TEGELIK parim                 0.1567
      empiiriline p = 0.0280

  Tegelik tulemus ULETAB aus best-of-36 nulli 95. protsentiili, aga
  mitte suure varuga. See on parim voimalik vordlus ja see LABITAKSE,
  aga napilt.

===============================================================================
12. OHLC-BASELINE — KAS SEE ON MASKEERITUD HINNASTRATEEGIA?
===============================================================================

  See on uurimuse KESKNE kusimus. Spekulandid jalitavad trendi, seega
  ekstreemne positsioon on korreleeritud varasema hinnaliikumisega.

  12a  Juba testitud perekond: ristloikeline hinnamomentum, SAMA struktuur

  variant                  keskm_bp   sharpe       t       p
  -------                  --------   ------       -       -
  U7  osta-ja-hoia            +0.18     0.03    0.10   0.924
  U28 osta-ja-hoia            +1.09     0.16    0.52   0.602
  U7  px-mom h1               -1.45    -0.14   -0.43   0.667
  U7  px-mom REV h1           +0.27     0.03    0.08   0.937
  U7  px-mom h4               -2.94    -0.27   -0.86   0.392
  U7  px-mom REV h4           +2.29     0.21    0.67   0.505
  U28 px-mom h1               -4.32    -0.54   -1.71   0.088
  U28 px-mom REV h1           +2.49     0.31    0.99   0.324
  U28 px-mom h4               -4.50    -0.55   -1.75   0.079
  U28 px-mom REV h4           +3.41     0.42    1.33   0.183

  12b  TAPSELT SAMA MASINAVARK, hinnapohine sisend
       (156n rullpertsentiil hinnamomentumist -> ekstreemsed detsiilid -> REV)

  variant              keskm_bp   sharpe       t       p
  -------              --------   ------       -       -
  U28 PX12_REV h1         -0.20    -0.03   -0.08   0.933
  U28 PX26_REV h1         -0.94    -0.12   -0.37   0.712
  U28 PX52_REV h1         +2.86    +0.43   +1.35   0.176
  U28 COT_REV h1 (COT)   +10.09    +1.13   +3.58   0.000

  Hinnapohine analoog annab -0.94 .. +2.86 bp. COT annab +10.09 bp.
  ERINEVUS ON 3-10 KORDA.

  12c  Korrelatsioon COT-pertsentiili ja 26n hinnamomentumi-pertsentiili vahel
       USD +0.57  EUR +0.49  GBP +0.68  JPY +0.32  CHF -0.02
       CAD +0.58  AUD +0.44  NZD +0.52     keskmine +0.447

  12d  Ortogonaliseerimine: r_COT = alfa + beeta * r_PX26REV
       beeta          +0.279
       alfa          +10.35 bp/nadal   t = +3.79   p = 0.0002
       korr(COT, PX)  +0.251

  12e  TAIELIK ortogonaliseerimine sisendi tasandil
       net_pct regresseeriti expanding-OLS-iga tema enda valuuta 4/12/26/52
       nadala hinnamomentumile; JAAK laks labi tapselt sama masinavarga.

       R2: kui palju hinnamomentum net_pct-st seletab
       USD -0%  EUR 47%  GBP 39%  JPY 30%  CHF 10%  CAD 29%  AUD 42%  NZD 35%
       keskmine 29%  =>  71% net_pct-st on hinnast SOLTUMATU

       variant                        keskm_bp  sharpe      t      p
       U28 A_REV algne                  +10.09    1.13   3.58  0.000
       U28 A_REV ORTOGONAALNE jaak       +3.20    0.59   1.87  0.061
       U7  A_REV algne                   +9.80    0.78   2.48  0.013
       U7  A_REV ORTOGONAALNE jaak       +5.03    0.57   1.80  0.071

  JARELDUS: COT EI OLE maskeeritud OHLC-strateegia — hinnapohine analoog
  annab peaaegu nulli ja alfa hinnapohise jarel on +10.35 bp (t=3.79).
  AGA rangelt hinnast ortogonaliseeritud komponent UKSI annab t = 1.80-1.87,
  mis EI ULATA 5% lavini. Aus tolgendus: serv tuleb positsioneerimise ja
  hinna KOOSMOJUST, kusjuures positsioneerimine kannab enamiku infost,
  kuid puhtalt hinnast soltumatu osa ei ole eraldi voetuna toestatud.

===============================================================================
13. ROBUSTSUSTESTID
===============================================================================

  13a  EEMALDA VALUUTA (U28 A_REV h1, neto)

  variant                keskm_bp   sharpe       t       p
  -------                --------   ------       -       -
  koik                     +10.09     1.13    3.58   0.000
  ilma USD                 +10.44     1.11    3.50   0.000
  ilma EUR                 +10.91     1.15    3.65   0.000
  ilma GBP                  +9.99     1.13    3.57   0.000
  ilma JPY                  +6.08     0.69    2.18   0.029   <- norgim
  ilma CHF                  +9.58     1.02    3.25   0.001
  ilma CAD                  +8.22     0.89    2.81   0.005
  ilma AUD                  +8.27     0.97    3.06   0.002
  ilma NZD                  +9.72     1.10    3.48   0.001

  KOIK POSITIIVSED, koik p < 0.03. Halvim juht (ilma JPY-ta) kaotab 40%
  servast, aga jaab oluliseks.

  13b  EEMALDA PAAR

  U28 ilma parima paarita (JPYAUD)   +9.36 bp, Sharpe 1.08, t = 3.41
  U7  ilma EURUSD  +10.62 / ilma GBPUSD +9.46 / ilma AUDUSD +8.06
  U7  ilma NZDUSD   +7.23 / ilma USDJPY +7.44 / ilma USDCHF +9.17
  U7  ilma USDCAD   +8.74        => koik 7 eemaldust jaavad positiivseks

  13c  LAVITUNDLIKKUS (U28 h1) — EI OLE optimeerimine, robustsuskontroll

  lavi          keskm_bp   sharpe       t       p
  ----          --------   ------       -       -
  0.05 / 0.95      +4.18     0.51    1.61   0.108
  0.10 / 0.90     +10.09     1.13    3.58   0.000   <- eelregistreeritud
  0.15 / 0.85      +6.44     0.78    2.47   0.013
  0.20 / 0.80      +7.44     0.91    2.90   0.004
  0.25 / 0.75      +5.56     0.72    2.29   0.022

  13d  PERTSENTIILIAKEN

  aken     keskm_bp   sharpe       t       p
  ----     --------   ------       -       -
  104 n       +3.20     0.36    1.15   0.249   <- KUKUB LABI
  156 n      +10.09     1.13    3.58   0.000   <- eelregistreeritud
  260 n       +7.64     0.90    2.86   0.004

  13e  MUUD DEFINITSIOONID

  USD = USDX futuur (098662)     +9.29 bp, Sharpe 1.05, t = 3.32
  toorne net (mitte /OI)         +9.65 bp, Sharpe 1.13, t = 3.57
  USD-skoor nulliks (U28)       +10.51 bp, Sharpe 1.14, t = 3.62
  USD-skoor nulliks (U7)        +10.79 bp, Sharpe 0.84, t = 2.66
  ainult 21 risti (ei USD)      +10.44 bp, Sharpe 1.11, t = 3.50

  => serv EI TULE USD-jalast. Ainult ristide peal on ta sama tugev.

  13f  REZIIMID (VIX mediaan 16.9)

  U28 VIX > 17 (korge)    +13.04 bp, Sharpe 1.28, t = 2.86
  U28 VIX <= 17 (madal)    +7.13 bp, Sharpe 0.96, t = 2.15
  U7  VIX > 17 (korge)     +9.09 bp, Sharpe 0.63, t = 1.40
  U7  VIX <= 17 (madal)   +10.52 bp, Sharpe 1.03, t = 2.31

  Tootab molemas rezhiimis. U28 on tugevam korge volatiilsuse ajal, mis on
  KOOSKOLAS mehhanismiga (rahvamassi likvideerimine stressi ajal).

  13g  SABADE TEST — kas efekt on vaheses uksikus episoodis?

  UHEPOOLNE eemaldus (ainult parimad nadalad eemaldatud):
    U7   ilma  5 parima nadalata  +5.82 bp, t = 1.64
    U7   ilma 10 parima nadalata  +3.35 bp, t = 0.98
    U7   ilma 20 parima nadalata  -0.60 bp, t = -0.19   <- KUKUB LABI
    U28  ilma  5 parima nadalata  +7.74 bp, t = 2.93
    U28  ilma 10 parima nadalata  +5.82 bp, t = 2.31
    U28  ilma 20 parima nadalata  +2.83 bp, t = 1.19    <- KUKUB LABI

  SUMMEETRILINE trim (sama arv parimaid JA halvimaid eemaldatud) —
  see on aus test, uhepoolne eemaldus tapab iga positiivse strateegia:
    U7   trim +- 5   +8.30 bp, t = 2.44
    U7   trim +-10   +7.93 bp, t = 2.52
    U7   trim +-20   +7.59 bp, t = 2.73
    U7   trim +-40   +7.27 bp, t = 3.04
    U28  trim +- 5   +9.56 bp, t = 3.78
    U28  trim +-10   +9.10 bp, t = 3.89
    U28  trim +-20   +8.53 bp, t = 4.08
    U28  trim +-40   +8.03 bp, t = 4.37

  Summeetrilise trimmiga t KASVAB. Efekt EI OLE sabades — ta on jaotuse
  keskel ja sabad hoopis lisavad mura. Vordluseks osta-ja-hoia:
  taielik +1.09 bp, trim +-20 +1.38 bp (U28).

  13h  ilma 2020 aastata: U7 +11.21 bp (t=2.84), U28 +10.72 bp (t=3.76)
       esimene pool vs teine pool: U7 +5.48 / +14.12, U28 +8.95 / +11.22

===============================================================================
14. KONTSENTRATSIOON
===============================================================================

  U7 (bruto panus kokku +53.88%)
    positiivseid paare            7 / 7  = 100.0%
    mediaan paar                  +7.22%
    TOP-1 paar    NZDUSD         +17.97%  = 33.4% kogukasumist
    TOP-3 paari   NZDUSD, AUDUSD, USDCAD  = 63.3% kogukasumist
    TOP-1 valuuta USD                      = 50.0% kogukasumist

  U28 (bruto panus kokku +57.32%)
    positiivseid paare           28 / 28 = 100.0%
    mediaan paar                  +1.53%
    TOP-1 paar    JPYAUD          +6.22%  = 10.9% kogukasumist
    TOP-3 paari   JPYAUD, JPYCAD, GBPJPY  = 28.4% kogukasumist
    TOP-1 valuuta JPY                      = 21.7% kogukasumist
    valuutapanus: JPY +12.5%  AUD +8.5%  CAD +8.1%  NZD +7.4%
                  CHF +6.7%   GBP +5.4%  USD +5.0%  EUR +3.8%

  NEMSIS-i lavi on "TOP-1 alla 30% kasumist".
    U28 LABIB (10.9% paar, 21.7% valuuta).
    U7 KUKUB LABI paari tasandil (33.4%) ja valuuta tasandil (50.0% USD),
    aga U7-s on ainult 7 paari ja KOIK 7 on USD-paarid, seega 50% USD
    on definitsiooni jargi vaeramatu, mitte kontsentratsiooniviga.

===============================================================================
15. STATISTILINE ANALUUS
===============================================================================

  15a  Benjamini-Hochberg (q = 0.05) ule 36 variandi
       lavi p = 0.0225, labis 19 varianti
       nendest POSITIIVSEID: 9
       (9 negatiivset on A_CONT/C_CONT peegelpildid — sama hupotees
        vastupidises suunas, mitte 9 eraldi leidu)

       labinud positiivsed:
         U7  A_REV h1  p=0.0133   +9.80 bp
         U7  A_REV h2  p=0.0225   +8.80 bp
         U7  C_REV h2  p=0.0096   +9.93 bp
         U7  C_REV h4  p=0.0139   +9.96 bp
         U28 A_REV h1  p=0.0003  +10.09 bp
         U28 A_REV h2  p=0.0006   +9.59 bp
         U28 A_REV h4  p=0.0021   +8.24 bp
         U28 C_REV h2  p=0.0180   +6.41 bp
         U28 C_REV h4  p=0.0214   +6.61 bp

  15b  Deflated Sharpe (Bailey & Lopez de Prado)
       parim variant U28 A_REV h1
       Sharpe aastane 1.13  =>  nadalane 0.1566
       36 variandi nadalase Sharpe standardhalve 0.1024
       SR* (oodatav maksimum 36 juhuslikust katsest) = 0.2078
       DEFLATED SHARPE p = 0.0755    vaja > 0.95    => KUKUB LABI

       AUS TOLGENDUS: DSR on siin karm kahel pohjusel.
       (1) 36 varianti sisaldavad tapseid peegelpilte (A_CONT = -A_REV),
           mis paisutab katsete-ulest Sharpe hajuvust kunstlikult.
       (2) DSR eeldab soltumatuid katseid; meie 36 on tugevalt
           korreleeritud (sama signaal, 3 hoidu, 2 universumit).
       Kumbki pohjus EI OLE luba tulemust ignoreerida. Empiiriline
       best-of-36 null (sektsioon 11, p = 0.0280) on parem test ja
       LABITAKSE — aga napilt.

  15c  Autokorrelatsioon
       Newey-West (4 lag) t: U7 +2.72, U28 +3.99 — MOLEMAD SUUREMAD kui
       tavaline t. Kattuvust h=1 juures ei ole, seega t ei ole paisutatud.

  15d  VALIKUVIGA — mida ma tegin ja mida mitte
       TEGIN: kirjutasin koik 36 varianti, lavid, aknad ja viivitused
       cot_engine.py paisesse ENNE esimest jooksu. Ei muutnud uhtegi
       parameetrit parast tulemuste nagemist.
       TEGIN: robustsustestid 13c/13d on KONTROLL, mitte optimeerimine —
       raporteerin need ka siis, kui nad halvemad on (104n aken kukub labi).
       EI TEINUD: ei valinud paare, valuutasid ega perioode tulemuste jargi.
       AUSTAN: 0.90/0.10 lavi osutus PARIMAKS koigist viiest lavist.
       See on onn, mitte toestus. Kui oleksin valinud 0.15/0.85, oleks
       tulemus +6.44 bp, t = 2.47 — ikka positiivne, aga poole norgem.

===============================================================================
16. 205 EUR TAITEVUSANALUUS
===============================================================================

  konto        205 EUR
  min lot      0.01  =>  1 000 uhikut baasvaluutat
  EURUSD       1.1596 (viimane)

  paar      nadala sigma   0.01 lot EUR   1-sigma PnL EUR   % kontost
  ----      ------------   ------------   ---------------   ---------
  EURUSD           1.01%           1000             10.09        4.9%
  GBPUSD           1.25%           1165             14.52        7.1%
  AUDUSD           1.38%            619              8.52        4.2%
  NZDUSD           1.41%            502              7.10        3.5%
  USDJPY           1.21%            862             10.43        5.1%
  USDCHF           1.07%            862              9.20        4.5%
  USDCAD           0.90%            862              7.72        3.8%

  kavatsetud risk 0.25% = 0.51 EUR/positsioon  ->  TAIDETAV 0 / 7 paaril
  kavatsetud risk 0.50% = 1.02 EUR/positsioon  ->  TAIDETAV 0 / 7 paaril

  vajalik konto, et 0.01 lot vastaks 0.25% riskile:
      min 2 838 EUR, mediaan 3 680 EUR, max 5 806 EUR
  vajalik konto, et 0.01 lot vastaks 0.50% riskile:
      min 1 419 EUR, mediaan 1 840 EUR, max 2 903 EUR

  samaaegseid positsioone U7:  keskmine 2.9, mediaan 2, max 7
  samaaegseid positsioone U28: keskmine 11.3, mediaan 12, max 21

  minimaalne portfelli notsionaal (2 positsiooni x 0.01 lot):  1 678 EUR
  see on 8.2x konto  =>  vajalik voimendus 8:1
  marginaal 1:30  juures: 56 EUR (27% kontost)
  marginaal 1:500 juures:  3 EUR ( 2% kontost)

  portfelli 1-sigma nadalane PnL miinimumlottidega: 17.68 EUR = 8.6% kontost
  (eeldab soltumatust; paarid on korreleeritud => tegelikult suurem)

  VASTUS KUSIMUSELE "kas 205 EUR kontol saab seda kaubelda":
  EI. Marginaal mahub ara (1:500 juures ainult 2% kontost), AGA RISK
  MITTE. Miinimumlot sunnib iga positsiooni 3.5-7.1% riskile konto kohta,
  kui kavatsus oli 0.25%. See on 14-28x ule limiidi.

  RISKI EI TOSTETA, ET STRATEEGIA MAHUKS. See on sama viga, mis tehti
  kulla gridiga (0.01 lot + $45 stopp = 22% riski tehingu kohta).
  205 EUR kontol on see strateegia mitte-teostatav, punkt.

===============================================================================
17. PASS / FAIL OTSUS
===============================================================================

  kriteerium                                          tulemus     staatus
  ----------                                          -------     -------
  positiivne neto ootus parast realistlikke kulusid   +10.09 bp   LABIB
  positiivne FINAL OOS                          6/6 lahtrit +     LABIB
  elab ule parima paari eemaldamise                    +9.36 bp   LABIB
  elab ule parima valuuta eemaldamise                  +6.08 bp   LABIB
  ei soltu uhest ajaperioodist                    11/11 aastat    LABIB
  majanduslikult usutav mehhanism                  rahvamass      LABIB
  lookahead puudub                              16/16 auditit     LABIB
  ei ole maskeeritud OHLC-strateegia          alfa t = 3.79       LABIB
  aus juhuslik baseline (best-of-36)               p = 0.0280     LABIB
  TOP-1 panus alla 30%                        U28 10.9% / U7 33%  OSALINE
  Deflated Sharpe                                  p = 0.0755     KUKUB
  ortogonaalne (puhas) komponent                   t = 1.87       KUKUB
  pertsentiiliaken 104n                            t = 1.15       KUKUB
  teostatav 205 EUR / 0.01 lot juures              0/7 paari      KUKUB

  9 LABIB, 1 OSALINE, 4 KUKUB.

  Kriteeriumide nimekiri utleb: ROBUST EDGE FOUND nouab, et KOIK
  tingimused oleks taidetud, sealhulgas teostatavus 205 EUR kontol.
  See tingimus KUKUB LABI uheselt ja parandamatult.

  ==> PROMISING BUT NOT PROVEN

===============================================================================
18. TAPNE JARELDUS
===============================================================================

  1. CFTC COT sisaldab infot, mida OHLC-hinnas EI OLE. See on esimene
     kord 11 650 testi jooksul, kui NEMSIS leiab midagi, mis tousb ulalpoole
     kulusid ja ausat juhuslikku nulli. Hinnapohine analoog annab -0.94 kuni
     +2.86 bp; COT annab +10.09 bp; alfa hinnapohise jarel on +10.35 bp
     (t = 3.79). Hinnamomentum seletab net_pct-st keskmiselt 29%,
     71% on soltumatu.

  2. Toimiv suund on REVERSAL, mitte jatkumine. Ekstreemselt pika
     spekulatiivse positsiooni FADE toodab; sellega kaasa minek kaotab
     summeetriliselt (-11.87 bp). Mehhanism: rahvamass, mis on uhele poole
     kogunenud, on sunnitud likvideerima.

  3. Positsiooni MUUTUS (hupotees B) EI SISALDA infot. Ainult TASE.
     See on eristav tulemus, mitte kohin: koik 12 B-varianti on
     |t| < 2.5 ja enamik |t| < 1.

  4. HINNAKINNITUS KAHJUSTAB. C (A + 12n momentum) on halvem kui puhas A
     koigil hoidudel ja molemas universumis. Serv EI TULE hinnast.

  5. Kulu ei ole probleem. Kaive on 0.42 nadalas; isegi 8bp uhesuunaline
     kulu jatab t = 2.69. Carry-lohk on -0.06 kuni -0.21 %/aastas ja
     murdepunkt on brokeri juurdehindlus 6%/aastas/jalg — 4x rohkem varu
     kui v6 carry-strateegial, mis kukkus labi 1.49% peal.

  6. NORKUSED, mida EI TOHI varjata:
     - Deflated Sharpe p = 0.0755 (vaja > 0.95)
     - taielikult hinnast ortogonaliseeritud komponent t = 1.80-1.87
     - 104-nadalane pertsentiiliaken kukub labi (t = 1.15)
     - eelregistreeritud lavi 0.90/0.10 osutus parimaks viiest — onn
     - U28 tugineb sunteetilistele ristidele; U7 (paris hinnad) on
       oluliselt norgem (Sharpe 0.78 vs 1.13)
     - uhepoolne "eemalda 20 parimat nadalat" test kukub labi molemas

  7. 205 EUR KONTOL EI SAA SEDA KAUBELDA. 0/7 paari mahub 0.25% riski
     sisse, 0/7 isegi 0.50% sisse. Vajalik konto 2 903 - 5 806 EUR.
     Miinimumlot 0.01 sunnib iga positsiooni 3.5-7.1% riskile.

  8. MIDA EI TEHTUD (ja mida EI TOHI jargmisena teha ilma otsuseta):
     - live-faile ei muudetud
     - /update ei saadetud
     - strateegiat ei optimeeritud
     - uut live-strateegiat ei loodud

  LOPLIK OTSUS:  PROMISING BUT NOT PROVEN

  See on esimene kandidaat NEMSIS-i ajaloos, mis vaarib teist uurimisringi.
  Aga ta ei ole toestatud ja ta ei mahu praegusele kontole.

===============================================================================
KOOD
===============================================================================
  bot/sb_cot.py        Supabase -> CSV konverter
  bot/cot_engine.py    mootor, eelregistreeritud konstandid, statistika
  bot/cot_audit.py     16 no-lookahead ja korrektsuskontrolli
  bot/cot_run.py       36 varianti + BH + Deflated Sharpe
  bot/cot_robust.py    juhuslik null, baseline'id, OHLC-test, TRAIN/VALID/OOS
  bot/cot_robust2.py   kontsentratsioon, kulud, ajastus, lavid, definitsioonid
  bot/cot_exec.py      tehingutasand, tugevusproovid, 205 EUR taitevus
  bot/cot_carry.py     carry-kontroll ja summeetriline trim
  bot/cot_ortho.py     ortogonaliseeritud COT + rezhiimid
  bot/data/cot_legacy.csv   10 565 rida CFTC andmeid (gitignore'itud)
===============================================================================
```
