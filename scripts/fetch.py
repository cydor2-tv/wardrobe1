import os
import requests
from bs4 import BeautifulSoup

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

# 1. HÁDA WEBSHOP DIRECT SCRAPER (Magyarországi használtruha)
def fetch_hada():
    log("\n--- [1/4] Háda Webshop Lekérdezés ---")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    url = "https://hadawebshop.hu/catalogsearch/result/"
    params = {"q": "mellény"} # Keresési kifejezés (pl. mellény, kabát, dzseki)
    
    try:
        res = requests.get(url, headers=headers, params=params, timeout=15)
        log(f"Háda HTTP Válaszkód: {res.status_code}")
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            # Magento 2 alapértelmezett termékkártya elemei
            products = soup.select('.product-item-info') or soup.select('.product-item')
            log(f"✅ Háda Webshopon talált elemek: {len(products)}")
            
            for item in products[:10]:
                title_elem = item.select_one('.product-item-link') or item.select_one('.product-item-name')
                price_elem = item.select_one('.price')
                img_elem = item.select_one('img.product-image-photo') or item.select_one('img')
                
                title = title_elem.get_text(strip=True) if title_elem else "Háda Ruházat"
                link = title_elem['href'] if title_elem and title_elem.has_attr('href') else "https://hadawebshop.hu"
                price = price_elem.get_text(strip=True) if price_elem else "N/A"
                img = img_elem['src'] if img_elem and img_elem.has_attr('src') else None
                
                items_data.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "images": [img] if img else [],
                    "source": "Háda Webshop (HU)"
                })
        else:
            log(f"❌ Háda Webshop Hiba: {res.status_code}")
    except Exception as e:
        log(f"❌ Kivétel (Háda Webshop): {e}")

# 2. GERMAN AMAZON DATA SCRAPER
def fetch_amazon_de():
    log("\n--- [2/4] German Amazon API Keresés ---")
    url = "https://german-amazon-data-scraper.p.rapidapi.com/search/tactical%20vest"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "german-amazon-data-scraper.p.rapidapi.com"
    }
    try:
        res = requests.get(url, headers=headers, timeout=20)
        log(f"Amazon.de HTTP Válaszkód: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            products = data.get("products", []) or data if isinstance(data, list) else []
            log(f"✅ Amazon.de talált elemek száma: {len(products)}")
            
            for item in products[:8]:
                title = item.get("title") or item.get("name") or "Amazon Termék"
                price = item.get("price") or item.get("current_price") or "N/A"
                link = item.get("url") or item.get("link") or "https://amazon.de"
                img = item.get("thumbnail") or item.get("image")
                
                items_data.append({
                    "title": title[:50] + "..." if len(title) > 50 else title,
                    "price": str(price),
                    "link": link if link.startswith("http") else f"https://amazon.de{link}",
                    "images": [img] if img else [],
                    "source": "Amazon.de"
                })
        else:
            log(f"❌ Amazon.de API Hiba: {res.status_code}")
    except Exception as e:
        log(f"❌ Kivétel (Amazon.de): {e}")

# 3. SHEIN SCRAPER API
def fetch_shein():
    log("\n--- [3/4] Shein API Keresés ---")
    url = "https://shein-scraper-api.p.rapidapi.com/shein/product/details"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "shein-scraper-api.p.rapidapi.com"
    }
    params = {"goods_id": "16477544", "currency": "usd", "country": "us", "language": "en"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=20)
        log(f"Shein HTTP Válaszkód: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            info = data.get("info", {}) or data
            title = info.get("goods_name") or "Shein Techwear Item"
            price = info.get("sale_price", {}).get("amount") or "N/A"
            img = info.get("goods_img")
            
            items_data.append({
                "title": title,
                "price": f"${price}",
                "link": "https://www.shein.com",
                "images": [img] if img else [],
                "source": "Shein API"
            })
            log("✅ Shein termék sikeresen hozzáadva")
        else:
            log(f"❌ Shein API Hiba: {res.status_code}")
    except Exception as e:
        log(f"❌ Kivétel (Shein): {e}")

# 4. TEMU PRODUCT SCRAPER
def fetch_temu():
    log("\n--- [4/4] Temu API Keresés ---")
    url = "https://temu-product-scraper.p.rapidapi.com/temu"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "temu-product-scraper.p.rapidapi.com"
    }
    params = {"keyword": "tactical harness", "maxItems": "8"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=20)
        log(f"Temu HTTP Válaszkód: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            products = data.get("products", []) or data.get("data", []) or (data if isinstance(data, list) else [])
            log(f"✅ Temu talált elemek száma: {len(products)}")
            
            for item in products[:8]:
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

# Lekérdezések futtatása
fetch_hada()
if API_KEY:
    fetch_amazon_de()
    fetch_shein()
    fetch_temu()

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
            height: 260px;
            overflow: hidden;
            background: #111;
        }}
        .image-gallery img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
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
        <p style="color: #888; font-size: 13px;">Élő Marketplace katalógus (HádaHU + Amazon.de + Temu + Shein)</p>
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

print("HTML Generálás befejeződött.")
