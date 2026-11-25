import os
import sys
import json
import ssl
import urllib.request

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

articles = [
    ('Adrak / Ginger', 'Zingiber_officinale'),
    ('Bhindi / Okra', 'Okra'),
    ('Mooli / Radish', 'Daikon'),
    ('Amrood / Guava', 'Guava'),
    ('Shahtoot / Mulberry', 'Morus_nigra'),
    ('Injeer / Fig', 'Common_fig'),
    ('Cheeku / Sapodilla', 'Sapodilla'),
    ('Bakain / Chinaberry', 'Melia_azedarach'),
    ('Kari Patta / Curry Leaf', 'Curry_tree'),
    ('Tulsi / Holy Basil', 'Ocimum_tenuiflorum'),
    ('Lehsan / Garlic', 'Garlic'),
    ('Tamatar / Tomato', 'Tomato'),
    ('Kheera / Cucumber', 'Cucumber'),
    ('Shimla Mirch / Bell Pepper', 'Bell_pepper'),
    ('Gajar / Carrot', 'Carrot'),
    ('Karela / Bitter Gourd', 'Momordica_charantia'),
    ('Tori / Ridge Gourd', 'Luffa_acutangula'),
    ('Nimbu / Lemon', 'Lemon'),
    ('Anar / Pomegranate', 'Pomegranate'),
    ('Aam / Mango', 'Mango'),
    ('Falsa', 'Grewia_asiatica'),
    ('Neem', 'Azadirachta_indica'),
    ('Moringa', 'Moringa_oleifera'),
    ('Sukh Chain', 'Millettia_pinnata'),
    ('Sheesham', 'Dalbergia_sissoo'),
]

headers = {'User-Agent': 'BaghbaanAcademicBot/8.0 (contact@baghbaan.ai)'}

print(f"{'Item':25s} | {'Source File':40s} | {'Dimensions':12s} | URL")
print("-" * 110)

for label, title in articles:
    url = f"https://en.wikipedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=pageimages&format=json&pilicense=any&piprop=original"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ctx, timeout=8) as r:
            data = json.loads(r.read().decode())
            pages = data.get('query', {}).get('pages', {})
            for pid, p in pages.items():
                orig = p.get('original', {})
                src = orig.get('source', '')
                w = orig.get('width', 0)
                h = orig.get('height', 0)
                fn = os.path.basename(src.split('?')[0]) if src else 'NONE'
                print(f"{label:25s} | {fn[:40]:40s} | {w}x{h:<8d} | {src}")
    except Exception as e:
        print(f"{label:25s} | ERROR: {e}")
