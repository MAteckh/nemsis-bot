===============================================================
KONTROLLISIN — LOOKAHEAD-VIGA OLI PÄRIS. EDGE KADUS.
===============================================================
  Võtsin oma kõige puhtama tulemuse (V2: 1 jalg, ainult NFP/Fed/
  PCE/CPI, selektiivsus, breakeven+trail — +454 EUR/2.4a) ja
  jooksutasin selle UUESTI, seekord PARANDATULT: sisenemine
  alles JÄRGMISE H1 baari AVAL (mitte reaktsioonibaari SEES),
  pluss realistlik kulu (0.40 EUR / 0.01 lot, sama tava, mida
  compare.py mujal selles repos kasutab).

  TULEMUS:

  seade                          netto P&L    voit%    PF
  -----------------------------  -----------  -------   ----
  VANA (nagu V2, lookahead sees)   +428 EUR    43.9%    1.72
  PARANDATUD (jargmise baari AVA)  -113 EUR    34.3%    0.88

  Edge POORDUS MIINUSESSE, kui lookahead parandada. See kinnitab
  TAPSELT seda, mida origin/main'i teine uuring leidis: "sisene
  baaris, mis katab uudise hetke" kasutab infot, mis polnud
  sisenemise hetkel veel teada, ja see YKSI selgitab suure osa
  minu "positiivsest" tulemusest.

---------------------------------------------------------------
JARELDUS
---------------------------------------------------------------
  Minu V2/V7/V8 tulemused (+454 EUR, +27042 EUR, +40563 EUR jne)
  olid metoodikaveaga paisutatud. Kui viga parandada, kaob
  edge — see langeb kokku origin/main'i sõltumatu, rangema
  uuringu järeldusega ("CALENDAR IMMEDIATE EXECUTION: FAIL").

  See ei ole enam "vaja rohkem testida" olukord — see on kaks
  sõltumatut, erineva metoodikaga kontrolli, mis mõlemad
  jõudsid samale kohale: see konkreetne idee (nii nagu see H1-
  baaridel testitav on) ei tooda live'is raha.

  news_momentum_enabled jääb False'iks. Kood jääb repos alles
  (dokumenteeritud, testitav näide selle kohta, MIKS see ei
  tööta), aga ma ei soovita seda enam live'i panna ilma täiesti
  teistsuguse lähenemiseta (nt paremad andmed, tegelik tick-
  tasand, mida origin/main'i Oanor-pohine News-Tick proovib).

  Kas tahad, et vaatan origin/main'i "Benedictus News-Tick v1"
  koodi lähemalt — see kasutab paremaid andmeid (paris tick,
  Oanor API) ja võib olla see, mis lõpuks päriselt tootab, kui
  see kunagi backtestitakse?
===============================================================
