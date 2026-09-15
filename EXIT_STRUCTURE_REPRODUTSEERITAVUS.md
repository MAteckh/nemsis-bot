===============================================================
EXIT STRUCTURE FALSIFICATION v1 — KORDUSJOOKSU KONTROLL
===============================================================
  kuupaev 2026-09-15
  branch  claude/great-noether-um7382
  commit  a9d3fed

---------------------------------------------------------------
1. KORDUSJOOKS
---------------------------------------------------------------
  Kaivitati bot/exit_structure_falsification.py teist korda
  algusest lopuni, samad fikseeritud seemned (20260915).
  Exit code: 0

  Vorreldi md5-summasid ENNE ja PARAST kordusjooksu:

  fail                        md5 (esimesed 32)                 tulem
  ----                        -----------------                 -----
  EXIT_SL_RESULTS.csv         5841061af6dccac2b598bc58ff67634b  OK
  EXIT_TP_RESULTS.csv         ca5b5916a86c43b9008806ed59e90291  OK
  EXIT_HOLD_RESULTS.csv       fac70de382d0089faffd9c0acfe27d9a  OK
  EXIT_SL_TP_GRID.csv         3fb04a4d69abf8a02d2256af1b03ecda  OK
  EXIT_PAIR_RESULTS.csv       a1d8b68d62615398cac754eb22cbf4df  OK
  EXIT_COST_STRESS.csv        7ebc8a7e079b4d5f4097f8a5215d9a6f  OK
  EXIT_ENTRY_VS_EXIT.csv      bfb026fd6e0635984fdb43b8e655b1d6  OK

  TULEM: 7/7 baidi-identsed. REPRODUTSEERITAV.

---------------------------------------------------------------
2. LIVE-FAILIDE PUUTUMATUS
---------------------------------------------------------------
  git diff HEAD -- main_v4.py config.py mt5_connector.py
                   strategy_meanrev.py backtest.py
                   (+ bot/ vasted)
  => TUHI. Ukski live-fail ei ole muudetud.

  Juur vs bot/ sunkroonis (diff read):
    main_v4.py          0
    config.py           0
    mt5_connector.py    0
    strategy_meanrev.py 0
    backtest.py         0
    gold_logic.py       0
    strategies.py       0

---------------------------------------------------------------
3. REPO SEIS
---------------------------------------------------------------
  git status --porcelain  => tuhi (puhas)
  local  HEAD             a9d3fedee122d569b673cbc7edc3e9c9369e027a
  origin HEAD             a9d3fedee122d569b673cbc7edc3e9c9369e027a
  => sunkroonis, koik pushitud.

---------------------------------------------------------------
4. MIDA SEE EI TOENDA
---------------------------------------------------------------
  Kordusjooks toendab AINULT determinismi — et sama kood samade
  seemnetega annab sama tulemuse. See EI toenda, et tulemus on
  oige, ega muuda verdikti.

  VERDIKT JAAB: E) FAIL — valjumisstruktuur ei ole serva allikas.
