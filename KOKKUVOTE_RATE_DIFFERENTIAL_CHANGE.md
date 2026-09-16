===============================================================================
NEMSIS — INTEREST-RATE DIFFERENTIAL CHANGE TEST
===============================================================================
  16. september 2026
  branch  claude/great-noether-um7382
  seeme   20260916 (koik randomiseerimised fikseeritud)
  Uurimistoo. Live-botti EI PUUDUTATUD, /update EI SAADETUD.


===============================================================================
1. EXECUTIVE SUMMARY
===============================================================================

  Eelregistreeritud primary test: CHANGE_D_4W -> jargmine ava -> 4 nadalat.

    bruto    +4.82 bp
    kulu      3.87 bp   (NEMSIS paaripohine, edasi-tagasi)
    neto     +0.95 bp
    kordne    1.25 x    (NEMSIS noue >= 2.00)
    t = 1.19,  p = 0.233,  n = 3 516,  10.29 aastat

  Positiivne keskmine tehingu kohta EI KANDU portfelli. Mittekattuvatel
  kohortidel (ainus aus aktsiakover) on tulemus NEGATIIVNE:

    neto kumulatiivne  -5.3%   ule 10.3 aasta
    maxDD             -13.6%
    Sharpe             -0.17

  Kolm fakti, mis otsustavad:

    1 KONTSENTRATSIOON. GBPUSD uksi annab 65.3% kogu brutost.
      ilma GBPUSD-ta        bruto +1.74 bp  p = 0.669
      ilma GBPUSD+GBPCHF    bruto -0.53 bp  p = 0.898
      Serv EI OLE mehhanism, ta on kaks paari.

    2 PERIOOD. TRAIN -5.16 bp, VALID -4.08 bp, FINAL OOS +21.60 bp.
      Kogu efekt on viimases 2.7 aastas. See on TAPSELT sama muster,
      mis NEMSIS COT-uuringus tuvastati kui SAMPLE-DEPENDENT.

    3 NULL. 500 juhusliku margi seast annab 11.6% sama voi parema
      tulemuse (p = 0.116). Segatud CHANGE_D p = 0.144.

  MEHHANISM ON OLEMAS JA ERISTUV. CHANGE_D ja TASE on samasuunalised
  ainult 56.6% ajast, korr(CHANGE_D, D) = +0.15. CHANGE EI OLE TASEME
  umberpakendamine. Aga eristuv mehhanism ilma robustse servata jaab
  ikka servata.

  LOPLIK KLASSIFIKATSIOON:  SAMPLE/REGIME DEPENDENT


===============================================================================
2. OLEMASOLEV CARRY vs UUS MEHHANISM
===============================================================================

  MIDA NEMSIS JUBA TESTIS (bot/v6_carry.py, kategooria 1):
    signaal    CARRY_REL = maara TASE vs korvi keskmine
    portfell   LONG top-2 / SHORT bottom-2 valuutat
    rebalanss  21 paeva (C1) voi 5 paeva (C2)
    tootlus    hinnamuutus + carry-kogunemine - kulu
    tulemus    Sharpe 0.42, kolm tapjat: brokeri markup, JPY-
               kontsentratsioon, 205 EUR konto

  MIDA SEE TEST TEEB — ERINEV NELJAL MOODUSEL:
    1 signaal on MUUTUS, mitte tase
    2 uhik on PAAR (28 tk), mitte valuutakorv (top-2/bottom-2)
    3 tootlus on ainult HINNAMUUTUS; carry-kogunemist EI LISATA,
      sest me testime muutuse INFOSISU, mitte carry teenimist
    4 hoid on fikseeritud 4 nadalat, mitte pidev rebalanss

  MASTER EDGE MAP rida 17: "Rate differentials — tase testitud;
  MUUTUS mitte". See test taidab selle lunga.

  KONTROLLITUD, ET DUBLEERIMIST EI OLE (RC.2):
    CHANGE ja LEVEL signaalid samasuunalised     56.6% ajast
    korr(CHANGE_D, D)                            +0.1458
    sign(D) TASE sama raamistikus (kirjeldav)    +3.94 bp, n = 14 693
    sign(CHANGE_D) PRIMARY                       +4.82 bp, n =  3 516

  Kaubeldavate vaatluste arv erineb 4x: TASE annab signaali peaaegu
  alati, MUUTUS ainult 24.1% nadalatest.


