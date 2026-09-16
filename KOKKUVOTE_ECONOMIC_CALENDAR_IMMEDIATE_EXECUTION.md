===============================================================================
NEMSIS — ECONOMIC CALENDAR IMMEDIATE RELEASE EXECUTION TEST
===============================================================================
  16. september 2026
  branch  claude/great-noether-um7382
  seeme   20260916 (koik randomiseerimised fikseeritud)
  Uurimistoo. Live-botti EI PUUDUTATUD, /update EI SAADETUD.


===============================================================================
1. EXECUTIVE SUMMARY
===============================================================================

  KLASSIFIKATSIOON:  FAIL
  (korge resolutsiooni kinnitus eraldi: DATA INSUFFICIENT, n = 15 / 39)

  Hupe on OLEMAS ja ta on SUUR. Ta on lihtsalt LABI, enne kui esimene
  taidetav hind saabub.

  Mooedetud, RADA A (M5), 15 TIER 1 sundmust |z| >= 1:
    |liikumine| 0 -> +5 min   mediaan 17.0 bp, p90 37.0 bp
    sellest 94% kogu 60-minutilisest liikumisest on juba toimunud
    +5 minuti hetkeks (mediaan suhe)

  Margiga, signaali suunas:
    0 -> 5 min    +5.91 bp   t = 0.98   <- HUPE, EI OLE KAUBELDAV
    5 -> 15 min   +0.47 bp   t = 0.46
    15 -> 30 min  +2.10 bp   t = 1.51
    30 -> 60 min  -0.56 bp   t = -0.31

  PRIMARY (sisenemine esimesel taidetaval hinnal, hoid 30 min):
    rada          n    bruto    kulu    neto      t       p
    RADA A  M5   15    +1.22    2.19   -0.97   0.96   0.339
    RADA B  M15  39    +1.40    2.22   -0.82   0.95   0.341
    RADA C  H1  408    -0.09    2.25   -2.34  -0.11   0.913   (hoid 60 min)

  Paaritatud juhusliku suuna baas (2000 katset, samad sundmused, sama
  sisenemine ja valjumine, ainult suund juhuslik):
    RADA A   signaal +1.22 vs juhuslik mediaan -0.03   p = 0.174
    RADA B   signaal +1.40 vs juhuslik mediaan -0.03   p = 0.187
    RADA C   signaal -0.09 vs juhuslik mediaan +0.03   p = 0.558

  Murdepunkt (kulu, mille juures ootus = 0):
    RADA A  1.22 bp    RADA B  1.40 bp    RADA C  -0.09 bp
  Eeldatud kulu ILMA sundmuse libisemiseta on 2.19-2.25 bp.
  Strateegia on ule murdepunkti juba enne, kui uudise libisemine
  uldse arvesse voetakse.

  UKS ASI ON POSITIIVNE JA SEDA EI VARJATA: 205 EUR konto SUUDAKS seda
  taita. 30-minutilise hoiu sigma on 0.037-0.110%, seega 0.01 lot riskib
  ainult 0.18-0.46% kontost. 0.50% riski juures on taidetav 5/5 paari.
  See on esimene kord kogu NEMSIS-i uurimisprogrammis, kus 205 EUR EI
  OLE piirav tegur. Piirav tegur on see, et serva ei ole.


===============================================================================
2. MIS ON UUS — VAHE B1 JA B2 SUHTES
===============================================================================

  Neid EI SEGATA. B1 ja B2 definitsioone EI MUUDETUD.

  B1 (KOKKUVOTE_ECONOMIC_CALENDAR_B1.md)
    paevane efekt, sisenemine tunde hiljem, ristloikeliselt
    tsentreeritud valuutatootlus, 2013-2026, TIER 1 1d +4.27 bp
    verdikt: PROMISING BUT NOT PROVEN

  B2 (KOKKUVOTE_ECONOMIC_CALENDAR_B2.md)
    viivitatud efekt T+8h -> T+32h, H1-baarid
    leidis, et kogu efekt on loigus 0h -> 1h: +9.55 bp, t = 11.51
    verdikt: NO ROBUST DELAYED EFFECT FOUND

  SEE TEST (uus)
    VAHETU VALJALASKE TAITMINE. Kusimus ei ole "kas efekt on olemas",
    vaid "kas selle esimene osa on TAIDETAV".
    Erinevused, mis on teadlikud ja markitud:
      - UHE PAARI TOORES log-tootlus, MITTE ristloikeliselt
        tsentreeritud valuutatootlus (see on taitmistest uhel
        instrumendil, mitte turuneutraalne korv)
      - korgeim olemasolev resolutsioon (M5), mitte H1 ega paevane
      - sisenemine esimesel hinnal, mis on RANGELT parast valjalaset
    Seetottu EI OLE selle testi bp-numbrid otse vorreldavad B1/B2
    omadega.


