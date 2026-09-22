===============================================================
KOOD KIRJUTATUD — UUDISE-MOMENTUM STRATEEGIA (VAIKIMISI VÄLJAS)
===============================================================
  Pushitud harusse claude/great-davinci-8wchd4, commit b3e6b69.

---------------------------------------------------------------
MIS LISATI
---------------------------------------------------------------
  gold_logic.py    news_reaction_signal() — puhas suuna/SL-
                    otsustusfunktsioon, testitav ilma MT5-ta

  mt5_connector.py  modify_position_sltp() — UUS. Varem sai bot
                    ordereid ainult AVADA, mitte avatud
                    positsiooni SL-i muuta. Vajalik trailingu
                    jaoks.

  config.py         news_momentum_enabled = False + koik
                    parameetrid (risk_pct 1.5%/jalg x 2 jalga,
                    SL 1.5xATR, trail 1.0/1.5xATR, 54-realine
                    sundmuste valgenimekiri, MAX_HOLD 240h
                    tagavara). Pikk kommentaar backtest-
                    numbrite ja hoiatustega, nagu koik teised
                    lulitid selles failis.

  main_v4.py        run_news_momentum(now) — avab uue
                    positsiooni, kui econ_cal's on valge-
                    nimekirja sundmus viimase 90 min seest JA
                    hind on sellest ajast piisavalt liikunud.
                    manage_news_momentum(now) — trailing SL +
                    240h tagavara-sulgemine. Molemad seotud
                    skanni-tsuklisse "news_momentum_enabled"
                    taha.

---------------------------------------------------------------
KOHUSTUSLIK KONTROLL (CLAUDE.md)
---------------------------------------------------------------
  1. Suntaks:  python3 -m py_compile config/gold_logic/
               mt5_connector.py -> OK. main_v4.py: AST-parse OK
               (MT5 pole Linuxil importitav, ei saa siin
               pariselt kaivitada).
  2. Import:   koik uued funktsioonid kontrollitud grep'iga -
               defineeritud JA kutsutud, mitte surnud kood.
  3. Juur/bot: koik 4 muudetud faili on IDENTSED (diff tuhi).
  4. Dead code: run_news_momentum, manage_news_momentum,
               modify_position_sltp, news_reaction_signal -
               koik reaalselt kasutuses.
  5. Kaitumise muutus: news_momentum_enabled = False VAIKIMISI.
               LIVE KAITUMINE EI MUUTU enne, kui ise config.py's
               sisse lulitad.
  6. Backtest: signaaliloogika ISE on ulatuslikult backtestitud
               (KOKKUVOTE_UUDISE_MOMENTUM_V2/V7/V8*.md), AGA
               see PARIS kood (Supabase-paring + MT5 order +
               trailing) pole KORDAGI jooksnud - ei backtestis
               ega VPS-il.

---------------------------------------------------------------
LEITUD JA PARANDATUD 3 VIGA KIRJUTAMISE AJAL
---------------------------------------------------------------
  - sync_mt5_positions() ei tundnud "news_momentum" regiimi -
    suletud positsioonid oleks markinud "recovered"-iks (SAMA
    viga, mis varasema "recovered" segaduse tekitas). Lisatud
    regime-nimekirja.
  - Sundmuse pealkirjad nagu "S&P Global Manufacturing PMI
    Flash" sisaldavad "&" - see oleks lohkunud andmebaasi
    paringu URL-i. Lisatud puhastus (ainult tahed/numbrid/
    alakriips).
  - Ajatempli formaat "+00" URL-is oleks tolgendatud tuhikuna
    ja lohkunud ajafiltri. Vahetatud "Z" formaadi vastu.

---------------------------------------------------------------
MIDA SEE VEEL EI TEE (aus piirang)
---------------------------------------------------------------
  See kood pole KORDAGI paris MT5/VPS vastu jooksnud - see on
  esimene kord, kui modify_position_sltp() ja Supabase econ_cal
  paring kirjutati ja neid ei saa siin (Linuxi liivakastis)
  otsse testida. Enne sisselulitamist:

  1. `/update` VPS-il (git pull + kompileerimiskontroll).
  2. Jata `news_momentum_enabled` VEEL False'iks paar paeva,
     vaata logisid - kas get_recent_news_events() leiab
     sundmusi, kas ATR/hind toovad moistlikke vaartusi.
  3. Alles siis luulita sisse, esialgu vaiksema riskiga
     (nt news_momentum_risk_pct_per_leg = 0.005 mõne paeva,
     enne kui 0.015 peale lahed).

===============================================================
