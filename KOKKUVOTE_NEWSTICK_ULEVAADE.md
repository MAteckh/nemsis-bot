===============================================================
MIDA VAJAB "PÄRIS" KIIRE UUDISE-REAKTSIOON — ÜLEVAADE
===============================================================
  Ainult uurimine/lugemine. Koodis EI MUUDETUD midagi, midagi
  EI DEPLOY'ITUD, midagi live'i EI PANDUD.

  Hea uudis: see infrastruktuur on JUBA EHITATUD origin/main's
  (Benedictus News-Tick v1) — see EI OLE "ehita nullist" projekt.
  See on lihtsalt minu harus (claude/great-davinci-8wchd4) veel
  puudu, kuna see haru lahknes enne seda tood.

---------------------------------------------------------------
MIS ON JUBA OLEMAS JA VALMIS
---------------------------------------------------------------
  1. Otsustusloogika (newstick_engine.py) — z-skoor, suund,
     agregeerimine, 71 läbivat testi.
  2. Andmeallikas (oanor_client.py) — Oanor economic calendar
     API klient, mis toob actual/consensus AVALDAMISHETKEL.
  3. KIIRE POLLIMISE ARHITEKTUUR (juba ehitatud, main_v4.py's):
     - Enamik ajast: pollib Oanorit iga 300 sekundi tagant (jõude)
     - 20 sekundit ENNE plaanitud avaldamist: hakkab pollima
       IGA 1 SEKUNDI tagant, kuni 120 sekundit
     - See TÄPSELT vastab su kirjeldatud kiirusele — 1s pollimine
       tähendab, et sündmus avastatakse tõenäoliselt 0-1
       sekundi jooksul selle avaldamisest.
  4. hold_seconds=30, sl_pips=24, risk_pct=0.01 — juba
     seadistatud, vastavuses tick-testi endaga (mis kasutas
     samuti 30s hoidmist).
  5. mt5_connector.get_bid_ask() — kiire hinna lugemine lisatud.
  6. Eraldi lõim (thread), mis ei jaga tavalist 65s skanni —
     jookseb OMA tempoga.

---------------------------------------------------------------
MIS ON PUUDU / RISKANTNE (AUSALT)
---------------------------------------------------------------
  1. OANOR_API_KEY. See on KOLMANDA OSAPOOLE tasuline/võtmega
     teenus (api.oanor.com). Ilma selleta ei käivitu see lõim
     üldse (fail-closed, logib vea, ei tee midagi). Ma ei tea,
     kas sul on selle jaoks juba konto/võti — see on esimene
     praktiline takistus.

  2. OANOR ENDA KIIRUS ON MÕÕTMATA. Isegi kui pollid Oanorit
     iga 1 sekundi tagant, ei tea me, KUI KIIRESTI Oanor ISE
     saab "actual" väärtuse KÄTTE ja oma API kaudu tagasi
     annab. See on täiesti eraldi latentsuse allikas väljaspool
     boti enda kontrolli.

  3. PÄRIS BROKER'I TÄITMISKIIRUS ON MÕÕTMATA. Otsuse-hetkest
     kuni MT5 order'i täitmiseni (võrk + MT5 API + BlackBull
     broker'i töötlus) — see number puudub täielikult. Kogu
     edge (tick-testi järgi) sõltub sellest, kas kogu ahel
     (avastamine + otsus + order) mahub 1-3 sekundisse.

  4. SERV ISE ON VÄIKESE VALIMIGA (30 sündmust) ja osaliselt
     üksikute korreleeritud sündmuste kanda (3 suurimat võitu
     samast klastrist — ilma nendeta +11.14 -> +6.82 pipsi).

  5. "actual" andmete revisjoni-küsimus lahendamata — kas Oanori
     number avaldamishetkel on "esialgne trükk" (see, mida turg
     päriselt nägi) või hiljem parandatud väärtus.

---------------------------------------------------------------
MIDA SEE TÄHENDAB SINU JAOKS PRAKTILISELT
---------------------------------------------------------------
  See EI OLE "kuude pikkune ehitusprojekt" — enamik rasket tööd
  on juba tehtud ja testitud (offline, mock-andmetega). Kolm
  PÄRISELT puuduvat asja on:

  a) Oanor API konto/võti (sinu otsustada — kas ja kust seda
     hankida, mis see maksab)
  b) Kontrollitud test PÄRIS võtmega, esialgu VÕIMALUSEL
     demo-kontol, mitte otse 264 EUR live-kontol — et mõõta
     päriselt (2) ja (3) latentsust
  c) Rohkem sündmusi valimisse enne, kui usaldada väikest
     30-sündmuse serva päris rahaga

  See, kes selle ehitas, jättis selle TEADLIKULT väljalülitatuks
  täpselt neil põhjustel — mitte sellepärast, et kood on
  poolik, vaid sellepärast, et PÄRIS maailma latentsus ja
  serva robustsus on kinnitamata.

---------------------------------------------------------------
KOKKUVÕTE
---------------------------------------------------------------
  Kui tahad seda tõsiselt kaaluda:
  1. Kontrolli, kas Oanor API on midagi, mida saad/tahad hankida
  2. Kui jah, sean üles (või aitab keegi teine) võtme ja
     jälgin esimesi logisid TAAS demo/paberraha peal
  3. Alles siis, kui latentsus on mõõdetud ja mõistlik, kaalu
     päris (väikest!) riski

  See on suurem otsus kui midagi, mida ma sinu eest praegu
  vaikselt ette valmistan — see vajab sinu teadlikku otsust
  Oanor'i konto ja kulude osas.
===============================================================
