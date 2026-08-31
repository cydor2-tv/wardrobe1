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

log("=== TÖBBFORRÁSOS KATALÓGUS GENERÁLÁS ===")

# 1. HÁDA WEBSHOP SCRAPER (Releváns keresések + S méret kiszűrése)
def fetch_hada():
    log("\n--- [1/4] Háda Webshop Lekérdezés (Targeted & Filtered) ---")
    if not HAS_BS4:
        log("❌ Háda kihagyva (hiányzó bs4 modul)")
        return

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    # Cyberpunk / Wasteland releváns keresőszavak a Hádán
    search_terms = ["taktikai", "bor melleny", "zsebes", "kapucnis melleny", "motoros"]
    
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
                    
                    # SZŰRÉS: S méretű ruhák kiszűrése (pl. "mellény S" vagy " S " a címben)
                    if re.search(r'\bS\b', title, re.IGNORECASE):
                        continue
                        
                    link = title_elem['href'] if title_elem and title_elem.has_attr('href') else "https://hadawebshop.hu"
                    price = price_elem.get_text(strip=True) if price_elem else "N/A"
                    img = img_elem['src'] if img_elem and img_elem.has_attr('src') else None
                    
                    # Duplikációk elkerülése
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
            
    log(f"✅ Hádáról behelyezett releváns termékek: {len(items_data)}")

# 2. GERMAN AMAZON SCRAPER
def fetch_amazon_de():
    log("\n--- [2/4] German Amazon API Keresés ---")
    if not API_KEY:
        return
    url = "https://german-amazon-data-scraper.p.rapidapi.com/search/cyberpunk%20vest"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "german-amazon-data-scraper.p.rapidapi.com"
    }
    try:
        res = requests.get(url, headers=headers, timeout=15)
        log(f"Amazon.de HTTP Válaszkód: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            products = data.get("products", []) or (data if isinstance(data, list) else [])
            log(f"✅ Amazon.de talált elemek: {len(products)}")
            for item in products[:6]:
                title = item.get("title") or item.get("name") or "Amazon Termék"
                price = item.get("price") or item.get("current_price") or "N/A"
                link = item.get("url") or item.get("link") or "https://amazon.de"
                img = item.get("thumbnail") or item.get("image")
                items_data.append({
                    "title": title[:50] + "..." if len(title) > 50 else title,
                    "price": str(price),
                    "link": link if str(link).startswith("http") else f"https://amazon.de{link}",
                    "images": [img] if img else [],
                    "source": "Amazon.de"
                })
        else:
            log(f"❌ Amazon.de API Hiba: {res.status_code} (Szerver oldali válaszhiány)")
    except Exception as e:
        log(f"❌ Kivétel (Amazon.de): {e}")

# 3. SHEIN SCRAPER
def fetch_shein():
    log("\n--- [3/4] Shein API Keresés ---")
    if not API_KEY:
        return
    url = "https://shein-scraper-api.p.rapidapi.com/shein/product/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "shein-scraper-api.p.rapidapi.com"
    }
    params = {"keywords": "tactical vest", "currency": "USD", "country": "US"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        log(f"Shein HTTP Válaszkód: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            products = data.get("info", {}).get("products", []) or data.get("products", [])
            log(f"✅ Shein talált elemek: {len(products)}")
            for item in products[:6]:
                title = item.get("goods_name") or "Shein Techwear"
                price = item.get("sale_price", {}).get("amount") if isinstance(item.get("sale_price"), dict) else item.get("price", "N/A")
                img = item.get("goods_img")
                link = item.get("product_url") or "https://www.shein.com"
                items_data.append({
                    "title": title[:50] + "..." if len(title) > 50 else title,
                    "price": f"${price}",
                    "link": link if link.startswith("http") else f"https://www.shein.com{link}",
                    "images": [img] if img else [],
                    "source": "Shein"
                })
        else:
            log(f"❌ Shein API Hiba: {res.status_code}")
    except Exception as e:
        log(f"❌ Kivétel (Shein): {e}")

# 4. TEMU SCRAPER
def fetch_temu():
    log("\n--- [4/4] Temu API Keresés ---")
    if not API_KEY:
        return
    url = "https://temu-product-scraper.p.rapidapi.com/temu"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "temu-product-scraper.p.rapidapi.com"
    }
    params = {"keyword": "tactical vest", "maxItems": "6"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        log(f"Temu HTTP Válaszkód: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            products = data.get("products", []) or data.get("data", []) or (data if isinstance(data, list) else [])
            log(f"✅ Temu talált elemek: {len(products)}")
            for item in products[:6]:
                title = item.get("title") or item.get("name") or "Temu Termék"
                price = item.get("price") or "N/A"
                link = item.get("url") or item.get("link") or "https://temu.com"
                img = item.get("image") or item.get("thumbnail")
                items_data.append({
                    "title": title[:50] + "..." if len(title) > 50 else title,
                    "price": str(price),
                    "link": link,
                    "images": [img] if img else [],
                    "source": "Temu"
                })
        else:
            log(f"❌ Temu API Hiba: {res.status_code}")
    except Exception as e:
        log(f"❌ Kivétel (Temu): {e}")

# Végrehajtás
try:
    fetch_hada()
    fetch_amazon_de()
    fetch_shein()
    fetch_temu()
except Exception as main_e:
    log(f"❌ Fő folyamat kivétel: {main_e}")

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
        /* KÉPMÉRET-ARÁNY FIX: Nincs több levágás */
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
        <p style="color: #888; font-size: 13px;">Katalógus (Háda + Amazon.de + Temu + Shein)</p>
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
