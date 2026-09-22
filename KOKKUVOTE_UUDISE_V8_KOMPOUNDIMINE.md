===============================================================
KOMPOUNDIMISE KYSIMUS — EI, VARASEMAD TESTID EI KOMPOUNDINUD
===============================================================
  Otsene vastus: EI. Testid v4-v7 (5/3/2 jalga, 0.03-0.05 lot)
  kasutasid FIKSEERITUD lot'i — kui konto kasvas 250-lt
  7266 EUR-le, JARGMINE tehing kasutas ENDISELT sama 0.05
  lot'i, mitte suuremat. Varem teenitud kasum EI mojutanud
  jargmise tehingu suurust.

  Testisin nuud KOMPOUNDIVAT versiooni (lot kasvab koos
  balance'iga, nagu sina kusisid) — ja tulemus naitab, MIKS
  see on ohtlik, kui riskiprotsent on liiga korge.

---------------------------------------------------------------
KOLM RISKITASET, SAMA KOMPOUNDIV LOOGIKA
---------------------------------------------------------------
  risk/jalg   1 aasta jargi      lopp (2.4a)      madalaim
  ---------   ---------------    --------------   ---------
  20% (sinu algne 50/250)  472 496 EUR      2 475 057 EUR    129.86
  3%                          9 454 EUR        234 831 EUR    225.46
  1.5% (bot'i enda tase mujal) 2 558 EUR         13 735 EUR    225.46

---------------------------------------------------------------
MIKS 20% ON PROBLEEM — MITTE AINULT RISKANTNE, VAID EBAREAALNE
---------------------------------------------------------------
  20%-risk/jalg kompoundimine kasvatab lot'i sama kiiresti kui
  kontot. Ilma piirita oleks see jouda tehinguteni, kus lot on
  SADU MILJARDEID (kontrollisin — ilma lot-lae'ta lopp-tulemus
  oli 2 815 000 000 000 000 EUR, mis on puhas matemaatika-
  artefakt, mitte midagi, mida ukski broker/turg suudaks
  taita). Isegi 5.0 lot-lakke pannes (mis on ISE juba
  ebareaalselt suur retail-kontole) joudis tulemus 2.4 miljoni
  euroni — see EI OLE saavutatav paris turul (likviidsus,
  margin, broker'i piirid peatavad selle ammu enne).

  See ON tuntud lokks kauplemismatemaatikas: kui riskid
  liiga suurt % pangast IGA kord, isegi POSITIIVSE edge'iga,
  loob kompoundimine kas (a) konto rikke (nagu varasemad
  testid naitasid 20%+ juures ilma piiranguteta) voi (b)
  matemaatiliselt vointud, aga paris elus VOIMATU tulemuse.

---------------------------------------------------------------
1.5% ON PALJU MOISTLIKUM — JA SEE ON JUBA BOTIS OLEMAS
---------------------------------------------------------------
  1.5%/jalg (bot'i enda risk_pct, mida portfolio strateegia
  mujal juba kasutab): 250 -> 2558 EUR 1 aastaga, madalaim
  punkt 225.46 EUR (AINULT -10%, mitte -75% nagu fikseeritud
  lot'iga varem). See on tunduvalt VAHEM dramaatiline, aga
  PALJU turvalisem — ja endiselt 10x tootlus aastas.

---------------------------------------------------------------
JARELDUS
---------------------------------------------------------------
  Kompoundimine ISE ei ole halb idee — see on tapselt see,
  mida risk_based_lot mujal botis juba teeb. Probleem on
  RISKIPROTSENDI SUURUS: 20%/jalg (mis tuli sinu algsest "50
  EUR SL 250 EUR pangale") on liiga korge kompoundimiseks —
  see plahvatab kas kontoni nulli VOI matemaatiliselt
  vointud numbriteni, mida paris turg ei suudaks taita.

  1.5% on koht, kust bot mujal juba tootab, ja see test
  naitab, et see toimib SIINGI moistlikult (10x/aasta,
  -10% max dd) ilma plahvatuseta.

  Kas 1.5%/jalg (2 jalga = 3% kokku) on suund, mida edasi
  arendame?
===============================================================
