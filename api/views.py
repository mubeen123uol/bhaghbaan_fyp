from django.db import models
from rest_framework import generics, status, permissions, viewsets, serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, NotFound
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

from accounts.models import User, SellerProfile, DeviceToken
from plants.models import Plant, Disease
from ai_doctor.models import Diagnosis, ChatSession, ChatMessageAI
from ai_doctor.services import AIDoctorService
from care.models import UserPlant, CareTask, PlantPhoto, WeatherSnapshot
from care.services import CareCalendarService
from services.models import Garden, GardenMember, Task, Expense
from services.services import GardenService
from marketplace.models import Product, Order
from marketplace.services import MarketplaceService
from community.models import Group, GroupMembership, ChatRoom, Message
from community.services import CommunityService
from notifications.models import Notification

from .serializers import (
    UserSerializer, RegisterSerializer, SellerProfileSerializer, DeviceTokenSerializer,
    PlantSerializer, DiseaseSerializer, DiagnosisSerializer, ChatMessageAISerializer,
    UserPlantSerializer, CareTaskSerializer, PlantPhotoSerializer, WeatherSnapshotSerializer,
    GardenSerializer, TaskSerializer, ExpenseSerializer,
    ProductSerializer, OrderSerializer,
    GroupSerializer, ChatRoomSerializer, MessageSerializer,
    NotificationSerializer
)

# --- AUTH VIEWS ---
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class DeviceTokenAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = DeviceTokenSerializer

    def post(self, request):
        token_str = request.data.get('token')
        platform = request.data.get('platform', 'android')
        if not token_str:
            return Response({'error': 'Token is required'}, status=status.HTTP_400_BAD_REQUEST)
        token_obj, _ = DeviceToken.objects.update_or_create(
            user=request.user,
            defaults={'token': token_str, 'platform': platform}
        )
        return Response({'message': 'Device token registered successfully', 'platform': platform})


class SellerApplicationAPIView(generics.CreateAPIView):
    serializer_class = SellerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, verification_status='PENDING')


# --- PLANTS VIEWS ---
class PlantViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plant.objects.all().order_by('name_en')
    serializer_class = PlantSerializer
    search_fields = ['name_en', 'name_ur', 'name_roman', 'scientific_name', 'category']
    filterset_fields = ['category', 'is_indoor_suitable']


class DiseaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Disease.objects.all().order_by('name_en')
    serializer_class = DiseaseSerializer
    search_fields = ['name_en', 'name_ur', 'name_roman', 'symptoms_en', 'symptoms_ur']


