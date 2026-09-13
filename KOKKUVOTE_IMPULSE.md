===============================================================================
NO ROBUST EDGE FOUND
===============================================================================
NEMSIS — IMPULSI JATKUVUSE / POORDUMISE TEST
13. september 2026 | 205 EUR | MAteckh/nemsis-bot | RESEARCH ONLY
Live-faile EI MUUDETUD. Midagi ei deploy'itud.

===============================================================================
1. EXECUTIVE SUMMARY
===============================================================================

Testitud algne idee: skaneeri palju valuutapaare, tuvasta ebatavaliselt
tugev liikumine, sisene vaikse riskiga, puua luhike jatkuimpulss.

TULEMUS: efekt ON OLEMAS, aga on 3-5x liiga vaike, et kulusid katta.

  parim 108-st variandist:  BRUTO  +0.71 bp
  kulu (retail-CFD):              -3.36 bp
  NETO                            -2.65 bp
  murdepunkt                       0.71 bp round-trip = 0.36 bp/pool
  (parim paris ECN-spread on ~0.7-0.9 bp round-trip)

MIS SEE TEST TEGI TEISITI kui v4-v7.1: see on esimene tulemus, mis on
STRUKTUURSELT terve. 17/22 paari plussis, parim paar annab ainult 18.6%
kasumist (v7.1-s andis USDJPY 89%), walk-forward on jarjepidev koigis
kolmes aknas. Varasemad "servad" olid uhe paari voi uhe perioodi
artefaktid. See ei ole. See on lihtsalt liiga vaike.

Labitud PASS-kriteeriume: 4/10.

===============================================================================
2. TAPNE HUPOTEES
===============================================================================

H1 (jatkuvus): kui valuutapaar teeb ebatavaliselt tugeva liikumise, mis
  ei ole mura, siis liikumine JATKUB lyhiajaliselt samas suunas.

H2 (poordumine): sama impulss POORDUB.

MOLEMAD defineeriti ENNE tulemuste vaatamist ja moLEMAT testiti
sama raamistikuga.

===============================================================================
3. TAPSED REEGLID (eelregistreeritud, EI muudetud parast tulemusi)
===============================================================================

IMPULSI VARIANDID:
  A: kuunla ulatus >= 1.5 x ATR(14) JA sulgemine ulemises 25% (tous)
     voi alumises 25% (langus)
  B: sama, aga ulatus >= 2.0 x ATR(14)
  C: kaks jarjestikust kuunalt samas suunas, koguliikumine >= 1.5 x ATR,
     viimane kuunal sulgeb liikumise suunas

KINNITUSED:
  JATK:   impulss murrab viimase 6 baari tipu/pohja, entry baaril i+1
  TAGASI: jargmine LOPETATUD kuunal ei poora impulssi taielikult,
          entry baaril i+2

HOIDMISAJAD: 1, 2, 4 baari
ATR-STOPID:  puudub, 0.75 x ATR, 1.0 x ATR
SUUND:       jatkuvus (+1) voi poordumine (-1)

KOKKU: 3 x 2 x 3 x 3 x 2 = 108 varianti. Mitte uhtegi juurde, mitte
uhtegi ara. Uhtegi lavendit ei optimeeritud parast tulemuste nagemist.

===============================================================================
4. ANDMED
===============================================================================

  paare              22 FX (7 majorit + 15 ristpaari)
  ajaskaala          H1
  periood            2023-11-27 .. 2026-09-13
  baare kokku        380 000+ (mediaan 17 280 paari kohta)
  puuduvad andmed    nadalavahetused puuduvad (normaalne), laupaeva-baare 0
  bid/ask andmed     EI OLE
  tick-andmed        EI OLE
  order flow         EI OLE — ja EI LOODUD sunteetiliselt