===============================================================================
3. ANDMEALLIKAS
===============================================================================

  INTRESSIMAARAD
    fail       bot/data/policy_rates.csv
    allikas    BIS WS_CBPOL, keskpankade AMETLIKUD poliitikamaarad
    sagedus    KUINE, kuu lopu seis
    valuutad   USD EUR GBP JPY CHF AUD NZD CAD
    revisjon   EI OLE. Keskpank kuulutab maara valja; hilisemat
               revideerimist ei toimu. See on selle andmestiku
               peamine eelis vorreldes makrostatistikaga.

  HINNAD
    failid     bot/data/{EURUSD,GBPUSD,AUDUSD,NZDUSD,USDJPY,USDCHF,
               USDCAD}_d25.csv (Yahoo paevane OHLC)
    ristid     arvutatud USD-jalgadest: P = V_baas / V_kvoot
    kontroll   audit D3: EURJPY == EURUSD * USDJPY, max erinevus 2.84e-14

  MIS ON KUINE JA MIS MITTE — OLULINE PIIRANG
    Signaali INFO on kuine. "4 nadalat" tahendab praktikas kuu-kuu
    muutust. Nadalane vaatlusvork annab rohkem sisenemispunkte, aga
    MITTE rohkem infot. Seetottu on 3 516 tehingut, mis polvnevad
    ainult ~128 kuust ja ~168 tegelikust maaraotsusest.
    See on selle uuringu koige olulisem statistiline piirang.


===============================================================================
4. ANDMEPERIOOD
===============================================================================

  maarad      2016-01 .. 2026-08      128 kuud
  nihe        1 kuu (kuu M maar kehtib kuus M+1)
  hinnad      2006-05-15 .. 2026-09-10, 4 644 sessiooni
  tehingud    2016-04-07 .. 2026-07-23  = 10.29 aastat

  JPY ALGAB HILJEM: BIS-i JPY-seeria algab 2016-09 (teised 2016-01).
  8 kuud JPY-paare puudub. Ei taidetud, ei ekstrapoleeritud.

  JAOTUS (fikseeritud ENNE tulemusi, kalendriaastate jargi):
    TRAIN      .. 2020-12-31        900 tehingut
    VALID      2021-01-01 .. 2023-12-31   1 360 tehingut
    FINAL OOS  2024-01-01 ..              1 256 tehingut


===============================================================================
5. VALUUTAUNIVERSUM
===============================================================================

  Koik 8 valuutat olid saadaval => koik C(8,2) = 28 unikaalset paari.
  Uhtegi paari EI EEMALDATUD, ei enne ega parast tulemusi.

  ORIENTATSIOON. Seitse majorit on TURUKONVENTSIOONIS (EURUSD mitte
  USDEUR, USDJPY mitte JPYUSD), sest kulutabel on selles orientatsioonis.
  Vale orientatsioon annaks majoritele risti kulu 4.4 bp asemel
  2.0-3.6 bp. Audit D1, D2b, D2c kontrollivad seda.

  KULUD (uhesuunaline bp, cot_engine.KULU_BASE):
    EURUSD 1.0  USDJPY 1.0  GBPUSD 1.2  AUDUSD 1.2
    USDCHF 1.3  USDCAD 1.3  NZDUSD 1.8  koik ristid 2.2
  Edasi-tagasi = 2 x uhesuunaline. Keskmine tehingu kohta 3.87 bp.


===============================================================================
6. TAPNE HUPOTEES
===============================================================================

  PRIMARY HYPOTHESIS (eelregistreeritud, kirjutatud enne esimest jooksu):

    CHANGE_D > 0  =>  LONG baas / SHORT kvoot
    CHANGE_D < 0  =>  SHORT baas / LONG kvoot

  Ehk: valuuta, mille intressidiferentsiaal on viimase 4 nadalaga
  TOUSNUD, tugevneb jargneva 4 nadala jooksul.

  L = 4 nadalat on fikseeritud ENNE tulemusi. Teisi lookback'e
  (1W / 2W / 8W / 12W / 6M) EI TESTITUD. Teisi hoideperioode
  EI TESTITUD. Muutuse suurust EI FILTREERITUD.


===============================================================================
7. TAPNE SIGNAALI DEFINITSIOON
===============================================================================

    R_c(t)        valuuta c poliitikamaar, % aastas, BIS kuu lopp,
                  nihutatud 1 kuu, ffill paevasele vorgule
    D_p(t)        R_baas(t) - R_kvoot(t)        protsendipunktides
    CHANGE_D(t)   D_p(t) - D_p(t - 4 nadalat)
    signaal       +1 kui CHANGE_D > 0;  -1 kui CHANGE_D < 0
                  tehingut EI TEHTA, kui |CHANGE_D| < 1e-9

  TOLERANTS 1e-9 ON NUMBRILINE KORREKTSUS, MITTE FILTER.
  Poliitikamaarad on noteeritud kolme kohaga (0.375, -0.75, 4.35).
  IEEE-754 lahutamine jatab muutumatu vahe korral jaagi ~1e-16, mille
  sign() teeb ekslikult signaaliks. Diagnostika leidis 24 sellist
  "tehingut" (|CHANGE_D| = 1.11e-16), mis andsid keskmiselt +128.93 bp
  ja tostsid primary tulemust +4.82 -> +5.66 bp. Need EI OLE tehingud.
  Vaikseim tegelik maaramuutus on 0.05 pp, seega 1e-9 on uheselt ohutu.
  Audit F4 kontrollib seda.

  SIGNAALI KVANTISEERITUS (RC.9). |CHANGE_D| ei ole pidev suurus:
    0.25 pp  2 528 tehingut  71.4%
    0.50 pp    640 tehingut  18.1%
    0.75 pp    140 tehingut   4.0%
    ulejaanud 11 taset kokku    6.5%
  Kvartiilide 25/50/75 piirid on KOIK 0.25 => kvartiilianaluus
  kollapseerub. Raporteeritud on tegelikud tasemed, mitte kvartiilid.


