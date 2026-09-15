```
===============================================================================
NEMSIS — EXIT STRUCTURE FALSIFICATION v1
===============================================================================
  kuupaev 2026-09-15   haru claude/great-noether-um7382
  LIVE PUUTUMATA: main_v4.py, config.py, mt5_connector.py,
  strategy_meanrev.py, backtest.py — git diff on TUHI. /update EI saadetud.
  RESEARCH ONLY. NO LIVE INTEGRATION.

===============================================================================
0. LOPPVERDIKT
===============================================================================

                        FINAL VERDICT:  E) FAIL

  Hupotees "positiivne ootus tuleb VALJUMISSTRUKTUURIST" on FALSIFITSEERITUD.

  Mis tegelikult alles jaab, ei ole valjumismehhanism, vaid KOLM
  triviaalset asja, mis koik on eraldi mooedetud:

  (1) SUUNA ASUMMEETRIA. Juhuslik LONG annab +0.0323 R/tehing,
      juhuslik SHORT annab -0.0001 R/tehing. KOGU "serv" on pikas suunas.
      Valjumisstruktuur on molemal identne — seega EI SAA olla valjumine.

  (2) PAARIDE KONTSENTRATSIOON. MAJORID on NEGATIIVSED (-0.0244 R).
      Positiivsed on JPY- ja AUD-ristid: EURAUD +0.0842, EURJPY +0.0818,
      GBPJPY +0.0798, GBPAUD +0.0613, AUDJPY +0.0565.
      See on tosti 2006-2026 carry- ja trendikorvi kirjeldus, mitte
      valjumisreegel.

  (3) MONOTOONSUS. Tulemus on TP suhtes rangelt monotoonne:
      TP 0.5R = -0.0925  ...  TP 4R = +0.0650. SL-i (0.75..3.0) ja
      hoiuaja (10..60) muutmine EI MUUDA PRAKTILISELT MIDAGI.
      Ei ole "erilist" 2R-eesmarki ega "erilist" 20-baarilist hoidu.
      On ainult asummeetrilise vaartuse R-uhikutes arvestamine positiivse
      kaldega tootlusjaotusel.

  Ja isegi see kaob kulude all: +50% spread viib -0.0047 R-ni,
  +50% spread & 2x libisemine -0.0114 R-ni, +100% spread -0.0226 R-ni.

===============================================================================
1. BASELINE KONTROLL (nouetes sektsioon 4)
===============================================================================

  MOMENTUM baseline   n = 2483   +0.0294 R
     D1 Momentum Validation v1:  n = 2483   +0.0294 R      TAPSELT SAMA

  RANDOM entry + SL 1.5ATR / TP 2R / hold 20 (1000 katset):
     neto   +0.0132 R      bruto +0.0556 R      kulu 0.0424 R
     n = 3 462 134 tehingut, wr 39.4%, PF 1.02
     katsete keskmiste sd 0.0216, 5% -0.0237, 95% +0.0482
     Validation v1 andis +0.0126 R oma seemnejadaga.
     Erinevus +0.0006 R on katsete keskmiste standardvea (0.0007) piires.
     => BASELINE KLAPIB.

  LAHKNEVUS, mis leiti ja lahendati ENNE jatkamist (nouetes sektsioon 4):
     Esimene versioon andis MOMENTUM baseline'iks 2484 tehingut, mitte 2483.
     Pohjus: signaalide nullimine enne 2006 vs tehingute filtreerimine
     kuupaeva jargi. hm_engine simuleerib kogu seeria ja uks-positsioon-
     korraga reegel tahendab, et USDJPY-l 2005. lopus avatud positsioon
     blokeerib 2006-01-04 signaali. Lahendus: simuleeri KOGU seeria ja
     filtreeri TEHINGUD, mitte signaalid. Parast seda: 2483 = 2483.

===============================================================================
2. TEST A — STOP LOSS (TP = 2R, hold = 20)
===============================================================================

  SL          n         wr%   bruto_R   kulu_R   neto_R    PF
  0.75 ATR   1 157 942  36.8  +0.0983   0.0835  +0.0148   1.02
  1.00 ATR   1 036 970  37.0  +0.0822   0.0630  +0.0191   1.03
  1.25 ATR     938 712  38.1  +0.0706   0.0507  +0.0199   1.03
  1.50 ATR     865 826  39.4  +0.0564   0.0424  +0.0140   1.02  <- baseline
  1.75 ATR     811 571  41.0  +0.0486   0.0364  +0.0122   1.02
  2.00 ATR     770 887  42.6  +0.0449   0.0319  +0.0130   1.02
  2.50 ATR     716 036  44.9  +0.0355   0.0256  +0.0099   1.02
  3.00 ATR     683 127  46.5  +0.0294   0.0213  +0.0080   1.02

  1.5 ATR EI OLE ERILINE. Koik kaheksa varianti annavad +0.008..+0.020 R,
  ja katsete keskmiste sd on 0.019-0.022 — see tahendab, et KOGU SL-telje
  varieeruvus on VAIKSEM kui uhe katse juhuslik hajuvus.
  BRUTO kasvab kitsama stopiga (0.0294 -> 0.0983), aga KULU kasvab
  tapselt sama kiiresti (0.0213 -> 0.0835), sest kulu mooedetakse
  R-uhikutes ja kitsam stopp = vaiksem R.

===============================================================================
3. TEST B — TAKE PROFIT (SL = 1.5 ATR, hold = 20)
===============================================================================

  TP          n         wr%   bruto_R    neto_R    PF
  0.50 R    1 158 302  63.0  -0.0508   -0.0925   0.76
  0.75 R    1 075 653  55.4  -0.0245   -0.0665   0.85
  1.00 R    1 010 186  49.8  -0.0012   -0.0433   0.91
  1.25 R      959 445  45.7  +0.0175   -0.0248   0.95
  1.50 R      919 398  42.8  +0.0323   -0.0101   0.98
  2.00 R      865 826  39.4  +0.0564   +0.0140   1.02  <- baseline
  2.50 R      833 885  37.8  +0.0747   +0.0323   1.05
  3.00 R      815 069  37.1  +0.0893   +0.0469   1.08
  4.00 R      796 562  36.5  +0.1073   +0.0650   1.10

  RANGELT MONOTOONNE. 2R ei ole erilist midagi — ta on lihtsalt esimene
  vaartus, kus kulude jarel jouab ulespoole. TP 4R annab 4.6x parema
  tulemuse kui TP 2R.

  MIDA SEE TEGELIKULT TAHENDAB: FX paevatootluste jaotusel on paks
  parem saba. Kui mootad tulemust R-uhikutes (R = SL-kaugus), siis mida
  kaugemale lubad kasumil joosta, seda rohkem sa sellest sabast koristad.
  See EI OLE "serv" — see on tootlusjaotuse kuju umberkirjutamine
  R-uhikutes. Sama efekt tekiks iga hinnaseeria peal, millel on positiivne
  kaldega trendiepisoode.

===============================================================================
4. TEST C — MAX HOLD (SL = 1.5 ATR, TP = 2R)
===============================================================================

  hold        n         wr%   bruto_R    neto_R    PF
   5 baari  1 161 039  47.1  +0.0407   -0.0017   1.00
  10 baari    995 108  44.2  +0.0564   +0.0139   1.03
  15 baari    912 378  41.4  +0.0578   +0.0154   1.03
  20 baari    865 826  39.4  +0.0564   +0.0140   1.02  <- baseline
  30 baari    818 321  37.3  +0.0572   +0.0148   1.02
  40 baari    796 520  36.3  +0.0569   +0.0145   1.02
  60 baari    778 737  35.6  +0.0565   +0.0142   1.02

  20 BAARI EI OLE ERILINE. Alates 10 baarist on tulemus TASANE
  (+0.0139..+0.0154). Ainus erinev on hold=5, mis loikab kasumid enne
  TP-d ara. Hoiuaeg ei ole mehhanism, ta on ainult "piisavalt pikk, et
  TP saaks tabatud".

===============================================================================
5. TEST D — SL x TP GRID (hold = 20), neto R/tehing
===============================================================================

  SL \ TP       1.0R       1.5R       2.0R       2.5R       3.0R
  1.00 ATR   -0.0636    -0.0161    +0.0191    +0.0475    +0.0676
  1.50 ATR   -0.0433    -0.0101    +0.0140    +0.0323    +0.0469
  2.00 ATR   -0.0314    -0.0063    +0.0130    +0.0260    +0.0348
  2.50 ATR   -0.0256    -0.0044    +0.0099    +0.0195    +0.0260

  positiivseid ruute 12/20, vahemik -0.0636 .. +0.0676 R

  PIND ON SILE JA MONOTOONNE — ei ole uksikuid positiivseid ruute
  (mis oleks overfit'i hoiatus), vaid tervikuna korrastatud pind, kus
  KOIK TP >= 2R ruudud on positiivsed ja KOIK TP <= 1.5R ruudud
  negatiivsed. SL-telg on sekundaarne ja monotoonne.

  See on hea uudis metoodikale (ei ole muraruudud) ja HALB uudis
  hupoteesile: sile monotoonne pind tahendab, et tegu on UHE pideva
  nahtusega (payoff'i asummeetria), mitte "leitud struktuuriga".

===============================================================================
6. TEST E — HOLD x TP GRID (SL = 1.5 ATR)
===============================================================================

  hold \ TP     1.0R       2.0R       3.0R
  10         -0.0432    +0.0139    +0.0381
  20         -0.0433    +0.0140    +0.0469
  40         -0.0431    +0.0145    +0.0492

  HOLD-telg on praktiliselt LAME (erinevus 0.0001-0.011), TP-telg
  domineerib taielikult. Ajaline valjumine ei ole mehhanism.

===============================================================================
7. LONG vs SHORT — KOIGE PALJASTAVAM TULEMUS
===============================================================================

  suund            n         wr%   bruto_R    neto_R    PF
  LONG + SHORT  3 462 134   39.4   +0.0556   +0.0132   1.02
  ainult LONG   3 452 250   40.2   +0.0747   +0.0323   1.05
  ainult SHORT  3 472 714   38.7   +0.0423   -0.0001   1.00

  VALJUMISSTRUKTUUR ON MOLEMAL SUUNAL IDENTNE. Kui positiivne ootus
  tuleks valjumisest, peaks LONG ja SHORT andma sama tulemuse.
  Nad ei anna: LONG +0.0323, SHORT -0.0001.

  => Efekt EI TULE valjumisstruktuurist. Ta tuleb sellest, et nendel
     15 paaril 2006-2026 oli PIKAL suunal positiivne nihe (carry ja
     trend JPY- ning AUD-ristides).

===============================================================================
8. PAARID JA GRUPID (baseline exit, juhuslik sisenemine)
===============================================================================

  paar           n      wr%    neto_R    PF
  EURAUD     208 298   41.2   +0.0842  1.14
  EURJPY     252 343   40.4   +0.0818  1.14
  GBPJPY     261 291   40.1   +0.0798  1.13
  GBPAUD     212 193   40.4   +0.0613  1.10
  AUDJPY     228 082   39.1   +0.0565  1.09
  EURGBP     234 510   38.5   +0.0176  1.03
  EURCHF     244 828   40.5   +0.0035  1.01
  USDJPY     237 980   39.6   -0.0027  1.00
  EURUSD     224 695   39.3   -0.0221  0.96
  NZDUSD     226 373   38.5   -0.0237  0.96
  AUDCAD     232 692   37.8   -0.0240  0.96
  AUDUSD     211 391   38.8   -0.0271  0.95
  GBPUSD     217 637   39.0   -0.0296  0.95
  USDCAD     236 409   38.8   -0.0310  0.95
  USDCHF     233 412   38.5   -0.0358  0.94

  positiivseid paare 7/15, mediaan -0.0027 R

  grupp            n        neto_R    PF
  ALL         3 462 134    +0.0132   1.02
  MAJORS      1 587 897    -0.0244   0.96   <- NEGATIIVSED
  CROSSES     1 874 237    +0.0450   1.07
  JPY           979 696    +0.0549   1.09
  EUR         1 164 674    +0.0328   1.05
  COMMODITY   1 555 438    +0.0125   1.02

  Seitse koige likviidsemat paari on NEGATIIVSED. Positiivne on ainult
  ristide alamhulk. Valjumisreegel on koigil identne.

===============================================================================
9. AJAPERIOODID — EFEKT VAHENEB MONOTOONSELT
===============================================================================

  periood              n        wr%    neto_R    PF
  2006-2010        882 364     38.1   +0.0256  1.04
  2011-2015        823 623     39.7   +0.0123  1.02
  2016-2020        830 917     39.7   +0.0093  1.02
  2021-2026        925 230     40.0   +0.0054  1.01
  TRAIN 2006-2013 1 376 218    38.6   +0.0231  1.04
  VALID 2014-2017   662 270    40.0   +0.0158  1.03
  OOS   2018-2026 1 423 646    39.8   +0.0023  1.00
  ALL   2006-2026 3 462 134    39.4   +0.0132  1.02

  2006-2010 +0.0256  ->  2021-2026 +0.0054. Viiekordne vahenemine.
  OOS 2018-2026 on +0.0023 R — kulude (0.0424 R) korval PRAKTILISELT NULL.
  Kui see oleks struktuurne valjumisomadus, ei tohiks ta ajas kaduda.

===============================================================================
10. REZHIIMID
===============================================================================

  rezhiim                     n        neto_R    PF
  HIGH_VOLATILITY [ALL]   1 413 306   +0.0190  1.03
  HIGH_VOLATILITY [OOS]     554 698   -0.0001  1.00
  LOW_VOLATILITY  [ALL]   2 023 470   +0.0091  1.02
  LOW_VOLATILITY  [OOS]     868 948   +0.0038  1.01
  TRENDING        [ALL]   1 468 626   +0.0202  1.03
  TRENDING        [OOS]     501 411   -0.0088  0.98
  RANGING         [ALL]   1 302 645   +0.0125  1.02
  RANGING         [OOS]     601 863   +0.0082  1.01

  OOS-perioodil on KOIK NELI rezhiimi sisuliselt nullis (-0.0088..+0.0082),
  kulu on 0.0424. Rezhiim ei paasta midagi.

===============================================================================
11. KULUSTRESS — SIIN SEE SUREB
===============================================================================

  variant                    kulu_R    neto_R    PF
  BASE                       0.0424   +0.0132   1.02
  spread +25%                0.0514   +0.0042   1.01
  spread +50%                0.0603   -0.0047   0.99   <- NEGATIIVNE
  slippage 2x                0.0490   +0.0065   1.01
  spread +50% & slip 2x      0.0669   -0.0114   0.98   <- NEGATIIVNE
  spread +100%               0.0782   -0.0226   0.96   <- NEGATIIVNE
  kulu = 0                   0.0000   +0.0556   1.10

  Kogu "serv" (+0.0132 R) on VAIKSEM kui kulu ise (0.0424 R) ja kaob
  juba +25%..+50% spreadi juures. See on FRAGILE definitsiooni jargi.

===============================================================================
12. DRAWDOWN — KORREKTSELT ARVUTATUD
===============================================================================

  METOODILINE MARKUS: tabelites naidatud maxDD ~ -100% tuleneb sellest,
  et 1000 soltumatut katset on jarjestikku liidetud. See EI OLE
  tolgendatav. Oige DD arvutatakse IGA KATSE SEES kronoloogiliselt.

  200 katset, risk 1% tehingu kohta:
     maxDD mediaan       -53.5%
     5% kvantiil         -79.0%
     halvim              -87.2%
     P(maxDD > 20%)      100.0%

  Iga uksik "maailm" labib ule 20% drawdowni 100% juhtudest.

===============================================================================
13. JUHUSLIKKUSE JAOTUS (1000 katset variandi kohta)
===============================================================================

  variant                  keskm   mediaan     sd       5%       95%      min      max
  BASELINE SL1.5/TP2/h20  +0.0132  +0.0128  0.0216  -0.0237  +0.0482  -0.0750  +0.0799
  SL 1.0                  +0.0175  +0.0168  0.0213  -0.0172  +0.0516  -0.0504  +0.0980
  SL 3.0                  +0.0076  +0.0066  0.0185  -0.0211  +0.0393  -0.0574  +0.0627
  TP 1R                   -0.0436  -0.0436  0.0149  -0.0671  -0.0183  -0.0927  +0.0060
  TP 4R                   +0.0644  +0.0636  0.0276  +0.0210  +0.1111  -0.0426  +0.1652
  hold 5                  -0.0027  -0.0024  0.0134  -0.0243  +0.0196  -0.0376  +0.0508
  hold 60                 +0.0126  +0.0120  0.0252  -0.0278  +0.0554  -0.0674  +0.0886

  Baseline'i 5% kvantiil on -0.0237 R: iga kahekumnes juhuslik maailm
  on selle valjumisstruktuuriga MIINUSES.

===============================================================================
14. ENTRY vs EXIT — LAHUTUS
===============================================================================

  variant                                   n         neto_R
  A) RANDOM entry + baseline exit      3 462 134     +0.0132
  B) MOMENTUM entry + baseline exit        2 483     +0.0294
  B - A (MOMENTUM panus)                       -     +0.0163
  C) RANDOM entry + SL 1.0             1 036 970     +0.0191
  C) RANDOM entry + SL 3.0               683 127     +0.0080
  C) RANDOM entry + TP 1R              1 010 186     -0.0433
  C) RANDOM entry + TP 4R                796 562     +0.0650
  C) RANDOM entry + hold 5             1 161 039     -0.0017
  C) RANDOM entry + hold 60              778 737     +0.0142

  MOMENTUM sisenemise panus: +0.0163 R/tehing.
  AGA: MOMENTUM tulemus (+0.0294) asub juhuslike katsete jaotuses
  PROTSENTIILIL 76.2  =>  empiiriline p = 0.238.
  Sisenemissignaal EI LISA statistiliselt tuvastatavat vaartust —
  see kinnitab D1 Momentum Validation v1 tulemust (p = 0.26).

  Samas: VALJUMISE muutmine TP 1R -> TP 4R liigutab tulemust
  -0.0433 -> +0.0650, st 0.108 R. See on 6.6x suurem kui MOMENTUM
  sisenemise panus (+0.0163). VALJUMINE MAARAB ROHKEM KUI SISENEMINE —
  aga mitte sellepargi, et valjumises oleks serv, vaid sellepargi, et
  valjumine maarab, kui palju tootlusjaotuse sabast R-uhikutesse jouab.

===============================================================================
15. MITME TESTIMISE ARVESTUS
===============================================================================

  valjumisvariante:  53  (SL 8, TP 9, HOLD 7, SLxTP 20, HOLDxTP 9)
  + suund 3, paare 15, gruppe 6, perioode 8, rezhiime 8, kuluvariante 7
  juhuslikke katseid: baseline/kulud/suund/jaotus 1000,
                      variandigridid 250 (nested, SAMAD sisenemised)
  positiivseid variante: 36/53
  BH q=0.05 ule 53 variandi: labis 53, neist positiivseid 36
  Bonferroni lavi: 0.000943

  HOIATUS, mis on siin kohustuslik: n on 250-1000 x tegelik tehingute arv,
  sest iga katse annab oma tehingukomplekti. Seetottu on t-vaartused
  paisutatud faktoriga ~sqrt(250) = 16 kuni sqrt(1000) = 32. SISULINE
  hajuvus on KATSETE KESKMISTE sd (veerg katse_sd, 0.011-0.029),
  MITTE p-vaartus. Uhtegi p < 0.05 vaidet ei tohi siin teha ja ma ei tee.
  BH "labis 53/53" on selle paisutuse artefakt, mitte leid.

===============================================================================
16. VASTUSED 12 KUSIMUSELE
===============================================================================

   1. KAS RANDOM ENTRY + EXIT ON POSITIIVNE?
      Baaskulude juures jah: +0.0132 R/tehing (katsete sd 0.0216).
      +50% spreadi juures EI (-0.0047). OOS 2018-2026 +0.0023 = null.

   2. MILLINE OSA EXITIST SELLE POHJUSTAB?
      TAKE PROFIT, ja ainult tema. TP 0.5R -> 4R liigutab tulemust
      -0.0925 -> +0.0650. SL (0.75-3.0) ja hold (10-60) on praktiliselt
      lamedad. Aga see "pohjus" ei ole mehhanism — see on asummeetrilise
      vaartuse R-uhikutes arvestamine positiivse sabaga jaotusel.

   3. KAS 2R TP ON ERILINE?
      EI. Pind on rangelt monotoonne. 2R on lihtsalt esimene vaartus,
      kus kulude jarel ulatub ulespoole. 4R on 4.6x parem.

   4. KAS 20-BAARILINE HOLD ON ERILINE?
      EI. 10-60 baari annavad +0.0139..+0.0154 (erinevus 0.0015,
      katsete sd 0.014-0.026). Ainult hold=5 on erinev (-0.0017).

   5. KAS 1.5 ATR SL ON ERILINE?
      EI. 0.75-3.00 ATR annavad +0.0080..+0.0199. Kogu SL-telje
      varieeruvus (0.012) on VAIKSEM kui uhe katse hajuvus (0.019-0.022).

   6. KAS POSITIIVNE ALA ON LAI VOI UKSIKUD RUUDUD?
      LAI JA SILE: 12/20 ruutu positiivsed, korrastatud monotoonselt
      TP jargi. Metoodiliselt on see hea (ei ole muraruudud), aga
      sisuliselt tahendab see, et tegu on UHE pideva nahtusega.

   7. KAS TULEMUS PUSIB 2006-2026 PERIOODIDEL?
      EI. Monotoonne vahenemine: +0.0256 (2006-10) -> +0.0054 (2021-26).

   8. KAS TULEMUS PUSIB OOS-IS?
      Praktiliselt EI. OOS 2018-2026 = +0.0023 R kulu 0.0424 R korval.

   9. KAS TULEMUS PUSIB ERINEVATEL PAARIDEL?
      EI. 7/15 positiivseid, mediaan -0.0027. MAJORID on negatiivsed
      (-0.0244). Positiivne on ainult JPY/AUD-ristide alamhulk.

  10. KAS TULEMUS PUSIB KULUDE HALVENEMISEL?
      EI. +50% spread => -0.0047. +100% => -0.0226. FRAGILE.

  11. KUI PALJU LISAB MOMENTUM ENTRY?
      +0.0163 R/tehing nominaalselt, AGA protsentiil 76.2 juhuslike
      katsete jaotuses (p = 0.238) — statistiliselt mitte midagi.

  12. KAS NEMSIS PEAKS EXIT STRUCTURE'I EDASI UURIMA?
      EI SELLEL KUJUL. Kolm asja on nuud toestatud ja need sulgevad tee:
      (a) efekt on ainult pikas suunas (LONG +0.0323, SHORT -0.0001)
      (b) efekt on ainult ristides (MAJORID -0.0244)
      (c) efekt vaheneb ajas ja on OOS-is null
      Valjumisstruktuur on koigil kolmel juhul IDENTNE, seega ta ei saa
      olla pohjus.

===============================================================================
17. METOODILINE REEGEL (nouetes sektsioon 24)
===============================================================================

  EI UTLE: "Leidsime strateegia."
  EI UTLE ISEGI: "Leidsime potentsiaalse exit-mehhanismi."

  UTLEN: valjumisstruktuuri hupotees on FALSIFITSEERITUD. Positiivne
  ootus, mida D1 Momentum Validation v1 juhusliku sisenemise juures
  nagi (+0.0126 R), ei ole valjumismehhanism. See on pikas suunas
  JPY/AUD-ristides 2006-2026 esinenud nihe, mis on ajas kahanenud
  nullini ja mis kaob 25-50% suurema spreadi juures.

===============================================================================
18. AUDIT (bot/exit_audit.py — 23 kontrolli, 0 viga)
===============================================================================

  ANDMEALLIKAS   bot/data/{PAAR}_d25.csv (Yahoo paevane close, sama
                 load_yahoo_bars nagu kogu NEMSIS-is); ristid, millel
                 ei ole oma faili, arvutatakse USD-jalgadest
  VAHEMIKUD      AUDUSD/AUDJPY/EURAUD/GBPAUD/AUDCAD 2006-05-15 ->
                 EURUSD/GBPUSD/NZDUSD/EURGBP/EURJPY/GBPJPY/EURCHF 2003-12-01 ->
                 USDCAD/USDCHF 2003-09-16 ->   USDJPY 2001-09-10 ->
                 koik kuni 2026-09-10/13; sisenemised AINULT 2006-01-01 ->
  SISENEMINE     juhuslik baar lubatud hulgast (ATR olemas, kuupaev >= 2006),
                 kandidaate = 1.3 x sama paari MOMENTUM signaalide arv,
                 suund juhuslik +-1 (voi fikseeritud long/short testis)
  SL VALEM       sl_atr x ATR(14) signaalibaaril, ATR = Wilder
  TP VALEM       tp_r x SL-kaugus
  HOLD           max_hold baari, siis valjumine sulgemishinnaga
  SAMA-BAARI     kui SL ja TP tabatakse uhes baaris => loetakse SL
  KULUD          spread hm_engine.KULU_BP (1.0-2.2 bp) + 0.3 bp libisemine,
                 kulu_R = 2 x (spread+slip)/1e4 x sisenemishind / SL-kaugus
  LOOKAHEAD      sisenemine JARGMISE baari avahinnaga; audit A6: seeria
                 viimased 50 baari korrutati 3-ga ja varasemad tehingud
                 jaid identseks
  PUUDUV ANDME   paar alla 500 baari => INSUFFICIENT DATA (ei olnud uhtegi)
  TEHINGUID      baseline 3 462 134 (1000 katset), MOMENTUM 2483
  KATSEID        1000 (baseline, kulud, suund, jaotus),
                 250 (SL/TP/HOLD/gridid, nested ja PAARITUD)
  SEEME          20260915 koigis testides
  KORDATAVUS     kordusjooks andis identsed md5 summad (vt sektsioon 19)

  A2  KIIRE SIMULAATOR == hm_engine.simuleeri:
      0 tehingut ja 0.00e+00 R erinevust KOIGIL 15 paaril
  A3  teadaoleva vastusega testid: TP => +2.000000 R, SL => -1.000000 R,
      TP 3R => +3.000000 R, SL ja TP samas baaris => SL
  A4  kulu=0 => neto==bruto; spread 2x => kulu 0.0217 -> 0.0384 R
  A5  sama seeme => identsed sisenemised; 1.3x kandidaate (6289 vs 4843)
  A7  MOMENTUM baseline 2483 tehingut, +0.0294 R == Validation v1 TAPSELT

===============================================================================
19. FAILID
===============================================================================
  EXIT_STRUCTURE_REPORT.md          see raport
  EXIT_SL_RESULTS.csv               8 SL-varianti
  EXIT_TP_RESULTS.csv               9 TP-varianti
  EXIT_HOLD_RESULTS.csv             7 hoiuaega
  EXIT_SL_TP_GRID.csv               20 kombinatsiooni
  EXIT_HOLD_TP_GRID.csv             9 kombinatsiooni
  EXIT_DIRECTION_RESULTS.csv        long / short / molemad
  EXIT_PAIR_RESULTS.csv             15 paari + 6 gruppi
  EXIT_PERIOD_RESULTS.csv           8 perioodi
  EXIT_REGIME_RESULTS.csv           4 rezhiimi x ALL/OOS
  EXIT_COST_STRESS.csv              7 kuluvarianti
  EXIT_RANDOM_BENCHMARK.csv         7 varianti x 1000 katse jaotus
  EXIT_ENTRY_VS_EXIT.csv            entry- ja exit-panuse lahutus
  EXIT_SL_TP_HEATMAP.png            SL x TP, neto R/tehing + n
  EXIT_HOLD_TP_HEATMAP.png          HOLD x TP, neto R/tehing + n

  kood: bot/exit_structure_falsification.py
        bot/exit_audit.py
        bot/exit_plot.py
  jooksutamine:
    python3 bot/exit_audit.py
    python3 bot/exit_structure_falsification.py
    python3 bot/exit_plot.py

===============================================================================
20. JARGMINE KOIGE MOISTLIKUM NEMSIS-I UURIMISKUSIMUS
===============================================================================

  See uuring paljastas midagi, mis puudutab KOIKI senist ~11 700 testi:

    JUHUSLIK PIKK POSITSIOON JPY/AUD-RISTIDES ANDIS 2006-2026
    +0.0323 R/TEHING. NULL EI OLE NULL.

  Iga seni tehtud test on vordelnud strateegiat NULLIGA. Aga oige
  vordlusalus ei ole null — see on "mida oleks andnud sama riskiga
  suvaline pikk positsioon samadel paaridel samal perioodil".

  JARGMINE KUSIMUS:
    "Ehita NEMSIS-i AUS BENCHMARK: suunaneutraalne ja carry-neutraalne
     vordlusalus, mille vastu iga tulevane strateegia peab voitma.
     Seejarel jooksuta KOIK senised leiud (COT A_REV, kalendri surprise,
     D1 Momentum, Heat Map top-10) selle benchmarki vastu ja vaata,
     kui palju neist jaab alles."

  See on odav (andmed olemas, mootorid olemas) ja see on ainus kusimus,
  mis voib seletada, miks 11 700 testi on andnud jarjekindlalt
  "midagi vaikest positiivset, mis kaob kulude all" — nimelt sellepargi,
  et need koik motavad osaliselt sama pikka nihet.

===============================================================================
                        FINAL VERDICT:  E) FAIL
===============================================================================
```
