===============================================================
TEST v7 — 2 JALGA VS 3 JALGA (0.05 lot, keskmine+suur uudised)
===============================================================
  Ainult test. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD.

  Sama seaded (250 EUR pank, 0.05 lot/jalg, 50 EUR SL-floor/jalg,
  882 keskmine+suur USD sundmust, T/K/N), AINULT jalgade arv
  muutus 5 -> 2 ja 5 -> 3.

---------------------------------------------------------------
2 JALGA (max teoreetiline risk: 2x50=100 EUR = 40% kontost)
---------------------------------------------------------------
  tehinguid:          200
  netto P&L:           +27 042.04 EUR
  voiduprotsent:        63.5%
  profit factor:        5.11
  max drawdown:         -21.0%
  MADALAIM KONTO:       125.75 EUR  (50% algkapitalist)

---------------------------------------------------------------
3 JALGA (max teoreetiline risk: 3x50=150 EUR = 60% kontost)
---------------------------------------------------------------
  tehinguid:          200
  netto P&L:           +40 563.06 EUR
  voiduprotsent:        63.5%
  profit factor:        5.11
  max drawdown:         -36.4%
  MADALAIM KONTO:       63.62 EUR  (25% algkapitalist —
                        UKS järgmine kaotus oleks olnud lahedal)

---------------------------------------------------------------
KONTO ESIMESED 2 NADALAT (naitab, miks madalaim punkt niimoodi)
---------------------------------------------------------------
  2 jalga:
    02.05  Initial Jobless Claims   -100.00   -> 150.00 EUR
    14.05  PPI MoM                   -20.72   -> 129.28 EUR
    15.05  Retail Sales MoM          +18.63   -> 147.90 EUR
    16.05  Initial Jobless Claims    -22.16   -> 125.75 EUR (pohi)
    22.05  Existing Home Sales MoM  +362.20   -> 487.95 EUR

  3 jalga (SAMA sundmused, suurem lot):
    02.05  Initial Jobless Claims   -150.00   -> 100.00 EUR
    14.05  PPI MoM                   -31.08   ->  68.92 EUR
    15.05  Retail Sales MoM          +27.94   ->  96.86 EUR
    16.05  Initial Jobless Claims    -33.24   ->  63.62 EUR (pohi)
    22.05  Existing Home Sales MoM  +543.30   -> 606.92 EUR

  Molemad juhtusid PAASTA end sama "Existing Home Sales" voiduga
  22. mail — see on ONN, mitte garantii. Kui see voit poleks
  tulnud (voi kui oleks tulnud veel uks kaotus enne seda),
  oleks 3 jalga olnud otsas, 2 jalga veel elus, aga korralikult
  vigastatud.

---------------------------------------------------------------
JARELDUS
---------------------------------------------------------------
  2 JALGA on selgelt turvalisem kui 3 VOI 5: teoreetiline
  maksimumrisk uhel sundmusel on 40% kontost (mitte 60% ega
  100%), ja see test naitas, et see vahe on PARIS — 3 jalga
  kaigus 25%-ni kontost, 2 jalga ainult 50%-ni.

  AGA isegi 2 jalaga langes konto UHE NADALAGA poole vaiksemaks
  (250 -> 125.75 EUR) enne, kui taastus. See ei ole "turvaline",
  see on "vahem katastroofiline". Kui soovid, et konto EI saaks
  kunagi lahedale nullile isegi halval nadalal, on jargmine
  moistlik samm minna 1 jalale VOI risk-pohisele lot'ile, mis
  vaheneb automaatselt, kui konto on juba kahjumis (mitte jaa
  fikseerituks nagu praegu).

  Kas jaame 2 jala juurde ja liigume koodi kirjutamise
  juurde (vaikimisi valjas lulitina), voi tahad veel uht
  varianti testida?
===============================================================
