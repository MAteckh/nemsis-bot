NEMSIS v7 — MULTI-PAIR MICRO-RISK PORTFELL
13. september 2026 | 205 EUR | MAteckh/nemsis-bot | RESEARCH ONLY

===============================================================================
LOPPVASTUS: HUPOTEES LUKATAKSE TAGASI
===============================================================================

Sinu hupotees oli:
  "Paljude FX paaride skaneerimine + vaga selektiivsed entry'd + range
   risk annab parema risk-adjusted tulemuse kui uksikute paaride
   agressiivne strateegia."

Tulemus: multi-paar portfell EI OLE parem kui uksik paar ega paaride
keskmine. Ja 205 EUR kontol on 0.25% riskiga TAIDETAVAID SIGNAALE NULL.

AGA — uks osa sinu ideest SAI KINNITUST. Vt "OSALINE KINNITUS" allpool.
See on koige tahtsam asi, mis sellest voorust valja tuli.

===============================================================================
MIS OLI UUS (mitte kordus v4-v6-st)
===============================================================================

v4-v6 testisid: "mis juhtub, kui votta KOIK signaalid".
v7 testis:      "mis juhtub, kui votta ainult PARIMAD".
Need on erinevad kusimused. Ma ei korranud 11 500 testi.

UNIVERSUM laiendatud 22 FX-paarini (7 uut laetud: EURNZD, GBPCHF,
GBPCAD, AUDNZD, NZDJPY, CADJPY, CHFJPY). 33 784 signaali.

===============================================================================
1. OTSUSTAV TEST — KAS KVALITEEDISKOOR ENNUSTAB TULEMUST?
===============================================================================

Kvaliteediskoor 6 komponendist, KOIK arvutatud enne sisenemist:
  ATR-i laienemine | trendi joondus | suhteline valuutatugevus
  kulu/ATR suhe    | murde selgus   | ADX

 detsiil  signaale  BRUTO bp  NETO bp  voit%
 -------  --------  --------  -------  -----
    1        3379     -1.41    -5.07   37.9%   <- pohi
    2        3378     +0.21    -3.34   41.7%
    3        3378     -0.52    -4.07   41.5%
    4        3379     +0.35    -3.20   42.8%
    5        3378     +0.28    -3.26   42.7%
    6        3378     -0.29    -3.79   41.4%
    7        3379     -0.21    -3.63   42.4%
    8        3378     +0.04    -3.33   44.5%
    9        3378     -1.13    -4.41   43.0%
   10        3379     +0.05    -3.02   43.8%   <- TOP
 -------  --------  --------  -------  -----
 KOIK       33784     -0.26    -3.71   42.2%

 TOP miinus POHI:  +2.05bp
 TOP vs KOIK:      +0.70bp
 korrelatsioon detsiili ja NETO vahel: +0.368  => EI OLE monotoonne
 TOP-detsiil on ISE miinuses (-3.02bp)

=> selektiivsus ei vii plussi.

===============================================================================
2. OSALINE KINNITUS — SEE ON TAHTIS
===============================================================================

Uksikute filtrite mojul on suund OIGE:

 filter                              signaale  BRUTO bp  NETO bp
 --------------------------------    --------  --------  -------
 koik signaalid                         33784     -0.26    -3.71
 trendi joondus JAH                     20005     +0.10    -3.35
 suht. tugevus kooskolas                23957     -0.14    -3.59
 MOLEMAD kooskolas                      18419     -0.05    -3.50
 MOLEMAD + ATR laienemine                3284     +1.83    -1.52  <--
 molemad + selge murre                   9808     -0.19    -3.57

+1.83bp on PARIM BRUTO NUMBER KOGU PROJEKTIS (v4-v7, ~11 500 testi).
Selektiivsus tostis bruto serva -0.26 -> +1.83, ehk 7x oiges suunas,
kasutades ainult 9.7% signaalidest.

