===============================================================================
NEMSIS — ECONOMIC CALENDAR SUB-60-SECOND EXECUTION TEST
===============================================================================
  16. september 2026
  branch  claude/great-noether-um7382
  seeme   20260916
  Uurimistoo. Live-botti EI PUUDUTATUD, /update EI SAADETUD.


===============================================================================
1. EXECUTIVE SUMMARY
===============================================================================

  LOPPKLASSIFIKATSIOON:  DATA INSUFFICIENT

  Kusimus oli: kas hupet saab puuda 0-60 SEKUNDI jooksul?
  Vastus: seda EI SAA PRAEGU TEADA, sest sekundi-tasandi andmeid ei ole
  kattesaadav ja neid EI FABRITSEERITUD.

  MIS ON UUS JA MOOEDETUD. Laeti Yahoo M1 (1-minutilised) baarid seitsmele
  majorile — koige peenem resolutsioon, mis ilma tasulise allikata
  saadaval. See lubab MOOTA TAPSELT UHE punkti: sisenemine T+60 s.

    RADA M1  D0 sisenemine (= T+60 s), hoid 60 s, TIER 1, |z| >= 1
      n = 10   bruto +2.03 bp   kulu 2.22 bp   neto -0.19 bp
      t = 1.84   p = 0.066
      juhusliku suuna pertsentiil 96.8%,  p = 0.037

  See uksi naeks huvitav valja. AGA:

    RADA M5  (kattuv perioodi osa, n = 15)  bruto -1.58 bp
             juhusliku suuna pertsentiil 0.6%,  p = 0.994
    RADA M15 (n = 39)                       bruto -0.16 bp,  p = 0.551

  Kaks rada annavad KATTUVAL perioodil VASTUPIDISE margi ja vastupidise
  pertsentiili. n = 10 vs n = 15. See on MURA, mitte leid.

  MIDA JAI TOESTAMATA, TAPSELT: 1 / 3 / 5 / 10 / 15 / 30 sekundi
  horisonte EI SAA MOOTA UHELGI rajal. Vaikseim baar on 60 s.
  Loigu 0 -> 60 s SISEMUS on endiselt taiesti avamata.

  KAS SEE ON SERV? EI. Isegi parim mooedetud punkt (RADA M1, +2.03 bp)
  jaab alla eeldatava tavalise round-trip kulu 2.22 bp, ENNE kui uudise
  libisemine uldse arvesse voetakse. Ja uudise libisemist EI SAA MOOTA,
  sest bid/ask-andmeid ei ole.


===============================================================================
2. TAPNE HUPOTEES
===============================================================================

  Kasutatud MUUTMATA B1/B2 mehhanism:

    z = (actual - forecast) / rull-std(20 VARASEMAT sama
        (valuuta, indikaator) prognoosiviga, min 10 vaatlust)
    shift(1) enne rolling'ut; tulevasi prognoosivigu EI KASUTATA.
    cal_engine.z_ullatus KUTSUTAKSE OTSE, ei kopeerita (audit 1b).

    suund = sign(z) * eelregistreeritud majanduslik mark
    universum = B1 TIER 1, 11 indikaatorit, liikmeid EI MUUDETUD
    lavi PRIMARY |z| >= 1.0; tundlikkus 1.5 ja 2.0

  INSTRUMENDIKAART (cal_imm.KAART, MUUTMATA):
    EUR -> EURUSD BASE     USD -> EURUSD QUOTE
    GBP -> GBPUSD BASE     JPY -> USDJPY QUOTE
    CHF -> USDCHF QUOTE    AUD -> AUDUSD BASE
    CAD -> USDCAD QUOTE    NZD -> NZDUSD BASE
  Kontrollitud audit B2/B3-ga: OSTA EUR => +EURUSD; OSTA USD => -EURUSD.

  PRIMARY: RADA M1, D0 sisenemine, hoid 60 s.


