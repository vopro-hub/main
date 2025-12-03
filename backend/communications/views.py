from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
from django.http import JsonResponse, HttpResponse
from rest_framework import generics, permissions
from .models import RoomChatMessage, CityLobbyChatMessage, CommunicationLog, SMSMessage, EmailMessage
from .serializers import RoomChatMessageSerializer, CityLobbyChatMessageSerializer, CommunicationLogSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .tasks import send_sms_task, send_email_task, classify_and_autoreply

# -------------------------------
# ROOM CHAT
# -------------------------------
class RoomChatView(generics.ListCreateAPIView):
    serializer_class = RoomChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        room_id = self.kwargs["room_id"]
        return RoomChatMessage.objects.filter(room_id=room_id)

    def perform_create(self, serializer):
        room_id = self.kwargs["room_id"]
        serializer.save(user=self.request.user, room_id=room_id)


# -------------------------------
# CITY LOBBY CHAT
# -------------------------------
class CityLobbyChatView(generics.ListCreateAPIView):
    serializer_class = CityLobbyChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        lobby_id = self.kwargs["lobby_id"]
        return CityLobbyChatMessage.objects.filter(city_lobby_id=lobby_id)

    def perform_create(self, serializer):
        lobby_id = self.kwargs["lobby_id"]
        serializer.save(user=self.request.user, city_lobby_id=lobby_id)



class SendSMSView(APIView):
    def post(self, request):
        office_id = request.data.get("office_id")
        to = request.data.get("to")
        body = request.data.get("body") or ""
        media = request.data.get("media")  # optional list

        if not to:
            return Response({"error":"Missing 'to'"}, status=400)

        log = CommunicationLog.objects.create(office_id=office_id, type="sms", direction="outbound", status="queued", payload={})
        # enqueue
        send_sms_task.delay(log.id, to, body, media)
        return Response({"ok": True, "log_id": log.id}, status=201)

class SendEmailView(APIView):
    def post(self, request):
        office_id = request.data.get("office_id")
        to = request.data.get("to")  # list or string
        subject = request.data.get("subject","")
        body_text = request.data.get("body_text","")
        body_html = request.data.get("body_html","")
        log = CommunicationLog.objects.create(office_id=office_id, type="email", direction="outbound", status="queued", payload={})
        send_email_task.delay(log.id, to, subject, body_text, body_html)
        return Response({"ok": True, "log_id": log.id}, status=201)

class CommunicationLogList(generics.ListAPIView):
    serializer_class = CommunicationLogSerializer
    def get_queryset(self):
        office_id = self.request.query_params.get("office_id")
        qs = CommunicationLog.objects.all().order_by("-created_at")
        if office_id:
            qs = qs.filter(office_id=office_id)
        # optional filters: type, direction, date range
        t = self.request.query_params.get("type")
        if t:
            qs = qs.filter(type=t)
        return qs

# -------------------------------
# AUTO-REPLY INBOUND HANDLERS
# -------------------------------


@csrf_exempt
def twilio_inbound_sms(request):
    """Handles incoming SMS from Twilio and triggers AI auto-reply."""
    from_number = request.POST.get("From")
    to_number = request.POST.get("To")
    body = request.POST.get("Body", "")

    if not body:
        return HttpResponse("Missing Body", status=400)

    # 1️⃣ Create inbound communication log
    log = CommunicationLog.objects.create(
        type="sms",
        direction="inbound",
        status="received",
        payload={
            "from": from_number,
            "to": to_number,
            "body": body,
        },
    )

    # 2️⃣ Save SMS record
    SMSMessage.objects.create(
        log=log,
        from_number=from_number,
        to_number=to_number,
        body=body,
        received_at=now(),
    )

    # 3️⃣ Trigger AI classification + auto-reply
    classify_and_autoreply.delay(log.id)

    return HttpResponse("OK", status=200)


@csrf_exempt
def inbound_email_webhook(request):
    """Handles incoming email webhooks and triggers AI auto-reply."""
    from_email = request.POST.get("from")
    to_email = request.POST.get("to")
    subject = request.POST.get("subject", "")
    body_text = request.POST.get("text", "")
    body_html = request.POST.get("html", "")

    if not (body_text or body_html):
        return HttpResponse("Missing email body", status=400)

    # 1️⃣ Create inbound log
    log = CommunicationLog.objects.create(
        type="email",
        direction="inbound",
        status="received",
        payload={
            "from": from_email,
            "to": to_email,
            "subject": subject,
            "preview": body_text[:200],
        },
    )

    # 2️⃣ Save email message
    EmailMessage.objects.create(
        log=log,
        from_email=from_email,
        to_emails=to_email,
        subject=subject,
        body_text=body_text,
        body_html=body_html,
        received_at=now(),
    )

    # 3️⃣ Trigger AI classification + auto-reply
    classify_and_autoreply.delay(log.id)

    return JsonResponse({"status": "received"})
