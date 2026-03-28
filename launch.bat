@echo off
REM NWF Scholarship Calculator — Windows launcher
REM Double-click this file to start the app.
REM Installs uv and dependencies automatically on first run (no admin rights required).

cd /d "%~dp0"

REM --- Ensure uv is on PATH (user-level install, no elevation needed) ---
where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    REM Add uv's default user install location in case it's installed but not on PATH
    set PATH=%USERPROFILE%\.local\bin;%PATH%
    where uv >nul 2>&1
)

if %ERRORLEVEL% neq 0 (
    echo uv not found. Installing now (no admin rights required)...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if %ERRORLEVEL% neq 0 (
        echo.
        echo ERROR: Could not install uv.
        echo Please visit https://docs.astral.sh/uv/getting-started/installation/ and install manually.
        pause
        exit /b 1
    )
    REM Add to PATH for this session
    set PATH=%USERPROFILE%\.local\bin;%PATH%
)

REM --- Sync dependencies (fast no-op if already current) ---
uv sync --quiet
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Dependency sync failed. Check your internet connection and try again.
    pause
    exit /b 1
)

REM --- Launch app ---
echo Starting NWF Scholarship Calculator...
uv run marimo run app.py
