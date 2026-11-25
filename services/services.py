import math
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Garden, GardenMember, Task, TaskReport, Expense
from notifications.models import Notification
from accounts.models import User

class GardenService:
    @staticmethod
    def haversine_distance(lat1, lon1, lat2, lon2):
        """
        Calculate great circle distance between two points in kilometers using Haversine formula.
        """
        R = 6371.0 # Earth's radius in kilometers
        phi1 = math.radians(float(lat1))
        phi2 = math.radians(float(lat2))
        delta_phi = math.radians(float(lat2) - float(lat1))
        delta_lambda = math.radians(float(lon2) - float(lon1))

        a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    @classmethod
    def find_nearby_professionals(cls, user_lat, user_lon, max_distance_km=25.0, role=None, city='Lahore'):
        """
        Find verified gardeners and supervisors ordered by geographical proximity.
        """
        query = User.objects.filter(role__in=['GARDENER', 'SUPERVISOR'])
        if role:
            query = query.filter(role=role)

        results = []
        for prof in query:
            if prof.latitude and prof.longitude and user_lat and user_lon:
                dist = cls.haversine_distance(user_lat, user_lon, prof.latitude, prof.longitude)
                if dist <= max_distance_km:
                    results.append({'user': prof, 'distance_km': round(dist, 1)})
            elif prof.city and city and prof.city.lower() == city.lower():
                results.append({'user': prof, 'distance_km': 5.0}) # approximate default for same city
            else:
                results.append({'user': prof, 'distance_km': 15.0})

        results.sort(key=lambda x: x['distance_km'])
        return results

    @classmethod
    def transition_task_state(cls, task, new_state, actor_user, notes=None, photo_proof=None):
        """
        Executes and validates the 5-state lifecycle:
        CREATED -> ASSIGNED -> IN_PROGRESS -> SUBMITTED -> APPROVED
        or SUBMITTED -> IN_PROGRESS (rejection by supervisor/owner)
        """
        current_state = task.state
        if not task.can_transition_to(new_state, actor_user):
            raise ValidationError(
                f"Invalid state transition from '{current_state}' to '{new_state}' for user {actor_user.username}."
            )

        task.state = new_state
        task.save()

        # Handle report creation on SUBMITTED
        if new_state == 'SUBMITTED':
            TaskReport.objects.update_or_create(
                task=task,
                defaults={
                    'notes': notes or 'کام مکمل کر دیا گیا ہے۔',
                    'photo_proof': photo_proof,
                    'submitted_at': timezone.now(),
                }
            )
            # Notify garden owner and supervisor
            Notification.objects.create(
                recipient=task.garden.owner,
                notification_type='TASK_UPDATE',
                title="رپورٹ موصول ہوئی",
                body=f"مالی {actor_user.username} نے ٹاسک '{task.title}' کی رپورٹ جمع کرا دی ہے۔",
                target_url=f"/services/gardens/{task.garden.id}/tasks/{task.id}/"
            )

        # Handle approval
        elif new_state == 'APPROVED':
            if hasattr(task, 'report'):
                task.report.supervisor_review_notes = notes or 'منظور شدہ'
                task.report.reviewed_at = timezone.now()
                task.report.save()

            if task.assigned_to:
                Notification.objects.create(
                    recipient=task.assigned_to,
                    notification_type='TASK_UPDATE',
                    title="کام منظور ہو گیا",
                    body=f"آپ کا کام '{task.title}' منظور کر لیا گیا ہے۔ شاباش!",
                    target_url=f"/services/gardens/{task.garden.id}/tasks/{task.id}/"
                )

        # Handle rejection / revision request
        elif new_state == 'IN_PROGRESS' and current_state == 'SUBMITTED':
            if hasattr(task, 'report'):
                task.report.supervisor_review_notes = notes or 'براہ کرم کام دوبارہ چیک کریں اور رپورٹ درست کریں۔'
                task.report.save()

            if task.assigned_to:
                Notification.objects.create(
                    recipient=task.assigned_to,
                    notification_type='TASK_UPDATE',
                    title="رپورٹ واپس بھیجی گئی",
                    body=f"ٹاسک '{task.title}' کی رپورٹ میں بہتری کی ضرورت ہے: {notes}",
                    target_url=f"/services/gardens/{task.garden.id}/tasks/{task.id}/"
                )

        return task

    @classmethod
    def record_expense(cls, garden, title, category, amount, user, receipt_photo=None, expense_date=None):
        """
        Record garden expenditure and warn if exceeding allocated garden budget.
        """
        from datetime import date
        expense = Expense.objects.create(
            garden=garden,
            title=title,
            category=category,
            amount=amount,
            recorded_by=user,
            receipt_photo=receipt_photo,
            expense_date=expense_date or date.today()
        )

        remaining = garden.remaining_budget()
        if remaining < 0:
            Notification.objects.create(
                recipient=garden.owner,
                notification_type='SYSTEM',
                title="بجٹ کی حد تجاوز کر گئی!",
                body=f"باغ '{garden.name}' میں کل اخراجات الاٹ کردہ بجٹ سے Rs {abs(remaining):.0f} زائد ہو چکے ہیں۔",
                target_url=f"/services/gardens/{garden.id}/"
            )

        return expense
