import math
from .models import Group, ChatRoom, Message
from services.services import GardenService

class CommunityService:
    @classmethod
    def find_nearby_groups(cls, user_lat, user_lon, max_distance_km=30.0, city='Lahore'):
        """
        Find gardening community groups within radial distance or in same city.
        """
        groups = Group.objects.all()
        results = []

        for grp in groups:
            if grp.latitude and grp.longitude and user_lat and user_lon:
                dist = GardenService.haversine_distance(user_lat, user_lon, grp.latitude, grp.longitude)
                if dist <= max_distance_km:
                    results.append({'group': grp, 'distance_km': round(dist, 1)})
            elif grp.city and city and grp.city.lower() == city.lower():
                results.append({'group': grp, 'distance_km': 5.0})
            else:
                results.append({'group': grp, 'distance_km': 15.0})

        results.sort(key=lambda x: x['distance_km'])
        return results

    @classmethod
    def get_or_create_direct_room(cls, user_a, user_b):
        """
        Retrieves or creates a 1-to-1 direct chat room between two users.
        """
        p1, p2 = (user_a, user_b) if user_a.id < user_b.id else (user_b, user_a)
        room = ChatRoom.objects.filter(
            room_type='DIRECT',
            participant_one=p1,
            participant_two=p2
        ).first()

        if not room:
            room = ChatRoom.objects.create(
                room_type='DIRECT',
                name=f"{p1.username} & {p2.username}",
                participant_one=p1,
                participant_two=p2
            )
        return room
