from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.static import serve

from accounts import views as acc_views
from plants import views as plant_views
from ai_doctor import views as ai_views
from care import views as care_views
from services import views as serv_views
from marketplace import views as market_views
from community import views as comm_views
from notifications import views as notif_views

urlpatterns = [
    # Favicon
    path('favicon.ico', lambda r: HttpResponse(status=204)),

    # Admin Portal
    path('admin/', admin.site.urls),

    # Versioned REST API & OpenAPI Documentation
    path('api/v1/', include(('api.urls', 'api'), namespace='api')),

    # Accounts & Authentication
    path('', acc_views.home, name='home'),
    path('dashboard/', acc_views.dashboard, name='dashboard'),
    path('login/', acc_views.login_view, name='login'),
    path('register/', acc_views.register_view, name='register'),
    path('logout/', acc_views.logout_view, name='logout'),
    path('profile/', acc_views.profile_view, name='profile'),
    path('lang/<str:lang_code>/', acc_views.set_language_view, name='set-language'),
    path('seller/apply/', acc_views.seller_apply_view, name='seller-apply'),

    # Standard Django auth compatibility aliases
    path('accounts/login/', acc_views.login_view),
    path('accounts/register/', acc_views.register_view),
    path('accounts/logout/', acc_views.logout_view),
    path('accounts/profile/', acc_views.profile_view),

    # Plant Encyclopedia
    path('plants/', plant_views.plant_list, name='plant-list'),
    path('plants/<int:pk>/', plant_views.plant_detail, name='plant-detail'),

    # AI Plant Doctor
    path('ai/diagnose/', ai_views.diagnose_view, name='diagnose'),
    path('ai/diagnoses/<int:pk>/', ai_views.diagnosis_result, name='diagnosis-result'),
    path('ai/history/', ai_views.diagnosis_history, name='diagnosis-history'),
    path('ai/chatbot/', ai_views.chatbot_view, name='chatbot'),
    path('ai/chatbot/clear/', ai_views.chatbot_clear_view, name='chatbot-clear'),

    # Smart Care & My Plants
    path('care/plants/', care_views.my_plants, name='my-plants'),
    path('care/plants/add/', care_views.add_user_plant, name='add-user-plant'),
    path('care/plants/<int:pk>/', care_views.user_plant_detail, name='user-plant-detail'),
    path('care/calendar/', care_views.care_calendar_view, name='care-calendar'),
    path('care/tasks/<int:task_id>/toggle/', care_views.toggle_task_view, name='toggle-task'),
    path('care/plants/<int:plant_id>/photos/', care_views.add_plant_photo_view, name='add-plant-photo'),

    # Garden Services & Task Lifecycle
    path('services/gardens/', serv_views.garden_list, name='garden-list'),
    path('services/gardens/create/', serv_views.garden_create, name='garden-create'),
    path('services/gardens/<int:pk>/', serv_views.garden_detail, name='garden-detail'),
    path('services/gardens/<int:garden_id>/tasks/create/', serv_views.task_create, name='task-create'),
    path('services/tasks/<int:pk>/', serv_views.task_detail, name='task-detail'),
    path('services/gardens/<int:garden_id>/expenses/add/', serv_views.add_expense, name='add-expense'),
    path('services/professionals/', serv_views.gardener_directory, name='gardener-directory'),

    # Marketplace-Lite & Cash on Delivery Orders
    path('marketplace/', market_views.product_list, name='marketplace-products'),
    path('marketplace/products/<int:pk>/', market_views.product_detail, name='product-detail'),
    path('marketplace/cart/', market_views.cart_view, name='cart'),
    path('marketplace/cart/add/<int:pk>/', market_views.add_to_cart, name='add-to-cart'),
    path('marketplace/cart/remove/<int:pk>/', market_views.remove_from_cart, name='remove-from-cart'),
    path('marketplace/checkout/', market_views.checkout_view, name='checkout'),
    path('marketplace/orders/', market_views.order_list, name='order-list'),
    path('marketplace/orders/<int:pk>/', market_views.order_detail, name='order-detail'),
    path('marketplace/seller/dashboard/', market_views.seller_dashboard, name='seller-dashboard'),

    # Community Groups & Real-Time Chat
    path('community/', comm_views.community_home, name='community-home'),
    path('community/groups/<int:pk>/', comm_views.group_detail, name='group-detail'),
    path('community/rooms/<int:pk>/', comm_views.chat_room_view, name='chat-room'),
    path('community/direct/<int:user_id>/', comm_views.start_direct_chat, name='start-direct-chat'),

    # In-App Notification Center
    path('notifications/', notif_views.notification_list, name='notifications'),
    path('notifications/<int:pk>/read/', notif_views.mark_read, name='notification-read'),
    path('notifications/mark-all-read/', notif_views.mark_all_read, name='notification-mark-all-read'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
