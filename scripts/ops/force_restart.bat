@echo off
echo ========================================
echo   FOREXBOT - REDEMARRAGE FORCE
echo ========================================
echo.
echo [1/4] Arret complet du ForexBot...
taskkill /IM python.exe /F /T >nul 2>&1
echo [2/4] Attente de 3 secondes...
timeout /t 3 /nobreak >nul
echo [3/4] Nettoyage du cache Python...
python -c "import sys; sys.modules.clear()" >nul 2>&1
echo [4/4] Redemarrage du systeme...
cd /d C:\ForexBot
python main.py
echo.
echo Si le bot ne se relance pas automatiquement,
echo allez dans C:\ForexBot et lancez: python main.py
pause