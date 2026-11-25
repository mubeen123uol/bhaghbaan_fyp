from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from decimal import Decimal
from .models import Product, Order, OrderItem
from .services import MarketplaceService

def product_list(request):
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', '').strip()

    products = Product.objects.filter(status='APPROVED', stock_quantity__gt=0)
    if query:
        products = products.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if category:
        products = products.filter(category=category)

    return render(request, 'marketplace/product_list.html', {
        'products': products,
        'categories': Product.CATEGORY_CHOICES,
        'query': query,
        'selected_category': category,
    })

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk, status='APPROVED')
    return render(request, 'marketplace/product_detail.html', {'product': product})

def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk, status='APPROVED')
    qty = int(request.POST.get('quantity', 1))

    cart = request.session.get('cart', {})
    prod_id = str(product.id)
    cart[prod_id] = cart.get(prod_id, 0) + qty
    request.session['cart'] = cart
    messages.success(request, f"{product.title} کارٹ میں شامل کر دیا گیا ہے۔")
    return redirect(request.META.get('HTTP_REFERER', 'cart'))

def remove_from_cart(request, pk):
    cart = request.session.get('cart', {})
    prod_id = str(pk)
    if prod_id in cart:
        del cart[prod_id]
        request.session['cart'] = cart
        messages.info(request, "آئٹم کارٹ سے خارج کر دیا گیا ہے۔")
    return redirect('cart')

def cart_view(request):
    cart = request.session.get('cart', {})
    cart_items = []
    subtotal = Decimal('0.00')

    for prod_id, qty in cart.items():
        product = Product.objects.filter(id=prod_id).first()
        if product:
            total = product.price * qty
            subtotal += total
            cart_items.append({
                'product': product,
                'quantity': qty,
                'total_price': total,
            })

    delivery_fee = Decimal('200.00') if cart_items else Decimal('0.00')
    grand_total = subtotal + delivery_fee

    return render(request, 'marketplace/cart.html', {
        'cart_items': cart_items,
        'subtotal': subtotal,
        'delivery_fee': delivery_fee,
        'grand_total': grand_total,
    })

@login_required
def checkout_view(request):
    cart = request.session.get('cart', {})
    if not cart:
        messages.warning(request, "آپ کی کارٹ خالی ہے۔")
        return redirect('marketplace-products')

    cart_items = [{'product_id': int(pid), 'quantity': qty} for pid, qty in cart.items()]

    if request.method == 'POST':
        addr = request.POST.get('shipping_address')
        city = request.POST.get('shipping_city', request.user.city)
        phone = request.POST.get('contact_phone', request.user.phone)

        try:
            order = MarketplaceService.create_cod_order(
                buyer=request.user,
                shipping_address=addr,
                shipping_city=city,
                contact_phone=phone,
                cart_items=cart_items
            )
            # Clear session cart
            request.session['cart'] = {}
            messages.success(request, "کیش آن ڈیلیوری آرڈر کامیابی سے درج ہو گیا ہے!")
            return redirect('order-detail', pk=order.pk)
        except Exception as e:
            messages.error(request, str(e))

    return render(request, 'marketplace/checkout.html', {'user': request.user})

@login_required
def order_list(request):
    orders = Order.objects.filter(buyer=request.user)
    return render(request, 'marketplace/order_list.html', {'orders': orders})

@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk)
    # Check access: buyer or seller
    is_buyer = order.buyer == request.user
    is_seller = hasattr(request.user, 'seller_profile') and order.items.filter(seller=request.user.seller_profile).exists()

    if not is_buyer and not is_seller and not request.user.is_superuser:
        messages.error(request, "آپ کو اس آرڈر تک رسائی کی اجازت نہیں ہے۔")
        return redirect('order-list')

    return render(request, 'marketplace/order_detail.html', {
        'order': order,
        'is_buyer': is_buyer,
        'is_seller': is_seller,
    })

@login_required
def seller_dashboard(request):
    if not hasattr(request.user, 'seller_profile'):
        messages.info(request, "پہلے بطور سیلر اپلائی کریں۔")
        return redirect('seller-apply')

    profile = request.user.seller_profile
    my_products = Product.objects.filter(seller=profile)
    received_orders = Order.objects.filter(items__seller=profile).distinct()

    if request.method == 'POST' and 'add_product' in request.POST:
        title = request.POST.get('title')
        category = request.POST.get('category')
        desc = request.POST.get('description')
        price = Decimal(request.POST.get('price', '0.00'))
        stock = int(request.POST.get('stock_quantity', 1))
        image = request.FILES.get('main_image')

        Product.objects.create(
            seller=profile,
            title=title,
            category=category,
            description=desc,
            price=price,
            stock_quantity=stock,
            main_image=image,
            status='APPROVED' # Instant approval for demo / verified sellers
        )
        messages.success(request, "نیا پروڈکٹ کامیابی سے شامل ہو گیا ہے۔")
        return redirect('seller-dashboard')

    if request.method == 'POST' and 'update_order_status' in request.POST:
        order_id = request.POST.get('order_id')
        new_status = request.POST.get('new_status')
        order = get_object_or_404(Order, id=order_id)
        try:
            MarketplaceService.update_order_status(order, new_status, request.user)
            messages.success(request, f"آرڈر #{order.id} کا اسٹیٹس '{new_status}' کر دیا گیا ہے۔")
        except Exception as e:
            messages.error(request, str(e))
        return redirect('seller-dashboard')

    return render(request, 'marketplace/seller_dashboard.html', {
        'profile': profile,
        'products': my_products,
        'orders': received_orders,
        'categories': Product.CATEGORY_CHOICES,
    })