===============================================================================
3. ANDMEALLIKAD JA KATVUS
===============================================================================

  Liivakastil EI OLE otseuhendust. Kontrollitud: curl kolmele hostile
  andis HTTP 000 (dukascopy, histdata, yahoo). Ainus valjapaas on
  kasutaja Supabase `http` laiendus.

  allikas                     bid/ask   resolutsioon   periood      saadav
  -------------------------   -------   ------------   ----------   ------
  Dukascopy .bi5 tick         JAH       tick           2003-        EI
  HistData M1 / tick          JAH       M1 / tick      2000-        EI
  TrueFX tick                 JAH       tick           2009-        EI
  Yahoo Finance 1m            EI        M1 mid OHLC    ~28 paeva    JAH
  Yahoo Finance 5m            EI        M5 mid OHLC    ~60 paeva    JAH

  MIKS TICK EI OLE SAADAV — konkreetsed pohjused:
    Dukascopy: .bi5 on LZMA-pakitud BINAAR. pgsql-http tagastab
      `content` TEKSTINA; bytea-tagastust laiendusel ei ole, seega
      binaarne sisu rikutakse. EI PROOVITUD "parandada" — see oleks
      andmete voltsimine.
    HistData: nouab POST-vormi tokeniga ja tagastab ZIP-i. Sama takistus.
    TrueFX: ajalooarhiiv nouab registreerimist ja sisselogimist.
      Kasutaja API-votit EI KUSITUD (uurimisprotokolli reegel).

  YAHOO M1 PIIR ON MOOEDETUD, MITTE EELDATUD:
    7-paevased period1/period2 aknad 0-7, 7-14, 14-21 paeva tagasi
    annavad ~7100 baari kumbki; aknad 28 ja 35 paeva tagasi annavad
    0 rida. Seega ~28 paeva, MITTE rohkem.

  RADAD:
    rada    periood                     paevi   T1 |z|>=1   T1+T2 |z|>=1
    ----    ------------------------    -----   ---------   ------------
    M1      2026-08-19 .. 2026-09-16       28          10             22
    M5      2026-08-05 .. 2026-09-16       41          15             33
    M15     2026-06-22 .. 2026-09-11       80          39             72

  ANDMEKVALITEET (audit):
    kalendri T1 sundmusi |z|>=1 kokku            2016
    duplikaat-votmeid (aeg, valuuta, indikaator)    4 / 2016
    M1-ga seotud sundmusi                          10 (kadu 2006 —
                                                   valdavalt valjaspool
                                                   28-paevast akent)
    M5-ga seotud                                   15
    M15-ga seotud                                  39
    BID/ASK-iga sundmusi                            0
    ainult mid-hinnaga                            koik
    lungaga sundmused                    valja jaetud, proksit EI ASENDATUD


===============================================================================
4. EVENT TIMESTAMP VALIDATION
===============================================================================

  Kasutatud TradingView kalendri tegelikku UTC valjalaske ajatemplit.
  EI umardatud lahima baarini. EI tuletatud kuupaevast.

  audit 5   ajatempel on UTC (naive, UTC-na tolgendatud); hinnaindeks
            samuti UTC
  audit 6   DST on andmetes NAHTAV: NFP kellaajad on 12:30 (suveaeg) ja
            13:30 (talveaeg) — seega ajad EI OLE fikseeritud kohalikku
            aega sisse kulmutatud
  audit 7   minutitapsus: esinevad minutid 0, 15, 20, 30, 45, 50
  audit 7b  EMPIIRILINE KINNITUS: valjalaske M1-baari volatiilsus on
            8.13 bp vs tavaline baar 0.51 bp = 15.9x
            => ajatempel osutab OIGELE minutile

  Ajatempli-ebakindlaid sundmusi: 0. Uhtegi sundmust EI JAETUD valja
  ajatempli tottu.


