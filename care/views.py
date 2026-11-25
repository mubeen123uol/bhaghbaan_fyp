from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import date
from .models import UserPlant, CareTask, PlantPhoto
from .services import CareCalendarService
from plants.models import Plant
from services.models import Garden

@login_required
def my_plants(request):
    plants = UserPlant.objects.filter(user=request.user)
    return render(request, 'care/my_plants.html', {'user_plants': plants})

@login_required
def add_user_plant(request):
    templates = Plant.objects.all()
    user_gardens = Garden.objects.filter(owner=request.user)

    if request.method == 'POST':
        template_id = request.POST.get('plant_template')
        nickname = request.POST.get('nickname')
        garden_id = request.POST.get('garden')
        location = request.POST.get('location_description', 'Balcony')
        is_indoor = request.POST.get('is_indoor') == 'on'
        interval = int(request.POST.get('watering_interval_days', 2))
        photo = request.FILES.get('primary_photo')

        plant_tpl = Plant.objects.filter(id=template_id).first() if template_id else None
        garden = Garden.objects.filter(id=garden_id, owner=request.user).first() if garden_id else None

        up = UserPlant.objects.create(
            user=request.user,
            plant_template=plant_tpl,
            nickname=nickname,
            garden=garden,
            location_description=location,
            is_indoor=is_indoor,
            watering_interval_days=interval,
            primary_photo=photo
        )

        CareCalendarService.generate_care_schedule(up, days=30)
        messages.success(request, f"پودا '{nickname}' کامیابی کے ساتھ آپ کے ڈیجیٹل باغ میں شامل کر دیا گیا!")
        return redirect('user-plant-detail', pk=up.pk)

    return render(request, 'care/add_user_plant.html', {
        'plant_templates': templates,
        'user_gardens': user_gardens,
    })

@login_required
def user_plant_detail(request, pk):
    user_plant = get_object_or_404(UserPlant, pk=pk, user=request.user)
    tasks = user_plant.care_tasks.all()[:15]
    photos = user_plant.health_photos.all()
    return render(request, 'care/user_plant_detail.html', {
        'plant': user_plant,
        'tasks': tasks,
        'photos': photos,
    })

@login_required
def care_calendar_view(request):
    weather = CareCalendarService.fetch_live_weather(request.user.city or 'Lahore')
    CareCalendarService.apply_weather_rules(request.user)
    tasks = CareTask.objects.filter(user_plant__user=request.user).order_by('scheduled_date', 'status')[:30]
    return render(request, 'care/care_calendar.html', {
        'tasks': tasks,
        'weather': weather,
        'today': date.today(),
    })

@login_required
def toggle_task_view(request, task_id):
    task = get_object_or_404(CareTask, id=task_id, user_plant__user=request.user)
    task.status = 'COMPLETED' if task.status != 'COMPLETED' else 'PENDING'
    task.completed_at = timezone.now() if task.status == 'COMPLETED' else None
    task.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'status': task.status, 'task_id': task.id})
    return redirect(request.META.get('HTTP_REFERER', 'care-calendar'))

@login_required
def add_plant_photo_view(request, plant_id):
    user_plant = get_object_or_404(UserPlant, id=plant_id, user=request.user)
    if request.method == 'POST':
        photo = request.FILES.get('photo')
        note = request.POST.get('note', '')
        if photo:
            PlantPhoto.objects.create(user_plant=user_plant, photo=photo, note=note)
            messages.success(request, "ٹائم لائن میں نئی تصویر محفوظ کر لی گئی ہے۔")
    return redirect('user-plant-detail', pk=user_plant.pk)
