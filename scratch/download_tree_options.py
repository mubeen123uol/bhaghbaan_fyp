import os
import sys
import io
import time
import ssl
import urllib.request
from PIL import Image

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'BaghbaanHorticultureQualityAudit/9.0 (academic@baghbaan.ai)'
}

urls = {
    'sheesham_leaves': 'https://upload.wikimedia.org/wikipedia/commons/5/5c/Shisham_leaves.jpg',
    'sheesham_tree': 'https://upload.wikimedia.org/wikipedia/commons/5/5b/Dalbergia_sissoo.jpg',
    'sheesham_nepal': 'https://upload.wikimedia.org/wikipedia/commons/1/11/Sisau_Tree%2C_Indian_rosewood%2C_%28Dalbergia_sissoo%29-IMG_7825.jpg',
    'neem_leaves1': 'https://upload.wikimedia.org/wikipedia/commons/9/90/Neem_leaves_Neem_Leaves.jpg',
    'neem_leaves2': 'https://upload.wikimedia.org/wikipedia/commons/2/22/Leaves_Azadirachta_indica_Heritage_tree_Philippines.jpg',
    'neem_tree_punjab': 'https://upload.wikimedia.org/wikipedia/commons/4/4d/Azadirachta_indica_tree_located_in_Moga_city%2C_Moga_tehsil%2C_Moga_district%2C_Punjab%2C_India%2C_9_April_2023_01.jpg',
    'neem_green_branch': 'https://upload.wikimedia.org/wikipedia/commons/2/20/Neem_%28Azadirachta_indica%29_in_Hyderabad_W_IMG_6976.jpg'
}

os.makedirs('scratch/tree_cands', exist_ok=True)

for name, url in urls.items():
    dest = f'scratch/tree_cands/{name}.jpg'
    print(f'Fetching {name}...')
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = resp.read()
        with open(dest, 'wb') as f:
            f.write(data)
        im = Image.open(dest)
        print(f'  ✓ {name}: {im.size}, {len(data)} bytes')
    except Exception as e:
        print(f'  ✗ {name}: {e}')
    time.sleep(1.0)