===============================================================================
8. AJASTUS JA NO-LOOKAHEAD METOODIKA
===============================================================================

    t         nadala VIIMANE sessioon. D(t) on selleks hetkeks teada
              (BIS kuu lopu maar, nihutatud 1 kuu).
    sisse     JARGMISE sessiooni AVAHIND
    valja     20 sessiooni hiljem, AVAHIND

  Nihe 1 kuu on TAPSELT sama reegel mis v6_carry.py. Ta on
  KONSERVATIIVNE: paris bot teaks maaramuutust kohe, kui keskpank
  selle valja kuulutab; siin teab ta seda alles jargmise kuu algusest.

  20 sessiooni = 4 nadalat. Audit B5: koigil 3 516 tehingul on samm
  TAPSELT 20; B4: mediaan hoid 28 kalendripaeva.


===============================================================================
9. PRIMARY TULEMUSED
===============================================================================

  test                         n    bruto     med    neto    wr%   sd_bp      t       p
  ------------------------  ----   ------   -----   -----   ----   -----   ----   -----
  PRIMARY CHANGE_D_4W       3516    +4.82   +3.44   +0.95   50.5   239.7   1.19   0.233

    bruto / kulu     1.25 x      (NEMSIS noue >= 2.00)
    voidumaar        50.5%       (nulli peal)
    sd               239.7 bp    (2.40% tehingu kohta)

  MITTEKATTUVAD KOHORDID — AINUS AUS AKTSIAKOVER
  Iga nadal avatakse uus 4-nadalane korv, seega korraga on avatud 4
  korvi ja tehingute jarjestikune korrutamine EI OLE aktsiakover.
  Kohort = iga 4. vaatlusnadal; koik 4 faasi arvutatud, faasi
  EI VALITUD tulemuse jargi.

    faas    n   bruto kum%   neto kum%   neto maxDD%   Sharpe
    ----   --   ----------   ---------   -----------   ------
    0      74        -3.1        -5.8         -14.8    -0.14
    1      74        -0.1        -2.9         -13.7    -0.07
    2      74       -11.0       -13.5         -18.6    -0.55
    3      74        +4.0        +1.1          -7.4    +0.07
    KESKM             -2.5        -5.3         -13.6    -0.17

    aastane neto ~ -0.84%

  KOIK NELI FAASI ANNAVAD NEGATIIVSE VOI NULLI LAHEDASE TULEMUSE.
  Erinevus tehingupohise +0.95 bp ja portfelli -5.3% vahel tuleneb
  sellest, et tehingupohine keskmine kaalub koiki 3 516 tehingut
  vordselt, portfell aga kaalub NADALAID vordselt. Aastatel, kus
  signaale on palju (2022: 724, 2025: 628), on tulemus erinev kui
  aastatel, kus neid on vahe (2021: 56). Portfelli vaade on see,
  mida konto tegelikult naeks.

  POORD- JA TASEMEKONTROLL (KIRJELDAV, mitte live-kandidaat)
    PRIMARY sign(CHANGE_D)    3516    +4.82   +0.95   t=+1.19  p=0.233
    poordsignaal              3516    -4.82   -9.53   t=-1.19  p=0.233
    sign(D) TASE (v6)        14693    +3.94   +0.03   t=+2.03  p=0.042

  Poordsignaal on tapselt peegeldus ja on parast kulu selgelt halvem.
  Signaal EI OLE taiesti juhuslik (poordversioon kaotab rohkem), aga
  see ei ole ka statistiliselt oluline.

  PIDEV VERSIOON: korr(CHANGE_D, D) = +0.1458. Mehhanismid on
  eristatavad.


