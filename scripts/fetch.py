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
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")
os.makedirs(OUTPUT_DIR, exist_ok=True)

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
    if not HAS_BS4: return
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    search_terms = ["taktikai melleny"]
    
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
                    if re.search(r'\b(S|női|noi|dolls|woman|women)\b', title, re.IGNORECASE): continue
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
        "name": "Vinted",
        "url": "https://vinted-second-hand-marketplace-data-api.p.rapidapi.com/vinted/v1/catalog_search",
        "method": "POST",
        "host": "vinted-second-hand-marketplace-data-api.p.rapidapi.com",
        "json": {"query": "vest"},
        "paths": [["data", "items"], ["data"]], # Új útvonal a napló alapján
        "parse_item": lambda x: {
            "title": (x.get("title") or x.get("description") or "Vinted Vest")[:50],
            "price": f"{x.get('price', {}).get('amount')} {x.get('price', {}).get('currency_code')}" if isinstance(x.get("price"), dict) else (x.get("price") or "N/A"),
            "link": x.get("url") if str(x.get("url")).startswith("http") else f"https://www.vinted.com{x.get('url', '')}",
            "images": [x.get("photo", {}).get("url") if isinstance(x.get("photo"), dict) else x.get("image_url")]
        }
    },
    {
        "name": "AliExpress",
        "url": "https://aligate-aliexpress-data-api.p.rapidapi.com/api/v2/search/text",
        "method": "GET",
        "host": "aligate-aliexpress-data-api.p.rapidapi.com",
        "params": {"locale": "en_US", "query": "tactical vest", "country": "US", "page": "1", "currency": "USD"},
        "paths": [["item"], ["data", "items"]], # Új útvonal a napló alapján
        "parse_item": lambda x: {
            "title": (x.get("title") or "AliExpress Vest")[:50],
            "price": str(x.get("sku", {}).get("def", {}).get("promotionPrice") or x.get("price") or "N/A"),
            "link": x.get("itemUrl") if str(x.get("itemUrl")).startswith("http") else f"https:{x.get('itemUrl', '')}",
            "images": [x.get("image") or x.get("imageUrl")]
        }
    }
]

def run_api_providers():
    if not API_KEY:
        return

    for provider in API_PROVIDERS:
        name = provider['name']
        log(f"\n--- {name} API Keresés ---")
        headers = {"x-rapidapi-key": API_KEY, "x-rapidapi-host": provider["host"]}
        
        try:
            if provider["method"] == "GET":
                res = requests.get(provider["url"], headers=headers, params=provider.get("params"), timeout=15)
            else:
                res = requests.post(provider["url"], headers=headers, json=provider.get("json"), timeout=15)

            log(f"{name} HTTP Válaszkód: {res.status_code}")
            
            if res.status_code == 200:
                raw_json = res.json()
                items_list = extract_items_from_json(raw_json, provider["paths"])
                
                if items_list:
                    log(f"✅ Talált elemek: {len(items_list)}")
                    # Nyers JSON minta kiíratása az első elemről a weboldalra!
                    log(f"🔍 ELSŐ TERMÉK NYERS JSON-JA ({name}):\n{json.dumps(items_list[0], indent=2, ensure_ascii=False)}")
                    
                    added_count = 0
                    for item in items_list:
                        if isinstance(item, dict) and added_count < 6:
                            try:
                                parsed = provider["parse_item"](item)
                                parsed["source"] = name
                                items_data.append(parsed)
                                added_count += 1
                            except Exception as parse_err:
                                log(f"⚠️ Hiba az elem feldolgozásakor: {parse_err}")
                else:
                    log("❌ A válasz sikeres, de nem találtam listát az új útvonalakon sem.")
        except Exception as e:
            log(f"❌ Kivétel ({name}): {e}")

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
            <img src="{img_src}" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600'">
        </div>
        <div class="card-body">
            <h3>{item['title']}</h3>
            <div class="price">{item['price']}</div>
            <a href="{item['link']}" target="_blank" class="buy-btn">MEGTEKINTÉS</a>
        </div>
    </div>
    """

debug_log_formatted = "\n".join(debug_logs)

html_content = f"""<!DOCTYPE html>
<html lang="hu">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CYBERPUNK WARDROBE</title>
    <style>
        :root {{ --bg-color: #0a0a0c; --card-bg: #141419; --accent-neon: #00ffcc; --accent-pink: #ff0055; --text-color: #e0e0e0; --border-color: #2a2a35; }}
        body {{ background-color: var(--bg-color); color: var(--text-color); font-family: 'Segoe UI', Roboto, sans-serif; margin: 0; padding: 20px; }}
        .grid-container {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 25px; max-width: 1400px; margin: 0 auto; }}
        .product-card {{ background: var(--card-bg); border: 1px solid var(--border-color); border-radius: 6px; overflow: hidden; position: relative; display: flex; flex-direction: column; }}
        .source-badge {{ position: absolute; top: 10px; left: 10px; background: rgba(0,0,0,0.85); color: var(--accent-neon); padding: 4px 8px; font-size: 11px; font-weight: bold; border-radius: 3px; border: 1px solid var(--accent-neon); }}
        .image-gallery {{ height: 320px; background: #08080b; padding: 10px; display: flex; justify-content: center; align-items: center; }}
        .image-gallery img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
        .card-body {{ padding: 15px; display: flex; flex-direction: column; flex-grow: 1; justify-content: space-between; }}
        .card-body h3 {{ font-size: 14px; margin: 0 0 10px 0; height: 38px; overflow: hidden; }}
        .price {{ font-size: 18px; font-weight: bold; color: var(--accent-neon); margin-bottom: 15px; }}
        .buy-btn {{ text-align: center; background: var(--accent-pink); color: #fff; text-decoration: none; padding: 10px; font-size: 12px; font-weight: bold; border-radius: 4px; }}
        .debug-box {{ max-width: 1400px; margin: 50px auto; background: #111; border: 1px solid var(--accent-pink); padding: 20px; border-radius: 6px; }}
        .debug-log {{ color: #00ffcc; font-family: monospace; white-space: pre-wrap; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="grid-container">{cards_html}</div>
    <div class="debug-box">
        <h2 style="color:#ff0055; margin-top:0;">🛠 API DIAGNOSZTIKA</h2>
        <div class="debug-log">{debug_log_formatted}</div>
    </div>
</body>
</html>
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)
