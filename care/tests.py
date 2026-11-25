from django.test import TestCase
from datetime import date, timedelta
from accounts.models import User
from plants.models import Plant
from care.models import UserPlant, CareTask, WeatherSnapshot
from care.services import CareCalendarService

class CareAndWeatherTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='care_user', password='password123', city='Lahore')
        self.plant_tpl = Plant.objects.create(
            name_en="Tomato",
            name_ur="ٹماٹر",
            scientific_name="Solanum lycopersicum test",
            watering_interval_days=2,
            fertilizer_interval_days=20
        )
        self.user_plant = UserPlant.objects.create(
            user=self.user,
            plant_template=self.plant_tpl,
            nickname="Test Tomato",
            watering_interval_days=2,
            is_indoor=False
        )

    def test_care_schedule_generation(self):
        count = CareCalendarService.generate_care_schedule(self.user_plant, days=30)
        self.assertGreater(count, 0)
        tasks = CareTask.objects.filter(user_plant=self.user_plant)
        self.assertTrue(tasks.filter(task_type='WATER').exists())
        self.assertTrue(tasks.filter(task_type='FERTILIZE').exists())

    def test_rain_weather_postponement_rule(self):
        # Create a watering task due today
        today = date.today()
        task = CareTask.objects.create(
            user_plant=self.user_plant,
            task_type='WATER',
            scheduled_date=today,
            status='PENDING'
        )

        # Mock weather snapshot with 8mm rain in 24 hours
        WeatherSnapshot.objects.update_or_create(
            city='Lahore',
            defaults={
                'temperature': 22.0,
                'precipitation_mm': 2.0,
                'forecast_24h_rain_mm': 8.5,
                'weather_condition': 'Heavy Rain'
            }
        )

        # Run weather adjustment
        CareCalendarService.apply_weather_rules(self.user)

        task.refresh_from_db()
        # Task should now be postponed to tomorrow
        self.assertEqual(task.status, 'POSTPONED')
        self.assertEqual(task.scheduled_date, today + timedelta(days=1))
        self.assertIn("بارش", task.weather_note)