# --- AI DOCTOR VIEWS ---
class DiagnosisViewSet(viewsets.ModelViewSet):
    queryset = Diagnosis.objects.all()
    serializer_class = DiagnosisSerializer
    parser_classes = [MultiPartParser, FormParser]
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):
            return Diagnosis.objects.none()
        if self.request.user.is_authenticated:
            return Diagnosis.objects.filter(user=self.request.user)
        return Diagnosis.objects.none()

    def create(self, request, *args, **kwargs):
        image = request.FILES.get('image')
        if not image:
            return Response({'error': 'An image file is required for diagnosis.'}, status=status.HTTP_400_BAD_REQUEST)

        # File size check <= 5MB
        if image.size > 5 * 1024 * 1024:
            return Response({'error': 'Image size exceeds maximum limit of 5.0 MB.'}, status=status.HTTP_400_BAD_REQUEST)

        lang = request.data.get('language', 'ur')
        city = request.data.get('city', request.user.city if request.user.is_authenticated else 'Lahore')

        try:
            diag = AIDoctorService.diagnose_image(request.user, image, language=lang, city=city)
            serializer = self.get_serializer(diag)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except ValueError as ve:
            return Response({'error': str(ve), 'is_plant': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f"Diagnosis processing error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def escalate(self, request, pk=None):
        diag = self.get_object()
        diag.is_escalated = True
        diag.save()
        return Response({'message': 'Diagnosis escalated to gardening community and experts.', 'is_escalated': True})


class ChatbotMessageAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=inline_serializer('ChatbotRequest', fields={'message': serializers.CharField(), 'session_id': serializers.IntegerField(required=False)}),
        responses={200: inline_serializer('ChatbotResponse', fields={'session_id': serializers.IntegerField(), 'reply': serializers.CharField()})}
    )
    def post(self, request):
        user_message = request.data.get('message', '').strip()
        session_id = request.data.get('session_id')
        if not user_message:
            return Response({'error': 'Message content cannot be blank'}, status=status.HTTP_400_BAD_REQUEST)

        session = None
        if session_id:
            session = ChatSession.objects.filter(id=session_id, user=request.user).first()
        if not session:
            session = ChatSession.objects.create(user=request.user)

        user_lang = getattr(request.user, 'preferred_language', 'en') or 'en'
        bot_reply = AIDoctorService.ask_chatbot(request.user, session.id, user_message, request_lang=user_lang)
        return Response({
            'session_id': session.id,
            'reply': bot_reply,
        })


# --- CARE & WEATHER VIEWS ---
class UserPlantViewSet(viewsets.ModelViewSet):
    queryset = UserPlant.objects.all()
    serializer_class = UserPlantSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return UserPlant.objects.none()
        return UserPlant.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        user_plant = serializer.save(user=self.request.user)
        CareCalendarService.generate_care_schedule(user_plant, days=30)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def photos(self, request, pk=None):
        user_plant = self.get_object()
        photo = request.FILES.get('photo')
        note = request.data.get('note', '')
        if not photo:
            return Response({'error': 'Photo file required'}, status=status.HTTP_400_BAD_REQUEST)
        p = PlantPhoto.objects.create(user_plant=user_plant, photo=photo, note=note)
        return Response(PlantPhotoSerializer(p).data, status=status.HTTP_201_CREATED)


class CareTaskViewSet(viewsets.ModelViewSet):
    queryset = CareTask.objects.all()
    serializer_class = CareTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return CareTask.objects.none()
        qs = CareTask.objects.filter(user_plant__user=self.request.user)
        date_param = self.request.query_params.get('date')
        if date_param:
            qs = qs.filter(scheduled_date=date_param)
        return qs

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        task = self.get_object()
        task.status = 'COMPLETED'
        from django.utils import timezone
        task.completed_at = timezone.now()
        task.save()
        return Response({'message': 'Task marked as completed.', 'status': 'COMPLETED'})


class LiveWeatherAPIView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = WeatherSnapshotSerializer

    def get(self, request):
        city = request.query_params.get('city', 'Lahore')
        snapshot = CareCalendarService.fetch_live_weather(city)
        return Response(WeatherSnapshotSerializer(snapshot).data)


# --- GARDEN SERVICES & TASKS VIEWS ---
class GardenViewSet(viewsets.ModelViewSet):
    queryset = Garden.objects.all()
    serializer_class = GardenSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Garden.objects.none()
        user = self.request.user
        return Garden.objects.filter(owner=user) | Garden.objects.filter(members__user=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def members(self, request, pk=None):
        garden = self.get_object()
        user_id = request.data.get('user_id')
        role = request.data.get('role', 'GARDENER')
        target_user = User.objects.get(id=user_id)
        gm, _ = GardenMember.objects.update_or_create(garden=garden, user=target_user, defaults={'role': role})
        return Response({'message': f"User {target_user.username} added as {role}"})


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Task.objects.none()
        garden_id = self.request.query_params.get('garden')
        if garden_id:
            return Task.objects.filter(garden_id=garden_id)
        user = self.request.user
        return Task.objects.filter(garden__owner=user) | Task.objects.filter(assigned_to=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], parser_classes=[MultiPartParser, FormParser, JSONParser])
    def transition(self, request, pk=None):
        task = self.get_object()
        new_state = request.data.get('state')
        notes = request.data.get('notes', '')
        photo = request.FILES.get('photo_proof')
        try:
            updated_task = GardenService.transition_task_state(task, new_state, request.user, notes, photo)
            return Response(TaskSerializer(updated_task).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


class ExpenseViewSet(viewsets.ModelViewSet):
    queryset = Expense.objects.all()
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Expense.objects.none()
        garden_id = self.request.query_params.get('garden')
        if garden_id:
            return Expense.objects.filter(garden_id=garden_id)
        return Expense.objects.filter(garden__owner=self.request.user)

    def perform_create(self, serializer):
        garden_id = self.request.data.get('garden')
        garden = Garden.objects.get(id=garden_id)
        serializer.save(garden=garden, recorded_by=self.request.user)


class NearbyProfessionalsAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: inline_serializer('NearbyProfResponse', fields={'user': UserSerializer(), 'distance_km': serializers.FloatField()}, many=True)})
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        role = request.query_params.get('role')
        city = request.query_params.get('city', 'Lahore')
        profs = GardenService.find_nearby_professionals(lat, lng, role=role, city=city)
        data = [{'user': UserSerializer(p['user']).data, 'distance_km': p['distance_km']} for p in profs]
        return Response(data)


