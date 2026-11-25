from django.contrib import admin
from .models import UserPlant, CareTask, PlantPhoto, WeatherSnapshot

@admin.register(UserPlant)
class UserPlantAdmin(admin.ModelAdmin):
    list_display = ('nickname', 'user', 'plant_template', 'location_description', 'watering_interval_days', 'is_indoor', 'created_at')
    list_filter = ('is_indoor',)
    search_fields = ('nickname', 'user__username')

@admin.register(CareTask)
class CareTaskAdmin(admin.ModelAdmin):
    list_display = ('user_plant', 'task_type', 'scheduled_date', 'status', 'weather_note', 'reminder_sent')
    list_filter = ('task_type', 'status', 'reminder_sent')
    search_fields = ('user_plant__nickname', 'weather_note')

@admin.register(PlantPhoto)
class PlantPhotoAdmin(admin.ModelAdmin):
    list_display = ('id', 'user_plant', 'note', 'taken_at')

@admin.register(WeatherSnapshot)
class WeatherSnapshotAdmin(admin.ModelAdmin):
    list_display = ('city', 'temperature', 'precipitation_mm', 'forecast_24h_rain_mm', 'weather_condition', 'fetched_at')
