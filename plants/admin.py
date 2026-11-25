from django.contrib import admin
from .models import Plant, Disease, Treatment

class TreatmentInline(admin.StackedInline):
    model = Treatment
    extra = 1

@admin.register(Plant)
class PlantAdmin(admin.ModelAdmin):
    list_display = ('name_ur', 'name_en', 'scientific_name', 'category', 'watering_interval_days', 'is_indoor_suitable')
    list_filter = ('category', 'is_indoor_suitable', 'sunlight_requirement')
    search_fields = ('name_en', 'name_ur', 'name_roman', 'scientific_name')

@admin.register(Disease)
class DiseaseAdmin(admin.ModelAdmin):
    list_display = ('name_ur', 'name_en', 'severity_level', 'scientific_name')
    list_filter = ('severity_level',)
    search_fields = ('name_en', 'name_ur', 'symptoms_en', 'symptoms_ur')
    inlines = [TreatmentInline]

@admin.register(Treatment)
class TreatmentAdmin(admin.ModelAdmin):
    list_display = ('title_ur', 'disease', 'treatment_type')
    list_filter = ('treatment_type',)
    search_fields = ('title_en', 'title_ur', 'instructions_ur')