===============================================================================
10. PAARIDE TULEMUSED
===============================================================================

  Norku paare EI EEMALDATUD.

  paar        n    bruto     med    neto    wr%      t       p
  ------   ----   ------   -----   -----   ----   ----   -----
  EURUSD    140   +33.79  +57.93  +31.79   60.7   1.83   0.067
  GBPUSD    136   +81.28  +88.94  +78.88   59.6   3.31   0.001
  USDJPY    132    -2.72   +1.43   -4.72   50.0  -0.11   0.910
  USDCHF    128   -31.05  -28.98  -33.65   43.0  -1.67   0.095
  USDCAD    144   -40.02  -43.04  -42.62   41.0  -3.03   0.002
  AUDUSD    160   +14.44  +17.03  +12.04   51.9   0.64   0.521
  NZDUSD    176   +22.38  +45.29  +18.78   53.4   0.92   0.356
  EURGBP    116   +54.47  +38.54  +50.07   65.5   3.48   0.000
  EURJPY     88   +54.92  +22.94  +50.52   52.3   1.93   0.053
  EURCHF     60   +38.41  +17.80  +34.01   60.0   2.36   0.018
  EURCAD    124    -5.77  -23.56  -10.17   46.8  -0.32   0.746
  EURAUD    132   -48.32  -37.61  -52.72   40.2  -2.52   0.012
  EURNZD    136    +3.95   -5.90   -0.45   48.5   0.23   0.815
  GBPJPY    104   +26.58  +34.71  +22.18   54.8   1.03   0.303
  GBPCHF    116   +65.76  +52.81  +61.36   59.5   3.28   0.001
  GBPCAD    164   +20.77  +18.19  +16.37   52.4   1.19   0.236
  GBPAUD    104   +16.43  +32.89  +12.03   57.7   0.60   0.551
  GBPNZD    116   -29.08  -32.76  -33.48   46.6  -1.46   0.145
  JPYCHF     60   +52.64  +62.59  +48.24   61.7   1.87   0.061
  JPYCAD    116    +8.45   -0.19   +4.05   50.0   0.29   0.768
  JPYAUD    116   -33.33  -40.01  -37.73   43.1  -1.36   0.174
  JPYNZD    116   -36.53  -55.30  -40.93   39.7  -1.43   0.153
  CHFCAD     80   -30.94  -39.53  -35.34   40.0  -1.30   0.195
  CHFAUD    120   -27.33  -26.13  -31.73   45.0  -1.11   0.268
  CHFNZD    152   -11.71   -3.93  -16.11   49.3  -0.59   0.557
  CADAUD    168    +9.37  +13.70   +4.97   53.6   0.64   0.519
  CADNZD    172    +2.62  +21.61   -1.78   54.1   0.16   0.870
  AUDNZD    140   -32.56  -30.57  -36.96   41.4  -2.39   0.017

  positiivseid paare (bruto)   16 / 28
  kogu bruto logsumma          +169.39%
  top 1 paar  GBPUSD           +110.54% =  65.3% kogusummast
  top 2 paari GBPUSD + GBPCHF  +186.83% = 110.3% kogusummast

  NEMSIS standard: top-1 osakaal < 30%   =>   KUKUB (65.3%)

  FALSIFITSEERIMINE — kas serv jaab alles ilma suurima panustajata?
  See EI OLE paaride valimine, vaid vastupidine test.

    ilma GBPUSD           n=3380   bruto +1.74   neto -2.18   p = 0.669
    ilma GBPUSD + GBPCHF  n=3264   bruto -0.53   neto -4.44   p = 0.898

  KAKS PAARI 28-st KANNAVAD KOGU TULEMUST. Ilma nendeta ei ole
  mehhanismi jalgegi. Top-2 osakaal 110.3% tahendab, et ulejaanud
  26 paari on KOKKU negatiivsed.


===============================================================================
11. AASTATE TULEMUSED
===============================================================================

  Halbu aastaid EI EEMALDATUD.

  aasta     n   bruto_bp   neto_bp    wr%       t
  -----   ---   --------   -------   ----   -----
  2016    144      -3.93     -8.03   47.9   -0.14
  2017    168     -11.41    -14.74   44.0   -0.70
  2018    224     -16.80    -20.13   48.2   -1.09
  2019    240     +26.18    +22.70   52.1   +2.03
  2020    124     -37.73    -41.70   37.1   -1.77
  2021     56    -150.04   -154.32   19.6   -6.17
  2022    724     -28.23    -32.19   46.1   -2.55
  2023    580     +40.16    +36.20   57.2   +4.66
  2024    428     -18.89    -22.86   47.2   -1.66
  2025    628     +30.42    +26.46   53.5   +3.87
  2026    200     +80.58    +76.62   70.0   +6.89

  neto positiivseid aastaid: 4 / 11

  Tehingute arv aastate loikes koigub 56-st (2021) 724-ni (2022).
  See peegeldab keskpankade aktiivsust: 2016-2021 oli maarasid
  praktiliselt nulli kulmutatud, 2022-2023 oli suur tostmislaine.


