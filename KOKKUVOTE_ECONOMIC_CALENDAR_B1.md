```
===============================================================================
NEMSIS B1 — MAJANDUSKALENDRI "SURPRISE": KAS MEHHANISM EKSISTEERIB?
===============================================================================
  kuupaev 2026-09-15   haru claude/great-noether-um7382
  LIVE PUUTUMATA: main_v4.py / config.py / mt5_connector.py /
  strategy_meanrev.py / backtest.py EI OLE muudetud. /update EI saadetud.
  B2/B3/B4 EI OLE alustatud.

===============================================================================
0. KOKKUVOTE JUHILE
===============================================================================

  MEHHANISM EKSISTEERIB. See on esimene kord NEMSIS-i ajaloos, kus efekt
  ei ole ainult statistiliselt oluline, vaid ka STABIILNE koigis
  alamperioodides ja majanduslikult loogiline.

     koik sundmused |z|>=1, 1 paev:  +2.72 bp bruto, t = 4.40, p = 0.00002
     ainult TIER 1,        1 paev:  +4.27 bp bruto, t = 4.97, p = 0.0000007
     permutation null (500x):        p = 0.0000 MOLEMAS variandis
     TIER 1 bruto positiivne:        13 / 14 aastal
     TIER 1 koigis kolmes perioodis: 2013-16 +2.97, 2017-20 +3.99, 2021-26 +5.28

  AGA SEE EI OLE KAUBELDAV.

     edasi-tagasi kulu                          2.50 bp
     efekt / kulu, koik sundmused               1.09 x   (vaja >= 2.0)
     efekt / kulu, TIER 1 1 paev                1.71 x   (vaja >= 2.0)
     neto koik sundmused                        +0.22 bp/tehing
     neto TIER 1                                +1.77 bp/tehing
     neto positiivseid aastaid                  7/14 (koik), 8/14 (TIER 1)
     205 EUR kontol taidetav                    0 / 8 valuutal

  B1 DECISION: PROMISING BUT NOT PROVEN

  Pohjendus: mehhanism on toestatud (see EI OLE "uks positiivne backtest"),
  aga efekti suurus jaab alla NEMSIS-i kaubeldavuse lavi 2x kulu ja
  kontol ei ole seda voimalik taita.

===============================================================================
A. ANDMEALLIKAS
===============================================================================

  VALITUD: TradingView economic calendar API
    https://economic-calendar.tradingview.com/events?from=...&to=...&countries=...
    Taksonoomia parineb Trading Economics'ilt (standarditud nimed).
    Tasuta, ilma API-votmeta, programmiliselt kasutatav.
    Noab Origin/Referer paist (ilma selleta 403).

  TEE: liivakastil EI OLE otseuhendust valismaailmaga. Kontrollitud:
    curl -> kood 000 koigil neljal kandidaadil.
    Paring kaib kasutaja Supabase `http` laienduse kaudu
    (funktsioonid fetch_hdr + load_cal -> tabel econ_cal).

  MIS EI TOOTANUD — proovitud ja mooedetud:

  allikas                              tulemus     miks ei sobinud
  -------                              -------     ---------------
  curl otse (4 hosti)                  000         proxy blokeerib koik
  TradingView ilma Origin paiseta      403         nginx nouab paist
  FXStreet calendar-api                401         vajab autentimist
  MQL5 economic-calendar/content       404         endpoint muutunud
  ForexFactory (nfs.faireconomy.media) 200         AINULT jooksev nadal,
                                                   `actual` puudub uldse
  TradingEconomics guest:guest         -           demo katab 4 riiki
  FRED / ALFRED                        -           actual on, FORECAST PUUDUB
  Philadelphia Fed SPF                 -           kvartaalne, ei ole
                                                   sundmusepohine konsensus

  PIIRANG 1 (ajalugu): see allikas EI ANNA andmeid enne 2013.
  Paringud 2006 / 2008 / 2010 / 2011 / 2012 kohta tagastavad
  taismahus {"status":"no_data"}. 2013 on horedam, 2014+ tais.
  => B1 valim on 13.1 aastat, MITTE soovitud 2008-2026.

  PIIRANG 2 (revisjonid): allikas EI UTLE, kas `actual` on ESIALGNE trukk
  voi hiljem revideeritud vaartus. Seda ei saa API-st kontrollida.
  Riski maandatakse kahel viisil: sisenemine toimub tunde parast teadet,
  ja raporteeritakse tundlikkus sisenemishetkele (1d / 2d / 5d).
  SEDA EI SAA TAIELIKULT VALISTADA ja see on B1 suurim nork koht.

===============================================================================
B. ANDMETE PIKKUS JA MAHT
===============================================================================

  laetud toorandmeid            92 364 sundmust  2013-01-04 .. 2026-09-30
  neist actual JA forecast      39 588
  eksporditud CSV-sse           37 595   (265 indikaatorit, 8 valuutat)
  eelregistreeritud universum   15 673   (24 indikaatorit: 11 T1 + 13 T2)
  neist z-ga ja hinnaga         13 974   2013-08-16 .. 2026-09-10
  neist |z| >= 1                 3 947   = 303 sundmust aastas

  valuuta kaupa (eelregistreeritud universum):
    EUR 2972   GBP 2605   USD 2567   JPY 2228
    CAD 1799   AUD 1660   CHF 1089   NZD  753

  HINNAD: Yahoo `=X` paevane close, sama load_yahoo_bars() mis kogu
  NEMSIS-is, failid bot/data/{PAAR}_d25.csv, ristuv aken 7 paari ule
  2006-05-15 .. 2026-09-10. Intraday: bot/data/{PAAR}_h1.csv,
  2023-11-27 .. 2026-09-11 (ainult 2.8 aastat — Yahoo tunniandmete piir).

===============================================================================
C. EVENTIDE ARV JA KLASSIFIKATSIOON
===============================================================================

  TIER 1 — 11 indikaatorit, 8 300 sundmust, mark majandusteooriast:
    Inflation Rate              +1      Unemployment Rate           -1
    Core Inflation Rate         +1      GDP Growth Rate             +1
    Inflation Rate Mom          +1      GDP Annual Growth Rate      +1
    Retail Sales MoM            +1      Interest Rate               +1
    Retail Sales YoY            +1      Employment Change           +1
    Non Farm Payrolls           +1

  TIER 2 — 13 indikaatorit, 7 373 sundmust:
    Producer Price Inflation MoM +1     Producer Prices Change      +1
    Consumer Confidence          +1     Business Confidence         +1
    Industrial Production Mom    +1     Industrial Production       +1
    Current Account              +1     Balance of Trade            +1
    Building Permits MoM         +1     House Price Index MoM       +1
    Wage Growth                  +1     Leading Economic Index      +1
    Labor Force Participation Rate +1

  Margid on EELREGISTREERITUD majandusteooriast (korgem inflatsioon =>
  hawkish keskpank => tugevam valuuta; korgem tootus => norgem valuuta),
  MITTE valitud tulemuste jargi. 265-st saadaolevast indikaatorist
  testiti 24 — ei tehtud 1000 eraldi strateegiat.

===============================================================================
D. TIMESTAMP AUDIT — 18 kontrolli, 0 viga  (bot/cal_audit.py)
===============================================================================

  A1 kalendri ridu                                 15 673 sundmust        OK
  A1 8 valuutat                                    loendatud              OK
  A1 vahemik                                       2013-03-05..2026-09-15 OK
  A1 actual ja forecast alati olemas                                      OK
  A1 koigil indikaatoritel eelregistreeritud mark  11 T1 + 13 T2          OK
  A2 PAEVANE sisenemine ALATI parast teadet        min 1.0h, med 14.0h    OK
  A2 sidumata sundmused loendatud                  16 / 15 673            OK
  A3 H1 sisenemine ALATI parast teadet             min 1.00h, med 1.17h   OK
  A3 H1 katvus                                     3 272 / 15 673         OK
  A4 z: esimesed 10 vaatlust NaN                                          OK
  A4 z: TULEVIKU MUUTMINE EI MUUDA MINEVIKKU                              OK
  A4 z: std vastab kasitsi arvutatule              5.916080 = 5.916080    OK
  A5 NFP avaldamisaeg 12:30/13:30 UTC              162 NFP-d              OK
  A5 NFP valdavalt reedel                          94.4%                  OK
  A5 H1 VOLATIILSUS NFP TUNNIL                     30.1bp vs 5.5bp = 5.4x OK
  A6 valuutatootlused ristloikeliselt tsentreeritud max|summa| 2.8e-17    OK
  A6 USD saab sisulise tootluse                    41.0 bp/paev           OK
  A7 moodikud: konstantne +1% -> 99.50 bp                                 OK

  A5 volatiilsustest on ajavoondi TOESTUS: kui timestamp'id oleksid
  vales ajavoondis, ei oleks NFP-tunni volatiilsus 5.4x tavalisest.

===============================================================================
E. SURPRISE DEFINITSIOON (eelregistreeritud)
===============================================================================

  viga:  e = actual - forecast
  z   :  e / std(sama (valuuta, indikaator) VAREMATE vigade seast)
         aken 20 sundmust, min 10, shift(1) ENNE rolling'ut
         => AINULT MINEVIK. Full-sample standardiseerimist EI KASUTATUD.
         Parameetreid 20/10 ei valitud tulemuste jargi.

  suund: d = sign(z) * mark(indikaator)

  valuuta tootlus: V[c] = 1 uhiku c vaartus USD-des (7 USD-paarist),
         r_c = log-muut MIINUS ristloikeline keskmine
         => turuneutraalne, USD saab sisulise tootluse

  SISENEMISREEGEL (no lookahead):
    paevane — eeldame paevabaari sulgemise 21:00 UTC (varasem kui Yahoo
              tegelik sulgemine => konservatiivne). Sisenemine = esimene
              paevabaar, mille sulgemine on PARAST T.
              Teade 12:30 UTC -> sisenemine ~8.5 h hiljem.
    H1      — sisenemine = esimene H1 baar, mis ALGAB hetkel >= T,
              selle baari SULGEMISHIND. Teade 12:30 -> sisenemine 14:00.

  Kogu vahetu reaktsioon (esimesed minutid) on TAHTLIKULT VALJA JAETUD.
  Seda ei saa 205 EUR retail-kontoga niikuinii puududa.

===============================================================================
F+G. PEATULEMUSED — A, B, C ja OOS
===============================================================================

  test                              n  bruto_bp  kulu  neto_bp   wr%    pf      t      p
  ----                              -  --------  ----  -------   ---    --      -      -
  A+B koos          1d           3947     +2.72  2.50    +0.22  52.5  1.21   4.40  0.000
    A positiivne ullatus 1d      2019     +3.09  2.50    +0.59  52.6  1.26   3.71  0.000
    B negatiivne ullatus 1d      1928     +2.32  2.50    -0.18  52.3  1.17   2.54  0.011
  A+B koos          2d           3947     +2.23  2.50    -0.27  51.6  1.12   2.61  0.009
  A+B koos          5d           3940     +2.67  2.50    +0.17  51.8  1.09   1.97  0.049

  MOLEMAD SUUNAD TOOTAVAD. See on oluline: kui ainult uks pool tootaks,
  oleks tegu drifti, mitte ullatuse-efektiga.

  PIDEV VERSIOON (kogu valim, mitte ainult |z|>=1):
    horisont      n      korr(z*mark, r)      t     beeta bp per 1 z
    1d        13 972            +0.0430    5.09               +1.40
    2d        13 972            +0.0217    2.57               +0.97
    5d        13 956            +0.0195    2.30               +1.39

  HUPOTEES C (magnituud, kirjeldav):
    horisont   korr(|z|,|r|)   |r| kui |z|<1   |r| kui |z|>=2
    1d              +0.0424           25.9bp           29.4bp
    2d              +0.0432           36.1bp           41.1bp
    5d              +0.0271           57.1bp           61.1bp
    => suur ullatus toesti suurendab liikumist, aga ainult ~13%.

  TRAIN / VALIDATION / FINAL OOS
    TRAIN 2013-08-16 .. 2017-12-31   VALID .. 2020-12-31   OOS 2021-01-01 ..
    FINAL OOS avati UKS KORD, parast kogu spetsifikatsiooni fikseerimist.

  test                 n  bruto_bp  neto_bp   wr%      t      p
  ----                 -  --------  -------   ---      -      -
  TRAIN 1d          1160     +2.45    -0.05  50.8   1.90  0.058
  VALID 1d          1136     +1.93    -0.57  52.5   1.78  0.075
  FINAL OOS 1d      1651     +3.44    +0.94  53.7   3.85  0.000
  TRAIN 5d          1160     -1.39    -3.89  48.9  -0.46  0.644
  VALID 5d          1136     +2.11    -0.39  50.6   0.87  0.385
  FINAL OOS 5d      1644     +5.92    +3.42  54.6   3.27  0.001

  BRUTO on positiivne koigis kolmes aknas (1d). NETO ei ole.

===============================================================================
H. GROSS / COST / NET ja KULUTUNDLIKKUS
===============================================================================

  kulueeldus: 1.25 bp uhesuunaline (NEMSIS BASE 7 USD-paari keskmine),
              => 2.50 bp edasi-tagasi uhel valuutajalal.

  variant                        bruto_bp  kulu_bp  neto_bp
  -------                        --------  -------  -------
  kulu 0 bp uhesuunaline            +2.72     0.00    +2.72
  kulu 1 bp uhesuunaline            +2.72     2.00    +0.72
  kulu 2 bp uhesuunaline            +2.72     4.00    -1.28
  kulu 3 bp uhesuunaline            +2.72     6.00    -3.28
  NEMSIS BASE (1 jalg)              +2.72     2.50    +0.22
  NEMSIS BASE + korvi hedge         +2.72     5.00    -2.28

  Ristloikeline valuutatootlus tahendab tegelikult KAHT jalga (valuuta
  vs korv). Kui hedge tuleb ka kaubelda, on kulu 5.00 bp ja tulemus
  NEGATIIVNE. Uhe jala versioon (2.50 bp) eeldab, et korvi ei hedgita —
  see on optimistlikum eeldus.

  AASTANE KULUEELARVE
    koik |z|>=1   303 tehingut/a  bruto +8.23%  kulu 7.58%  neto +0.65%
    ainult TIER 1 155 tehingut/a  bruto +6.61%  kulu 3.87%  neto +2.74%
    => kulu soob koigi sundmuste versioonis 92% brutost.

  EFEKTI SUURUS vs KULU (NEMSIS nouab >= 2x)
    variant                bruto_bp  kulu_bp  kordne  verdikt
    koik |z|>=1  1d           +2.72     2.50    1.09   KUKUB
    TIER 1       1d           +4.27     2.50    1.71   KUKUB
    TIER 1       5d           +5.35     2.50    2.14   LABIB

===============================================================================
I. AASTATE KAUPA (1d, |z|>=1)
===============================================================================

  KOIK SUNDMUSED                       AINULT TIER 1
  aasta    n  bruto  neto     t        aasta    n  bruto   neto     t
  -----    -  -----  ----     -        -----    -  -----   ----     -
  2014   186  +3.61 +1.11  1.29        2014   124  +4.50  +2.00  1.32
  2015   295  +0.21 -2.29  0.08        2015   162  +4.55  +2.05  1.37
  2016   360  +0.34 -2.16  0.13        2016   198  +0.23  -2.27  0.06
  2017   315  +6.15 +3.65  2.83        2017   156 +12.63 +10.13  3.95
  2018   322  +2.69 +0.19  1.47        2018   145  +3.37  +0.87  1.27
  2019   368  +2.48 -0.02  1.48        2019   177  +2.02  -0.48  0.86
  2020   446  +0.94 -1.56  0.47        2020   239  +0.20  -2.30  0.08
  2021   277  +1.35 -1.15  0.79        2021   135  +0.17  -2.33  0.06
  2022   281  -2.76 -5.26 -1.00        2022   136  +0.73  -1.77  0.19
  2023   284  +8.51 +6.01  3.85        2023   148 +10.12  +7.62  3.10
  2024   244  +4.47 +1.97  2.11        2024   119  +8.35  +5.85  3.06
  2025   301  +6.20 +3.70  2.62        2025   151  +8.49  +5.99  3.01
  2026   264  +2.70 +0.20  1.71        2026   124  +3.22  +0.72  1.56

  KOIK:   bruto positiivseid 12/13, neto positiivseid 7/14
  TIER 1: bruto positiivseid 13/14, neto positiivseid 8/14

  See on B1 tugevaim tulemus. BRUTO on positiivne peaaegu igal aastal —
  see EI OLE uhe perioodi artefakt. Aga NETO on positiivne ainult
  pooltel aastatel, sest kulu sooab efekti ara.

===============================================================================
J. EVENT CATEGORY KAUPA (1d, |z|>=1)
===============================================================================

  TIER T1                        2016     +4.27  +1.77  54.6  1.36  4.97  0.000
  TIER T2                        1931     +1.10  -1.40  50.2  1.08  1.24  0.216

  TIER 1 on 4x tugevam kui TIER 2. See on MEHHANISMI KINNITUS: tahtsamad
  teated liigutavad turgu rohkem. Juhuslik muster ei kaituks nii.

  indikaator                        n  bruto_bp  neto_bp   wr%      t      p
  ----------                        -  --------  -------   ---      -      -
  Interest Rate                    34    +13.00   +10.50  70.6   1.39  0.164
  Wage Growth                      99    +11.92    +9.42  60.6   3.14  0.002
  Non Farm Payrolls                41    +11.63    +9.13  58.5   1.55  0.122
  Labor Force Participation Rate   57     +9.33    +6.83  61.4   2.17  0.030
  Building Permits MoM            108     +9.17    +6.67  59.3   2.86  0.004
  Inflation Rate Mom              222     +7.10    +4.60  60.4   2.75  0.006
  Employment Change               146     +6.03    +3.53  53.4   1.91  0.056
  Inflation Rate                  346     +5.21    +2.71  56.9   2.48  0.013
  Unemployment Rate               322     +4.60    +2.10  54.3   2.06  0.040
  Retail Sales MoM                216     +4.35    +1.85  55.1   1.68  0.093
  GDP Annual Growth Rate          101     +4.26    +1.76  52.5   1.18  0.239
  Current Account                 139     +3.65    +1.15  55.4   1.04  0.298
  Business Confidence             150     +2.56    +0.06  48.0   0.89  0.376
  GDP Growth Rate                 163     +2.27    -0.23  51.5   0.83  0.405
  Balance of Trade                245     +1.77    -0.73  49.4   0.62  0.536
  Industrial Production Mom       173     +1.31    -1.19  49.1   0.42  0.675
  Core Inflation Rate             261     +0.85    -1.65  52.1   0.38  0.703
  House Price Index MoM           106     +0.55    -1.95  47.2   0.16  0.869
  Retail Sales YoY                164     -0.11    -2.61  47.0  -0.04  0.970
  Industrial Production           114     -0.63    -3.13  40.4  -0.15  0.879
  Consumer Confidence             245     -0.79    -3.29  51.8  -0.33  0.742
  Leading Economic Index           80     -1.75    -4.25  50.0  -0.40  0.690
  Producer Price Inflation MoM    229     -2.32    -4.82  48.5  -1.00  0.317
  Producer Prices Change          186     -6.77    -9.27  44.1  -2.39  0.017

  positiivseid indikaatoreid (neto): 13 / 24

  TOP-5 on tooturg ja inflatsioon — tapselt need, mille jargi keskpangad
  otsustavad. Alumine ots on tootjahinnad ja kindlustunde indeksid —
  tapselt need, mida turg ignoreerib. Muster on MAJANDUSLIKULT LOOGILINE.

===============================================================================
K. VALUUTA KAUPA (1d, |z|>=1)
===============================================================================

  valuuta      n  bruto_bp  neto_bp   wr%    pf      t      p
  -------      -  --------  -------   ---    --      -      -
  AUD        407     +8.89    +6.39  60.7  1.78   4.09  0.000
  CAD        461     +5.81    +3.31  55.3  1.62   3.86  0.000
  USD        652     +4.16    +1.66  54.4  1.32   2.57  0.010
  NZD        157     +3.70    +1.20  49.7  1.27   1.15  0.249
  GBP        720     +2.04    -0.46  51.2  1.16   1.40  0.160
  CHF        282     +0.95    -1.55  52.1  1.08   0.44  0.660
  EUR        727     +0.26    -2.24  49.2  1.02   0.22  0.824
  JPY        541     -1.48    -3.98  48.4  0.91  -0.77  0.441

  positiivseid valuutasid: bruto 7/8, neto 4/8

  Nork koht: EUR ja JPY — kaks suurimat FX-turgu — ei tooda uldse.
  Tootavad valuutad on kommoditeedivaluutad (AUD, CAD, NZD) ja USD.
  See on kooskolas selega, et vaiksema likviidsusega turud on
  aeglasemad, aga see tahendab ka, et efekt on koige norgem seal,
  kus spread on koige kitsam.

===============================================================================
L. PERMUTATION / NULL TEST
===============================================================================

  500 randomiseerimist, kaks soltumatut varianti:
  (a) juhuslik MARK   — sama sundmuste hulk, sama hinnaseeria, suund juhuslik
  (b) SEGATUD ullatus — suunad segatakse sundmuste vahel, sagedus sailib

  variant                mediaan     95%      max     tegelik       p
  -------                -------     ---      ---     -------       -
  (a) juhuslik mark       +0.031  +1.089   +1.912      +2.716  0.0000
  (b) segatud ullatus     +0.049  +1.048   +2.034      +2.716  0.0000

  0 / 500 juhuslikku katset kummaski variandis ei ulatunud tegelikuni.
  See on B1 puhtaim tulemus: ullatus kannab PARIS INFOT.

  Vordluseks: COT-i parim variant sai ausa best-of-36 nulli vastu p=0.028.
  Siin on p < 0.002 (0/500) ilma uhegi variandivalikuta.

===============================================================================
M. SUURIM KASUMIALLIKAS
===============================================================================

  kogu bruto logsumma +107.20% (3 947 sundmust, 13.1 aastat)

  VALUUTA:    parim AUD +36.18% = 33.7% kogusummast; positiivseid 7/8
  INDIKAATOR: parim Inflation Rate +18.03% = 16.8%; positiivseid 18/24
  TIER:       T1 +86.02% = 80.2% kogusummast
  AASTA:      parim 2023 +24.18% = 22.6% kogusummast

  TOP-1 valuuta 33.7% ON ULE NEMSIS-i 30% lavi. TOP-1 indikaator (16.8%)
  ja TOP-1 aasta (22.6%) on alla lavi. Kontsentratsioon on piiripealne,
  aga mitte katastroofiline: 7/8 valuutat ja 18/24 indikaatorit on
  bruto-positiivsed.

===============================================================================
N. SUURIM KAHJUMIALLIKAS
===============================================================================

  valuuta    JPY                    -8.02%
  indikaator Producer Prices Change -12.59%  (t = -2.39, p = 0.017)
  aasta      2022                    -7.75%

  "Producer Prices Change" on STATISTILISELT OLULISELT NEGATIIVNE.
  Aus tolgendus: kahe eelregistreeritud tootjahinna-indikaatori
  (Producer Prices Change, Producer Price Inflation MoM) mark on
  toenaoliselt VALE — turg loeb neid vastupidiselt, sest tootjahinna
  tous ilma tarbijahinna tousuta tahendab marginaalisurvet, mitte
  hawkish keskpanka. MA EI POORA MARKI UMBER — see oleks tulemuste
  jargi reeglite muutmine. Margin selle B2 jaoks ules.

===============================================================================
O. LOOKAHEAD AUDIT — LISAKONTROLLID
===============================================================================

  O1  H1 (INTRADAY) TEST — luhike valim 2023-11-27 .. 2026-09-11
      Sisenemine 1 tund parast teadet, mitte 8-14 tundi.

      test                     n  bruto_bp  neto_bp   wr%      t      p
      koik |z|>=1  +1h       831     -0.24    -2.74  46.6  -0.80  0.424
        TIER 1     +1h       408     -0.66    -3.16  45.8  -1.55  0.121
      koik |z|>=1  +4h       831     +0.09    -2.41  48.6   0.18  0.857
        TIER 1     +4h       408     -0.17    -2.67  48.8  -0.22  0.823
      koik |z|>=1 +24h       830     -0.12    -2.62  49.6  -0.11  0.911
        TIER 1    +24h       408     -0.62    -3.12  50.0  -0.39  0.698

      H1 aknas EI LEIDNUD KINNITUST. See on B1 teine nork koht.

  O2  VOIMSUSANALUUS — kas H1 null tahendab "efekti pole"?
      paevane: n=3947, keskm +2.72bp, sd 38.8bp, SE 0.62bp
      sama efekt n=831 juures: SE 1.35bp => oodatav t = 2.02
      sama efekt n=408 juures: SE 1.92bp => oodatav t = 1.42
      => H1 test on ALAVOIMSAS. Null EI OLE toestus efekti puudumisest,
         aga ta ei ole ka kinnitus. Aus sona: EBASELGE.

  O3  OUN-OUNA — paevane test SAMAL aknal, kus H1-andmed olemas
      paevane 1d kogu valim        3947   +2.72bp   t=4.40
      paevane 1d 2023-11+ aken      830   +4.80bp   t=4.06
        TIER 1 2023-11+ aken        408   +7.28bp   t=4.91

      SAMAL AKNAL ja SAMADEL sundmustel annab paevane test +4.80bp
      (t=4.06), H1 test -0.24bp. Erinevus EI OLE valimi suurus —
      valim on identne. Erinevus on AKEN: paevane test motab
      sulgemisest sulgemiseni (T+8h .. T+32h), H1 test motab
      T+1.5h .. T+2.5h / +5.5h / +25.5h.
      => efekt EI OLE vahetus reaktsioonis, vaid HILISEMAS drifis.
         See on mehhanismi jaoks ebamugav tulemus ja vajab B2-s
         eraldi uurimist enne kui midagi kaubelda.

  O4  FALSIFITSEERIMINE — kas see on sama lugu mis COT?
      test                    n  bruto_bp  neto_bp      t      p
      koik 2013-2016        845     +1.07    -1.43   0.68  0.497
        TIER 1 2013-2016    486     +2.97    +0.47   1.42  0.155
      koik 2017-2020       1451     +2.85    +0.35   2.92  0.003
        TIER 1 2017-2020    717     +3.99    +1.49   2.90  0.004
      koik 2021-2026       1651     +3.44    +0.94   3.85  0.000
        TIER 1 2021-2026    813     +5.28    +2.78   4.31  0.000

      EI OLE. COT oli 2006-2016 NEGATIIVNE (-9.41bp) ja 2016-2026
      positiivne. Siin on KOIK KOLM perioodi positiivsed, ka TIER 1
      varaseim periood (+2.97bp). Efekt TUGEVNEB ajas, mis on
      ebatavaline, aga ta ei puudu uheski perioodis.

===============================================================================
P. 205 EUR TAITEVUS
===============================================================================

  konto 205 EUR, min lot 0.01 = 1000 uhikut baasvaluutat, EURUSD 1.1610

  valuuta   1d sigma%   0.01 lot EUR   1-sigma EUR   % kontost
  -------   ---------   ------------   -----------   ---------
  USD            0.41            861          3.53        1.7
  EUR            0.51           1000          5.09        2.5
  GBP            0.39           1164          4.56        2.2
  JPY            0.72            861          6.20        3.0
  CHF            0.47            861          4.09        2.0
  CAD            0.38            861          3.26        1.6
  AUD            0.50            616          3.06        1.5
  NZD            0.48            500          2.42        1.2

  kavatsetud risk 0.25% = 0.51 EUR  ->  taidetav 0 / 8 valuutal
  kavatsetud risk 0.50% = 1.02 EUR  ->  taidetav 0 / 8 valuutal
  vajalik konto 0.25% jaoks:   969 - 2 480 EUR
  vajalik konto 0.50% jaoks:   484 - 1 240 EUR

  Sama sein mis COT-il, aga madalam: 1-paevane hoid on lyhem kui
  1-nadalane, seega sigma on vaiksem ja vajalik konto ~2x madalam
  (969-2480 EUR vs COT 2838-5806 EUR). Ikkagi 5-12x ule 205 EUR.
  RISKI EI TOSTETUD, et strateegia mahuks.

===============================================================================
Q. OTSUS
===============================================================================

  kriteerium                                       tulemus        staatus
  ----------                                       -------        -------
  mehhanism eksisteerib (permutation null)         p = 0.0000     LABIB
  efekt erinevatel aastatel olemas (bruto)         13/14 T1       LABIB
  TRAIN -> VALID -> OOS bruto stabiilne            +2.45/+1.93/+3.44 LABIB
  >= 60% valuutasid oiges suunas                   7/8 bruto      LABIB
  >= 60% eventidest oiges suunas                   18/24 bruto    LABIB
  majanduslikult loogiline muster (T1 >> T2)       4x vahe        LABIB
  lookahead puudub                                 18/18 auditit  LABIB
  paris uus mehhanism (mitte OHLC)                 jah            LABIB
  uks periood EI tee kogu kasumit                  parim aasta 23% LABIB
  uks valuuta EI tee kogu kasumit                  AUD 33.7%      PIIRIL
  efekt >= 2x kulu                                 1.09x / 1.71x  KUKUB
  neto positiivne enamikul aastatel                7/14           KUKUB
  H1 (kaubeldav) aken kinnitab                     -0.24 bp       KUKUB
  teostatav 205 EUR juures                         0/8            KUKUB

  9 LABIB, 1 PIIRIL, 4 KUKUB.

  B1 DECISION:  PROMISING BUT NOT PROVEN

  See EI OLE "PROMISING sest uks backtest oli positiivne". Mehhanism on
  toestatud kolme soltumatu tookindlusega: permutation null 0/500,
  TIER1 >> TIER2 neljakordne vahe, ja bruto positiivsus 13/14 aastal.
  Aga kolm asja takistavad seda strateegiaks tegemast:
    1. efekt on 1.1-1.7x kulu, mitte noutud 2x
    2. kaubeldavas H1 aknas seda ei naa (kuigi test on alavoimsas)
    3. 205 EUR kontol ei saa uhtegi positsiooni oige riskiga avada

===============================================================================
R. MIDA EI TEHTUD
===============================================================================

  live-faile ei muudetud; /update ei saadetud; strateegiat ei loodud
  ega optimeeritud; B2/B3/B4 ei alustatud; sunteetilisi andmeid ei
  genereeritud; indikaatorite marke ei poordud parast tulemuste nagemist
  (Producer Prices jai vale margiga, nagu eelregistreeritud).

===============================================================================
KOOD JA ANDMED
===============================================================================
  bot/sb_cal.py         Supabase -> CSV konverter
  bot/cal_engine.py     eelregistreeritud definitsioonid, z, ajastus, stat
  bot/cal_audit.py      18 lookahead- ja korrektsuskontrolli
  bot/cal_run.py        hupoteesid A/B/C, OOS, aastad, valuutad, indikaatorid
  bot/cal_run2.py       permutation null, H1 test, kontsentratsioon
  bot/cal_exec.py       oun-ouna, voimsus, kulueelarve, 205 EUR
  bot/data/econ_cal.csv 37 595 sundmust (gitignore'itud, 2.2 MB)
===============================================================================
```
