from django.db import models
from django.conf import settings

class Garden(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='gardens')
    name = models.CharField(max_length=150)
    location_address = models.TextField()
    city = models.CharField(max_length=100, default='Lahore', db_index=True)
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def total_expenses(self):
        total = self.expenses.aggregate(models.Sum('amount'))['amount__sum']
        return total or 0.0

    def remaining_budget(self):
        return float(self.total_budget) - float(self.total_expenses())

    @property
    def name_en(self):
        if '(' in self.name and ')' in self.name:
            import re
            m = re.search(r'\((.*?)\)', self.name)
            if m:
                return m.group(1).strip()
        return self.name

    @property
    def name_ur(self):
        if '(' in self.name:
            return self.name.split('(')[0].strip()
        return self.name

    def __str__(self):
        return f"{self.name} - {self.owner.username} ({self.city})"


class GardenMember(models.Model):
    MEMBER_ROLES = (
        ('GARDENER', 'Gardener / مالی'),
        ('SUPERVISOR', 'Supervisor / نگران'),
    )

    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='garden_memberships')
    role = models.CharField(max_length=20, choices=MEMBER_ROLES, default='GARDENER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('garden', 'user')

    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()}) in {self.garden.name}"


class Task(models.Model):
    STATE_CHOICES = (
        ('CREATED', 'Created / بنایا گیا'),
        ('ASSIGNED', 'Assigned / سونپا گیا'),
        ('IN_PROGRESS', 'In Progress / کام جاری ہے'),
        ('SUBMITTED', 'Submitted / رپورٹ جمع کر دی گئی'),
        ('APPROVED', 'Approved / منظور شدہ'),
    )

    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField()
    state = models.CharField(max_length=20, choices=STATE_CHOICES, default='CREATED', db_index=True)
    assigned_to = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_tasks')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def can_transition_to(self, new_state, user):
        """
        Enforce the 5-state lifecycle:
        CREATED -> ASSIGNED -> IN_PROGRESS -> SUBMITTED -> APPROVED
        or SUBMITTED -> IN_PROGRESS (on supervisor rejection)
        """
        if self.state == 'CREATED' and new_state == 'ASSIGNED':
            return user == self.garden.owner or user.role == 'SUPERVISOR'
        if self.state == 'ASSIGNED' and new_state == 'IN_PROGRESS':
            return user == self.assigned_to or user == self.garden.owner
        if self.state == 'IN_PROGRESS' and new_state == 'SUBMITTED':
            return user == self.assigned_to
        if self.state == 'SUBMITTED' and new_state == 'APPROVED':
            return user == self.garden.owner or user.role == 'SUPERVISOR'
        if self.state == 'SUBMITTED' and new_state == 'IN_PROGRESS':
            return user == self.garden.owner or user.role == 'SUPERVISOR'
        return False

    @property
    def title_en(self):
        task_map_en = {
            'ڈرپ اریگیشن پائپ اور نوزلز کی صفائی': 'Clean Drip Irrigation Pipes & Nozzles',
            'ڈرپ اریگیشن پائیپ اور نوزلز کی صفائی': 'Clean Drip Irrigation Pipes & Nozzles',
            'کچن گارڈن کے لیے پالک اور دھنیا کی نئی پنیری لگانا': 'Sow Spinach & Coriander Seedlings for Kitchen Garden',
            'لیموں کے پودے پر سفید مکھی کے خاتمے کے لیے نیم آئل اسپرے': 'Spray Neem Oil on Lemon Plant for Whitefly Control',
            'گلاب کی پرانی شاخوں کی کٹائی اور گملے کی گڈی': 'Prune Dead Rose Canes & Till Pot Soil with Compost',
            'موسم بہار کے پھولوں کے لیے نئے مٹی کے گملے خریدنا': 'Purchase 14-Inch Terracotta Pots for Spring Blooms',
        }
        stripped = self.title.strip()
        if stripped in task_map_en:
            return task_map_en[stripped]
        for k, v in task_map_en.items():
            if 'ڈرپ' in stripped and 'صفائی' in stripped:
                return 'Clean Drip Irrigation Pipes & Nozzles'
            if 'پالک' in stripped or 'دھنیا' in stripped:
                return 'Sow Spinach & Coriander Seedlings for Kitchen Garden'
            if 'سفید مکھی' in stripped or 'نیم' in stripped:
                return 'Spray Neem Oil on Lemon Plant for Whitefly Control'
            if 'گلاب' in stripped and 'کٹائی' in stripped:
                return 'Prune Dead Rose Canes & Till Pot Soil with Compost'
            if 'گملے' in stripped and 'خرید' in stripped:
                return 'Purchase 14-Inch Terracotta Pots for Spring Blooms'
        if '(' in self.title and ')' in self.title:
            import re
            m = re.search(r'\((.*?)\)', self.title)
            if m:
                return m.group(1).strip()
        return self.title

    @property
    def title_ur(self):
        if '(' in self.title:
            return self.title.split('(')[0].strip()
        return self.title

    @property
    def description_en(self):
        desc_map_en = {
            'چھت پر لگے خودکار ڈرپ پائپوں کو چیک کریں اور بند نوزلز کھولیں۔': 'Inspect rooftop automatic drip irrigation pipes and unclog clogged emitter nozzles.',
            'گرو بیگز میں نرم بھل مٹی بھر کر موسم سرما کی سبزیوں کی پنیری منتقل کریں۔': 'Fill grow bags with soft fertile bhal soil and transplant winter vegetable seedlings.',
            'لیموں کے پتوں کے نیچے سفید مکھی دیکھی گئی ہے، شام کے وقت نیم کے تیل کا اسپرے کریں۔': 'Whiteflies observed on underside of lemon foliage; spray dilute organic neem oil in the evening.',
            'دیسی گلاب کی سوکھی شاخیں کاٹیں اور مٹی میں 2 انچ گہری گڈی کر کے دیسی کھاد ملائیں۔': 'Prune dry rose canes and till soil 2 inches deep, mixing well-rotted organic manure.',
            'نرسری سے 12 انچ والے 10 عدد مٹی کے گملے لانا۔': 'Procure 10 units of 12-inch terracotta clay pots from the nursery.',
        }
        stripped = self.description.strip()
        return desc_map_en.get(stripped, self.description)

    @property
    def state_en(self):
        map_state = {
            'CREATED': 'Created',
            'ASSIGNED': 'Assigned',
            'IN_PROGRESS': 'In Progress',
            'SUBMITTED': 'Submitted for Review',
            'APPROVED': 'Approved & Completed',
        }
        return map_state.get(self.state, self.state)

    @property
    def assigned_to_name_en(self):
        if self.assigned_to:
            return self.assigned_to.display_name_en
        return "Unassigned"

    @property
    def assigned_to_name_ur(self):
        if self.assigned_to:
            return self.assigned_to.display_name_ur
        return "غیر متعین / کوئی نہیں"

    @property
    def assigned_to_name(self):
        if self.assigned_to:
            return self.assigned_to.first_name or self.assigned_to.username
        return "غیر متعین / کوئی نہیں"

    def __str__(self):
        return f"Task #{self.id}: {self.title} [{self.get_state_display()}]"


class TaskReport(models.Model):
    task = models.OneToOneField(Task, on_delete=models.CASCADE, related_name='report')
    notes = models.TextField()
    photo_proof = models.ImageField(upload_to='task_reports/%Y/%m/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    supervisor_review_notes = models.TextField(blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Report for Task #{self.task.id}"


class Expense(models.Model):
    CATEGORY_CHOICES = (
        ('LABOR', 'Labor / مالی کی اجرت'),
        ('PLANTS', 'Plants & Saplings / پودے اور قلمیں'),
        ('FERTILIZER', 'Fertilizer & Soil / کھاد اور بھل'),
        ('TOOLS', 'Tools & Pots / گملے اور اوزار'),
        ('OTHER', 'Other / دیگر اخراجات'),
    )

    garden = models.ForeignKey(Garden, on_delete=models.CASCADE, related_name='expenses')
    title = models.CharField(max_length=150)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='LABOR')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    receipt_photo = models.ImageField(upload_to='receipts/', null=True, blank=True)
    recorded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expense_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-expense_date']

    def __str__(self):
        return f"{self.title}: Rs {self.amount} ({self.garden.name})"
