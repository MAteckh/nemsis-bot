===============================================================
TEST: KAS ADP ENNUSTAB NFP ÜLLATUST? — EI, JA SEE ON HUVITAV LUGU
===============================================================
  Ainult test. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD,
  midagi PÄRIS ei puudutatud.

  Idee: ADP Employment Change avaldatakse ~2 päeva ENNE Non Farm
  Payrolls'i, sama kuu kohta. Kas ADP üllatuse SUUND (actual vs
  forecast) ennustab NFP üllatuse suunda paremini kui juhus?
  Kui jah, saaks ENNE NFP-d positsiooni panna.

---------------------------------------------------------------
ANDMED
---------------------------------------------------------------
  econ_cal, 2013-2026, 154 paari (ADP avaldatud 0-2 päeva enne
  vastavat NFP-d).

---------------------------------------------------------------
TULEMUS — ESIMENE VAADE NÄGI HEA VÄLJA, AGA OLI PETLIK
---------------------------------------------------------------
  naitaja                              vaartus
  ------------------------------------ ------------------------
  Pearson korrelatsioon (ADP vs NFP)   r=0.895  p<0.0001  (!!)
  Spearman (auaste-)korrelatsioon      rho=-0.017  p=0.84
  Suuna kokkulangevus                  81/153 = 52.9%  p=0.52

  Pearson r=0.895 näeb tugevast tugev välja. AGA Spearman
  (mis ei lase üksikutel äärmuslikel väärtustel domineerida)
  näitab PEAAEGU NULLI. See vastuolu tähendab: korrelatsioon
  tuleb paarist ÄÄRMUSLIKUST punktist, mitte üldisest mustrist.

---------------------------------------------------------------
MIS NEED ÄÄRMUSED OLID
---------------------------------------------------------------
  kuupaev        ADP üllatus     NFP üllatus
  -------------  --------------  --------------
  2020-06-05      +6 240 000      +10 509 000
  2020-07-02        -631 000       +1 800 000
  2020-05-08        -236 000       +1 500 000

  KOIK KOLM on COVID-19 pandeemia tööturu kokkuvarisemise/
  taastumise kuud — ajaloos ENNENÄGEMATA suurusjärgus üllatused
  (10-20x tavalisest kuust suuremad). Kui need 3 kuud testist
  eemaldada:

  Pearson korrelatsioon ILMA 3 suurima äärmuseta:
    r = -0.122  p=0.134  (n=151) — EI OLE olulisel positiivne,
    kui midagi, siis kergelt NEGATIIVNE.

---------------------------------------------------------------
JARELDUS
---------------------------------------------------------------
  ADP EI ENNUSTA NFP üllatuse suunda. Tavalistel (mitte-COVID)
  kuudel on suund tabamus 52.9% — statistiliselt eristamatu
  mündiviskest (p=0.52). See "hea" Pearson-korrelatsioon oli
  statistiline artefakt 3 erakordsest pandeemia-kuust, mitte
  paris seaduspara.

  See klapib laialt tuntud finantsajakirjanduse/majandus-
  analüütikute tähelepanekuga, et ADP on ajalooliselt olnud
  ebausaldusväärne NFP ennustaja — see EI OLE uus leid, aga
  nuud on see selle repo enda andmetega kinnitatud, mitte
  ainult kuulduse pohjal.

---------------------------------------------------------------
MIS JÄRGMISEKS
---------------------------------------------------------------
  See on 1/mitmest voimalikust juhtnaitaja-paarist. Teisi, mida
  saaks sama meetodiga testida:
  - Initial Jobless Claims (iganadalane) trend → Unemployment Rate
  - ISM Manufacturing/Services PMI → järgnev laiem kasvunumber
  - Philadelphia Fed / NY Empire State → hilisem tootmisandmed

  Kas proovin mõnda neist, või on see piisav vastus praegu?
===============================================================
