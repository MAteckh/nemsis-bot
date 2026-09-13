NEMSIS v7.1 — LOW-COST EXECUTION STRESS TEST
13. september 2026 | 205 EUR | MAteckh/nemsis-bot | RESEARCH ONLY

===============================================================================
OTSUS:  D = V7 SELECTIVITY EDGE WAS SAMPLE/SELECTION ARTIFACT
===============================================================================

Kusimus oli: kas v7 selektiivne +1.83bp bruto serv on piisavalt tugev, et
madalate kuludega muutuda pariselt positiivseks?

Vastus: kusimus on vale, sest serva ennast ei ole. See oli uks makropanus.

===============================================================================
1. TEST: SAMA SIGNAAL, AINULT MAJORID
===============================================================================

Signaal MUUTMATA v7-st:
  murre  : c > 24h max(shift 1)  voi  c < 24h min(shift 1)
  filter : trendi joondus (sign(sg) == sign(EMA50-EMA200))
           JA suhteline tugevus kooskolas
           JA ATR laienemine > 1.2
  entry  : baar i+1 avanemine
  exit   : baar i+8 sulgemine
Ainus muutus: universum = 7 majorit, ristpaarid valjas.

  signaale         1289  (v7-s 3284, 22 paari peale)
  periood          2024-01-02 .. 2026-09-10
  tehinguid aastas ~480
  BRUTO            +1.46 bp   (v7-s 22 paariga +1.83 bp)
  t-statistik      +1.29      p(uhepoolne) = 0.098

===============================================================================
2. KULU-SWEEP (kogu kover, mitte parim punkt)
===============================================================================

  round-trip kulu   NETO bp   aastas %   hinnang
  ---------------   -------   --------   -------
        0.00 bp      +1.46      +6.99%   PLUSS
        0.25 bp      +1.21      +5.79%   PLUSS
        0.50 bp      +0.96      +4.59%   PLUSS
        0.75 bp      +0.71      +3.39%   PLUSS
        1.00 bp      +0.46      +2.19%   PLUSS
        1.25 bp      +0.21      +0.99%   PLUSS
        1.50 bp      -0.04      -0.21%   miinus
        1.75 bp      -0.29      -1.41%   miinus
        2.00 bp      -0.54      -2.61%   miinus
        2.25 bp      -0.79      -3.81%   miinus
        2.50 bp      -1.04      -5.01%   miinus
        2.75 bp      -1.29      -6.21%   miinus
        3.00 bp      -1.54      -7.41%   miinus
        3.25 bp      -1.79      -8.61%   miinus
        3.50 bp      -2.04      -9.81%   miinus

===============================================================================
3. MURDEPUNKT
===============================================================================

  BREAK-EVEN round-trip kulu = 1.46 bp  (= 0.73 bp poole kohta)

  Vordluseks paris hinnakirjad (round-trip, EURUSD):
    BlackBull ECN Prime (raw + $6/lot)   ~0.7-0.9 bp   <- MAHUB
    BlackBull Standard                   ~1.6-2.4 bp   <- ei mahu
    minu BASE-mudel v4-v7-s               2.0 bp
    minu HIGH-mudel                       4.0 bp

  Ehk: ECN-kontol oleks see TEOREETILISELT plussis (+0.46..+0.71 bp).
  See on ainus positiivne asi selles raportis. Aga vaata edasi.

===============================================================================
4. SESSIOONIFILTER (ainult 4 varianti)
===============================================================================

         sessioon   signaale   BRUTO bp   murdepunkt   teh/aastas
  ---------------   --------   --------   ----------   ----------
        kogu paev       1289      +1.46      1.46 bp          480
           London        681      -0.08     -0.08 bp          254
         New York        672      +1.71      1.71 bp          250
   LN/NY kattuvus        341      +3.49      3.49 bp          127

  NB: kattuvuse valimine (+3.49bp) oleks TAPSELT see optimeerimine,
  mille eest sa hoiatasid. Ma ei vali seda.

