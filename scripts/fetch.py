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

log(f"=== RAPIDAPI DIAGNOSZTIKA INDÍTÁSA ===")
if not API_KEY:
    log("❌ KRITIKUS HIBA: A RAPIDAPI_KEY környezeti változó üres vagy nem található!")
else:
    log(f"✅ RAPIDAPI_KEY megtalálva (Karakterszám: {len(API_KEY)}, Első 4 karakter: {API_KEY[:4]}...)")

# 1. POSHMARK LISTINGS API
def test_poshmark_listings():
    log("\n--- [1/3] Poshmark Listings API Teszt ---")
    url = "https://poshmark-listings-api.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "poshmark-listings-api.p.rapidapi.com"
    }
    params = {"query": "harness"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=12)
        log(f"HTTP Válaszkód: {res.status_code}")
        log(f"Válasz szöveg (első 300 kar.): {res.text[:300]}")
        
        if res.status_code == 200:
            data = res.json()
            raw_items = data.get("data", []) or data.get("listings", []) or (data if isinstance(data, list) else [])
            log(f"✅ Talált elemek száma: {len(raw_items)}")
            for item in raw_items[:10]:
                title = item.get("title") or item.get("name") or "Poshmark Termék"
                price = item.get("price") or "N/A"
                link = item.get("url") or item.get("link") or "https://poshmark.com"
                img = item.get("picture") or item.get("cover_shot", {}).get("url")
                items_data.append({
                    "title": title,
                    "price": f"${price}" if not str(price).startswith("$") else str(price),
                    "link": link,
                    "images": [img] if img else [],
                    "source": "Poshmark Listings API"
                })
        else:
            log(f"❌ Poshmark Listings API Hiba ({res.status_code})")
    except Exception as e:
        log(f"❌ Kivétel történt (Poshmark Listings): {e}")

# 2. POSHMARK FASHION RESALE API
def test_poshmark_resale():
    log("\n--- [2/3] Poshmark Fashion Resale API Teszt ---")
    url = "https://poshmark-fashion-resale.p.rapidapi.com/poshmark/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "poshmark-fashion-resale.p.rapidapi.com"
    }
    params = {"query": "nike shoes", "limit": "10"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=12)
        log(f"HTTP Válaszkód: {res.status_code}")
        log(f"Válasz szöveg (első 300 kar.): {res.text[:300]}")
        
        if res.status_code == 200:
            data = res.json()
            raw_items = data.get("data", []) or data.get("results", []) or (data if isinstance(data, list) else [])
            log(f"✅ Talált elemek száma: {len(raw_items)}")
            for item in raw_items[:10]:
                title = item.get("title") or item.get("title_text") or "Poshmark Termék"
                price = item.get("price") or item.get("formatted_price") or "N/A"
                link = item.get("url") or item.get("link") or "https://poshmark.com"
                img = item.get("picture_url") or item.get("cover_shot_url")
                items_data.append({
                    "title": title,
                    "price": str(price),
                    "link": link,
                    "images": [img] if img else [],
                    "source": "Poshmark Fashion Resale"
                })
        else:
            log(f"❌ Poshmark Fashion Resale Hiba ({res.status_code})")
    except Exception as e:
        log(f"❌ Kivétel történt (Poshmark Resale): {e}")

# 3. GRAILED API
def test_grailed():
    log("\n--- [3/3] Grailed API Teszt ---")
    url = "https://grailed.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "grailed.p.rapidapi.com"
    }
    params = {"query": "techwear", "page": "1", "hitsPerPage": "10"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=12)
        log(f"HTTP Válaszkód: {res.status_code}")
        log(f"Válasz szöveg (első 300 kar.): {res.text[:300]}")
        
        if res.status_code == 200:
            data = res.json()
            hits = data.get("data", {}).get("search", {}).get("hits", []) or data.get("hits", [])
            log(f"✅ Talált elemek száma: {len(hits)}")
            for item in hits[:10]:
                title = item.get("title") or item.get("name") or "Grailed Termék"
                price = f"${item.get('price', 'N/A')}"
                link = item.get("url") or "https://www.grailed.com"
                images = item.get("cover_photo", {}).get("url") or item.get("photo_url")
                img_list = [images] if isinstance(images, str) else (images or [])
                items_data.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "images": img_list[:1],
                    "source": "Grailed API"
                })
        else:
            log(f"❌ Grailed API Hiba ({res.status_code})")
    except Exception as e:
        log(f"❌ Kivétel történt (Grailed): {e}")

# Tesztek futtatása
if API_KEY:
    test_poshmark_listings()
    test_poshmark_resale()
    test_grailed()

# Tartalék kártyák, ha az API-k nem adnának vissza élő terméket
FALLBACK_ITEMS = [
    {
        "title": "Cyberpunk Tactical Chest Rig Harness",
        "price": "$79.00",
        "link": "https://www.grailed.com",
        "images": ["https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600&auto=format&fit=crop"],
        "source": "Tartalék (Demo)"
    },
    {
        "title": "Wasteland Heavy Duty Leather Strap Vest",
        "price": "$135.00",
        "link": "https://www.poshmark.com",
        "images": ["https://images.unsplash.com/photo-1517445312882-bc9910d016b7?w=600&auto=format&fit=crop"],
        "source": "Tartalék (Demo)"
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
            <img src="{img_src}" alt="Termékkép" loading="lazy">
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
            height: 240px;
            overflow: hidden;
            background: #000;
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

print("Kész. HTML frissítve a diagnosztikai naplóval.")
