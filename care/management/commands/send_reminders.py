from django.core.management.base import BaseCommand
from care.services import CareCalendarService
from accounts.models import User

class Command(BaseCommand):
    help = 'Idempotent worker that checks due plant care tasks, applies weather rules, and dispatches reminders.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Checking weather conditions and adjusting care tasks..."))
        
        # Apply weather forecast rules for users
        active_users = User.objects.filter(user_plants__isnull=False).distinct()
        for user in active_users:
            adjustments = CareCalendarService.apply_weather_rules(user)
            for adj in adjustments:
                self.stdout.write(f"  - [{user.username}] {adj}")

        # Dispatch due reminders
        sent_count = CareCalendarService.dispatch_due_reminders()
        self.stdout.write(self.style.SUCCESS(f"Successfully processed reminders. Sent {sent_count} new alerts."))
