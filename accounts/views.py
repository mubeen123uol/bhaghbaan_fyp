from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import FileResponse, Http404
from django.utils.translation import gettext as _
from .models import User, SellerProfile
from care.models import UserPlant, CareTask
from care.services import CareCalendarService
from services.models import Garden, Task
from ai_doctor.models import Diagnosis
from marketplace.models import Order
from datetime import date

def home(request):
    """Public landing page featuring AI Doctor hero, Pakistani plant showcase, and quick links."""
    weather = CareCalendarService.fetch_live_weather('Lahore')
    from plants.models import Plant
    featured_plants = Plant.objects.all()[:6]
    return render(request, 'home.html', {
        'weather': weather,
        'featured_plants': featured_plants,
    })

@login_required
def dashboard(request):
    """Personalized user dashboard customized for Homeowner, Gardener, Supervisor, or Seller."""
    user = request.user
    today = date.today()
    weather = CareCalendarService.fetch_live_weather(user.city or 'Lahore')

    # Care tasks for Homeowner
    user_plants = UserPlant.objects.filter(user=user)[:5]
    today_tasks = CareTask.objects.filter(user_plant__user=user, scheduled_date=today)
    recent_diagnoses = Diagnosis.objects.filter(user=user)[:4]

    # Services tasks
    if user.role in ['GARDENER', 'SUPERVISOR']:
        assigned_tasks = Task.objects.filter(assigned_to=user).exclude(state='APPROVED')[:5]
        supervised_gardens = Garden.objects.filter(members__user=user)[:4]
    else:
        assigned_tasks = Task.objects.filter(garden__owner=user).exclude(state='APPROVED')[:5]
        supervised_gardens = Garden.objects.filter(owner=user)[:4]

    # Marketplace orders
    if hasattr(user, 'seller_profile'):
        recent_orders = Order.objects.filter(items__seller=user.seller_profile).distinct()[:5]
    else:
        recent_orders = Order.objects.filter(buyer=user)[:5]

    return render(request, 'dashboard.html', {
        'user': user,
        'weather': weather,
        'user_plants': user_plants,
        'today_tasks': today_tasks,
        'recent_diagnoses': recent_diagnoses,
        'assigned_tasks': assigned_tasks,
        'supervised_gardens': supervised_gardens,
        'recent_orders': recent_orders,
    })

def login_view(request):
    """Login with quick test account fill buttons for evaluation convenience."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        u = request.POST.get('username')
        p = request.POST.get('password')
        user = authenticate(request, username=u, password=p)
        if user:
            login(request, user)
            messages.success(request, f"خوش آمدید، {user.first_name or user.username}!")
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "غلط صارف نام یا پاس ورڈ درج کیا گیا ہے۔ (Invalid credentials)")

    return render(request, 'accounts/login.html')

def register_view(request):
    """Registration for Homeowner, Gardener, or Supervisor."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        role = request.POST.get('role', 'HOMEOWNER')
        phone = request.POST.get('phone', '')
        city = request.POST.get('city', 'Lahore')
        language = request.POST.get('preferred_language', 'ur')

        if User.objects.filter(username=username).exists():
            messages.error(request, "یہ صارف نام پہلے سے زیر استعمال ہے۔")
        else:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                role=role,
                phone=phone,
                city=city,
                preferred_language=language
            )
            login(request, user)
            messages.success(request, "باغبان اے آئی میں آپ کا اکاؤنٹ کامیابی سے بن گیا ہے!")
            return redirect('dashboard')

    return render(request, 'accounts/register.html')

def logout_view(request):
    logout(request)
    messages.info(request, "آپ لاگ آؤٹ ہو چکے ہیں۔")
    return redirect('home')

@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.phone = request.POST.get('phone', user.phone)
        user.city = request.POST.get('city', user.city)
        user.preferred_language = request.POST.get('preferred_language', user.preferred_language)
        user.bio = request.POST.get('bio', user.bio)
        if request.FILES.get('avatar'):
            user.avatar = request.FILES.get('avatar')
        user.save()
        messages.success(request, "پروفائل کامیابی سے اپڈیٹ ہو گئی ہے۔")
        return redirect('profile')

    return render(request, 'accounts/profile.html', {'user': user})

def set_language_view(request, lang_code):
    """Switch language between Urdu ('ur') and English ('en')."""
    if lang_code in ['ur', 'en', 'ur_ro']:
        request.session['django_language'] = lang_code
        if request.user.is_authenticated:
            request.user.preferred_language = lang_code
            request.user.save()
    next_url = request.META.get('HTTP_REFERER', 'home')
    return redirect(next_url)

@login_required
def seller_apply_view(request):
    if hasattr(request.user, 'seller_profile'):
        messages.info(request, "آپ پہلے ہی نرسری سیلر کے طور پر رجسٹرڈ ہیں۔")
        return redirect('seller-dashboard')

    if request.method == 'POST':
        business_name = request.POST.get('business_name')
        cnic = request.POST.get('cnic_number')
        address = request.POST.get('shop_address')
        phone = request.POST.get('contact_phone')

        SellerProfile.objects.create(
            user=request.user,
            business_name=business_name,
            cnic_number=cnic,
            shop_address=address,
            contact_phone=phone,
            verification_status='PENDING'
        )
        request.user.role = 'SELLER'
        request.user.save()
        messages.success(request, "سیلر درخواست ایڈمن کو ارسال کر دی گئی ہے۔ منظوری کے بعد پروڈکٹس لائیو ہوں گی۔")
        return redirect('dashboard')

    return render(request, 'accounts/seller_apply.html')


def download_apk_view(request):
    """Serve the signed Baghbaan AI Android APK for direct mobile download."""
    apk_path = settings.BASE_DIR / 'static' / 'releases' / 'baghbaan-ai.apk'
    if not apk_path.exists():
        raise Http404("Android APK is not available.")
    response = FileResponse(
        open(apk_path, 'rb'),
        as_attachment=True,
        filename='baghbaan-ai.apk',
        content_type='application/vnd.android.package-archive',
    )
    response['Content-Length'] = apk_path.stat().st_size
    return response