SINU IDEE MEHHANISM TOOTAB. Ta lihtsalt ei ulatu kulubarjaarini:
  bruto serv  +1.83bp
  kulu        -3.35bp
  NETO        -1.52bp
Vaja oleks kulu alla 1.83bp ehk alla 0.92bp poole kohta. Retail-CFD
spread majoritel on 1.0-1.3bp poole kohta. Vahe on ~2x.

===============================================================================
3. TEISED SIGNAALIPEREKONNAD — kas moni reageerib selektiivsusele?
===============================================================================

 perekond                signaale   BRUTO    NETO  TOP-25% NETO   vahe
 --------------------    --------  ------  ------  ------------  -----
 A murre+vol                16160   +0.21   -3.20        -2.88   +0.32
 B trend+tagasitomme        23647   -0.50   -4.00        -4.64   -0.64
 C poore range'is           12245   +0.02   -3.49        -3.10   +0.39
 E sessioonimurre           13665   -0.11   -3.57        -5.13   -1.56
 F surve+momentum           15457   +0.42   -2.88        -4.64   -1.76

=> uheski perekonnas ei anna TOP-25% olulist paranemist. Kolmel viiest
   teeb selektiivsus tulemuse HALVEMAKS.

===============================================================================
4. PUNKT 19 — A vs B vs C VORDLUS
===============================================================================

Sama signaal (24h murre), samad kulud. Erinevus ainult paaride arvus
ja valikus.

 variant                          paare  keskm bp  Sharpe    maxDD  tulu/DD
 -----------------------------    -----  --------  ------  -------  -------
 A) parim uks paar (USDJPY)*          1    +0.07   +0.59    -7.1%     1.67
 B) koik paarid eraldi (keskm)       22    -0.13   -1.65   -23.1%        -
 C1) portfell, koik vordselt         22    -0.13   -3.17   -20.8%     1.08
 C2) portfell TOP-1                   1    -0.07   -0.55   -18.4%     0.62
 C2) portfell TOP-2                   2    -0.13   -1.23   -23.0%     0.95
 C2) portfell TOP-3                   3    -0.12   -1.29   -21.8%     0.97
 C2) portfell TOP-5                   5    -0.11   -1.35   -19.8%     1.01

 * A on OPTIMISTLIK: parim paar valiti kogu perioodi pealt (valikunihe).
   Paris elus seda paari ette ei tea. Aus vordlus on B vs C.

=> C EI OLE parem kui A ega B. Huopotees lukatakse tagasi.

TAHELEPANEK, mis on vastuintuitiivne aga oluline:
 portfelli Sharpe (-3.17) on HALVEM kui uksikute keskmine (-1.65).
 Hajutamine vahendas HAJUVUST (nimetaja), aga keskmine jai negatiivseks
 => negatiivne Sharpe laks veel negatiivsemaks.
 HAJUTAMINE VOIMENDAB NEGATIIVSET SERVA Sharpe motes.
 See on tapselt pohjus, miks portfell ei saa kaotavat strateegiat paasta.

===============================================================================
5. PARIS TAITMINE — 205 EUR, REEGEL "REJECT KUI EI MAHU"
===============================================================================

Sinu reegel: kui arvutatud lot < miinimum, siis TRADE = REJECTED.
MITTE umardada ules. Jargisin seda tapselt.

 205 EUR @ 0.25% risk  =  0.51 EUR lubatud kahjum
 keskmine SL miinimum-lotiga (0.01) = 2.26 EUR = 1.1% kontost
 => 4.4x ULE lubatud piiri

 TAIDETAVAID SIGNAALE:  0 / 33 784  (0.0%)
 TAIDETAVAID PAARE:     0 / 22

 205 EUR @ 0.50% risk (hard max): 1 368 / 33 784 = 4.0%

===============================================================================
6. KAPITALI SKAALEERIMINE — millal piirang kaob?
===============================================================================

