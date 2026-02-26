#!/bin/bash

# ============================================
# Scrapling MCP Server - Bali Bliss Weddings
# Double-click this file on Mac to start
# ============================================

cd "$(dirname "$0")"

echo ""
echo "🤖 Starting Scrapling MCP Server"
echo "============================================"
echo ""

# Check venv exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "   Run setup.command first."
    echo ""
    read -p "Press Enter to close..."
    exit 1
fi

# Activate venv
source venv/bin/activate
echo "✅ Virtual environment activated"
echo "✅ Python: $(python --version)"
echo ""

# Start MCP Server
echo "🚀 MCP Server starting on http://127.0.0.1:8000"
echo "   Press Ctrl+C to stop"
echo "============================================"
echo ""

python -c "
from scrapling.core.ai import ScraplingMCPServer
print('🌐 Server running at http://127.0.0.1:8000')
print('📡 Connect this to your Gemini/n8n workflows')
print('')
ScraplingMCPServer().serve(True, '127.0.0.1', 8000)
"

echo ""
read -p "Server stopped. Press Enter to close..."
