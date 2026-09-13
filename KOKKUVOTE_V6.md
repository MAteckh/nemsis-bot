NEMSIS v6 — FINAL EDGE HUNT, LOPPRAPORT
13. september 2026 | BlackBull 525854 LIVE | 205 EUR | MAteckh/nemsis-bot

===============================================================================
LOPPVASTUS:  C — NO ROBUST EDGE FOUND
===============================================================================

Strateegiaotsing on LOPETATUD. v7 ei tule.

Testiti koik kolm ulejaanud edge-allikat. Uks neist (paris carry) andis
esimese usutava positiivse tulemuse kogu projektis — ja kukkus labi kolme
soltumatu praktilise piirangu peal.

===============================================================================
KATEGOORIA 1 — PARIS FX CARRY
===============================================================================

UUS ANDMEALLIKAS (v5 ETF-proxy tuhistatud lookahead-artefaktina):
  BIS WS_CBPOL — keskpankade AMETLIKUD poliitikamaarad
  https://stats.bis.org/api/v2/data/dataflow/BIS/WS_CBPOL/1.0/M.XX
  2016-01 .. 2026-08, kuu lopu seis, koik 8 valuutat (USD EUR GBP JPY
  CHF AUD NZD CAD). Neid maarasid EI REVIDEERITA — nad kuulutatakse
  valja ja kehtivad kindlast kuupaevast.

LOOKAHEAD-KAITSE: maarad nihutatud 1 kuu. Kuu M maar (teada kuu M lopus)
kehtib alles kuus M+1. See on KONSERVATIIVNE — paris bot teaks maara
muutust kohe valjakuulutamisel.

VALIDEERIMINE (peab vastama teadaolevatele faktidele):
  2020-06: USD 0.125  CHF -0.75  JPY -0.1     OK
  2023-07: USD 5.375  JPY -0.1                OK
  2016-01: NZD 2.5    AUD 2.0                 OK
Intressivahe korvi vastu 2023-07: JPY -3.87%, CHF -2.02%, NZD +1.73%,
USD +1.36% — tapselt see, mis reaalsuses oli.

5 EELREGISTREERITUD SPETSIFIKATSIOONI (bp/paev, NETO parast kulusid):

 spetsifikatsioon         hind   carry   kulu    NETO  Sharpe  TRAIN VALID FIN.OOS
 --------------------    -----  ------  -----  ------  ------  ----- ----- -------
 C1 kuine rebalanss      +0.14  +1.05   0.01   +1.18   +0.42   +1.26 +1.01  +1.23
 C2 nadalane rebalanss   +0.11  +1.05   0.01   +1.15   +0.41   +1.17 +1.08  +1.21
 C3 vol-skaleeritud      -0.14  +0.51   0.02   +0.35   +0.26   +0.40 +0.16  +0.52
 C4 carry + trendifilter -0.54  +0.53   0.17   -0.18   -0.10   -0.35 -0.23  +0.44
 C5 ilma USD-ta          +0.20  +1.01   0.01   +1.21   +0.40   +0.59 +1.57  +2.54

KULUTUNDLIKKUS:
 C1 kuine:  BRUTO +1.19 | LOW +1.19 | BASE +1.18 | HIGH +1.17  robustne
 C5 ilma USD-ta: BRUTO +1.22 | LOW +1.21 | BASE +1.21 | HIGH +1.20 robustne
 C4 trendifiltriga: kaotaja koigil tasemetel

KOHUSTUSLIKUD VORDLUSED:
 CARRY C1 (kuine)             +1.18 bp  Sharpe +0.42  maxDD -11.2%
 juhuslik valuutavalik (30x)  -0.28 bp                parim +1.01
 osta-ja-hoia EURUSD          +0.22 bp  Sharpe +0.08  maxDD -23.3%
 v5 parim FX (TS-MOM-MULTI)   -0.99 bp  Sharpe -1.02  maxDD -24.3%
 p(juhuslik >= carry) = 0.000

