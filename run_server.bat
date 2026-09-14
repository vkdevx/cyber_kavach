@echo off
title CyberKavach Threat Detection & Defence System
cd /d "%~dp0"
echo =================================================================
echo    CYBERKAVACH (SIH26145) - AI CYBER THREAT DEFENCE SYSTEM
echo =================================================================
echo.

if exist venv\Scripts\uvicorn.exe (
    echo [*] Starting CyberKavach using venv environment...
    venv\Scripts\uvicorn.exe backend.api.main:app --host 0.0.0.0 --port 8000 --reload
) else if exist venv\Scripts\python.exe (
    echo [*] Starting CyberKavach via Python venv module...
    venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    echo [*] Starting CyberKavach via system Python...
    python -m uvicorn backend.api.main:app --host 0.0.0.0 --port 8000 --reload
)

pause