===============================================================================
5. LOOKAHEAD AUDIT
===============================================================================

  bot/cal_sub60_audit.py — 21 kontrolli, 0 FAIL. Jooksis ENNE tulemusi.
  Kaetud on koik 12 kasutaja loetletud punkti.

   1  actual/forecast ainult valjalaske hetkel voi hiljem      PASS
      sunteetiline test: viimase vaartuse muutmine ei muuda
      uhtegi varasemat z-i
   2  entry price on kindlasti PARAST valjalaset               PASS
      n=10, min 60 s, mediaan 60 s, max 60 s
   3  kasutatud baar ei sisalda valjalaset ennast              PASS
   4  bar OPEN/CLOSE ei ole enne valjalaset                    PASS
   4b KRIITILINE LEID: 6/6 EURUSD-sundmusel sulgeb M1-baar
      TAPSELT valjalaske hetkel. Lubav (>=) reegel annaks
      LOOKAHEAD-tehingud. Range (>) reegel on KOHUSTUSLIK.
      (Sama viga leiti ja parandati eelmises testis, kus ta
       andis +10.79 bp asemel +1.22 bp.)
   5  ajavoond UTC                                             PASS
   6  DST mojutab event mappingut — kontrollitud, nahtav       PASS
   7  release timestamp tapne (15.9x volatiilsus)              PASS
   8  duplicate events: 4/2016 rida, loendatud                 PASS
   9  sama paar+sisenemisaeg mitu korda: 10 tehingut ->
      7 unikaalset (paar, sisenemisaeg), 3 kattuvat            PASS
  10  exit price on kindlasti tulevikus                        PASS
      mediaan hoid 60 s, min 60 s, max 120 s
  11  spread arvutatakse oigest poolest — EI SAA, bid/ask
      puudub; kasutatakse mid + eelmaaratud libisemist         PASS
  12  weekend/holiday lungad: sundmus jaetakse valja,
      proksit EI ASENDATA                                      PASS

  AUDITI KAIGUS PARANDATUD (enne tulemusi):
    Esialgne versioon kasutas RANGET vordlust ka VALJUMISEL, mis
    pikendas 60 s hoidu 120 s peale ilma pohjuseta. Valjumisel on
    vordus lubatud (baar, mis sulgeb siht-ajal, annab hinna, mis ON
    siht-ajal teada). Parandatud: sisenemine range, valjumine lubav.


===============================================================================
6. MIDA SAAB JA MIDA EI SAA MOOTA
===============================================================================

  horisont          M1     M5    M15   markus
  --------------   ----   ----   ----  --------------------------------
  viivitus   0 s    JAH    JAH    JAH
  viivitus   1 s     EI     EI     EI  DATA INSUFFICIENT
  viivitus   3 s     EI     EI     EI  DATA INSUFFICIENT
  viivitus   5 s     EI     EI     EI  DATA INSUFFICIENT
  viivitus  10 s     EI     EI     EI  DATA INSUFFICIENT
  viivitus  15 s     EI     EI     EI  DATA INSUFFICIENT
  viivitus  30 s     EI     EI     EI  DATA INSUFFICIENT
  viivitus  60 s    JAH     EI     EI
  hoid       5 s     EI     EI     EI  DATA INSUFFICIENT
  hoid      10 s     EI     EI     EI  DATA INSUFFICIENT
  hoid      15 s     EI     EI     EI  DATA INSUFFICIENT
  hoid      30 s     EI     EI     EI  DATA INSUFFICIENT
  hoid      60 s    JAH     EI     EI
  hoid     120 s    JAH     EI     EI

  TAHTIS TAPSUSTUS. RADA M1 "D0" tahendab PRAKTIKAS TAPSELT T+60 s,
  sest teated tulevad minuti piiril ja esimene baar, mis sulgeb rangelt
  parast valjalaset, sulgeb tapselt 60 sekundit hiljem. Koigil 10
  sundmusel oli viivitus TAPSELT 60 s.

  See tahendab: me mootsime 0-60 sekundi akna LOPP-PUNKTI, mitte tema
  sisemust. Sisemus jaab avamata.


