#!/bin/bash

# ==========================================
# Scrapling - Bali Bliss Weddings Setup Script
# Double-click this file on Mac to run
# ==========================================

cd "$(dirname "$0")"

echo ""
echo "  Scrapling Setup for Bali Bliss Weddings"
echo "=========================================="
echo ""

# ---- Fix broken .zprofile Homebrew references ----
if [ -f "$HOME/.zprofile" ]; then
    if grep -q '/opt/homebrew/bin/brew' "$HOME/.zprofile" 2>/dev/null || grep -q '/usr/local/bin/brew' "$HOME/.zprofile" 2>/dev/null; then
        if ! command -v brew &> /dev/null; then
            echo "  Fixing broken Homebrew references in .zprofile..."
            sed -i '' '/\/opt\/homebrew\/bin\/brew/d' "$HOME/.zprofile" 2>/dev/null
            sed -i '' '/\/usr\/local\/bin\/brew/d' "$HOME/.zprofile" 2>/dev/null
            echo "  .zprofile cleaned"
        fi
    fi
fi

# ---- Check for Homebrew ----
if ! command -v brew &> /dev/null; then
    echo "  Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH (Apple Silicon & Intel)
    if [[ -f /opt/homebrew/bin/brew ]]; then
        eval "$(/opt/homebrew/bin/brew shellenv)"
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
    elif [[ -f /usr/local/bin/brew ]]; then
        eval "$(/usr/local/bin/brew shellenv)"
        echo 'eval "$(/usr/local/bin/brew shellenv)"' >> "$HOME/.zprofile"
    fi
    echo "  Homebrew installed"
else
    echo "  Homebrew already installed"
fi

# ---- Find best Python 3.10+ ----
PYTHON_CMD=""
for ver in python3.13 python3.12 python3.11 python3.10; do
    if command -v $ver &> /dev/null; then
        PYTHON_CMD=$ver
        break
    fi
done

# Check default python3
if [ -z "$PYTHON_CMD" ] && command -v python3 &> /dev/null; then
    PY_VER=$(python3 -c 'import sys; print(sys.version_info.minor)')
    if [ "$PY_VER" -ge 10 ]; then
        PYTHON_CMD=python3
    fi
fi

# Install Python 3.11 if nothing found
if [ -z "$PYTHON_CMD" ]; then
    echo "  No Python 3.10+ found. Installing Python 3.11..."
    brew install python@3.11
    PYTHON_CMD=python3.11
    echo "  Python 3.11 installed"
else
    echo "  Found: $($PYTHON_CMD --version)"
fi

echo ""

# ---- Create or reuse Virtual Environment ----
VENV_DIR=""
if [ -d ".venv" ]; then
    VENV_DIR=".venv"
    echo "  Found existing .venv"
elif [ -d "venv" ]; then
    VENV_DIR="venv"
    echo "  Found existing venv"
else
    echo "  Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    VENV_DIR=".venv"
    echo "  Virtual environment created"
fi

# Activate venv
source "$VENV_DIR/bin/activate"
echo "  Virtual environment activated"
echo "   Python: $(python --version)"
echo ""

# ---- Check Python version in venv ----
VENV_PY_VER=$(python -c 'import sys; print(sys.version_info.minor)')
if [ "$VENV_PY_VER" -lt 10 ]; then
    echo "  Your venv uses Python 3.$VENV_PY_VER but Scrapling needs 3.10+"
    echo "   Recreating venv with $PYTHON_CMD..."
    deactivate 2>/dev/null
    rm -rf "$VENV_DIR"
    $PYTHON_CMD -m venv .venv
    VENV_DIR=".venv"
    source "$VENV_DIR/bin/activate"
    echo "  New venv created with $(python --version)"
fi
echo ""

# ---- Install Scrapling ----
echo "  Upgrading pip..."
pip install --upgrade pip
echo ""

echo "  Installing Scrapling with all extras..."
pip install "scrapling[all]"
echo ""
echo "  Scrapling installed"
echo ""

# ---- Install Browser Engines ----
echo "  Installing browser engines (Playwright, Camoufox)..."
scrapling install || echo "  Browser engine install had warnings (may be OK)"
echo ""
echo "  Browser engines installed"
echo ""

# ---- Quick Test ----
echo "  Running quick test..."
python -c "
from scrapling import Fetcher
try:
    page = Fetcher().get('https://httpbin.org/get')
    if page:
        print('    Basic Fetcher: WORKING')
    else:
        print('    Basic Fetcher: FAILED')
except Exception as e:
    print(f'    Basic Fetcher error: {e}')

try:
    from scrapling.fetchers import StealthyFetcher
    print('    StealthyFetcher: AVAILABLE')
except Exception as e:
    print(f'    StealthyFetcher: {e}')

try:
    from scrapling.core.ai import ScraplingMCPServer
    print('    MCP Server: AVAILABLE')
except Exception as e:
    print(f'    MCP Server: {e}')

print('')
print('  Scrapling is ready for Bali Bliss!')
"

echo ""
echo "=========================================="
echo "  Setup complete!"
echo ""
echo "Commands you can run:"
echo ""
echo "   Start MCP Server:"
echo "    source $VENV_DIR/bin/activate"
echo "    python -c \"from scrapling.core.ai import ScraplingMCPServer; ScraplingMCPServer().serve(True, '127.0.0.1', 8000)\""
echo ""
echo "   Quick scrape test:"
echo "    source $VENV_DIR/bin/activate"
echo "    python -c \"from scrapling import Fetcher; print(Fetcher().get('https://quotes.toscrape.com').css_first('.quote .text').text)\""
echo ""
echo "   Open in VS Code:"
echo "    code ."
echo "=========================================="
echo ""
read -p "Press Enter to close..."