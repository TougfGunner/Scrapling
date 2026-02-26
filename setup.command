#!/bin/bash

# ==========================================
# Scrapling - Bali Bliss Weddings Setup Script
# Double-click this file on Mac to run
# ==========================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo "  Scrapling Setup for Bali Bliss Weddings"
echo "=========================================="
echo ""

# ---- Fix broken .zprofile Homebrew references ----
if [ -f "$HOME/.zprofile" ]; then
    if grep -q 'homebrew' "$HOME/.zprofile" 2>/dev/null; then
        if ! command -v brew &> /dev/null; then
            echo "  Cleaning broken Homebrew lines from .zprofile..."
            grep -v 'homebrew' "$HOME/.zprofile" > "$HOME/.zprofile.tmp" 2>/dev/null
            mv "$HOME/.zprofile.tmp" "$HOME/.zprofile" 2>/dev/null
            echo "  .zprofile cleaned"
        fi
    fi
fi

# ---- Step 1: Check for existing virtual environment ----
VENV_DIR=""
SKIP_INSTALL=false

if [ -d ".venv" ] && [ -f ".venv/bin/python" ]; then
    VENV_DIR=".venv"
    echo "  Found existing .venv"
elif [ -d "venv" ] && [ -f "venv/bin/python" ]; then
    VENV_DIR="venv"
    echo "  Found existing venv"
fi

# If venv exists, check if Python in it works
if [ -n "$VENV_DIR" ]; then
    source "$VENV_DIR/bin/activate"
    VENV_PY_VER=$("$VENV_DIR/bin/python" -c 'import sys; print(sys.version_info.minor)' 2>/dev/null)
    if [ -n "$VENV_PY_VER" ]; then
        echo "  Python 3.$VENV_PY_VER found in $VENV_DIR"
        if [ "$VENV_PY_VER" -ge 10 ] 2>/dev/null; then
            echo "  Python version OK (3.10+ required)"
            SKIP_INSTALL=true
        else
            echo "  Python 3.$VENV_PY_VER is too old (need 3.10+)"
            echo "  Will need to recreate venv..."
            deactivate 2>/dev/null
            VENV_DIR=""
        fi
    else
        echo "  Venv Python is broken, will recreate..."
        deactivate 2>/dev/null
        VENV_DIR=""
    fi
fi

echo ""

# ---- Step 2: Only install Homebrew + Python if no working venv ----
if [ "$SKIP_INSTALL" = false ]; then
    echo "  No working Python 3.10+ venv found. Setting up from scratch..."
    echo ""

    # Find Python 3.10+ on system
    PYTHON_CMD=""
    for ver in python3.13 python3.12 python3.11 python3.10; do
        if command -v $ver &> /dev/null; then
            PYTHON_CMD=$ver
            break
        fi
    done

    # Check default python3
    if [ -z "$PYTHON_CMD" ] && command -v python3 &> /dev/null; then
        PY_VER=$(python3 -c 'import sys; print(sys.version_info.minor)' 2>/dev/null)
        if [ -n "$PY_VER" ] && [ "$PY_VER" -ge 10 ] 2>/dev/null; then
            PYTHON_CMD=python3
        fi
    fi

    # If no Python 3.10+, try installing via Homebrew
    if [ -z "$PYTHON_CMD" ]; then
        echo "  No Python 3.10+ found on system."
        echo ""

        # Check/install Homebrew
        if ! command -v brew &> /dev/null; then
            echo "  Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

            # Add to PATH
            if [ -f /opt/homebrew/bin/brew ]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
                echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
            elif [ -f /usr/local/bin/brew ]; then
                eval "$(/usr/local/bin/brew shellenv)"
                echo 'eval "$(/usr/local/bin/brew shellenv)"' >> "$HOME/.zprofile"
            fi
        fi

        # Verify brew actually works now
        if command -v brew &> /dev/null; then
            echo "  Installing Python 3.11 via Homebrew..."
            brew install python@3.11
            PYTHON_CMD=python3.11
        else
            echo ""
            echo "  ERROR: Homebrew installation failed."
            echo "  This is usually a network issue."
            echo ""
            echo "  Try these manual fixes:"
            echo "   1. Check your internet connection"
            echo "   2. Try: curl -fsSL https://raw.githubusercontent.com"
            echo "   3. If on VPN, try disconnecting it"
            echo "   4. Install Homebrew manually: https://brew.sh"
            echo ""
            read -p "Press Enter to close..."
            exit 1
        fi
    fi

    echo "  Using: $($PYTHON_CMD --version)"
    echo ""

    # Remove broken venv if exists
    if [ -n "$VENV_DIR" ]; then
        rm -rf "$VENV_DIR"
    fi

    # Create new venv
    echo "  Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
    VENV_DIR=".venv"
    source "$VENV_DIR/bin/activate"
    echo "  Virtual environment created"
fi

echo "  Python: $(python --version)"
echo "  Venv: $VENV_DIR"
echo ""

# ---- Step 3: Install Scrapling ----
echo "  Upgrading pip..."
pip install --upgrade pip 2>&1 | tail -1
echo ""

echo "  Installing Scrapling with all extras..."
pip install "scrapling[all]" 2>&1 | tail -5
echo ""
echo "  Scrapling installed"
echo ""

# ---- Step 4: Install Browser Engines ----
echo "  Installing browser engines..."
scrapling install 2>&1 | tail -3 || echo "  (browser engines may need manual setup)"
echo ""

# ---- Step 5: Quick Test ----
echo "  Running quick test..."
python -c "
try:
    from scrapling import Fetcher
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