===============================================================================
3. ANDMEAUDIT — MIS ON JA MIS PUUDUB
===============================================================================

  PUUDUB TAIELIKULT (kontrollitud, mitte eeldatud):
    tick-andmed      EI OLE
    bid/ask          EI OLE   => taitmishind on SIMULEERITUD
    M1               EI OLE   => D1 (+1 min) on DATA INSUFFICIENT

  OLEMAS — KOLM RADA, iga uks eraldi margitud:
    RADA A  M5    2026-08-05 .. 2026-09-16    41 paeva   T1 |z|>=1:  15
    RADA B  M15   2026-06-22 .. 2026-09-11    80 paeva   T1 |z|>=1:  39
    RADA C  H1    2023-11-27 .. 2026-09-11  1019 paeva   T1 |z|>=1: 408

  M5-andmed laeti selle uuringu jaoks Yahoo'st Supabase kaudu
  (bot/sb_m5.py). Yahoo annab 5-minutilisi baare AINULT ~60 paeva
  tagasi — seda EI SAA pikendada ja seda EI OLE voltsitud.

  TAGAJARG, MIS TULEB VALJA OELDA:
    RADA A ja RADA B ei kanna jareldavat statistikat (n = 15 ja 39).
    Nad on KIRJELDAVAD.
    RADA C kannab statistikat (n = 408), AGA tema vaikseim samm on tund,
    seega ta EI SAA vastata kusimusele "kas hupet saab taita".
    Kumbki rada uksinda ei anna lopplikku vastust. Koos annavad.


===============================================================================
4. TAPNE PRIMARY REEGEL
===============================================================================

  ULLATUS (cal_engine.z_ullatus, KUTSUTAKSE OTSE, ei kopeerita)
    z = (actual - forecast) / rull-std(20 VARASEMAT sama
        (valuuta, indikaator) prognoosiviga, min 10 vaatlust)
    shift(1) enne rolling'ut. Lookahead'i ei ole.

  SUUND
    suund_valuuta = sign(z) * eelregistreeritud majanduslik mark
    +1 = OSTA valuuta

  LAVI
    PRIMARY |z| >= 1.0
    tundlikkus 1.5 ja 2.0 (eelmaaratud, EI OPTIMEERITUD)

  SUNDMUSE AEG
    TradingView kalendri tegelik UTC valjalaske ajatempel.
    EI tuletatud kuupaevast. EI kasutatud paevabaare.

  SISENEMINE  D0
    esimene baar, mille SULGEMINE on RANGELT PARAST valjalaset.
    Tegelik viivitus: RADA A mediaan 5 min, RADA B 15 min,
    RADA C 30 min (min 10, max 70).

  HOID
    PRIMARY 30 min. Tundlikkus 5 / 15 / 60 / 120 min.
    RADA C ei suuda 30 min hoidu (baar on 60 min) — DATA INSUFFICIENT,
    seal on hoid 60 min.

  INSTRUMENDIKAART (fikseeritud ENNE tulemuste nagemist)
    EUR -> EURUSD (baas)     USD -> EURUSD (kvoot)
    GBP -> GBPUSD (baas)     JPY -> USDJPY (kvoot)
    CHF -> USDCHF (kvoot)    AUD -> AUDUSD (baas)
    CAD -> USDCAD (kvoot)    NZD -> NZDUSD (baas)
    OSTA valuuta => osta paar, kui valuuta on BAAS; muu paar, kui KVOOT.

  KULU
    paaripohine uhesuunaline bp x 2 (edasi-tagasi):
    EURUSD 1.0, USDJPY 1.0, GBPUSD 1.2, AUDUSD 1.2, USDCHF 1.3,
    USDCAD 1.3, NZDUSD 1.8 bp
    Sundmuse LISALIBISEMINE rakendub UKS KORD sisenemisel:
    0 / 1 / 2 / 3 / 5 / 10 bp (eelmaaratud, EI VALITUD tagantjarele).


