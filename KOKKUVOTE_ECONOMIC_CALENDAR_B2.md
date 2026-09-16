===============================================================================
NEMSIS B2 — ECONOMIC CALENDAR DELAYED-REACTION TEST
===============================================================================
  16. september 2026
  branch  claude/great-noether-um7382
  seeme   20260915 (koik randomiseerimised fikseeritud)
  Uurimistoo. Live-botti EI PUUDUTATUD, /update EI SAADETUD.


===============================================================================
1. EXECUTIVE SUMMARY
===============================================================================

  Eelregistreeritud primary test T+8h -> T+32h EI TOOTA.

    bruto   +1.47 bp
    kulu     2.50 bp
    neto    -1.03 bp
    kordne   0.59 x   (NEMSIS noue >= 2.00)
    t = 0.77,  p = 0.441,  n = 276

  Event-time profiil naitab, MIKS. Kogu efekt on esimeses tunnis:

    0h -> 1h    +9.55 bp    t = 11.51   <- TEATEHUPE, EI OLE KAUBELDAV
    1h -> 2h    +0.42 bp    t =  1.01
    2h -> 4h    -0.57 bp    t = -0.96
    4h -> 8h    -0.46 bp    t = -0.72
    8h -> 12h   +0.20 bp    t =  0.40
    12h -> 16h  -0.41 bp    t = -0.65
    16h -> 24h  -0.19 bp    t = -0.24
    24h -> 32h  +2.00 bp    t =  1.66
    32h -> 48h  -0.83 bp    t = -0.59

  Ukski KAUBELDAV loik ei ole statistiliselt eristatav nullist. Hupotees
  "efekt koguneb 8-32 tunni jooksul" on FALSIFITSEERITUD.

  TEINE, OOTAMATU LEID. B1 paevane tulemus EI KORDU, kui sama reegel
  jooksutada tunniandmetel. SAMAL 276 sundmusel:

    B1 paevane 1d (Yahoo _d25)            +8.46 bp   t = 4.54
    B2 T+8 -> T+32 (H1-hinnad)            +1.47 bp   t = 0.77

  Ja sama kella-reegel (21:00 UTC -> jargmine 21:00 UTC), ainult erinev
  hinnaseeria:

    B1 ajastus, Yahoo paevane             +7.28 bp   t = 4.91
    B1 ajastus, H1-hinnad                 +2.04 bp   t = 1.48

  Erinevus EI OLE valim ega ajastus. Erinevus on HINNASEERIA. Mootsin:
  EURUSD paevatootluse korrelatsioon Yahoo _d25 ja H1-st tuletatud
  fikseeritud kellaaja seeria vahel on maksimaalselt 0.61 (parim tund
  19:00 UTC). Sunkroonse hetktoomsvotu korral peaks see olema ~0.99.
  Yahoo paevane sulgemine EI OLE fikseeritud kellaajal.

  See tahendab, et B1 ristloikeline tsentreerimine (8 valuutat, iga
  valuuta tootlus miinus keskmine) kasutab MITTESUNKROONSEID hindu.
  B1 peatulemus +4.27 bp sisaldab tundmatus osas seda artefakti.

  LOPLIK KLASSIFIKATSIOON:  NO ROBUST DELAYED EFFECT FOUND


===============================================================================
2. TAPNE HUPOTEES (eelregistreeritud enne esimest jooksu)
===============================================================================

  HYPOTHESIS B2:
    Kui B1 majanduskalendri efekt on reaalne, kuid ei realiseeru kohe,
    siis parast release'i tekib positiivne drift jargneva 8-32 tunni
    jooksul.

  Fikseeritud event-time grid (valitud ENNE tulemusi, ei muudetud):
    +1h +2h +4h +8h +12h +16h +24h +32h +48h

  AINUS jareldav test:
    sisenemine T + 8 h,  valjumine T + 32 h,  hoid 24 h.

  Koik ulejaanud horisondid on KIRJELDAVAD. Neid ei kasitleta
  soltumatute kinnitavate testidena.


===============================================================================
3. B1 BASELINE — MIS JAI MUUTMATA
===============================================================================

  Kontrollitud koodist (cal_engine.py), mitte eeldatud. Audit A1-A7
  tostab need eraldi esile.

  z              (actual - forecast) / rull-std(20 VARASEMAT sama
                 (valuuta, indikaator) prognoosiviga, min 10 vaatlust).
                 shift(1) enne rolling'ut. cal_engine.z_ullatus KUTSUTAKSE
                 otse, mitte ei kopeerita. Audit A6: z on B1-ga bitt-
                 identne, max erinevus 0.00e+00 ule 1608 rea.
  suund          sign(z) * eelregistreeritud majanduslik mark.
  universum      TIER 1, 11 indikaatorit. Liikmeid EI MUUDETUD.
  lavi           |z| >= 1.0. Uut lavet EI OTSITUD.
  tootlus        valuuta log-tootlus MIINUS ristloikeline keskmine
                 (8 valuutat, turuneutraalne).
  kulu           1.25 bp uhesuunaline = 2.50 bp edasi-tagasi.

  TIER 1 liikmed (mark sulgudes):
    Core Inflation Rate (+1)        Non Farm Payrolls (+1)
    Employment Change (+1)          Retail Sales MoM (+1)
    GDP Annual Growth Rate (+1)     Retail Sales YoY (+1)
    GDP Growth Rate (+1)            Unemployment Rate (-1)
    Inflation Rate (+1)             Interest Rate (+1)
    Inflation Rate Mom (+1)


