from django.test import TestCase
from django.core.exceptions import ValidationError
from decimal import Decimal
from datetime import date
from accounts.models import User
from services.models import Garden, GardenMember, Task, Expense
from services.services import GardenService

class TaskStateMachineTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='test_owner', password='password123', role='HOMEOWNER')
        self.gardener = User.objects.create_user(username='test_gardener', password='password123', role='GARDENER')
        self.supervisor = User.objects.create_user(username='test_supervisor', password='password123', role='SUPERVISOR')
        self.other_user = User.objects.create_user(username='test_other', password='password123', role='HOMEOWNER')

        self.garden = Garden.objects.create(
            owner=self.owner,
            name="Test Garden",
            location_address="Model Town, Lahore",
            total_budget=Decimal('20000.00')
        )
        GardenMember.objects.create(garden=self.garden, user=self.gardener, role='GARDENER')
        GardenMember.objects.create(garden=self.garden, user=self.supervisor, role='SUPERVISOR')

    def test_valid_task_lifecycle_transitions(self):
        # 1. Create Task (CREATED)
        task = Task.objects.create(
            garden=self.garden,
            title="Prune Rose Bush",
            description="Remove dead wood",
            created_by=self.owner,
            state='CREATED'
        )
        self.assertEqual(task.state, 'CREATED')

        # 2. Transition CREATED -> ASSIGNED
        task.assigned_to = self.gardener
        updated = GardenService.transition_task_state(task, 'ASSIGNED', self.owner)
        self.assertEqual(updated.state, 'ASSIGNED')

        # 3. Transition ASSIGNED -> IN_PROGRESS by gardener
        updated = GardenService.transition_task_state(task, 'IN_PROGRESS', self.gardener)
        self.assertEqual(updated.state, 'IN_PROGRESS')

        # 4. Transition IN_PROGRESS -> SUBMITTED by gardener with report
        updated = GardenService.transition_task_state(task, 'SUBMITTED', self.gardener, notes="Finished pruning.")
        self.assertEqual(updated.state, 'SUBMITTED')
        self.assertTrue(hasattr(updated, 'report'))
        self.assertEqual(updated.report.notes, "Finished pruning.")

        # 5. Transition SUBMITTED -> APPROVED by supervisor/owner
        updated = GardenService.transition_task_state(task, 'APPROVED', self.supervisor, notes="Great job.")
        self.assertEqual(updated.state, 'APPROVED')

    def test_invalid_task_transition_rejected(self):
        task = Task.objects.create(
            garden=self.garden,
            title="Irrigation check",
            description="Fix pipes",
            created_by=self.owner,
            state='CREATED'
        )
        # Attempt illegal jump CREATED directly to APPROVED
        with self.assertRaises(ValidationError):
            GardenService.transition_task_state(task, 'APPROVED', self.owner)

    def test_unauthorized_user_transition_rejected(self):
        task = Task.objects.create(
            garden=self.garden,
            title="Fertilizing",
            description="Add compost",
            created_by=self.owner,
            state='ASSIGNED',
            assigned_to=self.gardener
        )
        # Unrelated user cannot start gardener's task
        with self.assertRaises(ValidationError):
            GardenService.transition_task_state(task, 'IN_PROGRESS', self.other_user)

    def test_expense_and_budget_tracking(self):
        exp1 = GardenService.record_expense(
            garden=self.garden,
            title="Fertilizer bags",
            category="FERTILIZER",
            amount=Decimal('5000.00'),
            user=self.owner,
            expense_date=date.today()
        )
        self.assertEqual(self.garden.total_expenses(), 5000.00)
        self.assertEqual(self.garden.remaining_budget(), 15000.00)
