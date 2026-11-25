from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('HOMEOWNER', 'Homeowner'),
        ('GARDENER', 'Gardener'),
        ('SUPERVISOR', 'Supervisor'),
        ('SELLER', 'Seller'),
        ('ADMIN', 'Admin'),
    )
    LANGUAGE_CHOICES = (
        ('ur', 'Urdu'),
        ('ur_ro', 'Roman Urdu'),
        ('en', 'English'),
    )

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='HOMEOWNER', db_index=True)
    phone = models.CharField(max_length=25, blank=True, null=True, unique=True)
    city = models.CharField(max_length=100, default='Lahore', db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    preferred_language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='ur')
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    is_verified_professional = models.BooleanField(default=False)
    years_of_experience = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_gardener(self):
        return self.role in ['GARDENER', 'SUPERVISOR']

    def is_supervisor(self):
        return self.role == 'SUPERVISOR' or self.is_superuser

    def is_seller(self):
        return self.role == 'SELLER' or hasattr(self, 'seller_profile')

    @property
    def display_name_en(self):
        name_map = {
            'ahmed': 'Ahmed Khan',
            'ali_mali': 'Ali (Mali)',
            'tariq_supervisor': 'Tariq Mehmood',
            'bilal_nursery': 'Bilal Nursery',
            'admin': 'Admin',
        }
        if self.username in name_map:
            return name_map[self.username]
        # If first_name is non-ASCII (Urdu), fallback to username title
        if self.first_name and any(ord(c) > 127 for c in self.first_name):
            return self.username.replace('_', ' ').title()
        return self.first_name or self.username

    @property
    def display_name_ur(self):
        name_map = {
            'ahmed': 'احمد خان',
            'ali_mali': 'علی مالی',
            'tariq_supervisor': 'طارق محمود',
            'bilal_nursery': 'بلال نرسری والے',
            'admin': 'ایڈمن',
        }
        if self.username in name_map:
            return name_map[self.username]
        return self.first_name or self.username

    def get_role_display_en(self):
        role_map = {
            'HOMEOWNER': 'Homeowner',
            'GARDENER': 'Gardener',
            'SUPERVISOR': 'Supervisor',
            'SELLER': 'Nursery Seller',
            'ADMIN': 'Administrator',
        }
        return role_map.get(self.role, self.role)

    def get_role_display_ur(self):
        role_map = {
            'HOMEOWNER': 'باغبانی شوقین',
            'GARDENER': 'مالی',
            'SUPERVISOR': 'نگران',
            'SELLER': 'نرسری سیلر',
            'ADMIN': 'ایڈمن',
        }
        return role_map.get(self.role, self.role)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()}) - {self.city}"


class SellerProfile(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending Admin Verification'),
        ('VERIFIED', 'Verified Seller'),
        ('REJECTED', 'Rejected'),
        ('SUSPENDED', 'Suspended'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=150)
    cnic_number = models.CharField(max_length=20, blank=True)
    shop_address = models.TextField()
    contact_phone = models.CharField(max_length=20)
    verification_status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', db_index=True)
    admin_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_approved(self):
        return self.verification_status == 'VERIFIED'

    @property
    def business_name_en(self):
        if '(' in self.business_name and ')' in self.business_name:
            import re
            m = re.search(r'\((.*?)\)', self.business_name)
            if m:
                return m.group(1).strip()
        return self.business_name

    @property
    def business_name_ur(self):
        if '(' in self.business_name:
            return self.business_name.split('(')[0].strip()
        return self.business_name

    def __str__(self):
        return f"{self.business_name} [{self.get_verification_status_display()}]"


class DeviceToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='device_tokens')
    token = models.CharField(max_length=255, unique=True)
    platform = models.CharField(max_length=20, default='android')
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.platform} token"
