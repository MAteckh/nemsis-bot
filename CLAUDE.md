# NEMSIS bot — tööjuhised

## ⚠️ SEE ON LIVE-KAUPLEMISBOT PÄRIS RAHAGA

Konto jookseb BlackBull brokeri juures MT5 kaudu. Iga muudatus failides
`main_v4.py`, `config.py`, `mt5_connector.py`, `strategy_meanrev.py` võib
liikuda päris rahani. Käitu vastavalt.

## KOHUSTUSLIK KONTROLL IGA FAILIMUUDATUSE JÄREL

Kasutaja nõue: **kontrolli alati üle, et midagi ei ununeks lisamata, midagi
ei läheks katki ja kõik oleks 100% õigesti.** Seda tuleb teha iga kord, kui
faile muudetakse — mitte ainult siis, kui tundub vajalik.

Enne kui ütled, et muudatus on valmis:

1. **Süntaks** — `python3 -m py_compile` kõigi muudetud failide peal
2. **Import** — kontrolli, et kõik kasutatud nimed on defineeritud/imporditud
   (`grep` funktsiooni nime järele; `main_v4.py`-d ei saa Linuxil importida,
   sest `MetaTrader5` on Windows-only — seepärast on puhas loogika
   `gold_logic.py`-s, mida SAAB testida)
3. **Juur ja bot/ sünkroonis** — repos on iga fail kahes kohas
   (`main_v4.py` ja `bot/main_v4.py` jne). Railway deploy'b juurest.
   Peale iga muudatust: `diff bot/X.py X.py` peab olema tühi.
   Ajalooline viga: commit bc23e25 muutis ainult `bot/config.py`, juur jäi
   vanaks ja live jooksis vanade parameetritega.
4. **Surnud kood** — kontrolli, et lisatud funktsiooni ka päriselt kutsutakse.
   Ajalooline viga: `calc_gold_tp_sl()` ja `get_swing_levels()` olid
   kirjutatud, aga order placement ei kasutanud neid kunagi.
5. **Käitumise muutus** — ütle kasutajale VÄLJA, kui muudatus mõjutab
   live-käitumist, isegi kui see on väike. Vaikimisi peavad uued
   strateegia-lülitid olema `False`, kuni backtest neid kinnitab.
6. **Backtest** — kui muutub kauplemisloogika, jooksuta `bot/compare.py`
   või `bot/backtest.py` enne kui midagi soovitad.

## Andmed

- Liivakastil **ei ole** võrguühendust andmepakkujatega ega Supabase REST-iga.
- Andmed tulevad kasutaja Supabase'i kaudu: seal on `http` laiendus sees ja
  funktsioon `load_yahoo_bars(symbol, yahoo_symbol, range, interval)`, mis
  laeb Yahoo Finance'i baarid tabelisse `market_bars`.
- MCP `execute_sql` suur vastus salvestatakse automaatselt faili;
  `bot/sb_fetch.py` teisendab selle CSV-ks, mida `backtest.py` loeb.
- Ajaloolised CSV-d on `bot/data/` all (gitignore'itud).

## Tööriistad

- `bot/gold_logic.py` — puhtad funktsioonid, testitavad ilma MT5-ta
- `bot/strategies.py` — strateegia-agnostiline mootor + strateegiaperekonnad
- `bot/backtest.py` — grid/scalp/dual-engine simulaatorid
- `bot/walkforward.py` — out-of-sample valideerimine
- `bot/compare.py` — kõigi variantide õun-õuna võrdlus

## SEIS 11. sept 2026 (kust jätkata)

- Konto: BlackBull **525854 LIVE**, balance ~214€. Bot jookseb **VPS-il**,
  kaust `C:\nemsis-bot`, käivitatud `update.bat`-iga PowerShellis.
- Deploy käib nüüd **Telegramist: `/update`** (git pull + kompileerimiskontroll
  + restart). `/restart`, `/status`, `/reset`, `/help` samuti olemas.
- `main`-i on merge'itud ja pushitud: portfell SEES, vana kulla grid VÄLJAS,
  vana forex meanrev VÄLJAS.
- **OOTAB: kasutaja peab saatma `/update`**, et portfell käiku läheks.
- Esimesel käivitusel jälgi Telegramist `🔎 Sümbol lahendatud: US500` — kui
  tuleb hoiatus, vajab BlackBulli õiget indeksi nime `portfolio_legs` sees.
- Andmebaasi vanad rippuvad forex-read (ilma mt5_ticket'ita) on koristatud
  (executed=true). Kasutaja kinnitas: need EI olnud päris positsioonid.

## Mida andmed on seni näidanud

- Praegune live-konfiguratsioon: +61€ / 2 aastat, drawdown -81%. Live kinnitab
  (+2,35€ 2 kuuga). Sisuliselt ei tooda midagi.
- Mean reversion (RSI/Bollinger fade) on kullal mürgine — suurimad kahjumid.
- Trendijärgimine/breakout on ainus perekond, millel on serv.
- Osta-ja-hoia lööb enamikku aktiivseid strateegiaid.
- Trailing SL kukkus läbi kolmel sõltumatul testil — ära kasuta.
- `risk_based_lot` on üksik kõige mõjusam parandus (+61€ → +638€).
- €200 konto on kulla jaoks alakapitaliseeritud: 0.01 lot + $45 stopp = ~22%
  riski tehingu kohta. Sama strateegia €5000 kontol: drawdown -25% vs -114%.

## VÄLJUNDI VORM — KOHUSTUSLIK

Kasutaja nõue: **anna ALATI kogu info nii, et seda saab copy/paste teha.**

See tähendab iga sisulise vastuse puhul:

1. **Kogu tulemus ühes koodiplokis** (```), mitte laiali markdown-tabelites.
   Markdown-tabelid kaovad kopeerimisel ära; ASCII-tabelid mitte.
2. **Kõik numbrid sees** — mitte "vt faili", vaid päris arvud kohapeal.
3. **Lisaks salvesta fail** repo juurde (nt `KOKKUVOTE_VX.md`) ja saada
   see kasutajale `SendUserFile`-ga. Fail ja chat-plokk MÕLEMAD.
4. **ASCII-tabelid**, mitte markdown-püstkriipsud, sest need säilivad
   igal pool (Telegram, Notepad, e-kiri).
5. Ära jäta olulist ainult jutu sisse — see peab olema plokis.

Vorm, mis töötab:
```
===== PEALKIRI =====
 veerg1      veerg2     veerg3
 ------      ------     ------
 väärtus     väärtus    väärtus
```
