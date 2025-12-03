
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_presence(worker, action):
    channel_layer = get_channel_layer()
    payload = {
        "type": "presence_update",
        "action": action,  # "login" or "logout"
        "worker": {
            "id": worker.id,
            "work_id": worker.worker_id,
            "name": worker.name,
            "rooms": list(worker.rooms.values_list("id", flat=True)),
        }
    }
    async_to_sync(channel_layer.group_send)(
        f"public_office_{worker.office.public_slug}",
        {
            "type": "presence.broadcast",
            "payload": payload,
        },
    )
