import json
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from workspace.models import Presence, Office, WorkerPresence
from .models import RoomChatMessage, CityLobbyChatMessage
from asgiref.sync import sync_to_async


# ------------------------------------
# ROOM CHAT CONSUMER
# ------------------------------------
class RoomChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope["url_route"]["kwargs"]["room_id"]
        self.group_name = f"room_chat_{self.room_id}"

        if not self.scope.get("user") or isinstance(self.scope["user"], AnonymousUser):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content", "").strip()
        if not content:
            return

        msg = await self.save_message(self.scope["user"].id, int(self.room_id), content)
        payload = {
            "type": "chat.message",
            "user": self.scope["user"].username,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        await self.channel_layer.group_send(
            self.group_name, {"type": "broadcast", "payload": payload}
        )

    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def save_message(self, user_id, room_id, content):
        return RoomChatMessage.objects.create(user_id=user_id, room_id=room_id, content=content)


# ------------------------------------
# CITY LOBBY CHAT CONSUMER
# ------------------------------------
class CityLobbyChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.lobby_id = self.scope["url_route"]["kwargs"]["lobby_id"]
        self.group_name = f"city_lobby_chat_{self.lobby_id}"

        if not self.scope.get("user") or isinstance(self.scope["user"], AnonymousUser):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        content = data.get("content", "").strip()
        if not content:
            return

        msg = await self.save_message(self.scope["user"].id, int(self.lobby_id), content)
        payload = {
            "type": "chat.message",
            "user": self.scope["user"].username,
            "content": msg.content,
            "created_at": msg.created_at.isoformat(),
        }
        await self.channel_layer.group_send(
            self.group_name, {"type": "broadcast", "payload": payload}
        )

    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    @database_sync_to_async
    def save_message(self, user_id, lobby_id, content):
        return CityLobbyChatMessage.objects.create(
            user_id=user_id, city_lobby_id=lobby_id, content=content
        )


# ------------------------------------
# PRESENCE (same as before)
# ------------------------------------
class PresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.office_id = int(self.scope["url_route"]["kwargs"]["office_id"])
        self.group_name = f"presence_{self.office_id}"

        if not self.scope.get("user") or isinstance(self.scope["user"], AnonymousUser):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.update_presence("online")
        await self.broadcast_presence_list()

    async def disconnect(self, code):
        await self.update_presence("offline")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.broadcast_presence_list()

    async def receive(self, text_data):
        data = json.loads(text_data) if text_data else {}
        status = data.get("status", "online")
        await self.update_presence(status)
        await self.broadcast_presence_list()

    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    async def broadcast_presence_list(self):
        users = await self.get_online_users()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast",
                "payload": {"type": "presence.list", "users": users},
            },
        )

    @database_sync_to_async
    def update_presence(self, status):
        Presence.objects.update_or_create(
            office_id=self.office_id,
            user_id=self.scope["user"].id,
            defaults={"status": status},
        )

    @database_sync_to_async
    def get_online_users(self):
        return list(
            Presence.objects.filter(office_id=self.office_id, status="online")
            .values_list("user__username", flat=True)
        )


# consumers.py (add this below PresenceConsumer)
class CityPresenceConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.city_id = int(self.scope["url_route"]["kwargs"]["city_id"])
        self.group_name = f"city_presence_{self.city_id}"

        if not self.scope.get("user") or isinstance(self.scope["user"], AnonymousUser):
            await self.close()
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        await self.update_presence("online")
        await self.broadcast_presence_list()

    async def disconnect(self, code):
        await self.update_presence("offline")
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        await self.broadcast_presence_list()

    async def receive(self, text_data):
        data = json.loads(text_data) if text_data else {}
        status = data.get("status", "online")
        await self.update_presence(status)
        await self.broadcast_presence_list()

    async def broadcast(self, event):
        await self.send(text_data=json.dumps(event["payload"]))

    async def broadcast_presence_list(self):
        users = await self.get_online_users()
        await self.channel_layer.group_send(
            self.group_name,
            {
                "type": "broadcast",
                "payload": {"type": "presence.list", "users": users},
            },
        )

    @database_sync_to_async
    def update_presence(self, status):
        Presence.objects.update_or_create(
            city_id=self.city_id,     # ✅ requires adding city_id field
            user_id=self.scope["user"].id,
            defaults={"status": status},
        )

    @database_sync_to_async
    def get_online_users(self):
        return list(
            Presence.objects.filter(city_id=self.city_id, status="online")
            .values_list("user__username", flat=True)
        )




class PublicPresenceConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.slug = self.scope["url_route"]["kwargs"]["slug"]
        try:
            office = await sync_to_async(Office.objects.get)(public_slug=self.slug, public=True)
        except Office.DoesNotExist:
            await self.close()
            return

        self.office = office
        self.group_name = f"public_office_{self.slug}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # Send snapshot of all workers currently present
        presences = await sync_to_async(list)(
            WorkerPresence.objects.filter(worker__office=office, is_presence=True)
            .select_related("worker")
        )
        workers_data = [
            {
                "id": p.worker.id,
                "worker_id": p.worker.worker_id,
                "name": p.worker.name,
                "rooms": list(p.worker.rooms.values_list("id", flat=True)),
                "last_login": p.last_login.isoformat() if p.last_login else None,
            }
            for p in presences
        ]
        await self.send_json({"type": "worker.presence", "workers": workers_data})

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        # Public WS is read-only, so ignore
        pass

    async def presence_broadcast(self, event):
        await self.send_json(event["payload"])
