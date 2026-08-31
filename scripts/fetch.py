import os
import sys
import re
import requests

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

API_KEY = os.environ.get("RAPIDAPI_KEY", "").strip()
OUTPUT_DIR = "public"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)

debug_logs = []
items_data = []

def log(msg):
    print(msg)
    debug_logs.append(str(msg))

# -------------------------------------------------------------------
# 1. HELPER / PARSER FÜGGVÉNYEK
# -------------------------------------------------------------------

def safe_extract_list(data, keys):
    """Biztonságosan kinyeri a listát beágyazott dict-ből anélkül, hogy hibát dobona."""
    current = data
    for k in keys:
        if isinstance(current, dict):
            current = current.get(k, {})
        else:
            return []
    return current if isinstance(current, list) else []

# -------------------------------------------------------------------
# 2. HÁDA KÜLÖNÁLLÓ SCRAPER (HTML alapú)
# -------------------------------------------------------------------

def fetch_hada():
    log("\n--- [1/5] Háda Webshop Lekérdezés ---")
    if not HAS_BS4:
        log("❌ Háda kihagyva (hiányzó bs4 modul)")
        return

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    search_terms = ["taktikai", "bor melleny", "zsebes melleny", "motoros melleny"]
    
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
                    price_elem = item.select_one('.price')
                    img_elem = item.select_one('img.product-image-photo') or item.select_one('img')
                    
                    title = title_elem.get_text(strip=True) if title_elem else ""
                    
                    # S-es méret és női ruhák szűrése
                    if re.search(r'\b(S|női|noi|dolls|woman|women)\b', title, re.IGNORECASE):
                        continue
                        
                    link = title_elem['href'] if title_elem and title_elem.has_attr('href') else "https://hadawebshop.hu"
                    price = price_elem.get_text(strip=True) if price_elem else "N/A"
                    img = img_elem['src'] if img_elem and img_elem.has_attr('src') else None
                    
                    if title and not any(d['title'] == title for d in items_data):
                        items_data.append({
                            "title": title,
                            "price": price,
                            "link": link,
                            "images": [img] if img else [],
                            "source": f"Háda HU ({term})"
                        })
        except Exception as e:
            log(f"❌ Háda hiba [{term}]: {e}")
            
    log(f"✅ Hádáról behelyezett releváns termékek: {len(items_data) - count_before}")

# -------------------------------------------------------------------
# 3. CONFIG-ALAPÚ API PROVIDEREK A RAPIDAPI-HOZ
# -------------------------------------------------------------------

