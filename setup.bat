@echo off
title CyberKavach - Auto Setup
color 0A

echo.
echo  ================================================
echo   CYBERKAVACH - SIH26145 Auto Setup
echo   AI-Based Cyber Threat Detection System
echo  ================================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Download from https://python.org/downloads
    echo         Make sure to tick "Add Python to PATH" during install.
    pause
    exit /b 1
)

echo [1/5] Python found:
python --version
echo.

REM Create venv if not exists
if not exist "venv\" (
    echo [2/5] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create venv. Check Python installation.
        pause
        exit /b 1
    )
    echo       Done!
) else (
    echo [2/5] Virtual environment already exists. Skipping.
)
echo.

REM Install dependencies
echo [3/5] Installing Python dependencies (this may take 2-3 minutes)...
venv\Scripts\pip install --upgrade pip --quiet
venv\Scripts\pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo [ERROR] Dependency installation failed. Check requirements.txt.
    pause
    exit /b 1
)
echo       Done!
echo.

REM Copy .env if not exists
if not exist ".env" (
    echo [4/5] Creating .env config file from template...
    copy .env.example .env >nul
    echo       Done! Open .env to set your CAPTURE_INTERFACE if needed.
) else (
    echo [4/5] .env already exists. Skipping.
)
echo.

echo [5/5] Setup complete!
echo.
echo  ================================================
echo   HOW TO RUN:
echo     python run_server.py
echo   OR just double-click:
echo     run_server.bat
echo.
echo   Then open: http://localhost:8000
echo.
echo   NOTE (Windows): Run as Administrator for
echo   packet capture to work properly.
echo  ================================================
echo.
pause