PAARID:
  EURUSD GBPUSD USDJPY USDCHF USDCAD AUDUSD NZDUSD
  EURGBP EURJPY EURCHF EURAUD EURNZD GBPJPY GBPCHF GBPAUD GBPCAD
  AUDJPY AUDNZD AUDCAD NZDJPY CADJPY CHFJPY

KULUEELDUSED (uhesuunaline, bp):
  majorid      1.0-1.8 bp   (EURUSD 1.0, GBPUSD 1.2, USDJPY 1.0, ...)
  ristpaarid   2.2 bp
  round-trip   2.0-3.6 bp majoritel, 4.4 bp ristpaaridel
  komisjon     sisaldub ulaltoodus (retail-CFD mudel)
  slippage     modelleeritud kulu-sweepi kaudu (0-3 bp)

Ei eeldatud soodsat kulu ilma toenditeta.

===============================================================================
5. LOOKAHEAD-AUDIT (kohustuslik, tehtud ENNE testi)
===============================================================================

7 sunteetilist testi, iga konstrueeritud nii, et KUKUKS LABI kui viga sees:

  [OK] T1 ATR ei sisalda jooksva baari ulatust
       korrelatsioon ATR vs jooksev ulatus = +0.014
  [OK] T2 6-baari tipp on baarid i-6..i-1
       jooksev high uletab 6-baari tippu 2974 korda (peab olema > 0)
  [OK] T3 juhuslikul jalutuskaigul BRUTO ~ 0
       moodetud -0.27 bp, SE 0.27
  [OK] T4 tuleviku info annab suure plussi (test TOIMIB)
       +11.1 bp vs juhuslik -0.27 bp
  [OK] T5 entry=open[i+1], exit=close[i+1+hoia]
       saadud -0.00100230, oodatav -0.00100230 (tapsus 1e-12)
  [OK] T6 poordumine = -1 x jatkuvus (ilma stopita)
       -0.00026644 + +0.00026644 = 0
  [OK] T7 TAGASI-kinnitus nihutab entry i+2-le
       JATK nihe=0, TAGASI nihe=1

  AUDIT: 7 OK, 0 VIGA. Lookahead'i ei tuvastatud.

KONKREETSED KAITSED KOODIS:
  1. ATR(14) on .shift(1) — ei sisalda jooksva baari ulatust. Vastasel
     juhul oleks kunnis osaliselt iseennast maaratlev.
  2. 6-baari tipp on .rolling(6).max().shift(1) — baarid i-6..i-1.
  3. Sisenemine ALATI baari i+1 (voi i+2) AVANEMISHIND.
  4. Valjumine baari i+1+k SULGEMISHIND voi stopi tase teel.
  5. Jarjestus portfelli jaoks kasutab ainult impulsi tugevust
     (ulatus/ATR), mis on teada baari i sulgemisel.
  6. Mitte uhtegi normaliseerimist tuleviku andmete peal.

