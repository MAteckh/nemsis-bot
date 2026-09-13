NEMSIS v4 — UURINGUTE KOKKUVOTE
13. september 2026 | Konto: BlackBull 525854 LIVE | Kapital: 205 EUR
Repo: MAteckh/nemsis-bot | 127 commit'i, 95 uurimisskripti, 61 andmefaili

===============================================================================
LOPPJARELDUS
===============================================================================

ROBUSTSET EDGE'I EI LEITUD - mitte uhtegi, mida saaks 205 EUR kontoga
ohutult kaubelda.

Struktuurne pohjus on vastupidisus, mida parameetritega ei lahenda:
  - Instrumendid, kus riskijuhtimine 205 EUR kontol ON voimalik (FX,
    0,5-1,0% riski tehingu kohta), on tapselt need, kus SERVA EI LEITUD.
  - Instrument, kus serv ON olemas (XAUUSD donchian), EI MAHU riskiraami:
    22% tehingu kohta = 22x ule lubatud ulempiiri.

===============================================================================
1. ANDMESTIK
===============================================================================

Paev   22 instrumenti, 2016-2026, ~2600 baari/seeria
H1     24 instrumenti, 2023-2026, 13500-17400 baari (12 FX-paari laetud
       selle too kaigus - varem polnud paevasiseseid andmeid UHELGI paaril)
M15    15 FX-paari, 60 paeva, ~5590 baari (valideerimiseks liiga luhike)

Andmeaudit: duplikaate 0, OHLC-vigu 0, sunteetilist Open'i ei ole,
laupaeva-baare 0.

===============================================================================
2. MOOTORI AUDIT (16 sunteetilist testi)
===============================================================================

Iga test konstrueeritud nii, et KUKUKS LABI, kui viga oleks sees.

  Lookahead, juhuslik jalutuskaik     oodatav -2,00 bp   motis -2,43 (SE 0,23)  OK
  Positiivne kontroll (tuleviku info)  oodatav suur pluss motis +16,5 bp        TUVASTAB
  Teooria P(TP enne SL)=SL/(TP+SL)     oodatav 25,0%      motis 25,0% / 26,2%   OK
  "Molemad tabatud samas baaris"                          motis 0,00%           OK
  TP/SL taitmine kasitsi baaridel                         tapne 1e-12 piires    OK
  Kulu 0 vs 1,0bp = tapselt 2,0bp                         motis 2,000000        OK
  Pip value EURUSD/USDJPY/XAUUSD                          koik oiged            OK
  Positsioonid ei kattu ajaliselt                         18453 <= 20000        OK
  Position sizing 205EUR/0,5%/30pip    noutud <=1%        tegelik 1,5%          PIIRANG

=> Mootor on korrektne. Jareldus "bruto-serv on null" EI OLE artefakt.

LEID A: backtest.py ei modelleeri tehingukulusid uldse (rida 136).
        Live ostab tick.ask-ilt, sulgeb tick.bid-ilt = tais spread iga
        tehingu pealt (mt5_connector.py 143-144, 234-235).
        Lahendus: uus kulumudel.py rakendab kulud tagantjarele.

LEID B: INSTRUMENTS["XAUUSD"]["enabled"]=False - kulla grid EI joose.
        Live'is on ainult portfell, uks jalg: XAUUSD donchian 50 paevabaaril.

===============================================================================
3. TESTIDE REGISTER
===============================================================================

 #  Huopotees                      Teste    Verdikt
--  ----------------------------   ------   ------------------------------------
 1  JP225 lead-lag                    ~40   Serv paris, aga rezhiimist soltuv.
                                            EI OLE SIZEABLE (volume_min 0,1 =
                                            17,7x voimendus)
 2  Kulla grid, koik konfid            75   LABI KUKKUNUD. Tapja pole suur
                                            kahjum vaid float_stop (141x) ja
                                            trend_reset (31x) = -661 EUR
 3  Tugi/vastupanu tagasilukkamine    190   HALVEM KUI JUHUSLIK (null p=1,000).
                                            41/46 miinuses; TP x SL maatriksis
                                            iga SL-tase miinuses
 4  Kuunlamustrid                     157   SERVA EI OLE. 2 Bonferroni labijat,
                                            molemad negatiivsed
 5  Norkade signaalide korv           634   RINGTOESTUS. Sharpe +2,20 oli
                                            valikunihe; puhas WF +0,37;
                                            libisev aken -1,45
 6  Lai paevasisene soel (10 pere-  10156   LABI KUKKUNUD. Range soel:
    konda: kellaaeg, ORB, Donchian,          1 LABIJA 10156-st, ja seegi oli
    momentum, poore, sess-ulek,              lihtsalt pikk aktsiapositsioon.
    paevasis. momentum, vol-surve,           Puhas WF: OOS 7/21 (mundivise 10,5)
    tagasitomme, juht-jargi)
 7  PDF-i 15 paaripohist konfi        252   LABI KUKKUNUD. Ootus>0: 22/252.
                                            FINAL OOS 2/9. Ausas baseline-
                                            vordluses 0/15
 8  Setupide umberpooramine            63   MURA. H1-l bruto -1,3 -> +2,5bp,
                                            aga M15-l pooramine -2,8bp
 9  1H trend + 15m entry               63   VALIDEERIMATA. Bruto -1,3 -> +1,7bp,
                                            ECN neto +0,8bp. Parem kui H1, aga
                                            ainult 60 paeva / 28-92 tehingut