===============================================================================
7. DELAY RESULTS
===============================================================================

  test                       n   bruto   kulu    neto    wr%      t       p
  ---------------------    ---   -----   ----   -----   ----   ----   -----
  RADA M1  viivitus   0 s   10   +2.03   2.22   -0.19   50.0   1.84   0.066  PRIMARY
  RADA M1  viivitus   1 s        DATA INSUFFICIENT
  RADA M1  viivitus   3 s        DATA INSUFFICIENT
  RADA M1  viivitus   5 s        DATA INSUFFICIENT
  RADA M1  viivitus  10 s        DATA INSUFFICIENT
  RADA M1  viivitus  15 s        DATA INSUFFICIENT
  RADA M1  viivitus  30 s        DATA INSUFFICIENT
  RADA M1  viivitus  60 s   10   +1.53   2.22   -0.69   30.0   1.22   0.221

  Ainus mooedetav viivituse-samm (0 s -> 60 s, st T+60 s -> T+120 s)
  kaotab +0.50 bp. Kiirem kadu, kui see on, jaab nahtamatuks.


===============================================================================
8. HOLD RESULTS
===============================================================================

  test                       n   bruto   kulu    neto    wr%      t       p
  ---------------------    ---   -----   ----   -----   ----   ----   -----
  RADA M1  hoid   5 s            DATA INSUFFICIENT
  RADA M1  hoid  10 s            DATA INSUFFICIENT
  RADA M1  hoid  15 s            DATA INSUFFICIENT
  RADA M1  hoid  30 s            DATA INSUFFICIENT
  RADA M1  hoid  60 s       10   +2.03   2.22   -0.19   50.0   1.84   0.066  PRIMARY
  RADA M1  hoid 120 s       10   +3.34   2.22   +1.12   40.0   1.94   0.052
  RADA M1  hoid 300 s       10   +3.94   2.22   +1.72   70.0   2.09   0.036
  RADA M1  hoid 600 s       10   +3.61   2.22   +1.39   50.0   1.70   0.089

  Hoid 300 s annab neto +1.72 bp (p = 0.036). SEE EI OLE PRIMARY ja
  seda EI NIMETATA leiuks: n = 10, uks lahter kaheksast hoiust, ja
  RADA M5 samal perioodil annab 300 s hoiuga -1.58 bp (p = 0.994).


===============================================================================
9. BID/ASK JA SPREAD
===============================================================================

  BID/ASK EI OLE SAADAVAL. Seetottu EI SAA raporteerida:
    normal spread, release-time spread, mediaan, p75, p90, p95,
    max spread, spread widening around release.
  KOIK need on DATA INSUFFICIENT. Neid EI HINNATUD ega MODELLEERITUD.

  MIDA SAAB OELDA:
    eeldatud tavaline round-trip kulu 2.0-3.6 bp (paaripohine)
    RADA M1 murdepunkt (max talutav kulu) +2.03 bp
    => juba tavaline spread on murdepunkti PIIRIL voi ULAL
    uudise ajal spread LAIENEB; kui palju, seda me EI TEA

  SIMULEERITUD LIBISEMINE (rakendub UKS KORD sisenemisel):
    lib    M1 neto    M5 neto   M15 neto
    ----   -------    -------   --------
     0 bp    -0.19      -3.77      -2.39
     1 bp    -1.19      -4.77      -3.39
     2 bp    -2.19      -5.77      -4.39
     3 bp    -3.19      -6.77      -5.39
     5 bp    -5.19      -8.77      -7.39
    10 bp   -10.19     -13.77     -12.39

  Ukski stsenaarium ei ole positiivne uhelgi rajal.


