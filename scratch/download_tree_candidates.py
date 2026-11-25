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

def get_url(title):
    url = f"https://commons.wikimedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}&prop=imageinfo&iiprop=url&format=json"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as r:
        data = json.loads(r.read())
    pages = data['query']['pages']
    for pid, p in pages.items():
        return p['imageinfo'][0]['url']

def download_and_check(title, filename):
    url = get_url(title)
    print(f"Downloading {title} from {url}...")
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, context=ctx) as r:
        data = r.read()
    dest = os.path.join("scratch", filename)
    with open(dest, "wb") as f:
        f.write(data)
    im = Image.open(dest)
    print(f"  Saved to {dest} ({im.size}, {len(data)} bytes, format: {im.format})")
    return dest

os.makedirs("scratch", exist_ok=True)

# 1. Download Sheesham candidates
download_and_check("File:Shisham leaves.jpg", "sheesham_cand1_leaves.jpg")
download_and_check("File:Dalbergia sissoo.jpg", "sheesham_cand2_tree.jpg")
download_and_check("File:Sisau Tree, Indian rosewood, (Dalbergia sissoo)-IMG 7825.jpg", "sheesham_cand3_tree.jpg")

# 2. Download Neem candidates
download_and_check("File:Leaves Azadirachta indica Heritage tree Philippines.jpg", "neem_cand1_leaves.jpg")
download_and_check("File:Neem leaves Neem Leaves.jpg", "neem_cand2_leaves.jpg")
download_and_check("File:Azadirachta indica - Neem at Tenkasi 2014 (1).jpg", "neem_cand3_tree.jpg")