===============================================================================
12. WALK-FORWARD
===============================================================================

  Jaotus fikseeritud ENNE tulemusi, kalendriaastate jargi.
  Primary 4-nadalane lookback ja 4-nadalane hoid EI MUUTUNUD.

  osa            n    bruto     med    neto    wr%      t       p
  ---------   ----   ------   -----   -----   ----   ----   -----
  TRAIN        900    -5.16  -11.90   -8.74   46.9  -0.64   0.524
  VALID       1360    -4.08   -0.68   -8.05   49.8  -0.57   0.566
  FINAL OOS   1256   +21.60  +20.50  +17.64   54.0  +3.66   0.000

  Kohortide (aus aktsiakover) lousikes:
    TRAIN      neto kum  -5.5%   maxDD  -7.1%   Sharpe -0.43
    VALID      neto kum  -4.1%   maxDD  -8.6%   Sharpe -0.40
    FINAL OOS  neto kum  +4.5%   maxDD  -3.5%   Sharpe +0.69

  SEE ON OTSUSTAV TABEL. TRAIN ja VALID on MOLEMAD negatiivsed,
  kokku 7.6 aastat. FINAL OOS on tugevalt positiivne, 2.7 aastat.

  Kaks tolgendust:
    (a) mehhanism hakkas tooma, kui keskpangad hakkasid pariselt
        liikuma (2022+ tostmislaine)
    (b) 2024-2026 on soodne valim ja 7.6 aastat toendab vastupidist

  Ma EI VALI nende vahel. NEMSIS COT-uuringus oli TAPSELT sama
  muster (vana periood negatiivne, uus positiivne) ja seal osutus
  see valimisoltuvuseks: 2016-2026 aken oli koigi rulluvate akende
  99. pertsentiilis. Sama kahtlus kehtib siin.


===============================================================================
13. RANDOMIZATION
===============================================================================

  500 permutatsiooni, seeme 20260916.

  tegelik bruto: +4.818 bp  (n = 3 516)

  null                  mediaan       95%       max        p
  ------------------   --------   -------   -------   ------
  A juhuslik suund       +0.295    +6.754   +10.415   0.1160
  B segatud CHANGE_D     +0.077    +6.911   +11.123   0.1440

  11.6% juhuslikest markidest annab sama voi parema tulemuse.
  Ei ole oluline uheski tavaparases lavendis.

  VORDLUSEKS: NEMSIS B1 majanduskalendri testil oli sama null
  p = 0.0000 (0/500). Seal oli mehhanism olemas. Siin ei ole.


===============================================================================
14. KULUTUNDLIKKUS
===============================================================================

  kulu uhesuunaline   edasi-tagasi   bruto_bp   neto_bp   kordne   verdikt
  -----------------   ------------   --------   -------   ------   -------
  0.00 bp                     0.00      +4.82     +4.82      inf      —
  0.50 bp                     1.00      +4.82     +3.82     4.82    LABIB
  1.00 bp                     2.00      +4.82     +2.82     2.41    LABIB
  1.25 bp                     2.50      +4.82     +2.32     1.93    KUKUB
  1.50 bp                     3.00      +4.82     +1.82     1.61    KUKUB
  2.00 bp                     4.00      +4.82     +0.82     1.20    KUKUB
  NEMSIS BASE                 3.87      +4.82     +0.95     1.25    KUKUB

  NEMSIS base jaab primary klassifikatsiooni jaoks muutmata.
  Kulu ei ole siin ainus tapja: ka nullkuluga on p = 0.233.


===============================================================================
15. TASEMEKONTROLL — KAS SEE ON SAMA VANA CARRY?
===============================================================================

  EI OLE. Mehhanismid on statistiliselt eristatavad:

    CHANGE ja LEVEL samasuunalised     56.6% ajast
    korr(CHANGE_D, D)                  +0.1458
    kaubeldavaid vaatlusi CHANGE-l     3 516  (24.1% koigist)
    kaubeldavaid vaatlusi LEVEL-il    14 693  (peaaegu koik)

  56.6% on vaevu ule munditaskemise (50%). Kui CHANGE oleks TASEME
  umberpakendamine, peaks see arv olema 80-90%.

  sign(D) TASE samas raamistikus (kirjeldav, EI OLE primary):
    bruto +3.94 bp, neto +0.03 bp, t = 2.03, p = 0.042

  Tahelepanek: TASE annab siin madalama bruto (+3.94 vs +4.82), aga
  suurema t (2.03 vs 1.19), sest tal on 4x rohkem vaatlusi. Kumbki
  ei ulata 2x kulu latini. Neid EI KOMBINEERITUD.