===============================================================================
10. EVENT-TIME SIGNED MOVEMENT  (RADA M1, n = 10)
===============================================================================

  Ankur = viimane sulgemine ENNE valjalaset. Margiga (signaali suunas).

  kumulatiiv         n   keskm_bp   med_bp    wr%      t       p
  --------------   ---   --------   ------   ----   ----   -----
  0 -> +60 s        10     +10.45    +5.45   70.0   2.31   0.021  SISALDAB
                                                                  HUPET
  0 -> +120 s       10     +12.48    +6.60   50.0   2.27   0.023
  0 -> +300 s       10     +14.52    +9.05   70.0   2.56   0.010
  0 -> +600 s       10     +12.50    +7.40   80.0   2.32   0.020
  0 -> +1800 s      10     +12.60    +7.52   80.0   2.30   0.021
  0 -> +3600 s      10     +12.46    +8.14   70.0   3.08   0.002

  Hupe on OLEMAS ja suunatud: +10.45 bp juba esimese 60 sekundiga,
  ja 3600 sekundi parast on kumulatiiv +12.46 bp — st peaaegu kogu
  tunniajane suunatud liikumine on esimese minuti sees.


===============================================================================
11. INCREMENTAL MOVEMENT  (RADA M1, n = 10)
===============================================================================

  inkrement             n   keskm_bp   med_bp    wr%      t       p
  -----------------   ---   --------   ------   ----   ----   -----
  0 s -> 60 s          10     +10.45    +5.45   70.0   2.31   0.021  EI OLE
                                                                     KAUBELDAV
  60 s -> 120 s        10      +2.03    +1.16   50.0   1.84   0.066
  120 s -> 300 s       10      +2.04    +2.24   60.0   1.40   0.163
  300 s -> 600 s       10      -2.03    -1.17   10.0  -3.14   0.002
  600 s -> 1800 s      10      +0.11    +0.58   50.0   0.09   0.931
  1800 s -> 3600 s     10      -0.14    +2.90   70.0  -0.05   0.959

  84% kogu tunniajasest suunatud liikumisest (10.45 / 12.46) toimub
  ESIMESE 60 SEKUNDI JOOKSUL, enne kui esimene taidetav hind saabub.

  ALLA 60 SEKUNDI: loigu 0 -> 60 s SISEMUST EI SAA AVADA. See on
  tapselt see osa, kus kogu efekt asub, ja tapselt see osa, mida
  praeguste andmetega EI SAA MOOTA.


===============================================================================
12. RANDOM BASELINE  (paaritatud, 2000 katset)
===============================================================================

  Samad sundmused, sama sisenemine ja valjumine, AINULT suund juhuslik.
  Jarjekorra permutatsiooni EI KASUTATUD (varasem audit naitas, et see
  on fikseeritud protsendiriski juures sisutu).

  rada       n   signaal   juh.med   juh.95%   pertsentiil       p
  -------   ---   -------   -------   -------   -----------   ------
  M1         10     +2.03     -0.07     +1.80        96.8%    0.037
  M5         15     -1.58     +0.04     +1.26         0.6%    0.994
  M15        39     -0.16     -0.02     +1.70        44.9%    0.551

  bootstrap 95% CI:
    M1   [+0.17, +4.37]     M5   [-2.78, -0.39]     M15  [-2.29, +1.88]

  SEE ON RAPORTI OTSUSTAV TABEL. M1 on 96.8. pertsentiilil, M5 on
  0.6. pertsentiilil. Perioodid KATTUVAD. Sama signaal, sama kaart,
  sama kulu — ainult baarisamm erineb, ja tulemus poordub umber.
  n = 10 vs n = 15. See on mura.


===============================================================================
13. OUT-OF-SAMPLE
===============================================================================

  RADA M1 katab 28 paeva (2026-08-19 .. 2026-09-16).
  TRAIN through 2024 / VALID 2025 / FINAL OOS 2026 jaotus EI OLE
  voimalik — kogu valim on uhe kuu sees.

  AUS SONA: sample too short for meaningful OOS.
  See EI OLE FAIL. See on DATA INSUFFICIENT.

  Kunstlikku jaotust EI SURUTUD.


