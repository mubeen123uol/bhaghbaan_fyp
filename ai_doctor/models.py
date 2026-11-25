from django.db import models
from django.conf import settings

class AISetting(models.Model):
    provider_priority = models.CharField(max_length=100, default='PLANT_ID_THEN_GEMINI')
    confidence_threshold = models.FloatField(default=60.0)
    daily_quota_limit = models.PositiveIntegerField(default=1000)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AI Config (Threshold: {self.confidence_threshold}%, Priority: {self.provider_priority})"


class Diagnosis(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='diagnoses')
    image = models.ImageField(upload_to='diagnoses/%Y/%m/')
    image_hash = models.CharField(max_length=64, db_index=True)
    detected_species = models.CharField(max_length=150, blank=True)
    detected_disease = models.CharField(max_length=150, blank=True)
    confidence = models.FloatField(default=0.0)
    is_confident = models.BooleanField(default=True)
    provider_used = models.CharField(max_length=50, default='GEMINI_VISION')
    advice_en = models.TextField(blank=True)
    advice_ur = models.TextField(blank=True)
    advice_roman = models.TextField(blank=True)
    is_escalated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Diagnosis #{self.id}: {self.detected_disease or 'Unknown'} ({self.confidence:.1f}%)"


class ChatSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chat_sessions')
    session_title = models.CharField(max_length=150, default='Gardening Chat / باغبانی مشورہ')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.session_title}"


class ChatMessageAI(models.Model):
    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    is_user = models.BooleanField(default=True)
    text = models.TextField()
    audio_file = models.FileField(upload_to='chat_audio/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender = "User" if self.is_user else "Baghbaan Bot"
        return f"[{sender}] {self.text[:40]}"
