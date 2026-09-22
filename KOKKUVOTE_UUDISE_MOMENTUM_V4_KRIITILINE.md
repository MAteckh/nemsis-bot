===============================================================
TEST v4 (250 EUR, 5x0.05 lot XAUUSD korraga) — KONTO SAI OTSA
ESIMESE NADALAGA
===============================================================
  Ainult test. Koodis EI MUUDETUD midagi, midagi EI DEPLOY'ITUD.

  Tegin tapselt sinu kirjelduse jargi: 250 EUR pank, 5 tehingut
  x 0.05 lot (=0.25 lot kokku) XAUUSD-l KORRAGA, sama suund,
  uudise peale koos sisse, trailing SL kogu aeg, mitte tihedam
  kui 50 EUR kahjumi vaste UHE 0.05-lotise jala kohta.

  TULEMUS ON SELGE JA OTSENE: ESIMENE tehing kogu 2.4-aastases
  testis (2024-05-02, sundmus "Imports" — TAVALINE, MITTE
  isegi suur uudis) kaotas TAPSELT -250.00 EUR. KOGU algkapital.
  Uhe tehinguga. Kontol jai jargi 0.00 EUR.

  Kolmas tehing (2024-05-08) viis konto -118.45 EUR peale —
  MIINUSESSE. Paris broker'i juures oleks konto selleks hetkeks
  ammu suletud (margin call / negative balance protection),
  mitte lastud edasi kaubelda.

---------------------------------------------------------------
MIKS SEE JUHTUB — MATEMAATIKA ON LIHTNE
---------------------------------------------------------------
  5 tehingut, SAMA suund, SAMA instrument (XAUUSD), SAMA
  hetk. See ei ole 5x hajutatud risk — see on 1x risk 5x
  SUURUSES. Kui hind laheb vastu, tabavad KOIK 5 oma SL-i
  PEAAEGU KOOS (nagu esimeses tehingus juhtuski).

  Igal jalal on SL-floor 50 EUR = kokku 5 x 50 EUR = 250 EUR
  maksimaalne UHEKORDNE risk. See on TAPSELT 100% sinu
  kirjeldatud 250 EUR algkapitalist. Matemaatiliselt on see
  "koik-sisse" panus uhele sundmusele, mitte riskijuhtimine.

---------------------------------------------------------------
LOPP-TULEMUS ON PETLIK — LOE HOOLIKALT
---------------------------------------------------------------
  Kui vaatan AINULT lopp-numbrit (koik 301 tehingut kokku
  arvestatuna, nagu kontol oleks lubatud jatkata pärast
  miinuses kaimist), naitab see +89 079 EUR. See number on
  VOLTS, sest see EELDAB, et keegi paneks kontole raha juurde
  peale esimest -250 EUR kaotust ja lubaks jatkata — paris
  broker'i juures see nii ei toimi. Kontol EI OLE olemas
  tehinguid 4 kuni 301, sest konto sai otsa tehingul 1.

---------------------------------------------------------------
KOKKUVOTE
---------------------------------------------------------------
  seade                            vaartus
  -------------------------------  -----------------------
  algkapital                       250 EUR
  1. tehingu tulemus                -250.00 EUR (0.00 EUR jargi)
  3. tehingu tulemus (kumulatiivne) -118.45 EUR (KONTO OTSAS)
  sundmus, mis lopetas konto        "Imports" (tavaline andmed,
                                    mitte isegi Fed/NFP/CPI)

---------------------------------------------------------------
MINU SOOVITUS
---------------------------------------------------------------
  Selle suurusega (5x0.05 = 0.25 lot koos, min 50 EUR SL-i
  floor) EI SAA seda 250 EUR kontol turvaliselt teha — see
  test naitab konto otsalemist esimese nadalaga, mitte
  hüpoteetilist riski. Kui tahad jatkata SAMA ideega
  (uudise-suunas, trailing SL), on kaks paris valikut:

  1. VAHENDA positsiooni suurust drastiliselt (nt 1 tehing,
     mitte 5, VOI 0.01 lot 5 tehingu asemel 0.05) — nii et
     UHEL sundmusel kadu ei ulataks lahedalegi 100% kontost.

  2. Kasuta RISK-POHIST lot'i (nagu bot mujal juba teeb,
     risk_pct=1.5%) fikseeritud lot'i asemel — see automaatselt
     VAHENDAB lot'i, kui konto on vaike, mitte ei riski sama
     dollari-summat sõltumata balance'ist.

  Kumba proovin?
===============================================================
