import os
import sys
import shutil
from PIL import Image

import django
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baghbaan.settings')
django.setup()

from django.core.files.base import ContentFile
from plants.models import Plant

sheesham_art = r"C:\Users\mubee\.gemini\antigravity\brain\9c5863c6-fe3e-4e52-b51f-8198f191ae7b\sheesham_upright_tree_1795522381299.jpg"
neem_art = r"C:\Users\mubee\.gemini\antigravity\brain\9c5863c6-fe3e-4e52-b51f-8198f191ae7b\neem_upright_tree_1795522382591.jpg"

print("Checking generated files:")
for path in [sheesham_art, neem_art]:
    if os.path.exists(path):
        im = Image.open(path)
        print(f"  {os.path.basename(path)}: {im.size}, {os.path.getsize(path)} bytes, format: {im.format}")
    else:
        print(f"  MISSING: {path}")

def smart_crop_4_3(img, target_size=(1200, 900)):
    if img.mode != 'RGB':
        img = img.convert('RGB')
    w, h = img.size
    target_w, target_h = target_size
    target_aspect = target_w / target_h
    current_aspect = w / h
    
    if current_aspect > target_aspect:
        crop_w = int(h * target_aspect)
        left = (w - crop_w) // 2
        img = img.crop((left, 0, left + crop_w, h))
    else:
        crop_h = int(w / target_aspect)
        top = int((h - crop_h) * 0.35)
        img = img.crop((0, top, w, top + crop_h))
        
    return img.resize(target_size, Image.Resampling.LANCZOS)

# 1. Update Plant 40: Sheesham / Tahli
p40 = Plant.objects.get(id=40)
im40 = Image.open(sheesham_art)
cropped_40 = smart_crop_4_3(im40)
buf40 = os.path.join("scratch", "sheesham_final_1200x900.jpg")
cropped_40.save(buf40, format="JPEG", quality=92, optimize=True)

with open(buf40, "rb") as f:
    p40.image.save("plant_40_dalbergia_sissoo.jpg", ContentFile(f.read()), save=True)
print(f"Updated Plant 40 in DB: {p40.image.name} ({cropped_40.size}, {os.path.getsize(p40.image.path)} bytes)")

# 2. Update Plant 37: Neem
p37 = Plant.objects.get(id=37)
im37 = Image.open(neem_art)
cropped_37 = smart_crop_4_3(im37)
buf37 = os.path.join("scratch", "neem_final_1200x900.jpg")
cropped_37.save(buf37, format="JPEG", quality=92, optimize=True)

with open(buf37, "rb") as f:
    p37.image.save("plant_37_azadirachta_indica.jpg", ContentFile(f.read()), save=True)
print(f"Updated Plant 37 in DB: {p37.image.name} ({cropped_37.size}, {os.path.getsize(p37.image.path)} bytes)")

# Also overwrite all legacy aliases in media/plants/
sheesham_aliases = [
    "media/plants/plant_40.jpg",
    "media/plants/plant_40_dalbergia_sissoo.jpg",
    "media/plants/plant_40_dalbergia_sissoo_LsoowOT.jpg",
    "media/plants/plant_40_dalbergia_sissoo_PZi3VXp.jpg",
    "media/plants/plant_40_dalbergia_sissoo_j8RVrWC.jpg",
]

for a in sheesham_aliases:
    shutil.copy2(p40.image.path, a)
    print(f"  Overwrote {a}")

neem_aliases = [
    "media/plants/plant_37.jpg",
    "media/plants/plant_37_neem.jpg",
    "media/plants/plant_37_azadirachta_indica.jpg",
    "media/plants/plant_37_azadirachta_indica_090lP30.jpg",
    "media/plants/plant_37_azadirachta_indica_ESpykqh.jpg",
]

for a in neem_aliases:
    shutil.copy2(p37.image.path, a)
    print(f"  Overwrote {a}")