MIKS SEE ON USUTAV: ta on TAGASIHOIDLIK. Sharpe 0.42 on tapselt
akadeemilises vahemikus (kirjanduses 0.4-0.8). Lahutus naitab, et
+1.05bp tuleb INTRESSIST, hinnamuutus annab ainult +0.14bp. Nii carry
peabki valja nagema. Kui oleks tulnud Sharpe 4, oleks see olnud viga
(nagu v5-s oligi).

--- KOLM SOLTUMATUT TAPJAT ---

TAPJA 1 — BROKERI SWAP-JUURDEHINDLUS
 Ma arvutasin carry KESKPANGA maaradest. Sina ei kauple keskpangaga.
 BlackBulli CFD-swap = intressivahe MIINUS brokeri juurdehindlus.
 Carry-positsioon on ALATI kahepoolne => juurdehindlust makstakse KAKS
 korda, iga paev.

  juurdehindlus/pool/a   aastane kulu   NETO bp/paev  Sharpe  hinnang
  --------------------   ------------   ------------  ------  -------
             0.00%           0.00%          +1.18     +0.42   TOOTAB
             0.50%           1.00%          +0.78     +0.28   TOOTAB
             1.00%           2.00%          +0.39     +0.14   TOOTAB
             1.30%           2.60%          +0.15     +0.05   TOOTAB
             1.50%           3.00%          -0.01     -0.00   KAOTAJA
             2.00%           4.00%          -0.40     -0.14   KAOTAJA

 MURDEPUNKT: 1.49% poole kohta aastas.
 BlackBull standard-konto tuupiline FX swap-markup: 0.5-1.5%/pool.
 => SERV ISTUB TAPSELT MURDEPUNKTIL. FRAGIILNE.

TAPJA 2 — KONTSENTRATSIOON UHTE VALUUTASSE
  valuuta  LONG %ajast  SHORT %ajast   panus NETO-sse
  USD          52.5%          0.0%         +0.16bp
  EUR           0.0%          0.8%         -0.01bp
  GBP          23.3%          0.0%         +0.02bp
  JPY           0.0%         99.2%         +0.98bp   <-- 82% kogutulust
  CHF           0.0%        100.0%         -0.15bp   <-- KAOTAS
  AUD          20.8%          0.0%         +0.09bp
  NZD          65.4%          0.0%         +0.10bp
  CAD          37.9%          0.0%         +0.01bp
  KOKKU                                    +1.20bp

 82% kogutulust on SHORT JPY. CHF short KAOTAS raha, hoolimata sellest
 et ta oli teine madalaim tootlus — ehk "carry faktor" ei tootanud isegi
 teise madalaima valuuta peal.
 => See EI OLE hajutatud faktor. See on UKS MAKROPANUS: BoJ jai -0.1%
    peale kogu kumnendiks, samal ajal kui koik teised tostsid.

TAPJA 3 — 205 EUR TEOSTATAVUS
  C1 noiab LONG 2 + SHORT 2 = 4 valuutapositsiooni.
  0.01 lot nominaal                 1100$
  4 positsiooni nominaal            4400$
  konto                              205 EUR
  VAJALIK VOIMENDUS                 21.5x
  strateegia aastatootlus (1x)      2.98%
  sama 205 EUR pealt (1x)           6.11 EUR/aastas
  21.5x voimendusega maxDD          -240.2%
 => Miinimum-lot sunnib peale voimenduse, mida strateegia ei kannata.
    Konto oleks ammu otsas.

CARRY CRASH-RISK (taielikkuse huvides):
  kalduvus (skew)     -0.33    kurtoos +3.29
  halvim paev        -292bp    halvim kuu -5.62%
  maxDD              -11.2%    taastumistegur +2.91

===============================================================================
KATEGOORIA 2 — MAKROSUNDMUSED
===============================================================================

MIS ON AUSALT TESTITAV: NFP = kuu ESIMENE REEDE 13:30 UTC. See on
reegliga tuletatav, kalendrit ei vaja, ajakava on fikseeritud alates
1940ndatest.

MIS EI OLE: FOMC/ECB/BoE/BoJ kuupaevad ei ole reegliga tuletatavad
(maaratakse igal aastal eraldi). Ilma kalendrita ma neid EI testinud
ega vermi kuupaevi malust. => TESTIMATA.

