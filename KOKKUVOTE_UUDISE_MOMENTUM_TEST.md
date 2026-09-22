===============================================================
BACKTEST: "UUDISE SUUNAS KAASA, OHUTU TP" — TULEMUS
===============================================================
  Ainult test. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD.
  git status repos naitab 0 muudatust.

  TULEMUS ETTE ARA: koigis kolmes seades, mida testisin, KAOTAS
  see strateegia raha — isegi kui voiduprotsent oli 60-70%.
  Sama SL/TP JUHUSLIKUL ajal (mitte uudise jargel) tegi ROHKEM
  kasumit kui uudise-ajastusel. See tahendab: nii nagu ma seda
  testida sain, ei ole "liigu kaasa kui uudis juba liikunud on"
  kasumlik — see on ISE kahjumi allikas, mitte lihtsalt
  kasutamata voimalus.

---------------------------------------------------------------
KUIDAS TESTISIN
---------------------------------------------------------------
  Andmed:     XAUUSD H1 (Supabase market_bars), 2024-04..2026-09
              (~2.4 aastat) + econ_cal, USD, korge tahtsus
              (importance=1), 653 sundmust (Fed, NFP, CPI jne)

  Proxy suunale: kuna minuti-tasandi andmeid pole, kasutasin
  seda H1 baari, mis katab uudise ilmumise hetke — kui selle
  baari close > open, "uudis liigutas ules", vastasel juhul
  "alla". Sisenesin selle baari SULGEMISHINNAGA (nagu sina
  reaalajas naeksid liikumist ja astuksid sisse).

  Konto: 214 EUR, risk_pct 1.5%, SL-lagi 45 EUR — samad numbrid,
  mis live portfellis kehtivad.

---------------------------------------------------------------
TULEMUSED (kattuvusteta tehingud, uks korraga)
---------------------------------------------------------------
  seade                        teh   netto EUR   voit%   PF
  --------------------------   ---   ---------   -----   ----
  1) SL 1.5xATR / TP 1.0xATR   357     -88.06     59.7%   0.98
  2) SL 1.5xATR / TP 0.6xATR   366    -453.94     70.2%   0.84
     (see on kige lahem sinu "ohutu TP" ideele)
  3) SL 1.0xATR / TP 0.5xATR   374    -736.43     61.8%   0.72

  VORDLUS — SAMA SL/TP mis (2), aga SISENETUD JUHUSLIKUL AJAL
  (mitte uudise jargel):
  4) juhuslik ajastus          575    +371.70     70.4%   1.10

  PF = profit factor (voitude summa / kaotuste summa). Alla 1.0
  tahendab, et kaotused olid suuremad kui voidud KOKKU, isegi
  kui uksikvoite oli rohkem.

---------------------------------------------------------------
MIKS SEE JUHTUB — ARV EI VALETA
---------------------------------------------------------------
  Voiduprotsent 60-70% on korge, aga see ei paasta, sest "ohutu"
  TP on VAIKE (0.6x ATR) vorreldes SL-iga (1.5x ATR) — iga
  UKS kaotus kustutab ara 2-3 voitu. See on tapselt sama muster,
  mille kohta on selles repos varem juba korduvalt leitud:
  korge voiduprotsendiga vaikeste TP-dega strateegiad naevad
  paberil head valja, aga matemaatika (RR-suhe) tapab need ara.

  Veelgi olulisem: SAMADE parameetritega JUHUSLIK ajastus (4)
  tegi ROHKEM kasumit kui uudise-jargne ajastus. See viitab,
  et hind, mis on H1 baari SEES juba uudise peale liikunud,
  KIPUB OSALISELT TAGASI POORDUMA jargmistel tundidel — ehk
  "juba liikunud suund" on statistiliselt halvem sisenemiskoht
  kui suvaline hetk, mitte parem.

---------------------------------------------------------------
MIS SEE EI TESTINUD (ausad piirangud)
---------------------------------------------------------------
  - See EI ole sinu paris meetod. Sina jargid arvatavasti
    hinda MINUTITE, mitte tundide kaupa, ja astud sisse enne,
    kui terve H1 baar on lopetanud liikuma. Minuti-tasandi
    andmeid XAUUSD kohta selles Supabase'is ei ole (ainult H1
    ja paevabaar) — seega ei saa ma tapselt sinu meetodit
    jarele testida, ainult uht kindlat proxy't sellest.
  - See ei arvesta spreadi laienemist uudise hetkel (paris
    taitmine oleks selle tulemuse veelgi halvemaks teinud, mitte
    paremaks).
  - Testisin AINULT importance=1 USD sundmusi — voib-olla sinu
    fookus on kitsam (ainult Fed/NFP/CPI) voi laiem (kaasa
    arvatud EUR/GBP uudised).

---------------------------------------------------------------
JARELDUS
---------------------------------------------------------------
  Selle testi pohjal EI EHITA ma seda live'i — CLAUDE.md
  reegel utleb selgelt: uus kauplemisloogika vajab enne
  soovitust backtest'i kinnitust, ja see backtest utleb
  vastupidist sellele, mida oleksime lootnud.

  Kui tahad, saan proovida:
  1) kitsam sundmuste hulk (ainult Fed + NFP, mitte koik
     importance=1 read, millest paljud on vahetahtsad)
  2) OODATA jargmise H1 baari algust enne sisenemist (mitte
     sama baari sees, mis voib olla osaliselt lookahead)
  3) vastupidine idee: uudise-jargne FADE (mine liikumise
     VASTU, mitte kaasa) — arvestades, et (4) vihjab
     tagasipoordumisele, voib see olla huvitavam suund
===============================================================
