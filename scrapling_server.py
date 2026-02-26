#!/usr/bin/env python3
"""
Scrapling Control Panel - Advanced Web UI Server
Bali Bliss Weddings Edition

A powerful localhost control panel for managing Scrapling operations.
Run this server and open http://localhost:8888 in your browser.
"""

import http.server
import socketserver
import json
import threading
import time
import sys
import os
import traceback
import urllib.parse
from datetime import datetime
from pathlib import Path

# ---- Configuration ----
PORT = 8888
HOST = "localhost"
SCRAPE_HISTORY = []
ACTIVE_SESSIONS = {}
SERVER_START_TIME = None

# ---- Scrapling Import Check ----
def check_scrapling():
    """Check which Scrapling components are available."""
    status = {
        "fetcher": False,
        "stealthy_fetcher": False,
        "playwright_fetcher": False,
        "mcp_server": False,
        "version": "unknown"
    }
    try:
        from scrapling import Fetcher
        status["fetcher"] = True
    except Exception:
        pass
    try:
        from scrapling.fetchers import StealthyFetcher
        status["stealthy_fetcher"] = True
    except Exception:
        pass
    try:
        from scrapling.fetchers import PlayWrightFetcher
        status["playwright_fetcher"] = True
    except Exception:
        pass
    try:
        from scrapling.core.ai import ScraplingMCPServer
        status["mcp_server"] = True
    except Exception:
        pass
    try:
        import scrapling
        status["version"] = getattr(scrapling, "__version__", "0.4+")
    except Exception:
        pass
    return status


def run_scrape(url, fetcher_type="basic", selectors=None, extract_type="full"):
    """Execute a scrape operation and return results."""
    result = {
        "success": False,
        "url": url,
        "fetcher": fetcher_type,
        "timestamp": datetime.now().isoformat(),
        "data": None,
        "error": None,
        "timing_ms": 0
    }
    
    start = time.time()
    
    try:
        if fetcher_type == "basic":
            from scrapling import Fetcher
            page = Fetcher.get(url)
        elif fetcher_type == "stealthy":
            from scrapling.fetchers import StealthyFetcher
            page = StealthyFetcher.fetch(url)
        elif fetcher_type == "playwright":
            from scrapling.fetchers import PlayWrightFetcher
            page = PlayWrightFetcher.fetch(url)
        else:
            result["error"] = f"Unknown fetcher type: {fetcher_type}"
            return result
        
        if page:
            data = {"status": "success"}
            
            if extract_type == "full":
                data["title"] = ""
                title_els = page.css("title")
                if title_els:
                    data["title"] = title_els[0].text if hasattr(title_els[0], 'text') else str(title_els[0])
                data["text_length"] = len(page.get_all_text()) if hasattr(page, 'get_all_text') else 0
                data["html_length"] = len(str(page.body)) if hasattr(page, 'body') else 0
                links = page.css("a[href]")
                data["link_count"] = len(links) if links else 0
                imgs = page.css("img")
                data["image_count"] = len(imgs) if imgs else 0
                
            elif extract_type == "links":
                links = page.css("a[href]")
                link_list = []
                if links:
                    for a in links[:50]:
                        href = a.attrib.get("href", "") if hasattr(a, 'attrib') else ""
                        txt = a.text if hasattr(a, 'text') else str(a)
                        link_list.append({"href": href, "text": txt[:100]})
                data["links"] = link_list
                
            elif extract_type == "images":
                imgs = page.css("img")
                img_list = []
                if imgs:
                    for img in imgs[:50]:
                        src = img.attrib.get("src", "") if hasattr(img, 'attrib') else ""
                        alt = img.attrib.get("alt", "") if hasattr(img, 'attrib') else ""
                        img_list.append({"src": src, "alt": alt[:100]})
                data["images"] = img_list
                
            elif extract_type == "text":
                data["text"] = page.get_all_text()[:5000] if hasattr(page, 'get_all_text') else ""
                
            elif extract_type == "css" and selectors:
                elements = page.css(selectors)
                el_list = []
                if elements:
                    for el in elements[:30]:
                        txt = el.text if hasattr(el, 'text') else str(el)
                        el_list.append(txt[:200])
                data["elements"] = el_list
                
            result["data"] = data
            result["success"] = True
        else:
            result["error"] = "Page returned empty response"
            
    except Exception as e:
        result["error"] = f"{type(e).__name__}: {str(e)}"
    
    result["timing_ms"] = round((time.time() - start) * 1000, 2)
    SCRAPE_HISTORY.append(result)
    return result


def get_bali_bliss_presets():
    """Return preset scraping configurations for Bali Bliss Weddings."""
    return [
        {
            "name": "Wedding Venue Search",
            "description": "Scrape Bali wedding venue listings",
            "url": "https://www.thebridestory.com/wedding-venues/in/bali",
            "selectors": ".vendor-card",
            "extract_type": "css"
        },
        {
            "name": "Vendor Pricing Check",
            "description": "Check vendor pricing pages",
            "url": "https://www.weddingku.com/vendor",
            "selectors": ".price, .cost, .rate",
            "extract_type": "css"
        },
        {
            "name": "Review Monitor",
            "description": "Monitor reviews on Google Maps",
            "url": "https://www.google.com/maps",
            "selectors": ".review-text",
            "extract_type": "css"
        },
        {
            "name": "Competitor Analysis",
            "description": "Analyze competitor wedding sites",
            "url": "",
            "selectors": "h1, h2, .service, .package",
            "extract_type": "css"
        },
        {
            "name": "Instagram Hashtag",
            "description": "Track Bali wedding hashtags",
            "url": "https://www.instagram.com/explore/tags/baliwedding/",
            "selectors": "article img",
            "extract_type": "images"
        }
    ]


