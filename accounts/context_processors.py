import re

_ANDROID_PACKAGE_RE = re.compile(r'^[a-zA-Z0-9_]+(\.[a-zA-Z0-9_]+)+$')


def _detect_app_view(request):
    """
    Detect whether the request comes from an installed Android APK/WebView
    or explicit app-mode override rather than a normal mobile web browser.
    """
    session = getattr(request, 'session', None)
    get_params = getattr(request, 'GET', None)
    app_param = ''
    if get_params is not None:
        app_param = (get_params.get('app') or get_params.get('mode') or '').strip().lower()

    if app_param in ('1', 'true', 'yes', 'app', 'apk'):
        if session is not None:
            session['app_view'] = True
        return True
    if app_param in ('0', 'false', 'no', 'web', 'site', 'website'):
        if session is not None:
            session.pop('app_view', None)
        return False

    if session is not None and session.get('app_view'):
        return True

    meta = getattr(request, 'META', {}) or {}
    ua = (meta.get('HTTP_USER_AGENT') or '').lower()
    if '; wv)' in ua or ';wv)' in ua:
        return True
    if any(token in ua for token in ('baghbaanapp', 'baghbaan-apk', 'baghbaan_apk', 'capacitor', 'cordova')):
        return True

    x_req = (meta.get('HTTP_X_REQUESTED_WITH') or '').strip()
    if x_req and x_req.lower() != 'xmlhttprequest' and _ANDROID_PACKAGE_RE.match(x_req):
        return True

    return False


def baghbaan_context(request):
    """
    Context processor to inject unread notification count, shopping cart count,
    user language, RTL indicators, and app-view flag across all templates.
    """
    context = {
        'unread_notifications_count': 0,
        'cart_count': 0,
        'user_role': None,
        'current_language': 'ur',
        'is_rtl': True,
        'is_app_view': _detect_app_view(request),
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
