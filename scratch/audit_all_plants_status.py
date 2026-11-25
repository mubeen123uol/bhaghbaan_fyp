import os
import sys
import django

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baghbaan.settings')
django.setup()

from plants.models import Plant
from PIL import Image

print(f"{'ID':<3} | {'Plant Name':<35} | {'Dimensions':<12} | {'Size KB':<8} | {'Status':<10}")
print("-" * 75)

for p in Plant.objects.all().order_by('id'):
    if p.image and os.path.exists(p.image.path):
        im = Image.open(p.image.path)
        sz_kb = os.path.getsize(p.image.path) // 1024
        status = "OK"
        # Check aspect ratio
        w, h = im.size
        if w < 1000 or h < 800:
            status = "LOW_RES"
        print(f"{p.id:<3} | {p.name_en:<35} | {f'{w}x{h}':<12} | {sz_kb:<8} | {status}")
    else:
        print(f"{p.id:<3} | {p.name_en:<35} | MISSING FILE")
