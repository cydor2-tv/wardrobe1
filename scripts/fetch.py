import os
import json
import requests

API_KEY = os.environ.get("RAPIDAPI_KEY", "").strip()
OUTPUT_DIR = "public"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)

items_data = []

# 1. Grailed API lekérdezése
def fetch_grailed():
    if not API_KEY:
        return
    url = "https://grailed.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "grailed.p.rapidapi.com"
    }
    params = {"query": "techwear", "page": "1", "hitsPerPage": "10"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Grailed status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            hits = data.get("data", {}).get("search", {}).get("hits", []) or data.get("hits", [])
            for item in hits:
                title = item.get("title") or item.get("name") or "Grailed Item"
                price = f"${item.get('price', 'N/A')}"
                link = item.get("url") or "https://www.grailed.com"
                images = item.get("cover_photo", {}).get("url") or item.get("photo_url")
                img_list = [images] if isinstance(images, str) else (images or [])
                items_data.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "images": img_list[:1],
                    "source": "Grailed"
                })
    except Exception as e:
        print(f"Grailed hiba: {e}")

# 2. Poshmark Listings API lekérdezése
def fetch_poshmark():
    if not API_KEY:
        return
    url = "https://poshmark-listings-api.p.rapidapi.com/search"
    headers = {
        "x-rapidapi-key": API_KEY,
        "x-rapidapi-host": "poshmark-listings-api.p.rapidapi.com"
    }
    params = {"query": "cyberpunk harness"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Poshmark status: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            results = data.get("data", []) or data.get("listings", []) or []
            for item in results:
                title = item.get("title") or item.get("name") or "Poshmark Item"
                price = item.get("price") or "N/A"
                link = item.get("url") or item.get("link") or "https://poshmark.com"
                img = item.get("picture") or item.get("cover_shot", {}).get("url")
                items_data.append({
                    "title": title,
                    "price": f"${price}" if not str(price).startswith("$") else str(price),
                    "link": link,
                    "images": [img] if img else [],
                    "source": "Poshmark"
                })
    except Exception as e:
        print(f"Poshmark hiba: {e}")

# Lekérdezések indítása
fetch_grailed()
fetch_poshmark()

# Tartalék adatok, ha semmilyen élő találat nem érkezne
FALLBACK_ITEMS = [
    {
        "title": "Cyberpunk Tactical Harness Vest",
        "price": "$89.00",
        "link": "https://www.grailed.com",
        "images": ["https://images.unsplash.com/photo-1551488831-00ddcb6c6bd3?w=600&auto=format&fit=crop"],
        "source": "Grailed / Demo"
    },
    {
        "title": "Wasteland Heavy Duty Leather Strap Vest",
        "price": "$135.00",
        "link": "https://www.poshmark.com",
        "images": ["https://images.unsplash.com/photo-1517445312882-bc9910d016b7?w=600&auto=format&fit=crop"],
        "source": "Poshmark / Demo"
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
</body>
</html>
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Generálás kész. Megjelenített termékek száma: {len(display_items)}")
