@echo off
REM ============================================================
REM  NEMSIS bot - uuenda ja kaivita
REM  Tee topeltklikk sellel failil.
REM ============================================================
cd /d "%~dp0"
title NEMSIS bot

echo.
echo ============================================
echo   1/3  Tombran GitHubist uue koodi...
echo ============================================
git pull
if errorlevel 1 (
    echo.
    echo  !!! git pull ebaonnestus.
    echo  !!! Bot EI ole uuendatud. Saada see aken pildina Claude'ile.
    echo.
    pause
    exit /b 1
)

echo.
echo ============================================
echo   2/3  Kontrollin, kas kood on terve...
echo ============================================
python -m py_compile main_v4.py config.py gold_logic.py strategies.py mt5_connector.py strategy_meanrev.py
if errorlevel 1 (
    echo.
    echo  !!! Kood on katki - botti EI kaivitatud.
    echo  !!! Saada see aken pildina Claude'ile.
    echo.
    pause
    exit /b 1
)
echo  Kood on terve.

echo.
echo ============================================
echo   3/3  Kaivitan boti...
echo ============================================
echo  Telegrami peaks tulema kaivitusteade.
echo  Seda akent EI TOHI kinni panna - bot jookseb siin.
echo  Peatamiseks: Ctrl+C
echo.
python main_v4.py

echo.
echo  Bot peatus. Vajuta klahvi akna sulgemiseks.
pause