# ---- HTML UI (embedded) ----
def get_ui_html():
    """Return the full HTML UI as a string."""
    return UI_HTML


class ScraplingHandler(http.server.BaseHTTPRequestHandler):
    """HTTP Request Handler for Scrapling Control Panel."""
    
    def log_message(self, format, *args):
        """Custom log format."""
        sys.stderr.write(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]}\n")
    
    def send_json(self, data, status=200):
        """Send JSON response."""
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=2).encode())
    
    def send_html(self, html, status=200):
        """Send HTML response."""
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(html.encode())
    
    def do_GET(self):
        """Handle GET requests."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)
        
        if path == "/" or path == "/index.html":
            self.send_html(get_ui_html())
            
        elif path == "/api/status":
            scrapling_status = check_scrapling()
            uptime = 0
            if SERVER_START_TIME:
                uptime = round(time.time() - SERVER_START_TIME, 1)
            self.send_json({
                "server": "running",
                "port": PORT,
                "uptime_seconds": uptime,
                "scrapling": scrapling_status,
                "history_count": len(SCRAPE_HISTORY),
                "python_version": sys.version.split()[0]
            })
            
        elif path == "/api/history":
            limit = int(params.get("limit", [50])[0])
            self.send_json({
                "history": SCRAPE_HISTORY[-limit:],
                "total": len(SCRAPE_HISTORY)
            })
            
        elif path == "/api/presets":
            self.send_json({"presets": get_bali_bliss_presets()})
            
        elif path == "/api/clear-history":
            SCRAPE_HISTORY.clear()
            self.send_json({"success": True, "message": "History cleared"})
            
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_POST(self):
        """Handle POST requests."""
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode() if content_length > 0 else "{}"
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self.send_json({"error": "Invalid JSON"}, 400)
            return
        
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        
        if path == "/api/scrape":
            url = data.get("url", "")
            if not url:
                self.send_json({"error": "URL is required"}, 400)
                return
            fetcher = data.get("fetcher", "basic")
            selectors = data.get("selectors", "")
            extract_type = data.get("extract_type", "full")
            result = run_scrape(url, fetcher, selectors, extract_type)
            self.send_json(result)
            
        elif path == "/api/batch-scrape":
            urls = data.get("urls", [])
            fetcher = data.get("fetcher", "basic")
            extract_type = data.get("extract_type", "full")
            results = []
            for url in urls[:10]:
                r = run_scrape(url.strip(), fetcher, None, extract_type)
                results.append(r)
            self.send_json({"results": results})
            
        else:
            self.send_json({"error": "Not found"}, 404)
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


# ---- Main Entry Point ----
def main():
    global SERVER_START_TIME
    SERVER_START_TIME = time.time()
    
    print("")
    print("  =============================================")
    print("   Scrapling Control Panel - Bali Bliss       ")
    print("  =============================================")
    print(f"  Server: http://{HOST}:{PORT}")
    print("  Press Ctrl+C to stop")
    print("")
    
    # Check Scrapling
    status = check_scrapling()
    print("  Scrapling Status:")
    print(f"    Basic Fetcher:    {'OK' if status['fetcher'] else 'NOT AVAILABLE'}")
    print(f"    Stealthy Fetcher: {'OK' if status['stealthy_fetcher'] else 'NOT AVAILABLE'}")
    print(f"    MCP Server:       {'OK' if status['mcp_server'] else 'NOT AVAILABLE'}")
    print(f"    Version:          {status['version']}")
    print("")
    
    # Auto-open browser
    import webbrowser
    import threading
    def open_browser():
        time.sleep(1.5)
        webbrowser.open(f"http://{HOST}:{PORT}")
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Start server
    with socketserver.TCPServer((HOST, PORT), ScraplingHandler) as httpd:
        httpd.allow_reuse_address = True
        print(f"  Serving at http://{HOST}:{PORT}")
        print("  Opening browser...")
        print("")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n  Server stopped.")


# ---- Embedded HTML UI ----
UI_HTML = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Scrapling Control Panel - Bali Bliss</title>
<style>
:root {
  --bg-primary: #0a0e17;
  --bg-secondary: #111827;
  --bg-card: #1a2332;
  --bg-input: #0d1520;
  --accent: #06d6a0;
  --accent-hover: #05c490;
  --accent-dim: rgba(6,214,160,0.15);
  --danger: #ef4444;
  --warning: #f59e0b;
  --info: #3b82f6;
  --text-primary: #e2e8f0;
  --text-secondary: #94a3b8;
  --text-dim: #64748b;
  --border: #1e293b;
  --border-light: #334155;
  --glow: 0 0 20px rgba(6,214,160,0.3);
  --radius: 12px;
  --radius-sm: 8px;
  --font: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --mono: 'JetBrains Mono', 'SF Mono', 'Fira Code', monospace;
}

* { margin:0; padding:0; box-sizing:border-box; }

@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');

body {
  font-family: var(--font);
  background: var(--bg-primary);
  color: var(--text-primary);
  min-height: 100vh;
  overflow-x: hidden;
}

/* Animated background */
.bg-grid {
  position: fixed; top:0; left:0; width:100%; height:100%;
  background-image:
    linear-gradient(rgba(6,214,160,0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(6,214,160,0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  z-index: 0;
  animation: gridMove 20s linear infinite;
}
@keyframes gridMove {
  0% { transform: translate(0,0); }
  100% { transform: translate(50px,50px); }
}

.bg-orb {
  position: fixed; border-radius:50%; filter: blur(80px); z-index:0; opacity:0.4;
}
.bg-orb-1 { width:400px; height:400px; background: rgba(6,214,160,0.15); top:-100px; right:-100px; animation: orbFloat 15s ease-in-out infinite; }
.bg-orb-2 { width:300px; height:300px; background: rgba(59,130,246,0.1); bottom:-50px; left:-50px; animation: orbFloat 20s ease-in-out infinite reverse; }
@keyframes orbFloat {
  0%,100% { transform: translate(0,0) scale(1); }
  50% { transform: translate(30px,20px) scale(1.1); }
}

/* Layout */
.app { position: relative; z-index: 1; }
.header {
  background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg-card) 100%);
  border-bottom: 1px solid var(--border);
  padding: 16px 32px;
  display: flex; align-items: center; justify-content: space-between;
  backdrop-filter: blur(20px);
  position: sticky; top: 0; z-index: 100;
}
.logo { display: flex; align-items: center; gap: 12px; }
.logo-icon {
  width:40px; height:40px; border-radius:10px;
  background: linear-gradient(135deg, var(--accent) 0%, #059669 100%);
  display:flex; align-items:center; justify-content:center;
  font-size:20px; font-weight:800; color:#000;
  box-shadow: var(--glow);
}
.logo-text { font-size:20px; font-weight:700; letter-spacing:-0.5px; }
.logo-sub { font-size:11px; color:var(--accent); font-weight:500; letter-spacing:1px; text-transform:uppercase; }

.status-bar {
  display:flex; gap:16px; align-items:center;
}
.status-dot {
  width:8px; height:8px; border-radius:50%;
  display:inline-block; margin-right:6px;
  animation: pulse 2s infinite;
}
.status-dot.green { background:var(--accent); box-shadow: 0 0 8px var(--accent); }
.status-dot.red { background:var(--danger); box-shadow: 0 0 8px var(--danger); }
.status-dot.yellow { background:var(--warning); box-shadow: 0 0 8px var(--warning); }
@keyframes pulse { 0%,100%{opacity:1;} 50%{opacity:0.5;} }
.status-item { font-size:12px; color:var(--text-secondary); display:flex; align-items:center; }

.main { display:flex; min-height:calc(100vh - 72px); }

/* Sidebar */
.sidebar {
  width: 260px; min-width:260px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  padding: 16px; display:flex; flex-direction:column; gap:4px;
}
.nav-item {
  padding: 10px 14px; border-radius: var(--radius-sm);
  cursor: pointer; display:flex; align-items:center; gap:10px;
  font-size:13px; font-weight:500; color:var(--text-secondary);
  transition: all 0.2s;
}
.nav-item:hover { background:var(--accent-dim); color:var(--text-primary); }
.nav-item.active { background:var(--accent-dim); color:var(--accent); border-left:3px solid var(--accent); }
.nav-item .icon { font-size:16px; width:20px; text-align:center; }
.nav-section { font-size:10px; color:var(--text-dim); font-weight:600; letter-spacing:1.5px; text-transform:uppercase; padding:16px 14px 6px; }

/* Content */
.content { flex:1; padding:24px; overflow-y:auto; max-height:calc(100vh - 72px); }
.page { display:none; }
.page.active { display:block; }

/* Cards */
.card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 16px;
  transition: all 0.3s;
}
.card:hover { border-color: var(--border-light); }
.card-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; }
.card-title { font-size:16px; font-weight:600; }
.card-subtitle { font-size:12px; color:var(--text-dim); margin-top:2px; }

/* Stats Grid */
.stats-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap:16px; margin-bottom:24px; }
.stat-card {
  background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-secondary) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  position: relative; overflow:hidden;
}
.stat-card::before {
  content:''; position:absolute; top:0; right:0; width:80px; height:80px;
  border-radius:50%; filter:blur(30px); opacity:0.3;
}
.stat-card.green::before { background:var(--accent); }
.stat-card.blue::before { background:var(--info); }
.stat-card.yellow::before { background:var(--warning); }
.stat-card.red::before { background:var(--danger); }
.stat-value { font-size:28px; font-weight:800; letter-spacing:-1px; }
.stat-label { font-size:12px; color:var(--text-secondary); margin-top:4px; }
.stat-icon { font-size:24px; position:absolute; top:16px; right:16px; opacity:0.5; }

/* Buttons */
.btn {
  padding: 10px 20px; border-radius: var(--radius-sm);
  font-family: var(--font); font-size: 13px; font-weight: 600;
  cursor: pointer; border: none; transition: all 0.2s;
  display: inline-flex; align-items: center; gap: 8px;
}
.btn-primary {
  background: linear-gradient(135deg, var(--accent) 0%, #059669 100%);
  color: #000; box-shadow: 0 4px 15px rgba(6,214,160,0.3);
}
.btn-primary:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(6,214,160,0.4); }
.btn-primary:disabled { opacity:0.5; cursor:not-allowed; transform:none; }
.btn-secondary {
  background: var(--bg-input); color: var(--text-primary);
  border: 1px solid var(--border-light);
}
.btn-secondary:hover { border-color: var(--accent); }
.btn-danger { background: var(--danger); color: white; }
.btn-sm { padding: 6px 12px; font-size: 11px; }

/* Form Elements */
.form-group { margin-bottom: 16px; }
.form-label { display:block; font-size:12px; font-weight:600; color:var(--text-secondary); margin-bottom:6px; text-transform:uppercase; letter-spacing:0.5px; }
.form-input, .form-select, .form-textarea {
  width: 100%; padding: 10px 14px; border-radius: var(--radius-sm);
  background: var(--bg-input); border: 1px solid var(--border);
  color: var(--text-primary); font-family: var(--font); font-size: 13px;
  transition: all 0.2s;
}
.form-input:focus, .form-select:focus, .form-textarea:focus {
  outline: none; border-color: var(--accent);
  box-shadow: 0 0 0 3px var(--accent-dim);
}
.form-textarea { resize:vertical; min-height:80px; font-family: var(--mono); }
.form-select { cursor:pointer; }
.form-select option { background: var(--bg-card); }

/* Results Console */
.console {
  background: #000810; border: 1px solid var(--border);
  border-radius: var(--radius); padding: 16px;
  font-family: var(--mono); font-size: 12px;
  max-height: 400px; overflow-y: auto;
  line-height: 1.6;
}
.console-line { padding: 2px 0; }
.console-line.success { color: var(--accent); }
.console-line.error { color: var(--danger); }
.console-line.info { color: var(--info); }
.console-line.warning { color: var(--warning); }
.console-line.dim { color: var(--text-dim); }

/* Tags */
.tag {
  display:inline-block; padding:3px 8px; border-radius:4px;
  font-size:10px; font-weight:600; text-transform:uppercase;
  letter-spacing:0.5px;
}
.tag-green { background:rgba(6,214,160,0.15); color:var(--accent); }
.tag-red { background:rgba(239,68,68,0.15); color:var(--danger); }
.tag-blue { background:rgba(59,130,246,0.15); color:var(--info); }
.tag-yellow { background:rgba(245,158,11,0.15); color:var(--warning); }

/* Table */
.table { width:100%; border-collapse:collapse; font-size:13px; }
.table th { text-align:left; padding:10px; color:var(--text-dim); font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid var(--border); }
.table td { padding:10px; border-bottom:1px solid var(--border); }
.table tr:hover td { background:var(--accent-dim); }

/* Preset Cards */
.preset-grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(280px,1fr)); gap:12px; }
.preset-card {
  background: var(--bg-card); border:1px solid var(--border);
  border-radius: var(--radius); padding:16px; cursor:pointer;
  transition: all 0.3s;
}
.preset-card:hover { border-color:var(--accent); transform:translateY(-2px); box-shadow: var(--glow); }
.preset-name { font-size:14px; font-weight:600; margin-bottom:4px; }
.preset-desc { font-size:12px; color:var(--text-dim); }

/* Spinner */
.spinner {
  width:16px; height:16px; border:2px solid transparent;
  border-top-color:var(--accent); border-radius:50%;
  animation: spin 0.8s linear infinite; display:inline-block;
}
@keyframes spin { to { transform:rotate(360deg); } }

/* Toast Notifications */
.toast-container { position:fixed; top:80px; right:24px; z-index:1000; display:flex; flex-direction:column; gap:8px; }
.toast {
  padding:12px 20px; border-radius:var(--radius-sm);
  font-size:13px; font-weight:500;
  animation: slideIn 0.3s ease; min-width:300px;
  display:flex; align-items:center; gap:8px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.3);
}
.toast.success { background:#065f46; border:1px solid var(--accent); }
.toast.error { background:#7f1d1d; border:1px solid var(--danger); }
.toast.info { background:#1e3a5f; border:1px solid var(--info); }
@keyframes slideIn { from { transform:translateX(100%); opacity:0; } to { transform:translateX(0); opacity:1; } }

/* Scrollbar */
::-webkit-scrollbar { width:6px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:var(--border-light); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:var(--text-dim); }

.flex { display:flex; } .flex-col { flex-direction:column; } .gap-2 { gap:8px; } .gap-4 { gap:16px; }
.items-center { align-items:center; } .justify-between { justify-content:space-between; }
.mb-4 { margin-bottom:16px; } .mt-4 { margin-top:16px; }
.text-accent { color:var(--accent); } .text-dim { color:var(--text-dim); }
.w-full { width:100%; }
</style>
</head>
<body>
<div class="bg-grid"></div>
<div class="bg-orb bg-orb-1"></div>
<div class="bg-orb bg-orb-2"></div>
<div class="toast-container" id="toasts"></div>

<div class="app">
  <!-- Header -->
  <header class="header">
    <div class="logo">
      <div class="logo-icon">S</div>
      <div>
        <div class="logo-text">Scrapling</div>
        <div class="logo-sub">Bali Bliss Weddings</div>
      </div>
    </div>
    <div class="status-bar">
      <div class="status-item"><span class="status-dot green" id="serverDot"></span><span id="serverStatus">Connecting...</span></div>
      <div class="status-item" id="uptimeDisplay">Uptime: --</div>
      <div class="status-item" id="versionDisplay">v--</div>
    </div>
  </header>

  <div class="main">
    <!-- Sidebar -->
    <nav class="sidebar">
      <div class="nav-section">Main</div>
      <div class="nav-item active" onclick="showPage('dashboard')"><span class="icon">&#9632;</span> Dashboard</div>
      <div class="nav-item" onclick="showPage('scraper')"><span class="icon">&#10095;</span> Scraper</div>
      <div class="nav-item" onclick="showPage('batch')"><span class="icon">&#9776;</span> Batch Scrape</div>
      <div class="nav-section">Bali Bliss</div>
      <div class="nav-item" onclick="showPage('presets')"><span class="icon">&#9733;</span> Presets</div>
      <div class="nav-item" onclick="showPage('monitor')"><span class="icon">&#8635;</span> Monitor</div>
      <div class="nav-section">System</div>
      <div class="nav-item" onclick="showPage('history')"><span class="icon">&#9201;</span> History</div>
      <div class="nav-item" onclick="showPage('settings')"><span class="icon">&#9881;</span> Settings</div>
    </nav>

    <!-- Content -->
    <div class="content">

      <!-- Dashboard Page -->
      <div class="page active" id="page-dashboard">
        <h2 style="font-size:24px;font-weight:800;margin-bottom:4px;">Dashboard</h2>
        <p class="text-dim" style="margin-bottom:24px;">System overview and quick actions</p>

        <div class="stats-grid" id="statsGrid">
          <div class="stat-card green">
            <div class="stat-icon">&#9889;</div>
            <div class="stat-value" id="statFetcher">--</div>
            <div class="stat-label">Fetcher Status</div>
          </div>
          <div class="stat-card blue">
            <div class="stat-icon">&#128202;</div>
            <div class="stat-value" id="statScrapes">0</div>
            <div class="stat-label">Total Scrapes</div>
          </div>
          <div class="stat-card yellow">
            <div class="stat-icon">&#9201;</div>
            <div class="stat-value" id="statUptime">0s</div>
            <div class="stat-label">Server Uptime</div>
          </div>
          <div class="stat-card red">
            <div class="stat-icon">&#128640;</div>
            <div class="stat-value" id="statPython">--</div>
            <div class="stat-label">Python Version</div>
          </div>
        </div>

        <div class="card">
          <div class="card-header">
            <div><div class="card-title">Component Status</div><div class="card-subtitle">Available Scrapling modules</div></div>
          </div>
          <table class="table">
            <thead><tr><th>Component</th><th>Status</th><th>Description</th></tr></thead>
            <tbody id="componentTable"></tbody>
          </table>
        </div>

        <div class="card">
          <div class="card-header">
            <div><div class="card-title">Quick Scrape</div><div class="card-subtitle">Test a URL instantly</div></div>
          </div>
          <div class="flex gap-2">
            <input type="text" class="form-input" id="quickUrl" placeholder="https://example.com" style="flex:1">
            <button class="btn btn-primary" onclick="quickScrape()">&#9889; Scrape</button>
          </div>
          <div id="quickResult" class="mt-4"></div>
        </div>
      </div>

      <!-- Scraper Page -->
      <div class="page" id="page-scraper">
        <h2 style="font-size:24px;font-weight:800;margin-bottom:4px;">Advanced Scraper</h2>
        <p class="text-dim" style="margin-bottom:24px;">Configure and execute scraping operations</p>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Scrape Configuration</div>
          </div>
          <div class="form-group">
            <label class="form-label">Target URL</label>
            <input type="text" class="form-input" id="scrapeUrl" placeholder="https://example.com">
          </div>
          <div class="flex gap-4">
            <div class="form-group" style="flex:1">
              <label class="form-label">Fetcher Engine</label>
              <select class="form-select" id="scrapeFetcher">
                <option value="basic">Basic Fetcher (httpx)</option>
                <option value="stealthy">Stealthy Fetcher (Camoufox)</option>
                <option value="playwright">PlayWright Fetcher</option>
              </select>
            </div>
            <div class="form-group" style="flex:1">
              <label class="form-label">Extract Type</label>
              <select class="form-select" id="scrapeExtract">
                <option value="full">Full Analysis</option>
                <option value="text">Text Content</option>
                <option value="links">Links Only</option>
                <option value="images">Images Only</option>
                <option value="css">CSS Selector</option>
              </select>
            </div>
          </div>
          <div class="form-group" id="selectorGroup" style="display:none">
            <label class="form-label">CSS Selector</label>
            <input type="text" class="form-input" id="scrapeSelector" placeholder=".class-name, #id, tag">
          </div>
          <button class="btn btn-primary" id="scrapeBtn" onclick="executeScrape()">&#9889; Execute Scrape</button>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Results Console</div>
            <button class="btn btn-secondary btn-sm" onclick="clearConsole()">Clear</button>
          </div>
          <div class="console" id="scrapeConsole">
            <div class="console-line dim">// Ready. Configure a scrape operation above.</div>
          </div>
        </div>
      </div>

      <!-- Batch Scrape Page -->
      <div class="page" id="page-batch">
        <h2 style="font-size:24px;font-weight:800;margin-bottom:4px;">Batch Scraper</h2>
        <p class="text-dim" style="margin-bottom:24px;">Scrape multiple URLs at once</p>

        <div class="card">
          <div class="form-group">
            <label class="form-label">URLs (one per line)</label>
            <textarea class="form-textarea" id="batchUrls" rows="6" placeholder="https://example1.com&#10;https://example2.com&#10;https://example3.com"></textarea>
          </div>
          <div class="flex gap-4">
            <div class="form-group" style="flex:1">
              <label class="form-label">Fetcher</label>
              <select class="form-select" id="batchFetcher">
                <option value="basic">Basic Fetcher</option>
                <option value="stealthy">Stealthy Fetcher</option>
              </select>
            </div>
            <div class="form-group" style="flex:1">
              <label class="form-label">Extract Type</label>
              <select class="form-select" id="batchExtract">
                <option value="full">Full Analysis</option>
                <option value="text">Text Only</option>
                <option value="links">Links Only</option>
              </select>
            </div>
          </div>
          <button class="btn btn-primary" id="batchBtn" onclick="executeBatch()">&#9889; Run Batch</button>
        </div>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Batch Results</div>
          </div>
          <div class="console" id="batchConsole">
            <div class="console-line dim">// Enter URLs above and run batch scrape.</div>
          </div>
        </div>
      </div>

      <!-- Presets Page -->
      <div class="page" id="page-presets">
        <h2 style="font-size:24px;font-weight:800;margin-bottom:4px;">Bali Bliss Presets</h2>
        <p class="text-dim" style="margin-bottom:24px;">Pre-configured scraping tasks for wedding business</p>
        <div class="preset-grid" id="presetsGrid"></div>
      </div>

      <!-- Monitor Page -->
      <div class="page" id="page-monitor">
        <h2 style="font-size:24px;font-weight:800;margin-bottom:4px;">Live Monitor</h2>
        <p class="text-dim" style="margin-bottom:24px;">Real-time scraping activity and performance</p>

        <div class="card">
          <div class="card-header">
            <div class="card-title">Activity Feed</div>
            <button class="btn btn-secondary btn-sm" onclick="refreshHistory()">&#8635; Refresh</button>
          </div>
          <div id="activityFeed" style="max-height:500px;overflow-y:auto;"></div>
        </div>
      </div>

      <!-- History Page -->
      <div class="page" id="page-history">
        <h2 style="font-size:24px;font-weight:800;margin-bottom:4px;">Scrape History</h2>
        <p class="text-dim" style="margin-bottom:24px;">View all past scraping operations</p>

        <div class="card">
          <div class="card-header">
            <div class="card-title">History Log</div>
            <div class="flex gap-2">
              <button class="btn btn-secondary btn-sm" onclick="refreshHistory()">&#8635; Refresh</button>
              <button class="btn btn-danger btn-sm" onclick="clearHistory()">Clear All</button>
            </div>
          </div>
          <table class="table">
            <thead><tr><th>Time</th><th>URL</th><th>Fetcher</th><th>Status</th><th>Time (ms)</th></tr></thead>
            <tbody id="historyTable"></tbody>
          </table>
        </div>
      </div>

      <!-- Settings Page -->
      <div class="page" id="page-settings">
        <h2 style="font-size:24px;font-weight:800;margin-bottom:4px;">Settings</h2>
        <p class="text-dim" style="margin-bottom:24px;">Server configuration and info</p>

        <div class="card">
          <div class="card-title mb-4">Server Info</div>
          <table class="table">
            <tbody id="settingsTable"></tbody>
          </table>
        </div>

        <div class="card">
          <div class="card-title mb-4">API Endpoints</div>
          <div class="console">
            <div class="console-line info">GET  /api/status      - Server and Scrapling status</div>
            <div class="console-line info">GET  /api/history     - Scrape history</div>
            <div class="console-line info">GET  /api/presets     - Bali Bliss presets</div>
            <div class="console-line info">POST /api/scrape      - Execute single scrape</div>
            <div class="console-line info">POST /api/batch-scrape - Execute batch scrape</div>
            <div class="console-line info">GET  /api/clear-history - Clear history</div>
          </div>
        </div>
      </div>

    </div>
  </div>
</div>

<script>
// ---- State ----
let serverData = null;
let historyData = [];

// ---- Navigation ----
function showPage(name) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
  const page = document.getElementById('page-' + name);
  if (page) page.classList.add('active');
  event.target.closest('.nav-item').classList.add('active');
  if (name === 'history' || name === 'monitor') refreshHistory();
  if (name === 'presets') loadPresets();
  if (name === 'settings') loadSettings();
}

// ---- Toast Notifications ----
function toast(msg, type='info') {
  const container = document.getElementById('toasts');
  const el = document.createElement('div');
  el.className = 'toast ' + type;
  el.innerHTML = msg;
  container.appendChild(el);
  setTimeout(() => el.remove(), 4000);
}

// ---- API Calls ----
async function api(path, method='GET', body=null) {
  const opts = { method, headers: {'Content-Type':'application/json'} };
  if (body) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  return await res.json();
}

// ---- Status Polling ----
async function pollStatus() {
  try {
    const data = await api('/api/status');
    serverData = data;
    document.getElementById('serverStatus').textContent = 'Connected';
    document.getElementById('serverDot').className = 'status-dot green';
    
    const uptime = data.uptime_seconds;
    const mins = Math.floor(uptime / 60);
    const hrs = Math.floor(mins / 60);
    const uptimeStr = hrs > 0 ? hrs+'h '+mins%60+'m' : mins > 0 ? mins+'m '+Math.floor(uptime%60)+'s' : Math.floor(uptime)+'s';
    document.getElementById('uptimeDisplay').textContent = 'Uptime: ' + uptimeStr;
    document.getElementById('versionDisplay').textContent = 'v' + data.scrapling.version;
    
    document.getElementById('statFetcher').textContent = data.scrapling.fetcher ? 'READY' : 'OFF';
    document.getElementById('statScrapes').textContent = data.history_count;
    document.getElementById('statUptime').textContent = uptimeStr;
    document.getElementById('statPython').textContent = data.python_version;
    
    const tbody = document.getElementById('componentTable');
    tbody.innerHTML = '';
    const components = [
      ['Basic Fetcher', data.scrapling.fetcher, 'HTTP client with auto-parsing'],
      ['Stealthy Fetcher', data.scrapling.stealthy_fetcher, 'Anti-bot browser automation'],
      ['PlayWright Fetcher', data.scrapling.playwright_fetcher, 'Full browser rendering'],
      ['MCP Server', data.scrapling.mcp_server, 'AI model context protocol']
    ];
    components.forEach(([name, ok, desc]) => {
      const tr = document.createElement('tr');
      tr.innerHTML = '<td><strong>'+name+'</strong></td><td><span class="tag '+(ok?'tag-green':'tag-red')+'">'+(ok?'Available':'Not Available')+'</span></td><td class="text-dim">'+desc+'</td>';
      tbody.appendChild(tr);
    });
    
  } catch(e) {
    document.getElementById('serverStatus').textContent = 'Disconnected';
    document.getElementById('serverDot').className = 'status-dot red';
  }
}

// ---- Quick Scrape ----
async function quickScrape() {
  const url = document.getElementById('quickUrl').value.trim();
  if (!url) { toast('Enter a URL first', 'error'); return; }
  document.getElementById('quickResult').innerHTML = '<div class="spinner"></div> Scraping...';
  try {
    const result = await api('/api/scrape', 'POST', {url, fetcher:'basic', extract_type:'full'});
    if (result.success) {
      toast('Scrape successful! ('+result.timing_ms+'ms)', 'success');
      document.getElementById('quickResult').innerHTML = '<div class="console"><div class="console-line success">SUCCESS in '+result.timing_ms+'ms</div><div class="console-line info">Title: '+(result.data.title||'N/A')+'</div><div class="console-line">Links: '+(result.data.link_count||0)+' | Images: '+(result.data.image_count||0)+'</div><div class="console-line dim">HTML: '+(result.data.html_length||0)+' bytes | Text: '+(result.data.text_length||0)+' chars</div></div>';
    } else {
      toast('Scrape failed: '+result.error, 'error');
      document.getElementById('quickResult').innerHTML = '<div class="console"><div class="console-line error">ERROR: '+result.error+'</div></div>';
    }
    pollStatus();
  } catch(e) {
    toast('Request failed: '+e.message, 'error');
    document.getElementById('quickResult').innerHTML = '';
  }
}

// ---- Advanced Scraper ----
document.getElementById('scrapeExtract').addEventListener('change', function() {
  document.getElementById('selectorGroup').style.display = this.value === 'css' ? 'block' : 'none';
});

async function executeScrape() {
  const url = document.getElementById('scrapeUrl').value.trim();
  if (!url) { toast('Enter a URL', 'error'); return; }
  const fetcher = document.getElementById('scrapeFetcher').value;
  const extract_type = document.getElementById('scrapeExtract').value;
  const selectors = document.getElementById('scrapeSelector').value;
  const btn = document.getElementById('scrapeBtn');
  const con = document.getElementById('scrapeConsole');
  
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Scraping...';
  con.innerHTML = '<div class="console-line info">[' + new Date().toLocaleTimeString() + '] Starting scrape...</div>' +
    '<div class="console-line dim">URL: ' + url + '</div>' +
    '<div class="console-line dim">Fetcher: ' + fetcher + ' | Extract: ' + extract_type + '</div>';
  
  try {
    const result = await api('/api/scrape', 'POST', {url, fetcher, extract_type, selectors});
    if (result.success) {
      toast('Scrape complete! (' + result.timing_ms + 'ms)', 'success');
      let html = '<div class="console-line success">[' + new Date().toLocaleTimeString() + '] SUCCESS (' + result.timing_ms + 'ms)</div>';
      const d = result.data;
      if (d.title !== undefined) html += '<div class="console-line info">Title: ' + d.title + '</div>';
      if (d.link_count !== undefined) html += '<div class="console-line">Links: ' + d.link_count + ' | Images: ' + d.image_count + '</div>';
      if (d.html_length !== undefined) html += '<div class="console-line dim">HTML: ' + d.html_length + ' bytes | Text: ' + d.text_length + ' chars</div>';
      if (d.links) { d.links.forEach(l => { html += '<div class="console-line dim">  ' + l.text + ' -> ' + l.href + '</div>'; }); }
      if (d.images) { d.images.forEach(i => { html += '<div class="console-line dim">  [IMG] ' + i.alt + ' -> ' + i.src + '</div>'; }); }
      if (d.text) html += '<div class="console-line">' + d.text.substring(0,500) + '...</div>';
      if (d.elements) { d.elements.forEach((el,i) => { html += '<div class="console-line dim">  [' + i + '] ' + el + '</div>'; }); }
      con.innerHTML += html;
    } else {
      toast('Scrape failed', 'error');
      con.innerHTML += '<div class="console-line error">[ERROR] ' + result.error + '</div>';
    }
    pollStatus();
  } catch(e) {
    toast('Request error: ' + e.message, 'error');
    con.innerHTML += '<div class="console-line error">[NETWORK ERROR] ' + e.message + '</div>';
  }
  btn.disabled = false;
  btn.innerHTML = '&#9889; Execute Scrape';
}

function clearConsole() {
  document.getElementById('scrapeConsole').innerHTML = '<div class="console-line dim">// Console cleared.</div>';
}

// ---- Batch Scrape ----
async function executeBatch() {
  const urls = document.getElementById('batchUrls').value.trim().split('\n').filter(u => u.trim());
  if (!urls.length) { toast('Enter at least one URL', 'error'); return; }
  const fetcher = document.getElementById('batchFetcher').value;
  const extract_type = document.getElementById('batchExtract').value;
  const btn = document.getElementById('batchBtn');
  const con = document.getElementById('batchConsole');
  
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span> Running...';
  con.innerHTML = '<div class="console-line info">Starting batch scrape of ' + urls.length + ' URLs...</div>';
  
  try {
    const result = await api('/api/batch-scrape', 'POST', {urls, fetcher, extract_type});
    let ok = 0, fail = 0;
    result.results.forEach(r => {
      if (r.success) {
        ok++;
        con.innerHTML += '<div class="console-line success">[OK] ' + r.url + ' (' + r.timing_ms + 'ms)</div>';
      } else {
        fail++;
        con.innerHTML += '<div class="console-line error">[FAIL] ' + r.url + ': ' + r.error + '</div>';
      }
    });
    con.innerHTML += '<div class="console-line info">Batch complete: ' + ok + ' success, ' + fail + ' failed</div>';
    toast('Batch complete: ' + ok + '/' + urls.length + ' success', ok === urls.length ? 'success' : 'error');
    pollStatus();
  } catch(e) {
    toast('Batch error: ' + e.message, 'error');
    con.innerHTML += '<div class="console-line error">[ERROR] ' + e.message + '</div>';
  }
  btn.disabled = false;
  btn.innerHTML = '&#9889; Run Batch';
}

// ---- Presets ----
async function loadPresets() {
  try {
    const data = await api('/api/presets');
    const grid = document.getElementById('presetsGrid');
    grid.innerHTML = '';
    data.presets.forEach(p => {
      const card = document.createElement('div');
      card.className = 'preset-card';
      card.innerHTML = '<div class="preset-name">' + p.name + '</div><div class="preset-desc">' + p.description + '</div><div style="margin-top:8px"><span class="tag tag-blue">' + p.extract_type + '</span></div>';
      card.onclick = () => {
        showPage('scraper');
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        document.querySelectorAll('.nav-item')[1].classList.add('active');
        document.getElementById('scrapeUrl').value = p.url;
        document.getElementById('scrapeSelector').value = p.selectors || '';
        if (p.extract_type === 'css') {
          document.getElementById('scrapeExtract').value = 'css';
          document.getElementById('selectorGroup').style.display = 'block';
        } else {
          document.getElementById('scrapeExtract').value = p.extract_type;
        }
        toast('Preset loaded: ' + p.name, 'info');
      };
      grid.appendChild(card);
    });
  } catch(e) { toast('Failed to load presets', 'error'); }
}

// ---- History ----
async function refreshHistory() {
  try {
    const data = await api('/api/history');
    historyData = data.history;
    
    const tbody = document.getElementById('historyTable');
    tbody.innerHTML = '';
    data.history.reverse().forEach(h => {
      const tr = document.createElement('tr');
      const t = new Date(h.timestamp).toLocaleTimeString();
      const shortUrl = h.url.length > 40 ? h.url.substring(0,40)+'...' : h.url;
      tr.innerHTML = '<td class="text-dim">' + t + '</td><td>' + shortUrl + '</td><td><span class="tag tag-blue">' + h.fetcher + '</span></td><td><span class="tag ' + (h.success?'tag-green':'tag-red') + '">' + (h.success?'OK':'FAIL') + '</span></td><td>' + h.timing_ms + '</td>';
      tbody.appendChild(tr);
    });
    
    const feed = document.getElementById('activityFeed');
    if (feed) {
      feed.innerHTML = '';
      data.history.forEach(h => {
        const div = document.createElement('div');
        div.style.cssText = 'padding:10px;border-bottom:1px solid var(--border);';
        const t = new Date(h.timestamp).toLocaleTimeString();
        div.innerHTML = '<div class="flex justify-between items-center"><span>' + (h.success?'&#9989;':'&#10060;') + ' ' + h.url.substring(0,50) + '</span><span class="text-dim">' + t + '</span></div><div class="text-dim" style="font-size:11px;margin-top:4px">' + h.fetcher + ' | ' + h.timing_ms + 'ms</div>';
        feed.appendChild(div);
      });
      if (!data.history.length) feed.innerHTML = '<div class="text-dim" style="padding:20px;text-align:center">No activity yet. Run a scrape to see results here.</div>';
    }
  } catch(e) { /* silent */ }
}

async function clearHistory() {
  await api('/api/clear-history');
  toast('History cleared', 'info');
  refreshHistory();
  pollStatus();
}

// ---- Settings ----
async function loadSettings() {
  if (!serverData) await pollStatus();
  const tbody = document.getElementById('settingsTable');
  tbody.innerHTML = '';
  const rows = [
    ['Server Port', serverData?.port || '--'],
    ['Python Version', serverData?.python_version || '--'],
    ['Scrapling Version', serverData?.scrapling?.version || '--'],
    ['Uptime', serverData?.uptime_seconds ? Math.round(serverData.uptime_seconds) + 's' : '--'],
    ['Total Scrapes', serverData?.history_count || 0],
    ['Basic Fetcher', serverData?.scrapling?.fetcher ? 'Available' : 'Not Available'],
    ['Stealthy Fetcher', serverData?.scrapling?.stealthy_fetcher ? 'Available' : 'Not Available'],
    ['MCP Server', serverData?.scrapling?.mcp_server ? 'Available' : 'Not Available']
  ];
  rows.forEach(([k,v]) => {
    const tr = document.createElement('tr');
    tr.innerHTML = '<td class="text-dim">' + k + '</td><td>' + v + '</td>';
    tbody.appendChild(tr);
  });
}

// ---- Init ----
pollStatus();
setInterval(pollStatus, 5000);

document.getElementById('quickUrl').addEventListener('keydown', e => { if (e.key === 'Enter') quickScrape(); });
document.getElementById('scrapeUrl').addEventListener('keydown', e => { if (e.key === 'Enter') executeScrape(); });
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