API_PROVIDERS = [
    {
        "name": "Temu",
        "url": "https://temu-product-scraper.p.rapidapi.com/temu",
        "method": "GET",
        "host": "temu-product-scraper.p.rapidapi.com",
        "params": {"keyword": "tactical vest", "maxItems": "6"},
        "path_to_list": ["products"],
        "parse_item": lambda x: {
            "title": (x.get("title") or x.get("name") or "Temu Vest")[:50],
            "price": str(x.get("price", "N/A")),
            "link": x.get("url") or x.get("link") or "https://temu.com",
            "images": [x.get("image") or x.get("thumbnail")]
        }
    },
    {
        "name": "Vinted",
        "url": "https://vinted-second-hand-marketplace-data-api.p.rapidapi.com/vinted/v1/catalog_search",
        "method": "POST",
        "host": "vinted-second-hand-marketplace-data-api.p.rapidapi.com",
        "json": {"query": "tactical vest"},
        "path_to_list": ["items"],
        "parse_item": lambda x: {
            "title": (x.get("title") or "Vinted Vest")[:50],
            "price": f"{x.get('price')} EUR" if x.get("price") else "N/A",
            "link": x.get("url") or "https://vinted.com",
            "images": [x.get("photo", {}).get("url") if isinstance(x.get("photo"), dict) else None]
        }
    },
    {
        "name": "AliExpress",
        "url": "https://aligate-aliexpress-data-api.p.rapidapi.com/api/v2/search/text",
        "method": "GET",
        "host": "aligate-aliexpress-data-api.p.rapidapi.com",
        "params": {"locale": "en_US", "query": "cyberpunk vest", "country": "US", "page": "1", "currency": "USD"},
        "path_to_list": ["data", "items"],
        "parse_item": lambda x: {
            "title": (x.get("title") or "AliExpress Vest")[:50],
            "price": str(x.get("sku", {}).get("def", {}).get("price") or x.get("price") or "N/A"),
            "link": x.get("itemUrl") if str(x.get("itemUrl")).startswith("http") else f"https:{x.get('itemUrl')}",
            "images": [x.get("image")]
        }
    },
    {
        "name": "FB Marketplace",
        "url": "https://facebook-pages-scraper2.p.rapidapi.com/get_facebook_marketplace_items_listing",
        "method": "GET",
        "host": "facebook-pages-scraper2.p.rapidapi.com",
        "params": {
            "query": "tactical vest",
            "commerce_search_sort_by": "BEST_MATCH",
            "filter_location_latitude": "47.4979",
            "filter_location_longitude": "19.0402",
            "filter_radius_km": "100",
            "proxy_country": "gb"
        },
        "path_to_list": ["data"],
        "parse_item": lambda x: {
            "title": (x.get("title") or "FB Item")[:50],
            "price": str(x.get("price", {}).get("formatted_amount") if isinstance(x.get("price"), dict) else "N/A"),
            "link": x.get("url") if str(x.get("url")).startswith("http") else f"https://facebook.com{x.get('url')}",
            "images": [x.get("primary_listing_photo", {}).get("image", {}).get("uri") if isinstance(x.get("primary_listing_photo"), dict) else None]
        }
    }
]

def run_api_providers():
    if not API_KEY:
        log("\n⚠️ RAPIDAPI_KEY nincs beállítva, API hívások kihagyva.")
        return

    for idx, provider in enumerate(API_PROVIDERS, start=2):
        log(f"\n--- [{idx}/5] {provider['name']} API Keresés ---")
        headers = {
            "x-rapidapi-key": API_KEY,
            "x-rapidapi-host": provider["host"]
        }
        
        try:
            if provider["method"] == "GET":
                res = requests.get(provider["url"], headers=headers, params=provider.get("params"), timeout=12)
            else:
                res = requests.post(provider["url"], headers=headers, json=provider.get("json"), timeout=12)

            log(f"{provider['name']} HTTP Válaszkód: {res.status_code}")
            
            if res.status_code == 200:
                raw_json = res.json()
                
                # Lista kinyerése
                if isinstance(raw_json, list):
                    items_list = raw_json
                else:
                    items_list = safe_extract_list(raw_json, provider["path_to_list"])
                
                log(f"✅ {provider['name']} talált elemek: {len(items_list)}")
                
                # Biztonságos feldolgozás (Szeletelési hiba elleni védelem)
                for item in list(items_list)[:6]:
                    if isinstance(item, dict):
                        parsed = provider["parse_item"](item)
                        parsed["source"] = provider["name"]
                        items_data.append(parsed)
            else:
                log(f"❌ {provider['name']} API Hiba: HTTP {res.status_code}")

        except Exception as e:
            log(f"❌ Kivétel ({provider['name']}): {e}")

# -------------------------------------------------------------------
# 4. MAIN EXECUTOR & HTML RENDER
# -------------------------------------------------------------------

log("=== TÖBBFORRÁSOS KATALÓGUS GENERÁLÁS ===")
fetch_hada()
run_api_providers()

cards_html = ""
for item in items_data:
    img_src = item["images"][0] if item["images"] and item["images"][0] else "https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600"
    cards_html += f"""
    <div class="product-card">
        <div class="source-badge">{item['source']}</div>
        <div class="image-gallery">
            <img src="{img_src}" alt="{item['title']}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600'">
        </div>
        <div class="card-body">
            <h3>{item['title']}</h3>
            <div class="price">{item['price']}</div>
            <a href="{item['link']}" target="_blank" rel="noopener noreferrer" class="buy-btn">MEGTEKINTÉS</a>
        </div>
    </div>
    """

