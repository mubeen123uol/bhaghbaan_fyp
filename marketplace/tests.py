from django.test import TestCase
from decimal import Decimal
from accounts.models import User, SellerProfile
from marketplace.models import Product, Order, CommissionSetting, CommissionLedger
from marketplace.services import MarketplaceService

class MarketplaceTests(TestCase):
    def setUp(self):
        self.buyer = User.objects.create_user(username='test_buyer', password='password123', city='Lahore')
        self.seller_user = User.objects.create_user(username='test_seller_user', password='password123')
        self.seller_profile = SellerProfile.objects.create(
            user=self.seller_user,
            business_name="Test Nursery",
            shop_address="Mall Road, Lahore",
            contact_phone="03001112233",
            verification_status='VERIFIED'
        )
        self.product = Product.objects.create(
            seller=self.seller_profile,
            title="Neem Oil 500ml",
            price=Decimal('500.00'),
            stock_quantity=10,
            status='APPROVED'
        )
        CommissionSetting.objects.get_or_create(id=1, defaults={'commission_percentage': 10.0, 'is_active': True})

    def test_cod_order_creation_and_commission(self):
        cart_items = [{'product_id': self.product.id, 'quantity': 2}]
        order = MarketplaceService.create_cod_order(
            buyer=self.buyer,
            shipping_address="House 10, Lahore",
            shipping_city="Lahore",
            contact_phone="03001234567",
            cart_items=cart_items
        )

        # Subtotal: 500 * 2 = 1000, Delivery: 200, Total: 1200
        self.assertEqual(order.subtotal, Decimal('1000.00'))
        self.assertEqual(order.delivery_fee, Decimal('200.00'))
        self.assertEqual(order.total_amount, Decimal('1200.00'))
        self.assertEqual(order.status, 'PLACED')

        # Check stock decrement: 10 - 2 = 8
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, 8)

        # Check Commission Ledger entry: 10% of 1000 = 100
        ledger = CommissionLedger.objects.get(order=order)
        self.assertEqual(ledger.rate_applied, 10.0)
        self.assertEqual(ledger.commission_amount, Decimal('100.00'))

    def test_order_status_progression(self):
        cart_items = [{'product_id': self.product.id, 'quantity': 1}]
        order = MarketplaceService.create_cod_order(
            buyer=self.buyer,
            shipping_address="Address",
            shipping_city="Lahore",
            contact_phone="0300",
            cart_items=cart_items
        )

        # Advance PLACED -> CONFIRMED
        MarketplaceService.update_order_status(order, 'CONFIRMED', self.seller_user)
        self.assertEqual(order.status, 'CONFIRMED')

        # Advance CONFIRMED -> SHIPPED
        MarketplaceService.update_order_status(order, 'SHIPPED', self.seller_user)
        self.assertEqual(order.status, 'SHIPPED')

        # Advance SHIPPED -> DELIVERED
        MarketplaceService.update_order_status(order, 'DELIVERED', self.seller_user)
        self.assertEqual(order.status, 'DELIVERED')
