```
===============================================================================
NEMSIS — D1 MOMENTUM EDGE VALIDATION v1
===============================================================================
  kuupaev 2026-09-15   haru claude/great-noether-um7382
  LIVE PUUTUMATA: main_v4.py, config.py, mt5_connector.py,
  strategy_meanrev.py, backtest.py — git diff HEAD nende peal on TUHI.
  /update EI saadetud. RESEARCH ONLY.

===============================================================================
0. LOPPVERDIKT
===============================================================================

                        FINAL VERDICT:  E) FAIL

  D1 MOMENTUM +0.0303 R/tehing EI OLE serv. Kaheksast eelregistreeritud
  FAIL-tingimusest on taidetud SEITSE.

  KOIGE OTSUSTAVAM UKSIKNUMBER:
    juhuslik sisenemine (1000 katset, sama SL/TP/valjumine/kulu/periood/
    instrumendid, ainult sisenemissignaal juhuslik):
        juhuslik  +0.0126 R/tehing, sd 0.0268, 95% kvantiil +0.0572
        TEGELIK   +0.0294 R/tehing  =>  protsentiil 74.0, p = 0.26
    Sisenemissignaal EI ERINE juhuslikust sisenemisest.

===============================================================================
1. BASELINE — REEGLID MUUTMATA
===============================================================================

  bot/d1_momentum_validation.py IMPORDIB reeglid otse hm_engine.py-st
  (import, mitte kopeerimine): sisenemine, SL 1.5 x ATR(14), TP 2.0 R,
  max hoid 20 baari, uks positsioon korraga, sisenemine jargmise baari
  avahinnaga, SL ja TP samas baaris => SL, kulu 2 x (spread + 0.3 bp) /
  SL-kaugus, rezhiimid W1 eelmiselt lopetatud baarilt.
  UHTEGI REEGLIT EI MUUDETUD.

  n = 2483 (2006-01-04 .. 2026-09-03, 15 paari, 20.7 aastat)
  bruto +0.0720 R   kulu 0.0426 R   neto +0.0294 R   t = 1.13   p = 0.260

  (Heat Map v1 raporteeris n=2678 ja +0.0303 R, sest seal olid kaasas ka
   2003-2005 tehingud paaridel, mille ajalugu ulatub kaugemale. 2006+
   loige on siin kasutusel, sest AUDUSD algab 2006-05.)

===============================================================================
2. PERIOODID  (D1_MOMENTUM_PERIOD_RESULTS.csv)
===============================================================================

  periood              n   wr%    neto_R    PF  Sharpe  maxDD%      t      p   pos.paare
  2006-2010          661  41.0  +0.0956  1.16    0.80   -25.0   1.79  0.074      9/15
  2011-2015          575  38.4  -0.0414  0.93   -0.35   -31.6  -0.78  0.435      6/15
  2016-2020          585  39.1  -0.0316  0.95   -0.27   -35.4  -0.60  0.547      6/15
  2021-2026          662  44.0  +0.0787  1.14    0.67   -21.2   1.59  0.111      8/15
  TRAIN 2006-2013    997  40.6  +0.0648  1.11    0.54   -41.3   1.52  0.128     10/15
  VALID 2014-2017    457  36.5  -0.1151  0.82   -0.99   -45.8  -1.98  0.047      4/15
  OOS   2018-2026   1029  42.8  +0.0593  1.11    0.51   -32.9   1.49  0.137     10/15
  ALL   2006-2026   2483  40.8  +0.0294  1.05    0.25   -49.8   1.13  0.260      9/15

  2 neljast viieaastasest perioodist on NEGATIIVSED.
  VALID 2014-2017 on ainus statistiliselt OLULINE periood — ja ta on
  NEGATIIVNE (p = 0.047). Ukski positiivne periood ei ulata p < 0.05-ni.

===============================================================================
3. PAARID  (D1_MOMENTUM_PAIR_RESULTS.csv), ALL 2006-2026
===============================================================================

  paar        n   wr%    neto_R    PF  Sharpe  maxDD%      t      p    bruto
  GBPJPY    177  48.0  +0.2810  1.54    0.59   -11.2   2.69  0.007  +0.3270
  AUDUSD    149  45.0  +0.1538  1.31    0.33    -8.8   1.46  0.143  +0.1733
  AUDJPY    175  42.3  +0.1293  1.23    0.28   -11.8   1.24  0.213  +0.1702
  EURJPY    183  44.3  +0.1076  1.19    0.24   -19.9   1.09  0.278  +0.1506
  EURCHF    175  45.1  +0.0853  1.15    0.19   -11.9   0.85  0.396  +0.1980
  GBPAUD    159  39.6  +0.0651  1.11    0.13    -7.1   0.59  0.554  +0.1215
  AUDCAD    169  40.2  +0.0445  1.07    0.10   -10.5   0.43  0.667  +0.1045
  EURAUD    153  39.2  +0.0164  1.03    0.03    -9.9   0.16  0.877  +0.0648
  USDCHF    167  41.9  +0.0047  1.01    0.01   -17.3   0.05  0.962  +0.0296
  USDJPY    169  40.8  -0.0314  0.94   -0.07   -21.2  -0.33  0.739  -0.0106
  EURGBP    164  37.2  -0.0446  0.93   -0.10   -22.6  -0.43  0.664  +0.0135
  USDCAD    165  40.0  -0.0582  0.90   -0.14   -19.8  -0.62  0.537  -0.0293
  NZDUSD    156  36.5  -0.0866  0.86   -0.19   -19.7  -0.87  0.382  -0.0607
  EURUSD    161  35.4  -0.1217  0.80   -0.28   -27.4  -1.28  0.199  -0.0999
  GBPUSD    161  34.2  -0.1411  0.78   -0.32   -27.0  -1.47  0.143  -0.1172

  positiivseid 9/15, mediaan +0.0164 R.

  KONTSENTRATSIOON — kogu netokasum 73.0 R:
    GBPJPY  +0.2810 x 177 = +49.7 R  =  68.1% KOGU KASUMIST
    AUDUSD  +0.1538 x 149 = +22.9 R  =  31.4%
    AUDJPY  +0.1293 x 175 = +22.6 R  =  31.0%
    ILMA GBPJPY-ta: kogu valimi ootus +0.0294 -> +0.0101 R (n=2306)
  Uks paar 15-st kannab kaks kolmandikku tulemusest. NEMSIS-i lavi on 30%.

===============================================================================
4. GRUPID  (eelregistreeritud ENNE tulemuste vaatamist)
===============================================================================

  grupp                     n   wr%    neto_R    PF      t      p
  ALL       ALL_2006_2026 2483  40.8  +0.0294  1.05   1.13  0.260
  ALL       OOS_2018_2026 1029  42.8  +0.0593  1.11   1.49  0.137
  MAJORS    ALL_2006_2026 1128  39.1  -0.0417  0.93  -1.13  0.257
  MAJORS    OOS_2018_2026  462  41.8  +0.0085  1.02   0.15  0.884
  CROSSES   ALL_2006_2026 1355  42.1  +0.0886  1.15   2.42  0.016
  CROSSES   OOS_2018_2026  567  43.6  +0.1008  1.18   1.83  0.067
  JPY       ALL_2006_2026  704  43.9  +0.1232  1.22   2.45  0.014
  JPY       OOS_2018_2026  287  47.7  +0.1940  1.38   2.50  0.012
  EUR       ALL_2006_2026  836  40.4  +0.0122  1.02   0.27  0.786
  EUR       OOS_2018_2026  355  42.8  +0.0290  1.05   0.43  0.665
  COMMODITY ALL_2006_2026 1126  40.4  +0.0380  1.07   0.98  0.329
  COMMODITY OOS_2018_2026  478  41.0  +0.0522  1.09   0.88  0.377

  MAJORID (7 koige likviidsemat paari) on NEGATIIVSED.
  Kogu serv elab JPY-ristides. See ei ole hajutatud efekt.

===============================================================================
5. REZHIIMID  (D1_MOMENTUM_REGIME_RESULTS.csv)
===============================================================================

  rezhiim                  n   wr%    neto_R    PF  Sharpe  maxDD%      t      p
  HIGH_VOLATILITY [ALL] 1004  38.5  -0.0249  0.96   -0.14   -47.6  -0.62  0.533
  HIGH_VOLATILITY [OOS]  389  38.8  -0.0596  0.90   -0.34   -28.7  -0.98  0.329
  LOW_VOLATILITY  [ALL] 1462  42.2  +0.0636  1.11    0.41   -23.5   1.85  0.065
  LOW_VOLATILITY  [OOS]  640  45.2  +0.1317  1.24    0.86   -21.4   2.52  0.012
  TRENDING        [ALL] 1065  38.0  -0.0099  0.98   -0.05   -42.8  -0.25  0.805
  TRENDING        [OOS]  379  36.9  -0.0522  0.91   -0.27   -26.5  -0.80  0.423
  RANGING         [ALL]  924  44.0  +0.0995  1.18    0.51   -17.9   2.31  0.021
  RANGING         [OOS]  423  48.9  +0.2014  1.40    1.08   -11.1   3.17  0.002

  STRATEEGIA TOOTAB TAPSELT VASTUPIDI OMA KONSTRUKTSIOONI EELDUSELE.
  MOMENTUM on ehitatud trendi jargimiseks (kontekst EMA50 > EMA200, RSI
  ristub ules) — aga ta on TRENDING-rezhiimis NEGATIIVNE (-0.0099 / -0.0522)
  ja positiivne ainult RANGING-rezhiimis (+0.0995 / +0.2014).
  See ei ole "rezhiimispetsiifiline serv", see on mark sellest, et
  mehhanism, mida strateegia vaidab kasutavat, ei ole see, mis tulemust
  tekitab. Kui MOMENTUM tootaks momentumi tottu, oleks pilt vastupidine.

===============================================================================
6. JUHUSLIK SISENEMINE — KOIGE TAHTSAM TEST
===============================================================================

  Meetod: SAMAD instrumendid, SAMA periood (2006+), SAMA SL (1.5 ATR),
  SAMA TP (2 R), SAMA valjumisreegel (max 20 baari, uks positsioon
  korraga), SAMA kulumudel — kasutatakse TAPSELT sama H.simuleeri koodi.
  AINUS erinevus: sisenemise aeg ja suund on juhuslikud.
  Tehingute arv kalibreeritud: juhuslik keskm 2276 vs tegelik 2483 (0.92x).

  1000 katset:
    juhuslik keskmine      +0.0126 R/tehing
    juhuslik sd             0.0268
    juhuslik 95% kvantiil  +0.0572 R
    juhuslik maksimum      +0.0953 R
    TEGELIK MOMENTUM       +0.0294 R
    ---------------------------------------
    protsentiil            74.0
    empiiriline p          0.26

  => FAIL. Tegelik tulemus on tavaline juhuslik tulemus.

  KORVALLEID, mis on omaette oluline: juhuslik sisenemine annab selle
  valjumisstruktuuriga +0.0126 R/tehing, st POSITIIVSE ootuse. Enamik
  D1 MOMENTUMi "servast" tuleb VALJUMISSTRUKTUURIST (2R eesmark, 20-baariline
  ajaline valjumine) ja valimist, mitte sisenemissignaalist.

===============================================================================
7. KULUSTRESS  (D1_MOMENTUM_COST_STRESS.csv)
===============================================================================

  variant                   loige             n  kulu_R   neto_R    PF      t
  BASE                      ALL_2006_2026  2483  0.0426  +0.0294  1.05   1.13
  BASE                      OOS_2018_2026  1029  0.0426  +0.0593  1.11   1.49
  spread +25%               ALL_2006_2026  2483  0.0515  +0.0204  1.03   0.78
  spread +50%               ALL_2006_2026  2483  0.0605  +0.0114  1.02   0.44
  slippage 2x               ALL_2006_2026  2483  0.0492  +0.0228  1.04   0.87
  spread +50% & slip 2x     ALL_2006_2026  2483  0.0672  +0.0048  1.01   0.18
  spread +50% & slip 2x     OOS_2018_2026  1029  0.0672  +0.0347  1.06   0.87
  spread +100%              ALL_2006_2026  2483  0.0785  -0.0065  0.99  -0.25
  kulu = 0 (ainult bruto)   ALL_2006_2026  2483  0.0000  +0.0720  1.13   2.76

  +50% spread ja 2x libisemine viib kogu valimi ootuse +0.0048 R-ni
  (t = 0.18) — praktiliselt nulli. +100% spread viib NEGATIIVSEKS.
  => FRAGILE. Serv, mis kaob tavalise brokerivahetuse mastaabis
     kuluerinevusega, ei ole kaubeldav serv.

===============================================================================
8. PARAMEETRI PERTURBATSIOON  (+-10%, EI OPTIMEERITUD)
===============================================================================

  parameeter   -10%          baseline      +10%
  EMA_F        +0.0310       +0.0294       +0.0294
  EMA_M        +0.0274       +0.0294       +0.0232
  EMA_S        +0.0296       +0.0294       +0.0274
  RSI_MOM_HI   +0.0360       +0.0294       +0.0017   <- kokkuvarisemine
  RSI_MOM_LO   +0.0136       +0.0294       +0.0257
  SL_ATR       +0.0257       +0.0294       +0.0251
  MAX_HOID     +0.0215       +0.0294       +0.0221
  TP_R         +0.0144       +0.0294       +0.0387
  RSI_N        +0.0365       +0.0294       +0.0317
  ATR_N        +0.0293       +0.0294       +0.0323

  8 parameetrit 10-st on stabiilsed (+0.014 .. +0.039 R vahemikus).
  AGA: RSI_MOM_HI 55 -> 60.5 viib tulemuse +0.0017 R-ni (t = 0.06) ja
  RSI_MOM_LO 45 -> 40.5 viib +0.0136 R-ni. Baseline ei ole terav tipp,
  aga ta ei ole ka lame plato — ja kuna kogu tulemus on niigi juhusliku
  mura sees (p = 0.26), ei ole see test siin otsustav kummaski suunas.
  MARGIME: OSALISELT ROBUSTNE, aga see ei paasta midagi.

===============================================================================
9. WALK-FORWARD  (TRAIN 5 a / TEST 2 a, samm 2 a)
===============================================================================

  Parameetreid EI FITTITUD (neid ei otsitudki). TRAIN-i kasutatakse
  AINUS OTSUSEKS: kaubelda jargmises TEST-aknas ainult neid paare, mille
  TRAIN-i ootus oli positiivne. TEST-i ei kasutata uhekski valikuks.

  train      test       tr_n  tr_ood  te_n   te_ood  te_PF  te_Shrp  te_DD%  val.paare  val_ood
  2006-2010  2011-2012   661 +0.0956   226  +0.0062   1.01    0.05   -18.2       9    +0.0697
  2008-2012  2013-2014   623 +0.0352   223  -0.0594   0.91   -0.49   -21.1       8    -0.1152
  2010-2014  2015-2016   585 +0.0062   237  -0.0995   0.84   -0.88   -24.3       7    -0.0352
  2012-2016  2017-2018   563 -0.0747   235  -0.0159   0.97   -0.14   -17.8       5    -0.0631
  2014-2018  2019-2020   585 -0.0693   239  -0.0130   0.98   -0.11   -25.9       6    +0.0075
  2016-2020  2021-2022   585 -0.0316   217  -0.1046   0.83   -0.87   -29.7       6    -0.2058
  2018-2022  2023-2024   584 -0.0235   251  +0.2782   1.58    2.42    -7.1       7    +0.3584
  2020-2024  2025-2026   579 +0.0818   194  +0.0258   1.05    0.23   -13.3      10    +0.0531

  TEST-aknaid positiivseid: 3/8 (filtrita), 4/8 (TRAIN-i valikuga)
  korr(train_ood, test_ood) = -0.022

  KORRELATSIOON ON NULL. TRAIN-i tulemus ei utle TEST-i tulemuse kohta
  MITTE MIDAGI. Parim TEST-aken (2023-2024 +0.2782) jargneb NEGATIIVSELE
  TRAIN-ile (-0.0235); halvim TEST-aken (2021-2022 -0.1046) jargneb
  samuti negatiivsele TRAIN-ile. => FAIL.

===============================================================================
10. MONTE CARLO  (10 000 simulatsiooni, risk 1% tehingu kohta)
===============================================================================

  (a) JARJEKORRA PERMUTATSIOON (nagu kusitud)
      lopptulemus  mediaan +68.5%   5% +68.5%   1% +68.5%
      maxDD        mediaan -42.2%   95% kvantiil -57.2%
      P(lopptulemus < 0) = 0.0%     P(maxDD > 20%) = 100.0%
      lopptulemuse standardhalve = 3.94e-13

      METOODILINE MARKUS, mida ei varjata: fikseeritud protsendiriski
      juures on lopp-equity prod(1 + risk*R_i) ja KORRUTAMINE ON
      KOMMUTATIIVNE. Lopptulemus on IGAS permutatsioonis TAPSELT SAMA
      (sd = 4e-13 = numbriline mura). Seetottu on selle meetodi
      "5%/1% lopptulemus" ja "P(< 0)" SISUTUD — need ei mota riski,
      vaid kommutatiivsust. Ainult drawdown varieerub sisuliselt.

  (b) BOOTSTRAP TAGASIPANEKUGA (lisatud, et kusimustele saaks vastata)
      lopptulemus  mediaan +69.2%   5% -41.9%   1% -62.9%
      maxDD        mediaan -42.8%   95% kvantiil -66.3%
      P(lopptulemus < 0) = 20.9%    P(maxDD > 20%) = 99.9%

  IGA VIIES MAAILM 20.7 aasta parast on MIINUSES. Mediaan drawdown on
  -42.8% ja 99.9% juhtudest uletab 20% drawdowni — 1% riski juures
  tehingu kohta. 205 EUR kontol tahendab -42% drawdown 118 EUR-i.
  => Monte Carlo EI TOETA kasutamist.

===============================================================================
11. MITME TESTIMISE ARVESTUS
===============================================================================

  testitud:
    15 paari x 8 perioodi              = 120 paar-perioodi lahtrit
    neist n >= 30                      = 114
    rezhiime                           = 4 (x ALL ja OOS = 8 loiget)
    gruppe                             = 6 (x 8 perioodi)
    kulustressi variante               = 7
    parameetriteste                    = 30
    walk-forward aknaid                = 8
    juhuslikke katseid                 = 1000
    Monte Carlo simulatsioone          = 10 000

  BH q=0.05 ule 114 paar-perioodi lahtri: labis 0, NEIST POSITIIVSEID 0
  parim positiivne toores p           = 0.0072 (GBPJPY, ALL)
  Bonferroni lavi 114 testi juures    = 0.00044

  GBPJPY p = 0.0072 EI OLE oluline, kui arvestada, et ta on parim 114-st.
  Uhtegi "statistically significant edge" vaidet ei saa teha.

===============================================================================
12. VASTUSED 12 KUSIMUSELE
===============================================================================

  1. KAS D1 MOMENTUM EDGE ON PARISELT OLEMAS?
     EI. +0.0294 R/tehing (t=1.13, p=0.26) ei ole eristatav juhuslikust
     sisenemisest (+0.0126 R, protsentiil 74, p=0.26).

  2. KUI JAH, SIIS MILLISTEL PAARIDEL?
     Nominaalselt GBPJPY (+0.2810, t=2.69, p=0.0072). Aga see on parim
     114-st lahtrist ja ei labi uhtegi mitme testimise korrektsiooni.
     Ta kannab 68.1% kogu kasumist; temata langeb serv +0.0101 R-ni.

  3. KAS EDGE PUSIB ERINEVATEL AJAPERIOODIDEL?
     EI. 2/4 viieaastasest perioodist on negatiivsed (2011-2015 -0.0414,
     2016-2020 -0.0316). Ainus oluline periood on VALID 2014-2017 ja ta
     on NEGATIIVNE (p = 0.047).

  4. KAS EDGE PUSIB OOS-IS?
     Nominaalselt jah (+0.0593, t=1.49), aga p = 0.137 — ebaoluline.
     Ja OOS-ile eelnev VALID oli oluliselt negatiivne, seega jarjepidevust
     ei ole.

  5. KAS EDGE ERINEB RANDOM ENTRY'ST?
     EI. protsentiil 74.0, empiiriline p = 0.26. See on TESTI POHITULEMUS.

  6. KAS EDGE PUSIB +50% SPREADI JA 2x SLIPPAGE JUURES?
     Vaevu: +0.0048 R (t = 0.18) kogu valimil. +100% spreadi juures
     NEGATIIVNE. FRAGILE.

  7. KAS EDGE ON PARAMEETRI SUHTES ROBUSTNE?
     OSALISELT. 8/10 parameetrit annavad +-10% juures sarnase tulemuse,
     aga RSI_MOM_HI +10% viib tulemuse nulli (+0.0017). Kuna baseline ise
     ei ole oluline, ei paasta see test midagi.

  8. KAS EDGE ON REGIME-SPETSIIFILINE?
     JAH, aga VALES SUUNAS. Positiivne ainult RANGING (+0.0995 / OOS
     +0.2014) ja LOW_VOL (+0.0636) rezhiimis; NEGATIIVNE TRENDING
     (-0.0099) ja HIGH_VOL (-0.0249) rezhiimis. Trendijargimise strateegia,
     mis kaotab trendis ja voidab vahemikus, ei toota vaidetud mehhanismi
     kaudu.

  9. KAS EDGE ON PAARISPETSIIFILINE?
     Nailiselt jah (JPY-ristid +0.1232, majorid -0.0417), aga see on
     seesama kontsentratsiooniprobleem: GBPJPY uksi on 68.1%. "Paarispetsii-
     filisus" ja "uks paar kannab koike" on siin sama nahtus.

 10. KAS MONTE CARLO TOETAB KASUTAMIST?
     EI. Bootstrap: P(lopptulemus < 0) = 20.9%, 5% kvantiil -41.9%,
     mediaan maxDD -42.8%, P(maxDD > 20%) = 99.9% 1% riski juures.

 11. MIS ON KOIGE TUGEVAM KANDIDAAT JARGMISSE ETAPPI?
     Mitte D1 MOMENTUM. Ainus asi, mis sellest tood vaarib jargmist
     sammu, on KORVALLEID: juhuslik sisenemine annab selle
     valjumisstruktuuriga +0.0126 R/tehing. See tahendab, et
     2R-eesmargi + 20-baarilise ajalise valjumise kombinatsioon on
     nendel paaridel sel perioodil iseenesest positiivse ootusega.
     Kui midagi uurida, siis VALJUMISSTRUKTUURI, mitte sisenemist.
     AGA: ka see +0.0126 on kulude sees ja 1 sd on 0.0268, seega ka see
     ei ole toestatud — see on hupotees, mitte leid.

 12. KAS NEMSIS PEAKS D1 MOMENTUMIGA EDASI MINEMA VOI SELLE MAHA MATMA?
     MAHA MATMA. Seitse kaheksast eelregistreeritud FAIL-tingimusest on
     taidetud. Edasiminek tahendaks parameetrite otsimist, mis on
     tapselt see, mida keelati — ja mis annaks paremaid numbreid ilma
     paremat serva andmata.

===============================================================================
13. FAIL-TINGIMUSTE KONTROLL
===============================================================================

  tingimus                                              taidetud?  toend
  ---------                                             ---------  -----
  edge eksisteerib ainult uhes vaikses alamvalimis      JAH        JPY-ristid /
                                                                   RANGING
  random benchmark on sama hea                          JAH        p = 0.26
  walk-forward laguneb                                  JAH        3/8, korr -0.02
  parameetri vaike muutmine havitab tulemuse            OSALISELT  RSI_MOM_HI
  VALID/OOS ei pusi                                     JAH        VALID p=0.047 neg
  costs havitavad edge'i                                JAH        +100% => neg
  tulemuse taga on ainult uks paar                      JAH        GBPJPY 68.1%
  Monte Carlo naitab korget negatiivse tulemuse tn      JAH        20.9%

  7 taielikult + 1 osaliselt = 8/8.

===============================================================================
14. FAILID JA REPRODUTSEERITAVUS
===============================================================================

  D1_MOMENTUM_VALIDATION_REPORT.md        see raport
  D1_MOMENTUM_PERIOD_RESULTS.csv          8 perioodi
  D1_MOMENTUM_PAIR_RESULTS.csv            15 paari x 8 perioodi = 120 rida
  D1_MOMENTUM_GROUP_RESULTS.csv           6 gruppi x 8 perioodi
  D1_MOMENTUM_REGIME_RESULTS.csv          4 rezhiimi, koond + paaride kaupa
  D1_MOMENTUM_RANDOM_BENCHMARK.csv        1000 juhuslikku katset
  D1_MOMENTUM_COST_STRESS.csv             7 varianti x 2 loiget
  D1_MOMENTUM_PARAMETER_ROBUSTNESS.csv    10 parameetrit x 3 varianti
  D1_MOMENTUM_WALK_FORWARD.csv            8 akent
  D1_MOMENTUM_MONTE_CARLO.csv             10 000 simulatsiooni x 2 meetodit

  kood: bot/d1_momentum_validation.py (impordib hm_engine.py-st)
  jooksutamine: python3 bot/d1_momentum_validation.py
  juhuslikkus: RandomState(20260915) koigis testides => korratav.

  LIVE PUUTUMATA — kontrollitud enne ja parast:
    git diff HEAD -- main_v4.py config.py mt5_connector.py
                     strategy_meanrev.py backtest.py   =>   TUHI
===============================================================================
```