10  Rezhiimipohine strateegiavalik  61 lh   LABI KUKKUNUD. 1/61 lahtrit plussis.
    (7 rezhiimi x 10 perekonda)              Rezhiimiluliti OOS 0/14, -3,65bp
11  Turustruktuur (likv. puhkimine,   5 p   SERVA EI OLE. Bruto -0,87..+0,47bp.
    BOS, CHOCH, ebaonn. murre,               Parim (CHOCH) +0,47bp kulu 3,05
    noudlus/pakkumine)                       vastu
12  Vol. kokkusurve -> labimurre   27 x 16  SERV < KULU. Bruto plussis 26/27
                                            parameetrikombinatsioonist (PLATOO),
                                            aga p<0,10 ainult 3/16 paaril
13  XAUUSD donchian 50 (LIVE)       65 teh  TOOTAB, AGA... vt allpool

===============================================================================
4. KAKS KESKSET LEIDU
===============================================================================

LEID A - SIGNAALI BRUTO-SERV ON NULL, KULU ON 3 BP

  perekond              BRUTO     NETO    kulu
  ------------------   ------   ------   -----
  F surve->murre        +1,42    -1,59    3,01     <- ainus, mis eristub
  E CHOCH               +0,47    -2,58    3,05
  C Donchian 24h        +0,31    -2,69    3,00
  E BOS                 +0,15    -2,87    3,02
  A trend EMA20/50      +0,06    -2,92    2,99
  B momentum 24h        -0,29    -3,28    2,99
  D poore BB20          -0,48    -3,48    2,99
  E likv. puhkimine     -0,55    -3,56    3,01
  E ebaonn. murre       -0,87    -3,87    3,00
  E noudl./pakkumine    -0,87    -3,91    3,04

  => Probleem EI OLE signaal, mida kulud voimendavad.
     Signaal on H1-l lihtsalt vaartusetu ja kulu teeb ulejaanu.

LEID B - KULU KASVAB SAGEDUSEGA LINEAARSELT, SERV EI KASVA ULDSE

  tehinguid/aastas   teste   parim BRUTO   kulu/aastas   parim NETO
  ----------------   -----   -----------   -----------   ----------
  < 100                152     +35,9 bp         3,8 %     +29,9 bp
  100-300             5878     +42,1 bp         8,5 %     +36,1 bp
  300-700             2011     +21,5 bp        23,3 %     +18,5 bp
  700-1500            1362     +18,2 bp        52,9 %     +13,3 bp
  1500-4000            421     +13,9 bp        93,1 %     +10,9 bp
  > 4000               332      +6,3 bp       285,2 %      +2,7 bp

  205 EUR kontol: 5 tehingut paevas = 1260 aastas x 0,214$ = 270$ kulu
  aastas. Iga tehing peab bruto teenima 2,0bp ainult nulli tulemiseks.
  Keskmine bruto-serv koigist 10156 testist: +0,1 bp.
  KULU ON 20x SUUREM KUI SERV.

  Voimendus EI AITA - ta suurendab serva ja kulu tapselt uhepalju.

===============================================================================
5. AINUS STRATEEGIA, MIS LABIB: XAUUSD DONCHIAN 50, PAEVABAAR
===============================================================================

65 tehingut, 2020-2026, miinimum-lot 0,01:

  stsenaarium        BRUTO      KULUD       NETO      PF    maxDD
  ---------------   -------   --------   --------   -----   ------
  kuludeta          +2187 E       0 E     +2187 E    2,81   -45,6%
  STANDARD-konto    +2187 E     204 E     +1983 E    2,53   -56,9%
  ECN-konto         +2187 E     189 E     +1999 E    2,56   -56,1%

  Kulud soovad ainult 9% brutost - madal sagedus paastab.

MIDA LABIB:
  Lookback 20/30/40/50/60/80/100     7/7 plussis  => PLATOO, mitte uksik tipp
  Aastate kaupa                      6/7 plussis
  Juhuslik sisenemine sama TP/SL-iga +321 vs +1983 EUR, p = 0,033
  Paevabaari mitmetimoistetavus      0/29 tehingut muutus (H1-ga lahendatud)

