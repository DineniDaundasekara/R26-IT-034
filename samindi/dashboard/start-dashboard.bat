@echo off
title PathReady Dashboard Launcher
setlocal
cd /d "%~dp0"

echo Starting Dashboard API on Port 8010...
start "[API 8010] Dashboard API" cmd /k "cd /d "%~dp0backend" && python -m uvicorn app:app --host 127.0.0.1 --port 8010"
timeout /t 2 /nobreak >nul

echo Starting Dashboard Frontend on Port 5180...
start "[UI 5180] Dashboard Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo Dashboard running at: http://127.0.0.1:5180
echo.
echo For the full integrated platform (recommended for viva), from repo root run:
echo   python -m uvicorn app.main:app --reload --port 8000
echo   then open http://127.0.0.1:8000  (includes Employability / Career Simulation)
echo.
echo To start all sub-components at once, run: ..\start-all.bat
start http://127.0.0.1:5180
endlocal
