===============================================================
TEST v6 — 0.03 LOT (5 tk), KESKMINE+SUUR UUDISED
===============================================================
  Ainult test. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD.

  Testisin KAKS erinevat viisi, kuidas "0.03" voib tahendada,
  sest see on tahtis vahe:

---------------------------------------------------------------
STSENAARIUM A: 0.03 lot/jalg, SAMA 50 EUR SL-floor
---------------------------------------------------------------
  (Kui SL-floor jaab 50 EUR/jalg, aga lot vaheneb, LAIENEB
  hinnavahe: 50/(0.03x100) = $16.67 varem $10 asemel)

  tehinguid:          199
  netto P&L:           +40 254.90 EUR
  voiduprotsent:        63.8%
  profit factor:        5.26
  max drawdown:         -19.6%
  MADALAIM KONTO:       149.02 EUR — EI LAINUD MIINUSESSE

---------------------------------------------------------------
STSENAARIUM B: 0.03 lot/jalg, floor SKAALEERUB (30 EUR/jalg)
---------------------------------------------------------------
  (Sama hinnavahe $10 mis varasemas 0.05-testis, aga dollari-
  risk vaheneb koos lot'iga)

  tehinguid:          200
  netto P&L:           +40 563.06 EUR
  voiduprotsent:        63.5%
  profit factor:        5.11
  max drawdown:         -36.4% (kolme tehinguga peaaegu -75%)
  MADALAIM KONTO:       63.62 EUR — EI lainud miinusesse, AGA
                        peaaegu (250 -> 63.62 EUR vahemikus)

---------------------------------------------------------------
TAHTIS SELGITUS — MIKS KAKS STSENAARIUMI ERINEVAD
---------------------------------------------------------------
  Kui ainult LOT vaheneb (0.05->0.03), aga SL-EUR-floor jaab
  SAMAKS (50 EUR), siis hinnavahe LAIENEB (10->16.67$) —
  see EI vahenda tegelikku dollari-riski jala kohta, see teeb
  stopi LAIEMAKS. See laiem stopp juhuslikult AITAS selles
  konkreetses ajaloos (esimene tehing ei tabanud enam SL-i nii
  kiiresti). AGA teoreetiline HALVIM juht on endiselt SAMA:
  kui koik 5 jalga tabavad oma 50 EUR floor'i koos, on kadu
  ikka 5x50=250 EUR = 100% kontost. Stsenaarium A ei kaotanud
  seda testis, aga see on OSALT ONNE, mitte garantii.

  Kui SEE ON VALE (25%) skaleerub PROPORTSIONAALSELT lot'iga
  (30 EUR/jalg, stsenaarium B), on halvim TEOREETILINE juht
  5x30=150 EUR = 60% kontost — PARIS vahendatud, aga endiselt
  korge. Ja backtest naitas, et see peaaegu juhtuski (63.62
  EUR = -75% dropdown).

---------------------------------------------------------------
KOKKUVOTE
---------------------------------------------------------------
  Kumbki variant EI LAINUD miinusesse SELLES konkreetses
  ajaloos, aga ainult stsenaarium B vahendab PARIS teoreetilist
  maksimumriski (150 EUR vs 250 EUR). Stsenaarium A parandus
  tuleb LAIEMAST stopist, mitte vahendatud riskist — see on
  krehke argument ("toimis seekord"), mitte kindel ("ei saagi
  enam ebaonnestuda").

  Kui tahad kindlust (mitte ainult "seekord lain labi"), on
  minu soovitus siiski: vahenda KAS jalgade arvu (5 -> 2-3)
  VOI liigu risk-pohise lot'i peale (nagu bot mujal juba teeb),
  mis kohandub automaatselt balance'iga.

  Kas proovin 5 jala asemel 2-3 jalga, VOI risk-pohist lot'i?
===============================================================
