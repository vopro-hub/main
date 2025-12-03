from django.db import models
from django.conf import settings
from workspace.models import Office, Room, cityLobby
from django.contrib.postgres.fields import JSONField  # or use models.JSONField in modern Django


class RoomChatMessage(models.Model):
    
    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name="chat_messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[Room: {self.room.name}] {self.user.username}: {self.content[:20]}"


class CityLobbyChatMessage(models.Model):
    city_lobby = models.ForeignKey(cityLobby, on_delete=models.CASCADE, related_name="chat_messages")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"[CityLobby: {self.city_lobby.city.city}] {self.user.username}: {self.content[:20]}"


class CommunicationLog(models.Model):
    OFFICE = "office"
    COMM_TYPES = [
      ("voice","voice"),
      ("sms","sms"),
      ("email","email"),
    ]
    office = models.ForeignKey("workspace.Office", on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=10, choices=COMM_TYPES)
    direction = models.CharField(max_length=10, choices=[("inbound","inbound"),("outbound","outbound")])
    provider_id = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(max_length=50, blank=True, null=True)
    payload = models.JSONField(default=dict)  # raw provider payload
    created_at = models.DateTimeField(auto_now_add=True)
    staff = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    visitor_identifier = models.CharField(max_length=200, blank=True, null=True)

class SMSMessage(models.Model):
    log = models.ForeignKey(CommunicationLog, on_delete=models.CASCADE, related_name="sms_messages")
    from_number = models.CharField(max_length=100)
    to_number = models.CharField(max_length=100)
    body = models.TextField(blank=True)
    media = models.JSONField(default=list)  # list of urls
    received_at = models.DateTimeField(auto_now_add=True)

class VoiceCall(models.Model):
    log = models.ForeignKey(CommunicationLog, on_delete=models.CASCADE, related_name="voice_calls")
    from_number = models.CharField(max_length=100)
    to_number = models.CharField(max_length=100)
    status = models.CharField(max_length=50, blank=True, null=True)
    recording_url = models.URLField(blank=True, null=True)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)

class EmailMessage(models.Model):
    log = models.ForeignKey(CommunicationLog, on_delete=models.CASCADE, related_name="emails")
    from_email = models.CharField(max_length=200)
    to_emails = models.JSONField(default=list)
    subject = models.CharField(max_length=400, blank=True)
    body_text = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    attachments = models.JSONField(default=list)
    received_at = models.DateTimeField(auto_now_add=True)
