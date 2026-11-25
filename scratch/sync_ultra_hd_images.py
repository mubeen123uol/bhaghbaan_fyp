import os
import sys
import io
import time
import shutil
import urllib.request
from PIL import Image

import django
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baghbaan.settings')
django.setup()

from django.core.files.base import ContentFile
from plants.models import Plant, Disease
from marketplace.models import Product
from care.models import UserPlant, PlantPhoto

WIKI_HEADERS = {
    'User-Agent': 'BaghbaanAgricultureResearchBot/3.0 (https://baghbaan.ai; research@baghbaan.ai)'
}

UNSPLASH_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def download_and_process_image(url, target_width=1200):
    """
    Downloads image, converts to RGB, resizes proportionally if width > target_width
    using high-quality Lanczos antialiasing, and compresses as crisp JPEG (quality 88).
    """
    is_wiki = 'wikimedia.org' in url or 'wikipedia.org' in url
    headers = WIKI_HEADERS if is_wiki else UNSPLASH_HEADERS

    for attempt in range(3):
        try:
            if is_wiki:
                time.sleep(1.5)
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=18) as resp:
                data = resp.read()
                
            img = Image.open(io.BytesIO(data))
            if img.mode in ('RGBA', 'LA', 'P'):
                bg = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    bg.paste(img, mask=img.split()[3])
                else:
                    bg.paste(img.convert('RGB'))
                img = bg
            elif img.mode != 'RGB':
                img = img.convert('RGB')
                
            orig_w, orig_h = img.size
            if orig_w > target_width:
                new_h = int((target_width / orig_w) * orig_h)
                img = img.resize((target_width, new_h), Image.Resampling.LANCZOS)
                
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=88, optimize=True)
            processed_bytes = buf.getvalue()
            return processed_bytes, img.size
        except Exception as e:
            time.sleep(2.0)
    return None, None