NFP TULEMUSED (8 instrumenti, 27-34 sundmust igauhel):
 volatiilsus NFP-baaril: 1.78-1.98x tavalisest (ootusparane)

 suuna jatkuvus (bp, ILMA kuludeta):
  paar         +1h      +4h     +24h
  EURUSD      -1.3     -1.4     +5.7
  GBPUSD      -2.7     -1.6     +2.3
  USDJPY      -0.3     -1.0    +23.4
  USDCHF      +1.0     -3.2     +3.1
  USDCAD      +3.5     +6.6     +8.2
  AUDUSD      +1.3     +5.6     +0.7
  NZDUSD      -0.6     -2.2     +1.0
  XAUUSD     +15.8    +24.8    +27.2   <-- domineerib
  KESKMINE    +2.1     +3.5     +8.9

 KULUD UUDISE AJAL (spread laieneb 3-10x):
  tavaline (2.6bp)     -0.5     +0.9     +6.3
  uudise ajal 3x       -5.7     -4.3     +1.1
  uudise ajal 10x     -23.9    -22.5    -17.1

 => Parim (+24h) annab konservatiivse slippage'iga +1.1bp.
    NFP on 12 korda aastas => 12 x 1.1bp = 13bp = 0.13% aastas.
    Ja tulemust domineerib XAUUSD, mitte FX.
    Valim: 27-34 sundmust paari kohta. Statistiline voimekus puudub.
 => FAIL.

===============================================================================
KATEGOORIA 3 — MIKROSTRUKTUUR = UNTESTABLE
===============================================================================

NOUTUD: tick-andmed voi bid/ask kvoodid.
OLEMAS: ainult OHLC (paev, H1, M15). Bid/ask EI OLE. Tick EI OLE.
        Mahtu (volume) samuti mitte.

Sunteetilist order flow'd EI loodud.

Mida OHLC-st saaks tuletada ja miks ma seda EI teinud:
  - "bid/ask imbalance" kuunla kerest => see on hinnamuutus teise nimega.
    Juba testitud momentumina. Negatiivne.
  - "quote intensity" baari ulatusest => see on volatiilsus.
    Juba testitud v4 vol-rezhiimides. Negatiivne.
  - "likviidsusshokk" suurest baarist => see on vol-huppe.
    Juba testitud v4 "ebanormaalne" rezhiimina. Negatiivne.

=> UNTESTABLE, mitte FAIL. Vahe on oluline: seda EI SAA otsustada ilma
   oigete andmeteta.

===============================================================================
KULD — LOPETATUD
===============================================================================

Ma ei nimeta XAUUSD Donchianit enam edge'iks.
  Donchian:   +2148 EUR, maxDD -47.3%, tulu/DD 22.15
  Osta-ja-hoia: +2616 EUR, maxDD -25.1%, tulu/DD 50.91
Osta-ja-hoia on risk-adjusted 2.3x parem.

Kusimus oli: "kas on olemas risk-adjusted strateegia, mis PARANDAB
osta-ja-hoia'd?" Vastus kolme testivooru jarel: EI.
=> XAUUSD strateegiaotsing LOPETATUD.

===============================================================================
KOKKUVOTE: MIDA TESTITI
===============================================================================

v4:  ~11 500 testi, 10 strateegiaperekonda, 24 instrumenti
     lai paevasisene soel, rezhiimipohine raamistik, turustruktuur,
     PDF-i 15 paaripohist konfi, backtest-engine'i audit (16 testi)
v5:  14 eelregistreeritud huopoteesi, latentne valuutatugevus,
     ristloikeline momentum, ETF-carry (osutus artefaktiks)
v6:  5 carry-spetsifikatsiooni paris BIS-i maaradega, NFP, mikrostruktuur

KOKKU: ~11 530 testi. Positiivseid, mis labivad koik 13 PASS-kriteeriumi: 0.

===============================================================================
MIDA EI OLNUD VOIMALIK TESTIDA
===============================================================================

1. TICK- JA BID/ASK-ANDMED. Kogu mikrostruktuuri suund. Ilma nendeta
   ei saa oelda ei jah ega ei.
