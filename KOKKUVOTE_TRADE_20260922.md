===============================================================
KAS BOT OLEKS PIDANUD TANA (22.09.2026) TRADI TEGEMA
===============================================================
  Vastus lyhidalt: AMETLIK strateegia ei teinud tana yhtki tehingut
  ja seda oli oodata. AGA kontol TOIMUS tana 8 tehingut labi
  MUU, seletamata kanali kaudu. See on toenaoliselt olulisem
  leid kui algne kysimus.

---------------------------------------------------------------
1. AMETLIK STRATEEGIA (portfolio / donchian XAUUSD, 1x paevas)
---------------------------------------------------------------
  Live config.py jargi jookseb praegu AINULT yks strateegia:
  portfolio_legs = XAUUSD, signaal donchian(50), paevabaaril.
  Vana kulla grid on enabled=False, forex meanrev koik enabled=False.

  Signaali reegel: OSTA kui tanane sulgemishind > viimase 50
  paeva korgeima high yle; MYY kui alla viimase 50 paeva
  madalaima low. Max 1 positsioon jala kohta, max 1 avatud
  positsioon KOKKU portfellis, uudiste-blackout aktiivne
  (kolmapaev 18-19 UTC Fed, kuu 1. reede 12-14 UTC NFP).

  22.09.2026 on teisipaev, blackout ei kehti.

  KONTROLLISIN signals-tabelit regime='portfolio' jargi:
  seda regiimi EI OLE KORDAGI kasutatud (0 rida) alates
  strateegia live-mineku paevast 11.-12. sept. Ehk see
  strateegia pole 11 paeva jooksul KORDAGI tehingut teinud.
  Seega "kas ta oleks tana pidanud" -> ajaloolise baasmaara
  jargi on tavaline paev pigem "ei", aga MA EI SAA seda
  100% tanase paeva kohta yle kontrollida (vt piirangud all).

---------------------------------------------------------------
2. MIDA KONTO TEGELIKULT TEGI TANA
---------------------------------------------------------------
  trades-tabelist (paris MT5 tulemus, sync_mt5_positions kirjutab):

  kellaaeg(UTC)  suund   sisse    valja    pnl(EUR)  SL seatud?
  ------------   -----   -----    -----    --------  ----------
  09:55:12       sell    4331.93  4324.63    +6.37     EI
  09:55:13       sell    4332.31  4324.63    +6.70     EI
  10:01:37       sell    4335.81  4324.63    +9.75     EI
  13:35:46       sell    4334.01  4329.48    +3.96     EI
  13:35:48       sell    4334.10  4329.48    +4.03     EI
  13:36:52       sell    4334.91  4329.48    +4.74     EI
  13:36:53       sell    4336.47  4329.48    +6.10     EI
  15:35:01       buy     4329.30  4330.22    +0.80     EI

  Kokku tana: 8 tehingut, koik lot 0.01, netto +42.45 EUR,
  KOIK ilma stop-lossita (sl=0.0 MT5-s).

---------------------------------------------------------------
3. MIS KANAL SEE ON - "recovered"
---------------------------------------------------------------
  Koik 8 on kirjas regime="recovered", session="recovered_XAUUSD".
  main_v4.py koodi jargi (sync_mt5_positions, rida ~700) tahendab
  see: bot leidis MT5 kontolt AVATUD positsiooni, mida Supabase
  signals-tabelis EI OLNUD. See ei tule portfolio-strateegia
  loogikast (run_portfolio_leg) - see AINULT LOGIB tagantjarele
  positsiooni, mis kuskilt MUJALT juba tekkis.

  Koik oleks laksid nn "boti oma, kadunud Supabase'ist" voi
  "kasitsi/muu, magic pole boti" harudesse - kumb tapselt, ei
  ole andmebaasi kirjes eraldi salvestatud (ainult Telegrami
  logis, mida ma ei nae).

