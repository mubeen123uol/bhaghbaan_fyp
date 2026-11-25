from django.contrib import admin
from .models import AISetting, Diagnosis, ChatSession, ChatMessageAI

@admin.register(AISetting)
class AISettingAdmin(admin.ModelAdmin):
    list_display = ('id', 'confidence_threshold', 'daily_quota_limit', 'provider_priority', 'is_active', 'updated_at')

@admin.register(Diagnosis)
class DiagnosisAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'detected_disease', 'detected_species', 'confidence', 'is_confident', 'provider_used', 'is_escalated', 'created_at')
    list_filter = ('is_confident', 'is_escalated', 'provider_used')
    search_fields = ('detected_species', 'detected_disease', 'advice_ur', 'user__username')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'session_title', 'created_at')

@admin.register(ChatMessageAI)
class ChatMessageAIAdmin(admin.ModelAdmin):
    list_display = ('session', 'is_user', 'text', 'created_at')
    list_filter = ('is_user',)