===============================================================================
14. CURRENCY BREAKDOWN  (RADA M1, midagi EI EEMALDATUD)
===============================================================================

  valuuta (paar)      n   bruto    neto    wr%      t       p
  --------------    ---   -----   -----   ----   ----   -----
  USD (EURUSD)        1   (alla 5 sundmuse)
  EUR (EURUSD)        5   -0.46   -2.46    0.0  -1.63   0.102
  GBP (GBPUSD)        0   (alla 5 sundmuse)
  JPY (USDJPY)        0   (alla 5 sundmuse)
  CHF (USDCHF)        2   (alla 5 sundmuse)
  CAD (USDCAD)        1   (alla 5 sundmuse)
  AUD (AUDUSD)        1   (alla 5 sundmuse)
  NZD (NZDUSD)        0   (alla 5 sundmuse)

  10 sundmust kaheksa valuuta peale. Valuutapohine analuus on
  SISUTU sellel valimil. Naidatud on kogu universum, midagi ei ole
  eemaldatud — aga midagi EI SAA sellest ka jareldada.


===============================================================================
15. INDICATOR BREAKDOWN  (RADA M1 + M5 koos, n = 25)
===============================================================================

  Uksikindikaatorid: KOIK alla 5 sundmuse (0-4 tk). EI RAPORTEERITA
  eraldi, sest see oleks mura esitamine tulemusena.

  EELMAARATUD GRUPID (B1 klassifikatsioon, uusi EI LOODUD):
  grupp                 n   bruto    neto    wr%      t       p
  ----------------    ---   -----   -----   ----   ----   -----
  CPI / inflatsioon     8   -0.10   -2.50   50.0  -0.08   0.938
  toohoive / NFP        6   +1.31   -0.99   50.0   0.65   0.513
  tootus                3   (alla 5)
  SKP                   2   (alla 5)
  intressiotsus         0   (alla 5)
  jaemuuk               6   -1.55   -3.55   16.7  -1.67   0.096
  PMI                       ei kuulu B1 TIER 1 hulka; uut kategooriat
                            EI LOODUD


===============================================================================
16. SURPRISE MAGNITUDE  (RADA M1 + M5 koos)
===============================================================================

  vahemik                n   bruto    neto    wr%      t       p
  ------------------   ---   -----   -----   ----   ----   -----
  1.0 <= |z| < 1.5      13   +0.40   -1.80   30.8   0.43   0.670
  1.5 <= |z| < 2.0       4   (alla 5 sundmuse)
  |z| >= 2.0             8   -1.36   -3.66   37.5  -0.99   0.320

  Suurem ullatus EI anna paremat tulemust. Monotoonsust ei ole.
  RADA M1 uksi: |z|>=1 +2.03, |z|>=1.5 +1.61 (n=5), |z|>=2 alla 5.


===============================================================================
17. COST / SLIPPAGE SENSITIVITY
===============================================================================

  Vt sektsioon 9. Kokkuvottes:

  rada    bruto    murdepunkt   eeldatud kulu   varu
  ----    -----    ----------   -------------   -----
  M1      +2.03         2.03           2.22     -0.19
  M5      -1.58         0.00           2.19     -3.77
  M15     -0.16         0.00           2.22     -2.39

  Murdepunkt = maksimaalne round-trip kulu, mille juures ootus on 0.
  Isegi parimal rajal on murdepunkt ALLPOOL eeldatavat tavalist kulu,
  ja uudise libisemine tuleks sellele LISAKS.


