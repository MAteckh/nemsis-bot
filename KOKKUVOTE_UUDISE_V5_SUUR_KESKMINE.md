===============================================================
TEST v5 — AINULT KESKMISED+SUURED UUDISED — SAMA PROBLEEM
===============================================================
  Ainult test. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD.

  Piirasin sundmused 54 tuupi peale, mis on paris majandus-
  andmed (mitte torusesisu/nafta laoseisud/Fed konede mura) —
  Fed Interest Rate Decision, NFP, CPI (Inflation Rate),
  Core PCE, ISM PMI, Retail Sales, Jobless Claims, ADP,
  Consumer Confidence, Housing Starts, PPI, JOLTs, GDP jne.
  Sundmusi jai 1911 -> 882.

  TULEMUS ON SAMA PROBLEEM, AINULT VEIDI VAIKSEM KUKKUMINE:
  esimene tehing (2024-05-02, "Initial Jobless Claims" — see
  ON keskmine/oige uudis, mitte mürarida) kaotas JÄLLE -250.00
  EUR — KOGU algkapitali. Neljas tehing (2024-05-16) viis
  konto -60.63 EUR miinusesse.

---------------------------------------------------------------
MIDA SEE TAHENDAB
---------------------------------------------------------------
  Uudiste-filtreerimine EI LAHENDA probleemi, sest probleem
  EI OLE "vale uudised" — probleem on POSITSIOONI SUURUS.
  "Initial Jobless Claims" on paris, korralik, iganadalane
  keskmise tahtsusega uudis — ja isegi SELLE peal laks minu
  proxy suund esimesel korral valesti, nagu vahel juhtub IGA
  meetodiga (mitte ukski suunavalik ei ole 100% oige).

  Kui UKS vale suunavalik piisab TERVE konto kaotamiseks
  (sest 5 tk 0.05 lot samas suunas = 100% riski uhel
  sundmusel), siis ei paasta MITTE MIKS uudiste kvaliteet —
  varem voi hiljem tuleb vale suund ja konto on otsas.

  Vordlus:
  seade                          madalaim konto   1. tehing
  -----------------------------  --------------   ---------
  koik uudised (v3/v4)              -118.45 EUR    -250 EUR
  ainult keskmine+suur (see test)    -60.63 EUR    -250 EUR

  Parem uudiste valik vahendas UMBES kui palju MIINUSESSE
  laheb (kolmandas tehingus tuli natuke tagasi enne uut
  kaotust), aga ESIMENE tehing kaotab endiselt 100% —
  see EI SOLTU uudise tuubist.

---------------------------------------------------------------
JARELDUS — TAHTIS
---------------------------------------------------------------
  Uudiste kvaliteedi parandamine on hea samm YLDISELT (see
  aitas v2 testis, kus kasutasime moistlikku, risk-pohist
  lot-suurust), AGA see EI SAA parandada ULEKAALUKA POSITSIOONI
  SUURUSE probleemi. 5 samasuunalist 0.05-lotist tehingut
  250 EUR kontol on struktuurselt "koik-sisse" panus, olenemata
  sellest, MIS uudis pohjuseks on.

  Kui tahad seda ideed (uudise-suunas, trailing SL) edasi
  arendada, PEAB positsiooni suurus muutuma — see ei ole
  valikuline samm, see on EELDUS, et strateegia yldse ellu
  jaaks esimesest valest kutsest.

  Kas proovin sama (keskmine+suur uudised) VAHENDATUD
  suurusega — nt 1 tehing 5 asemel, voi risk-pohine lot
  (nagu bot mujal juba kasutab)?
===============================================================