===============================================================================
16. KESKPANGA OTSUSE DIAGNOSTIKA
===============================================================================

  PIIRANG: NEMSIS-il EI OLE keskpankade istungite kuupaevi. BIS-i
  andmed on kuised, seega otsuse hetk on teada ainult kuu tapsusega.

  maara MUUTUSI 2016-2026:
    USD  29 / 128 kuud = 22.7%      CAD  25 / 128 = 19.5%
    NZD  28 / 128      = 21.9%      GBP  24 / 128 = 18.8%
    AUD  26 / 128      = 20.3%      EUR  20 / 128 = 15.6%
    CHF  11 / 128      =  8.6%      JPY   5 / 120 =  4.2%

  KOIK nadalased vaatlused (kus D on olemas)     14 693
  neist CHANGE_D != 0 ehk kaubeldavaid            3 516  (24.1%)

  SEE ONGI DIAGNOOS. CHANGE_D on nullist erinev TAPSELT SIIS, kui
  uks kahest keskpangast muutis maara viimase 4 nadala jooksul.
  Signaal EI OLE pidev muutuja, vaid SUNDMUSSIGNAAL: 100%
  tehingutest jargneb poliitikaotsusele. Jaotust "otsuse ajal vs
  otsuste vahel" EI SAA teha — "otsuste vahel" grupp on definitsiooni
  jargi tuhi.

  Millise valuuta otsus signaali kannab (tehingujalgade osakaal):
    USD 14.4%  NZD 14.3%  CAD 13.7%  AUD 13.6%
    GBP 12.1%  EUR 11.4%  JPY 10.3%  CHF 10.2%
  Jaotus on uhtlane — signaal ei tule uhest keskpangast.
  (Kasum aga tuleb kahest paarist, vt sektsioon 10.)

  PIIRANG JAAB: ilma istungite kuupaevadeta ei saa eristada "otsuse
  hetke reaktsiooni" ja "otsuse-jargset drifti". Meetingute EI
  EEMALDATUD — neid ei saanud eemaldada, sest kogu valim on neist.


===============================================================================
17. ANDMEKVALITEET
===============================================================================

  Audit: 35 kontrolli, 0 FAIL. Jooksis ENNE tulemuste klassifitseerimist.

  MIS OLI KORRAS
    duplikaatkuid ei ole (128 unikaalset kuud / 128 rida)
    duplikaatkuupaevi hinnaindeksis ei ole (4 644 sessiooni)
    ootamatuid huppeid (>5%/paev) 33 / 37 152 = 0.089%
    maarad on astmefunktsioon: 47.6% paevadest ei muutu ukski maar
    EURJPY == EURUSD * USDJPY, max erinevus 2.84e-14
    USDJPY = 154.48 (mitte 0.0065) — orientatsioon oige
    D(EURUSD) = R_EUR - R_USD, kontrollitud kuupaeval 2024-06-14

  KAKS VIGA, MILLE AUDIT LEIDIS ENNE TULEMUSI — MOLEMAD PARANDATUD

  VIGA 1 — NADALAVAHETUSE BAARID
    Yahoo FX-seerias on puhapaevased OSABAARID (turg avaneb ~21-22
    UTC puhapaeval). Need said nadala "viimaseks kauplemispaevaks"
    ja rikkusid nii vaatluspaeva valikut kui 20-sessioonilist sammu.
    Parandus: laupaevad ja puhapaevad eemaldatud (621 baari).

  VIGA 2 — UJUKOMA-MURA SIGNAALID
    24 "tehingut" tekkisid |CHANGE_D| = 1.11e-16 pealt, mis on IEEE-754
    lahutamise jaak muutumatust vahest. Nad andsid keskmiselt
    +128.93 bp ja tostsid primary tulemust +4.82 -> +5.66 bp.
    Parandus: tolerants 1e-9 (vaikseim tegelik muutus on 0.05 pp).

  KOLMAS LEID — EI OLE VIGA, AGA ON PIIRANG
    Yahoo FX paevases seerias on igas nadalas 5 baari, kuid 58%
    nadalatest on sildistatud P-N ja 42% E-R (reedesid 493, puhapaevi
    691, E-N igauks ~1182). Kontrollisin, kas kuupaevasilt on
    susteemselt 1 paeva nihkes: EI OLE. Nihe 0 annab tootluste
    korrelatsiooni 0.58 ja tasemevea 6.2 bp, nihe +1 vastavalt 0.04
    ja 27.9 bp. Nihke-huopotees on UMBER LUKATUD.
    Tagajarg: nadala vaatluspaev on 63% juhtudest neljapaev ja 37%
    reede. See EI OLE lookahead ja EI MOJUTA 20-sessioonilist hoidu
    (audit B5: koigil tehingutel tapselt 20), aga kuupaevasildid ei
    ole nominaalvaartuses usaldusvaarsed.


