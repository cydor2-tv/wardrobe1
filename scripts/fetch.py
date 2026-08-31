import os
import json
import requests

API_KEY = os.environ.get("RAPIDAPI_KEY", "").strip()
OUTPUT_DIR = "public"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)

debug_logs = []
items_data = []

def log(msg):
    print(msg)
    debug_logs.append(str(msg))

log("=== CYBERPUNK & WASTELAND KATALÓGUS GENERÁLÁS ===")
if not API_KEY:
    log("❌ KRITIKUS HIBA: A RAPIDAPI_KEY környezeti változó üres!")
else:
    log(f"✅ RAPIDAPI_KEY aktív (Karakterszám: {len(API_KEY)})")

# 1. POSHMARK LISTINGS API
def fetch_poshmark_listings():
    log("\n--- [1/3] Poshmark Listings API Keresés ---")
    url = "https://poshmark-listings-api.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "poshmark-listings-api.p.rapidapi.com"
    }
    params = {"query": "tactical harness"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=20)
        log(f"HTTP Válaszkód: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            # Az API a 'products' mezőben küldi a termékeket
            products = data.get("products", []) or data.get("data", []) or []
            log(f"✅ Talált Poshmark Listings elemek száma: {len(products)}")
            
            for item in products[:12]:
                title = item.get("title") or item.get("name") or "Tactical Harness"
                price = item.get("price") or "N/A"
                link = item.get("link") or item.get("url") or "https://poshmark.com"
                
                # Kép kicsomagolása
                img = None
                if isinstance(item.get("cover_shot"), dict):
                    img = item.get("cover_shot", {}).get("url")
                if not img:
                    img = item.get("picture") or item.get("image")
                
                items_data.append({
                    "title": title,
                    "price": f"${price}" if not str(price).startswith("$") else str(price),
                    "link": link,
                    "images": [img] if img else [],
                    "source": "Poshmark Listings"
                })
        else:
            log(f"❌ Poshmark Listings Hiba: {res.status_code}")
    except Exception as e:
        log(f"❌ Kivétel (Poshmark Listings): {e}")

# 2. POSHMARK FASHION RESALE API
def fetch_poshmark_resale():
    log("\n--- [2/3] Poshmark Fashion Resale API Keresés ---")
    url = "https://poshmark-fashion-resale.p.rapidapi.com/poshmark/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "poshmark-fashion-resale.p.rapidapi.com"
    }
    params = {"query": "techwear vest", "limit": "12"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=20)
        log(f"HTTP Válaszkód: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            results = data.get("results", []) or data.get("data", []) or []
            log(f"✅ Talált Poshmark Resale elemek száma: {len(results)}")
            
            for item in results[:12]:
                title = item.get("title") or "Techwear Vest"
                price = item.get("price") or item.get("formatted_price") or "N/A"
                
                # Link generálás hirdetés azonosítóból, ha nincs közvetlen URL
                listing_id = item.get("listingId") or item.get("id")
                link = item.get("url") or (f"https://poshmark.com/listing/{listing_id}" if listing_id else "https://poshmark.com")
                
                img = item.get("picture_url") or item.get("cover_shot_url") or item.get("picture")
                
                items_data.append({
                    "title": title,
                    "price": f"${price}" if not str(price).startswith("$") else str(price),
                    "link": link,
                    "images": [img] if img else [],
                    "source": "Poshmark Resale"
                })
        else:
            log(f"❌ Poshmark Resale Hiba: {res.status_code}")
    except Exception as e:
        log(f"❌ Kivétel (Poshmark Resale): {e}")

# 3. GRAILED API
def fetch_grailed():
    log("\n--- [3/3] Grailed API Keresés ---")
    url = "https://grailed.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "grailed.p.rapidapi.com"
    }
    params = {"query": "cyberpunk harness", "page": "1", "hitsPerPage": "12"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=25)
        log(f"HTTP Válaszkód: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            hits = data.get("data", {}).get("search", {}).get("hits", []) or data.get("hits", []) or []
            log(f"✅ Talált Grailed elemek száma: {len(hits)}")
            
            for item in hits[:12]:
                title = item.get("title") or item.get("name") or "Cyberpunk Item"
                price = item.get("price", "N/A")
                link = item.get("url") or "https://www.grailed.com"
                
                img = None
                if isinstance(item.get("cover_photo"), dict):
                    img = item.get("cover_photo", {}).get("url")
                if not img:
                    img = item.get("photo_url") or item.get("image_url")
                
                items_data.append({
                    "title": title,
                    "price": f"${price}" if not str(price).startswith("$") else str(price),
                    "link": link,
                    "images": [img] if img else [],
                    "source": "Grailed"
                })
        else:
            log(f"❌ Grailed API Hiba: {res.status_code}")
    except Exception as e:
        log(f"❌ Kivétel (Grailed): {e}")

# Keresések lefuttatása
if API_KEY:
    fetch_poshmark_listings()
    fetch_poshmark_resale()
    fetch_grailed()

# Tartalék kártyák (csak ha egyetlen API sem adna semmit)
FALLBACK_ITEMS = [
    {
        "title": "Cyberpunk Tactical Chest Rig Harness",
        "price": "$79.00",
        "link": "https://www.grailed.com",
        "images": ["https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600&auto=format&fit=crop"],
        "source": "Demo Backup"
    }
]

display_items = items_data if len(items_data) > 0 else FALLBACK_ITEMS

cards_html = ""
for item in display_items:
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
        <p style="color: #888; font-size: 13px;">Élő Marketplace katalógus RapidAPI integrációval</p>
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

print("HTML Sikeresen kigenerálva!")
