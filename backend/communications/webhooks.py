from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .models import CommunicationLog, SMSMessage, VoiceCall, EmailMessage
from django.utils import timezone
from twilio.request_validator import RequestValidator
from django.conf import settings
import json

@csrf_exempt
def twilio_sms_webhook(request):
    # Validate signature (recommended)
    validator = RequestValidator(settings.TWILIO_AUTH_TOKEN)
    signature = request.META.get("HTTP_X_TWILIO_SIGNATURE","")
    url = request.build_absolute_uri()
    params = request.POST.dict()
    if not validator.validate(url, params, signature):
        return HttpResponse(status=403)

    from_number = request.POST.get("From")
    to_number = request.POST.get("To")
    body = request.POST.get("Body","")
    media = []
    num_media = int(request.POST.get("NumMedia","0"))
    for i in range(num_media):
        media.append(request.POST.get(f"MediaUrl{i}"))

    log = CommunicationLog.objects.create(type="sms", direction="inbound", status="received", payload=params)
    SMSMessage.objects.create(log=log, from_number=from_number, to_number=to_number, body=body, media=media)
    # Optionally: dispatch AI classification or push to WebSocket
    return HttpResponse("OK")

@csrf_exempt
def twilio_call_webhook(request):
    # handle call status & recordings (validate signature similarly)
    data = request.POST.dict()
    call_sid = data.get("CallSid")
    from_number = data.get("From")
    to_number = data.get("To")
    status = data.get("CallStatus")
    # create or update log
    log, _ = CommunicationLog.objects.get_or_create(provider_id=call_sid, defaults={"type":"voice","direction":"inbound"})
    VoiceCall.objects.create(log=log, from_number=from_number, to_number=to_number, status=status)
    return HttpResponse("OK")

@csrf_exempt
def sendgrid_inbound(request):
    # SendGrid posts raw email data. Validate using SendGrid verification as desired.
    try:
        attachments = []
        # Save minimal fields
        data = request.POST.dict()
        from_email = data.get("from")
        to_email = data.get("to")
        subject = data.get("subject","")
        text = data.get("text","")
        html = data.get("html","")
        log = CommunicationLog.objects.create(type="email", direction="inbound", status="received", payload=data)
        EmailMessage.objects.create(log=log, from_email=from_email, to_emails=[to_email], subject=subject, body_text=text, body_html=html, attachments=attachments)
    except Exception:
        return HttpResponse(status=400)
    return HttpResponse("OK")