===============================================================================
6. TULEMUSTE TABEL — TIPP 18 varianti 108-st (BRUTO jargi)
===============================================================================

  var kinnitus hoia  stopp suund tehinguid  BRUTO bp  NETO bp       t  voit%
  --- -------- ---- ------ ----- --------- --------- -------- ------- ------
   B   TAGASI    4      -   JATK     10770     +0.71    -2.65   +2.88  41.6%
   B     JATK    4      -   JATK      8214     +0.58    -2.76   +2.02  42.7%
   A     JATK    1      -   POOR     18606     +0.38    -3.01   +3.00  41.5%
   B     JATK    2      -   JATK      8214     +0.35    -3.00   +1.44  40.1%
   B   TAGASI    2      -   JATK     10770     +0.33    -3.03   +1.71  40.1%
   C     JATK    1      -   POOR     21407     +0.28    -3.06   +2.33  40.8%
   B   TAGASI    1      -   JATK     10770     +0.26    -3.10   +1.57  37.6%
   C     JATK    2      -   POOR     21407     +0.26    -3.09   +1.85  42.6%
   C   TAGASI    4      -   POOR     23049     +0.21    -3.14   +1.24  43.4%
   A     JATK    2      -   POOR     18606     +0.20    -3.19   +1.35  42.8%
   A   TAGASI    4      -   JATK     28315     +0.17    -3.23   +1.14  40.9%
   C   TAGASI    1      -   POOR     23049     +0.13    -3.22   +1.15  38.8%
   C     JATK    4      -   POOR     21407     +0.13    -3.22   +0.71  44.3%
   C   TAGASI    4    1.0   POOR     23049     +0.11    -3.23   +0.86  35.9%
   B     JATK    1      -   POOR      8214     +0.11    -3.24   +0.52  42.4%
   A     JATK    4      -   JATK     18606     +0.07    -3.32   +0.40  41.6%
   A   TAGASI    2      -   JATK     28315     +0.07    -3.33   +0.61  38.9%
   C   TAGASI    1    1.0   POOR     23049     +0.05    -3.30   +0.53  36.5%

  MITTE UHESKI variandis 108-st ei ole NETO positiivne.
  TAHELEPANEK: koik tipus olevad variandid on ILMA STOPITA. ATR-stopp
  teeb tulemuse igal juhul halvemaks — see on jarjepidev muster.

===============================================================================
7. KULUTUNDLIKKUS (parim variant)
===============================================================================

  round-trip kulu   NETO bp   aastas %   hinnang
  ---------------   -------   --------   -------
         0.0 bp      +0.71     +27.55%   PLUSS
         0.5 bp      +0.21      +8.25%   PLUSS
         1.0 bp      -0.29     -11.05%   miinus
         1.5 bp      -0.79     -30.35%   miinus
         2.0 bp      -1.29     -49.65%   miinus
         2.5 bp      -1.79     -68.95%   miinus
         3.0 bp      -2.29     -88.25%   miinus

  MURDEPUNKT: 0.71 bp round-trip = 0.36 bp poole kohta

  Vordluseks paris hinnakirjad (EURUSD, round-trip):
    BlackBull ECN Prime (raw + $6/lot)   ~0.7-0.9 bp  <- JUBA ULE
    BlackBull Standard                   ~1.6-2.4 bp  <- 2-3x ule
    selles testis eeldatud (majorid)      2.0-3.6 bp
    selles testis eeldatud (ristpaarid)   4.4 bp

  Ainult majoritega on BRUTO +1.00 bp => murdepunkt 0.50 bp/pool.
  Ka see jaab alla parima ECN-spreadi.

  3860 tehingut aastas tahendab, et kulu kordub 3860 korda. Sellepolikult
  on "aastas %" veerg nii dramaatiline.

===============================================================================
8. JATKUVUS vs POORDUMINE (kasutaja punkt 7)
===============================================================================

     suund  variante  keskm BRUTO  parim BRUTO  plussis  keskm NETO
  --------  --------  -----------  -----------  -------  ----------
      JATK        54        -0.16        +0.71     9/54       -3.52
      POOR        54        -0.13        +0.38    14/54       -3.50

  Impulsi variandi kaupa:
   variant  JATK bruto  POOR bruto  kumb tugevam
   -------  ----------  ----------  ------------
         A       -0.24       -0.06  POORDUMINE
         B       +0.02       -0.36  JATKUVUS
         C       -0.25       +0.03  POORDUMINE

  JARELDUS: JARJEPIDEVAT suunaefekti EI OLE. Variant B eelistab
  jatkuvust, A ja C poordumist. Kui efekt oleks paris, peaks ta olema
  sama suunaga koigil kolmel impulsi definitsioonil. Ta ei ole.

  See on tugev argument selle poolt, et +0.71 bp on osaliselt mura.

