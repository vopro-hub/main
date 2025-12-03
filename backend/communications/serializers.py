from rest_framework import serializers
from .models import RoomChatMessage, CityLobbyChatMessage, CommunicationLog, SMSMessage, VoiceCall, EmailMessage



class RoomChatMessageSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = RoomChatMessage
        fields = ["id", "room", "user", "content", "created_at"]


class CityLobbyChatMessageSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = CityLobbyChatMessage
        fields = ["id", "city_lobby", "user", "content", "created_at"]

class SMSMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMSMessage
        fields = "__all__"

class VoiceCallSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoiceCall
        fields = "__all__"

class EmailMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailMessage
        fields = "__all__"

class CommunicationLogSerializer(serializers.ModelSerializer):
    sms_messages = SMSMessageSerializer(many=True, read_only=True)
    voice_calls = VoiceCallSerializer(many=True, read_only=True)
    emails = EmailMessageSerializer(many=True, read_only=True)
    class Meta:
        model = CommunicationLog
        fields = "__all__"
