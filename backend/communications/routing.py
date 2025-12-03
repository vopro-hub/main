from django.urls import re_path
from .consumers import RoomChatConsumer, CityLobbyChatConsumer, PresenceConsumer, CityPresenceConsumer, PublicPresenceConsumer

websocket_urlpatterns = [
    re_path(r"ws/chat/office/(?P<room_id>\d+)/$", RoomChatConsumer.as_asgi()),
    re_path(r"ws/chat/city/(?P<lobby_id>\d+)/$", CityLobbyChatConsumer.as_asgi()),
    
    re_path(r"ws/presence/office/(?P<office_id>\d+)/$", PresenceConsumer.as_asgi()),
    re_path(r"ws/presence/city/(?P<city_id>\d+)/$", CityPresenceConsumer.as_asgi()),
    
    re_path(r"ws/public/offices/(?P<slug>[^/]+)/presence/$", PublicPresenceConsumer.as_asgi()),
]