---------------------------------------------------------------
4. SEE EI OLE UHEKORDNE - 11 PAEVA PILT
---------------------------------------------------------------
  paev          tehinguid   netto(EUR)   koik ilma SL-ita?
  ----------    ---------   ----------   -----------------
  11.09.2026        1          +25.42          JAH
  14.09.2026       20          +39.56          JAH
  15.09.2026        3          +18.93          JAH
  16.09.2026        7          +11.33          JAH
  17.09.2026        3           -2.15          JAH
  18.09.2026        2          -18.14          JAH
  21.09.2026       14           -4.83          JAH
  22.09.2026        8          +42.45          JAH
  ----------    ---------   ----------
  KOKKU            58         +112.57

  TAHTIS: trades-tabelis EI OLE alates 11. septembrist yhtegi
  MUUD regime't kui "recovered". Portfolio-strateegia (mis
  peaks olema ametlik live-strateegia) ei ole toonud SISSE
  yhtegi realiseeritud tehingut. KOGU reaalne kauplemine
  11 paeva jooksul kaib seletamata kanali kaudu.

---------------------------------------------------------------
5. KRIITILINE HOIATUS
---------------------------------------------------------------
  See on paris raha kontol (BlackBull 525854 LIVE):
  - 58 tehingut 11 paevaga, KOIK ilma stop-lossita.
  - portfolio_max_loss_eur (45 EUR lagi) ja get_risk_based_lot
    KEHTIVAD AINULT run_portfolio_leg() sisse avatud tehingutele.
    "Recovered" tehingud on juba MT5-s avatud, kui bot need
    esimest korda naeb - lagi ei rakendu neile KUNAGI.
  - Kui yks neist liigub ilma SL-ita valesse suunda suurelt,
    ei peata seda miski boti sisemistest kaitsetest.
  - See kaib jarjest (peaaegu iga paev), mitte yks juhuslik
    tehing - naeb valja nagu MUU protsess (teine EA, kasitsi
    VPS-i peal, voi broker-poolne mehhanism) kaupleb SAMAL
    MT5 kontol paralleelselt botiga.

  SOOVITUS: enne kui millegi muuga jatkata, tuleb VPS-il
  (C:\nemsis-bot) ja MT5 terminalis kontrollida:
  1. Kas terminalis jookseb veel MOni teine EA/skript peale
     nemsis-boti enda?
  2. Kas keegi (kasutaja ise voi keegi teine) logib MT5-sse
     kasitsi sisse ja kaupleb?
  3. Vordle tehingu tickette (nt 96409148, 96385318, 96353635)
     MT5 "History" vahekaardil magic-numbriga - kui magic
     vastab boti enda MAGIC konstandile, on tegu bot enda
     orderiga, mis kuidagi ei jouda oma tavaparast
     run_portfolio_leg() rada pidi Supabase'i (viga koodis).
     Kui magic on teine, kaupleb kontol keegi/miski VALIS.

---------------------------------------------------------------
6. MIDA MA EI SAANUD KONTROLLIDA (piirangud)
---------------------------------------------------------------
  - Liivakastil pole otseyhendust MT5 ega hinnapakkujaga -
    ei saa ise "praegust hinda" ega tanast H1/D1 baari otse
    kysida.
  - Supabase market_bars tabeli XAUUSD_d rida on TASELISENA
    11 paeva vana - viimane baar 11.09.2026, mitte tana. See
    tabel on backtest/uuringu jaoks (load_yahoo_bars), MITTE
    live-boti andmeallikas, seega see ei mojuta boti pariselt
    tehtud otsuseid - aga see tahendab, et ma EI SAANUD
    donchian(50) signaali tana ise yle arvutada ega kinnitada,
    mida bot tapselt tanasel D1 baaril nagi. Vastus punktis 1
    pohineb ajaloolisel esinemissagedusel (0/11 paeva), mitte
    tanase baari otsesel jarelarvutusel.
  - Kasutasin AINULT seda, mis on juba Supabase signals/trades/
    bot_state tabelites - see on boti enda VPS-ilt kirjutatud
    paris logi, mitte minu simulatsioon.

---------------------------------------------------------------
7. LISAKS - EI SEOTUD TANASE KYSimusEGA, AGA TURVALEID
---------------------------------------------------------------
  Supabase projektis (xqinzjaqorjqaexeoyqc) on Row Level
  Security VALJAS 5 tabelil, sh signals ja econ_cal - anon
  votmega saab neid igayks lugeda/kirjutada. Kui see pole
  teadlik otsus, tasub kaaluda RLS sisselulitamist koos
  oigete policy'dega (mitte pime ALTER TABLE, see blokeeriks
  koik ligipaasu ilma policy'teta).

===============================================================
