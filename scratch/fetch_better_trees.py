import os
import sys
import ssl
import json
import urllib.request
from PIL import Image, ImageOps

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE
headers = {'User-Agent': 'BaghbaanAcademicBot/2.0 (contact@baghbaan.org)'}

def search(q, limit=10):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={urllib.parse.quote(q)}&gsrnamespace=6&gsrlimit={limit}&prop=imageinfo&iiprop=url|size|dimensions&format=json"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as r:
        data = json.loads(r.read())
    pages = data.get('query', {}).get('pages', {})
    out = []
    for pid, p in pages.items():
        title = p.get('title')
        infos = p.get('imageinfo', [])
        if infos:
            info = infos[0]
            if not title.lower().endswith(('.pdf', '.svg', '.tif')) and info['width'] >= 1000 and info['height'] >= 700:
                out.append((title, info['width'], info['height'], info['url']))
                print(f"  {title}: {info['width']}x{info['height']}")
    return out

print("--- Neem Candidates ---")
neem1 = search('"Neem tree"', 10)
neem2 = search('"Azadirachta indica" leaves', 10)

print("\n--- Sheesham Candidates ---")
shee1 = search('"Dalbergia sissoo"', 10)
shee2 = search('"Shisham"', 10)