===============================================================================
9. PAARIPOHINE (parim variant)
===============================================================================

      paar  tehinguid  BRUTO bp  NETO bp  osa summast
  --------  ---------  --------  -------  -----------
    USDJPY        539     +2.63    +0.63        18.6%
    USDCHF        589     +1.79    -0.81        13.8%
    CHFJPY        481     +2.12    -2.28        13.3%
    GBPCAD        660     +1.52    -2.88        13.2%
    EURUSD        724     +0.93    -1.07         8.9%
    AUDNZD        477     +1.42    -2.98         8.9%
    CADJPY        469     +1.35    -3.05         8.3%
    EURJPY        529     +1.02    -1.98         7.1%
    GBPUSD        766     +0.67    -1.73         6.7%
    GBPCHF        338     +1.27    -3.13         5.6%
    NZDUSD        595     +0.69    -2.91         5.4%
    EURCHF        228     +1.09    -2.51         3.2%
    GBPJPY        521     +0.42    -3.18         2.9%
    NZDJPY        436     +0.47    -3.93         2.7%
    AUDJPY        469     +0.28    -3.32         1.7%
    AUDUSD        579     +0.07    -2.33         0.6%
    USDCAD        366     +0.09    -2.51         0.4%
    AUDCAD        160     -0.10    -4.50        -0.2%
    EURGBP        659     -0.42    -3.42        -3.6%
    EURNZD        372     -0.98    -5.38        -4.8%
    GBPAUD        450     -0.93    -4.53        -5.5%
    EURAUD        363     -1.50    -5.10        -7.1%

  plussis 17/22 paari,  mediaan +0.68 bp
  TOP-1 osa 18.6%,  TOP-2 kokku 32.4%
  ILMA parima paarita:  +0.71 -> +0.61 bp  (peaaegu ei muutu)
  ILMA kahe parimata:   +0.53 bp
  AINULT majorid:       +1.00 bp (4158 tehingut)

  SEE ON SELLE TESTI TUGEVAIM KULG. Vordluseks v7.1, kus USDJPY andis
  89% ja ilma temata kukkus serv +1.46 -> +0.19 bp. Siin ei ole efekt
  uhe paari kull.

  AINUS paar, mis on NETO plussis: USDJPY (+0.63 bp). Uks 22-st.

===============================================================================
10. PORTFELL (kasutaja punkt 9)
===============================================================================

  Piirangud: max 1 positsioon paari kohta, max 3 samaaegset,
  valuuta-exposure piiratud (ei kogune mitut sama valuuta panust).

  signaale kokku 10770  ->  portfelli piirangute jarel 6578 (61.1%)

                       variant  tehinguid  BRUTO bp  NETO bp
  ----------------------------  ---------  --------  -------
                koik signaalid      10770     +0.71    -2.65
    portfell (max 3, exposure)       6578     +0.75    -2.57
          TOP-1 tugevuse jargi       3535     +0.35    -2.93
          TOP-2 tugevuse jargi       5663     +0.67    -2.62
          TOP-3 tugevuse jargi       7150     +0.73    -2.57

  Portfelli piirangud ei paranda ega halvenda oluliselt. TOP-1 valimine
  teeb HALVEMAKS (+0.35 vs +0.71) — ehk tugevaim impulss ei ole parim
  impulss. See on omaette tahelepanek: selektiivsus tugevuse jargi EI
  TOOTA ka siin.

===============================================================================
11. 205 EUR / 0.01 LOT TAITMINE (kasutaja punkt 10)
===============================================================================

  SL = 1.0 x ATR, 0.01 lot = 1000 uhikut baasvaluutat
  keskmine SL 0.01 lotiga: 1.51 EUR = 0.7% 205 EUR kontost
  maksimaalne SL 0.01 lotiga: 1.2% kontost

   kapital   risk%   lubatud        taidetavaid signaale   paare
   -------   -----   -------   -------------------------   -----
    205 EUR  0.25%     0.51E        0/10770   (  0.0%)      0/22
    205 EUR  0.50%     1.02E     1833/10770   ( 17.0%)      3/22
    500 EUR  0.25%     1.25E     3374/10770   ( 31.3%)      6/22
    500 EUR  0.50%     2.50E    10398/10770   ( 96.5%)     21/22
   1000 EUR  0.25%     2.50E    10398/10770   ( 96.5%)     21/22
   1000 EUR  0.50%     5.00E    10770/10770   (100.0%)     22/22

  205 EUR @ 0.25% target: 0% signaalidest taidetav.
  205 EUR @ 0.50% hard max: 17% taidetav, ainult 3 paari 22-st.

  Voimendust EI suurendatud ja riskipiiri EI rikutud.