===============================================================================
18. LOOKAHEAD AUDIT — PASS / FAIL
===============================================================================

  1  CHANGE_D kasutab ainult mineviku maarainfot            PASS
     B1: 2022-07-15 kasutab 2022-06 maara 1.625
  2  jooksev maar oli sisenemise hetkel teada               PASS
     nihe 1 kuu, sama reegel mis v6_carry.py
  3  4W lag on korrektne                                    PASS
     B6: d.loc[:t0] votab viimase vaartuse kuni t-4 nadalat
  4  FX sisenemine on PARAST signaali                       PASS
     B3: min vahe 1 sessioon, B8: vaatlus < sisse koigil
  5  valjumine kasutab ainult simulatsiooni motet           PASS
     B4: valja > sisse koigil; B5: tapselt 20 sessiooni
  6  kulu rakendub sisenemisel + valjumisel                  PASS
     C1: 2 x uhesuunaline; C2: neto = bruto - kulu
  7  rolling / ranking ei kasuta tulevikku                   PASS
     B2: viimase kuu maara muutmine 99.0-le ei muuda varasemaid
  8  puuduvate andmete taitmine ei tekita leakage'it         PASS
     ffill AINULT edasi (kuu M -> kuu M+1); bfill EI KASUTATA;
     JPY 8 puuduvat kuud jaeti valja, ei ekstrapoleeritud

  Lisaks: A2 maarasid ei revideerita; F4 ujukoma-mura ei tekita
  signaale; G1-G3 teadaolev vastus klapib.


===============================================================================
19. TEOSTATAVUS 205 EUR KONTOL
===============================================================================

    tehinguid              3 516 / 10.29 a = 342 aastas
    hoidmisaeg             32.2 kalendripaeva (20 sessiooni)
    KORRAGA AVATUD         ~48 positsiooni
                           (uus 28-paariline korv iga nadal, hoid 4 nadalat)

  UHE positsiooni suurus min lot 0.01 juures:

  paar      4-nad sigma%   0.01 lot EUR   1-sigma EUR   % kontost
  ------    ------------   ------------   -----------   ---------
  EURUSD            2.18           1000         21.83        10.6
  GBPUSD            2.86           1164         33.30        16.2
  USDJPY            2.76            861         23.74        11.6
  USDCHF            2.10            861         18.10         8.8
  USDCAD            1.59            861         13.66         6.7
  AUDUSD            2.85            616         17.56         8.6
  NZDUSD            3.22            500         16.08         7.8
  EURJPY            2.67           1000         26.67        13.0
  AUDNZD            1.62            616          9.98         4.9

    risk 0.25% = 0.51 EUR  ->  taidetav 0/9 paaril
                               vajalik konto 3 991 - 13 320 EUR
                               UHE positsiooni kohta
    risk 0.50% = 1.02 EUR  ->  taidetav 0/9 paaril
                               vajalik konto 1 995 -  6 660 EUR
                               UHE positsiooni kohta

  OTSE VALJA OELDUD: 205 EUR konto EI SAA seda strateegiat kaubelda.
  Uks minimaalne positsioon on 4.9-16.2% kontost, kavatsetud risk on
  0.25%. See on 20-65 kordne ulejook. Ja korraga peaks avatud olema
  ~48 positsiooni.

  Minimaalne vajalik konto: ~4 000 EUR uhe positsiooni jaoks 0.25%
  riskiga. Taieliku 28-paarilise korvi jaoks kordades rohkem, kui
  positsioone ei netita valuutajalgade tasemel.


===============================================================================
20. BENCHMARK
===============================================================================

  test                              n    bruto    neto      t       p
  ----------------------------   ----   ------   -----   ----   -----
  PRIMARY CHANGE_D_4W            3516    +4.82   +0.95   1.19   0.233
  A vordkaaluline FX (LONG baas) 3516    +5.87   +2.00   1.45   0.147
  B osta-ja-hoia EURUSD                 kumulatiivne +1.8%
                                        (2016-04-11 .. 2026-08-31)

  PRIMARY ON HALVEM KUI BENCHMARK A. Kui votta TAPSELT samad 3 516
  sisenemis- ja valjumishetke ja minna alati LONG baasvaluutas
  (signaali eirates), on tulemus +5.87 bp vs signaali +4.82 bp.

  Signaal EI LISA vaartust selle valimi peal.

  BENCHMARKI PIIRANG. NEMSIS-is ei ole standardiseeritud FX-
  benchmarki. Primary moot on paari log-tootlus, mis on 28 paari
  ristloikes juba turuneutraalne: ristloikeline tsentreerimine
  taandub paaritasemel valja, sest (r_baas - keskm) - (r_kvoot -
  keskm) = r_baas - r_kvoot. Seetottu on "pair return" ja
  "market-neutral excess return" SIIN MATEMAATILISELT SAMA arv.