# --- MARKETPLACE VIEWS ---
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(status='APPROVED', stock_quantity__gt=0).order_by('-created_at')
    serializer_class = ProductSerializer
    search_fields = ['title', 'description', 'category']
    filterset_fields = ['category']

    def perform_create(self, serializer):
        if not hasattr(self.request.user, 'seller_profile') or not self.request.user.seller_profile.is_approved():
            raise PermissionDenied("Only verified sellers can create product listings.")
        serializer.save(seller=self.request.user.seller_profile, status='APPROVED')


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Order.objects.none()
        user = self.request.user
        if hasattr(user, 'seller_profile'):
            return Order.objects.filter(items__seller=user.seller_profile).distinct()
        return Order.objects.filter(buyer=user)

    def create(self, request, *args, **kwargs):
        cart_items = request.data.get('items', [])
        addr = request.data.get('shipping_address')
        city = request.data.get('shipping_city')
        phone = request.data.get('contact_phone')

        try:
            order = MarketplaceService.create_cod_order(
                buyer=request.user,
                shipping_address=addr,
                shipping_city=city,
                contact_phone=phone,
                cart_items=cart_items
            )
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def status(self, request, pk=None):
        order = self.get_object()
        new_status = request.data.get('status')
        try:
            updated = MarketplaceService.update_order_status(order, new_status, request.user)
            return Response(OrderSerializer(updated).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# --- COMMUNITY VIEWS ---
class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all().order_by('-created_at')
    serializer_class = GroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        grp = serializer.save(creator=self.request.user)
        GroupMembership.objects.create(group=grp, user=self.request.user)
        ChatRoom.objects.create(room_type='COMMUNITY', group=grp, name=f"{grp.name} Chat")

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def join(self, request, pk=None):
        group = self.get_object()
        membership, created = GroupMembership.objects.get_or_create(group=group, user=request.user)
        return Response({'message': f"Joined group {group.name}", 'joined': True})


class NearbyGroupsAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(responses={200: inline_serializer('NearbyGroupResponse', fields={'group': GroupSerializer(), 'distance_km': serializers.FloatField()}, many=True)})
    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        city = request.query_params.get('city', 'Lahore')
        groups = CommunityService.find_nearby_groups(lat, lng, city=city)
        data = [{'group': GroupSerializer(g['group']).data, 'distance_km': g['distance_km']} for g in groups]
        return Response(data)


class ChatRoomViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ChatRoom.objects.all()
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return ChatRoom.objects.none()
        user = self.request.user
        return ChatRoom.objects.filter(
            models.Q(room_type='COMMUNITY') |
            models.Q(participant_one=user) |
            models.Q(participant_two=user) |
            models.Q(garden__owner=user) |
            models.Q(garden__members__user=user)
        ).distinct()


class RoomMessagesAPIView(generics.ListCreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Message.objects.none()
        room_id = self.kwargs.get('room_id')
        if not room_id:
            return Message.objects.none()
        room = ChatRoom.objects.get(id=room_id)
        if not room.can_access(self.request.user):
            raise PermissionDenied("You do not have access to this chat room.")
        return Message.objects.filter(room=room, is_hidden=False)

    def perform_create(self, serializer):
        room_id = self.kwargs.get('room_id')
        room = ChatRoom.objects.get(id=room_id)
        if not room.can_access(self.request.user):
            raise PermissionDenied("You do not have access to this chat room.")
        serializer.save(sender=self.request.user, room=room)


# --- NOTIFICATIONS VIEWS ---
class NotificationViewSet(viewsets.ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return Notification.objects.none()
        return Notification.objects.filter(recipient=self.request.user)

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notif = self.get_object()
        notif.is_read = True
        notif.save()
        return Response({'message': 'Marked as read', 'is_read': True})
