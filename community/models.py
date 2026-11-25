from django.db import models
from django.conf import settings

class Group(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField()
    city = models.CharField(max_length=100, default='Lahore', db_index=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='groups/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def member_count(self):
        return self.memberships.count()

    @property
    def name_en(self):
        if '(' in self.name and ')' in self.name:
            import re
            m = re.search(r'\((.*?)\)', self.name)
            if m:
                return m.group(1).strip()
        if 'لاہور کچن گارڈننگ' in self.name:
            return "Lahore Kitchen Gardeners Club"
        return self.name

    @property
    def name_ur(self):
        if '(' in self.name:
            return self.name.split('(')[0].strip()
        return self.name

    def __str__(self):
        return f"{self.name} ({self.city})"


class GroupMembership(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='group_memberships')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')

    def __str__(self):
        return f"{self.user.username} in {self.group.name}"


class ChatRoom(models.Model):
    ROOM_TYPES = (
        ('DIRECT', 'Direct Message (راست پیغام)'),
        ('GARDEN_TEAM', 'Garden Team Chat (باغ ٹیم چیٹ)'),
        ('COMMUNITY', 'Public Community Chat (عوامی گروپ چیٹ)'),
    )

    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, default='COMMUNITY')
    name = models.CharField(max_length=150)
    garden = models.ForeignKey('services.Garden', on_delete=models.CASCADE, null=True, blank=True, related_name='chat_rooms')
    group = models.ForeignKey(Group, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_rooms')
    participant_one = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='direct_chats_as_p1')
    participant_two = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='direct_chats_as_p2')
    created_at = models.DateTimeField(auto_now_add=True)

    def can_access(self, user):
        """
        Direct chat: only participant_one or participant_two.
        Garden Team: members of the garden or garden owner.
        Community: any authenticated user.
        """
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        if self.room_type == 'DIRECT':
            return user == self.participant_one or user == self.participant_two
        if self.room_type == 'GARDEN_TEAM' and self.garden:
            return user == self.garden.owner or self.garden.members.filter(user=user).exists()
        if self.room_type == 'COMMUNITY':
            return True
        return False

    @property
    def name_en(self):
        if 'لاہور کچن گارڈننگ' in self.name:
            return "Lahore Kitchen Gardening Community"
        if self.room_type == 'GARDEN_TEAM' and self.garden:
            return f"Team Chat: {self.garden.name_en}"
        if self.room_type == 'DIRECT':
            p1 = self.participant_one.display_name_en if self.participant_one else "User"
            p2 = self.participant_two.display_name_en if self.participant_two else "User"
            return f"{p1} & {p2}"
        if '(' in self.name and ')' in self.name:
            import re
            m = re.search(r'\((.*?)\)', self.name)
            if m:
                return m.group(1).strip()
        return self.name

    @property
    def name_ur(self):
        if self.room_type == 'GARDEN_TEAM' and self.garden:
            return f"ٹیم چیٹ: {self.garden.name_ur}"
        if '(' in self.name:
            return self.name.split('(')[0].strip()
        return self.name

    @property
    def room_type_en(self):
        type_map = {
            'DIRECT': 'Direct Message',
            'GARDEN_TEAM': 'Garden Team Chat',
            'COMMUNITY': 'Public Community Chat',
        }
        return type_map.get(self.room_type, self.room_type)

    @property
    def room_type_ur(self):
        type_map = {
            'DIRECT': 'راست پیغام',
            'GARDEN_TEAM': 'باغ ٹیم چیٹ',
            'COMMUNITY': 'عوامی گروپ چیٹ',
        }
        return type_map.get(self.room_type, self.room_type)

    def __str__(self):
        return f"[{self.get_room_type_display()}] {self.name}"


class Message(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    image_attachment = models.ImageField(upload_to='chat_images/%Y/%m/', null=True, blank=True)
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.sender.username}: {self.content[:30]} ({self.created_at:%H:%M})"
