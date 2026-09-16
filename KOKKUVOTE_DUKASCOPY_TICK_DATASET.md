```
===============================================================================
NEMSIS - DUKASCOPY TICK DATASET SUB-60 TESTI JAOKS
===============================================================================
  16. september 2026   |   haru: claude/great-noether-um7382
  SEE EI OLE STRATEEGIATEST. P/L-i EI ARVUTATUD, signaali ei genereeritud.
  Ainus kusimus: KAS ANDMED ON OLEMAS.

-------------------------------------------------------------------------------
1. LOPPTULEMUS
-------------------------------------------------------------------------------

  TIER 1 |z|>=1 sundmusi sihiks .......... 30
  TIER 1 |z|>=1 sundmusi KAETUD .......... 30   (30/30 = 100%)

  PEATUSIN KOHE, nagu kask nois. Rohkem ei laadinud.

  Paevi ................................. 16
  Sumbol-paevi (tick-CSV-sid) ........... 47
  Sumboleid ............................. 7
  .bi5 faile ............................ 303
  Tikke kokku ........................... 1 276 957
  Ketta maht ............................ 74,4 MB (gitignore'itud)

-------------------------------------------------------------------------------
2. EELREGISTREERITUD VALIK (tehtud ENNE allalaadimist)
-------------------------------------------------------------------------------

  Reegel, kirja pandud failis bot/dukascopy_plan.py:

    1. Kandidaatpaev = paev, millel on vahemalt uks TIER 1 kalendrisundmus,
       mille |z| >= 1 ja mille valuuta on kaardistatav 7 major-paarile.
    2. Paevad voetakse POORD-KRONOLOOGILISELT varskeimast. Ei mingit
       valikut "kus tulemus ilusam".
    3. Peatumine: kui kumulatiivne sundmuste arv >= 30, nimekiri loppeb.
    4. Tunnid: koigi selle paeva TIER 1 sundmuste {h-1, h, h+1}. Ka need
       sundmused, mille |z| < 1 - see on KONTROLLGRUPP, voetud kaasa siin,
       et hilisem test ei saaks kontrollgruppi tagantjarele valida.
    5. Sumbolid: koik 7 majorit, igal paeval samad.

  Plaan: 16 paeva, 85 tundi, 595 sumbol-tundi.
  Failid: SUB60_TICK_PLAAN.csv, SUB60_TICK_PLAAN.json

  Prioriteet 1 = sundmuse ENDA kaardistatud paar tundidel {h-1, h}.
  Ainult see on peatumisreegli jaoks noutud: 42 sumbol-tundi.
  Prioriteet 2 = ulejaanud 6 majorit samadel tundidel (kontekst, mitte noue).

  Prioriteet 1: 42 / 42 alla laetud  (100%)
  Prioriteet 2: 121 / 553 alla laetud (22%) - allikas droseldas, vt osa 6

-------------------------------------------------------------------------------
3. KATVUS SUNDMUSTE KAUPA
-------------------------------------------------------------------------------

  Kriteerium, fikseeritud ENNE andmete vaatamist:
    eelmine tick <= 60 s enne release'i JA
    jargmine tick <= 5 s parast release'i JA
    aknas 0..+60 s vahemalt 1 tick

  aeg UTC             paar        z    eel s   jarg s   +1s   +5s  +60s  kaetud
  ------------------  ------  ------  -------  -------  ----  ----  ----  ------
  2026-07-14 12:30    EURUSD   -1.57    0.009    0.044    16    79   742  JAH
  2026-07-14 12:30    EURUSD   -2.62    0.009    0.044    16    79   742  JAH
  2026-07-14 12:30    EURUSD   -3.29    0.009    0.044    16    79   742  JAH
  2026-07-20 12:30    USDCAD   -1.21    0.028    0.074    13    42   170  JAH
  2026-07-23 01:30    AUDUSD    1.82    0.044    0.110    13    56   303  JAH
  2026-07-24 06:00    GBPUSD    1.39    0.034    0.170     7    36   120  JAH
  2026-07-24 06:00    GBPUSD    1.63    0.034    0.170     7    36   120  JAH
  2026-07-29 01:30    AUDUSD   -1.02    0.036    0.167    12    62   485  JAH
  2026-07-30 09:00    EURUSD    2.91    0.291    0.420     1     3    50  JAH
  2026-07-30 09:00    EURUSD    1.69    0.291    0.420     1     3    50  JAH
  2026-07-30 09:00    EURUSD    1.21    0.291    0.420     1     3    50  JAH
  2026-07-30 12:30    EURUSD   -1.08    0.021    0.086     4    23   257  JAH
  2026-07-30 23:50    USDJPY   -2.29    0.032    0.122     3     5    75  JAH
  2026-07-31 09:00    EURUSD    1.06    0.301    0.056     8    26   286  JAH
  2026-08-04 22:45    NZDUSD    1.06    0.931    0.026    10    18   144  JAH
  2026-08-06 09:00    EURUSD   -2.45    0.082    0.021     2     5    36  JAH
  2026-08-07 12:30    EURUSD   -1.03    0.016    0.036     7    63   661  JAH
  2026-08-07 12:30    EURUSD   -1.48    0.016    0.036     7    63   661  JAH
  2026-08-07 12:30    USDCAD    1.14    0.083    0.025     4    49   571  JAH
  2026-08-14 12:30    EURUSD   -2.23    0.035    0.017    13    55   372  JAH
  2026-08-26 01:30    AUDUSD    1.08    0.296    0.422     7    41   311  JAH
  2026-09-01 09:00    EURUSD    1.17    0.076    0.029     1     7    66  JAH
  2026-09-01 09:00    EURUSD   -1.06    0.076    0.029     1     7    66  JAH
  2026-09-03 06:30    USDCHF    2.37    0.068    0.037    12    50   212  JAH
  2026-09-03 06:30    USDCHF    3.15    0.068    0.037    12    50   212  JAH
  2026-09-04 09:00    EURUSD   -1.03    4.716    0.074     4     6    50  JAH
  2026-09-04 09:00    EURUSD   -5.20    4.716    0.074     4     6    50  JAH
  2026-09-04 12:30    USDCAD   -1.06    0.022    0.080     6    43   669  JAH
  2026-09-04 12:30    EURUSD    1.52    0.031    0.023    10    64   683  JAH
  2026-09-07 09:00    EURUSD    1.60    0.306    3.663     0     3    38  JAH

  KOKKUVOTVALT:
    eelmine tick enne release'i: mediaan 0,056 s, halvim 4,716 s
    jargmine tick parast        : mediaan 0,065 s, halvim 3,663 s
    aknas 0..+ 1 s: mediaan  7 tikki, halvim  0
    aknas 0..+ 5 s: mediaan 38 tikki, halvim  3
    aknas 0..+60 s: mediaan 212 tikki, halvim 36

  AUS MARKUS - kaks nork kohta, mis labisid kriteeriumi, aga vaevu:
    2026-09-04 09:00 EURUSD: eelmine tick 4,716 s enne. Release'ieelne
      hind on seega kuni 4,7 s vana.
    2026-09-07 09:00 EURUSD: jargmine tick 3,663 s parast, aknas 0..+1 s
      NULL tikki. Selle sundmuse puhul EI SAA 1-sekundilist akent moota.
    Neid EI TOHI hiljem vaikselt valja visata ega sisse jatta selle jargi,
    kummal pool tulemus ilusam on. Nad on siin kirjas ette.

-------------------------------------------------------------------------------
4. ANDMEKVALITEET
-------------------------------------------------------------------------------

  sha256 klapib (allika baidid vs kettal) ....... 303 / 303
  failisuurus klapib ............................ 303 / 303
  negatiivseid spread'e (ask < bid) ............. 0
  bid <= 0 ...................................... 0
  ask <= 0 ...................................... 0
  duplikaate parast dedup'i ..................... 0
  valideerimiskontrolle ......................... 27, neist FAIL 0

  sumbol    spread mediaan   paevi       tikke
  --------  --------------  ------  ----------
  AUDUSD          0,90 pip       7     143 729
  EURUSD          0,30 pip      13     203 075
  GBPUSD          0,60 pip       6     187 843
  NZDUSD          1,00 pip       5     135 218
  USDCAD          1,10 pip       5     139 101
  USDCHF          0,80 pip       5     150 337
  USDJPY          0,40 pip       6     317 654

  paev          sumboleid       tikke
  ------------  ---------  ----------
  2026-07-14            7     168 915
  2026-07-20            7     101 263
  2026-07-23            5      54 017
  2026-07-24            2      13 054
  2026-07-29            1       8 094
  2026-07-30            2      27 706
  2026-07-31            1       9 550
  2026-08-04            1       2 028
  2026-08-06            1       3 769
  2026-08-07            7     138 292
  2026-08-14            1       7 124
  2026-08-26            1       5 124
  2026-09-01            1       6 017
  2026-09-03            7     693 586
  2026-09-04            2      29 328
  2026-09-07            1       9 090

-------------------------------------------------------------------------------
5. KAKS VAIKSET VIGA, MIS LEITI JA PARANDATI
-------------------------------------------------------------------------------

  VIGA 1 - ingest kaotas iga ekspordi ESIMESE JA VIIMASE faili
    dukascopy_ingest.py otsis ridu mustriga ^...$ rea kaupa. MCP
    tulemusefailis on esimene andmerida liidetud JSON-i eesliitega
    ([{"csv":") ja viimane jareliitega ("}]), sest saatetekst sisaldab
    ise <untrusted-data-...> tagi, mille tottu JSON-i eraldamine
    ebaonnestub ja langetakse tooreks tekstiks.
    MOOEDETUD: 86 rida andmebaasis -> 83 sisse loetud. Vaikselt.
    PARANDUS: labiv re.finditer ilma reaankruteta. Base64-tahestikus
    ei ole '|', seega muster on uheselt maaratud.
    KONTROLL PARAST: 135 rida andmebaasis -> 135 sisse loetud.

  VIGA 2 - ebaonnestunud kordus rikkus korras rea metaandmed
    Postgresi ON CONFLICT DO UPDATE hoidis vana raw-i (coalesce), AGA
    kirjutas http_status / file_size / sha256 ule ebaonnestunud katse
    omadega. Tulemus: rida, kus on 8091 parisbaiti, aga status = 599,
    file_size = 0 ja sha256 = NULL. Baidid olid alles, kuid neid EI
    SAANUD enam verifitseerida, ja eksport jattis rea vaikselt valja.
    MOOEDETUD: AUDUSD 2026-07-23 tund 00.
    PARANDUS: metaandmeid uuendatakse ainult siis, kui uus katse toi
    baidid. Rikutud rida kustutati ja laeti ausalt uuesti.

  KOLMAS, vahem ohtlik: kirjuta_csv kirjutas faili "w"-ga ule. Kui sama
  paeva ingestiti osade kaupa, kustutas teine jooks esimese tunnid ara.
  Nuud LIIDAB olemasoleva failiga; dedup-voti (ts, bid, ask) hoiab
  tulemuse uheseks. Idempotentsus kontrollitud: kaks jarjestikust
  jooksu annavad baithaaval identsed CSV-d.

-------------------------------------------------------------------------------
6. MIKS AINULT 22% PRIORITEET-2 FAILIDEST
-------------------------------------------------------------------------------

  Allikas (datafeed.dukascopy.com) piirab paringute MAARA ajas.
  Mooedetud kaitumine:
    ~12 paringut puhangu kohta labib
    21 paringut (7 sumbolit x 3 tundi) jarjest -> HTTP 503
    tugevama koormuse all lakkab ta hoopis vastamast (paring ripub
    >9 s, meie ajalimiit margib selle koodiga 599)
  Jahtumisaeg ~90 s taastab teenuse.

  See EI takista sub-60 testi: peatumisreegel nouab ainult sundmuse enda
  paari, ja see on 42/42 olemas. Ulejaanud 6 majorit on kontekst.
  Kui neid hiljem vaja, jooksuta lihtsalt uuesti - fetch_bi5_plaan on
  idempotentne ja taidab tapselt augud.

-------------------------------------------------------------------------------
7. MIS MUUTUS TARISTUS (ja miks)
-------------------------------------------------------------------------------

  PROBLEEM: Edge Function 'dukascopy-bi5' nois Supabase JWT-d
  (verify_jwt = true). Selles sessioonis ei paasenud ma projekti
  anon/service votmele ligi ja otsene valjapaas Dukascopysse on kinni
  (CONNECT 403). Ilma votmeta ei saanud midagi laadida.

  SINU OTSUS: "Deploy v4: oma saladus".

  TEHTUD:
    - Postgresi vaultis genereeriti 32 juhuslikku baiti (nimi
      'dukascopy_token'). MA EI NAINUD SEDA VAARTUST KUNAGI - genereerisin
      selle SQL-is ja kusisin valja ainult SHA-256 raisi.
    - Edge Function v6, verify_jwt = false, kontrollib ise paist
      'x-nemsis-token', vorreldes selle SHA-256 koodis oleva raisiga
      konstantse ajaga. Funktsiooni koodis on AINULT rais.
    - fetch_bi5_hours loeb tokeni ise vaultist. Ukski SQL-parring, mille
      ma kirjutasin, ei sisalda tokenit.
    - Path-allowlist jai alles: ainult GET, ainult datafeed.dukascopy.com,
      ainult ajalooline tick-rada. Avatud proxy'ks teha ei saa.

  TURVAKONTROLL, TEHTUD JA MOOEDETUD:
    ilma tokenita ..... HTTP 401 {"error":"unauthorized"}
    vale tokeniga ..... HTTP 401 {"error":"unauthorized"}
    vaulti tokeniga ... HTTP 200, failid tulevad

  KAALUTLUS: anon key on Supabase disaini jargi AVALIK string (laheb
  brauseri JS-i sisse). 32 juhuslikku baiti, mida hoitakse ainult
  vaultis, on rangelt tugevam kui avalik string.
  TAGASIPOORATAV: redeploy verify_jwt = true.

-------------------------------------------------------------------------------
8. TURVALEID, MIS EI OLE MINU TOOST - PARANDA ISE
-------------------------------------------------------------------------------

  Failis DEPLOY.md rida 50 on PARIS Supabase secret key, mis on juba
  gitis sees (commit 10ab696). Ma ei tekitanud seda ega prindi siia
  selle vaartust.

  See on ajaloos, seega failist kustutamine UKSI EI AITA.

  MIDA TEHA:
    1. Roteeri see voti Supabase dashboardis (Settings -> API Keys).
       Vana voti muutub kehtetuks.
    2. Alles seejarel eemalda rida DEPLOY.md-st ja pane sinna
       kohatait, nt: SUPABASE_KEY = <keskkonnamuutujast>.

  Minu selle jooksu failides saladusi ei ole - kontrollitud.

-------------------------------------------------------------------------------
9. MIDA MA EI TEINUD (sinu keeldude jargi)
-------------------------------------------------------------------------------

  EI muutnud live boti koodi. Kontrollitud iga faili kohta:
    main_v4.py, config.py, mt5_connector.py, strategy_meanrev.py,
    backtest.py, gold_logic.py, strategies.py
    git diff = 0 rida, juur vs bot/ diff = 0 rida.
  EI saatnud /update. EI deploy'nud botti.
  EI testinud strateegiat. EI arvutanud uhtegi tootlust.
  EI commit'inud tooreid tick-andmeid (bot/data/* on gitignore'itud,
    kontrollitud git check-ignore'iga).
  EI salvestanud sinu votmeid ega paroole kuhugi.
  EI kasutanud tasulist teenust.
  EI fabritseerinud andmeid - iga bait on sha256-ga allika vastu
    kontrollitud.
  EI laadinud rohkem, kui vaja: peatusin 30 sundmuse peal.

-------------------------------------------------------------------------------
10. FAILID
-------------------------------------------------------------------------------

  Repos (commit'itud):
    SUB60_TICK_PLAAN.csv .......... eelregistreeritud paev/tund plaan
    SUB60_TICK_PLAAN.json ......... sama masinloetavalt
    SUB60_TICK_COVERAGE.csv ....... katvus sundmuste kaupa (30 rida)
    SUB60_TICK_DATASET.csv ........ 47 sumbol-paeva kvaliteedinaitajad
    bot/dukascopy_plan.py ......... eelregistreeritud valiku kood
    bot/dukascopy_kate.py ......... mitme paeva katvuse kontroll
    bot/dukascopy_ingest.py ....... PARANDATUD (vt osa 5)

  Kettal, gitignore'itud (74,4 MB):
    bot/data/dukascopy/bi5/<SUMBOL>/<PAEV>/<TT>h_ticks.bi5   303 faili
    bot/data/dukascopy/ticks/<SUMBOL>_<PAEV>_ticks.csv        47 faili

  Supabase'is:
    dukascopy_files ............... 471 rida, raw bytea
    dukascopy_plaan ............... 595 rida, prio 1/2
    fetch_bi5_hours / _paev / _plaan  idempotentsed allalaadijad
    Edge Function dukascopy-bi5 v6

-------------------------------------------------------------------------------
11. JARELDUS
-------------------------------------------------------------------------------

  ANDMED ON OLEMAS. Sub-60 test saab nuud tegelikult joosta.

  30 TIER 1 |z|>=1 sundmust, koigil on paris bid/ask tikid release'i
  hetke umber. Mediaan: eelmine tick 0,056 s enne, jargmine 0,065 s
  parast, 212 tikki esimese 60 sekundi jooksul.

  Kaks sundmust on nork: 09-04 09:00 (eelnev hind kuni 4,7 s vana) ja
  09-07 09:00 (0 tikki esimeses sekundis). Need on ette kirja pandud,
  et neid ei saaks hiljem tulemuse jargi valida.

  MA EI JOOKSUTANUD TESTI. Sa utlesid, et seda ei tohi, ja ma ei teinud.

  Mida ma EI tea enne testi jooksutamist: kas 0-60 s aknas on uldse
  serva. n = 30 on vaike. See annab moota, mitte toestada.
===============================================================================
```
