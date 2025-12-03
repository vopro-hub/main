# Example: in wallet/signals.py or in pay_per_success.py after successful deduction
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json

def send_wallet_update(user, wallet):
    """Broadcast wallet updates via WebSocket."""
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(
        f"user_{user.id}",  # group name based on user id
        {
            "type": "wallet.update",
            "event": "wallet_update",
            "data": {
                "balance": wallet.balance,
                "reserved": wallet.reserved,
                "available": wallet.available,
            },
        },
    )
