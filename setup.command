#!/bin/bash

# ============================================
# Scrapling - Bali Bliss Weddings Setup Script
# Double-click this file on Mac to run
# ============================================

set -e
cd "$(dirname "$0")"

echo ""
echo "🕷️  Scrapling Setup for Bali Bliss Weddings"
echo "============================================"
echo ""

# --- Check for Homebrew ---
if ! command -v brew &> /dev/null; then
    echo "🍺 Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add Homebrew to PATH (Apple Silicon & Intel)
    if [[ -f /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f /usr/local/bin/brew ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
    fi
    echo "✅ Homebrew installed"
else
    echo "✅ Homebrew already installed"
fi

# --- Check for Python 3.11 ---
if command -v python3.11 &> /dev/null; then
    PYTHON_CMD=python3.11
    echo "✅ Python 3.11 found"
elif command -v python3.12 &> /dev/null; then
    PYTHON_CMD=python3.12
    echo "✅ Python 3.12 found"
elif command -v python3.13 &> /dev/null; then
    PYTHON_CMD=python3.13
    echo "✅ Python 3.13 found"
else
    echo "🐍 Installing Python 3.11..."
    brew install python@3.11
    PYTHON_CMD=python3.11
    echo "✅ Python 3.11 installed"
fi

echo "   Using: $($PYTHON_CMD --version)"
echo ""

# --- Create Virtual Environment ---
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate venv
source venv/bin/activate
echo "✅ Virtual environment activated"
echo ""

# --- Install Scrapling ---
echo "📥 Installing Scrapling with all extras..."
pip install --upgrade pip
pip install "scrapling[all]"
echo "✅ Scrapling installed"
echo ""

# --- Install Browser Engines ---
echo "🌐 Installing browser engines (Playwright, Camoufox)..."
scrapling install
echo "✅ Browser engines installed"
echo ""

# --- Quick Test ---
echo "🧪 Running quick test..."
python -c "
from scrapling import Fetcher
page = Fetcher().get('https://httpbin.org/get')
print('   Response status: OK' if page else '   Response status: FAILED')
print('   Scrapling is working! 🎉')
"
echo ""

echo "============================================"
echo "✅ Setup complete!"
echo ""
echo "To start working:"
echo "  cd $(pwd)"
echo "  source venv/bin/activate"
echo ""
echo "Run MCP Server:"
echo "  python -c \"from scrapling.core.ai import ScraplingMCPServer; ScraplingMCPServer().serve(True, '127.0.0.1', 8000)\""
echo ""
echo "Run a quick scrape:"
echo "  python -c \"from scrapling import Fetcher; print(Fetcher().get('https://quotes.toscrape.com').css_first('.quote .text').text)\""
echo ""
echo "Open in VS Code:"
echo "  code ."
echo "============================================"
echo ""
read -p "Press Enter to close..."