===============================================================================
5. KRIITILINE VIGA, MILLE EELAUDIT LEIDIS
===============================================================================

  Makroteated tulevad kellaaegadel :00 :15 :30 :45. Need langevad TAPSELT
  kokku M5 / M15 / H1 baaride sulgemisega. Kell 12:30 valjalaske korral
  sulgeb baar 12:25-12:30 tapselt valjalaske hetkel ja on TERVIKUNA
  teate-EELNE.

  Esimene implementatsioon kasutas vordust (sulgemine >= T) ja sisenes
  selle baari sulgemisel. Tulemus: sisenemisviivitus oli KOIGIL sundmustel
  tapselt 0.0 minutit ja bruto oli +10.79 bp.

  See oli LOOKAHEAD: kaubeldi teate-eelse hinnaga, teades juba teadet.

  Audit E1 leidis selle ENNE tulemuste klassifitseerimist. Parandus:
  sulgemine peab olema RANGELT parast valjalaset.

  MOJU:
    enne parandust   bruto +10.79 bp   (lookahead)
    parast parandust bruto  +1.22 bp   (taidetav)

  See uks parandus on kogu selle raporti tulemuse ja "lubava" tulemuse
  vahe. Iga tulevane uudistestija peab seda kontrollima.


===============================================================================
6. KUS LIIKUMINE TOIMUB (KIRJELDAV, MARGITA)
===============================================================================

  Ankur = viimane sulgemine ENNE valjalaset (teate-eelne hind).

  RADA A (M5), n = 15
  aken           mediaan   keskm     p75     p90     p95   osa 60min-st
  ----------     -------   -----   -----   -----   -----   ------------
  0 -> +5 min       17.0    16.4    29.8    37.0    41.4        94%
  0 -> +15 min      20.9    18.1    32.7    41.6    43.6       107%
  0 -> +30 min      21.5    18.6    29.9    32.4    39.6       120%
  0 -> +60 min      11.6    15.6    28.9    30.5    34.0       100%
  0 -> +1 min     DATA INSUFFICIENT (M1-andmeid ei ole)

  RADA B (M15), n = 39
  0 -> +15 min       9.4    14.4    23.7    36.4    37.7        69%
  0 -> +30 min      11.5    15.5    26.3    38.1    42.2        79%
  0 -> +60 min      18.3    18.5    31.1    34.0    36.5       100%

  LUGEMISJUHIS: "osa 60min-st" on mediaan suhe |r(0->m)| / |r(0->60)|.
  Uleval 100% tahendab, et liikumine LABIS 60-minutilise taseme ja tuli
  tagasi. RADA A juures on 94% juba +5 minuti hetkeks olemas.

  MIDA SEE EI TOENDA: n = 15 ja n = 39. Need on kirjeldavad numbrid,
  mitte statistiline toend. Suund on aga sama molemal rajal ja kooskolas
  B2 leiuga (kogu efekt loigus 0h -> 1h).


===============================================================================
7. MARGIGA INKREMENDID — HUPE vs KAUBELDAV DRIFT
===============================================================================

  RADA A (M5), n = 15, signaali suunas

  loik                n   keskm_bp   med_bp    wr%      t       p
  ---------------   ---   --------   ------   ----   ----   -----
  0 -> 5 min  HUPE   15      +5.91    +1.16   66.7   0.98   0.325   EI OLE
                                                                     KAUBELDAV
  5 -> 15 min        15      +0.47    +0.00   33.3   0.46   0.643
  15 -> 30 min       15      +2.10    +3.49   60.0   1.51   0.132
  30 -> 60 min       15      -0.56    +1.16   60.0  -0.31   0.755

  VASTUS KUSIMUSELE, MIS OLI ULESANDE SUDA:
    Enamik statistilisest servast tekib valjalaske ja esimese taidetava
    hinna VAHEL. Parast seda on iga kaubeldav loik murane ja ukski ei
    ole oluline.


