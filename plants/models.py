from django.db import models

class Plant(models.Model):
    CATEGORY_CHOICES = (
        ('ORNAMENTAL', 'Ornamental / زرد پودے'),
        ('FRUIT', 'Fruit Trees / پھل دار درخت'),
        ('VEGETABLE', 'Vegetables / سبزیاں'),
        ('HERB', 'Herbs / جڑی بوٹیاں'),
        ('TREE', 'Trees / سایہ دار درخت'),
        ('SUCCULENT', 'Cactus & Succulents / کیکٹس'),
    )

    name_en = models.CharField(max_length=120)
    name_ur = models.CharField(max_length=120)
    name_roman = models.CharField(max_length=120, blank=True)
    scientific_name = models.CharField(max_length=150, unique=True)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default='ORNAMENTAL')
    image = models.ImageField(upload_to='plants/', null=True, blank=True)
    description_en = models.TextField()
    description_ur = models.TextField()

    # Baseline Care Parameters
    watering_interval_days = models.PositiveIntegerField(default=2)
    fertilizer_interval_days = models.PositiveIntegerField(default=30)
    pruning_season = models.CharField(max_length=60, blank=True)
    sunlight_requirement = models.CharField(max_length=60, default='Full Sun')
    is_indoor_suitable = models.BooleanField(default=False)
    climate_notes_pakistan = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name_ur} ({self.name_en}) - {self.scientific_name}"


class Disease(models.Model):
    SEVERITY_CHOICES = (
        ('LOW', 'Low Severity'),
        ('MEDIUM', 'Medium Severity'),
        ('HIGH', 'High Severity'),
        ('CRITICAL', 'Critical / Lethal'),
    )

    name_en = models.CharField(max_length=150)
    name_ur = models.CharField(max_length=150)
    name_roman = models.CharField(max_length=150, blank=True)
    scientific_name = models.CharField(max_length=150, blank=True)
    plants = models.ManyToManyField(Plant, related_name='diseases', blank=True)
    symptoms_en = models.TextField()
    symptoms_ur = models.TextField()
    severity_level = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='MEDIUM')
    sample_image = models.ImageField(upload_to='diseases/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name_ur} ({self.name_en})"


class Treatment(models.Model):
    TREATMENT_TYPES = (
        ('ORGANIC', 'Organic / دیسی اور گھریلو علاج'),
        ('CHEMICAL', 'Chemical / کیمیکل اور زرعی ادویات'),
    )

    disease = models.ForeignKey(Disease, on_delete=models.CASCADE, related_name='treatments')
    treatment_type = models.CharField(max_length=20, choices=TREATMENT_TYPES, default='ORGANIC')
    title_en = models.CharField(max_length=180)
    title_ur = models.CharField(max_length=180)
    instructions_en = models.TextField()
    instructions_ur = models.TextField()
    safety_disclaimer_ur = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.get_treatment_type_display()}] {self.title_en} for {self.disease.name_en}"