===============================================================================
21. NEMSIS KRITEERIUMID
===============================================================================

  kriteerium                              tulemus                verdikt
  ------------------------------------    -------------------    -------
   1 bruto serv vs kulu (noue >= 2x)      1.25 x                 KUKUB
   2 neto serv                            +0.95 bp/tehing, aga
                                          portfell -5.3% / 10 a   KUKUB
   3 statistiline olulisus                p = 0.233               KUKUB
   4 OOS                                  +21.60 bp t=3.66,
                                          kuid TRAIN ja VALID
                                          molemad negatiivsed     KUKUB
   5 aastate robustsus                    neto 4/11 aastat        KUKUB
   6 paaride robustsus                    16/28 bruto positiivne,
                                          ilma top-2-ta -0.53 bp  KUKUB
   7 kontsentratsioon                     top-1 65.3% (noue <30%)
                                          top-2 110.3%            KUKUB
   8 permutation null                     p = 0.116 / 0.144       KUKUB
   9 lookahead                            8/8 PASS, audit 35/35   LABIB
  10 majanduslik tolgendus                mehhanism on eristuv
                                          (korr TASEMEGA 0.15),
                                          aga serv on kahes paaris KUKUB
  11 teostatavus 205 EUR kontol           0/9 paari, ~48 pos.     KUKUB

  LABIB 1 / 11.


===============================================================================
22. PIIRANGUD
===============================================================================

  1 INFOSAGEDUS. 3 516 tehingut polvnevad ainult ~128 kuust ja
    ~168 keskpangaotsusest. Tehingute arv UELEHINDAB soltumatute
    vaatluste arvu. Sama otsus annab signaali neljal jarjestikusel
    nadalal ja mitmes paaris korraga. Kohordianaluus (74 vaatlust
    faasi kohta) on ausam moot.

  2 PERIOOD. 2016-2026 on 10.3 aastat, millest 2016-2021 olid
    maarad praktiliselt kulmutatud. Tegelik "maaraliikumise periood"
    on 2022-2026 = 4.5 aastat. BIS-i andmed ei ulatu kaugemale.

  3 MEETINGUTE KUUPAEVAD PUUDUVAD. Otsuse hetk on teada kuu
    tapsusega. Reaktsiooni ja drifti ei saa eristada.

  4 YAHOO PAEVASE SEERIA KUUPAEVASILDID. 58% nadalatest sildistatud
    P-N, 42% E-R. Nihke-huopotees sai umber lukatud, aga vaatluspaev
    on 63% juhtudest neljapaev.

  5 KATTUVAD POSITSIOONID. ~48 positsiooni korraga. Kapitali
    tegelik kasutus ja netitamine valuutajalgade tasemel ei ole
    modelleeritud. Kohortide vaade on lahendus, aga ta vahendab
    valimi 74 vaatluseni faasi kohta.

  6 JPY 8 PUUDUVAT KUUD (2016-01..2016-08). Ei taidetud.

  7 CARRY-KOGUNEMIST EI LISATUD. See on tahtlik: testime muutuse
    INFOSISU, mitte carry teenimist. Live-kauplemises tuleks swap
    juurde ja see MUUDAKS tulemust — tuupiliselt halvemaks nendel
    positsioonidel, kus shorditakse tousva maaraga valuutat.


===============================================================================
23. LOPLIK KLASSIFIKATSIOON
===============================================================================

              SAMPLE/REGIME DEPENDENT

  MIKS MITTE "NO ROBUST RATE-CHANGE EFFECT FOUND":
    FINAL OOS on +21.60 bp, t = 3.66, p = 0.000, 1 256 tehingut,
    2.7 aastat. Seda ei saa nimetada "efekti ei ole".

  MIKS MITTE "PROMISING BUT NOT PROVEN":
    TRAIN ja VALID on MOLEMAD negatiivsed, kokku 7.6 aastat.
    Ilma kahe paarita (GBPUSD, GBPCHF) on kogu efekt -0.53 bp.
    Permutation null p = 0.116. Vordkaaluline benchmark on PAREM
    kui signaal. "Promising" noaks vahemalt, et signaal loob
    benchmarki.

  MIKS SAMPLE/REGIME DEPENDENT:
    Tulemus soltub tugevalt UHEST PERIOODIST (2024-2026) ja KAHEST
    PAARIST (GBPUSD, GBPCHF). Muudel perioodidel ja muudel paaridel
    ta ei eksisteeri. See on definitsiooni jargi valimi- ja
    rezhiimisoltuvus.

  MIDA SEE TAHENDAB PRAKTIKAS:
    Seda EI TOHI live'i viia. Mitte sellepargi, et ta on tondatud
    valeks, vaid sellepargi, et 7.6 aastat andmeid utleb "ei" ja
    2.7 aastat utleb "jah", ning "jah" tuleb kahest paarist
    kahekümne kaheksast.

  ÄRA OPTIMEERI. Ma EI testinud teisi lookback'e ega hoideperioode
  ja EI SOOVITA seda teha. Kui keegi hakkab nuud otsima "paremat
  L-i", siis ta leiab selle — sest 2024-2026 aknas on midagi, mis
  sobib. See oleks ulesobitamine, mitte avastus.
