from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Product, Order, OrderItem, CommissionSetting, CommissionLedger
from notifications.models import Notification

class MarketplaceService:
    @classmethod
    @transaction.atomic
    def create_cod_order(cls, buyer, shipping_address, shipping_city, contact_phone, cart_items):
        """
        Processes Cash on Delivery (COD) order:
        - Validates stock.
        - Decrements inventory.
        - Calculates subtotal and delivery fee.
        - Creates Order and OrderItems.
        - Applies admin commission and creates CommissionLedger entry.
        """
        if not cart_items:
            raise ValidationError("آپ کی کارٹ خالی ہے۔")

        subtotal = Decimal('0.00')
        order_items_to_create = []

        # Validate products and stock
        for item in cart_items:
            product = Product.objects.select_for_update().get(id=item['product_id'])
            qty = int(item['quantity'])

            if product.stock_quantity < qty:
                raise ValidationError(f"پروڈکٹ '{product.title}' کا مطلوبہ اسٹاک دستیاب نہیں ہے۔")

            item_total = product.price * qty
            subtotal += item_total

            # Decrement stock
            product.stock_quantity -= qty
            product.save()

            order_items_to_create.append({
                'product': product,
                'seller': product.seller,
                'quantity': qty,
                'unit_price': product.price,
            })

        delivery_fee = Decimal('200.00')
        total_amount = subtotal + delivery_fee

        order = Order.objects.create(
            buyer=buyer,
            status='PLACED',
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            contact_phone=contact_phone,
            subtotal=subtotal,
            delivery_fee=delivery_fee,
            total_amount=total_amount,
        )

        for oi in order_items_to_create:
            OrderItem.objects.create(
                order=order,
                product=oi['product'],
                seller=oi['seller'],
                quantity=oi['quantity'],
                unit_price=oi['unit_price']
            )

        # Apply Admin Commission Rate
        commission_setting = CommissionSetting.objects.filter(is_active=True).first()
        rate = commission_setting.commission_percentage if commission_setting else 5.0
        commission_val = subtotal * (Decimal(str(rate)) / Decimal('100.0'))

        CommissionLedger.objects.create(
            order=order,
            rate_applied=rate,
            commission_amount=commission_val
        )

        # Notify Buyer
        Notification.objects.create(
            recipient=buyer,
            notification_type='ORDER_UPDATE',
            title=f"آرڈر موصول ہو گیا #{order.id}",
            body=f"آپ کا کیش آن ڈیلیوری آرڈر کامیابی کے ساتھ بک ہو گیا ہے۔ کل رقم: Rs {total_amount}",
            target_url=f"/marketplace/orders/{order.id}/"
        )

        # Notify unique Sellers involved
        sellers = {oi['seller'].user for oi in order_items_to_create}
        for seller_user in sellers:
            Notification.objects.create(
                recipient=seller_user,
                notification_type='ORDER_UPDATE',
                title="نیا آرڈر موصول ہوا!",
                body=f"خریدار {buyer.username} نے آپ کی نرسری کے سامان کا آرڈر #{order.id} دیا ہے۔",
                target_url=f"/marketplace/orders/{order.id}/"
            )

        return order

    @classmethod
    def update_order_status(cls, order, new_status, actor_user):
        """
        Tracks order lifecycle:
        PLACED -> CONFIRMED -> SHIPPED -> DELIVERED (or CANCELLED)
        """
        valid_transitions = {
            'PLACED': ['CONFIRMED', 'CANCELLED'],
            'CONFIRMED': ['SHIPPED', 'CANCELLED'],
            'SHIPPED': ['DELIVERED'],
            'DELIVERED': [],
            'CANCELLED': []
        }

        if new_status not in valid_transitions.get(order.status, []):
            raise ValidationError(f"Invalid transition from {order.status} to {new_status}")

        order.status = new_status
        order.save()

        # If cancelled, restore stock
        if new_status == 'CANCELLED':
            for item in order.items.all():
                item.product.stock_quantity += item.quantity
                item.product.save()

        # Notify Buyer
        status_display = order.get_status_display()
        Notification.objects.create(
            recipient=order.buyer,
            notification_type='ORDER_UPDATE',
            title=f"آرڈر اسٹیٹس اپڈیٹ #{order.id}",
            body=f"آپ کے آرڈر کا اسٹیٹس اب '{status_display}' ہو گیا ہے۔",
            target_url=f"/marketplace/orders/{order.id}/"
        )

        return order