===============================================================================
18. 205 EUR / 0.01 LOT TEOSTATAVUS
===============================================================================

  paar        60 s sigma%   0.01 lot EUR   1-sigma EUR   % kontost
  -------     -----------   ------------   -----------   ---------
  EURUSD            0.013           1000          0.13        0.06
  USDCHF            0.000            867          0.00        0.00
  (ulejaanud paaridel alla 2 tehingu — ei raporteerita)

  0.01 lot EURUSD, tehingu kohta:
    oodatav BRUTO              +0.203 EUR
    tavaline kulu               0.222 EUR
    oodatav NETO               -0.019 EUR
    uudise libisemine +5 bp     0.500 EUR  (LISAKS)

  risk 0.25% = 0.51 EUR -> taidetav 2/2 paaril
  risk 0.50% = 1.02 EUR -> taidetav 2/2 paaril

  VERDIKT: riskieelarve motes on 0.01 lot TAIDETAV — 60-sekundilise
  hoiu sigma on nii vaike (0.013%), et positsioon on 0.06% kontost.

  AGA: oodatav neto on -0.019 EUR tehingu kohta ja uks 5 bp libisemine
  maksab 0.50 EUR — 25 korda rohkem kui kogu oodatav bruto. Teostatavus
  EI OLE siin probleem. Probleem on see, et puudub see, mida taita.


===============================================================================
19. MULTIPLE TESTING
===============================================================================

  PRIMARY on UKS eelregistreeritud test: RADA M1, D0, hoid 60 s,
  TIER 1, |z| >= 1.

  Arvutatud lahtreid kokku ~55 (3 rada x 2 viivitust x 6 hoidu x
  3 lavet x 8 valuutat x 11 indikaatorit x 3 magnituudi, millest
  enamik jai alla raporteerimislavi).

  Nominaalselt olulisi ja POSITIIVSEID: 3
    M1 hoid 300 s p = 0.036;  M1 juhuslik baas p = 0.037;
    M1 hoid 120 s p = 0.052 (piiri peal)
  Nominaalselt olulisi ja NEGATIIVSEID: 3
    M5 D0 p = 0.011;  M5 |z|>=2 p = 0.018;  M1 300->600 s p = 0.002

  3 positiivset ~55 lahtrist on tapselt see, mida juhus annab.
  Lisaks annavad M1 ja M5 KATTUVAL perioodil vastupidise margi.
  BH/FDR korrektsiooni EI OLE motet rakendada valimile n = 10 —
  see annaks vale turvatunde. Ma EI NIMETA uhtegi lahtrit leiuks.


===============================================================================
20. ANDMEPIIRANGUD
===============================================================================

  1 SEKUNDI-TASAND PUUDUB TAIELIKULT. 1/3/5/10/15/30 s horisonte
    ei saa moota. Vaikseim baar on 60 s.
  2 BID/ASK PUUDUB. Uudise-aegset spreadi EI SAA moota. Koik
    libisemisnumbrid on SIMULATSIOON.
  3 M1 ULATUB 28 PAEVA. Yahoo piir, mooedetud. n = 10 TIER 1
    sundmust.
  4 OOS EI OLE VOIMALIK. Kogu valim on uhe kuu sees.
  5 VALUUTA- JA INDIKAATORIPOHINE ANALUUS ON SISUTU sellel valimil.
  6 REVISJON. Ei saa kinnitada, et 'actual' on esialgne trukk.
    B1 piirang, jaab lahendamata.
  7 M1 "D0" ON TAPSELT T+60 s, mitte "0-60 s vahel". Me mootsime
    akna LOPP-PUNKTI.


===============================================================================
21. MIDA SEE TEST TOESTAB
===============================================================================

  1 Hupe on PARIS ja SUUNATUD. 0 -> 60 s annab +10.45 bp signaali
    suunas (t = 2.31, p = 0.021), ja valjalaske M1-baar on 15.9x
    volatiilsem kui tavaline baar.
  2 84% kogu tunniajasest suunatud liikumisest (10.45 / 12.46) toimub
    esimese 60 sekundi jooksul.
  3 T+60 s sisenemisel on bruto +2.03 bp, mis on ALLPOOL eeldatavat
    tavalist round-trip kulu 2.22 bp.
  4 Lookahead-loks on universaalne ja kinnitatud: 6/6 EURUSD-sundmusel
    sulgeb baar tapselt valjalaske hetkel. Lubav vordlus annaks
    voltsitud serva.
  5 Luhike hoid teeb 0.01 loti riskieelarve motes taidetavaks.


