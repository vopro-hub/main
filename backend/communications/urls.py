from django.urls import path
from . import webhooks, views

urlpatterns = [
    path("rooms/<int:room_id>/chat/", views.RoomChatView.as_view(), name="room-chat"),
    path("city-lobbies/<int:lobby_id>/chat/", views.CityLobbyChatView.as_view(), name="city-lobby-chat"),
    path("sms/send/", views.SendSMSView.as_view()),
    path("email/send/", views.SendEmailView.as_view()),
    path("logs/", views.CommunicationLogList.as_view()),
    path("webhook/twilio/sms/", webhooks.twilio_sms_webhook),
    path("webhook/twilio/call/", webhooks.twilio_call_webhook),
    path("webhook/sendgrid/inbound/", webhooks.sendgrid_inbound),
]