===============================================================================
8. PRIMARY TULEMUSED
===============================================================================

  test                      n   bruto    med   kulu   lib   neto   wr%      t       p
  --------------------   ----   -----   ----   ----   ---   ----   ----   ----   -----
  RADA A  M5  PRIMARY      15   +1.22  +1.16   2.19   0.0  -0.97   66.7   0.96   0.339
  RADA B  M15 PRIMARY      39   +1.40  +2.32   2.22   0.0  -0.82   53.8   0.95   0.341
  RADA C  H1  30 min      DATA INSUFFICIENT (baar 60 min > hoid 30 min)
  RADA C  H1  D0 + 60 min 408   -0.09  -1.16   2.25   0.0  -2.34   45.6  -0.11   0.913

  Sisenemisviivitus: RADA A mediaan 5 min, RADA B 15 min, RADA C 30 min.

  ULLATUSE LAVE (eelmaaratud, EI OPTIMEERITUD)
  RADA A  |z|>=1.0    15   +1.22   2.19   -0.97   66.7   0.96   0.339
  RADA B  |z|>=1.0    39   +1.40   2.22   -0.82   53.8   0.95   0.341
  RADA A  |z|>=1.5     7   +1.72   2.17   -0.45   71.4   0.70   0.485
  RADA B  |z|>=1.5    21   +1.38   2.17   -0.79   57.1   0.76   0.446
  RADA A  |z|>=2.0     5   +2.40   2.24   +0.16   80.0   0.72   0.471
  RADA B  |z|>=2.0    13   +3.83   2.17   +1.66   69.2   1.80   0.071

  |z| >= 2 on molemal rajal neto POSITIIVNE. See on ainus koht, kus
  neto ulatub nulli. AGA: n = 5 ja n = 13, p = 0.471 ja 0.071, ja
  RADA C-l (n = 90 samas vahemikus) on |z| >= 2 neto -0.36 bp.
  Seda EI NIMETATA leiuks.


===============================================================================
9. SISENEMISVIIVITUSE JA HOIU TUNDLIKKUS
===============================================================================

  VIIVITUS (PRIMARY = D0)
  test                  n   bruto    neto    wr%      t       p
  -----------------   ---   -----   -----   ----   ----   -----
  RADA A  D0           15   +1.22   -0.97   66.7   0.96   0.339
  D1  +1 min          DATA INSUFFICIENT (M1-andmeid ei ole)
  RADA A  D5           15   +0.84   -1.35   53.3   0.77   0.439
  RADA A  D15          15   -0.64   -2.83   60.0  -0.51   0.612
  RADA B  D15          39   +4.04   +1.82   69.2   3.57   0.000
  RADA A  D30          15   +0.16   -2.03   46.7   0.09   0.927
  RADA B  D30          39   +3.69   +1.47   64.1   2.33   0.020
  RADA A  D60          15   +2.00   -0.19   60.0   1.65   0.099
  RADA B  D60          39   -0.47   -2.69   35.9  -0.50   0.618

  HOID (PRIMARY = 30 min)
  RADA A  hoid 5 min   15   -1.80   -3.98    6.7  -3.08   0.002
  RADA B  hoid 5 min  DATA INSUFFICIENT (baar 15 min)
  RADA A  hoid 15 min  15   -0.93   -3.12   13.3  -0.89   0.372
  RADA B  hoid 15 min  39   +0.09   -2.13   46.2   0.08   0.933
  RADA A  hoid 30 min  15   +1.22   -0.97   66.7   0.96   0.339  PRIMARY
  RADA B  hoid 30 min  39   +1.40   -0.82   53.8   0.95   0.341  PRIMARY
  RADA A  hoid 60 min  15   +0.53   -1.66   60.0   0.33   0.739
  RADA B  hoid 60 min  39   +3.78   +1.56   64.1   2.14   0.032
  RADA A  hoid 120 min 15   -0.08   -2.27   60.0  -0.03   0.974
  RADA B  hoid 120 min 39   +2.81   +0.59   64.1   1.60   0.111

  KOLM LAHTRIT ON "ILUSAD": RADA B D15 (+4.04, p = 0.000),
  RADA B D30 (+3.69, p = 0.020), RADA B hoid 60 (+3.78, p = 0.032).

  MIKS NEED EI OLE LEID:
    1 Nad ei ole PRIMARY. Primary oli fikseeritud enne tulemusi.
    2 Nad on 3 lahtrit ~20 arvutatud lahtrist.
    3 RADA A annab KATTUVATEL andmetel VASTUPIDISE tulemuse:
      D15 rajal A on -0.64 bp, rajal B +4.04 bp. Sama periood, sama
      sundmused, ainult erinev baarisamm. Kahe raja lahkuminek sellises
      suuruses tahendab MURA, mitte efekti.
    4 n = 39 ja aken on 80 paeva.
    Nende peale strateegia ehitamine oleks tagantjarele parima valimine.


