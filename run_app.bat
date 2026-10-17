@echo off
title PathReady AI Suite - Interview Readiness & Career Path Guidance
setlocal
cd /d "%~dp0"

echo ======================================================================
echo           PathReady AI Suite - Research Demonstration Server          
echo   Spoken Communication NLP Guidance & CV-Based Career Path Guidance   
echo ======================================================================
echo.
echo Starting Unified FastAPI Server on http://127.0.0.1:8000 ...
echo.

start "" "http://127.0.0.1:8000"
python -m uvicorn app.main:app --reload --port 8000

endlocal
pause
