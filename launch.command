#!/bin/bash
# NWF Scholarship Calculator — Mac launcher
# Double-click this file in Finder to start the app.
# The browser will open automatically.

# cd to the directory containing this script, regardless of where it's launched from
cd "$(dirname "$0")"

# Check for uv
if ! command -v uv &> /dev/null; then
    osascript -e 'display alert "uv not found" message "Please install uv first:\n\nbrew install uv\n\nOr visit: https://docs.astral.sh/uv/getting-started/installation/" as critical'
    exit 1
fi

# uv run handles venv creation and dependency install automatically on first run
echo "Starting NWF Scholarship Calculator..."
uv run marimo run app.py