===============================================================================
10. KULU, LIBISEMINE JA MURDEPUNKT
===============================================================================

  Libisemine rakendub UKS KORD sisenemisel.

  RADA A  M5 (bruto +1.22, kulu 2.19)
    +0 bp -> neto -0.97      +3 bp -> neto -3.97
    +1 bp -> neto -1.97      +5 bp -> neto -5.97
    +2 bp -> neto -2.97     +10 bp -> neto -10.97
    MURDEPUNKT  1.22 bp    tegelik kulu 2.19 bp    VARU -0.97 bp

  RADA B  M15 (bruto +1.40, kulu 2.22)
    +0 bp -> neto -0.82     +5 bp -> neto -5.82
    MURDEPUNKT  1.40 bp    tegelik kulu 2.22 bp    VARU -0.82 bp

  RADA C  H1 (bruto -0.09, kulu 2.25)
    +0 bp -> neto -2.34    +10 bp -> neto -12.34
    MURDEPUNKT -0.09 bp    tegelik kulu 2.25 bp    VARU -2.34 bp

  See on koige selgem viis tulemust naha: maksimaalne kulu, mida
  strateegia talub, on 1.22-1.40 bp. Tavaline spread ILMA uudise
  libisemiseta on juba 2.19-2.25 bp. Uudise ajal on spread
  tuupiliselt LAIEM, mitte kitsam.


===============================================================================
11. PAARITATUD JUHUSLIKU SUUNA BAAS
===============================================================================

  2000 katset. Samad sundmused, sama sisenemine ja valjumine, AINULT
  suund juhuslik. Jarjekorra permutatsiooni EI KASUTATUD.

  rada          n   signaal   juhuslik   juhuslik    vahe       p   boot 95% CI
                              mediaan       95%
  ---------   ---   -------   --------   --------   -----   -----   --------------
  RADA A  M5   15     +1.22      -0.03      +2.15   +1.25   0.174   [-1.13, +3.72]
  RADA B  M15  39     +1.40      -0.03      +2.38   +1.43   0.187   [-1.37, +4.26]
  RADA C  H1  408     -0.09      +0.03      +1.36   -0.12   0.558   [-1.66, +1.49]

  Ukski rada ei loo juhuslikku suunda. Koigi kolme bootstrap-
  usaldusvahemik sisaldab nulli.


===============================================================================
12. KRONOLOOGILINE JAOTUS
===============================================================================

  RADA A (41 paeva) ja RADA B (80 paeva) on liiga luhikesed
  kolmeosaliseks jaotuseks. Seda EI SURUTUD.

  RADA C (2.79 a), kalendriaasta-pohine jaotus (sama mis B2):
  osa                 n   bruto    neto    wr%      t       p
  ---------------   ---   -----   -----   ----   ----   -----
  TRAIN  .. 2024    133   -2.05   -4.34   36.8  -1.55   0.122
  VALID  2025       151   +0.03   -2.21   46.4   0.02   0.985
  FINAL OOS 2026    124   +1.86   -0.37   54.0   1.65   0.100

  FINAL OOS on bruto positiivne (+1.86 bp) ja neto endiselt negatiivne
  (-0.37 bp), p = 0.100. See EI OLE kinnitus, aga ta ei ole ka
  umberlukkamine. Aus sona: EBASELGE, kaldub nulli poole.


===============================================================================
13. VALUUTA KAUPA (RADA C, ainus statistiliselt kandev valim)
===============================================================================

  valuuta (paar)      n   bruto    neto    wr%      t       p
  ---------------   ---   -----   -----   ----   ----   -----
  USD (EURUSD)       57   +4.11   +2.11   52.6   1.22   0.224
  EUR (EURUSD)      125   +0.47   -1.53   46.4   0.39   0.693
  GBP (GBPUSD)       58   -1.92   -4.32   34.5  -1.25   0.212
  JPY (USDJPY)       34   +1.54   -0.46   52.9   0.44   0.659
  CHF (USDCHF)       43   -7.90  -10.50   23.3  -3.18   0.001
  CAD (USDCAD)       48   -1.78   -4.38   47.9  -0.93   0.353
  AUD (AUDUSD)       36   +2.72   +0.32   61.1   1.21   0.228
  NZD (NZDUSD)        7   +8.06   +4.46   71.4   1.00   0.318

  bruto positiivseid: 5/8.  neto positiivseid: 3/8.
  AINUS statistiliselt oluline valuuta on CHF ja ta on NEGATIIVNE
  (t = -3.18, wr 23.3%). Ma EI EEMALDA teda ja EI POORA marki umber.


