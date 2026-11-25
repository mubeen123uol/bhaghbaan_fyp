import os
import sys
import urllib.request
import django

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baghbaan.settings')
django.setup()

from django.core.files.base import ContentFile
from plants.models import Plant, Disease
from marketplace.models import Product
from care.models import UserPlant, PlantPhoto
from services.models import Garden
from community.models import Group
from accounts.models import User

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def download_image(url):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as resp:
            if resp.status == 200:
                return resp.read()
    except Exception as e:
        print(f"Error downloading {url}: {e}")
    return None

def run():
    print("==================================================")
    print("DOWNLOADING & ASSIGNING CURATED BOTANICAL IMAGES")
    print("==================================================")

    # 1. MARKETPLACE PRODUCTS
    product_images = {
        1: ("neem_oil.jpg", "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=800&auto=format&fit=crop&q=80"),
        2: ("compost.jpg", "https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=800&auto=format&fit=crop&q=80"),
        3: ("desi_rose_pot.jpg", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=800&auto=format&fit=crop&q=80"),
        4: ("lemon_plant.jpg", "https://images.unsplash.com/photo-1534856966150-c832f7b7f0ac?w=800&auto=format&fit=crop&q=80"),
        5: ("kitchen_seeds.jpg", "https://images.unsplash.com/photo-1509316975850-ff9c5deb0cd9?w=800&auto=format&fit=crop&q=80"),
        6: ("clay_pots.jpg", "https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=800&auto=format&fit=crop&q=80"),
        7: ("pruning_shears.jpg", "https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=800&auto=format&fit=crop&q=80"),
        8: ("npk_fertilizer.jpg", "https://images.unsplash.com/photo-1585314062340-f1a5a7c9328d?w=800&auto=format&fit=crop&q=80"),
    }

    print("\n--- [1/5] Updating Marketplace Products ---")
    for pid, (fname, url) in product_images.items():
        try:
            prod = Product.objects.get(id=pid)
            data = download_image(url)
            if data:
                prod.main_image.save(fname, ContentFile(data), save=True)
                print(f"  ✓ Saved image for Product #{pid}: {prod.title_en}")
        except Product.DoesNotExist:
            print(f"  ! Product #{pid} not found")

    # 2. ENCYCLOPEDIA PLANTS
    plant_keywords = {
        'Rose': ("rose.jpg", "https://images.unsplash.com/photo-1559563458-527698bf5295?w=800&auto=format&fit=crop&q=80"),
        'Jasmine': ("jasmine.jpg", "https://images.unsplash.com/photo-1600857544200-b2f666a9a2ec?w=800&auto=format&fit=crop&q=80"),
        'Money Plant': ("money_plant.jpg", "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=800&auto=format&fit=crop&q=80"),
        'Lemon': ("lemon.jpg", "https://images.unsplash.com/photo-1534856966150-c832f7b7f0ac?w=800&auto=format&fit=crop&q=80"),
        'Neem': ("neem.jpg", "https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=800&auto=format&fit=crop&q=80"),
        'Guava': ("guava.jpg", "https://images.unsplash.com/photo-1536511135899-73e4a3b811ef?w=800&auto=format&fit=crop&q=80"),
        'Tomato': ("tomato.jpg", "https://images.unsplash.com/photo-1592841200221-a6898f307baa?w=800&auto=format&fit=crop&q=80"),
        'Mint': ("mint.jpg", "https://images.unsplash.com/photo-1628556270448-4d4e4148e1b1?w=800&auto=format&fit=crop&q=80"),
        'Coriander': ("coriander.jpg", "https://images.unsplash.com/photo-1599940824399-b87987ceb72a?w=800&auto=format&fit=crop&q=80"),
        'Spinach': ("spinach.jpg", "https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=800&auto=format&fit=crop&q=80"),
        'Aloe': ("aloe.jpg", "https://images.unsplash.com/photo-1596547609652-9cf5d8d76921?w=800&auto=format&fit=crop&q=80"),
        'Bougainvillea': ("bougainvillea.jpg", "https://images.unsplash.com/photo-1582794543139-8ac9cb0f7b11?w=800&auto=format&fit=crop&q=80"),
        'Marigold': ("marigold.jpg", "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=800&auto=format&fit=crop&q=80"),
        'Snake Plant': ("snake_plant.jpg", "https://images.unsplash.com/photo-1593482892290-f54927ae1bf6?w=800&auto=format&fit=crop&q=80"),
        'Chili': ("chili.jpg", "https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=800&auto=format&fit=crop&q=80"),
        'Fig': ("fig.jpg", "https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?w=800&auto=format&fit=crop&q=80"),
        'Pomegranate': ("pomegranate.jpg", "https://images.unsplash.com/photo-1541344999736-83eca872f242?w=800&auto=format&fit=crop&q=80"),
    }

    print("\n--- [2/5] Updating Encyclopedia Plants ---")
    cached_plant_data = {}
    for kw, (fname, url) in plant_keywords.items():
        data = download_image(url)
        if data:
            cached_plant_data[kw] = (fname, data)

    for plant in Plant.objects.all():
        for kw, (fname, data) in cached_plant_data.items():
            if kw.lower() in plant.name_en.lower() or kw.lower() in plant.name_ur.lower():
                plant.image.save(f"plant_{plant.id}_{fname}", ContentFile(data), save=True)
                print(f"  ✓ Assigned photo to Plant #{plant.id}: {plant.name_en}")
                break

    # 3. SAMPLE LEAF PHOTOS FOR AI DOCTOR DIAGNOSE
    sample_dir = os.path.join('media', 'sample_leaves')
    os.makedirs(sample_dir, exist_ok=True)
    sample_leaves = {
        "rose_black_spot.jpg": "https://images.unsplash.com/photo-1597848212624-a19eb35e2651?w=800&auto=format&fit=crop&q=80",
        "citrus_leaf_curl.jpg": "https://images.unsplash.com/photo-1587334274328-64186a80aeee?w=800&auto=format&fit=crop&q=80",
        "tomato_early_blight.jpg": "https://images.unsplash.com/photo-1592417817098-8f3d69109853?w=800&auto=format&fit=crop&q=80",
        "whitefly_pest.jpg": "https://images.unsplash.com/photo-1591857177580-dc82b9ac4e1e?w=800&auto=format&fit=crop&q=80",
        "powdery_mildew.jpg": "https://images.unsplash.com/photo-1599598425947-320d36bc5b01?w=800&auto=format&fit=crop&q=80",
    }
    print("\n--- [3/5] Saving Sample Leaf Photos for AI Doctor Testing ---")
    for sname, surl in sample_leaves.items():
        sdata = download_image(surl)
        if sdata:
            spath = os.path.join(sample_dir, sname)
            with open(spath, 'wb') as f:
                f.write(sdata)
            print(f"  ✓ Saved test leaf: {spath} ({len(sdata)} bytes)")

    # 4. USER PLANTS (AHMED'S GARDEN)
    print("\n--- [4/5] Updating User Plants & Growth Timeline ---")
    for up in UserPlant.objects.all():
        if 'rose' in up.nickname.lower() or 'گلاب' in up.nickname:
            if 'Rose' in cached_plant_data:
                up.primary_photo.save(f"user_rose_{up.id}.jpg", ContentFile(cached_plant_data['Rose'][1]), save=True)
                print(f"  ✓ Saved photo for UserPlant: {up.nickname}")
        elif 'lemon' in up.nickname.lower() or 'لیموں' in up.nickname:
            if 'Lemon' in cached_plant_data:
                up.primary_photo.save(f"user_lemon_{up.id}.jpg", ContentFile(cached_plant_data['Lemon'][1]), save=True)
                print(f"  ✓ Saved photo for UserPlant: {up.nickname}")

    # Add growth timeline photos
    for up in UserPlant.objects.all():
        if not up.health_photos.exists() and up.primary_photo:
            PlantPhoto.objects.create(
                user_plant=up,
                photo=up.primary_photo,
                note="Healthy green growth after organic compost application"
            )
            print(f"  ✓ Created timeline entry for {up.nickname}")

    # 5. COMMUNITY GROUP & USER AVATARS
    print("\n--- [5/5] Community Group Cover & Avatars ---")
    group = Group.objects.first()
    if group and not group.image:
        gdata = download_image("https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=800&auto=format&fit=crop&q=80")
        if gdata:
            group.image.save("lahore_group.jpg", ContentFile(gdata), save=True)
            print(f"  ✓ Saved cover image for group: {group.name_en}")

    # Avatars
    avatar_urls = {
        'ahmed': "https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=300&auto=format&fit=crop&q=80",
        'ali_mali': "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=300&auto=format&fit=crop&q=80",
        'bilal_nursery': "https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=300&auto=format&fit=crop&q=80",
    }
    for uname, aurl in avatar_urls.items():
        try:
            u = User.objects.get(username=uname)
            if not u.avatar:
                adata = download_image(aurl)
                if adata:
                    u.avatar.save(f"{uname}_avatar.jpg", ContentFile(adata), save=True)
                    print(f"  ✓ Saved avatar for user: {uname}")
        except User.DoesNotExist:
            pass

    print("\n==================================================")
    print("ALL REAL BOTANICAL IMAGES POPULATED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run()
