from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Plant, Disease

def plant_list(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()
    
    plants = Plant.objects.all()
    if query:
        plants = plants.filter(
            Q(name_en__icontains=query) |
            Q(name_ur__icontains=query) |
            Q(name_roman__icontains=query) |
            Q(scientific_name__icontains=query)
        )
    if category:
        plants = plants.filter(category=category)

    categories = Plant.CATEGORY_CHOICES
    return render(request, 'plants/plant_list.html', {
        'plants': plants,
        'categories': categories,
        'query': query,
        'selected_category': category,
    })

def plant_detail(request, pk):
    plant = get_object_or_404(Plant, pk=pk)
    diseases = plant.diseases.all()
    return render(request, 'plants/plant_detail.html', {
        'plant': plant,
        'diseases': diseases,
    })