debug_log_formatted = "\n".join(debug_logs)

html_content = f"""<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CYBERPUNK & WASTELAND WARDROBE CATALOG</title>
    <style>
        :root {{
            --bg-color: #0a0a0c;
            --card-bg: #141419;
            --accent-neon: #00ffcc;
            --accent-pink: #ff0055;
            --text-color: #e0e0e0;
            --border-color: #2a2a35;
        }}
        body {{
            background-color: var(--bg-color);
            color: var(--text-color);
            font-family: 'Segoe UI', Roboto, monospace, sans-serif;
            margin: 0;
            padding: 20px;
        }}
        header {{
            text-align: center;
            padding: 20px 0 40px 0;
            border-bottom: 2px solid var(--accent-pink);
            margin-bottom: 30px;
        }}
        h1 {{
            color: var(--accent-neon);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin: 0;
            font-size: 26px;
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
            gap: 25px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .product-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            overflow: hidden;
            position: relative;
            display: flex;
            flex-direction: column;
            transition: transform 0.2s, border-color 0.2s;
        }}
        .product-card:hover {{
            transform: translateY(-5px);
            border-color: var(--accent-neon);
            box-shadow: 0 0 15px rgba(0, 255, 204, 0.2);
        }}
        .source-badge {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.85);
            color: var(--accent-neon);
            padding: 4px 8px;
            font-size: 11px;
            font-weight: bold;
            border-radius: 3px;
            z-index: 2;
            border: 1px solid var(--accent-neon);
        }}
        .image-gallery {{
            display: flex;
            align-items: center;
            justify-content: center;
            height: 320px;
            background: #08080b;
            padding: 10px;
            box-sizing: border-box;
        }}
        .image-gallery img {{
            max-width: 100%;
            max-height: 100%;
            width: auto;
            height: auto;
            object-fit: contain;
        }}
        .card-body {{
            padding: 15px;
            display: flex;
            flex-direction: column;
            flex-grow: 1;
            justify-content: space-between;
        }}
        .card-body h3 {{
            font-size: 14px;
            margin: 0 0 10px 0;
            height: 38px;
            overflow: hidden;
            line-height: 1.3;
        }}
        .price {{
            font-size: 18px;
            font-weight: bold;
            color: var(--accent-neon);
            margin-bottom: 15px;
        }}
        .buy-btn {{
            display: block;
            text-align: center;
            background: var(--accent-pink);
            color: #fff;
            text-decoration: none;
            padding: 10px;
            font-weight: bold;
            font-size: 12px;
            letter-spacing: 1px;
            border-radius: 4px;
            transition: background 0.2s;
        }}
        .buy-btn:hover {{
            background: #d40045;
        }}
        .debug-box {{
            max-width: 1400px;
            margin: 50px auto 20px auto;
            background: #000;
            border: 1px solid var(--accent-pink);
            padding: 20px;
            border-radius: 6px;
        }}
        .debug-box h2 {{
            color: var(--accent-pink);
            font-size: 16px;
            margin-top: 0;
        }}
        .debug-log {{
            background: #111;
            color: #00ffcc;
            font-family: monospace;
            padding: 15px;
            white-space: pre-wrap;
            word-break: break-all;
            font-size: 12px;
            border-radius: 4px;
            max-height: 400px;
            overflow-y: auto;
        }}
    </style>
</head>
<body>
    <header>
        <h1>Cyberpunk / Wasteland Wardrobe</h1>
        <p style="color: #888; font-size: 13px;">Katalógus (Háda + Temu + Vinted + AliExpress + FB Marketplace)</p>
    </header>

    <div class="grid-container">
        {cards_html}
    </div>

    <div class="debug-box">
        <h2>🛠 API DIAGNOSZTIKA ÉS KERESÉSI NAPLÓ</h2>
        <div class="debug-log">{debug_log_formatted}</div>
    </div>
</body>
</html>
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)

print("Kész. Generálás sikeres.")
sys.exit(0)
