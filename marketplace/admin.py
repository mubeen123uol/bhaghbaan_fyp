from django.contrib import admin
from .models import Product, ProductImage, Order, OrderItem, CommissionSetting, CommissionLedger

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'price', 'stock_quantity', 'status', 'created_at')
    list_filter = ('category', 'status')
    search_fields = ('title', 'description', 'seller__business_name')
    inlines = [ProductImageInline]
    actions = ['approve_products', 'reject_products']

    def approve_products(self, request, queryset):
        queryset.update(status='APPROVED')
    approve_products.short_description = "Approve selected products"

    def reject_products(self, request, queryset):
        queryset.update(status='REJECTED')
    reject_products.short_description = "Reject selected products"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'buyer', 'status', 'shipping_city', 'subtotal', 'delivery_fee', 'total_amount', 'created_at')
    list_filter = ('status', 'shipping_city')
    search_fields = ('id', 'buyer__username', 'shipping_address', 'contact_phone')
    inlines = [OrderItemInline]

@admin.register(CommissionSetting)
class CommissionSettingAdmin(admin.ModelAdmin):
    list_display = ('commission_percentage', 'is_active', 'updated_at')

@admin.register(CommissionLedger)
class CommissionLedgerAdmin(admin.ModelAdmin):
    list_display = ('order', 'rate_applied', 'commission_amount', 'recorded_at')
