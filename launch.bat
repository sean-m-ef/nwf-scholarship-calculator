@echo off
REM NWF Scholarship Calculator — Windows launcher
REM Double-click this file to start the app.
REM Installs uv and dependencies automatically on first run (no admin rights required).

cd /d "%~dp0"

REM Set a persistent title as a reminder while the app is running
title NWF Scholarship Calculator — Keep this window open (minimize, don't close)

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
        powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Could not install required components.`n`nPlease check your internet connection and try again.', 'NWF Scholarship Calculator — Error', 'OK', 'Error')"
        exit /b 1
    )
    set PATH=%USERPROFILE%\.local\bin;%PATH%
)

REM --- Sync dependencies (fast no-op if already current) ---
uv sync --quiet
if %ERRORLEVEL% neq 0 (
    powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('Dependency sync failed.`n`nPlease check your internet connection and try again.', 'NWF Scholarship Calculator — Error', 'OK', 'Error')"
    exit /b 1
)

REM --- Pre-launch reminder ---
powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('The app will open in your browser momentarily.`n`nIMPORTANT: A background window will appear in your taskbar. Leave it running while you use the app — minimize it, do not close it.`n`nWhen you are finished, close the browser tab and then close the background window.', 'NWF Scholarship Calculator', 'OK', 'Information')"

REM --- Launch app ---
echo Starting NWF Scholarship Calculator...
echo.
echo The app is running. Minimize this window - do not close it.
echo When finished, close your browser tab then close this window.
uv run marimo run app.py

REM --- App has stopped ---
powershell -command "Add-Type -AssemblyName PresentationFramework; [System.Windows.MessageBox]::Show('The NWF Scholarship Calculator has stopped.`n`nYou can now close this window.', 'NWF Scholarship Calculator', 'OK', 'Information')"