===============================================================================
14. INDIKAATOR JA EELMAARATUD GRUPID (RADA C)
===============================================================================

  indikaator (mark)                n   bruto    neto    wr%      t       p
  ----------------------------   ---   -----   -----   ----   ----   -----
  Core Inflation Rate (+1)        53   -0.75   -2.80   50.9  -0.27   0.790
  Employment Change (+1)          37   +1.23   -1.16   54.1   0.52   0.601
  GDP Annual Growth Rate (+1)     17   -3.53   -5.86   35.3  -1.36   0.174
  GDP Growth Rate (+1)            34   -0.71   -2.75   35.3  -0.25   0.804
  Inflation Rate (+1)             64   -0.56   -2.85   48.4  -0.25   0.805
  Inflation Rate Mom (+1)         43   +2.15   -0.22   53.5   0.71   0.479
  Interest Rate (+1)               6   -4.05   -6.85   33.3  -0.38   0.708
  Non Farm Payrolls (+1)          11   +0.61   -1.39   54.5   0.11   0.908
  Retail Sales MoM (+1)           36   -2.31   -4.60   36.1  -1.07   0.285
  Retail Sales YoY (+1)           39   +3.70   +1.44   41.0   1.61   0.107
  Unemployment Rate (-1)          68   -0.86   -3.15   44.1  -0.49   0.623

  EELMAARATUD GRUPID (B1 klassifikatsioon, uusi EI LOODUD)
  CPI / inflatsioon              160   +0.11   -2.13   50.6   0.07   0.944
  toohoive / NFP                  48   +1.09   -1.21   54.2   0.51   0.614
  tootus                          68   -0.86   -3.15   44.1  -0.49   0.623
  SKP                             51   -1.65   -3.78   35.3  -0.79   0.431
  intressiotsus                    6   -4.05   -6.85   33.3  -0.38   0.708
  jaemuuk                         75   +0.82   -1.46   38.7   0.51   0.612
  PMI                             PMI ei kuulu B1 TIER 1 hulka;
                                  uut kategooriat EI LOODUD

  TIER 2 (vordluseks)            423   +0.33   -1.97   48.7   0.38   0.701

  Ukski indikaator ega grupp ei ole oluline. Ukski neto ei ole
  usaldusvaarselt positiivne. TIER 1 ja TIER 2 on siin sisuliselt
  samad — vordluseks: B1 paevasel horisondil oli TIER 1 neli korda
  tugevam kui TIER 2. Vahetu taitmise juures see vahe KAOB.


===============================================================================
15. ULLATUSE SUURUS JA SESSIOON (RADA C, kirjeldav)
===============================================================================

  vahemik                n   bruto    neto    wr%      t       p
  ------------------   ---   -----   -----   ----   ----   -----
  1.0 <= |z| < 1.5     223   -0.87   -3.12   47.5  -0.82   0.412
  1.5 <= |z| < 2.0      95   -0.08   -2.40   40.0  -0.05   0.962
  |z| >= 2.0            90   +1.84   -0.36   46.7   0.93   0.351

  Monotoonsust on veidi (negatiivne -> null -> napilt positiivne), aga
  ukski vahemik ei ole oluline ja ukski neto ei ole positiivne.

  SESSIOON (UTC, aknaid EI OPTIMEERITUD)
  Aasia 00-07               97   -1.34   -3.83   42.3  -0.91   0.361
  London 07-12             167   -0.71   -2.83   42.5  -0.66   0.508
  London+NY kattuvus 12-16 104   +1.71   -0.56   51.0   0.84   0.402
  NY 16-21                 (alla 5 sundmuse)
  Aasia avanemine 21-24     39   +1.60   -0.60   53.8   0.51   0.613


===============================================================================
16. TEOSTATAVUS 205 EUR KONTOL
===============================================================================

  See on ainus sektsioon, kus tulemus on POSITIIVNE.

  tehinguid RADA C: 408 / 2.77 a = 147 aastas
  hoidmisaeg 30-60 min

  paar       30min sigma%   0.01 lot EUR   1-sigma EUR   % kontost
  -------    ------------   ------------   -----------   ---------
  AUDUSD            0.106            867          0.92        0.45
  EURUSD            0.037           1000          0.37        0.18
  GBPUSD            0.106            867          0.92        0.45
  USDCAD            0.110            867          0.95        0.46
  USDCHF            0.074            867          0.64        0.31

  kavatsetud risk 0.25% = 0.51 EUR -> taidetav 1/5 paaril
                                      vajalik konto 148-380 EUR
  kavatsetud risk 0.50% = 1.02 EUR -> taidetav 5/5 paaril
                                      vajalik konto  74-190 EUR

  VERDIKT: EXECUTABLE AT EUR 205 (0.50% riski juures koik 5 paari;
  0.25% juures 1/5 ja vajalik konto ~380 EUR).

  MIKS SEE ERINEB KOIGIST VARASEMATEST NEMSIS-i UURINGUTEST: hoid on
  30-60 minutit, mitte 24 tundi ega 4 nadalat. Luhike hoid tahendab
  vaikest sigmat, ja vaike sigma tahendab, et min lot 0.01 mahub
  riskieelarvesse. See on paris leid ja ta salvestatakse siia, isegi
  kui sellel konkreetsel strateegial serva ei ole.


