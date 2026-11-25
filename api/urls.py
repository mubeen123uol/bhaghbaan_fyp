from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from . import views

router = DefaultRouter()
router.register(r'plants', views.PlantViewSet, basename='plant')
router.register(r'diseases', views.DiseaseViewSet, basename='disease')
router.register(r'diagnoses', views.DiagnosisViewSet, basename='diagnosis')
router.register(r'my-plants', views.UserPlantViewSet, basename='userplant')
router.register(r'care-tasks', views.CareTaskViewSet, basename='caretask')
router.register(r'gardens', views.GardenViewSet, basename='garden')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'expenses', views.ExpenseViewSet, basename='expense')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'groups', views.GroupViewSet, basename='group')
router.register(r'rooms', views.ChatRoomViewSet, basename='chatroom')
router.register(r'notifications', views.NotificationViewSet, basename='notification')

urlpatterns = [
    # OpenAPI Schema & Interactive Docs
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='api:schema'), name='swagger-ui'),
    path('schema/redoc/', SpectacularRedocView.as_view(url_name='api:schema'), name='redoc'),

    # JWT Authentication Endpoints
    path('auth/register/', views.RegisterAPIView.as_view(), name='auth-register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', views.UserProfileAPIView.as_view(), name='auth-profile'),
    path('auth/device-token/', views.DeviceTokenAPIView.as_view(), name='auth-device-token'),
    path('auth/seller-apply/', views.SellerApplicationAPIView.as_view(), name='auth-seller-apply'),

    # AI Chatbot & Services
    path('chatbot/message/', views.ChatbotMessageAPIView.as_view(), name='chatbot-message'),
    path('care/weather/', views.LiveWeatherAPIView.as_view(), name='live-weather'),
    path('professionals/nearby/', views.NearbyProfessionalsAPIView.as_view(), name='nearby-professionals'),
    path('groups/nearby/', views.NearbyGroupsAPIView.as_view(), name='nearby-groups'),
    path('rooms/<int:room_id>/messages/', views.RoomMessagesAPIView.as_view(), name='room-messages'),

    # Router endpoints
    path('', include(router.urls)),
]
