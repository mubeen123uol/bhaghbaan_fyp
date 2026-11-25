from django.db import models
from django.conf import settings

class UserPlant(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_plants')
    plant_template = models.ForeignKey('plants.Plant', on_delete=models.SET_NULL, null=True, blank=True, related_name='user_instances')
    nickname = models.CharField(max_length=120)
    garden = models.ForeignKey('services.Garden', on_delete=models.SET_NULL, null=True, blank=True, related_name='plants')
    location_description = models.CharField(max_length=120, default='Balcony / چھت')
    is_indoor = models.BooleanField(default=False)
    primary_photo = models.ImageField(upload_to='user_plants/', null=True, blank=True)
    watering_interval_days = models.PositiveIntegerField(default=2)
    last_watered_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def nickname_en(self):
        nick_map = {
            'صحن کا سرخ گلاب': 'Courtyard Red Rose',
            'چھت کا کاغذی لیموں': 'Rooftop Kaghzi Lemon',
        }
        stripped = self.nickname.strip()
        if stripped in nick_map:
            return nick_map[stripped]
        if self.plant_template and self.plant_template.name_en:
            return f"{self.plant_template.name_en}"
        return self.nickname

    @property
    def nickname_ur(self):
        return self.nickname

    @property
    def location_description_en(self):
        loc_map = {
            'مرکزی صحن - مٹی کا 18 انچ کا غملا': 'Main Courtyard - 18" Terracotta Clay Pot',
            'چھت کے کونے میں دھوپ والی جگہ': 'Rooftop Corner - Full Sun Exposure',
            'چھت / بالکونی': 'Rooftop / Balcony',
        }
        stripped = self.location_description.strip()
        return loc_map.get(stripped, self.location_description)

    def __str__(self):
        return f"{self.nickname} ({self.user.username})"


class CareTask(models.Model):
    TASK_TYPES = (
        ('WATER', 'Watering / پانی دیں 💧'),
        ('FERTILIZE', 'Fertilizing / کھاد ڈالیں 🧪'),
        ('PRUNE', 'Pruning / کانٹ چھانٹ ✂️'),
        ('FROST_PROTECT', 'Frost Protection / سردی سے بچاؤ ❄️'),
    )
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('SKIPPED', 'Skipped'),
        ('POSTPONED', 'Postponed for Weather'),
    )

    user_plant = models.ForeignKey(UserPlant, on_delete=models.CASCADE, related_name='care_tasks')
    task_type = models.CharField(max_length=20, choices=TASK_TYPES, default='WATER')
    scheduled_date = models.DateField(db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    weather_note = models.CharField(max_length=255, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    reminder_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['scheduled_date', 'status']

    @property
    def task_type_en(self):
        type_map = {
            'WATER': 'Watering 💧',
            'FERTILIZE': 'Fertilizing 🧪',
            'PRUNE': 'Pruning ✂️',
            'FROST_PROTECT': 'Frost Protection ❄️',
        }
        return type_map.get(self.task_type, self.task_type)

    @property
    def task_type_ur(self):
        type_map = {
            'WATER': 'پانی دیں 💧',
            'FERTILIZE': 'کھاد ڈالیں 🧪',
            'PRUNE': 'کانٹ چھانٹ ✂️',
            'FROST_PROTECT': 'سردی سے بچاؤ ❄️',
        }
        return type_map.get(self.task_type, self.task_type)

    @property
    def status_en(self):
        stat_map = {
            'PENDING': 'Pending',
            'COMPLETED': 'Completed',
            'SKIPPED': 'Skipped',
            'POSTPONED': 'Postponed for Rain',
        }
        return stat_map.get(self.status, self.status)

    @property
    def status_ur(self):
        stat_map = {
            'PENDING': 'زیرِ التواء',
            'COMPLETED': 'مکمل شدہ',
            'SKIPPED': 'چھوڑ دیا گیا',
            'POSTPONED': 'موسم کی وجہ سے مؤخر',
        }
        return stat_map.get(self.status, self.status)

    @property
    def weather_note_en(self):
        if not self.weather_note:
            return ""
        if 'بارش' in self.weather_note or 'rain' in self.weather_note.lower():
            return "Rain forecast (>=5mm): outdoor watering postponed automatically"
        return self.weather_note

    def __str__(self):
        return f"{self.get_task_type_display()} for {self.user_plant.nickname} on {self.scheduled_date}"


class PlantPhoto(models.Model):
    user_plant = models.ForeignKey(UserPlant, on_delete=models.CASCADE, related_name='health_photos')
    photo = models.ImageField(upload_to='plant_timeline/%Y/%m/')
    note = models.TextField(blank=True)
    taken_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-taken_at']

    def __str__(self):
        return f"Timeline Photo #{self.id} for {self.user_plant.nickname}"


class WeatherSnapshot(models.Model):
    city = models.CharField(max_length=100, db_index=True)
    temperature = models.FloatField()
    precipitation_mm = models.FloatField(default=0.0)
    forecast_24h_rain_mm = models.FloatField(default=0.0)
    weather_condition = models.CharField(max_length=100)
    fetched_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.city}: {self.temperature}°C, {self.weather_condition} ({self.fetched_at:%Y-%m-%d %H:%M})"
