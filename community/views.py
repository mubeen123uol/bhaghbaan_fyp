from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Group, GroupMembership, ChatRoom, Message
from .services import CommunityService
from accounts.models import User

@login_required
def community_home(request):
    user = request.user
    user_groups = Group.objects.filter(memberships__user=user)
    nearby_groups = CommunityService.find_nearby_groups(user.latitude, user.longitude, city=user.city)
    
    # Active Chat rooms for user
    chat_rooms = ChatRoom.objects.filter(
        Q(room_type='COMMUNITY') |
        Q(participant_one=user) |
        Q(participant_two=user) |
        Q(garden__owner=user) |
        Q(garden__members__user=user)
    ).distinct()

    return render(request, 'community/community_home.html', {
        'user_groups': user_groups,
        'nearby_groups': nearby_groups,
        'chat_rooms': chat_rooms,
    })

@login_required
def group_detail(request, pk):
    group = get_object_or_404(Group, pk=pk)
    is_member = group.memberships.filter(user=request.user).exists()
    members = group.memberships.all()
    chat_room = group.chat_rooms.first()

    if request.method == 'POST' and 'join_group' in request.POST:
        GroupMembership.objects.get_or_create(group=group, user=request.user)
        messages.success(request, f"آپ گروپ '{group.name}' میں شامل ہو چکے ہیں!")
        return redirect('group-detail', pk=group.pk)

    return render(request, 'community/group_detail.html', {
        'group': group,
        'is_member': is_member,
        'members': members,
        'chat_room': chat_room,
    })

@login_required
def chat_room_view(request, pk):
    room = get_object_or_404(ChatRoom, pk=pk)
    if not room.can_access(request.user):
        messages.error(request, "آپ کو اس چیٹ روم تک رسائی کی اجازت نہیں ہے۔")
        return redirect('community-home')

    messages_list = room.messages.filter(is_hidden=False)[:50]

    # Handle standard HTTP form submission (fallback for WebSockets)
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image = request.FILES.get('image_attachment')
        if content or image:
            Message.objects.create(
                room=room,
                sender=request.user,
                content=content,
                image_attachment=image
            )
            return redirect('chat-room', pk=room.pk)

    return render(request, 'community/chat_room.html', {
        'room': room,
        'chat_messages': messages_list,
    })

@login_required
def start_direct_chat(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    if target_user == request.user:
        messages.warning(request, "آپ خود سے چیٹ شروع نہیں کر سکتے۔")
        return redirect('community-home')

    room = CommunityService.get_or_create_direct_room(request.user, target_user)
    return redirect('chat-room', pk=room.pk)
