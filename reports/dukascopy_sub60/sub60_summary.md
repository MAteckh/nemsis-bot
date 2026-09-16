```
===============================================================================
NEMSIS — SUB-60 TICK EXECUTION TEST
===============================================================================
  16. september 2026  |  haru claude/great-noether-um7382
  UURIMISTEST. Live koodi ei puudutatud. Parameetreid ei optimeeritud.

DATA
-----
  Sundmusi ................ 30 (eelregistreeritud TIER 1, |z| >= 1)
  Unikaalseid hinnaradu ... 21 (aeg, paar) — 30 sundmust EI OLE soltumatud
  Paare ................... 7  AUDUSD EURUSD GBPUSD NZDUSD USDCAD USDCHF USDJPY
  Tick-allikas ............ Dukascopy, paris BID/ASK
  Taitmine ................ OST sisse ASK / valja BID
                            MUUK sisse BID / valja ASK
  Puuduvaid vaatlusi ...... 0 / 1440 lahtrit
  Seeme ................... 20260916
  Mootori audit ........... 26 kontrolli, 0 FAIL

PRIMAARNE EELREGISTREERITUD TEST
--------------------------------
  Sisenemine .............. 0 s parast teadet (esimene tick >= T)
  Hoid .................... 30 s
  N ....................... 30 / 30
  Keskmine ................ +11.143 pip
  Mediaan ................. +4.050 pip
  Kokku ................... +334.30 pip
  Voiduprotsent ........... 90.0%
  Standardhalve ........... 18.986 pip
  t-statistik ............. +3.215
  p-vaartus (t) ........... 0.0032
  Keskmine voit ........... +13.637 pip
  Keskmine kaotus ......... -11.300 pip
  Suurim voit ............. +61.500 pip
  Suurim kaotus ........... -30.700 pip
  Sisenemisspread mediaan . 0.900 pip
  Release -> sisenemine ... mediaan 0.065 s, max 3.663 s
  Sisenemisi tapselt t=0 .. 0

  Juhusliku suuna baseline (samad sundmused ja hinnad, 10 000 permut.):
    keskmine ........ -1.007 pip
    sd .............. 4.122 pip
    5% / 95% ........ -7.877 / +5.784 pip
    signaal asub .... 100.0 pertsentiilis
    p (permut.) ..... 0.0009

  KLASTRITASE (aus N, keskmine sama (aeg, paar) sees):
    N = 21   keskmine +11.374 pip   mediaan +5.900   >0 90.5%
    t = +3.08   p = 0.0059

DELAY x HOLDING MAATRIKS  (KIRJELDAV — siit EI VALITA strateegiat)
------------------------------------------------------------------
  KESKMINE pip
  viiv \ hoid      5s     10s     15s     30s     60s    120s
  0s             7.76    9.67    9.87   11.14   11.46   11.09
  1s             6.41    8.20    8.45    9.12    9.76    9.48
  3s             1.67    2.33    2.78    3.21    3.77    3.68
  5s             0.81    1.06    1.77    1.64    2.71    2.39
  10s           -0.48    0.19    0.76    0.54    0.84    0.79
  15s           -0.09    0.55    0.44   -0.33    0.47    0.51
  30s           -1.38   -0.80   -1.34   -0.29   -0.80   -0.41
  60s           -0.46   -0.74   -0.86   -1.06   -0.91   -0.82

  VOIDUPROTSENT
  viiv \ hoid      5s     10s     15s     30s     60s    120s
  0s            56.7%   73.3%   80.0%   90.0%   86.7%   86.7%
  1s            43.3%   56.7%   80.0%   73.3%   73.3%   70.0%
  3s            46.7%   56.7%   63.3%   63.3%   66.7%   73.3%
  5s            50.0%   63.3%   66.7%   60.0%   60.0%   70.0%
  10s           36.7%   50.0%   53.3%   43.3%   53.3%   50.0%
  15s           40.0%   40.0%   43.3%   33.3%   50.0%   53.3%
  30s           16.7%   36.7%   26.7%   33.3%   50.0%   43.3%
  60s           20.0%   23.3%   30.0%   40.0%   36.7%   40.0%

  MEDIAAN pip
  viiv \ hoid      5s     10s     15s     30s     60s    120s
  0s             1.20    2.35    3.45    4.05    3.65    3.80
  1s            -0.10    0.30    1.45    1.30    1.30    1.00
  3s            -0.10    0.40    0.60    0.60    1.00    0.90
  5s             0.05    0.60    0.80    0.50    0.95    0.80
  10s           -0.30    0.20    0.55   -0.10    0.30    0.10
  15s           -0.25   -0.20   -0.10   -0.40    0.05    0.30
  30s           -0.70   -0.60   -0.60   -0.25   -0.10   -0.25
  60s           -0.45   -0.60   -0.65   -0.30   -0.40   -0.70

  N on 30 igas lahtris. KOKKU pip on failis sub60_matrix.csv.

  Maatriksi ainus sisuline sonum: serv ON AINULT esimestes sekundites.
  0 s -> +11.14   1 s -> +9.12   3 s -> +3.21   5 s -> +1.64
  10 s -> +0.54   15 s -> -0.33   30 s -> -0.29   60 s -> -1.06

EXECUTION QUALITY
-----------------
  Sisenemisspread  mediaan 0.700  keskm 0.945  p90 1.820  max 7.400 pip
  Valjumisspread   mediaan 0.500  keskm 0.610  p90 1.200  max 2.700 pip
  Korrelatsioon sisenemisspread vs |P/L| : +0.583

  Sisenemisspread paeva mediaani suhtes: mediaan 1.66x, p90 3.40x, max 5.33x
  12 sundmusel 30-st oli sisenemisspread >2x paeva mediaanist.
    lai spread (>2x)    n=12  keskm +21.825 pip  mediaan +28.350
    normaalne (<=2x)    n=18  keskm  +4.022 pip  mediaan  +0.800

  5 suurimat |P/L|:
    2026-09-04 12:30  USDCAD  +61.50 pip  sisse-spread 3.20 pip  333 ticki
    2026-07-14 12:30  EURUSD  +44.30 pip  sisse-spread 0.90 pip  401 ticki
    2026-07-14 12:30  EURUSD  +44.30 pip  (sama hinnarada, 2. sundmus)
    2026-07-14 12:30  EURUSD  +44.30 pip  (sama hinnarada, 3. sundmus)
    2026-08-07 12:30  USDCAD  +30.80 pip  sisse-spread 3.00 pip  296 ticki

DATA QUALITY
------------
  Puuduvaid 1-sekundi vaatlusi ... 0
  Muid puuduvaid kombinatsioone .. 0
  Koik 1440 lahtrit taidetud paris tickidega.

  2026-09-07 09:00 EURUSD: esimene tick tuli 3.663 s parast teadet. See
  sundmus ON valimis. Tema D=0 sisenemine on tegelikult +3.663 s.
  2026-09-04 09:00 EURUSD: eelmine tick oli 4.716 s enne teadet. Samuti
  valimis, samuti valja jatmata.
  Kumbagi ei kustutatud ega asendatud. Nulltootlust ei tekitatud.

CHRONOLOGY (kirjeldav)
----------------------
  Esimene pool  n=15  keskm +12.133 pip  mediaan +2.200  kokku +182.00  86.7%
  Teine pool    n=15  keskm +10.153 pip  mediaan +6.700  kokku +152.30  93.3%

DIAGNOSTIC MID-PRICE MOVEMENT (signaalisuunas, enne kulusid)
-----------------------------------------------------------
  horisont     n   keskm pip   mediaan   >0 osa       t        p
   1s         30       1.572     0.150    70.0%    2.08   0.0461
   3s         30       7.352     3.575    76.7%    3.42   0.0019
   5s         30       8.818     2.250    80.0%    3.16   0.0037
  10s         30      10.565     3.300    86.7%    3.07   0.0046
  15s         30      10.793     4.375    90.0%    3.27   0.0028
  30s         30      12.000     5.050    90.0%    3.41   0.0019
  60s         30      12.243     4.475    90.0%    3.31   0.0025

FALSIFIKATSIOON — katsed tulemus umber lukata
---------------------------------------------
  P1  PLATSEEBO ENNE TEADET (sama suund, sama taitmine, hoid 30 s)
        T-300 s .... -0.520 pip   33.3% voite   t -2.54
        T-120 s .... -0.507 pip   30.0% voite   t -3.61
        T-60 s  .... -0.580 pip   13.3% voite   t -4.44
        T+0 s   ... +11.143 pip   90.0% voite   t +3.21
      Enne teadet on tulemus tapselt see, mida spread ette naeb:
      vaike miinus. Serv ilmub AINULT teate hetkel. See on tugev
      argument ajatempli-lookaheadi VASTU.

  P2  KLASTRID. 21 soltumatut hinnarada, mitte 30. Klastritasemel
      +11.374 pip, t +3.08, p 0.0059. Pusib.
      NB: 2026-08-07 12:30 EURUSD-l on KAKS VASTUOLULIST signaali
      (+28.8 ja -30.7 pip). Molemad jaid valimisse.

  P3  KESKHINNA LIIKUMINE ENNE TEADET (signaalisuunas)
        T-300s -> T ... -0.030 pip  p 0.946
        T-120s -> T ... -0.327 pip  p 0.246
        T-60s  -> T ... -0.073 pip  p 0.716
        T-30s  -> T ... -0.078 pip  p 0.654
        T-10s  -> T ... +0.172 pip  p 0.180
      Turg EI liigu signaali suunas enne teadet. Lekke tunnuseid ei ole.

  P4/P7  LIKVIIDSUS. Spread on sisenemishetkel 1.66x paeva tavalisest.
      Aga: spread normaliseerub mediaanis 0.259 s jooksul (p90 1.827 s).
      Kui oodata, kuni spread on <=1.5x paeva mediaanist, ja alles siis
      siseneda, jaab tulemuseks +9.017 pip, t +3.03, 83.3% voite.
      Ehk: tulemus EI OLE lihtsalt laia/mittetaidetava kotatsiooni artefakt.

  P5  KONTSENTRATSIOON — siin on tulemuse nork koht.
        koik            n=30  keskm +11.143  kokku +334.30
        ilma top-1      n=29  keskm  +9.407  kokku +272.80
        ilma top-2      n=28  keskm  +8.161  kokku +228.50
        ilma top-3      n=27  keskm  +6.822  kokku +184.20
        ilma top-5      n=25  keskm  +4.364  kokku +109.10
      Kolm suurimat voitu on SAMA hinnarada (07-14 EURUSD, kolm
      uheaegset inflatsiooniteadet). Sisuliselt on tegu uhe vaatlusega,
      mida loetakse kolm korda.

  P6  LAHENDAMATA RISK. cal_engine.py dokumenteerib, et TradingView ei
      utle, kas 'actual' on ESIALGNE trukk voi hiljem REVIDEERITUD
      vaartus. Kui moni on revideeritud, sisaldab suund infot, mida
      teate hetkel EI OLNUD. Seda EI SAA selle andmeallikaga valistada.
      See on koige tousvam alternatiivseletus sellele tulemusele.

INTERPRETATION
--------------
  1. SIGNAALI SUUND
     Suund on informatiivne. Juhusliku suuna baseline annab -1.007 pip
     (ehk spreadi kulu), signaal +11.143 pip, pertsentiil 100.0,
     permutatsiooni p 0.0009. Suund ei ole muraga seletatav.

  2. TOORE TURULIIKUMINE
     Keskhind liigub signaali suunas +12.0 pip 30 sekundiga, ja 7.35
     pip sellest tuleb juba esimese 3 sekundiga. Enne teadet liikumist
     ei ole (P3). See on puhas teate-efekt.

  3. TAIDETAV BID/ASK P/L
     +11.143 pip 30 sekundiga, 90% voite, t +3.21. Klastritasemel
     +11.374 pip, t +3.08. Platseebo enne teadet -0.58 pip.

  4. SPREAD JA TAITMINE
     Spread laieneb teate hetkel ~1.66x, aga normaliseerub 0.26 s
     jooksul. Normaliseerumist oodates jaab +9.017 pip. Serv kaob
     3-5 sekundiga: 3 s -> +3.21, 5 s -> +1.64, 10 s -> +0.54.
     See tahendab, et KOGU tulemus soltub taitmisest esimese 1-3
     sekundi jooksul. MT5 turuorderi latentsus BlackBulli juures
     EI OLE siin moodetud. Kui reaalne latentsus on 2-3 sekundit,
     on serv laine.

  KOKKUVOTE: see on EBATAVALISELT TUGEV JA NOUAB KINNITUST.

  Tulemus ei ole "toestatud", ei ole "robustne", ei ole
  "production ready". Pohjused:
    - N = 30 sundmust, tegelikult 21 soltumatut hinnarada
    - 3 suurimat voitu on uks ja sama hinnarada
    - ilma top-3-ta kukub keskmine +11.14 -> +6.82
    - valim katab 8 nadalat (juuli-september 2026), uks rezhiim
    - 'actual' revideerimise riski EI SAA selle allikaga valistada
    - taitmislatentsust paris brokeri juures EI OLE moodetud
    - serv kaob 3-5 sekundiga, seega tundlikkus latentsusele on aarmuslik

  Mida see ON: esimene kord selles uurimisprogrammis, kus signaal
  louab juhusliku baseline'i taidetavatel bid/ask hindadel ja
  platseebotest enne teadet on puhas.

  Mida see EI OLE: tootav strateegia.

  MIDA ON VAJA ENNE KUI SEDA USKUDA:
    1. Out-of-sample: 2024-2025 sundmused, samad reeglid, muutmata.
    2. Esialgse trugi ('first print') andmeallikas, et revideerimise
       risk valistada.
    3. Paris taitmislatentsuse moootmine BlackBulli MT5-s.

  MA EI MUUTNUD MITTE MIDAGI live koodis ega paku parameetrimuudatusi.

FAILID
------
  reports/dukascopy_sub60/sub60_event_level.csv    1440 rida
  reports/dukascopy_sub60/sub60_matrix.csv         48 lahtrit
  reports/dukascopy_sub60/sub60_random_baseline.csv 10 000 permutatsiooni
  reports/dukascopy_sub60/sub60_mid_diagnostic.csv
  reports/dukascopy_sub60/sub60_run.txt
  reports/dukascopy_sub60/sub60_falsification.txt
  bot/sub60_tick.py, bot/sub60_tick_audit.py,
  bot/sub60_tick_run.py, bot/sub60_falsify.py
===============================================================================
```
