#!/bin/bash

# ============================================
# Bali Bliss - Wedding Vendor Scraper
# Double-click this file on Mac to run
# ============================================

cd "$(dirname "$0")"

echo ""
echo "🌺 Bali Bliss Weddings - Vendor Scraper"
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
echo ""

# Run scraper
echo "🕷️ Starting vendor scraper..."
echo ""

python -c "
from scrapling import Fetcher
import json

print('🔍 Scraping wedding directories...')
print('')

# Test with quotes site to verify it works
page = Fetcher().get('https://quotes.toscrape.com')
quotes = page.css('.quote')

results = []
for q in quotes:
    text = q.css_first('.text').text if q.css_first('.text') else ''
    author = q.css_first('.author').text if q.css_first('.author') else ''
    results.append({'text': text, 'author': author})
    print(f'  📝 {author}: {text[:60]}...')

print(f'')
print(f'✅ Scraped {len(results)} items successfully!')
print(f'')
print('🌺 Scrapling is ready for Bali Bliss vendor scraping.')
print('   Replace the URL above with wedding directory URLs.')
print('   Use StealthyFetcher for Cloudflare-protected sites.')
"

echo ""
echo "============================================"
read -p "Press Enter to close..."
