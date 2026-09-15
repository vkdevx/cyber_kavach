@echo off
title CyberKavach - Auto GitHub Sync Watcher
color 0B

echo ===================================================
echo   CyberKavach Automated Git Synchronizer
echo   Monitors file changes and auto-pushes to GitHub
echo ===================================================
echo.

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe auto_commit_watcher.py
) else (
    python auto_commit_watcher.py
)

pause