===============================================================================
22. MIDA SEE TEST EI TOESTA
===============================================================================

  1 EI TOESTA, et 0-60 sekundi aknas serva EI OLE. Seda akent ei
    mootedetud.
  2 EI TOESTA, et T+60 s sisenemine on kasumlik. n = 10, neto -0.19 bp,
    ja M5 annab kattuval perioodil vastupidise margi.
  3 EI TOESTA uhtegi valuuta-, indikaatori- ega magnituudipohist
    vaidet. Valim on selleks liiga vaike.
  4 EI TOESTA, et uudise spread on talutav. Spreadi ei mootedetud.
  5 EI TOESTA midagi OOS-i kohta.


===============================================================================
23. LOPPKLASSIFIKATSIOON
===============================================================================

              DATA INSUFFICIENT

  Pohjendus: kusimus oli 0-60 sekundi kohta. Selle akna sisemust ei
  saa praeguste kattesaadavate andmetega moota, ja neid andmeid EI
  FABRITSEERITUD.

  Mooedetava piiripunkti (T+60 s) kohta eraldi:

              WEAK  (kaldub negatiivsele)

  bruto +2.03 bp vs kulu 2.22 bp => neto -0.19 bp; n = 10;
  juhusliku suuna pertsentiil 96.8% M1-l, AGA 0.6% M5-l kattuval
  perioodil. Vastuolu kahe raja vahel tahendab mura, mitte serva.

  Ma EI NIMETA seda FAIL-iks, sest FAIL eeldaks, et mootmine oli
  voimalik ja andis negatiivse vastuse. Siin mootmine ei olnud
  voimalik selles aknas, kus efekt asub.


===============================================================================
24. KAS NEMSIS PEAKS SEDA MEHHANISMI EDASI AJAMA?
===============================================================================

  AINULT SIIS, kui saab paris tick-andmed bid/ask'iga. Ilma selleta
  on iga edasine jooks sama seina vastu.

  MIDA TAPSELT VAJA: ajalooline FX tick bid/ask, vahemalt 12 kuud,
  vahemalt 7 majori kohta. Dukascopy annaks selle tasuta, aga tema
  .bi5 binaar ei tule labi praegusest andmeteest (Supabase http
  tagastab teksti). See on TEHNILINE, mitte rahaline takistus —
  vaja oleks kohta, kus saab binaarfaili alla laadida ja lahti
  pakkida.

  ILMA SELLETA: mehhanism jaab TOESTAMATA, mitte umberlukatuks.

  MIDA MITTE TEHA:
    - mitte ehitada strateegiat hoiu 300 s peale (p = 0.036, n = 10,
      ja M5 utleb vastupidist)
    - mitte otsida "paremat" hoidu voi lavet sellel valimil
    - mitte votta M1 96.8. pertsentiili kinnituseks


===============================================================================
25. LOODUD FAILID
===============================================================================

  KOKKUVOTE_ECONOMIC_CALENDAR_SUB60.md
  bot/cal_sub60.py          mootor + andmeallikate audit
  bot/cal_sub60_audit.py    eelaudit, 21 kontrolli, 0 FAIL
  bot/cal_sub60_run.py      tulemused
  bot/sb_min.py             Supabase -> minutibaaride CSV teisendaja
  SUB60_PRIMARY.csv         SUB60_DELAY.csv        SUB60_HOLD.csv
  SUB60_INCREMENTAL.csv     SUB60_SPREAD.csv       SUB60_RANDOM.csv
  SUB60_OOS.csv             SUB60_CURRENCY.csv     SUB60_INDICATOR.csv
  SUB60_MAGNITUDE.csv       SUB60_DATA_QUALITY.csv SUB60_EXECUTION.csv
  SUB60_COST.csv


===============================================================================
26. REPRODUTSEERITAVUS
===============================================================================

  run 1 exit code        0
  run 2 exit code        0
  byte-identical         YES  (13/13 CSV)
  audit checks           21
  audit FAIL count       0