MIDA EI LABI:
  Osta-ja-hoia 1 untsi kullaga       +2616 EUR => JAAB ALLA 632 EUR VORRA
  Kasumi jaotus suuna jargi          pikad +1935, luhikesed +48
                                     => 98% on PIKK KULLAPOSITSIOON
  Kasumi jaotus ajas                 84% tuleb 2025-2026-st

MONTE CARLO (10 000 simulatsiooni, tehingute jarjekord segatud):

  algkapital   risk/teh   RISK OF RUIN   mediaan lopp   halvim 5%
  ----------   --------   ------------   ------------   ---------
     205 EUR     24,3 %      8,8-9,9 %       2188 EUR      38 EUR
     500 EUR      9,9 %          0,1 %       2483 EUR    2483 EUR
    1000 EUR      5,0 %          0,0 %       2983 EUR    2983 EUR
    2000 EUR      2,5 %          0,0 %       3983 EUR    3983 EUR
    5000 EUR      1,0 %          0,0 %       6983 EUR    6983 EUR

  MIKS 205 EUR EI KANNA:
  Pikim kaotusjada ajaloos = 5 tehingut. Halvim uksiktehing = -49,74 EUR.
  Viis jarjest = -249 EUR. Konto on 205 EUR.
  See jada on ajaloos JUBA JUHTUNUD. Konto elas ule ainult sellepolikult,
  et oli selleks ajaks kasvanud.

===============================================================================
6. POSITION SIZING - MIDA 205 EUR MIINIMUM-LOTIGA LUBAB
===============================================================================

SL = 1,5 x ATR(14) H1, miinimum-lot 0,01, 205 EUR konto:

  instrument              SL vaartus   % kontost   0,25-1% voimalik?
  --------------------   ----------   ---------   -----------------
  EURGBP                     1,01 E       0,5 %   JAH
  NZDUSD                     1,18 E       0,6 %   JAH
  AUDUSD                     1,44 E       0,7 %   JAH
  EURUSD                     1,59 E       0,8 %   JAH
  USDCHF                     1,64 E       0,8 %   JAH
  EURJPY                     1,99 E       1,0 %   JAH
  GBPUSD                     2,02 E       1,0 %   JAH
  USDJPY/USDCAD/GBPJPY       ~2,2 E       1,1 %   1-2%
  WTI                        5,76 E       2,8 %   EI
  XAGUSD                    18,35 E       9,0 %   EI
  XAUUSD                    21,65 E      10,6 %   EI
  XAUUSD PAEVABAARIL       104,65 E      51,0 %   EI  (45 EUR lagiga 22,0%)
  ^^ see on see, mida live praegu kasutab

===============================================================================
7. MINU ENDA VEAD (leitud ja parandatud)
===============================================================================

1. EBAAUS BASELINE (koige tosisem)
   Viga: vordlesin PARIMAT 252 variandi seast UHE juhusliku sisenemisega.
         Tulemus "11/15 loob juhuslikku".
   Oige: juhuslik peab labima SAMA valikuprotsessi (parim N seast).
         Tegelik tulemus: 0/15, keskmine -8,0 bp.

2. PAEVABAARIDEL TP/SL TESTIMINE
   Viga: breakout-straddle andis paevabaaridel Sharpe +4,76.
         Paevabaar ei utle, kumb tase tabati esimesena.
   Oige: sama reegel tunniandmetel Sharpe -1,48.

3. NULL-JAOTUSE VALE KONSTRUKTSIOON
   Viga: muraks abs(tootlus) x juhuslik_mark, kus kulu oli juba maha
         arvatud => kulu muutus potentsiaalseks kasumiks (mura 113 labijat).
   Oige: juhuslikusta SIGNAALI SUUND, rakenda kulud uuesti.
         Mura 42,5, paris 62, p=0,000.

4. BONFERRONI MOLEMAL POOL
   Viga: |t| > lavend andis "3577 labijat" - loeb labijaks ka
         statistiliselt kindlad KAOTAJAD.
   Oige: ainult positiivne pool => 1 labija 10156-st.

5. PLATOO-KONTROLL LUGES VALESTI
   Viga: lugesin kokku KOIK labijad (5) ja jareldasin "voib-olla platoo".
         Muster oli vahelduv: 8 ok / 10 halb / 12 halb / 14 ok / 16 halb.
   Oige: moda pikimat JARJESTIKUST jada.

6. KAPITALINOUE 1x VOIMENDUSEGA  [sina leidsid]
   Viga: utlesin et 1000 EUR/kuus vajab 60 000 EUR (eeldas 1x).
   Oige: 5x juures 12 000 EUR; ajalooline tulemus ~925 EUR/kuus.