===============================================================================
4. ANDMED JA PERIOOD
===============================================================================

  KALENDER
    allikas   TradingView economic calendar API (tasuta, ilma votmeta)
    fail      bot/data/econ_cal.csv, 37 595 sundmust actual+forecast'iga
    TIER 1    8 300 sundmust, 2013-08-16 .. 2026-09-15

  HINNAD — KAKS ERI ANDMESTIKKU, MILLE ERINEVUS ON SELLE RAPORTI LEID
    B1 paevane   Yahoo _d25, 2006-05-15 .. 2026-09-10
    B2 H1        bot/data/*_h1.csv, 2023-11-27 .. 2026-09-11

  VALIM
    TIER 1 sundmused z-ga H1 aknas            1 608
    neist |z| >= 1 (primary valim)              405
    primary test T+8 -> T+32 (molemad otsad)    276
    periood                     2023-11-29 .. 2026-09-07 = 2.77 aastat

  AJALINE PIIRANG — SELGELT VALJA OELDUD
    PAEVANE B1   2013-08-16 .. 2026-09-15   = 13.1 aastat
    H1 B2        2023-11-27 .. 2026-09-11   =  2.77 aastat

    B2 tulemus EI OLE 13 aasta kinnitus ega 13 aasta umberlukkamine.
    Ta on 2.77 aasta mootmine.


===============================================================================
5. EVENT-TIME METOODIKA
===============================================================================

  H1-baar on margistatud AVAMISAJAGA ja sulgub margis + 1 h. Sama eeldus
  mis B1 cal_engine.h1_sisenemine ja B1 audit A3.

  Hind hetkel tau = VIIMANE baar, mille SULGEMINE on <= tau.
  Rangelt pohjuslik: hetkel tau ei saa teada hilisemat hinda.

  Kui lahim sulgemine on vanem kui 4 h (nadalavahetus, andmeauk), on
  sundmus sellel horisondil VALJA JAETUD ja loendatud. Proksit EI
  ASENDATUD — kasutaja noue.

  ANKUR = viimane sulgemine <= T, st TEATE-EELNE hind.
  Seetottu loik 0h -> 1h SISALDAB teatehupet ja EI OLE KAUBELDAV.
  See on markitud igal pool eraldi. Kaubeldavad on loigud alates 1h.

  HORISONDI KATVUS (tolerants 4 h):
    +1h    405 / 405   valja jaetud   0  ( 0.0%)
    +2h    405 / 405                  0  ( 0.0%)
    +4h    405 / 405                  0  ( 0.0%)
    +8h    405 / 405                  0  ( 0.0%)
    +12h   405 / 405                  0  ( 0.0%)
    +16h   356 / 405                 49  (12.1%)
    +24h   298 / 405                107  (26.4%)
    +32h   276 / 405                129  (31.9%)
    +48h   186 / 405                219  (54.1%)

  Valjajatmised on nadalavahetuse tottu. Neid EI ASENDATUD.

  KAKS AJAARVESTUST, molemad eelregistreeritud, molemad raporteeritud:
    SEINAKELL (primaarne)   horisont = T + h tundi, tolerants 4 h
    BAARILUGEMINE (teisene) horisont = ankur + h baari, nagu B1 H1-test


===============================================================================
6. EVENT-TIME PROFIIL (KIRJELDAV)
===============================================================================

  Kumulatiivne ankrust (teate-eelne hind). SISALDAB teatehupet.

  SEINAKELL
  horisont     n   bruto_bp   med_bp   neto_bp   wr%       t       p   sd_bp
  --------   ---   --------   ------   -------   ----   -----   -----   -----
  +1h        405     +9.55    +4.08     +7.05   72.3   11.51   0.000    16.7
  +2h        405     +9.97    +5.23     +7.47   67.9   10.95   0.000    18.3
  +4h        405     +9.40    +6.50     +6.90   66.7    8.82   0.000    21.5
  +8h        405     +8.94    +6.87     +6.44   62.2    7.11   0.000    25.3
  +12h       405     +9.14    +7.42     +6.64   61.2    6.94   0.000    26.5
  +16h       356     +7.20    +4.59     +4.70   58.7    4.85   0.000    28.0
  +24h       298     +8.15    +5.76     +5.65   62.4    4.08   0.000    34.5
  +32h       276    +10.54    +9.12     +8.04   61.2    4.22   0.000    41.5
  +48h       186    +11.57   +12.50     +9.07   61.8    4.23   0.000    37.3

  BAARILUGEMINE (kontroll — nadalavahetust ei jaeta valja)
  horisont     n   bruto_bp   med_bp   neto_bp   wr%       t       p   sd_bp
  --------   ---   --------   ------   -------   ----   -----   -----   -----
  +1         405     +9.55    +4.08     +7.05   72.3   11.51   0.000    16.7
  +2         405     +9.97    +5.23     +7.47   67.9   10.95   0.000    18.3
  +4         405     +9.40    +6.50     +6.90   66.7    8.82   0.000    21.5
  +8         405     +8.94    +6.87     +6.44   62.2    7.11   0.000    25.3
  +12        405     +9.25    +7.68     +6.75   61.7    7.08   0.000    26.3
  +16        405     +9.07    +7.68     +6.57   62.0    6.32   0.000    28.9
  +24        405     +9.29    +7.56     +6.79   63.2    5.31   0.000    35.2
  +32        405    +10.56    +9.31     +8.06   61.0    5.14   0.000    41.3
  +48        405    +11.38    +9.87     +8.88   61.5    5.20   0.000    44.1

  Kumulatiiv on lame: +9.55 juba esimese tunniga, +9.29 kahekumne nelja
  tunniga. HOIATUS: kumulatiiv EI OLE uus soltumatu toend. Iga horisont
  sisaldab sama teatehupet. Ainus, mis utleb midagi uut, on LOIGUD.


===============================================================================
7. INKREMENTAALNE PROFIIL — KUS MOJU TEGELIKULT TEKIB
===============================================================================

  Iga loik arvutatud AINULT nendel sundmustel, millel on MOLEMAD
  otspunktid olemas, seega vahe ei tule erinevast valimist.

  loik                              n   inkr_bp   med_bp    wr%       t       p
  --------------------------      ---   -------   ------   ----   -----   -----
  0h -> 1h   TEATEHUPE, EI OLE
             KAUBELDAV            405     +9.55    +4.08   72.3   11.51   0.000
  1h -> 2h                        405     +0.42    +0.27   54.3    1.01   0.315
  2h -> 4h                        405     -0.57    -0.40   48.9   -0.96   0.336
  4h -> 8h                        405     -0.46    -1.73   43.5   -0.72   0.473
  8h -> 12h                       405     +0.20    -0.35   46.9    0.40   0.689
  12h -> 16h                      356     -0.41    +0.00   43.0   -0.65   0.519
  16h -> 24h                      298     -0.19    +0.70   52.0   -0.24   0.807
  24h -> 32h                      276     +2.00    +2.88   56.5    1.66   0.096
  32h -> 48h                      186     -0.83    -0.61   47.8   -0.59   0.553

  VASTUS KUSIMUSELE "KUS EFEKT TEKIB":
    A) toimub kohe — JAH, ja ainult seal. Kogu mootedetav efekt on
       teatehupes, mis toimub enne, kui uldse saaks siseneda.
    B) tekib 4-8h  — EI.  -0.46 bp, p = 0.473
    C) tekib 8-32h — EI.  summa +1.60 bp ule nelja loigu, uhegi p < 0.05
    D) tekib 32-48h — EI. -0.83 bp, p = 0.553
    E) ei ole stabiilne — kaubeldavad loigud on kokku 0 ja mura.

  Suurim kaubeldav loik on 24h -> 32h +2.00 bp (p = 0.096). See EI OLE
  oluline, ja ta on uks uheksast loigust. Kui teda kasitleda avastusena,
  on see tagantjarele parima valimine — mida see raport ei tee.


===============================================================================
8. PRIMARY TULEMUS  T+8h -> T+32h
===============================================================================

  test                            n    bruto     med    neto    wr%      t       p
  --------------------------    ---   ------   -----   -----   ----   ----   -----
  PRIMARY T+8h -> T+32h         276    +1.47   +0.12   -1.03   50.4   0.77   0.441
  sama, BAARILUGEMINE           405    +1.62   +0.54   -0.88   50.9   1.03   0.305

  kumulatiivne bruto  +4.13%
  kumulatiivne neto   -2.81%
  sd                  31.6 bp
  bruto / kulu        0.59 x     (NEMSIS noue >= 2.00)

  Voidumaar 50.4% on tais nulli peal. Mediaan +0.12 bp on nulli peal.
  Molemad ajaarvestused annavad sama vastuse.


===============================================================================
9. POSITIIVNE vs NEGATIIVNE ULLATUS
===============================================================================

  Signaali EI MUUDETUD. Sama primary aken.

  test                            n    bruto     med    neto    wr%      t       p
  --------------------------    ---   ------   -----   -----   ----   ----   -----
  A positiivne ullatus z>=+1    130    -1.92   -0.76   -4.42   45.4  -0.87   0.382
  B negatiivne ullatus z<=-1    146    +4.48   +2.06   +1.98   54.8   1.49   0.136
  C molemad koos                276    +1.47   +0.12   -1.03   50.4   0.77   0.441

  B1-s olid molemad positiivsed (A +3.09, B +2.32). B2 viivitatud aknas
  on A NEGATIIVNE ja B positiivne, kumbki ei ole oluline. See on
  kooskolas sellega, et signaali ei ole — kaks poolt lahevad lahku
  juhuslikult.


===============================================================================
10. PIDEV ULLATUS
===============================================================================

  signal = z * economic_sign,  return = valuuta tootlus - ristloikeline
  keskmine, samas T+8 -> T+32 aknas. Uusi teisendusi EI LISATUD.

    n                  1 156   (KOIK TIER 1, mitte ainult |z| >= 1)
    korr(signal, r)   +0.0385
    beeta             +1.18 bp uhe z-uhiku kohta
    t                 +1.31
    p                  0.191

  Mehhanismi kinnitust EI OLE. Vordluseks: B1 paevane 1d beeta oli
  oluliselt nullist erinev; siin ei ole.


===============================================================================
11. SEOS B1 PAEVASE TESTIGA — JA MIKS NAD EI KLAPI
===============================================================================

  test                              n    bruto     med    neto    wr%      t       p
  ----------------------------    ---   ------   -----   -----   ----   ----   -----
  B1 TIER1 1d KOGU 13.1a         2016    +4.27   +3.33   +1.77   54.6   4.97   0.000
  B1 TIER1 2d KOGU 13.1a         2016    +3.68   +1.89   +1.18   52.4   3.12   0.002
  B1 TIER1 5d KOGU 13.1a         2011    +5.35   +5.25   +2.85   52.6   2.78   0.005
  B1 TIER1 1d H1-aknas            408    +7.28   +4.24   +4.78   60.0   4.91   0.000
  B1 TIER1 2d H1-aknas            408    +7.36   +5.60   +4.86   57.8   3.64   0.000
  B1 TIER1 5d H1-aknas            403    +9.71   +7.25   +7.21   56.1   2.85   0.004
  B2 PRIMARY T+8 -> T+32          276    +1.47   +0.12   -1.03   50.4   0.77   0.441

  MIKS NAD EI OLE UKS-UHELE VORRELDAVAD
    - B1 1d = paevabaari sulgemisest sulgemiseni. Sisenemine on esimene
      sulgemine PARAST teadet, mis on teate kellaajast soltuvalt
      0.1 .. 24 h hiljem.
    - B2 primary on IGAL sundmusel tapselt T+8h -> T+32h.
    - B1 hoiab 24 h kalendriaega (sh nadalavahetus), B2 jatab
      nadalavahetusele sattuvad valja (31.9% +32h horisondil).
    - Valimid erinevad: B1 H1-aknas n=408, B2 primary n=276.

  SEETOTTU TEGIN KOLM ERALDAVAT TESTI.

  (i) SAMA VALIM, KAKS MOOTU — ainult sundmused, mis on MOLEMAS:
      B1 paevane 1d               276    +8.46   +5.07   +5.96   61.2   4.54   0.000
      B2 T+8 -> T+32              276    +1.47   +0.12   -1.03   50.4   0.77   0.441
      => vahe EI OLE valim.

  (ii) SAMA KELLA-REEGEL, KAKS HINNASEERIAT — sisene 21:00 UTC
       sulgemisel PARAST teadet, valju jargmisel 21:00 UTC sulgemisel:
      B1 ajastus, Yahoo paevane   408    +7.28   +4.24   +4.78   60.0   4.91   0.000
      B1 ajastus, H1-hinnad       405    +2.04   +1.36   -0.46   52.8   1.48   0.140
      => vahe EI OLE ajastus. Vahe on HINNASEERIA.

      B1-ajastuse sisenemisviivitus H1-baaridel: mediaan 12.0 h,
      5% 7.5 h, 95% 21.5 h. Hoidmisaeg mediaan 24 h, max 72 h.

  (iii) KAS PAEVANE SEERIA ON SUNKROONNE?
      EURUSD paevatootluse korrelatsioon Yahoo _d25 ja H1-st tuletatud
      fikseeritud kellaaja seeria vahel:
        parim  19:00 UTC -> 0.610   (n = 642)
               20:00 UTC -> 0.602
               17:00 UTC -> 0.598
        halvim 06:00 UTC -> 0.501

      Sunkroonse hetktoomsvotu korral peaks parim olema ~0.99.
      Mooedetud maksimum on 0.61.

      Lisamootmised: paevase tootluse sd klapib peaaegu tapselt
      (EUR 44.6 vs 45.0 bp, JPY 64.0 vs 63.0 bp) ja Yahoo paevane
      sulgemishind jaab H1-paeva high-low vahemikku 90.6% (EURUSD) /
      99.4% (USDJPY) juhtudest. Seega on tegu SAMA turuga, aga
      paevane sulgemine EI OLE fikseeritud kellaajal.

  JARELDUS. B1 ristloikeline tsentreerimine lahutab igast valuutast
  kaheksa valuuta keskmise. Kui need kaheksa hinda on votetud ERI
  hetkedel, tekib igale valuutale nait-idiosunkraatiline tootlus.
  Teatepaevadel on idiosunkraatiline liikumine suurim => artefakt on
  suurim just seal, kus signaal seda ootab.

  Ma EI VAIDA, et kogu B1 efekt on artefakt. Ma vaidan, et:
    - sama reegel sunkroonsetel hindadel annab +2.04 bp asemel +7.28 bp
    - ja +2.04 bp ei ole oluline (p = 0.140)

  KAS B1 SISENEMINE SAI OLLA TEATE-EELNE? Kontrollisin valjalaske
  kellaaja jargi (kogu 13.1 a valim):
    kellaaeg UTC                    n   bruto    neto    wr%      t       p
    00-06 Aasia                   238   +8.74   +6.24   61.8   3.28   0.001
    06-12 Euroopa                 986   +3.13   +0.63   52.5   2.71   0.007
    12-17 US hommik               548   +5.53   +3.03   55.5   3.22   0.001
    17-21 enne paeva sulgemist      2   (alla 20 sundmuse)
    21-24 parast paeva sulgemist  242   +0.99   -1.51   53.7   0.38   0.703

  Kui sisenemishind oleks susteemselt teate-EELNE, peaks efekt olema
  suurim hilise valjalaskega sundmustel (17-21 UTC), kus eeldatud 21:00
  sulgemine on teatele koige lahemal. Selles aknas on ainult 2 sundmust,
  seega seda mehhanismi EI SAA kinnitada ega umber lukata. Susteemset
  lookahead'i ma EI TOESTANUD. Mittesunkroonsuse mooedetud fakt jaab.


===============================================================================
12. WALK-FORWARD
===============================================================================

  Jaotus valitud ENNE tulemuste vaatamist, KALENDRIAASTA jargi, mitte
  tulemuse jargi. B1 oma jaotus (TRAIN <= 2017, VALID <= 2020) ei toota,
  sest kogu H1-aken 2023-11-27+ langeb tervikuna B1 FINAL OOS-i sisse
  (audit F3).

    TRAIN      .. 2024-12-31
    VALID      2025-01-01 .. 2025-12-31
    FINAL OOS  2026-01-01 ..

  osa              n    bruto     med    neto    wr%      t       p
  ----------     ---   ------   -----   -----   ----   ----   -----
  TRAIN           95    +1.15   +0.98   -1.35   51.6   0.33   0.744
  VALID          100    +0.69   -1.81   -1.81   49.0   0.19   0.853
  FINAL OOS       81    +2.79   +0.12   +0.29   50.6   1.35   0.177

  FINAL OOS on bruto positiivne (+2.79 bp) ja neto napilt positiivne
  (+0.29 bp), aga p = 0.177 ja n = 81. See EI OLE kinnitus. Kolme osa
  vahemik +0.69 .. +2.79 bp on kitsam kui uhe osa standardviga.

  VALIM ON VAIKE. Ma EI SURU siit statistilist jareldust.


===============================================================================
13. RANDOMIZATION / NULL
===============================================================================

  500 permutatsiooni, primary aknas, seeme 20260915.

  tegelik bruto: +1.466 bp  (n = 276)

  null                  mediaan      5%       95%      max        p
  ------------------   --------   ------   ------   ------   ------
  A juhuslik suund       -0.158   -3.054   +3.200   +5.299   0.2180
  B segatud ullatus      +0.145   -2.620   +3.485   +7.063   0.2600

  Tegelik tulemus on null-jaotuse keskmise laheduses. 22-26% juhuslikest
  markidest annab sama voi parema tulemuse.

  VORDLUSEKS: B1 paevasel testil oli sama null p = 0.0000 (0/500).
  Seal oli mehhanism olemas. Siin ei ole.


===============================================================================
14. KULUTUNDLIKKUS
===============================================================================

  kulu uhesuunaline   edasi-tagasi   bruto_bp   neto_bp   kordne   verdikt
  -----------------   ------------   --------   -------   ------   -------
  0.00 bp                    0.00      +1.47     +1.47      inf      —
  0.50 bp                    1.00      +1.47     +0.47     1.47    KUKUB
  1.00 bp                    2.00      +1.47     -0.53     0.73    KUKUB
  1.25 bp  NEMSIS BASE       2.50      +1.47     -1.03     0.59    KUKUB
  1.50 bp                    3.00      +1.47     -1.53     0.49    KUKUB
  2.00 bp                    4.00      +1.47     -2.53     0.37    KUKUB

  Isegi NULLKULUGA on bruto +1.47 bp p = 0.441 — st mitte eristatav
  nullist. Kulu ei ole siin see, mis strateegia tapab. Strateegiat ei ole.


===============================================================================
15. ROBUSTSUS AASTATE KAUPA
===============================================================================

  Halbu aastaid EI EEMALDATUD.

  aasta      n   bruto_bp   neto_bp    wr%       t
  -----    ---   --------   -------   ----   -----
  2023      11   (alla 20 sundmuse — ei raporteerita)
  2024      84      -1.99     -4.49   47.6   -0.55
  2025     100      +0.69     -1.81   49.0    0.19
  2026      81      +2.79     +0.29   50.6    1.35

  bruto positiivseid aastaid: 2/3 (2023 liiga vaike)
  neto positiivseid aastaid:  1/3

  VORDLUSEKS: B1 paevane TIER 1 oli bruto positiivne 13/14 aastal.
  B2 viivitatud aken ei korda seda.


===============================================================================
16. ROBUSTSUS VALUUTA KAUPA JA KONTSENTRATSIOON
===============================================================================

  Norku valuutasid EI EEMALDATUD.

  valuuta      n    bruto     med    neto    wr%      t       p
  -------    ---   ------   -----   -----   ----   ----   -----
  USD         38    +2.34   -0.75   -0.16   42.1   0.37   0.711
  EUR         95    +1.74   +0.79   -0.76   52.6   0.72   0.472
  GBP         34    +2.50   +9.04   -0.00   52.9   0.58   0.563
  JPY          9   (alla 20 sundmuse)
  CHF         39    +2.03   +0.19   -0.47   51.3   0.28   0.778
  CAD         18   (alla 20 sundmuse)
  AUD         36    +1.49   -1.53   -1.01   44.4   0.28   0.776
  NZD          7   (alla 20 sundmuse)

  Ukski valuuta ei ole oluline. Ukski neto ei ole positiivne.

  KONTSENTRATSIOON (B1 standard: osakaal kogu bruto logsummast)
    kogu bruto logsumma        +4.05%
    top 1 valuuta  EUR         +1.65% =  40.9% kogusummast
    top 2 valuutat EUR + USD   +2.54% =  62.9% kogusummast
    positiivseid valuutasid (bruto)      7/8

  7/8 positiivne on ilus, AGA koik on mikroskoopilised ja ukski ei ole
  oluline. Positiivsete lugemine on siin sisutu: 8 muraseeriast tuleb
  7 positiivset umbes 3% toenaosusega ainult siis, kui keskvaartus on
  tapselt 0; siin on keskvaartus +1.47 bp, mis on liiga vaike, et olla
  kaubeldav, aga piisav, et anda jarjekindlalt napilt positiivseid
  alamvalimeid. See EI OLE serva toend.


===============================================================================
17. ROBUSTSUS INDIKAATORI KAUPA
===============================================================================

  Koik TIER 1 naidatud, ka halvad. Marki EI MUUDETUD.

  indikaator (mark)               n    bruto     med    neto    wr%      t       p
  --------------------------    ---   ------   -----   -----   ----   ----   -----
  Core Inflation Rate (+1)       34    +3.35   +2.79   +0.85   55.9   0.68   0.496
  Employment Change (+1)         19   (alla 20 sundmuse)
  GDP Annual Growth Rate (+1)    14   (alla 20 sundmuse)
  GDP Growth Rate (+1)           22    -8.64   -1.46  -11.14   40.9  -1.42   0.154
  Inflation Rate (+1)            62    +0.77   -1.33   -1.73   46.8   0.17   0.862
  Inflation Rate Mom (+1)        43    +4.19   +1.76   +1.69   55.8   0.92   0.356
  Interest Rate (+1)              6   (alla 20 sundmuse)
  Non Farm Payrolls (+1)          0   (H1-aknas ei seotud uhtegi)
  Retail Sales MoM (+1)          19   (alla 20 sundmuse)
  Retail Sales YoY (+1)          16   (alla 20 sundmuse)
  Unemployment Rate (-1)         41    +5.54   +0.72   +3.04   56.1   1.07   0.286

  top 1 indikaator  Unemployment Rate     56.1% kogusummast
  top 2 indikaatorit                     100.7% kogusummast

  KAKS INDIKAATORIT ANNAVAD 100.7% KOGU BRUTOST. Ulejaanud uheksa on
  kokku negatiivsed. Ukski indikaator ei ole oluline.

  NFP = 0 sundmust. Pohjus: NFP avaldatakse 12:30/13:30 UTC reedel;
  T+32h langeb laupaeva peale, kus H1-baare ei ole, ja 4 h tolerants
  jatab need valja. See on aus valjajatmine, mitte valik.


===============================================================================
18. MITMIKTESTIMINE
===============================================================================

  Event-time grid = 9 horisonti. Need on KIRJELDAVAD, mitte 9 soltumatut
  kinnitavat testi. Nad jagavad sama teatehupet ja on tugevalt
  korreleeritud.

    BH q = 0.05:  labib 9/9,  neist positiivseid 9
    Bonferroni p-lavi 0.0056:  labib 9/9

  See "labib 9/9" EI OLE hea uudis. Koik uheksa on olulised SAMA
  pohjusega: teatehupe ankrus. Just seetottu on jareldav test
  INKREMENTAALNE, mitte kumulatiivne.

    PRIMARY (eelregistreeritud, 1 test):  p = 0.4413

  Primary ei vaja mitmiktestimise korrektsiooni, sest ta valiti ENNE
  tulemusi. Profiil vajab ja on markitud kirjeldavaks.

  Kaubeldavate LOIKUDE p-vaartused (8 tk), BH q = 0.05:
    parim p = 0.096 (24h -> 32h). BH lavi 0.05 * 1/8 = 0.00625.
    labib 0/8.


===============================================================================
19. ANDMEKVALITEET — ACTUAL vs REVISION
===============================================================================

  1. KAS ALLIKAS SISALDAB RELEASE TIMESTAMP'I?
     Jah. Veerg `ts` on UTC avaldamise hetk. Kinnitatud kaudselt:
     NFP-tunni H1-volatiilsus on 30.1 bp vs tavaline tund 5.5 bp = 5.4x
     (audit G1). Ajavoond on oige.

  2. KAS ACTUAL ON DOKUMENTEERITUD ESIALGNE TRUKK?
     EI. Fail sisaldab tapselt veerge:
       cur, ts, indicator, actual, forecast, previous, importance
     Revisjoni-valja EI OLE. TradingView API ei anna "initial print"
     margendit.

  3. KAUDNE KONTROLL EELNEVALT MAARATUD VALIMI PEAL
     Vordlesin previous_N vs actual_(N-1) sama (valuuta, indikaator)
     jaoks, KOGU valimi peal (mitte valitud alamhulgal):
       15 518 paari, kattub 55.2%

     Tolgendus: kui allikas hoiaks ainult lopprevideeritud vaartusi,
     peaks previous_N == actual_(N-1) peaaegu alati. 55% lahknevus
     viitab, et actual on esialgne trukk ja previous kannab revisjoni.

     SEE EI OLE TOESTUS. Lahknevus voib tulla ka umardamisest,
     hooajalisest korrigeerimisest voi seeria vahetusest.

     PIIRANG JAAB LAHENDAMATA. Ma ei vaida, et B1 revisjoniprobleem on
     lahendatud.

  4. UUS LEID — TOPELTVOTMED
     215 / 8 300 TIER 1 rida (2.6%) on sama (aeg, valuuta, indikaator)
     votmega:
       EUR / Employment Change   108 rida
       GBP / Interest Rate       104 rida
       USD / Interest Rate         3 rida

     Pohjus: TradingView annab EUR Employment Change QoQ ja YoY ning
     GBP Interest Rate kaks seeriat SAMA nime all. B1 rulliv std segab
     need uheks ajalooks => z on neil ridadel mootmisveaga.

     B2 EI PARANDANUD seda, sest B1 definitsioon pidi jaama. Moju on
     naha indikaatoritabelis (Employment Change n=19, Interest Rate n=6
     — molemad alla raporteerimislavi).

  5. KOIGE OLULISEM ANDMEKVALITEEDI LEID
     Hinnaandmed, mitte kalender. Vt sektsioon 11 (iii): Yahoo paevane
     sulgemine ei ole fikseeritud kellaajal (max korr 0.61 vs oodatav
     0.99). See mojutab B1 peatulemust, mitte B2 oma.


===============================================================================
20. LOOKAHEAD AUDIT
===============================================================================

  cal_b2_audit.py, 27 kontrolli, 0 VIGA. Jooksis ENNE tulemusi.

  A. B1 DEFINITSIOONID MUUTMATA
    A1  TIER 1 liikmeid 11, margid muutmata (Unemployment -1, Infl +1)
    A2  z-lavi 1.0
    A3  rulliv aken 20 / min 10
    A4  kulu 1.25 bp uhesuunaline = 2.50 edasi-tagasi
    A5  B2 kutsub cal_engine.z_ullatus'e, ei kopeeri seda
    A6  z on B1-ga BITT-IDENTNE: 1608 rida, max erinevus 0.00e+00
    A7  z ei kasuta tulevikku (sunteetiline test: viimase vaartuse
        muutmine ei muuda uhtegi varasemat z-i)
    A8  topeltvotmed loendatud (215/8300), B1 EI PARANDATUD

  B. AJASTUS JA POHJUSLIKKUS
    B1  ankur on ALATI teate ajal voi enne (max ankur - T = 0.00 h)
    B2  ankur ei ole vanem kui 4 h (mediaan 0.50 h, max 0.83 h)
    B3  iga horisondi valjumishind on siht-ajal voi enne
        (9 horisonti, 0 rikkumist)
    B4  valjumispositsioon ei ole kunagi enne ankrut
    B5  primary T+8 sisenemine rangelt PARAST teadet (min 7.17 h)
    B6  primary valjumine rangelt parast sisenemist (mediaan hoid 24.0 h)

  C. TOOTLUSE DEFINITSIOON
    C1  ristloikeline tsentreerimine: ridade summa = 0 (max 6.94e-18)
    C2  USD saab sisulise tootluse (sigma 43.8 bp), ei ole nullitud
    C3  teadaolev vastus: +2% uhel kahest -> +-log(1.02)/2, klapib

  D. KATTUVUS
    D1  405 sundmust -> 313 unikaalset (valuuta, aeg)
        42.5% valimist on klastris, suurim klaster 4 sundmust
        9 klastrit, kus suunad on VASTUOLUS

  E. ANDMEKVALITEET
    E1  previous vs eelmine actual: 15 518 paari, kattub 55.2%
    E2  allikas ei sisalda revisjoni-valja

  F. AJALINE PIIRANG
    F1  paevane B1 aken 2013-08-16 .. 2026-09-15 (7300 T1 sundmust)
    F2  H1 B2 aken 2023-11-27 .. 2026-09-11 (2.79 aastat)
    F3  kogu H1-aken langeb B1 FINAL OOS-i sisse => oma jaotus
    F4  B2 jaotus kalendriaasta-pohine: TRAIN 642, VALID 572, OOS 394

  G. AJAVOOND
    G1  NFP-tunni volatiilsus 30.1 bp vs 5.5 bp = 5.4x

  H. KAKS AJAARVESTUST
    H1  seinakell vs baarilugemine kattuvus horisondi kaupa:
        +1h 100%  +2h 100%  +4h 100%  +8h 100%  +12h 90%
        +16h 88%  +24h 94%  +32h 100%  +48h 93%

  MIDA AUDIT EI TOENDA
    Audit toendab, et B2 ise ei vaata tulevikku. Ta EI TOENDA, et
    kalendriandmete `actual` on esialgne trukk (vt 19.2-19.3).


===============================================================================
21. TEOSTATAVUS
===============================================================================

  Live order execution'it EI EHITATUD.

    tehinguid              276 / 2.77 a = 100 aastas
    keskmine hoidmisaeg    24.0 h (1.00 paeva)
    aastane bruto          +1.46%
    aastane kulu            2.49%
    aastane neto           -1.03%

  POSITSIOONI SUURUS 205 EUR KONTOL
  min lot 0.01 = 1000 uhikut kaubeldava paari baasvaluutat

  valuuta   24h sigma%   0.01 lot EUR   1-sigma EUR   % kontost
  -------   ----------   ------------   -----------   ---------
  USD             0.38            862          3.31        1.6
  EUR             0.20           1000          1.95        1.0
  GBP             0.27           1166          3.11        1.5
  JPY             0.51            862          4.42        2.2
  CHF             0.31            862          2.67        1.3
  CAD             0.25            862          2.14        1.0
  AUD             0.36            618          2.22        1.1
  NZD             0.35            501          1.75        0.9

    kavatsetud risk 0.25% = 0.51 EUR -> taidetav 0/8 valuutal
                                        vajalik konto 700-1766 EUR
    kavatsetud risk 0.50% = 1.02 EUR -> taidetav 0/8 valuutal
                                        vajalik konto 350-883 EUR

  OTSE VALJA OELDUD: 205 EUR konto EI SAA seda automaatselt kaubelda.
  Minimaalne lot 0.01 teeb kavatsetud 0.25% riskist 0.9-2.2% riski.
  See on 4-9 korda ule eelarve. Viga ei ole strateegias — see on
  konto suuruses. Aga kuna strateegiat ka ei ole, on kusimus
  akadeemiline.


===============================================================================
22. NEMSIS KRITEERIUMID
===============================================================================

  kriteerium                              tulemus              verdikt
  ------------------------------------    -----------------    -------
   1 bruto serv vs kulu (noue >= 2x)      0.59 x               KUKUB
   2 neto serv                            -1.03 bp             KUKUB
   3 statistiline olulisus                p = 0.441            KUKUB
   4 OOS                                  +2.79 bp p=0.177     KUKUB
   5 robustsus aastate kaupa              neto 1/3 aastat      KUKUB
   6 robustsus valuuta kaupa              0/8 oluline          KUKUB
   7 kontsentratsioon                     top2 valuutat 62.9%
                                          top2 indikaatorit
                                          100.7%               KUKUB
   8 permutation / null                   p = 0.218 / 0.260    KUKUB
   9 lookahead                            27 kontrolli, 0 viga LABIB
  10 majanduslik tolgendus                efekt on hupes, mis
                                          toimub enne sisenemist
                                                               KUKUB
  11 teostatavus 205 EUR kontol           0/8 valuutat         KUKUB

  LABIB 1 / 11.

  NEMSIS tugev serv noaks vahemalt ~2x kulu bruto serva. Mooedetud
  0.59x. Ma EI NIMETA seda ROBUST EDGE'iks.


===============================================================================
23. PIIRANGUD
===============================================================================

  1. VALIM. H1-aken on 2.77 aastat, 276 primary tehingut. See on VAIKE.
     Voimsus: sd 31.6 bp, n = 276 => SE 1.90 bp. Efekti +4.27 bp
     (B1 paevane tase) avastamiseks oleks oodatav t = 2.25 — st
     napilt piiri peal. Efekti +1.47 bp jaoks t = 0.77.
     Aus sona: B2 suudab valistada SUURE viivitatud efekti, aga
     EI SUUDA valistada 1-2 bp efekti.

  2. KAUBELDAVAD LOIGUD. Kaheksa kaubeldavat loiku annavad kokku
     ~0 bp. Iga uksik loik on murane. Ma ei valinud parimat.

  3. NADALAVAHETUSE VALJAJATMINE. +32h horisondil on 31.9% valimist
     valja jaetud, +48h juures 54.1%. See MUUDAB valimi koosseisu
     (reede-sundmused kaovad, sh KOIK NFP-d). Baarilugemise variant
     hoiab koik 405 ja annab sama vastuse (+1.62 vs +1.47 bp), seega
     see EI OLE tulemuse pohjus — aga see on piirang.

  4. REVISJON. Ei saa kinnitada, et `actual` on esialgne trukk.
     Kaudne mark (55.2% previous-lahknevus) viitab, et on, aga see ei
     ole toestus.

  5. TOPELTVOTMED. 2.6% TIER 1 ridadest on segatud z-ajalooga.
     Ei parandatud, sest B1 definitsioon pidi jaama.

  6. HINNASEERIA MITTESUNKROONSUS. See on B1 piirang, mille B2 avastas.
     B2 enda tulemus on H1-hindadel ja seega sunkroonne — aga see
     tahendab, et B1 ja B2 numbrid EI OLE otse vorreldavad, ja et B1
     peatulemus vajab eraldi ulevaatamist.

  7. KLASTRID. 42.5% primary valimist on sundmusklastris (sama valuuta,
     sama aeg). 9 klastris on suunad omavahel vastuolus. B1-l ei ole
     kattuvuse kasitlust; B2 kasutas SAMA kasitlust (st mitte uhtegi),
     et vordlus jaaks aus. Uut filtreerimisreeglit EI LOODUD.


===============================================================================
24. LOPLIK KLASSIFIKATSIOON
===============================================================================

              NO ROBUST DELAYED EFFECT FOUND

  Pohjendus, kolm soltumatut fakti:

    1. Eelregistreeritud primary T+8h -> T+32h annab bruto +1.47 bp
       kulu 2.50 bp vastu. Kordne 0.59x, p = 0.441.

    2. Inkrementaalne profiil naitab, et KOGU mootedetav efekt on
       loigus 0h -> 1h (+9.55 bp, t = 11.51), mis on teatehupe ja mida
       EI SAA kaubelda. Koik kaheksa kaubeldavat loiku on kokku ~0 bp
       ja ukski ei ole oluline (parim p = 0.096).

    3. Randomiseerimine: 500 juhusliku margi seast annab 21.8% sama voi
       parema tulemuse. B1 paevasel testil oli sama arv 0.0%.

  See EI OLE "PROMISING BUT NOT PROVEN", sest efekti ei ole naha.
  See EI OLE "SAMPLE/REGIME DEPENDENT", sest ta ei ole uheski
  alamvalimis oluline.


  ERALDI JARELDUS B1 KOHTA — MITTE B2 KLASSIFIKATSIOON

  B1 peatulemus (TIER 1 paevane +4.27 bp, t = 4.97) ei kordu
  sunkroonsetel hindadel. Sama kella-reegel H1-hindadel annab +2.04 bp
  (p = 0.140) asemel +7.28 bp (p = 0.000).

  B1 sai staatuse "PROMISING BUT NOT PROVEN". B2 ei muuda seda staatust
  ametlikult, aga lisab konkreetse kahtluse, mida tuleb B3-s kontrollida:
  kas ristloikeline tsentreerimine mittesunkroonsetel paevastel hindadel
  loob teatepaevadel nait-serva.

  ÄRA ALUSTA B3. See on kirjas siin ainult seetottu, et leid ei lahe
  kaotsi.
