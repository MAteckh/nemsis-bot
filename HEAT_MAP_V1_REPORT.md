```
===============================================================================
NEMSIS HEAT MAP v1 — ARUANNE
===============================================================================
  kuupaev 2026-09-15   haru claude/great-noether-um7382
  27 604 PARIS tehingut, genereeritud rakendatud reeglitest ajaloolistel
  andmetel. Uhtegi naidisarvu ega kohatait ei ole.
  LIVE PUUTUMATA. /update EI saadetud.

===============================================================================
0. KOKKUVOTE JUHILE
===============================================================================

  RADA A (H1 sisenemised, H4 kontekst, 2023-11 .. 2026-09):
    KOIK 60 paar-strateegia lahtrit on neto NEGATIIVSED. Mitte uks ei ole
    positiivne kogu valimil. Pohjus on mooedetud ja uheselt selge:
    1.5 x ATR stopp on H1-l ~11 bp, spread+slip on 1.3-2.5 bp edasi-tagasi,
    seega KULU = 0.19 R IGA TEHINGU KOHTA. Brutoserv on -0.01 .. -0.08 R.
    H1 selle stopilaiusega on struktuurselt kahjumlik.

  RADA B (D1 sisenemised, W1 kontekst, 2006-2026, kusitud jaotus):
    Kulu on 0.035 R, seega mang on aus. 34/60 lahtrit on OOS-is positiivsed.
    Parim strateegia on MOMENTUM (bruto +0.073 R, neto +0.030 R, t = 1.20).
    AGA: 0 lahtrit 92-st labib p < 0.05 positiivsel poolel, ja
    korr(VALID, OOS) = -0.205 — OOS-i voitjad on VALID-i kaotajad.

  UHTEGI ROBUSTSET STRATEEGIA-PAARI KOMBINATSIOONI EI LEITUD.

===============================================================================
1. ANDMED — MIDA TEGELIKULT ON JA MIDA EI OLE
===============================================================================

  ajaraam  paare  vahemik                     baare     kasutatav?
  -------  -----  -------                     -----     ----------
  H1          15  2023-11-27 .. 2026-09-11   ~17 300   JAH (2.79 a)
  M15         15  2026-06-22 .. 2026-09-11    ~5 590   EI (81 paeva)
  D1          15  2001-09 / 2006-05 .. 2026-09 5 271-6 491  JAH (20.3 a)

  KUSITUD 1H kontekst + 15m sisenemised: M15 katab 81 PAEVA. Sellega ei
  saa teha TRAIN/VALID/OOS jaotust. KUSITUD TRAIN 2006-2013 intraday:
  selliseid andmeid selles repos EI OLE ja Yahoo tunniandmed ulatuvad
  ~730 paeva tagasi. ANDMEID EI LEIUTATUD.

  Seetottu kaks rada, molemad PARIS andmetel:
    RADA A  kontekst H4 + sisenemine H1   (sama 1:4 suhe mis 1H:15m)
    RADA B  kontekst W1 + sisenemine D1   (KUSITUD jaotus tapselt)

===============================================================================
2. PAAR x STRATEEGIA, OOS neto oodatav vaartus (R/tehing) + n
===============================================================================

  RADA B (D1), OOS 2018-2026
  paar       TREND_PULLBACK   BREAKOUT_RETEST  MEAN_REVERSION      MOMENTUM
  EURUSD     -0.612/39        -0.215/55        +0.086/18       -0.070/70
  GBPUSD     -0.168/31        -0.031/54        +0.282/14       -0.020/63
  USDJPY     +0.071/37        -0.023/46        +0.224/20       +0.236/66
  AUDUSD     +0.303/21        -0.100/62        -0.022/16       +0.049/63
  NZDUSD     -0.272/23        -0.152/62        -0.203/11       -0.077/67
  USDCAD     -0.338/22        -0.016/61        +0.250/28       +0.063/66
  USDCHF     -0.344/25        +0.161/57        +0.138/13       -0.113/67
  EURGBP     -0.876/5         -0.190/36        +0.203/19       -0.208/73
  EURJPY     +0.947/10        +0.068/40        +0.185/18       +0.178/76
  GBPJPY     -0.598/13        -0.083/57        +0.078/25       +0.285/71
  AUDJPY     +0.523/25        +0.020/60        -0.194/19       +0.085/74
  EURCHF     +0.105/17        +0.298/37        -0.087/20       +0.241/65
  EURAUD     +1.052/8         +0.226/19        -0.081/27       +0.017/71
  GBPAUD     +0.083/12        +0.078/30        +0.075/23       +0.050/65
  AUDCAD     +0.077/27        -0.011/73        +0.266/12       +0.168/72

  NB: EURAUD TREND_PULLBACK +1.052 tugineb 8 TEHINGULE ja EURJPY +0.947
  10 tehingule. Need EI OLE leiud, need on mura. n < 30 lahtrid ei
  kvalifitseeru pingereas.

  RADA A (H1), OOS 2025-09 .. 2026-09
  paar       TREND_PULLBACK   BREAKOUT_RETEST  MEAN_REVERSION      MOMENTUM
  EURUSD     -0.289/115       -0.260/218       -0.181/62       -0.265/188
  GBPUSD     -0.431/109       -0.220/215       -0.349/55       -0.380/195
  USDJPY     -0.263/80        -0.232/191       -0.434/68       -0.200/157
  AUDUSD     -0.074/119       -0.263/216       +0.121/47       -0.188/199
  NZDUSD     -0.249/137       -0.224/236       -0.229/43       -0.315/186
  USDCAD     -0.272/128       -0.131/172       -0.448/36       -0.224/153
  USDCHF     -0.371/101       -0.102/204       -0.189/64       -0.416/175
  EURGBP     -0.585/92        -0.441/171       +0.010/49       -0.579/194
  EURJPY     -0.274/93        -0.188/184       -0.291/56       -0.280/162
  GBPJPY     -0.348/96        -0.210/217       -0.250/55       -0.203/167
  AUDJPY     -0.193/106       -0.070/217       -0.307/52       -0.134/179
  EURCHF     -0.544/89        -0.317/138       -0.308/39       -0.190/131
  EURAUD     -0.550/84        -0.367/203       -0.297/57       -0.302/161
  GBPAUD     -0.486/89        -0.469/203       +0.032/46       -0.444/193
  AUDCAD     -0.233/83        -0.295/149       +0.058/49       -0.346/135

  60 lahtrist 57 on negatiivsed. Kolm "positiivset" on 0.01-0.12 R
  47-49 tehingu peal ja ukski ei ole oluline.

===============================================================================
3. STRATEEGIA x REZHIIM, OOS (neto R/tehing + n)
===============================================================================

  RADA B (D1)
  strateegia        HIGH_VOL      LOW_VOL      TRENDING      RANGING
  TREND_PULLBACK   -0.068/164   -0.050/151   -0.059/315        n/a
  BREAKOUT_RETEST  -0.017/291   -0.017/458   -0.108/251   +0.048/322
  MEAN_REVERSION   +0.069/66    +0.083/217        n/a     +0.080/283
  MOMENTUM         -0.060/389   +0.132/640   -0.052/379   +0.201/423

  RADA A (H1)
  strateegia        HIGH_VOL      LOW_VOL      TRENDING      RANGING
  TREND_PULLBACK   -0.230/737   -0.430/784   -0.333/1521       n/a
  BREAKOUT_RETEST  -0.231/1295  -0.263/1639  -0.317/1147  -0.141/1135
  MEAN_REVERSION   -0.169/229   -0.225/549        n/a     -0.209/778
  MOMENTUM         -0.247/1022  -0.340/1553  -0.361/1043  -0.205/959

  KOIGE HUVITAVAM LAHTER KOGU UURINGUS:
  D1 MOMENTUM RANGING-rezhiimis +0.201 R/tehing 423 tehingu peal.
  See on VASTUOLUS ootusega (momentum peaks tootama trendis, mitte
  vahemikus) ja seetottu kahtlane — toenaoliselt on tegu ADX < 20
  jargse madalvolatiilsuse mojuga, mitte "momentumiga vahemikus".
  TREND_PULLBACK on TRENDING-rezhiimis NEGATIIVNE (-0.059) — tapselt
  vastupidi sellele, milleks ta ehitatud on.

  n/a lahtrid on definitsiooni jargi tuhjad: TREND_PULLBACK nouab
  ADX >= 25 (ei saa olla RANGING), MEAN_REVERSION nouab ADX < 20
  (ei saa olla TRENDING).

===============================================================================
4. PAAR x REZHIIM, OOS (RADA B, neto R/tehing + n, min n = 20)
===============================================================================

  paar      HIGH_VOL      LOW_VOL      TRENDING      RANGING
  EURUSD   -0.373/75    -0.104/107   -0.422/95    -0.008/61
  GBPUSD   -0.168/64    +0.067/98    -0.266/79    +0.182/50
  USDJPY   +0.324/56    +0.031/113   +0.107/86    +0.344/51
  AUDUSD   -0.127/51    +0.084/111   -0.040/57    +0.053/79
  NZDUSD   -0.329/58    -0.038/105   -0.125/60    -0.055/61
  USDCAD   -0.138/60    +0.094/117   -0.115/52    +0.164/97
  USDCHF   +0.063/64    -0.094/98    -0.121/71    -0.069/53
  EURGBP   -0.530/44    +0.009/89    -0.473/20    -0.041/67
  EURJPY   +0.233/59    +0.180/85    +0.156/54    +0.283/77
  GBPJPY   -0.008/66    +0.102/100   -0.167/51    +0.193/94
  AUDJPY   +0.090/75    +0.099/103   +0.297/88    -0.058/74
  EURCHF   +0.236/47    +0.170/92    -0.070/52    +0.380/55
  EURAUD   +0.034/49    +0.132/76    +0.138/38    +0.171/75
  GBPAUD   -0.114/50    +0.175/80    -0.259/54    +0.208/64
  AUDCAD   +0.130/92    +0.050/92    +0.072/88    +0.059/70

  MUSTER: RANGING on parem kui TRENDING 11/15 paaril, ja LOW_VOL on
  parem kui HIGH_VOL 10/15 paaril. See on jarjekindel ja majanduslikult
  moistetav (madalam volatiilsus = vaiksem SL = kulu suurem osakaal...
  ei, vastupidi: madalam vol = vahem valesid murdeid). AGA see muster
  EI KANNA ULE RADA A-le, kus KOIK 60 lahtrit on negatiivsed.

===============================================================================
5. TOP 10 OOS-KANDIDAATI (n >= 30), TAISSTATISTIKA
===============================================================================

  #  rada  paar    strateegia         n   wr%   ood_R    PF  Shrp  maxDD%  kokku%  aast%     t      p
  1  B_D1  EURCHF  BREAKOUT_RETEST   37  51.4  +0.298  1.59  0.44    -5.3    11.2    1.3  1.29  0.196
  2  B_D1  GBPJPY  MOMENTUM          71  49.3  +0.285  1.58  0.60    -7.9    21.6    2.3  1.77  0.076
  3  B_D1  EURCHF  MOMENTUM          65  53.8  +0.241  1.52  0.53    -7.9    16.3    1.8  1.51  0.131
  4  B_D1  USDJPY  MOMENTUM          66  53.0  +0.236  1.51  0.53    -7.9    16.2    1.9  1.51  0.131
  5  B_D1  EURJPY  MOMENTUM          76  48.7  +0.178  1.33  0.40    -7.8    13.7    1.5  1.17  0.243
  6  B_D1  AUDCAD  MOMENTUM          72  45.8  +0.168  1.33  0.37    -7.1    12.2    1.4  1.08  0.280
  7  B_D1  USDCHF  BREAKOUT_RETEST   57  49.1  +0.161  1.33  0.33    -5.5     9.1    1.0  0.96  0.338
  8  A_H1  AUDUSD  MEAN_REVERSION    47  63.8  +0.121  1.29  0.88    -4.1     5.6    6.1  0.85  0.396
  9  B_D1  AUDJPY  MOMENTUM          74  40.5  +0.085  1.15  0.19    -9.9     5.9    0.7  0.56  0.578
  10 B_D1  GBPAUD  BREAKOUT_RETEST   30  43.3  +0.078  1.14  0.12    -5.7     2.1    0.3  0.33  0.743

  (ood_R = neto oodatav R/tehing; kokku% ja aast% = 1% riski juures;
   maxDD% = sama equity peal; Shrp = tehingupohine Sharpe aastastatult)

  SAMA 10 KANDIDAATI — JARJEPIDEVUS JA ROBUSTSUS
  #  kombinatsioon                      TRAIN    VALID     OOS  sp+50/sl2x  SL1.25  SL1.75  MC dd5%
  1  B_D1 EURCHF BREAKOUT_RETEST       -0.143  +0.135  +0.298      +0.248  +0.530  +0.121    -7.8
  2  B_D1 GBPJPY MOMENTUM              +0.414  -0.010  +0.285      +0.261  +0.168  +0.357   -10.2
  3  B_D1 EURCHF MOMENTUM              +0.075  -0.197  +0.241      +0.193  +0.236  +0.219    -9.6
  4  B_D1 USDJPY MOMENTUM              -0.102  -0.415  +0.236      +0.221  +0.321  +0.216    -9.7
  5  B_D1 EURJPY MOMENTUM              +0.247  -0.408  +0.178      +0.152  +0.171  +0.101   -12.1
  6  B_D1 AUDCAD MOMENTUM              +0.085  -0.305  +0.168      +0.135  +0.172  +0.204   -11.6
  7  B_D1 USDCHF BREAKOUT_RETEST       -0.110  -0.050  +0.161      +0.144  +0.098  +0.160   -10.0
  8  A_H1 AUDUSD MEAN_REVERSION        -0.176  -0.093  +0.121      +0.027  +0.213  -0.089    -7.6
  9  B_D1 AUDJPY MOMENTUM              +0.242  +0.004  +0.085      +0.063  +0.128  -0.004   -13.3
  10 B_D1 GBPAUD BREAKOUT_RETEST       -0.043  +0.343  +0.078      +0.048  -0.038  +0.020    -8.7

  7 / 10 parimast OOS-kandidaadist on VALID-is NEGATIIVSED.
  Ainult 2 (nr 1 ja nr 10) on nii VALID-is kui OOS-is positiivsed.

===============================================================================
6. STATISTILINE HINNANG
===============================================================================

  OOS-lahtreid n >= 30                        92
  neist positiivse ootusega                   20 (22%)
  neist p < 0.05 POSITIIVSEL poolel            0
  BH q=0.05 "labis" 28 — AGA KOIK 28 on oluliselt NEGATIIVSED lahtrid
  Bonferroni lavi 92 testi juures             0.00054
  parim positiivne toores p                   0.076

  VALID <-> OOS jarjepidevus:
    RADA A: 0/60 molemas positiivne,  korr = +0.242
    RADA B: 12/60 molemas positiivne, korr = -0.205  <- NEGATIIVNE

  Negatiivne korrelatsioon VALID-i ja OOS-i vahel on ulesobitamise
  klassikaline signatuur: see, mis uhes aknas tootab, kaotab jargmises.

  STRATEEGIA AGREGAAT (koik 15 paari koos, kogu valim)
  rada  strateegia            n      wr%  bruto R/teh  kulu R/teh  neto R/teh      t
  A_H1  TREND_PULLBACK     4240     31.6      -0.0760      0.1869     -0.2629 -12.57
  A_H1  BREAKOUT_RETEST    7985     32.7      -0.0401      0.1851     -0.2252 -14.65
  A_H1  MEAN_REVERSION     2051     49.2      -0.0137      0.1860     -0.1997  -9.05
  A_H1  MOMENTUM           7039     31.5      -0.0720      0.1926     -0.2645 -16.30
  B_D1  TREND_PULLBACK     1009     39.0      +0.0395      0.0351     +0.0044  +0.11
  B_D1  BREAKOUT_RETEST    2011     38.3      +0.0205      0.0368     -0.0164  -0.57
  B_D1  MEAN_REVERSION      591     50.1      -0.0026      0.0420     -0.0446  -1.10
  B_D1  MOMENTUM           2678     40.7      +0.0732      0.0429     +0.0303  +1.20

  See tabel on kogu uuringu tuum. H1-l on BRUTO serv negatiivne KOIGIL
  neljal perekonnal — kulu ainult suvendab seda. D1-l on bruto serv
  kolmel perekonnal positiivne, aga nii vaike, et ainult MOMENTUM jaab
  parast kulusid ulespoole, ja seegi t = 1.20 juures.

===============================================================================
7. VASTUSED 8 KUSIMUSELE
===============================================================================

  1. MILLINE STRATEEGIA ON IGA PAARI JAOKS PARIM?
     RADA B (D1) OOS parim strateegia paari kohta:
       EURUSD MEAN_REVERSION(n=18)*  GBPUSD MEAN_REVERSION(14)*
       USDJPY MOMENTUM(66)           AUDUSD TREND_PULLBACK(21)*
       NZDUSD MOMENTUM(67) neg       USDCAD MEAN_REVERSION(28)*
       USDCHF BREAKOUT(57)           EURGBP MEAN_REVERSION(19)*
       EURJPY TREND_PULLBACK(10)*    GBPJPY MOMENTUM(71)
       AUDJPY TREND_PULLBACK(25)*    EURCHF BREAKOUT(37)
       EURAUD TREND_PULLBACK(8)*     GBPAUD BREAKOUT(30)
       AUDCAD MEAN_REVERSION(12)*
     * = alla 30 tehingu, EI OLE usaldusvaarne.
     Piisava valimiga (n >= 30) jaab alles: MOMENTUM 4 paaril,
     BREAKOUT_RETEST 3 paaril. Ukski pole statistiliselt oluline.
     RADA A (H1): mitte uhelgi paaril ei ole positiivset strateegiat.

  2. MILLINE REZHIIM ON IGA PAARI JAOKS PARIM?
     RADA B: RANGING > TRENDING 11/15 paaril, LOW_VOL > HIGH_VOL 10/15.
     Parimad lahtrid: EURCHF RANGING +0.380, USDJPY RANGING +0.344,
     AUDJPY TRENDING +0.297, EURJPY RANGING +0.283.
     RADA A: KOIK rezhiimid koigil paaridel negatiivsed. Parim on
     NZDUSD RANGING +0.006 (praktiliselt null).

  3. MILLISED KOMBINATSIOONID ELAVAD ULE OOS-i?
     Nominaalselt 20 lahtrit 92-st. Statistiliselt: MITTE UKSKI
     (0 lahtrit p < 0.05 positiivsel poolel, BH labib 0).
     Jarjepidevusnoude (VALID ja OOS molemad positiivsed) labib
     RADA B-s 12/60 ja RADA A-s 0/60.

  4. MILLISED ELAVAD ULE KULUDE HALVENEMISE?
     TOP-7 (koik RADA B) jaavad spread+50% JA slip 2x juures
     positiivseks, kaotades 0.03-0.05 R. Nr 8 (A_H1 AUDUSD
     MEAN_REVERSION) langeb +0.121 -> +0.027 ja on praktiliselt surnud.
     Kulude halvenemine EI OLE nende kandidaatide peamine oht —
     peamine oht on, et neid ei ole olemas.

  5. MILLISED ON TOENAOLISELT ULESOBITATUD?
     - koik n < 30 lahtrid (EURAUD TREND_PULLBACK +1.052 / n=8,
       EURJPY TREND_PULLBACK +0.947 / n=10, EURGBP -0.876 / n=5)
     - 7/10 top-kandidaadist, mille VALID on negatiivne
     - kogu RADA B pingerida tervikuna, arvestades korr(VALID,OOS) = -0.205
     - A_H1 AUDUSD MEAN_REVERSION: SL 1.75xATR juures -0.089 (margivahetus)

  6. KAS ON UNIVERSAALNE STRATEEGIA VOI ON NAD PARISELT PAARISPETSIIFILISED?
     EI OLE TOENDEID PAARISPETSIIFILISUSEST. Kui strateegia-paari sobivus
     oleks paris, oleks korr(VALID, OOS) POSITIIVNE. Ta on RADA B-s
     -0.205 ja RADA A-s +0.242 (samuti nork). Paarispetsiifilisus, mida
     heatmap silmale NAITAB, on valimimura.
     Kui midagi universaalset on, siis: MOMENTUM on D1-l ainus perekond
     positiivse neto agregaadiga (+0.030 R, t=1.20), ja H1 on KOIGI
     perekondade jaoks kahjumlik. Need kaks on ainsad mustrid, mis
     kanduvad ule paaride.

  7. MILLISED 3-5 KANDIDAATI VAARIVAD JARGMIST UURIMISETAPPI?
     Aus vastus: MITTE UKSKI ei vaari "strateegia" etappi. Aga kui
     jargmine etapp on EDASINE UURIMINE (mitte juurutamine), siis:
       a) D1 MOMENTUM agregaadina (mitte paari kaupa) — n=2678, ainus
          positiivse neto agregaadiga perekond
       b) D1 MOMENTUM RANGING-rezhiimis (+0.201 R, n=423) — koige
          suurem rezhiimiefekt, AGA kontrollida tuleb, kas see on
          tegelikult madalvolatiilsuse artefakt
       c) D1 MEAN_REVERSION rezhiimide loikes (+0.069..+0.083 koigis
          kolmes rezhiimis, kus ta uldse kaupleb) — konsistentne, kuigi
          n on vaike ja agregaat neto -0.045
       d) SL-laiuse ja kulu suhte uurimine: H1 kukub ainult seetottu, et
          stopp on 11 bp ja kulu 2.5 bp. Sama loogika laiema stopiga?
       e) EURCHF BREAKOUT_RETEST — ainus top-kandidaat, mis on
          positiivne NII VALID-is (+0.135) KUI OOS-is (+0.298)
     Neist a) ja d) on ainsad, millel on piisav valim jarelduseks.

  8. MILLISED KANDIDAADID TULEB KORVALE HEITA?
     - KOGU RADA A (H1 + 1.5xATR stopp): 60/60 lahtrit negatiivsed,
       bruto serv negatiivne koigil neljal perekonnal. See ei ole
       kuluprobleem, mida saaks parema brokeriga lahendada — bruto on
       juba miinuses.
     - TREND_PULLBACK moelmal rajal: D1 agregaat +0.004 R (t=0.11),
       H1 -0.263 R, ja TRENDING-rezhiimis (tema enda rezhiim!)
       D1-l -0.059 R. Strateegia ei toota isegi seal, kus ta peaks.
     - koik n < 30 lahtrid pingereas
     - A_H1 AUDUSD MEAN_REVERSION (margivahetus parameetri norgendusel)

===============================================================================
8. LOPPOTSUS
===============================================================================

  UHTEGI ROBUSTSET STRATEEGIA x PAAR x REZHIIM KOMBINATSIOONI EI LEITUD.

  kriteerium                                       tulemus      staatus
  ----------                                       -------      -------
  tulemused parinevad paris tehingutest            27 604       LABIB
  lookahead puudub                                 22/22        LABIB
  kulud modelleeritud ja raporteeritud             bruto+neto   LABIB
  TRAIN/VALID/OOS kronoloogiline                   jah          LABIB
  monigi OOS-lahter p < 0.05 positiivsel poolel    0/92         KUKUB
  monigi lahter labib BH q=0.05 positiivselt       0/92         KUKUB
  VALID ja OOS on jarjepidevad                     korr -0.205  KUKUB
  RADA A (kusitud ajaraam) annab midagi            0/60         KUKUB

  See EI OLE tooriista viga. Backtest-mootor on auditeeritud 22 testiga,
  sealhulgas teadaoleva vastusega TP/SL testidega (+2.000000 ja
  -1.000000 tapselt) ja tuleviku-rikkumise testiga koigil neljal
  strateegial. Tulemus on tulemus.

  KOIGE VAARTUSLIKUM UKSIKLEID: H1-l on 1.5 x ATR stopp ~11 bp ja
  edasi-tagasi kulu 1.3-2.5 bp, seega KULU = 19% RISKIUHIKUST IGA
  TEHINGU KOHTA. Selle juures peaks bruto voiduprotsent olema ~6
  protsendipunkti ule aus-mangu taseme, et ainult nulli jouda. Uhelgi
  neljast perekonnast ei ole seda. Kui H1-l kaubelda, peab stopp olema
  oluliselt laiem VOI kulu oluliselt madalam — vastasel juhul on
  strateegia valik ebaoluline.

===============================================================================
9. FAILID
===============================================================================
  HEAT_MAP_V1_REPORT.md        see aruanne
  HEAT_MAP_V1_AUDIT.md         andmed, reeglid, parameetrid, lookahead-audit
  HEAT_MAP_V1_RESULTS.csv      1 319 rida: rada x paar x strateegia x ulatus
  HEAT_MAP_V1_TRADES.csv       27 604 tehingut, iga tehing eraldi reana
  HEAT_MAP_V1_ROBUSTNESS.csv   80 rida: spread/slip/SL/Monte Carlo
  HEAT_MAP_V1_HEATMAP.png      4 paneeli: ootus, Sharpe, PF, maxDD
  HEAT_MAP_V1_OOS_HEATMAP.png  OOS neto ootus, 15 paari x 4 strateegiat

  kood (kogu uus, live puutumata):
  bot/hm_engine.py   andmed, indikaatorid, 4 strateegiat, simulaator, stat
  bot/hm_audit.py    22 lookahead- ja korrektsuskontrolli
  bot/hm_run.py      taisbacktest + robustsus -> 3 CSV-d
  bot/hm_plot.py     maatriksid + 2 PNG-d

  reprodutseerimine:
    python3 bot/hm_audit.py && python3 bot/hm_run.py && python3 bot/hm_plot.py
===============================================================================
```
