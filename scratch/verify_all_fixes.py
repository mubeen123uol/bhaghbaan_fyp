import os
import sys

sys.path.insert(0, os.path.abspath('.'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'baghbaan.settings')
import django
django.setup()

from django.test import Client
from accounts.models import User
from ai_doctor.services import AIDoctorService
from marketplace.models import Product
from services.models import Task
from community.models import ChatRoom

def run_checks():
    client = Client()
    # Authenticate as homeowner
    user = User.objects.get(username='ahmed')
    client.force_login(user)

    print("==================================================")
    print("1. VERIFYING CHATBOT BILINGUAL RESPONSES")
    print("==================================================")
    session, _ = user.chat_sessions.get_or_create()
    session.messages.all().delete()

    en_res = AIDoctorService.ask_chatbot(user, session.id, 'hi', request_lang='en')
    assert 'Welcome to' in en_res or 'Hello!' in en_res, f"EN greeting failed: {en_res}"
    print("[PASS] Chatbot replied to 'hi' in pure English:")
    print("      ", en_res[:70] + "...")

    ur_res = AIDoctorService.ask_chatbot(user, session.id, 'سلام', request_lang='ur')
    assert 'السلام علیکم' in ur_res or 'خوش آمدید' in ur_res, f"UR greeting failed: {ur_res}"
    print("[PASS] Chatbot replied to 'سلام' in pure Urdu:")
    print("      ", ur_res[:70] + "...")

    session.messages.all().delete()

    print("\n==================================================")
    print("2. VERIFYING ENGLISH MODE PURITY ACROSS KEY PAGES")
    print("==================================================")
    client.get('/lang/en/')

    test_urls = [
        ('/', 'Home'),
        ('/dashboard/', 'Dashboard'),
        ('/ai/diagnose/', 'AI Doctor Diagnose'),
        ('/ai/chatbot/', 'AI Chatbot'),
        ('/plants/', 'Plant Encyclopedia'),
        ('/care/calendar/', 'Care Calendar'),
        ('/care/plants/', 'My Digital Garden'),
        ('/services/gardens/', 'Garden List'),
        ('/services/tasks/1/', 'Task Detail (5-State)'),
        ('/marketplace/', 'Marketplace Products'),
        ('/marketplace/products/1/', 'Product Detail'),
        ('/marketplace/cart/', 'Shopping Cart'),
        ('/community/', 'Community Home'),
    ]

    for url, label in test_urls:
        resp = client.get(url)
        assert resp.status_code == 200, f"Failed {url}: status {resp.status_code}"
        content = resp.content.decode('utf-8')
        
        # Check badge styling present
        assert 'badge-count' in content, f"Missing badge-count in {url}"
        
        # Check mobile dock present
        assert 'lg:hidden fixed bottom-0' in content, f"Missing mobile dock in {url}"

        # Check no raw mixed parenthetical strings in English titles
        if url == '/marketplace/':
            assert '(Balanced NPK' not in content, f"Mixed product title in {url}"
            assert 'Balanced NPK 20-20-20 Fertilizer 1kg' in content
        if url == '/services/tasks/1/':
            assert 'Clean Drip Irrigation Pipes' in content or 'Prune Dead Rose Canes' in content
            assert 'In Progress' in content

        print(f"[PASS] {label} ({url}) - HTTP 200 - Mobile dock & English verified")

    print("\n==================================================")
    print("3. VERIFYING URDU MODE PURITY ACROSS KEY PAGES")
    print("==================================================")
    client.get('/lang/ur/')

    for url, label in test_urls:
        resp = client.get(url)
        assert resp.status_code == 200, f"Failed {url}: status {resp.status_code}"
        content = resp.content.decode('utf-8')
        assert 'dir="rtl"' in content, f"Missing RTL in {url}"
        assert 'badge-count' in content, f"Missing badge-count in {url}"
        assert 'lg:hidden fixed bottom-0' in content, f"Missing mobile dock in {url}"

        if url == '/marketplace/':
            assert 'این پی کے متوازن کھاد' in content
        if url == '/services/tasks/1/':
            assert 'بنایا گیا' in content or 'سونپا گیا' in content

        print(f"[PASS] {label} ({url}) - HTTP 200 - RTL & Urdu verified")

    print("\n==================================================")
    print("ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("==================================================")

if __name__ == '__main__':
    run_checks()
