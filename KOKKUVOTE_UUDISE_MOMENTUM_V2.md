===============================================================
UUDISE-MOMENTUM TEST v2 — SEEKORD POSITIIVNE TULEMUS
===============================================================
  Ainult test. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD.

  Parandasin testi sinu tagasiside pohjal (4 punkti eelmisest
  vastusest): ainult suured sundmused, kiirem sisenemine,
  selektiivsus (jata norgad liikumised vahele), dunaamiline
  stopi-juhtimine (breakeven + trailing, mitte fikseeritud
  vaike TP). Seekord TULI POSITIIVNE tulemus.

---------------------------------------------------------------
SEADED
---------------------------------------------------------------
  Sundmused:    Non Farm Payrolls, Fed Interest Rate Decision,
                Core PCE Price Index MoM, CPI — 102 sundmust
                2024-04..2026-09 (2.4a)
  Selektiivsus: kaubelda ainult kui reaktsioonibaari liikumine
                >= 0.4xATR (33 norka/ebaselget sundmust jaeti
                vahele, 102 -> jai 69 kandidaati)
  Sisenemine:   40% teekonnal reaktsioonibaari open->close
                (proxy kiiremale sisenemisele kui kogu tunni
                ootamine)
  SL:           1.5xATR (lagi 45 EUR nagu live)
  TP:           2.5xATR ALGNE, AGA:
                - stopp breakeveni kui kasum >= 1x algne risk
                - trailing 1xATR kui kasum >= 1.5x algne risk
                (lase voitjal joosta, mitte fikseeritud vaike TP)
  Konto:        214 EUR, risk_pct 1.5% (nagu live)

---------------------------------------------------------------
TULEMUS
---------------------------------------------------------------
  tehinguid:            66 (2.4 aasta peale, ~27/aastas)
  netto P&L:            +454.42 EUR  (+212.3%)
  voiduprotsent:        43.9%
  profit factor:        1.79
  max drawdown:         -19.4%
  valjumise pohjus:     28x TP, 24x SL, 14x breakeven-stopp

  VORDLUS — SAMA retsept (selektiivsus+breakeven+trail), aga
  SISENETUD JUHUSLIKUL AJAL, mitte uudise jargel:
                        37 tehingut, netto +71.55 EUR, PF 1.18,
                        DD -72.6%

  Ehk uudise AJASTUS ise annab paris lisavaartust — sama
  juhtimisstiil suvalisel ajal on nork ja kaigub palju
  rohkem (DD -72.6% vs -19.4%).

---------------------------------------------------------------
AUS HOIATUS — TULEMUS ON KONTSENTREERITUD
---------------------------------------------------------------
  sundmus                        teh   netto EUR   voit%
  ----------------------------   ---   ---------   -----
  Fed Interest Rate Decision      12    +310.01     58%
  Core PCE Price Index MoM        19     +86.50     58%
  Non Farm Payrolls               20     +59.93     30%
  CPI                             15      -2.02     33%

  Fed intressiotsus KANNAB 68% kogu kasumist AINULT 12
  tehinguga. NFP-l on madal voiduprotsent (30%), mis loeb
  ainult sellepart, et harvad voidud on suured (trail lasi
  neil joosta) — see on ohtlikum muster, kui ainult 12-20
  tehingu pealt otsustada (vaike valim). CPI on sisuliselt
  nulli peal.

  Kui Fed valja jatta, jaab jargi +144.41 EUR 54 tehingult
  2.4 aasta pealt — ikka positiivne, aga palju norgem.

---------------------------------------------------------------
PIIRANGUD (endiselt kehtivad)
---------------------------------------------------------------
  - H1 andmed, mitte minuti-andmed — "40% teekonnal" on proxy
    kiiremale sisenemisele, mitte sinu paris taitmiskiirus.
  - Ei arvesta spreadi laienemist uudise hetkel (paris
    taitmine oleks tulemust halvendanud).
  - Valim on vaike (66 tehingut, Fed ainult 12) — 2.4 aastat
    pole palju tsuklites, mis moodavad aastaid.

---------------------------------------------------------------
JARELDUS
---------------------------------------------------------------
  See versioon (selektiivne + kiirem sisenemine + dunaamiline
  stopp) NAITAB paris edge't, eriti Fed-otsuste peal. See on
  esimene positiivne backtest kogu selle vestluse jooksul.

  Kas soovid, et:
  1) testin PIKEMA ajaloo peal (kui saan H1 andmeid varasemast
     kui 2024-04), et valim oleks suurem, VOI
  2) hakkan koodi kirjutama (uus lulitatav strateegia, VAIKIMISI
     VALJAS, config.py's, mida saab hiljem eraldi sisse
     lulitada) — VASTAVALT CLAUDE.md reeglile, backtest'i
     kinnitus on nuud olemas selle jaoks?
===============================================================
