===============================================================
KAS MIDAGI ENNUSTAB TURGU ENNE UUDIST? — 11 TESTI, 11 EI
===============================================================
  Ainult testid. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD.

  Testisin süstemaatiliselt, kas mõni VAREM avaldatav majandus-
  näitaja ennustab HILISEMA näitaja üllatuse suunda paremini kui
  juhus — sinu idee "USA inflatsioon+ muud eeldused" pealt
  edasi arendatuna.

---------------------------------------------------------------
KOIK 11 TESTITUD PAARI
---------------------------------------------------------------
  juhtnaitaja -> hilisem naitaja          suund%   Pearson-p  Spearman-p
  ---------------------------------------  -------  ---------  ----------
  ADP -> Non Farm Payrolls                 52.9%    <0.0001*   0.839
    (*tekkis 3 COVID-erandist, ilma nendeta p=0.134 — vt eraldi kokkuvote)
  Jobless Claims -> Non Farm Payrolls      56.9%    0.705      0.092
  Jobless Claims -> Unemployment Rate      51.8%    0.367      0.371
  Empire State -> ISM Manufacturing        44.4%    0.128      0.309
  Philly Fed -> ISM Manufacturing          54.1%    0.316      0.379
  Dallas Fed -> ISM Manufacturing          57.6%    0.058      0.205
  Chicago PMI -> ISM Manufacturing         56.6%    0.129      0.118
  ISM Manufacturing -> Industrial Prod.    50.3%    0.537      0.768
  ISM Manufacturing -> Retail Sales        50.0%    0.488      0.574
  ISM Services -> Retail Sales             50.0%    0.966      0.848
  Philly Fed -> Industrial Production      48.6%    0.607      0.735

  MITTE UKSKI paar ei labi p<0.05 lavet MOLEMAL (Pearson JA
  Spearman) testil korraga. Suuna-kokkulangevus on 44-58%
  vahemikus koigil — see ON mündiviske vahemik.

---------------------------------------------------------------
LAHIM "PEAAEGU" — DALLAS FED, JA MIKS SEE EI KOLBA
---------------------------------------------------------------
  Dallas Fed -> ISM Manufacturing: Pearson p=0.058 (peaaegu
  0.05 lavi), AGA:
  - Spearman EI ole oluline (p=0.205)
  - Suuna-kokkulangevus EI ole oluline (57.6%, p=0.30)
  - Valim on vaike (n=61)
  - Ma testisin 11 hupoteesi KORRAGA — kui neist yks on
    p=0.058 lahedal, on see TAPSELT see, mida juhus 11 katse
    seast annaks (multiple testing). See EI OLE usaldusvaarne
    leid, see on mürasignaal.

---------------------------------------------------------------
JARELDUS
---------------------------------------------------------------
  Ausalt: EI leidnud yhtegi juhtnaitajat, mis paris ennustaks,
  kuhu jargmine suur uudis liigub. See klapib kolme asjaga:

  1. Turu enda loogikaga — kui selline seos oleks lihtne ja
     tugev, oleks seda ammu institutsionaalsete fondide poolt
     ara kasutatud ja kadunud (arbitraaz).
  2. Selle repo enda varasema ajalooga — origin/main'is on
     kymmekond sarnast katset (COT, D1 momentum, kalendri-
     reaktsioon, turustruktuur), millest peaaegu koik said
     "FAIL" voi "PROMISING BUT NOT PROVEN".
  3. Minu enda kahe testiga (see + ADP/NFP) — 11/11 EI.

  See EI TAHENDA, et sellist seost ei saa KUNAGI leida — aga
  see tahendab, et lihtsad, ilmsed juhtnaitaja-paarid seda ei
  paku. Paremaid kandidaate voiks olla kitsamad/spetsiifilisemad
  seosed (nt konkreetse sektori tarneahela andmed, satelliidi-
  andmed, krediitkaardikulutuste andmed) — aga need vajavad
  andmeallikaid, mida sellel liivakastil ega econ_cal'is pole.

---------------------------------------------------------------
KOKKUVOTE KOGU "UUDISE" UURIMISSUUNAST
---------------------------------------------------------------
  1. "Liigu uudise suunas kaasa PARAST" — EI toimi (lookahead
     parandatult -113 EUR, vt eraldi kokkuvote)
  2. "Ennusta ENNE uudist juhtnaitajaga" — EI toimi (11/11 testi)

  Molemad põhilised viisid, kuidas seda ideed proovida, on nuud
  ausalt testitud ja EI tootnud usaldusvaarset serva. Kui tahad
  midagi muud proovida, siis oleks aus vastus: liigume edasi
  millegi teise juurde, sest see konkreetne suund (uudiste-
  pohine kauplemine XAUUSD'il, saadaolevate andmetega) ei ole
  seni tootnud midagi, mis vastaks pidama.
===============================================================
