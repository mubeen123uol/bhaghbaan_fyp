from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from accounts.models import User, SellerProfile, DeviceToken
from plants.models import Plant, Disease, Treatment
from ai_doctor.models import Diagnosis, ChatSession, ChatMessageAI
from care.models import UserPlant, CareTask, PlantPhoto, WeatherSnapshot
from services.models import Garden, GardenMember, Task, TaskReport, Expense
from marketplace.models import Product, Order, OrderItem
from community.models import Group, ChatRoom, Message
from notifications.models import Notification

# --- ACCOUNTS SERIALIZERS ---
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'phone', 
                  'city', 'latitude', 'longitude', 'preferred_language', 'bio', 
                  'is_verified_professional', 'years_of_experience', 'hourly_rate', 'created_at')
        read_only_fields = ('id', 'created_at', 'is_verified_professional')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role', 'phone', 'city', 'latitude', 'longitude', 'preferred_language')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            role=validated_data.get('role', 'HOMEOWNER'),
            phone=validated_data.get('phone'),
            city=validated_data.get('city', 'Lahore'),
            latitude=validated_data.get('latitude'),
            longitude=validated_data.get('longitude'),
            preferred_language=validated_data.get('preferred_language', 'ur')
        )
        return user


class SellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = '__all__'
        read_only_fields = ('user', 'verification_status', 'created_at')


class DeviceTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceToken
        fields = ('token', 'platform')


# --- PLANTS SERIALIZERS ---
class TreatmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Treatment
        fields = '__all__'


class DiseaseSerializer(serializers.ModelSerializer):
    treatments = TreatmentSerializer(many=True, read_only=True)

    class Meta:
        model = Disease
        fields = '__all__'


class PlantSerializer(serializers.ModelSerializer):
    diseases = DiseaseSerializer(many=True, read_only=True)

    class Meta:
        model = Plant
        fields = '__all__'


# --- AI DOCTOR SERIALIZERS ---
class DiagnosisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Diagnosis
        fields = '__all__'
        read_only_fields = ('user', 'image_hash', 'detected_species', 'detected_disease', 
                            'confidence', 'is_confident', 'provider_used', 'advice_en', 
                            'advice_ur', 'advice_roman', 'is_escalated', 'created_at')


class ChatMessageAISerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessageAI
        fields = ('id', 'is_user', 'text', 'created_at')


# --- CARE & WEATHER SERIALIZERS ---
class CareTaskSerializer(serializers.ModelSerializer):
    plant_nickname = serializers.CharField(source='user_plant.nickname', read_only=True)
    task_type_display = serializers.CharField(source='get_task_type_display', read_only=True)

    class Meta:
        model = CareTask
        fields = '__all__'
        read_only_fields = ('user_plant', 'scheduled_date', 'task_type')


class PlantPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlantPhoto
        fields = '__all__'
        read_only_fields = ('user_plant', 'taken_at')


class UserPlantSerializer(serializers.ModelSerializer):
    care_tasks = CareTaskSerializer(many=True, read_only=True)
    health_photos = PlantPhotoSerializer(many=True, read_only=True)
    plant_details = PlantSerializer(source='plant_template', read_only=True)

    class Meta:
        model = UserPlant
        fields = '__all__'
        read_only_fields = ('user', 'created_at')


class WeatherSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeatherSnapshot
        fields = '__all__'


# --- SERVICES & TASKS SERIALIZERS ---
class TaskReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskReport
        fields = '__all__'
        read_only_fields = ('task', 'submitted_at', 'reviewed_at')


class TaskSerializer(serializers.ModelSerializer):
    report = TaskReportSerializer(read_only=True)
    assigned_to_name = serializers.CharField(source='assigned_to.username', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = Task
        fields = '__all__'
        read_only_fields = ('created_by', 'created_at', 'updated_at')


class ExpenseSerializer(serializers.ModelSerializer):
    recorded_by_name = serializers.CharField(source='recorded_by.username', read_only=True)

    class Meta:
        model = Expense
        fields = '__all__'
        read_only_fields = ('garden', 'recorded_by', 'created_at')


class GardenMemberSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)

    class Meta:
        model = GardenMember
        fields = '__all__'
        read_only_fields = ('garden', 'joined_at')


class GardenSerializer(serializers.ModelSerializer):
    members = GardenMemberSerializer(many=True, read_only=True)
    total_expenses = serializers.FloatField(read_only=True)
    remaining_budget = serializers.FloatField(read_only=True)

    class Meta:
        model = Garden
        fields = '__all__'
        read_only_fields = ('owner', 'created_at')


# --- MARKETPLACE SERIALIZERS ---
class ProductSerializer(serializers.ModelSerializer):
    seller_name = serializers.CharField(source='seller.business_name', read_only=True)

    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ('seller', 'status', 'created_at')


class OrderItemSerializer(serializers.ModelSerializer):
    product_title = serializers.CharField(source='product.title', read_only=True)

    class Meta:
        model = OrderItem
        fields = '__all__'


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('buyer', 'status', 'subtotal', 'delivery_fee', 'total_amount', 'created_at')


# --- COMMUNITY & CHAT SERIALIZERS ---
class GroupSerializer(serializers.ModelSerializer):
    member_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = '__all__'
        read_only_fields = ('creator', 'created_at')


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = '__all__'
        read_only_fields = ('sender', 'room', 'is_hidden', 'created_at')


class ChatRoomSerializer(serializers.ModelSerializer):
    latest_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatRoom
        fields = '__all__'

    @extend_schema_field(MessageSerializer)
    def get_latest_message(self, obj):
        last = obj.messages.filter(is_hidden=False).last()
        return MessageSerializer(last).data if last else None


# --- NOTIFICATIONS SERIALIZERS ---
class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = ('recipient', 'created_at')
