from django.db import models
from django.conf import settings

class Product(models.Model):
    CATEGORY_CHOICES = (
        ('PLANTS', 'Live Plants & Saplings / زندہ پودے'),
        ('SEEDS', 'Vegetable & Flower Seeds / بیج'),
        ('FERTILIZER', 'Organic & Chemical Fertilizers / کھاد'),
        ('PESTICIDE', 'Pest & Fungus Controls / زرعی ادویات'),
        ('POTS', 'Clay & Plastic Pots / گملے'),
        ('TOOLS', 'Gardening Tools / باغبانی کے اوزار'),
    )
    APPROVAL_CHOICES = (
        ('PENDING', 'Pending Admin Approval / زیر التواء'),
        ('APPROVED', 'Approved / منظور شدہ'),
        ('REJECTED', 'Rejected / مسترد شدہ'),
    )

    seller = models.ForeignKey('accounts.SellerProfile', on_delete=models.CASCADE, related_name='products')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='PLANTS')
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=20, choices=APPROVAL_CHOICES, default='APPROVED', db_index=True)
    main_image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def is_in_stock(self):
        return self.stock_quantity > 0

    @property
    def title_en(self):
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
        desc_map = {
            1: "100% cold-pressed organic neem oil for natural pest control against whiteflies, aphids, mealybugs, and spider mites. Safe for vegetables and ornamental plants.",
            2: "Two-year fully decomposed aged organic cow manure compost. Restores soil biology, enhances aeration, and enriches container soil naturally.",
            3: "Fragrant native Desi Red Rose established in a 12-inch clay pot with fertile silt mix. Blooming with multiple healthy flower buds.",
            4: "Two-year-old grafted Kaghzi Lemon sapling acclimated to Pakistani heat. High yield of thin-skinned, extra juicy fragrant lemons.",
            5: "Premium pack of 10 kitchen garden vegetable seeds (Tomato, Green Chili, Spinach, Coriander, Radish, Carrot, Fenugreek, Mint, Lettuce, Turnip) with 85%+ germination rate.",
            6: "Traditional Gujrat handcrafted porous terracotta clay pot. Naturally cools root systems during intense summer heat and prevents overwatering.",
            7: "Heavy-duty ergonomic garden bypass pruning shears with rust-resistant carbon steel blades and safety thumb lock.",
            8: "Premium 100% water-soluble balanced NPK (20-20-20) macro-nutrient plant food with trace micronutrients for vibrant blooms and deep green leaves."
        }
        if self.id in desc_map:
            return desc_map[self.id]
        if '(' in self.description and ')' in self.description:
            import re
            m = re.search(r'\((.*?)\)', self.description)
            if m:
                return m.group(1).strip()
        return self.description

    @property
    def description_ur(self):
        if '(' in self.description:
            return self.description.split('(')[0].strip()
        return self.description

    @property
    def category_en(self):
        cat_map = {
            'PLANTS': 'Live Plants',
            'SEEDS': 'Seeds',
            'FERTILIZER': 'Fertilizer',
            'PESTICIDE': 'Pest & Fungus Control',
            'POTS': 'Planters & Pots',
            'TOOLS': 'Gardening Tools',
        }
        return cat_map.get(self.category, self.category)

    @property
    def category_ur(self):
        cat_map = {
            'PLANTS': 'زندہ پودے',
            'SEEDS': 'بیج',
            'FERTILIZER': 'کھاد',
            'PESTICIDE': 'زرعی ادویات',
            'POTS': 'گملے',
            'TOOLS': 'باغبانی کے اوزار',
        }
        return cat_map.get(self.category, self.category)

    def __str__(self):
        return f"{self.title} - Rs {self.price} ({self.seller.business_name})"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='products/gallery/')

    def __str__(self):
        return f"Gallery image for {self.product.title}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('PLACED', 'Order Placed (COD) / آرڈر موصول ہوا'),
        ('CONFIRMED', 'Confirmed / تصدیق شدہ'),
        ('SHIPPED', 'Dispatched / روانہ کر دیا گیا'),
        ('DELIVERED', 'Delivered & Paid / پہنچ گیا اور ادائیگی مکمل'),
        ('CANCELLED', 'Cancelled / منسوخ شدہ'),
    )

    buyer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLACED', db_index=True)
    shipping_address = models.TextField()
    shipping_city = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=25)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_fee = models.DecimalField(max_digits=6, decimal_places=2, default=200.0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    @property
    def status_en(self):
        stat_map = {
            'PLACED': 'Order Placed (COD)',
            'CONFIRMED': 'Confirmed by Nursery',
            'SHIPPED': 'Dispatched / Out for Delivery',
            'DELIVERED': 'Delivered & Paid',
            'CANCELLED': 'Cancelled',
        }
        return stat_map.get(self.status, self.status)

    @property
    def status_ur(self):
        stat_map = {
            'PLACED': 'آرڈر موصول ہوا (COD)',
            'CONFIRMED': 'تصدیق شدہ',
            'SHIPPED': 'روانہ کر دیا گیا',
            'DELIVERED': 'پہنچ گیا اور ادائیگی مکمل',
            'CANCELLED': 'منسوخ شدہ',
        }
        return stat_map.get(self.status, self.status)

    def __str__(self):
        return f"Order #{self.id} by {self.buyer.username} - Rs {self.total_amount} [{self.get_status_display()}]"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    seller = models.ForeignKey('accounts.SellerProfile', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def total_price(self):
        return self.quantity * self.unit_price

    def __str__(self):
        return f"{self.quantity}x {self.product.title} in Order #{self.order.id}"


class CommissionSetting(models.Model):
    commission_percentage = models.FloatField(default=5.0)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Active Commission: {self.commission_percentage}%"


class CommissionLedger(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='commission_entry')
    rate_applied = models.FloatField()
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Commission for Order #{self.order.id}: Rs {self.commission_amount} ({self.rate_applied}%)"
