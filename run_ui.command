#!/bin/bash
# ==========================================
# Scrapling Control Panel - UI Launcher
# Double-click this file on Mac to run
# ==========================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo " Scrapling Control Panel Launcher"
echo " ==========================================="
echo ""

# ---- Find Python ----
PYTHON_CMD=""

if [ -d ".venv" ] && [ -f ".venv/bin/python" ]; then
    PYTHON_CMD=".venv/bin/python"
    echo " Using .venv Python"
elif [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    PYTHON_CMD="venv/bin/python"
    echo " Using venv Python"
elif command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    echo " Using system python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
    echo " Using system python"
else
    echo " ERROR: Python not found!"
    echo " Please run setup.command first."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

echo " Python: $($PYTHON_CMD --version 2>&1)"
echo ""

# ---- Check if Scrapling is installed ----
$PYTHON_CMD -c "import scrapling" 2>/dev/null
if [ $? -ne 0 ]; then
    echo " WARNING: Scrapling not installed in this environment."
    echo " Run setup.command first, or:"
    echo "   source .venv/bin/activate && pip install scrapling"
    echo ""
fi

# ---- Launch the UI server ----
echo " Starting Scrapling Control Panel..."
echo " UI will open at http://localhost:8888"
echo " Press Ctrl+C to stop the server."
echo ""

$PYTHON_CMD scrapling_server.py

echo ""
echo " Server stopped."
read -p "Press Enter to close..."
