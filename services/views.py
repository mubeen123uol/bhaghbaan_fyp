from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Q
from decimal import Decimal
from .models import Garden, GardenMember, Task, TaskReport, Expense
from .services import GardenService
from accounts.models import User

@login_required
def garden_list(request):
    user = request.user
    if user.role in ['GARDENER', 'SUPERVISOR']:
        gardens = Garden.objects.filter(members__user=user).distinct()
    else:
        gardens = Garden.objects.filter(owner=user)
    return render(request, 'services/garden_list.html', {'gardens': gardens})

@login_required
def garden_create(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        address = request.POST.get('location_address')
        city = request.POST.get('city', request.user.city)
        budget = Decimal(request.POST.get('total_budget', '0.00'))

        garden = Garden.objects.create(
            owner=request.user,
            name=name,
            location_address=address,
            city=city,
            total_budget=budget
        )
        messages.success(request, f"باغ '{name}' کامیابی سے بن گیا!")
        return redirect('garden-detail', pk=garden.pk)

    return render(request, 'services/garden_create.html')

@login_required
def garden_detail(request, pk):
    user = request.user
    garden = get_object_or_404(Garden, pk=pk)
    
    # Permission check: must be owner or member
    is_member = garden.owner == user or garden.members.filter(user=user).exists()
    if not is_member and not user.is_superuser:
        messages.error(request, "آپ کو اس باغ تک رسائی کی اجازت نہیں ہے۔")
        return redirect('garden-list')

    tasks = garden.tasks.all()
    expenses = garden.expenses.all()
    members = garden.members.all()
    available_gardeners = User.objects.filter(role__in=['GARDENER', 'SUPERVISOR'])

    return render(request, 'services/garden_detail.html', {
        'garden': garden,
        'tasks': tasks,
        'expenses': expenses,
        'members': members,
        'available_gardeners': available_gardeners,
    })

@login_required
def task_create(request, garden_id):
    garden = get_object_or_404(Garden, id=garden_id)
    if garden.owner != request.user and request.user.role != 'SUPERVISOR':
        messages.error(request, "صرف باغ کا مالک یا نگران نیا کام تفویض کر سکتا ہے۔")
        return redirect('garden-detail', pk=garden.pk)

    if request.method == 'POST':
        title = request.POST.get('title')
        desc = request.POST.get('description')
        due = request.POST.get('due_date') or None
        assignee_id = request.POST.get('assigned_to')

        assignee = User.objects.filter(id=assignee_id).first() if assignee_id else None
        state = 'ASSIGNED' if assignee else 'CREATED'

        Task.objects.create(
            garden=garden,
            title=title,
            description=desc,
            due_date=due,
            assigned_to=assignee,
            created_by=request.user,
            state=state
        )
        messages.success(request, "نیا ٹاسک کامیابی سے تفویض کر دیا گیا ہے۔")
        return redirect('garden-detail', pk=garden.pk)

    members = garden.members.all()
    return render(request, 'services/task_create.html', {'garden': garden, 'members': members})

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    user = request.user

    # Handle 5-State Transitions
    if request.method == 'POST':
        action = request.POST.get('action') # 'start', 'submit_report', 'approve', 'reject'
        notes = request.POST.get('notes', '')
        photo = request.FILES.get('photo_proof')

        try:
            if action == 'start' and task.state == 'ASSIGNED':
                GardenService.transition_task_state(task, 'IN_PROGRESS', user)
                messages.success(request, "کام شروع کر دیا گیا ہے (In Progress)۔")
            elif action == 'submit_report' and task.state == 'IN_PROGRESS':
                GardenService.transition_task_state(task, 'SUBMITTED', user, notes=notes, photo_proof=photo)
                messages.success(request, "رپورٹ جمع کرا دی گئی ہے (Submitted)۔ نگران کی منظوری کا انتظار ہے۔")
            elif action == 'approve' and task.state == 'SUBMITTED':
                GardenService.transition_task_state(task, 'APPROVED', user, notes=notes)
                messages.success(request, "کام منظور کر لیا گیا ہے (Approved & Completed)۔")
            elif action == 'reject' and task.state == 'SUBMITTED':
                GardenService.transition_task_state(task, 'IN_PROGRESS', user, notes=notes)
                messages.warning(request, "رپورٹ میں بہتری کے لیے کام مالی کو واپس بھیج دیا گیا ہے۔")
        except ValidationError as ve:
            messages.error(request, str(ve))

        return redirect('task-detail', pk=task.pk)

    return render(request, 'services/task_detail.html', {'task': task, 'user': user})

@login_required
def add_expense(request, garden_id):
    garden = get_object_or_404(Garden, id=garden_id)
    if request.method == 'POST':
        title = request.POST.get('title')
        cat = request.POST.get('category', 'LABOR')
        amt = Decimal(request.POST.get('amount', '0.00'))
        receipt = request.FILES.get('receipt_photo')
        
        GardenService.record_expense(
            garden=garden,
            title=title,
            category=cat,
            amount=amt,
            user=request.user,
            receipt_photo=receipt
        )
        messages.success(request, f"خرچہ Rs {amt} کامیابی سے رجسٹر ہو گیا ہے۔")
    return redirect('garden-detail', pk=garden.pk)

def gardener_directory(request):
    """Proximity directory to find verified gardeners and supervisors."""
    lat = request.GET.get('lat')
    lng = request.GET.get('lng')
    city = request.GET.get('city', 'Lahore')
    role = request.GET.get('role', '')

    profs = GardenService.find_nearby_professionals(lat, lng, role=role if role else None, city=city)
    return render(request, 'services/gardener_directory.html', {
        'professionals': profs,
        'city': city,
        'selected_role': role,
    })
