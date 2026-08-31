import os
import sys
import re
import requests
import json

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

API_KEY = os.environ.get("RAPIDAPI_KEY", "").strip()
OUTPUT_DIR = "public"
DEBUG_DIR = "debug_logs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(DEBUG_DIR, exist_ok=True) # Ide mentjük a nyers JSON-okat

debug_logs = []
items_data = []

def log(msg):
    print(msg)
    debug_logs.append(str(msg))

def extract_items_from_json(raw_json, possible_paths):
    if isinstance(raw_json, list):
        return raw_json
    for path in possible_paths:
        current = raw_json
        for k in path:
            if isinstance(current, dict):
                current = current.get(k, {})
            else:
                break
        if isinstance(current, list) and len(current) > 0:
            return current
    return []

# --- 1. HÁDA SCRAPER ---
def fetch_hada():
    log("\n--- [1/5] Háda Webshop Lekérdezés ---")
    if not HAS_BS4:
        log("❌ Háda kihagyva (hiányzó bs4 modul)")
        return
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    search_terms = ["taktikai"] # Csak egyet kérdezünk le a gyorsaság kedvéért
    
    count_before = len(items_data)
    for term in search_terms:
        url = f"https://hadawebshop.hu/catalogsearch/result/?q={term}"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                soup = BeautifulSoup(res.text, 'html.parser')
                products = soup.select('.product-item-info') or soup.select('.product-item')
                for item in products:
                    title_elem = item.select_one('.product-item-link') or item.select_one('.product-item-name')
                    if not title_elem: continue
                    title = title_elem.get_text(strip=True)
                    if re.search(r'\b(S|női|noi|dolls|woman|women)\b', title, re.IGNORECASE):
                        continue
                    price_elem = item.select_one('.price')
                    img_elem = item.select_one('img.product-image-photo') or item.select_one('img')
                    link = title_elem['href'] if title_elem.has_attr('href') else "https://hadawebshop.hu"
                    price = price_elem.get_text(strip=True) if price_elem else "N/A"
                    img = img_elem['src'] if img_elem and img_elem.has_attr('src') else None
                    if not any(d['title'] == title for d in items_data):
                        items_data.append({"title": title, "price": price, "link": link, "images": [img] if img else [], "source": "Háda HU"})
        except Exception as e:
            log(f"❌ Háda hiba: {e}")
    log(f"✅ Hádáról behelyezett releváns termékek: {len(items_data) - count_before}")

# --- 2. API PROVIDEREK ---
API_PROVIDERS = [
    {
        "name": "Temu",
        "url": "https://temu-product-scraper.p.rapidapi.com/temu",
        "method": "GET",
        "host": "temu-product-scraper.p.rapidapi.com",
        "params": {"keyword": "tactical vest", "maxItems": "10"},
        "paths": [["products"], ["data"], ["items"]]
    },
    {
        "name": "Vinted",
        "url": "https://vinted-second-hand-marketplace-data-api.p.rapidapi.com/vinted/v1/catalog_search",
        "method": "POST",
        "host": "vinted-second-hand-marketplace-data-api.p.rapidapi.com",
        "json": {"query": "vest"},
        "paths": [["items"], ["products"], ["data"], ["results"]]
    },
    {
        "name": "AliExpress",
        "url": "https://aligate-aliexpress-data-api.p.rapidapi.com/api/v2/search/text",
        "method": "GET",
        "host": "aligate-aliexpress-data-api.p.rapidapi.com",
        "params": {"locale": "en_US", "query": "tactical vest", "country": "US", "page": "1", "currency": "USD"},
        "paths": [["data", "items"], ["result", "items"], ["items"], ["data", "products"]]
    },
    {
        "name": "FB Marketplace",
        "url": "https://facebook-pages-scraper2.p.rapidapi.com/get_facebook_marketplace_items_listing",
        "method": "GET",
        "host": "facebook-pages-scraper2.p.rapidapi.com",
        "params": {"query": "vest", "commerce_search_sort_by": "BEST_MATCH", "filter_location_latitude": 47.4979, "filter_location_longitude": 19.0402, "filter_radius_km": 100, "proxy_country": "gb"},
        "paths": [["data"], ["items"], ["results"], ["listings"]]
    }
]

def run_api_providers():
    if not API_KEY:
        log("\n⚠️ RAPIDAPI_KEY nincs beállítva, API hívások kihagyva.")
        return

    for idx, provider in enumerate(API_PROVIDERS, start=2):
        name = provider['name']
        log(f"\n--- [{idx}/5] {name} API Keresés ---")
        headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": provider["host"]}
        
        try:
            if provider["method"] == "GET":
                res = requests.get(provider["url"], headers=headers, params=provider.get("params"), timeout=15)
            else:
                res = requests.post(provider["url"], headers=headers, json=provider.get("json"), timeout=15)

            log(f"{name} HTTP Válaszkód: {res.status_code}")
            
            if res.status_code == 200:
                raw_json = res.json()
                
                # NYERS JSON MENTÉSE FÁJLBA
                safe_name = name.replace(" ", "_").lower()
                debug_file_path = os.path.join(DEBUG_DIR, f"{safe_name}_response.json")
                with open(debug_file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_json, f, indent=4, ensure_ascii=False)
                
                # JSON GYÖKÉR KULCSOK KIÍRÁSA A NAPLÓBA
                if isinstance(raw_json, dict):
                    log(f"📝 JSON mentve: {debug_file_path}")
                    log(f"🔍 JSON gyökér kulcsok (Top-level keys): {list(raw_json.keys())}")
                elif isinstance(raw_json, list):
                    log(f"📝 JSON mentve: {debug_file_path}")
                    log(f"🔍 A válasz egy {len(raw_json)} elemű lista.")
                else:
                    log(f"🔍 Ismeretlen válasz formátum: {type(raw_json)}")

            else:
                log(f"❌ {name} API Hiba: HTTP {res.status_code}")
                # Hiba esetén is mentsük le a választ, hátha beszédes a hibaüzenet
                try:
                    error_json = res.json()
                    log(f"❌ Hiba részletei: {error_json}")
                except:
                    log(f"❌ Hiba szöveg: {res.text[:200]}")

        except Exception as e:
            log(f"❌ Kivétel ({name}): {e}")

# --- VÉGREHAJTÁS ÉS HTML GENERÁLÁS ---
log("=== TÖBBFORRÁSOS KATALÓGUS GENERÁLÁS (DIAGNOSZTIKA) ===")
fetch_hada()
run_api_providers()

debug_log_formatted = "\n".join(debug_logs)

html_content = f"""<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Diagnosztika</title>
    <style>
        body {{ background: #0a0a0c; color: #e0e0e0; font-family: monospace; padding: 20px; }}
        .debug-box {{ background: #111; border: 1px solid #ff0055; padding: 20px; border-radius: 6px; }}
        h1 {{ color: #00ffcc; }}
        pre {{ white-space: pre-wrap; word-break: break-all; color: #00ffcc; font-size: 14px; }}
    </style>
</head>
<body>
    <h1>API Diagnosztikai Napló</h1>
    <p>A nyers JSON válaszokat megtalálod a <strong>debug_logs</strong> mappában!</p>
    <div class="debug-box">
        <pre>{debug_log_formatted}</pre>
    </div>
</body>
</html>
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)

print("\nKész. Nézd meg az index.html-t és a debug_logs mappát!")
sys.exit(0)
