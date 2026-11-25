from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SellerProfile, DeviceToken

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'city', 'phone', 'is_verified_professional', 'is_staff')
    list_filter = ('role', 'city', 'is_verified_professional', 'preferred_language')
    fieldsets = UserAdmin.fieldsets + (
        ('Baghbaan Profile', {
            'fields': ('role', 'phone', 'city', 'latitude', 'longitude', 'preferred_language', 
                       'avatar', 'bio', 'is_verified_professional', 'years_of_experience', 'hourly_rate')
        }),
    )

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ('business_name', 'user', 'verification_status', 'contact_phone', 'created_at')
    list_filter = ('verification_status',)
    search_fields = ('business_name', 'cnic_number', 'shop_address')
    actions = ['approve_sellers', 'reject_sellers']

    def approve_sellers(self, request, queryset):
        queryset.update(verification_status='VERIFIED')
    approve_sellers.short_description = "Approve selected sellers"

    def reject_sellers(self, request, queryset):
        queryset.update(verification_status='REJECTED')
    reject_sellers.short_description = "Reject selected sellers"

@admin.register(DeviceToken)
class DeviceTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'platform', 'updated_at')
    search_fields = ('user__username', 'token')
