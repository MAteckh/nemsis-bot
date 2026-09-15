```
===============================================================================
NEMSIS — COT REZHIIMITEST: kas 2016. murdepunkti seletab tururezhiim?
===============================================================================
  kuupaev 2026-09-15   haru claude/great-noether-um7382
  LIVE PUUTUMATA: main_v4.py / config.py / mt5_connector.py /
  strategy_meanrev.py / backtest.py EI OLE muudetud. /update EI saadetud.
  A2/A3/A4/A5 EI OLE alustatud. COT baseline'i EI MUUDETUD.

===============================================================================
0. VASTUS PEAKUSIMUSELE
===============================================================================

  "KAS ME LEIDSIME OBJEKTIIVSE REZHIIMI, MIS OLI ENNE TEHINGUT TEADA JA
   MILLE ABIL COT-I 2016-2026 EDGE'I SAAB AUSALT SELEKTEERIDA?"

  EI.

  36 rezhiimitestist (9 rezhiimi x 2 universumit x 2 jaotust) EI LABI
  UKSKI Benjamini-Hochbergi korrektsiooni. Parim toores p = 0.079.
  Bonferroni lavi oleks 0.0014.

  Koige tahtsam uksiknumber: parim kandidaat USDTREND=HIGH (U28) annab
     kogu valim    +9.66 bp  t = 2.30
     2006-2016     +1.97 bp  t = 0.22   <- ikka NULL, mitte positiivne
     2016-2026    +13.92 bp  t = 3.30
  Rezhiim EI MUUDA vana perioodi kasumlikuks. Ta ainult vahendab kahjumi
  nullini, visates 2/3 valimist ara — ja kukub siis walk-forwardis labi.

  KLASSIFIKATSIOON:  D) FAIL

  COT-i uldstaatus jaab: SAMPLE-DEPENDENT (A1-st muutmata).

===============================================================================
1. BASELINE — MUUTMATA, KONTROLLITUD A1 VASTU
===============================================================================

  Kasutati TAPSELT sama A_REV signaali: net_pct, 156-nadalane
  rullpertsentiil, lavid 0.90/0.10, USD = -(7 valuuta keskmine),
  hoiud 1/2/4 nadalat, release-viive >= 6 paeva, NEMSIS BASE kulud,
  U7 ja U28. Uhtegi parameetrit EI MUUDETUD.

  Audit G1 kontrollis numbrilist identsust A1-ga:

  REGIME                         N    AVG BP  SHARPE   TOTAL%  MAXDD%      T       P
  U7 KOIK 2006-2026           1060      0.00    0.00     -5.8   -46.2   0.00   0.999
    U7 2006-2016               538     -9.41   -0.57    -42.0   -45.0  -1.83   0.068
    U7 2016-2026               522      9.70    0.77     62.4   -11.6   2.45   0.014
  U28 KOIK 2006-2026          1060      2.62    0.19     25.4   -27.6   0.87   0.386
    U28 2006-2016              538     -4.64   -0.27    -25.1   -27.2  -0.88   0.379
    U28 2016-2026              522     10.09    1.13     67.5    -5.0   3.58   0.000

  Koik neli numbrit kattuvad A1-ga tapsusega < 0.02 bp. Baseline on sama.

===============================================================================
2. REZHIIMIKANDIDAADID — 9 tukki, eelregistreeritud
===============================================================================

  kood      definitsioon                                        katvus
  ----      ------------                                        ------
  R1 FXVOL    7 USD-paari 60-paevase tootluse std keskmine       888/1061
  R2 USDTREND |USD-korvi 130-paevane log-muut|                   873/1061
  R3 FXTREND  ristl. keskmine |130p tsentreeritud momentum|      873/1061
  R4 VIX      VIX 60-paevane keskmine                           1061/1061
  R5 SPXTR    S&P 500 130-paevane log-tootlus                    1061/1061
  R6 DISP     valuutatootluste ristl. std (60p)                   888/1061
  R7 RATE     ^IRX (USA 3k T-bill) 60-paevane keskmine          1061/1061
  R8 RATECHG  ^TNX 130-paevane muut                             1061/1061
  R9 COTBRE   COT laius: mitu valuutat ekstreemis               1061/1061

  KATVUSE PIIRANG, mida ei varjata: FX-pohised rezhiimid (R1,R2,R3,R6)
  vajavad 780 kauplemispaeva FX-ajalugu, mis algab 2006-05-15, seega
  need algavad alles 2009-09 / 2009-12. Makrorezhiimid (VIX, SPX, IRX,
  TNX) ja COT-laius on arvutatud OMA PIKIMAL loomulikul indeksil
  (2001-09 / 2000-01) ja katavad KOGU valimi. See oli teadlik valik,
  et 156-nadalane soojendus ei sooks 2006-2009 valimit ara.

  ANDMED JUURDE: laeti Yahoo 25-aastane ajalugu ^VIX, ^GSPC, ^IRX, ^TNX
  (bot/data/{VIX,SPX,IRX,TNX}_d25.csv, 6283-6291 rida, 2001-09 ..).
  BIS policy_rates.csv katab ainult 2016+, seega seda EI SAANUD kasutada
  2006-2016 perioodil — R7/R8 on selle asemel USA turuintressid.

  SEISUNDID (eelregistreeritud, EI OPTIMEERITUD):
    PRIMAARNE  156-nadalane rullpertsentiil, lavi 0.50 (HIGH / LOW)
    SEKUNDAARNE sabad: HIGH kui pct >= 0.75, LOW kui pct <= 0.25
  Uhtegi muud lavi ei proovitud.

  TAHELEPANEK: rull_pertsentiil loeb, kui suur osa aknast on kaesolevast
  VAIKSEM. Diskreetsel muutujal (COTBRE = taisarv) on palju vordseid
  vaartusi, seega "HIGH" osakaal ei ole 50%. Tegelikud osakaalud:
    DISP 0.33, COTBRE 0.38, FXVOL 0.38, FXTREND 0.42, RATE 0.43,
    USDTREND 0.43, RATECHG 0.47, VIX 0.51, SPXTR 0.51

===============================================================================
3. LOOKAHEAD AUDIT — 12 kontrolli, 0 viga  (bot/cot_regime_audit.py)
===============================================================================

  G1 baseline U7  2006-2016 vastab A1-le    -9.41 = -9.41 bp        OK
  G1 baseline U7  2016-2026 vastab A1-le    +9.70 = +9.70 bp        OK
  G1 baseline U28 2006-2016 vastab A1-le    -4.64 = -4.64 bp        OK
  G1 baseline U28 2016-2026 vastab A1-le   +10.09 = +10.09 bp       OK
  G2 TULEVIKU MUUTMINE EI MUUDA VARASEMAID PERTSENTIILE             OK
  G2 warmup NaN kuni aken taidetud                                  OK
  G3 rezhiim on persistentne, mitte nadalane mura                   OK
     (1-nadalane nihe muudab seisundit: USDTREND 15%, COTBRE 14%,
      SPXTR 12%, FXTREND 11%, RATECHG 8%, FXVOL 5%, DISP 3%,
      VIX 3%, RATE 1%)
  G4 HIGH-osakaal raporteeritud (sidemed nihutavad)                 OK
  G5 t_vahe: +1 sigma erinevus n=5000 -> t = 50.5                   OK
  G5 t_vahe: identsed jaotused -> t = 0.97                          OK
  G6 katvus loendatud                                               OK
  G6 5 rezhiimi katavad KOGU valimi                                 OK

  Koik rezhiimimuutujad arvutatakse hindadest kuni SISENEMISE
  sulgemiseni (kaasa arvatud) — see on tapselt see hind, millega
  positsioon avatakse, seega teada. Tulevasi tootlusi, tulevast
  volatiilsust ega full-sample statistikat EI KASUTATUD.

===============================================================================
4. PEATULEMUSED — 18 testi, mediaanjaotus
===============================================================================

  U7 (ALL: 0.00 bp, Sharpe 0.00, t 0.00)
  REGIME              N   AVG BP  SHARPE  TOTAL%  MAXDD%      T      P
  FXVOL HIGH        340     0.94    0.06     1.3   -25.2   0.16  0.869
  FXVOL LOW         547     4.23    0.35    23.5   -21.4   1.13  0.257
    HIGH-LOW              -3.29                          -0.48  0.630
  USDTREND HIGH     373     7.12    0.51    27.9   -15.0   1.36  0.175
  USDTREND LOW      499     0.05    0.00    -1.7   -26.6   0.01  0.990
    HIGH-LOW              +7.07                          +1.07  0.283
  FXTREND HIGH      367     5.63    0.38    20.5   -14.9   1.02  0.308
  FXTREND LOW       505     1.21    0.10     4.4   -26.1   0.32  0.750
    HIGH-LOW              +4.43                          +0.66  0.509
  VIX HIGH          536    -2.69   -0.15   -17.1   -39.3  -0.49  0.622
  VIX LOW           524     2.76    0.24    13.6   -16.8   0.77  0.438
    HIGH-LOW              -5.45                          -0.84  0.403
  SPXTR HIGH        537     1.69    0.15     7.5   -17.5   0.48  0.634
  SPXTR LOW         523    -1.73   -0.10   -12.4   -38.7  -0.31  0.756
    HIGH-LOW              +3.41                          +0.52  0.604
  DISP HIGH         295     2.11    0.14     4.5   -19.3   0.32  0.747
  DISP LOW          592     3.40    0.29    19.7   -21.2   0.98  0.328
    HIGH-LOW              -1.29                          -0.17  0.861
  RATE HIGH         453     5.57    0.48    26.7   -12.3   1.42  0.156
  RATE LOW          607    -4.15   -0.25   -25.6   -40.7  -0.85  0.398
    HIGH-LOW              +9.72                          +1.55  0.122
  RATECHG HIGH      499    -1.97   -0.14   -11.8   -35.2  -0.42  0.671
  RATECHG LOW       561     1.76    0.12     6.8   -20.5   0.38  0.702
    HIGH-LOW              -3.73                          -0.57  0.568
  COTBRE HIGH       399    -5.63   -0.37   -22.0   -32.3  -1.03  0.302
  COTBRE LOW        661     3.40    0.23    20.8   -23.5   0.83  0.405
    HIGH-LOW              -9.04                          -1.33  0.185

  U28 (ALL: 2.62 bp, Sharpe 0.19, t 0.87)
  REGIME              N   AVG BP  SHARPE  TOTAL%  MAXDD%      T      P
  FXVOL HIGH        340     2.51    0.21     7.6    -9.4   0.55  0.585
  FXVOL LOW         547     6.48    0.64    40.5   -15.1   2.08  0.038
    HIGH-LOW              -3.97                          -0.71  0.476
  USDTREND HIGH     373     9.66    0.86    41.6    -8.4   2.30  0.022
  USDTREND LOW      499     1.06    0.10     4.0   -17.1   0.32  0.752
    HIGH-LOW              +8.60                          +1.60  0.109  <- parim
  FXTREND HIGH      367     6.10    0.55    23.6   -12.7   1.46  0.143
  FXTREND LOW       505     3.75    0.35    19.1   -12.3   1.11  0.269
    HIGH-LOW              +2.34                          +0.44  0.662
  VIX HIGH          536     4.71    0.28    23.9   -24.2   0.91  0.362
  VIX LOW           524     0.47    0.05     1.2   -16.9   0.15  0.878
    HIGH-LOW              +4.25                          +0.71  0.480
  SPXTR HIGH        537     1.31    0.14     6.0   -15.3   0.46  0.646
  SPXTR LOW         523     3.96    0.23    18.2   -24.2   0.74  0.462
    HIGH-LOW              -2.65                          -0.43  0.664
  DISP HIGH         295     3.54    0.28     9.7    -9.7   0.68  0.499
  DISP LOW          592     5.67    0.58    37.8   -13.1   1.94  0.052
    HIGH-LOW              -2.13                          -0.36  0.722
  RATE HIGH         453     5.33    0.56    26.0    -8.4   1.65  0.098
  RATE LOW          607     0.59    0.04    -0.5   -24.2   0.13  0.900
    HIGH-LOW              +4.75                          +0.83  0.405
  RATECHG HIGH      499    -1.61   -0.13    -9.4   -31.6  -0.41  0.679
  RATECHG LOW       561     6.37    0.43    38.4   -12.9   1.40  0.161
    HIGH-LOW              -7.98                          -1.34  0.182
  COTBRE HIGH       399    -1.81   -0.11    -9.4   -22.2  -0.31  0.756
  COTBRE LOW        661     5.29    0.44    38.4   -19.3   1.59  0.113
    HIGH-LOW              -7.10                          -1.06  0.290

  SABAD (0.25/0.75), parimad read:
    U28 USDTREND HIGH 163 nadalat  +12.43 bp  Sharpe 1.06  t 1.88  p 0.060
    U28 USDTREND LOW  276 nadalat   -0.93 bp                t -0.25 p 0.805
      HIGH-LOW +13.36, t 1.76, p 0.079   <- kogu uuringu parim toores p
    U28 COTBRE LOW    441 nadalat   +9.41 bp  Sharpe 0.82  t 2.38  p 0.017
      HIGH-LOW -14.71, t -1.24, p 0.214

===============================================================================
5. MULTIPLE TESTING
===============================================================================

  testitud hupoteese kokku: 36
    9 rezhiimi x 2 universumit x 2 jaotust (mediaan + sabad)

  mediaanjaotus (18 testi): BH q=0.05 labis 0.  parim toores p = 0.1095
  sabad         (18 testi): BH q=0.05 labis 0.  parim toores p = 0.0787

  Bonferroni lavi 36 testi juures: 0.0014.
  Parim toores p (0.0787) on sellest 56x suurem.

  MITTE UKSKI REZHIIM EI LABI MITME TESTI KORREKTSIOONI.

  Aus lisamarkus: uksikute seisundite oma t-vaartused (nt U28 USDTREND
  HIGH t=2.30, p=0.022) NAEVAD olulised valja, aga need on parim-36-st
  valikud. Oige test on HIGH-LOW ERINEVUS — see on see, mis kusib "kas
  rezhiim eristab midagi" — ja see ei ole uhelgi juhul oluline.

===============================================================================
6. AASTATE KAUPA — parim kandidaat USDTREND (U28)
===============================================================================

  aasta  domin.rezhiim  HIGH%   n   COT bp/n  aasta%  HIGH bp   LOW bp
  -----  -------------  -----   -   --------  ------  -------   ------
  2006        n/a         n/a   35     -7.47   -2.58      n/a      n/a
  2007        n/a         n/a   53     -5.78   -3.02      n/a      n/a
  2008        n/a         n/a   51    -33.62  -15.75      n/a      n/a
  2009        LOW           2   52     17.75    9.67   -17.06     8.57
  2010        LOW          33   52     -6.62   -3.39     5.75   -12.63
  2011        LOW          19   52      0.22    0.11    30.15    -6.91
  2012        LOW           8   53      0.16    0.09    32.19    -2.45
  2013        LOW          35   52    -12.78   -6.43    -7.22   -15.73
  2014        LOW          44   52     -1.48   -0.77    -4.24     0.71
  2015        HIGH         88   52      1.81    0.95     0.96     8.34
  2016        LOW          38   52     -2.74   -1.42     8.32    -9.65
  2017        LOW          33   52     12.10    6.49    13.77    11.28
  2018        LOW          38   53      9.81    5.34    13.64     7.49
  2019        LOW           6   52     13.92    7.51    57.63    11.24
  2020        HIGH         67   52      4.32    2.27     5.65     1.57
  2021        HIGH         69   52     14.68    7.93    15.77    12.22
  2022        HIGH         81   52     17.20    9.36    20.95     1.45
  2023        LOW          29   52      1.32    0.69    -0.75     2.16
  2024        LOW          25   53      7.51    4.06    13.86     5.45
  2025        HIGH         71   52     15.15    8.19    15.54    14.17
  2026        LOW          47   34      6.95    2.39     2.50    10.91

  2006-2008 on n/a, sest FX-pohise rezhiimi 780-paevane soojendus ei ole
  veel taidetud. See on katvuse piirang, mitte varjatud valik.

  Rezhiim EI ennusta head/halba aastat: 2013 oli LOW ja katastroof
  (-12.78), 2019 oli LOW ja suurepärane (+13.92). 2015 oli HIGH ja
  nork (+1.81).

===============================================================================
7. KAS REZHIIM LIHTSALT JARGIB AEGA?
===============================================================================

  rezhiim      HIGH% 2006-2016   HIGH% 2016-2026    vahe   hinnang
  -------      ---------------   ---------------    ----   -------
  FXVOL                   40.3              37.0    -3.3   ajast soltumatu
  USDTREND                38.0              46.0    +8.0   ajast soltumatu
  FXTREND                 42.3              42.0    -0.3   ajast soltumatu
  VIX                     48.5              52.7    +4.2   ajast soltumatu
  SPXTR                   45.9              55.6    +9.6   ajast soltumatu
  DISP                    37.8              30.1    -7.7   ajast soltumatu
  RATE                    26.6              59.4   +32.8   osaliselt ajaline
  RATECHG                 42.4              51.9    +9.5   ajast soltumatu
  COTBRE                  35.9              39.5    +3.6   ajast soltumatu

  See on hea uudis metoodikale: uksi rezhiim EI OLE lihtsalt ajaline
  proxy. RATE on ainus, mis osaliselt jargib aega (ZIRP 2009-2015 vs
  normaliseerumine 2016+) — ja just tema HIGH-LOW erinevus on
  ebaoluline (p = 0.122 U7, p = 0.405 U28).

===============================================================================
8. OTSUSTAV TEST — kas rezhiim tootab MOLEMAS pooles eraldi?
===============================================================================

  Kui rezhiim on paris, peab HIGH-LOW vahe olema SAMA MARGIGA nii
  2006-2016 kui 2016-2026 sees.

  uni  rezhiim    kogu HIGH-LOW    p    2006-2016    p    2016-2026    p   sama?
  ---  -------    -------------    -    ---------    -    ---------    -   -----
  U7   FXVOL            -3.29  0.630       +6.52 0.561       -9.43 0.265    ei
  U7   USDTREND         +7.07  0.283       +9.34 0.412       +3.56 0.658   JAH
  U7   FXTREND          +4.43  0.509      +12.49 0.259       -0.90 0.914    ei
  U7   VIX              -5.45  0.403      -11.57 0.268       -0.78 0.921   JAH
  U7   SPXTR            +3.41  0.604       +5.37 0.592       -2.34 0.778    ei
  U7   DISP             -1.29  0.861       +2.23 0.846       -1.59 0.871    ei
  U7   RATE             +9.72  0.122       +8.16 0.385       +0.02 0.998   JAH
  U7   RATECHG          -3.73  0.568       -9.37 0.363       -1.83 0.817   JAH
  U7   COTBRE           -9.04  0.185      -12.65 0.262       -6.94 0.373   JAH
  U28  FXVOL            -3.97  0.476       +2.93 0.778       -8.23 0.161    ei
  U28  USDTREND         +8.60  0.109       +8.40 0.435       +7.10 0.210   JAH
  U28  FXTREND          +2.34  0.662       +2.33 0.819       +2.43 0.675   JAH
  U28  VIX              +4.25  0.480       +0.34 0.974       +7.04 0.207   JAH
  U28  SPXTR            -2.65  0.664       -0.17 0.987       -8.19 0.165   JAH
  U28  DISP             -2.13  0.722       -2.64 0.806       +0.12 0.985    ei
  U28  RATE             +4.75  0.405       +1.62 0.863       -1.74 0.763    ei
  U28  RATECHG          -7.98  0.182      -17.27 0.094       -1.61 0.775   JAH
  U28  COTBRE           -7.10  0.290       -2.74 0.827      -12.57 0.019   JAH

  11/18 on sama margiga. Juhuslikult oodataks ~9/18. Ukski neist ei ole
  kummaski pooles oluline (v.a U28 COTBRE 2016-2026 p=0.019, mis on
  uksik lahter 36-st).

  KOIGE OLULISEM ARV KOGU UURINGUS — parima kandidaadi TASE poolte kaupa:

  seisund                        n      bp   sharpe      t      p
  -------                        -      --   ------      -      -
  U28 USDTREND HIGH kogu       373   +9.66     0.86   2.30  0.022
  U28 USDTREND HIGH 2006-2016  133   +1.97     0.14   0.22  0.827   <- NULL
  U28 USDTREND HIGH 2016-2026  240  +13.92     1.54   3.30  0.001
  U28 RATE     HIGH 2006-2016  143   -3.45    -0.32  -0.53  0.594
  U28 COTBRE   LOW  2006-2016  345   -3.65    -0.27  -0.71  0.481
  U28 FXTREND  HIGH 2006-2016  148   -1.90    -0.14  -0.24  0.808
  U7  USDTREND HIGH 2006-2016  133   -1.03    -0.07  -0.11  0.914

  MITTE UKSKI rezhiimiseisund ei tee 2006-2016 perioodi POSITIIVSEKS.
  Parim (USDTREND HIGH) toob selle -4.64-lt +1.97-le, mis on
  statistiliselt null (t = 0.22), ja viskab selleks 75% valimist ara.

===============================================================================
9. WALK-FORWARD — TRAIN 2006-2013 / VALID 2014-2017 / OOS 2018-2026
===============================================================================

  Protokoll: vali AINULT TRAIN-i pealt suurima |HIGH-LOW| rezhiim,
  fikseeri definitsioon, siis vaata VALID ja OOS.

  U7: TRAIN valib FXVOL, kaubelda seisundis HIGH (TRAIN HIGH-LOW +31.88 bp)
      TRAIN-i pingerida: FXVOL +31.9, USDTREND +27.9, FXTREND +24.9,
      DISP +21.9, RATECHG -16.2, COTBRE -14.1, RATE +11.2, VIX -4.4, SPXTR +4.3

      aken                  N   AVG BP  SHARPE  TOTAL%  MAXDD%      T      P
      TRAIN FXVOL=HIGH     54   +20.69    1.20    11.4    -6.9   1.23  0.220
      TRAIN FILTRITA      400    -8.63   -0.49   -31.5   -34.4  -1.36  0.175
      VALID FXVOL=HIGH     99   -14.44   -0.98   -13.8   -15.7  -1.35  0.178
      VALID FILTRITA      208    -5.89   -0.48   -12.3   -19.6  -0.95  0.341
      OOS   FXVOL=HIGH    187    +3.38    0.25     5.6   -15.2   0.47  0.637
      OOS   FILTRITA      452   +10.35    0.81    56.6   -11.6   2.38  0.017

      => VALID: filter on HALVEM kui filtrita (-14.44 vs -5.89)
      => OOS:   filter on HALVEM kui filtrita (+3.38 vs +10.35)
      TAIELIK LABIKUKKUMINE.

  U28: TRAIN valib RATECHG, kaubelda seisundis LOW (TRAIN HIGH-LOW -17.57 bp)
      TRAIN-i pingerida: RATECHG -17.6, USDTREND +16.1, FXTREND +9.1,
      COTBRE -8.3, DISP -7.3, FXVOL +4.2, VIX -0.5, RATE -0.5, SPXTR -0.3

      aken                  N   AVG BP  SHARPE  TOTAL%  MAXDD%      T      P
      TRAIN RATECHG=LOW   212    +2.39    0.12     3.0   -12.9   0.24  0.807
      TRAIN FILTRITA      400    -5.87   -0.33   -23.5   -25.9  -0.91  0.364
      VALID RATECHG=LOW   113    +2.88    0.20     2.7    -6.2   0.30  0.766
      VALID FILTRITA      208    +2.42    0.20     4.3    -9.5   0.40  0.689
      OOS   RATECHG=LOW   236   +11.62    1.29    30.9    -4.3   2.74  0.006
      OOS   FILTRITA      452   +10.21    1.12    57.1    -5.0   3.31  0.001

      => VALID: filter +2.88 vs filtrita +2.42 — praktiliselt sama
      => OOS:   filter +11.62 vs filtrita +10.21 — +1.4 bp, aga POOL
                valimist visatud ara ja kogutootlus 30.9% vs 57.1%
      EI ANNA MIDAGI JUURDE.

  Kummaski universumis EI TEE TRAIN-il valitud rezhiimifilter tulemust
  paremaks. U7-s teeb selgelt halvemaks.

===============================================================================
10. GROSS / COST / NET
===============================================================================

  variant                    N   BRUTO bp  KULU bp  NETO bp  SHARPE      T
  U7  ALL                 1060       0.58     0.57     0.00    0.00   0.00
  U7  USDTREND HIGH        373       7.58     0.46     7.12    0.51   1.36
  U7  USDTREND LOW         499       0.65     0.60     0.05    0.00   0.01
  U28 ALL                 1060       3.60     0.99     2.62    0.19   0.87
  U28 USDTREND HIGH        373      10.55     0.88     9.66    0.86   2.30
  U28 USDTREND LOW         499       2.07     1.01     1.06    0.10   0.32

  Rezhiimifilter EI MUUDA kulustruktuuri (kaive on sama, kulu 0.46-1.01 bp).
  Kogu erinevus tuleb brutost. Kulu ei ole siin probleem ega lahendus.

===============================================================================
11. REV vs CONT — kas rezhiim utleb, kumb suund sobib?
===============================================================================

  A_CONT = -A_REV konstruktsiooni jargi. Tabel naitab, millises
  seisundis kumb suund oleks olnud parem, ja kas vahe on oluline.

  uni  rezhiim    HIGH: parem       LOW: parem        eristab?
  ---  -------    -----------       ----------        --------
  U7   FXVOL      REV (+0.9)        REV (+4.2)        ei (p=0.63)
  U7   USDTREND   REV (+7.1)        REV (+0.0)        ei (p=0.28)
  U7   FXTREND    REV (+5.6)        REV (+1.2)        ei (p=0.51)
  U7   VIX        CONT (-2.7)       REV (+2.8)        ei (p=0.40)
  U7   SPXTR      REV (+1.7)        CONT (-1.7)       ei (p=0.60)
  U7   DISP       REV (+2.1)        REV (+3.4)        ei (p=0.86)
  U7   RATE       REV (+5.6)        CONT (-4.1)       ei (p=0.12)
  U7   RATECHG    CONT (-2.0)       REV (+1.8)        ei (p=0.57)
  U7   COTBRE     CONT (-5.6)       REV (+3.4)        ei (p=0.19)
  U28  FXVOL      REV (+2.5)        REV (+6.5)        ei (p=0.48)
  U28  USDTREND   REV (+9.7)        REV (+1.1)        ei (p=0.11)
  U28  FXTREND    REV (+6.1)        REV (+3.8)        ei (p=0.66)
  U28  VIX        REV (+4.7)        REV (+0.5)        ei (p=0.48)
  U28  SPXTR      REV (+1.3)        REV (+4.0)        ei (p=0.66)
  U28  DISP       REV (+3.5)        REV (+5.7)        ei (p=0.72)
  U28  RATE       REV (+5.3)        REV (+0.6)        ei (p=0.40)
  U28  RATECHG    CONT (-1.6)       REV (+6.4)        ei (p=0.18)
  U28  COTBRE     CONT (-1.8)       REV (+5.3)        ei (p=0.29)

  18 / 18 = "ei eristanud". Ukski rezhiim ei utle ette, kumb suund
  parajasti sobib. Lahedaim on U7 RATE (p=0.12) ja U28 USDTREND (p=0.11).

===============================================================================
12. LOPLIK KLASSIFIKATSIOON
===============================================================================

  kriteerium                                       tulemus         staatus
  ----------                                       -------         -------
  baseline muutmata ja A1-ga identne               4/4 numbrit     LABIB
  lookahead puudub                                 12/12 auditit   LABIB
  rezhiimid ei ole lihtsalt ajalised proxy'd       8/9             LABIB
  monigi rezhiim labib BH-korrektsiooni            0/36            KUKUB
  monigi rezhiim teeb 2006-2016 positiivseks       0/36            KUKUB
  monigi rezhiim eristab REV vs CONT (p<0.05)      0/18            KUKUB
  TRAIN-il valitud filter tootab VALID-is          ei              KUKUB
  TRAIN-il valitud filter tootab OOS-is            ei              KUKUB

  KLASSIFIKATSIOON:  D) FAIL

  Pohjendus: eesmark oli falsifitseerida, ja falsifitseerimine onnestus.
  Uhtegi objektiivset, enne tehingut teada olevat rezhiimi, mis 2016.
  aasta murdepunkti seletaks, EI LEITUD. Parim kandidaat (USDTREND)
  jatab 2006-2016 perioodi ikka nulli (t=0.22), kukub labi
  mitmese testimise korrektsioonis (p=0.109) ja kukub labi
  walk-forwardis.

  COT-i uldstaatus jaab A1-st: SAMPLE-DEPENDENT.

===============================================================================
13. MIDA EI TEHTUD
===============================================================================

  COT baseline'i ei muudetud (156n, 0.90/0.10, hoiud 1/2/4, USD-konstruktsioon)
  rezhiimilavisid ei optimeeritud (ainult 0.50 ja 0.25/0.75)
  paare ega valuutasid ei eemaldatud tulemuste jargi
  live-faile ei muudetud; /update ei saadetud
  A2/A3/A4/A5 ei alustatud

===============================================================================
KOOD JA ANDMED
===============================================================================
  bot/cot_regime.py         9 eelregistreeritud rezhiimi, seisundid, t_vahe
  bot/cot_regime_audit.py   12 kontrolli (sh baseline = A1 identsus)
  bot/cot_regime_run.py     18 testi, BH, otsustav pooltetest, bruto/kulu/neto
  bot/cot_regime_run2.py    sabad, ajaline test, aastad, walk-forward, REV/CONT
  bot/data/VIX_d25.csv      6291 rida  2001-09-17 ..
  bot/data/SPX_d25.csv      6288 rida  2001-09-17 ..
  bot/data/IRX_d25.csv      6283 rida  2001-09-17 ..
  bot/data/TNX_d25.csv      6283 rida  2001-09-17 ..
===============================================================================
```