Riskiprotsenti EI muudetud. Ainult kapital kasvab.
Arvud = mitu paari 22-st on TAIDETAV.

  kapital    0.25%    0.5%   0.75%    1.0%
    205 EUR   0/22    1/22    3/22   10/22
    250 EUR   0/22    2/22    4/22   15/22
    300 EUR   0/22    3/22   13/22   19/22
    500 EUR   2/22   15/22   21/22   22/22
   1000 EUR  15/22   22/22   22/22   22/22
   2000 EUR  22/22   22/22   22/22   22/22   <- piirang kaob taielikult

Taidetavad signaalid 0.25% riskiga:
    205 EUR      0 / 33 784  (  0.0%)
    500 EUR  3 432 / 33 784  ( 10.2%)
   1000 EUR 23 296 / 33 784  ( 69.0%)
   2000 EUR 33 784 / 33 784  (100.0%)

===============================================================================
7. KAS PROBLEEM ON STRATEEGIAS VOI KONTOSUURUSES?
===============================================================================

VASTUS: MOLEMAS. Ja see on tahtis, sest lootus oli, et ainult kontos.

 205 EUR juures: strateegiat EI SAA uldse kaubelda (0/33 784 signaali)
 2000 EUR juures: koik 33 784 signaali on taidetavad
                  ja strateegia NETO on ikka -3.71bp

=> kapitali parandamine annab TAIELIKULT TAIDETAVA KAOTAVA STRATEEGIA.

Kontosuurus maarab, KAS saad kaubelda.
Strateegia maarab, KAS tasub.
Praegu on vastus esimesele "ei" ja teisele samuti "ei".

===============================================================================
8. LOPPTABEL
===============================================================================

STRATEEGIA          PAARE  TEH/A   NETO bp  SHARPE   maxDD  KESKM RISK  KULU   OOS  205 EUR
-----------------   -----  -----   -------  ------  ------  ----------  ----  ----  -------
A parim uks paar        1    ~90     +0.07   +0.59   -7.1%       1.1%   3.4bp    -  EI
B paarid eraldi        22    ~90     -0.13   -1.65  -23.1%       1.1%   3.4bp    -  EI
C1 portfell koik       22   ~250     -0.13   -3.17  -20.8%       1.1%   3.4bp    -  EI
C2 portfell TOP-1       1    ~90     -0.07   -0.55  -18.4%       1.1%   3.4bp    -  EI
C2 portfell TOP-3       3   ~140     -0.12   -1.29  -21.8%       1.1%   3.4bp    -  EI
parim filter (3284)    22    ~12     -1.52       -       -       1.1%   3.4bp    -  EI

UKSKI ei labi. Pohjused: NETO negatiivne JA 205 EUR teostatavus 0/22.

===============================================================================
9. MIKS SEE VOIKS SIISKI TOOTADA — ainus tee
===============================================================================

Ainus number, mis eraldab sinu ideed toimimisest, on KULU.

  parim filtreeritud bruto serv:  +1.83 bp
  praegune kulu:                  -3.35 bp
  vajalik kulu:                   alla 1.83 bp (ehk alla 0.92bp/pool)

Mida see tahendaks praktikas:
 - ECN-konto raw spreadiga, mitte standard-konto
 - ainult koige likviidsemad paarid (EURUSD, USDJPY, GBPUSD) — ristpaarid
   maksavad 2.2bp/pool ja need tuleks universumist valja jatta
 - kauplemine ainult London/NY kattuvuse ajal, mil spread on kitsaim
 - JA ikka ei ole see toestatud, sest +1.83bp pole labinud walk-forwardi
   ega multiple-testing korrektsiooni

See ei ole soovitus. See on ainus suund, kus arv voiks muutuda.

===============================================================================
10. SEIS
===============================================================================

Live-faile main_v4.py, config.py, mt5_connector.py EI MUUDETUD.
RESEARCH ONLY, nagu sinu punkt 20 noudis.
Juur ja bot/ on sunkroonis. Koik kompileerub.
Bot ootab /update-i — ara saada.