===============================================================================
17. LOOKAHEAD JA KORREKTSUSAUDIT
===============================================================================

  bot/cal_imm_audit.py — 29 kontrolli, 0 FAIL. Jooksis ENNE tulemuste
  klassifitseerimist.

  A  B1/B2 definitsioonid muutmata; z-mootor kutsutakse otse; z ei
     kasuta tulevikku (sunteetiline test); see test EI kasuta
     ristloikelist tsentreerimist (teadlik ja margitud erinevus)
  B  instrumendikaart fikseeritud enne tulemusi; OSTA EUR => +EURUSD;
     OSTA USD => -EURUSD; kulu paaripohine
  C  tick / bid-ask / M1 puuduvad — kirjas; koik kolm rada olemas
  D  ajatemplid: keskoo-platsihoidjaid 0; minutid 0/15/20/30/45/50;
     valjalaske M5-baar on 10.0x volatiilsem kui tavaline baar
     (10.42 bp vs 1.04 bp) => ajatempel on minutitapsusega OIGE
  E  sisenemine ALATI parast valjalaset (min 5 min); valjumine ALATI
     parast sisenemist; hoid >= 30 min; M15 viivitus > M5 viivitus
  F  kulu edasi-tagasi; libisemine rakendub uks kord; murdepunkt = bruto
  G  teadaolev vastus: konstantne +0.1% -> 9.995 bp; juhusliku baasi
     mediaan konstantsel seerial ~0

  AJATEMPLI-EBAKINDLAID SUNDMUSI: 0. Koik ajad on usutavad
  valjalaskeajad. Uhtegi sundmust EI JAETUD valja ajatempli tottu.

  VALJA JAETUD: sundmused, kus hinnaandmetes on lunk (nadalavahetus,
  andmeauk) ja lahim baar on kaugemal kui 2 baari. Proksit EI ASENDATUD.

  MIDA AUDIT EI TOENDA: audit toendab, et see test ei vaata tulevikku.
  Ta EI TOENDA, et kalendri 'actual' on esialgne trukk — TradingView API
  ei anna revisjoni-valja. See B1 piirang jaab lahendamata.


===============================================================================
18. MITMIKTESTIMINE
===============================================================================

  PRIMARY on UKS test: |z| >= 1, TIER 1, D0 sisenemine, 30 min hoid,
  koik kehtivad valuutad, korgeim olemasolev resolutsioon.
  See oli fikseeritud enne tulemusi.

  Koik ulejaanu on secondary/kirjeldav: 3 lavet, 6 viivitust, 5 hoidu,
  6 libisemistaset, 8 valuutat, 11 indikaatorit, 6 gruppi, 3 magnituudi,
  5 sessiooni. Kokku ~60 arvutatud lahtrit.

  Nendest 3 on nominaalselt olulised ja POSITIIVSED:
    RADA B D15 p = 0.000,  RADA B D30 p = 0.020,  RADA B hoid 60 p = 0.032
  Ja 2 on nominaalselt olulised ja NEGATIIVSED:
    RADA A hoid 5 min p = 0.002,  CHF p = 0.001

  60 lahtri juures on ~3 nominaalselt olulist tulemust tapselt see, mida
  juhus annab. Lisaks annab RADA A samadel andmetel D15 juures
  VASTUPIDISE margi. Ma EI KUULUTA neist uhtegi leiuks.


