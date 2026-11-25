from django.contrib import admin
from .models import Group, GroupMembership, ChatRoom, Message

class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1

@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'creator', 'member_count', 'created_at')
    search_fields = ('name', 'description', 'city')
    inlines = [GroupMembershipInline]

@admin.register(ChatRoom)
class ChatRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'room_type', 'group', 'garden', 'created_at')
    list_filter = ('room_type',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'room', 'sender', 'content', 'is_hidden', 'created_at')
    list_filter = ('is_hidden', 'room__room_type')
    search_fields = ('content', 'sender__username')
    actions = ['hide_messages', 'unhide_messages']

    def hide_messages(self, request, queryset):
        queryset.update(is_hidden=True)
    hide_messages.short_description = "Hide selected messages (Moderate)"

    def unhide_messages(self, request, queryset):
        queryset.update(is_hidden=False)
    unhide_messages.short_description = "Unhide selected messages"