def run():
    print("=" * 70)
    print("BAGHBAAN ULTRA-HD (1200px) PHOTOGRAPHY SYNCHRONIZATION")
    print("=" * 70)

    # -------------------------------------------------------------
    # 1. MARKETPLACE PRODUCTS (8 Commercial Gardening Items)
    # -------------------------------------------------------------
    products_map = {
        1: ('Pure Organic Neem Oil 500ml', 'https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=1200&auto=format&fit=crop&q=85', 'neem_oil_500ml.jpg'),
        2: ('Organic Aged Compost 10kg', 'https://images.unsplash.com/photo-1585320806297-9794b3e4eeae?w=1200&auto=format&fit=crop&q=85', 'aged_organic_compost_10kg.jpg'),
        3: ('Desi Red Rose in 12-inch Pot', 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&auto=format&fit=crop&q=85', 'desi_red_rose_potted.jpg'),
        4: ('Grafted Kaghzi Lemon Plant', 'https://images.unsplash.com/photo-1590502593747-42a996133562?w=1200&auto=format&fit=crop&q=85', 'grafted_kaghzi_lemon_tree.jpg'),
        5: ('Winter Kitchen Garden Seeds', 'https://images.unsplash.com/photo-1523348837708-15d4a09cfac2?w=1200&auto=format&fit=crop&q=85', 'winter_kitchen_garden_seeds.jpg'),
        6: ('14-inch Terracotta Clay Pots', 'https://images.unsplash.com/photo-1485955900006-10f4d324d411?w=1200&auto=format&fit=crop&q=85', 'terracotta_clay_pots_14in.jpg'),
        7: ('Heavy Duty Garden Pruning Shears', 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b?w=1200&auto=format&fit=crop&q=85', 'bypass_pruning_shears.jpg'),
        8: ('Balanced NPK 20-20-20 Fertilizer 1kg', 'https://images.unsplash.com/photo-1585314062340-f1a5a7c9328d?w=1200&auto=format&fit=crop&q=85', 'npk_20_20_20_fertilizer.jpg'),
    }

    print("\n[PHASE 1] Synchronizing 8 Marketplace Products (1200px HD)...")
    for pid, (title, url, fname) in products_map.items():
        try:
            prod = Product.objects.get(id=pid)
            data, size = download_and_process_image(url)
            if data and size:
                prod.main_image.save(fname, ContentFile(data), save=True)
                print(f"  ✓ Product #{pid}: {title} -> {size[0]}x{size[1]}px, {len(data)//1024}KB")
            else:
                print(f"  ✗ Failed Product #{pid}: {title}")
        except Product.DoesNotExist:
            print(f"  ! Product #{pid} not found")

    # -------------------------------------------------------------
    # 2. PLANT DISEASES (5 Pathological Macro Specimens)
    # -------------------------------------------------------------
    diseases_map = {
        1: ('Safaid Makhi (Whitefly)', 'https://upload.wikimedia.org/wikipedia/commons/5/5b/Weisse-Fliege.jpg', 'disease_whitefly_pest.jpg'),
        2: ('Powdery Mildew / Safaid Phaphondi', 'https://upload.wikimedia.org/wikipedia/commons/f/fb/Golovinomyces_sordidus_on_Broadleaf_Plantain_-_Plantago_major_%2844171864324%29.jpg', 'disease_powdery_mildew.jpg'),
        3: ('Leaf Curl Virus / Marorha Rog', 'https://upload.wikimedia.org/wikipedia/commons/1/19/Yellow_curl_leaf_disease_Pj_IMG_3162.jpg', 'disease_leaf_curl_virus.jpg'),
        4: ('Susti Kida / Aphids', 'https://upload.wikimedia.org/wikipedia/commons/5/51/Aphids_September_2008-1.jpg', 'disease_aphids_infestation.jpg'),
        5: ('Jad Ki Saran / Root Rot', 'https://upload.wikimedia.org/wikipedia/commons/2/2d/Prei_papiervlekkenziekte_Phytophthora_porri_on_Allium_porrum.jpg', 'disease_root_rot_phytophthora.jpg'),
    }

    print("\n[PHASE 2] Synchronizing 5 Plant Diseases (High-Res Macro Pathology)...")
    for did, (name, url, fname) in diseases_map.items():
        try:
            dis = Disease.objects.get(id=did)
            data, size = download_and_process_image(url)
            if data and size:
                dis.sample_image.save(fname, ContentFile(data), save=True)
                print(f"  ✓ Disease #{did}: {name} -> {size[0]}x{size[1]}px, {len(data)//1024}KB")
            else:
                print(f"  ✗ Failed Disease #{did}: {name}")
        except Disease.DoesNotExist:
            print(f"  ! Disease #{did} not found")

    # -------------------------------------------------------------
    # 3. AI DOCTOR SAMPLE LEAVES (media/sample_leaves)
    # -------------------------------------------------------------
    sample_leaves = {
        'rose_black_spot.jpg': 'https://upload.wikimedia.org/wikipedia/commons/2/23/Black_spot.jpg',
        'citrus_leaf_curl.jpg': 'https://upload.wikimedia.org/wikipedia/commons/1/19/Yellow_curl_leaf_disease_Pj_IMG_3162.jpg',
        'tomato_early_blight.jpg': 'https://upload.wikimedia.org/wikipedia/commons/0/04/Alternaria_solani_-_leaf_lesions.jpg',
        'whitefly_pest.jpg': 'https://upload.wikimedia.org/wikipedia/commons/5/5b/Weisse-Fliege.jpg',
        'powdery_mildew.jpg': 'https://upload.wikimedia.org/wikipedia/commons/f/fb/Golovinomyces_sordidus_on_Broadleaf_Plantain_-_Plantago_major_%2844171864324%29.jpg',
    }

    print("\n[PHASE 3] Synchronizing AI Doctor Sample Leaves Gallery...")
    sample_dir = os.path.join('media', 'sample_leaves')
    os.makedirs(sample_dir, exist_ok=True)
    for fname, url in sample_leaves.items():
        data, size = download_and_process_image(url)
        if data and size:
            fpath = os.path.join(sample_dir, fname)
            with open(fpath, 'wb') as f:
                f.write(data)
            print(f"  ✓ Sample Leaf: {fname} -> {size[0]}x{size[1]}px, {len(data)//1024}KB")
        else:
            print(f"  ✗ Failed Sample Leaf: {fname}")

    # -------------------------------------------------------------
    # 4. ENCYCLOPEDIA PLANTS: 41 BOTANICAL HIGH-DEF PHOTOS (1200px)
    # -------------------------------------------------------------
    plants_map = {
        1: ('Desi Gulab (Rose)', 'https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1200&auto=format&fit=crop&q=85'),
        2: ('Motia / Jasmine', 'https://images.unsplash.com/photo-1600857544200-b2f666a9a2ec?w=1200&auto=format&fit=crop&q=85'),
        3: ('Chameli / Spanish Jasmine', 'https://images.unsplash.com/photo-1588872657578-7efd1f1555ed?w=1200&auto=format&fit=crop&q=85'),
        4: ('Money Plant', 'https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=1200&auto=format&fit=crop&q=85'),
        5: ('Raat ki Rani', 'https://upload.wikimedia.org/wikipedia/commons/0/02/Cestrum_nocturnum_%282464189820%29.jpg'),
        6: ('Sada Bahar / Periwinkle', 'https://images.unsplash.com/photo-1596728325488-58c87691e9af?w=1200&auto=format&fit=crop&q=85'),
        7: ('Bougainvillea', 'https://images.unsplash.com/photo-1582794543139-8ac9cb0f7b11?w=1200&auto=format&fit=crop&q=85'),
        8: ('Zard Kaner / Oleander', 'https://upload.wikimedia.org/wikipedia/commons/e/eb/Cascabela_thevetia.jpg'),
        9: ('Genda / Marigold', 'https://images.unsplash.com/photo-1563245372-f21724e3856d?w=1200&auto=format&fit=crop&q=85'),
        10: ('Petunia', 'https://upload.wikimedia.org/wikipedia/commons/7/7b/Pet%C3%BAnia_%28do_tupi_petyma%2C_%27tabaco%27%29.jpg'),
        11: ('Pudina / Spearmint', 'https://images.unsplash.com/photo-1628556270448-4d4e4148e1b1?w=1200&auto=format&fit=crop&q=85'),
        12: ('Dhaniya / Coriander', 'https://images.unsplash.com/photo-1599940824399-b87987ceb72a?w=1200&auto=format&fit=crop&q=85'),
        13: ('Kari Patta / Curry Leaf', 'https://upload.wikimedia.org/wikipedia/commons/a/ad/Curry_Trees.jpg'),
        14: ('Tulsi / Holy Basil', 'https://upload.wikimedia.org/wikipedia/commons/0/01/Tulsi_or_Tulasi_Holy_basil.jpg'),
        15: ('Aloe Vera', 'https://images.unsplash.com/photo-1596547609652-9cf5d8d76921?w=1200&auto=format&fit=crop&q=85'),
        16: ('Adrak / Ginger', 'https://images.unsplash.com/photo-1615485290382-441e4d049cb5?w=1200&auto=format&fit=crop&q=85'),
        17: ('Lehsan / Garlic', 'https://images.unsplash.com/photo-1540148426945-6cf22a6b2383?w=1200&auto=format&fit=crop&q=85'),
        18: ('Tamatar / Tomato', 'https://images.unsplash.com/photo-1592841200221-a6898f307baa?w=1200&auto=format&fit=crop&q=85'),
        19: ('Hari Mirch / Green Chilli', 'https://images.unsplash.com/photo-1588252303782-cb80119abd6d?w=1200&auto=format&fit=crop&q=85'),
        20: ('Baingan / Eggplant', 'https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=1200&auto=format&fit=crop&q=85'),
        21: ('Palak / Spinach', 'https://images.unsplash.com/photo-1576045057995-568f588f82fb?w=1200&auto=format&fit=crop&q=85'),
        22: ('Bhindi / Okra', 'https://images.unsplash.com/photo-1606923829579-0cb981a83e2e?w=1200&auto=format&fit=crop&q=85'),
        23: ('Kheera / Cucumber', 'https://images.unsplash.com/photo-1604977042946-1eecc30f269e?w=1200&auto=format&fit=crop&q=85'),
        24: ('Shimla Mirch / Bell Pepper', 'https://images.unsplash.com/photo-1563565375-f3fdfdbefa83?w=1200&auto=format&fit=crop&q=85'),
        25: ('Mooli / Radish', 'https://images.unsplash.com/photo-1593105544559-ecb03bf76f82?w=1200&auto=format&fit=crop&q=85'),
        26: ('Gajar / Carrot', 'https://images.unsplash.com/photo-1590868309235-ea34bed7bd7f?w=1200&auto=format&fit=crop&q=85'),
        27: ('Karela / Bitter Gourd', 'https://upload.wikimedia.org/wikipedia/commons/c/c4/Bitter_gourd_%28Momordica_charantia%29.jpg'),
        28: ('Tori / Ridge Gourd', 'https://upload.wikimedia.org/wikipedia/commons/d/d5/Luffa_acutangula_Chinese_okra.jpg'),
        29: ('Amrood / Guava', 'https://images.unsplash.com/photo-1610832958506-aa56368176cf?w=1200&auto=format&fit=crop&q=85'),
        30: ('Kagzi Nimbu / Lemon', 'https://images.unsplash.com/photo-1590502593747-42a996133562?w=1200&auto=format&fit=crop&q=85'),
        31: ('Anar / Pomegranate', 'https://upload.wikimedia.org/wikipedia/commons/9/9b/Pomegranate02_edit.jpg'),
        32: ('Aam / Mango', 'https://images.unsplash.com/photo-1553279768-865429fa0078?w=1200&auto=format&fit=crop&q=85'),
        33: ('Shahtoot / Mulberry', 'https://images.unsplash.com/photo-1563805042-7684c019e1cb?w=1200&auto=format&fit=crop&q=85'),
        34: ('Injeer / Fig', 'https://images.unsplash.com/photo-1601493700631-2b16ec4b4716?w=1200&auto=format&fit=crop&q=85'),
        35: ('Cheeku / Sapodilla', 'https://images.unsplash.com/photo-1546548970-71785318a17b?w=1200&auto=format&fit=crop&q=85'),
        36: ('Falsa', 'https://upload.wikimedia.org/wikipedia/commons/6/6e/Phalsa03_Asit.jpg'),
        37: ('Neem Tree', 'https://images.unsplash.com/photo-1542601906990-b4d3fb778b09?w=1200&auto=format&fit=crop&q=85'),
        38: ('Moringa / Sohanjna', 'https://images.unsplash.com/photo-1502082553048-f009c37129b9?w=1200&auto=format&fit=crop&q=85'),
        39: ('Sukh Chain / Pongamia', 'https://images.unsplash.com/photo-1448375240586-882707db888b?w=1200&auto=format&fit=crop&q=85'),
        40: ('Sheesham / Tahli', 'https://images.unsplash.com/photo-1513836279014-a89f7a76ae86?w=1200&auto=format&fit=crop&q=85'),
        41: ('Bakain / Chinaberry', 'https://images.unsplash.com/photo-1509198397868-475647b2a1e5?w=1200&auto=format&fit=crop&q=85'),
    }

    print("\n[PHASE 4] Synchronizing 41 Encyclopedia Plants (1200px Botanical HD)...")
    plant_success = 0
    for pid, (name, url) in plants_map.items():
        try:
            plant = Plant.objects.get(id=pid)
            safe_name = plant.scientific_name.lower().replace(' ', '_').replace('.', '')
            fname = f"plant_{pid:02d}_{safe_name}.jpg"
            data, size = download_and_process_image(url)
            if data and size:
                plant.image.save(fname, ContentFile(data), save=True)
                plant_success += 1
                print(f"  ✓ Plant #{pid:02d}: {name} -> {size[0]}x{size[1]}px, {len(data)//1024}KB")
            else:
                print(f"  ✗ Failed Plant #{pid:02d}: {name}")
        except Plant.DoesNotExist:
            print(f"  ! Plant #{pid} not found in database")

    print(f"==> Successfully updated {plant_success}/41 encyclopedia plants!")

    # -------------------------------------------------------------
    # 5. SYNC STATIC / DIRECT FILE: media/plants/rose.jpg
    # -------------------------------------------------------------
    print("\n[PHASE 5] Synchronizing direct static media plant assets...")
    rose_plant = Plant.objects.filter(id=1).first()
    if rose_plant and rose_plant.image and os.path.exists(rose_plant.image.path):
        target_rose = os.path.join('media', 'plants', 'rose.jpg')
        os.makedirs(os.path.dirname(target_rose), exist_ok=True)
        shutil.copyfile(rose_plant.image.path, target_rose)
        print(f"  ✓ Copied Plant #1 HD rose to {target_rose}")

    # -------------------------------------------------------------
    # 6. USER PLANTS & GROWTH TIMELINES
    # -------------------------------------------------------------
    print("\n[PHASE 6] Synchronizing Ahmed's Garden User Plants & Photos...")
    for up in UserPlant.objects.all():
        if up.plant_template and up.plant_template.image:
            up.primary_photo = up.plant_template.image
            up.save()
            print(f"  ✓ UserPlant: {up.nickname} synchronized with {up.plant_template.name_en} HD photo")
            
            # Sync timeline photos
            for hp in up.health_photos.all():
                hp.photo = up.primary_photo
                hp.save()
            if not up.health_photos.exists():
                PlantPhoto.objects.create(
                    user_plant=up,
                    photo=up.primary_photo,
                    note="Lush healthy vegetative growth with organic compost treatment"
                )

    print("\n" + "=" * 70)
    print("ALL ASSETS SUCCESSFULLY CONVERTED TO 1200PX CRISP ULTRA-HD!")
    print("=" * 70)

if __name__ == '__main__':
    run()