===============================================================================
19. VASTUS KESKSELE KUSIMUSELE
===============================================================================

  KUSIMUS: "Kui mul oleks reaalajas majanduskalender ja ma saaksin
  actual + forecast valjalaske hetkel, kas parast valjalaset oleks
  piisavalt hinnaliikumist, et realistlikult siseneda ja saada
  positiivne serv parast spreadi ja libisemist?"

  VASTUS: EI.

  A) TEOREETILINE SUNDMUSE HUPE — SUUR JA PARIS
     |liikumine| valjalaskest +5 min: mediaan 17.0 bp, p90 37.0 bp.
     Valjalaske M5-baar on 10.0x volatiilsem kui tavaline baar.
     Margiga: 0 -> 5 min annab +5.91 bp.
     Hupe EI OLE kahtluse all.

  B) PARAST-VALJALASET KAUBELDAV LIIKUMINE — PRAKTILISELT NULL
     94% (mediaan) kogu 60-minutilisest liikumisest on juba toimunud
     +5 minuti hetkeks.
     Kaubeldavad loigud: 5->15 min +0.47 bp, 15->30 min +2.10 bp,
     30->60 min -0.56 bp. Ukski ei ole oluline.

  C) REALISTLIK TAITMISTULEMUS — NEGATIIVNE
     Parim taidetav sisenemine (M5, mediaan 5 min viivitus) annab
     bruto +1.22 bp. Tavaline spread ilma uudise libisemiseta on
     2.19 bp. Neto -0.97 bp.
     Suurima valimiga rada (n = 408) annab bruto -0.09 bp.
     Juhuslik suund ei ole loodud (p = 0.174 / 0.187 / 0.558).

  UHE LAUSEGA: hupe on suur, aga ta juhtub sekunditega, ja esimene
  hind, mida sa saad, on juba hupppe teisel pool.

  MIS SEDA MUUDAKS: M1- voi tick-andmed koos paris bid/ask'iga naitaksid,
  kas 0-60 sekundi aknas on midagi. Seda EI SAA praeguste andmetega
  otsustada ja see on markitud DATA INSUFFICIENT, mitte FAIL.


===============================================================================
20. PIIRANGUD
===============================================================================

  1 VALIM. Korge resolutsiooni rajad on 15 ja 39 sundmust. See EI OLE
    piisav jareldava statistika jaoks. Nad on kirjeldavad.

  2 M5 AJALUGU. Yahoo annab 5m baare ~60 paeva tagasi. Seda EI SAA
    pikendada ilma tasulise allikata.

  3 TAITMISHIND ON SIMULEERITUD. Bid/ask'i ei ole. Kasutame sulgemist
    kui teoreetilist kesk-hinda ja lisame eelmaaratud libisemise
    stsenaariumid. Uudise ajal on spread tegelikult laiem ja
    taitmine halvem kui uheski meie stsenaariumis.

  4 0-60 SEKUNDI AKEN ON TAIESTI KATMATA. Kui serv on seal, see test
    seda ei naeks. DATA INSUFFICIENT, mitte FAIL.

  5 REVISJON. Ei saa kinnitada, et 'actual' on esialgne trukk.
    B1 piirang, jaab lahendamata.

  6 RADA C EI OLE TAITMISTEST. Tema sisenemisviivitus on mediaan
    30 min (max 70 min). Ta annab statistilise massi, aga ta ei
    vasta taitmiskusimusele.

  7 KOLM RADA LAHEVAD LAHKU. RADA A ja RADA B annavad D15 juures
    vastupidise margi samadel sundmustel. See on aus mark sellest,
    kui murane kogu asi selle valimi juures on.


===============================================================================
21. LOPPKLASSIFIKATSIOON
===============================================================================

              FAIL

  ja eraldi, korge resolutsiooni kinnituse kohta:

              DATA INSUFFICIENT  (0-60 sekundi aken, n = 15 / 39)

  MIKS FAIL, MITTE WEAK VOI INTERESTING:
    - PRIMARY on neto NEGATIIVNE koigil kolmel rajal
    - murdepunkt (1.22-1.40 bp) on ALLPOOL tavalist spreadi (2.19-2.25 bp)
      juba enne uudise libisemise lisamist
    - paaritatud juhusliku suuna baasi EI LOODA uhelgi rajal
      (p = 0.174 / 0.187 / 0.558)
    - suurima valimiga rada (n = 408) annab bruto -0.09 bp
    - ainus oluline valuuta on CHF ja ta on negatiivne

  MIKS MITTE "DATA INSUFFICIENT" TERVIKUNA:
    RADA C (n = 408, 2.79 aastat) vastab selgelt kusimusele, kas
    tunnise resolutsiooniga on midagi votta: ei ole. Ja 94% liikumisest
    +5 minuti hetkeks on mooedetud fakt, mitte spekulatsioon.

  MA EI ALANDA STANDARDIT, ET SAADA POSITIIVNE TULEMUS, ega tosta seda,
  et positiivset tappa. Kui neto oleks olnud napilt positiivne ja
  juhuslik baas loodud, oleks klassifikatsioon olnud WEAK voi
  INTERESTING. Ta ei ole.

  UKS ASI, MIS JAAB KIRJA POSITIIVSENA: luhike hoid (30-60 min) teeb
  205 EUR konto TAIDETAVAKS (0.50% risk, 5/5 paari). See on esimene
  kord kogu programmis. Kui tulevikus leitakse luhikese hoiuga serv,
  siis kontosuurus ei ole enam takistus.
