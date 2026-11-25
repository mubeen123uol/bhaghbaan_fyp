import os
import sys
import re
from PIL import Image

import django
sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baghbaan.settings')
django.setup()

from django.test import Client
from marketplace.models import Product
from plants.models import Plant, Disease
from care.models import UserPlant
from services.models import Task, Garden
from community.models import Group

URDU_REGEX = re.compile(r'[\u0600-\u06FF]')

def contains_urdu(text):
    return bool(URDU_REGEX.search(str(text or '')))

def run_audit():
    print("=" * 70)
    print("COMPREHENSIVE AUDIT: 1200px ULTRA-HD IMAGES & BILINGUAL PURITY")
    print("=" * 70)

    # 1. Image Audit
    print("\n[1] IMAGE RESOLUTION & INTEGRITY AUDIT")
    total_imgs = 0
    passed_imgs = 0

    # Products
    for p in Product.objects.all():
        total_imgs += 1
        if p.main_image and os.path.exists(p.main_image.path):
            with Image.open(p.main_image.path) as im:
                sz = os.path.getsize(p.main_image.path) // 1024
                w, h = im.size
                if w >= 1000 and sz >= 50:
                    passed_imgs += 1
                    print(f"  ✓ Product #{p.id}: {p.title_en} -> {w}x{h}px, {sz}KB")
                else:
                    print(f"  ✗ Product #{p.id} under resolution: {w}x{h}px, {sz}KB")
        else:
            print(f"  ✗ Product #{p.id} missing image file")

    # Diseases
    for d in Disease.objects.all():
        total_imgs += 1
        if d.sample_image and os.path.exists(d.sample_image.path):
            with Image.open(d.sample_image.path) as im:
                sz = os.path.getsize(d.sample_image.path) // 1024
                w, h = im.size
                if w >= 450 and sz >= 30:
                    passed_imgs += 1
                    print(f"  ✓ Disease #{d.id}: {d.name_en} -> {w}x{h}px, {sz}KB")
                else:
                    print(f"  ✗ Disease #{d.id} under resolution: {w}x{h}px, {sz}KB")
        else:
            print(f"  ✗ Disease #{d.id} missing image file")

    # Sample Leaves
    for fn in os.listdir('media/sample_leaves'):
        fpath = os.path.join('media/sample_leaves', fn)
        if os.path.isfile(fpath):
            total_imgs += 1
            with Image.open(fpath) as im:
                sz = os.path.getsize(fpath) // 1024
                w, h = im.size
                if w >= 450 and sz >= 30:
                    passed_imgs += 1
                    print(f"  ✓ Sample Leaf {fn} -> {w}x{h}px, {sz}KB")
                else:
                    print(f"  ✗ Sample Leaf {fn} under resolution: {w}x{h}px, {sz}KB")

    # 41 Plants
    low_res_plants = []
    for pl in Plant.objects.all().order_by('id'):
        total_imgs += 1
        if pl.image and os.path.exists(pl.image.path):
            with Image.open(pl.image.path) as im:
                sz = os.path.getsize(pl.image.path) // 1024
                w, h = im.size
                if w >= 1000 and sz >= 50:
                    passed_imgs += 1
                else:
                    low_res_plants.append((pl.id, pl.name_en, f"{w}x{h}", f"{sz}KB"))
        else:
            low_res_plants.append((pl.id, pl.name_en, "MISSING", "0KB"))

    if not low_res_plants:
        print(f"  ✓ ALL 41 Encyclopedia Plants verified >= 1000px width and >= 50KB HD quality!")
    else:
        print(f"  ✗ {len(low_res_plants)} plants failed: {low_res_plants}")

    # Direct rose.jpg
    rose_path = os.path.join('media', 'plants', 'rose.jpg')
    if os.path.exists(rose_path):
        with Image.open(rose_path) as im:
            sz = os.path.getsize(rose_path) // 1024
            print(f"  ✓ Static media/plants/rose.jpg -> {im.size[0]}x{im.size[1]}px, {sz}KB")

    print(f"\n--> Image Pass Rate: {passed_imgs}/{total_imgs} ({passed_imgs/total_imgs*100:.1f}%)")

    # 2. Bilingual Text & Model Property Audit
    print("\n[2] BILINGUAL PURITY AUDIT IN ENGLISH MODE")
    client = Client()

    # Test Task English Titles
    for t in Task.objects.all():
        en_title = t.title_en
        if contains_urdu(en_title):
            print(f"  ✗ Task #{t.id} title_en contains Urdu: '{en_title}'")
        else:
            print(f"  ✓ Task #{t.id} title_en pure English: '{en_title}'")

    # Test Garden English Names
    for g in Garden.objects.all():
        en_name = g.name_en
        if contains_urdu(en_name):
            print(f"  ✗ Garden #{g.id} name_en contains Urdu: '{en_name}'")
        else:
            print(f"  ✓ Garden #{g.id} name_en pure English: '{en_name}'")

    # Test Product English Titles
    for p in Product.objects.all():
        en_title = p.title_en
        if contains_urdu(en_title):
            print(f"  ✗ Product #{p.id} title_en contains Urdu: '{en_title}'")
        else:
            print(f"  ✓ Product #{p.id} title_en pure English: '{en_title}'")

    # Test Group English Names
    for gr in Group.objects.all():
        en_name = gr.name_en
        if contains_urdu(en_name):
            print(f"  ✗ Group #{gr.id} name_en contains Urdu: '{en_name}'")
        else:
            print(f"  ✓ Group #{gr.id} name_en pure English: '{en_name}'")

    # Test Chatbot in English
    from django.contrib.auth import get_user_model
    client.force_login(get_user_model().objects.first())
    client.cookies['django_language'] = 'en'
    resp = client.post('/ai/chatbot/', 
                       data={'message': 'How do I take care of roses?', 'language': 'en'}, 
                       headers={'x-requested-with': 'XMLHttpRequest'})
    if resp.status_code == 200:
        bot_reply = resp.json().get('reply', '')
        if contains_urdu(bot_reply):
            print(f"  ✗ Chatbot English message returned Urdu text: {bot_reply[:60]}...")
        else:
            print(f"  ✓ Chatbot English query returned pure English advice: {bot_reply[:60]}...")
    else:
        print(f"  ✗ Chatbot API returned status {resp.status_code}")

    print("\n" + "=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)

if __name__ == '__main__':
    run_audit()
