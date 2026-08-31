import os
import json
import requests

API_KEY = os.environ.get("RAPIDAPI_KEY")
OUTPUT_DIR = "public"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "index.html")

os.makedirs(OUTPUT_DIR, exist_ok=True)

headers_base = {
    "Content-Type": "application/json",
    "x-rapidapi-key": API_KEY or ""
}

items_data = []

# 1. Grailed lekérdezés
def fetch_grailed():
    url = "https://grailed.p.rapidapi.com/search"
    headers = {**headers_base, "x-rapidapi-host": "grailed.p.rapidapi.com"}
    params = {"query": "jacket", "page": "1", "hitsPerPage": "12"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Grailed Státusz: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            hits = data.get("data", {}).get("search", {}).get("hits", [])
            for item in hits:
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
                    "source": "Grailed"
                })
    except Exception as e:
        print(f"Grailed hiba: {e}")

# 2. Poshmark lekérdezés
def fetch_poshmark():
    url = "https://poshmark.p.rapidapi.com/search"
    headers = {**headers_base, "x-rapidapi-host": "poshmark.p.rapidapi.com"}
    params = {"query": "nike", "domain": "com"}
    try:
        res = requests.get(url, headers=headers, params=params, timeout=10)
        print(f"Poshmark Státusz: {res.status_code}")
        if res.status_code == 200:
            data = res.json()
            data_list = data.get("data", [])
            for item in data_list:
                title = item.get("title", "Poshmark Termék")
                price = f"${item.get('price', 'N/A')}"
                link = f"https://poshmark.com/listing/{item.get('id')}" if item.get('id') else "https://poshmark.com"
                picture = item.get("picture_url")
                items_data.append({
                    "title": title,
                    "price": price,
                    "link": link,
                    "images": [picture] if picture else [],
                    "source": "Poshmark"
                })
    except Exception as e:
        print(f"Poshmark hiba: {e}")

fetch_grailed()
fetch_poshmark()

cards_html = ""
for item in items_data:
    imgs_html = ""
    imgs = item["images"] if item["images"] else ["https://via.placeholder.com/300x400/1a1a1a/00ffcc?text=Nincs+K%C3%A9p"]
    for img in imgs:
        imgs_html += f'<img src="{img}" alt="Termékkép" loading="lazy">'
    
    cards_html += f"""
    <div class="product-card">
        <div class="source-badge">{item['source']}</div>
        <div class="image-gallery">
            {imgs_html}
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
        }}
        .source-badge {{
            position: absolute;
            top: 10px;
            left: 10px;
            background: rgba(0,0,0,0.8);
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
            height: 220px;
            overflow-x: auto;
            background: #000;
        }}
        .image-gallery img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            flex-shrink: 0;
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
        <p style="color: #888; font-size: 13px;">Automatizált termék-katalógus RapidAPI integrációval</p>
    </header>

    <div class="grid-container">
        {cards_html if cards_html else '<p style="text-align:center; grid-column: 1/-1;">Nincs találat vagy az API kulcs nem érvényes.</p>'}
    </div>
</body>
</html>
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"Sikeresen generálva: {OUTPUT_FILE}, Összes elem: {len(items_data)}")
