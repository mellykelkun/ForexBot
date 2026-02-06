@echo off
echo ========================================
echo   FOREXBOT - REDEMARRAGE CORRIGE
echo ========================================
echo.
echo [1/3] Arret du ForexBot...
taskkill /IM python.exe /F >nul 2>&1
timeout /t 2 /nobreak >nul
echo [2/3] Activation environnement virtuel...
call venv\Scripts\activate.bat
echo [3/3] Redemarrage...
python main.py
pause