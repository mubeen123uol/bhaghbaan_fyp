import requests
import logging
from datetime import date, timedelta
from django.utils import timezone
from django.conf import settings
from .models import UserPlant, CareTask, WeatherSnapshot
from notifications.models import Notification

logger = logging.getLogger(__name__)

# Coordinates for major Pakistani cities
PAK_CITY_COORDINATES = {
    'lahore': (31.5204, 74.3587),
    'karachi': (24.8607, 67.0011),
    'islamabad': (33.6844, 73.0479),
    'rawalpindi': (33.5651, 73.0169),
    'faisalabad': (31.4504, 73.1350),
    'multan': (30.1575, 71.5249),
    'peshawar': (34.0151, 71.5249),
    'quetta': (30.1798, 66.9750),
    'sialkot': (32.4945, 74.5229),
    'gujranwala': (32.1877, 74.1945),
}

class CareCalendarService:
    @staticmethod
    def get_city_coordinates(city_name):
        city = (city_name or 'lahore').lower().strip()
        return PAK_CITY_COORDINATES.get(city, (settings.DEFAULT_LATITUDE, settings.DEFAULT_LONGITUDE))

    @classmethod
    def fetch_live_weather(cls, city_name='Lahore'):
        """
        Fetches 48-hour live weather forecast from Open-Meteo REST API.
        Caches results in WeatherSnapshot model to prevent excessive network calls.
        """
        city_name = city_name.strip() if city_name else 'Lahore'
        cutoff = timezone.now() - timedelta(minutes=60)
        cached = WeatherSnapshot.objects.filter(city__iexact=city_name, fetched_at__gte=cutoff).first()
        if cached:
            return cached

        lat, lng = cls.get_city_coordinates(city_name)
        url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lng}&current=temperature_2m,precipitation,weather_code&"
            f"daily=precipitation_sum,temperature_2m_max,temperature_2m_min&timezone=Asia%2FKarachi&forecast_days=2"
        )

        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                curr = data.get('current', {})
                daily = data.get('daily', {})
                temp = curr.get('temperature_2m', 26.0)
                precip = curr.get('precipitation', 0.0)
                rain_24h = daily.get('precipitation_sum', [0.0])[0] if daily.get('precipitation_sum') else 0.0
                
                # Determine weather condition description
                code = curr.get('weather_code', 0)
                condition = 'Clear / مطلع صاف'
                if code in [1, 2, 3]:
                    condition = 'Partly Cloudy / جزوی ابر آلود'
                elif code in [51, 53, 55, 61, 63, 65, 80, 81]:
                    condition = 'Rainy / بارش'
                elif code in [95, 96]:
                    condition = 'Thunderstorm / گرج چمک'

                snapshot, _ = WeatherSnapshot.objects.update_or_create(
                    city=city_name,
                    defaults={
                        'temperature': temp,
                        'precipitation_mm': precip,
                        'forecast_24h_rain_mm': rain_24h,
                        'weather_condition': condition,
                    }
                )
                return snapshot
        except Exception as e:
            logger.warning(f"Open-Meteo API unavailable, using seasonal local estimate: {e}")

        # Local default snapshot
        snapshot, _ = WeatherSnapshot.objects.update_or_create(
            city=city_name,
            defaults={
                'temperature': 25.0,
                'precipitation_mm': 0.0,
                'forecast_24h_rain_mm': 0.0,
                'weather_condition': 'Clear Sunny / خوشگوار دھوپ',
            }
        )
        return snapshot

    @classmethod
    def generate_care_schedule(cls, user_plant, days=30):
        """
        Generates recurring CareTask instances for a plant for the next N days based on intervals.
        """
        today = date.today()
        tasks = []

        # 1. Watering Tasks
        interval = max(1, user_plant.watering_interval_days)
        current = today
        while current <= today + timedelta(days=days):
            tasks.append(CareTask(
                user_plant=user_plant,
                task_type='WATER',
                scheduled_date=current,
                status='PENDING'
            ))
            current += timedelta(days=interval)

        # 2. Fertilizer Tasks (e.g. every 30 days)
        fert_interval = user_plant.plant_template.fertilizer_interval_days if user_plant.plant_template else 30
        fert_date = today + timedelta(days=fert_interval)
        if fert_date <= today + timedelta(days=days):
            tasks.append(CareTask(
                user_plant=user_plant,
                task_type='FERTILIZE',
                scheduled_date=fert_date,
                status='PENDING'
            ))

        # 3. Pruning Task if seasonal
        if user_plant.plant_template and user_plant.plant_template.pruning_season:
            tasks.append(CareTask(
                user_plant=user_plant,
                task_type='PRUNE',
                scheduled_date=today + timedelta(days=14),
                status='PENDING',
                weather_note=f"Seasonal Pruning recommended ({user_plant.plant_template.pruning_season})"
            ))

        CareTask.objects.bulk_create(tasks)
        return len(tasks)

    @classmethod
    def apply_weather_rules(cls, user):
        """
        Evaluates weather conditions for user's city and dynamically adjusts pending outdoor care tasks:
        - Rain >= 5mm in 24h: Postpone watering by 1 day.
        - Heat >= 38 C: Attach heat warning note.
        - Cold <= 3 C: Inject frost warning note.
        """
        city = user.city or 'Lahore'
        weather = cls.fetch_live_weather(city)
        today = date.today()

        # Target outdoor pending watering tasks scheduled for today
        outdoor_tasks = CareTask.objects.filter(
            user_plant__user=user,
            user_plant__is_indoor=False,
            scheduled_date=today,
            status='PENDING'
        )

        adjustments = []
        for task in outdoor_tasks:
            if weather.forecast_24h_rain_mm >= 5.0 and task.task_type == 'WATER':
                task.status = 'POSTPONED'
                task.scheduled_date = today + timedelta(days=1)
                task.weather_note = f"بارش کی پیشگوئی ({weather.forecast_24h_rain_mm:.1f}mm) کی وجہ سے پانی دینا مؤخر کر دیا گیا ہے۔"
                task.save()
                adjustments.append(f"{task.user_plant.nickname}: Watering postponed for rain")
            elif weather.temperature >= 38.0 and task.task_type == 'WATER':
                task.weather_note = "شدید گرمی: براہ کرم صبح جلدی یا غروب آفتاب کے بعد پانی دیں۔"
                task.save()
            elif weather.temperature <= 4.0:
                task.weather_note = "سردی اور کورا: رات کو نازک پودوں کو ڈھانپ کر رکھیں۔"
                task.save()

        return adjustments

    @classmethod
    def dispatch_due_reminders(cls):
        """
        Idempotent background reminder sender (runs every 15 mins via cron/management command).
        """
        today = date.today()
        due_tasks = CareTask.objects.filter(
            scheduled_date=today,
            status='PENDING',
            reminder_sent=False
        ).select_related('user_plant__user', 'user_plant')

        sent_count = 0
        for task in due_tasks:
            user = task.user_plant.user
            type_label = task.get_task_type_display()
            title = f"یاددہانی: {task.user_plant.nickname} کی دیکھ بھال"
            body = f"آج {task.user_plant.nickname} کو {type_label} کا وقت ہے۔"
            if task.weather_note:
                body += f" ({task.weather_note})"

            Notification.objects.create(
                recipient=user,
                notification_type='CARE_REMINDER',
                title=title,
                body=body,
                target_url=f"/care/plants/{task.user_plant.id}/"
            )
            task.reminder_sent = True
            task.save()
            sent_count += 1

        return sent_count