7. S/R TESTITUD ILMA TP/SL-ita  [sina leidsid]
   Viga: testisin kas signaal ennustab suunda - aga sinu idee oli
         "vota vaike kasum", mis TAHENDAB TP-d.
   Oige: ehitasin teekonna-teadliku H1-simulatsiooni, 190 varianti.

8. MONKEY-PATCH, MIS VAIKSELT EI RAKENDUNUD
   Viga: asendasin mustri, mida originaalkoodis ei eksisteerinud -
         rakendus ainult ostu poolele. Koik 14 tulemust mottetud.
   Oige: kirjutatud umber config'i kaudu.

9. RUIN-LAVEND JA i.i.d. BOOTSTRAP
   Viga: i.i.d. bootstrap havitas kaotusjadad, ruin-lavend -95%,
         stop-out puudus => "10x voimendus = 100% edu, 635M EUR".
   Oige: block bootstrap 10-tehinguliste plokkidega, 100 EUR porand,
         stop-out sisse.

LIVE-KOODIST LEITUD VEAD:
  - sync_mt5_positions kontrollis sulgemist magic-filtreeritud ticket'ite
    vastu => kasutaja kasitsi tehing paistis igal skannil suletuna
    (13 duplikaatrida + 13 Telegrami teadet live'is)
  - spekulatiivne sulgemistuvastus "if TP ... elif SL" eeldas VOITU alati,
    kui molemat puudutati; executed=True kirjutati enne sync'i
  - MARGIVIGA get_scaled_max_float()-is ja backtest.py-s: negatiivne saldo
    pooras vordluse umber ja sulges IGA positsiooni, sh kasumlikud
  - surnud config-lulitid: tp_min/tp_max/sl_max ei loetud kunagi;
    risk_based_lot ei kasutatud live-grid'i poolt

===============================================================================
8. MIS ON TESTIMATA
===============================================================================

- M15 pikem ajalugu. Yahoo annab 60 paeva. "1H trend + 15m entry" andis
  parima tulemuse kogu PDF-i toost (bruto -1,3 -> +1,7bp), aga 28-92
  tehingu peal. Valideerimiseks vaja 2+ aastat teisest allikast.
- CARRY. Intressimaarade vahe on FX-i koige paremini dokumenteeritud
  anomaalia. Valuutapohiseid intressiandmeid ei ole.
- PARIS UUDISTEKALENDER (CPI, NFP, keskpangaotsused). Testisin ainult
  volatiilsuse huppe asendusnaitajana.
- TICK-ANDMED JA PARIS SPREAD. Koik kuluhinnangud on mudel.
- RISTLOIKELINE FX (jarjesta paarid, osta tugevaimad / muu norgimad).

===============================================================================
9. SOOVITUS
===============================================================================

1. ARA PANE 205 EUR PRAEGUSE KONFIGURATSIOONIGA TOOLE.
   Strateegia ise on hea. Konto on selle jaoks liiga vaike.
   8,8-9,9% toenaosus konto kaotada ei ole ports, mida maksta.

2. KUI TAHAD SEDA STRATEEGIAT KAUBELDA, VAJAD 500-1000 EUR.
   500 juures ruin 0,1%, 1000 juures 0,0%. Miinimum-lot 0,01 on
   fikseeritud, seega ainus muutuja on nimetaja.

3. KUI TAHAD 205 EUR-GA JATKATA, SIIS AINULT FX-il ja teadmisega, et
   serva pole toestatud. EURGBP, NZDUSD, AUDUSD, EURUSD, USDCHF mahuvad
   0,5-0,8% riskiraami. Aga 10156 testi ei leidnud neil serva.
   See oleks kapitali sailitamine ilma oodatava tuluta.

4. KULU ON AINUS HOOB, MIS ON PARISELT SINU KAES.
   ECN-konto standard-konto asemel poolitab spread'i. Ainus perekond
   selge bruto-servaga (vol. kokkusurve +1,42bp) muutub ECN-kuludega
   piiripealseks.

5. MIDA MITTE TEHA:
   Mitte suurendada sagedust. Mitte suurendada voimendust. Mitte otsida
   uut indikaatorite kombinatsiooni - 10156 testi utlevad, et bruto-serv
   on null, ja indikaator ei muuda seda.

===============================================================================
SEIS
===============================================================================

Live-faile main_v4.py, config.py, mt5_connector.py, strategy_meanrev.py
EI OLE selle uurimistoo kaigus muudetud. Juur ja bot/ on sunkroonis.
Bot ootab endiselt /update-i VPS-il - ja soovitus on, et see nii ka jaaks,
kuni konto on 500-1000 EUR.
