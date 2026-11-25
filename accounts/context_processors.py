def baghbaan_context(request):
    """
    Context processor to inject unread notification count, shopping cart count,
    user language, and RTL indicators across all templates.
    """
    context = {
        'unread_notifications_count': 0,
        'cart_count': 0,
        'user_role': None,
        'current_language': 'ur',
        'is_rtl': True,
    }

    # Shopping cart count from session
    cart = request.session.get('cart', {})
    context['cart_count'] = sum(cart.values()) if isinstance(cart, dict) else 0

    session_lang = request.session.get('django_language')
    if request.user.is_authenticated:
        user = request.user
        context['user_role'] = user.role
        current_lang = session_lang or user.preferred_language or 'ur'
        context['current_language'] = current_lang
        context['is_rtl'] = (current_lang == 'ur')
        
        # Calculate unread notifications safely
        try:
            from notifications.models import Notification
            context['unread_notifications_count'] = Notification.objects.filter(
                recipient=user, is_read=False
            ).count()
        except Exception:
            context['unread_notifications_count'] = 0
    else:
        current_lang = session_lang or 'ur'
        context['current_language'] = current_lang
        context['is_rtl'] = (current_lang == 'ur')

    return context