===============================================================================
12. WALK-FORWARD (kasutaja punkt 11)
===============================================================================

          aken                 periood  tehinguid  BRUTO bp       t
  ------------  ----------------------  ---------  --------  ------
         TRAIN  2023-11-27..2024-10-03       3590     +0.37   +0.88
    VALIDATION  2024-10-03..2025-09-04       3590     +0.95   +2.04
     FINAL OOS  2025-09-04..2026-09-11       3590     +0.80   +2.10

  KOIK KOLM AKENT ON POSITIIVSED. FINAL OOS t = +2.10, p = 0.018.
  See on selle testi teine tugev kulg — ja ainus kord kogu projektis,
  kus TRAIN, VALID ja OOS on koik samas suunas.

  Kalendriaastate kaupa:
    aasta  tehinguid  BRUTO bp
    -----  ---------  --------
     2023        488     +1.54
     2024       4042     -0.09
     2025       3853     +1.02
     2026       2387     +1.38

  2024 on praktiliselt null. Kolm aastat neljast on plussis.

===============================================================================
13. ROBUSTSUSTESTID (kasutaja punkt 12)
===============================================================================

  A) koik paarid                    +0.71 bp
  B) ainult majorid                 +1.00 bp  (parem!)
  C) ilma parima paarita            +0.61 bp
  D) ilma kahe parimata             +0.53 bp
  E) aastate kaupa                  3/4 plussis (2024 ~null)
  F) walk-forward aknad             3/3 plussis
  G) kulutundlikkus                 murdepunkt 0.71 bp round-trip

  plussis paare       17/22
  mediaan paar        +0.68 bp
  TOP-1 osa           18.6%
  TOP-2 osa           32.4%

  ROBUSTSUSE MOTES ON SEE KANDIDAAT PARIM, MIS PROJEKTIS LEITUD.
  Ta lihtsalt ei ole piisavalt suur.

===============================================================================
14. STATISTILINE OLULISUS
===============================================================================

  signaale (parim variant)     10770
  tehinguid                    10770 (iga signaal = 1 tehing)
  voiduprotsent                41.6%
  BRUTO ootus                  +0.71 bp
  NETO ootus                   -2.65 bp
  t-statistik (kogu)           +2.88
  p-vaartus (uhepoolne)        0.0020
  FINAL OOS t                  +2.10
  FINAL OOS p                  0.0180

===============================================================================
15. MULTIPLE TESTING — AUS ARUTELU
===============================================================================

  variante testitud            108
  parima p                     0.0020
  Bonferroni lavend            p < 0.00046
  => EI LABI

  variante t > +2              4/108   (juhuslikult oodatav ~2.5)
  variante t < -2             30/108
  keskmine t kogu jaotusest   -1.12

  SEE VIIMANE NUMBER ON OLULINE. Kui impulsi efekt oleks uldine ja
  paris, peaks variantide t-jaotus olema nihutatud PLUSSI poole. Ta on
  nihutatud MIINUSESSE (keskmine -1.12), ja negatiivseid olulisi
  tulemusi on 30, positiivseid 4.

  4 positiivset 108-st, kui juhuslikult oodatav on 2.5, ei ole toend.

  LISAKS: enne seda testi on tehtud ~11 500 v4-v6 testi + v7/v7.1.
  Kui arvestada kogu uurimisajalugu, on lavend veel rangem.

  KOKKUVOTE: +0.71 bp parim tulemus 108-st EI OLE statistiliselt
  kaitstav. Ma EI nimeta seda oluliseks.