2. FOMC/ECB/BoE/BoJ kuupaevad. Vajab majanduskalendrit.
3. PARIS BROKERI SWAP-TABEL. Koik kuluhinnangud on mudel. Sinu konto
   ajalugu annaks paris numbrid — ja see on tapselt see number, mis
   otsustab, kas carry tootaks.
4. M15 pikem ajalugu (Yahoo annab 60 paeva).

===============================================================================
MIKS EDGE PUUDUB — MEHHANISM
===============================================================================

Kolm sooltumatut pohjust, mis koik viivad samale vastusele:

1. HINNAPOHINE SIGNAAL. Bruto-serv on H1-l ~0 (moodetud: -0.9 kuni
   +1.4bp perekonniti, keskmine +0.1bp). Kulu on 2.6-3.0bp. Signaal ei
   sisalda infot; kulu teeb ulejaanu. Indikaatorite lisamine ei muuda
   seda, sest probleem ei ole mustri leidmises.

2. CARRY. Serv on PARIS (+2.65%/aastas bruto), aga see on TASU
   RISKI EEST, mitte turu viga. Broker votab selle tasu suures osas
   endale juurdehindlusena. Jarele jaab 0-1%, mis ei kata 205 EUR
   konto miinimum-loti sunnitud voimendust.

3. KAPITAL. Miinimum-lot 0.01 tahendab, et iga strateegia, mis noiab
   rohkem kui 1-2 positsiooni, sunnib 205 EUR kontol peale 10-20x
   voimenduse. Ukski nendest strateegiatest ei kannata sellist
   voimendust — maxDD korrutub sama kordajaga.

===============================================================================
JARGMINE VAJALIK ANDMESTIK (kui kunagi jatkad)
===============================================================================

TAHTSUSE JARJEKORRAS:
1. SINU ENDA BROKERI SWAP-TABEL. See on odavaim ja otsustavaim.
   Kui BlackBulli juurdehindlus on alla 1.3%/pool, on carry teoreetiliselt
   plussis. Kui ule 1.5%, on ta lopik ei. See on UKS number, mille saad
   MT5-st ise vaadata.
2. Tick/bid-ask andmed (mikrostruktuur) — ainus taielikult testimata suund.
3. Majanduskalender (FOMC/ECB/BoE/BoJ tapsed ajad).

===============================================================================
MILLINE KAPITAL OLEKS PRAKTILISEM
===============================================================================

Carry C1 noiab 4 positsiooni x 0.01 lot = 4400$ nominaali.
Et voimendus oleks mõistlik (alla 3x), oleks vaja ~1500 EUR.
Et see oleks ohutu (alla 1.5x), ~3000 EUR.
Aga isegi siis: 2.98% aastas bruto, millest broker votab poole.

XAUUSD Donchian: 500-1000 EUR viiks ruin-riski 8.8%-lt 0.0%-le.
Aga osta-ja-hoia on ikka parem, seega see ei ole pohjus kapitali lisada.

===============================================================================
KAS TRADING ON SELLE KAPITALIGA MOISTLIK
===============================================================================

Aus vastus: EI.

205 EUR juures on miinimum-lot piirang nii range, et ta maarab ara koik.
Iga strateegia, mis testides toimib, noiab kas (a) voimendust, mida ta
ei kannata, voi (b) risk tehingu kohta 10-25%, mis on 10-25x ule
moistliku piiri.

See ei ole strateegiaprobleem. See on kapitaliprobleem, ja seda ei
lahenda ukski kood.

Kui tahad kauplemist opida, on 205 EUR sobiv summa selleks, et opida
KAOTAMA vaikselt. See ei ole sobiv summa selleks, et TEENIDA.

===============================================================================
SEIS
===============================================================================

Live-faile main_v4.py, config.py, mt5_connector.py, strategy_meanrev.py,
backtest.py EI OLE muudetud uheski uurimisvoorus. Juur ja bot/ on
sunkroonis. Koik kompileerub.

Bot ootab endiselt /update-i. ARA saada seda.

Ma ei soovita live-tradingut. Ma ei ehita v7.
