@echo off
REM NWF Scholarship Calculator — Windows launcher
REM Double-click this file to start the app.
REM The browser will open automatically.

REM cd to the directory containing this script
cd /d "%~dp0"

REM Check for uv
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: uv is not installed.
    echo.
    echo Please install uv by opening PowerShell and running:
    echo     winget install astral-sh.uv
    echo.
    echo Or visit: https://docs.astral.sh/uv/getting-started/installation/
    echo.
    pause
    exit /b 1
)

echo Starting NWF Scholarship Calculator...
uv run marimo run app.py
