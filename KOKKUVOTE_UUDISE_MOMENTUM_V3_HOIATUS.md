===============================================================
TEST v3 (LAI RING, ILMA SL-ITA, AINULT TRAIL) — TULEMUS ON KATKI
===============================================================
  Ainult test. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD.

  Proovisin tapselt sinu kirjeldust: T/K/N, koik USD uudised
  (1911 sundmust 2.4a), EI PANDUD SL-i, ainult trail (aktiveerub
  0.4xATR kasumis, trail 0.25xATR) — kui lopeb vastu liikumisega,
  trail-SL on juba kasumis, tapselt nagu sina kirjeldasid.

  TOORES TULEMUS: +238 649 EUR, voiduprotsent 99.5%,
  profit factor 44.47.

  SEE EI OLE PARIS. Ma ei hakka seda sulle muumuinasjutuna
  maha muuma — see arv on katki ja ma selgitan tapselt, miks.

---------------------------------------------------------------
MIKS TULEMUS ON KATKI (mitte "vau, see toimib")
---------------------------------------------------------------
  Vaatasin valjumise pohjuseid: 369 tehingut 371-st suleti
  TRAIL'iga (ehk kasumis), ja AINULT 2 tehingut kogu 2.4 aasta
  peale suleti kahjumis (minu 10-paevase "tagavara"-reegli
  jargi). See tahendab minu testi YLESEHITUSES ON STRUKTUURNE
  VIGA: kuna SL-i pole, ei OLNUD testis peaaegu mitte KUNAGI
  voimalust kaotust realiseerida — kui tehing lakski vastu,
  ootas simulatsioon lihtsalt kuni 10 kauplemispaeva, LOOTES et
  hind tuleb tagasi. Ja 2024-2026 oli kullale erakordne TOUSU-
  periood (~2000 -> ~4600 dollarit, +130%) — nii et peaaegu
  IGA ostupositsioon voitis LOPUKS, olenemata sellest, kas
  algne suunavalik oli oige.

  Kokkuvottes ei testinud ma "sinu meetodit" — ma testisin
  "osta kulda peaaegu iga paev ja oota, kuni tousev turg sind
  paastab, sest miski ei sunni positsiooni kunagi kahjumis
  sulgema". See EI OLE korduv edge, see on YHE erakordse
  turutsukli artefakt.

  Lisaks: lot suurus kasvas koos balance'iga (risk_based_lot),
  seega korgemad "voidud" hilisemates tehingutes kasvasid
  eksponentsiaalselt koos vale-kindla balance'iga — see
  vohendas moonutust veelgi.

---------------------------------------------------------------
PARIS OHT, MIS SIIT VALJA TULEB (LIVE KONTO KOHTA)
---------------------------------------------------------------
  See ON tahtis leid, ainult vastupidises suunas kui lootsime:
  "ei pane SL-i" tahendab, et sinu backtest (ja paris konto)
  on siiani toiminud sellepärast, et kuld on 2+ aastat olnud
  tugevas tousutrendis. Kui/kui tuleb pikem paranduse periood
  (kuld on ajaloos langenud ka -28% 2013 ja mitmeaastaselt
  2011-2015), ei ole trail-only meetodil MITTE MIDAGI, mis
  kahjumit piiraks, kui hind sinu vastu liigub ja EI tule
  piisavalt kiiresti tagasi. See on tapselt see risk, mille
  eest KOVA SL-lagi (45 EUR) mujal live konfiguratsioonis
  praegu kaitseb.

---------------------------------------------------------------
KUIDAS SEDA AUSALT EDASI TESTIDA
---------------------------------------------------------------
  Kaks moistlikku suunda:

  1. Testi PIKEMA ajaloo peal (2016-2026, 10a paevabaaridel,
     mis katab ka kulla 2018-2019 vaiksema perioodi ja 2020
     COVID-kraahhi), et naha, kas trail-only meetod pusib
     vaeval, mitte ainult puhtas 2-aastases tousutrendis.

  2. Lisa SIISKI kaugele kova katastroofi-lagi (nt praegune
     45 EUR SL-lagi, VOI laiem, nt 100 EUR) — MITTE peamise
     valjumisena (sinu trail teeb seda), vaid ainult kui
     viimane turvavork, kui hind laheb PALJU vastu ja trail
     ei aktiveeru kunagi. See ei muuda su meetodit — sa ju
     harilikult ei koge seda olukorda, sest sa jalgid kasitsi
     — aga AUTOMATISEERITUD versioon vajab midagi, mis piiraks
     kahju siis, kui keegi ei vaata.

  Kumba proovin jargmisena, voi molemaid?
===============================================================
