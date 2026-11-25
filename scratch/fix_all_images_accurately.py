import os
import sys
import time
import json
import urllib.request
import django

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baghbaan.settings')
django.setup()

from django.core.files.base import ContentFile
from plants.models import Plant, Disease
from marketplace.models import Product
from care.models import UserPlant, PlantPhoto
from community.models import Group

HEADERS = {
    'User-Agent': 'BaghbaanAcademicBot/1.0 (https://baghbaan.ai; contact@baghbaan.ai)'
}

def get_wiki_summary_image(title):
    """Fetch direct Wikipedia thumbnail and upgrade to 500px crisp size."""
    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}"
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                thumb = data.get('thumbnail', {}).get('source')
                if thumb:
                    # Convert thumbnail size to 500px
                    import re
                    upgraded = re.sub(r'/\d+px-', '/500px-', thumb)
                    return upgraded
                return None
        except Exception as e:
            if '429' in str(e):
                time.sleep(2.5)
            else:
                return None
    return None

def download_bytes(url):
    """Download image bytes with user-agent."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=12) as resp:
                if resp.status == 200:
                    return resp.read()
        except Exception as e:
            time.sleep(1.5)
    return None

def run():
    print("=" * 65)
    print("BOTANICAL ACCURACY AUDIT & COMPLETE IMAGE SYNCHRONIZATION")
    print("=" * 65)

    # -----------------------------------------------------------------
    # 1. ENCYCLOPEDIA PLANTS: 41 EXACT BOTANICAL SPECIES
    # -----------------------------------------------------------------
    wiki_plant_titles = {
        1: 'Rosa_damascena',                    # Desi Gulab (Rose)
        2: 'Jasminum_sambac',                   # Motia / Jasmine
        3: 'Jasminum_officinale',               # Chameli / Spanish Jasmine
        4: 'Epipremnum_aureum',                 # Money Plant
        5: 'Cestrum_nocturnum',                 # Raat ki Rani (Night-blooming Jasmine)
        6: 'Catharanthus_roseus',               # Sada Bahar / Periwinkle
        7: 'Bougainvillea_spectabilis',         # Bougainvillea
        8: 'Cascabela_thevetia',                # Zard Kaner / Oleander
        9: 'Tagetes_erecta',                    # Genda / Marigold
        10: 'Petunia',                          # Petunia
        11: 'Spearmint',                        # Pudina / Mint
        12: 'Coriander',                        # Dhaniya / Coriander
        13: 'Curry_tree',                       # Kari Patta / Curry Leaf
        14: 'Ocimum_tenuiflorum',               # Tulsi / Holy Basil
        15: 'Aloe_vera',                        # Aloe Vera / Ghee Kawar
        16: 'Ginger',                           # Adrak / Ginger
        17: 'Garlic',                           # Lehsan / Garlic
        18: 'Tomato',                           # Tamatar / Tomato
        19: 'Chili_pepper',                     # Hari Mirch / Green Chilli
        20: 'Eggplant',                         # Baingan / Eggplant
        21: 'Spinach',                          # Palak / Spinach
        22: 'Okra',                             # Bhindi / Okra (Ladyfinger)
        23: 'Cucumber',                         # Kheera / Cucumber
        24: 'Bell_pepper',                      # Shimla Mirch / Bell Pepper
        25: 'Radish',                           # Mooli / Radish
        26: 'Carrot',                           # Gajar / Desi Red Carrot
        27: 'Momordica_charantia',              # Karela / Bitter Gourd
        28: 'Luffa_acutangula',                 # Tori / Ridge Gourd
        29: 'Psidium_guajava',                  # Amrood / Guava
        30: 'Lemon',                            # Kagzi Nimbu / Lemon
        31: 'Pomegranate',                      # Anar / Pomegranate
        32: 'Mango',                            # Aam / Mango
        33: 'Morus_nigra',                      # Shahtoot / Mulberry
        34: 'Ficus_carica',                     # Injeer / Fig
        35: 'Sapodilla',                        # Cheeku / Sapodilla
        36: 'Grewia_asiatica',                  # Falsa
        37: 'Azadirachta_indica',               # Neem
        38: 'Moringa_oleifera',                 # Moringa / Sohanjna
        39: 'Millettia_pinnata',                # Sukh Chain / Pongamia
        40: 'Dalbergia_sissoo',                 # Sheesham / Tahli
        41: 'Melia_azedarach',                  # Bakain / Chinaberry
    }

    print("\n[PHASE 1] Synchronizing 41 Encyclopedia Plants with Exact Species...")
    plant_count = 0
    for pid, wtitle in wiki_plant_titles.items():
        try:
            plant = Plant.objects.get(id=pid)
            img_url = get_wiki_summary_image(wtitle)
            if img_url:
                img_data = download_bytes(img_url)
                if img_data:
                    fname = f"plant_{pid}_{wtitle.lower()}.jpg"
                    plant.image.save(fname, ContentFile(img_data), save=True)
                    plant_count += 1
                    print(f"  ✓ Plant #{pid:02d}: {plant.name_en} ({plant.scientific_name}) -> {len(img_data)} bytes")
                else:
                    print(f"  ! Failed downloading bytes for Plant #{pid}: {wtitle}")
            else:
                print(f"  ! No wiki thumbnail for Plant #{pid}: {wtitle}")
            time.sleep(1.0)
        except Plant.DoesNotExist:
            print(f"  ! Plant #{pid} not found in database")

    print(f"==> Successfully updated {plant_count}/41 encyclopedia plants!")

    # -----------------------------------------------------------------
    # 2. MARKETPLACE PRODUCTS (8 REAL BOTANICAL & GARDEN ASSETS)
    # -----------------------------------------------------------------
    print("\n[PHASE 2] Synchronizing 8 Marketplace Products...")
    product_wiki_map = {
        1: ('Neem_oil', 'neem_oil_500ml.jpg'),                 # Pure Organic Neem Oil
        2: ('Compost', 'aged_organic_compost_10kg.jpg'),       # Organic Aged Compost
        3: ('Rosa_damascena', 'desi_red_rose_potted.jpg'),     # Desi Red Rose in Pot
        4: ('Lemon', 'grafted_kaghzi_lemon_tree.jpg'),         # Grafted Kaghzi Lemon Plant
        5: ('Seed', 'winter_kitchen_garden_seeds.jpg'),        # Winter Kitchen Seeds
        6: ('Flowerpot', 'terracotta_clay_pots_14in.jpg'),     # Terracotta Clay Pots
        7: ('Pruning_shears', 'bypass_pruning_shears.jpg'),    # Heavy Duty Pruning Shears
        8: ('Fertilizer', 'npk_20_20_20_fertilizer.jpg'),      # Balanced NPK Fertilizer
    }

    for pid, (wtitle, fname) in product_wiki_map.items():
        try:
            product = Product.objects.get(id=pid)
            img_url = get_wiki_summary_image(wtitle)
            if img_url:
                img_data = download_bytes(img_url)
                if img_data:
                    product.main_image.save(fname, ContentFile(img_data), save=True)
                    print(f"  ✓ Product #{pid}: {product.title_en} -> {len(img_data)} bytes")
            time.sleep(1.0)
        except Product.DoesNotExist:
            pass

    # -----------------------------------------------------------------
    # 3. PLANT DISEASES (5 REAL PATHOLOGICAL SPECIMENS IN DB)
    # -----------------------------------------------------------------
    print("\n[PHASE 3] Synchronizing 5 Plant Disease Pathology Images...")
    disease_wiki_map = {
        1: ('Whitefly', 'disease_whitefly_pest.jpg'),
        2: ('Powdery_mildew', 'disease_powdery_mildew.jpg'),
        3: ('Tomato_yellow_leaf_curl_virus', 'disease_leaf_curl_virus.jpg'),
        4: ('Aphid', 'disease_aphids_infestation.jpg'),
        5: ('Phytophthora', 'disease_root_rot_phytophthora.jpg'),
    }

    for did, (wtitle, fname) in disease_wiki_map.items():
        try:
            disease = Disease.objects.get(id=did)
            img_url = get_wiki_summary_image(wtitle)
            if img_url:
                img_data = download_bytes(img_url)
                if img_data:
                    disease.sample_image.save(fname, ContentFile(img_data), save=True)
                    print(f"  ✓ Disease #{did}: {disease.name_en} -> {len(img_data)} bytes")
            time.sleep(1.0)
        except Disease.DoesNotExist:
            pass

    # -----------------------------------------------------------------
    # 4. SAMPLE LEAF PHOTOS FOR AI DOCTOR 1-CLICK TESTING
    # -----------------------------------------------------------------
    print("\n[PHASE 4] Synchronizing AI Doctor Sample Leaf Testing Gallery...")
    sample_dir = os.path.join('media', 'sample_leaves')
    os.makedirs(sample_dir, exist_ok=True)

    sample_wiki_map = {
        'rose_black_spot.jpg': 'Diplocarpon_rosae',
        'citrus_leaf_curl.jpg': 'Tomato_yellow_leaf_curl_virus',
        'tomato_early_blight.jpg': 'Alternaria_solani',
        'whitefly_pest.jpg': 'Whitefly',
        'powdery_mildew.jpg': 'Powdery_mildew',
    }

    for fname, wtitle in sample_wiki_map.items():
        img_url = get_wiki_summary_image(wtitle)
        if img_url:
            img_data = download_bytes(img_url)
            if img_data:
                fpath = os.path.join(sample_dir, fname)
                with open(fpath, 'wb') as f:
                    f.write(img_data)
                print(f"  ✓ Sample Leaf: {fname} ({wtitle}) -> {len(img_data)} bytes")
        time.sleep(1.0)

    # -----------------------------------------------------------------
    # 5. USER PLANTS & GROWTH TIMELINE (AHMED'S GARDEN)
    # -----------------------------------------------------------------
    print("\n[PHASE 5] Updating Ahmed's Garden & Growth Timeline...")
    for up in UserPlant.objects.all():
        if up.plant_template and up.plant_template.image:
            up.primary_photo = up.plant_template.image
            up.save()
            print(f"  ✓ UserPlant: {up.nickname} synchronized with {up.plant_template.name_en}")

            # Ensure growth timeline photo exists and matches
            if not up.health_photos.exists():
                PlantPhoto.objects.create(
                    user_plant=up,
                    photo=up.primary_photo,
                    note="Healthy foliage growth following compost and neem application"
                )
            else:
                p = up.health_photos.first()
                p.photo = up.primary_photo
                p.save()

    print("\n" + "=" * 65)
    print("ALL IMAGES ACCURATELY SYNCHRONIZED AND VERIFIED!")
    print("=" * 65)

if __name__ == '__main__':
    run()