===============================================================================
16. PASS / FAIL (kasutaja punkt 14)
===============================================================================

  [EI ]  1. positiivne NETO ootus realistlike kuludega   -2.65 bp
  [OK ]  2. positiivne FINAL OOS                         +0.80 bp
  [EI ]  3. FINAL OOS ei soltu uhest paarist             ei kontrollitud
                                                         eraldi OOS-aknas
  [OK ]  4. parima paari eemaldamine ei havita serva     +0.71 -> +0.61
  [EI ]  5. serv talub realistlikke kulusid              0.71 < 2.0 bp
  [OK ]  6. piisavalt tehinguid                          10 770
  [EI ]  7. ei noia >0.50% riski tehingu kohta           keskm 0.7%, max 1.2%
  [EI ]  8. oluline osa signaale taidetav 205 EUR kontol 0% @ 0.25%
  [OK ]  9. tulemus ei piirdu uhe luhikese perioodiga    3/3 akent plussis
  [EI ] 10. labib multiple-testing korrektsiooni         p=0.0020 vs 0.00046

  LABITUD: 4 / 10

===============================================================================
17. LOPLIK OTSUS
===============================================================================

  NO ROBUST EDGE FOUND

  MIKS — kolm sooltumatut pohjust:

  1. SUURUS. Bruto +0.71 bp (majoritel +1.00). Murdepunkt 0.36 bp
     poole kohta. Parim paris ECN-spread on 0.35-0.45 bp poole kohta.
     Ehk parimal voimalikul kontol oleks tulemus umbes NULL — ja see
     eeldaks, et koik muu on taiuslik.

  2. SUUNAEFEKT EI OLE JARJEPIDEV. Variant B eelistab jatkuvust, A ja C
     poordumist. Paris efekt oleks sama suunaga koigil kolmel impulsi
     definitsioonil.

  3. MULTIPLE TESTING. 4 positiivset varianti 108-st (oodatav 2.5),
     30 negatiivset, keskmine t = -1.12. Jaotus on nihutatud miinusesse.
     Parim p = 0.0020 ei labi Bonferroni lavendit 0.00046.

  MIS OLI SELLES TESTIS TEISITI — ja miks see loeb:
  See on ainus kandidaat kogu projektis, mis labib STRUKTUURSED testid:
  17/22 paari plussis, parim paar ainult 18.6%, koik kolm walk-forward
  akent samas suunas. Varasemad "servad" (v6 carry 82% JPY, v7.1
  selektiivsus 89% USDJPY) olid uhe panuse artefaktid. See ei ole.

  Jareldus ei ole "impulsi jatkuvust ei eksisteeri". Jareldus on
  "impulsi jatkuvus on olemas, aga ta on ~0.7-1.0 bp ja retail-kulu
  on 2.0-3.6 bp, seega teda ei saa kaubelda".

  205 EUR kontol on kusimus nagunii akadeemiline: 0% signaalidest on
  taidetav 0.25% riskiga.

===============================================================================
18. STOP
===============================================================================

  Kasutaja juhis: "If no robust edge is found: STOP. Do not create
  another optimization round."

  Ma lopetan. Uut optimeerimisvooru ei tule.

  Live-faile main_v4.py, config.py, mt5_connector.py EI MUUDETUD.
  Midagi ei deploy'itud. Juur ja bot/ on sunkroonis. Koik kompileerub.
  Bot ootab /update-i — ARA saada.

  UUS KOOD (research only):
    bot/impulss_engine.py   impulsi definitsioonid, kinnitused, simulatsioon
    bot/impulss_audit.py    7 lookahead-testi
    bot/impulss_run.py      koik 108 eelregistreeritud varianti
    bot/impulss_lopp.py     kulutundlikkus, paarid, portfell, 205 EUR, WF
