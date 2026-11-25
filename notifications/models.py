from django.db import models
from django.conf import settings

class Notification(models.Model):
    TYPE_CHOICES = (
        ('CARE_REMINDER', 'Care Reminder / پودوں کی دیکھ بھال'),
        ('TASK_UPDATE', 'Task Update / کام کی اپڈیٹ'),
        ('ORDER_UPDATE', 'Order Update / آرڈر کی تفصیل'),
        ('CHAT_MESSAGE', 'New Message / نیا پیغام'),
        ('SYSTEM', 'System Alert / سسٹم الرٹ'),
    )

    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=TYPE_CHOICES, default='CARE_REMINDER')
    title = models.CharField(max_length=200)
    body = models.TextField()
    target_url = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"
