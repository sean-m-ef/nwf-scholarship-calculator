#!/bin/bash
# NWF Scholarship Calculator — Mac launcher
# Double-click this file in Finder to start the app.
# Installs uv and dependencies automatically on first run.

cd "$(dirname "$0")"

# --- Ensure uv is available ---
if ! command -v uv &> /dev/null; then
    export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing now..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if [ $? -ne 0 ]; then
        osascript -e 'display alert "Installation failed" message "Could not install required components.\n\nPlease check your internet connection and try again." as critical'
        exit 1
    fi
    export PATH="$HOME/.local/bin:$PATH"
fi

# --- Sync dependencies (fast no-op if already current) ---
uv sync --quiet
if [ $? -ne 0 ]; then
    osascript -e 'display alert "Setup failed" message "Dependency sync failed.\n\nPlease check your internet connection and try again." as critical'
    exit 1
fi

# --- Pre-launch reminder ---
osascript -e 'display dialog "The app will open in your browser momentarily.\n\nIMPORTANT: A background window will remain open in your Dock. Leave it running while you use the app — minimize it, do not close it.\n\nWhen finished, close the browser tab then close the background window." with title "NWF Scholarship Calculator" buttons {"OK"} default button "OK" with icon note'

# --- Trap exit to notify user the app has stopped ---
trap 'osascript -e "display notification \"The NWF Scholarship Calculator has stopped. You can now close this window.\" with title \"NWF Scholarship Calculator\""' EXIT

# --- Launch app ---
echo "Starting NWF Scholarship Calculator..."
echo ""
echo "The app is running. Minimize this window — do not close it."
echo "When finished, close your browser tab then close this window."
uv run marimo run app.py
