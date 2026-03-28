#!/bin/bash
# NWF Scholarship Calculator — Mac launcher
# Double-click this file in Finder to start the app.
# Installs uv and dependencies automatically on first run.

cd "$(dirname "$0")"

# --- Ensure uv is available ---
if ! command -v uv &> /dev/null; then
    # Add uv's default user install location in case it's installed but not on PATH
    export PATH="$HOME/.local/bin:$PATH"
fi

if ! command -v uv &> /dev/null; then
    echo "uv not found. Installing now..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    if [ $? -ne 0 ]; then
        osascript -e 'display alert "Installation failed" message "Could not install uv automatically.\n\nPlease visit https://docs.astral.sh/uv/getting-started/installation/ and install manually, then try again." as critical'
        exit 1
    fi
    export PATH="$HOME/.local/bin:$PATH"
fi

# --- Sync dependencies (fast no-op if already current) ---
uv sync --quiet
if [ $? -ne 0 ]; then
    echo "ERROR: Dependency sync failed. Check your internet connection and try again."
    read -p "Press Enter to close..."
    exit 1
fi

# --- Launch app ---
echo "Starting NWF Scholarship Calculator..."
uv run marimo run app.py