===============================================================================
5. PAARIPOHINE MURDEPUNKT (spread-filtri aus asendus)
===============================================================================

AUS PIIRANG: mul EI OLE tick- ega bid/ask-andmeid, seega ajas muutuvat
spread-filtrit ("kauple ainult kui spread <= 0.75bp") EI SAA teha. Ma ei
leiuta seda. Selle asemel: iga paari oma murdepunkt.

      paar   signaale   BRUTO bp   murdepunkt        t   teh/a
  --------   --------   --------   ----------   ------   -----
    EURUSD        214      +6.23      6.23 bp    +2.78      80
    GBPUSD        227      +0.98      0.98 bp    +0.54      85
    USDJPY        198      +8.44      8.44 bp    +2.15      74
    USDCHF        173      +6.98      6.98 bp    +1.97      64
    USDCAD        121      -2.64     -2.64 bp    -1.23      45
    AUDUSD        177      -5.95     -5.95 bp    -1.69      66
    NZDUSD        179      -6.62     -6.62 bp    -2.42      67

  4/7 plussis, 3/7 miinuses. NZDUSD on OLULISELT negatiivne (t=-2.42).

===============================================================================
6. WALK-FORWARD  <-- SIIN KUKKUS LABI
===============================================================================

H1-andmeid on 2023-11..2026-09 (~2.8 aastat), mitte 2016-2026. Jaotasin
OLEMASOLEVA kolmeks vordseks osaks, ei teeselnud pikemat ajalugu.

         aken                 periood   signaale   BRUTO bp        t
  -----------   ---------------------   --------   --------   ------
        TRAIN   2024-01-02..2024-11-26       429      -1.46    -0.84   <- NEGATIIVNE
        VALID   2024-11-26..2025-10-14       429      +5.10    +2.19
    FINAL OOS   2025-10-14..2026-09-10       431      +0.73    +0.43   <- ei ole oluline

  Kogu serv ratsutab KESKMISEL aknal. TRAIN on miinuses.
  FINAL OOS murdepunkt oleks 0.73 bp round-trip = 0.37 bp poole kohta —
  see on ALLA parima ECN-spreadi.

===============================================================================
7. KONTSENTRATSIOON  <-- SIIN SAI SELGEKS, MIS SEE TEGELIKULT ON
===============================================================================

      paar   signaale   panus bruto   osa kogusummast
  --------   --------   -----------   ---------------
    USDJPY        198     +1670.7bp            89.0%
    EURUSD        214     +1332.7bp            71.0%
    USDCHF        173     +1207.8bp            64.4%
    GBPUSD        227      +222.8bp            11.9%
    USDCAD        121      -319.6bp           -17.0%
    AUDUSD        177     -1052.8bp           -56.1%
    NZDUSD        179     -1185.5bp           -63.2%

  ILMA USDJPY-ta: bruto +1.46bp  ->  +0.19bp

=> "Selektiivsuse serv" ON long-USDJPY murded 2023-2026 jeeni kukkumise
   ajal. Kolm positiivset paari (USDJPY, EURUSD, USDCHF) on KOIK
   USD-vastu-madala-intressi-valuuta panused. Kolm negatiivset (AUDUSD,
   NZDUSD, USDCAD) on toormevaluutad.

   SEE ON TAPSELT SAMA UKS MAKROPANUS, mis tappis v6 carry-testi
   (seal andis JPY short 82% kogutulust).

===============================================================================
8. MULTIPLE TESTING
===============================================================================

  kogu periood  t = +1.29   p(uhepoolne) = 0.0981
  FINAL OOS     t = +0.43   p(uhepoolne) = 0.3334

  Kogu periood ei ole oluline isegi KORRIGEERIMATA (p=0.098 > 0.05).

  Kontekst: enne seda numbrit on ~11 500 v4-v6 testi + v7 soel. Selle
  filtri komponendid (trend, suht.tugevus, ATR-laienemine) VALITI v7-s
  6 kandidaadi seast TULEMUSE jargi — see on valik, mitte ennustus.
  Bonferroni ainult nende 6 peale: p < 0.0083.
  FINAL OOS p = 0.333 => ei labi isegi seda leebet lavendit.

