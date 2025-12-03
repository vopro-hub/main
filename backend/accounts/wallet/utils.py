from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .serializers import UserWalletSerializer
from .models import UserWallet

def send_wallet_update(user):
    layer = get_channel_layer()
    wallet = UserWallet.objects.get(user=user)
    data = UserWalletSerializer(wallet).data
    async_to_sync(layer.group_send)(
        f"wallet_{user.id}",
        {"type": "wallet.update", "wallet": data},
    )