===============================================================================
9. PORTFELL (A/B/C/D/E, ainult majorid)
===============================================================================

  variant                  paare  teh/a  BRUTO bp  @0.8bp  @2.0bp
  ----------------------   -----  -----  --------  ------  ------
  A) uksikud paarid keskm      7     69     +1.06   +0.26   -0.94
  B) koik majorid koos         7    480     +1.46   +0.66   -0.54
  C) TOP-1 samal paeval        1     99     -0.18   -0.98   -2.18
  D) TOP-2                     2    170     +2.01   +1.21   +0.01
  E) TOP-3                     3    229     +2.43   +1.63   +0.43

  TOP-3 naeb parim, aga see on sama valikunihe — ja kogu tulemus
  tugineb ikka USDJPY-le.

===============================================================================
10. 205 EUR PARIS TAITMINE
===============================================================================

  keskmine SL 0.01 lotiga majoritel: 1.76 EUR = 0.9% 205 EUR kontost

   kapital   risk%   lubatud   taidetavaid signaale   paare
   -------   -----   -------   --------------------   -----
    205 EUR  0.25%     0.51E      0/1289   (  0.0%)     0/7
    205 EUR  0.50%     1.02E      0/1289   (  0.0%)     0/7
    205 EUR  0.75%     1.54E    356/1289   ( 27.6%)     2/7
    205 EUR  1.00%     2.05E    970/1289   ( 75.3%)     5/7
    500 EUR  0.25%     1.25E    179/1289   ( 13.9%)     1/7
    500 EUR  0.50%     2.50E   1289/1289   (100.0%)     7/7
   1000 EUR  0.25%     2.50E   1289/1289   (100.0%)     7/7

===============================================================================
11. LOPPKRITEERIUMID
===============================================================================

  [OK] positiivne bruto (kogu periood)              +1.46 bp
  [OK] positiivne neto ECN-kulul (0.8bp)            +0.66 bp
  [OK] positiivne FINAL OOS                         +0.73 bp
  [OK] moistlik tehingute arv (>100/a)              480/a
  [EI] FINAL OOS statistiliselt oluline (t>2)       t = +0.43
  [EI] TRAIN aken positiivne                        -1.46 bp
  [EI] stabiilne ule majorite (>=5/7 plussis)       4/7
  [EI] ukski paar ei anna >50% kasumist             USDJPY 89%
  [EI] taidetav 205 EUR kontol 0.25% riskiga        0/1289

  LABITUD: 4 / 9

===============================================================================
12. MIKS OTSUS ON D, MITTE C
===============================================================================

C tahendaks "serv on paris, aga liiga vaike".
D tahendab "serva ei olnud".

Ma valin D, sest ma ei suuda toestada, et serv uldse eksisteerib:
  - kogu perioodi t = +1.29, p = 0.098 (ei ole oluline KORRIGEERIMATA)
  - TRAIN aken on NEGATIIVNE
  - 3/7 majorit on miinuses, uks neist oluliselt (NZDUSD t=-2.42)
  - ilma UHE paarita kukub serv +1.46 -> +0.19 bp
  - filtri komponendid valiti tulemuse jargi 6 kandidaadi seast

See muster — positiivne kogu periood, negatiivne alamperiood, kogu tulu
uhest instrumendist, komponendid valitud tagantjarele — on tapselt see,
mida mureandmete peal valik toodab.

Murdepunkt 1.46bp on ILUS number. Aga ilus number millegi umber, mida
ei ole, jaab ikka olematuks.

===============================================================================
13. STOP
===============================================================================

Sinu enda reegel: "Kui vastus on EI: STOP."

Vastus on EI. Ma ei ehita v7.2.

Live-faile main_v4.py, config.py, mt5_connector.py EI MUUDETUD.
Juur ja bot/ on sunkroonis. Koik kompileerub.
Bot ootab /update-i — ara saada.
