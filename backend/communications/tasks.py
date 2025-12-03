from celery import shared_task
from django.conf import settings
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from aistaff.services.ai_secretary import AIOfficeAssistant
from .models import CommunicationLog


# ---------------------------------------------------------------------
# 📞 SMS Sending
# ---------------------------------------------------------------------
@shared_task(bind=True, max_retries=3)
def send_sms_task(self, log_id, to, body, media=None):
    """Send outbound SMS via Twilio"""
    log = CommunicationLog.objects.get(pk=log_id)
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    try:
        msg = client.messages.create(
            from_=settings.TWILIO_NUMBER,
            to=to,
            body=body,
            media_url=media or None,
        )
        log.provider_id = msg.sid
        log.status = "sent"
        log.payload = {**(log.payload or {}), "twilio_sid": msg.sid}
        log.save(update_fields=["provider_id", "status", "payload"])
    except Exception as e:
        log.status = "error"
        log.payload = {**(log.payload or {}), "error": str(e)}
        log.save(update_fields=["status", "payload"])
        raise self.retry(exc=e, countdown=30)


# ---------------------------------------------------------------------
# 📧 Email Sending
# ---------------------------------------------------------------------
@shared_task(bind=True, max_retries=2)
def send_email_task(self, log_id, to_emails, subject, body_text, body_html=None):
    """Send outbound email via SendGrid"""
    log = CommunicationLog.objects.get(pk=log_id)
    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        mail = Mail(
            from_email=settings.DEFAULT_FROM_EMAIL,
            to_emails=to_emails,
            subject=subject,
            plain_text_content=body_text,
            html_content=body_html,
        )
        res = sg.send(mail)
        msg_id = getattr(getattr(res, "headers", {}), "get", lambda *_: "")("X-Message-Id", "")
        log.provider_id = msg_id
        log.status = "sent"
        log.payload = {**(log.payload or {}), "status_code": getattr(res, "status_code", 200)}
        log.save(update_fields=["provider_id", "status", "payload"])
    except Exception as e:
        log.status = "error"
        log.payload = {**(log.payload or {}), "error": str(e)}
        log.save(update_fields=["status", "payload"])
        raise self.retry(exc=e, countdown=60)


# ---------------------------------------------------------------------
# 🤖 AI Office Assistant Auto-Reply
# ---------------------------------------------------------------------
@shared_task
def classify_and_autoreply(log_id):
    """
    Automatically classify and respond to inbound communications (SMS/Email)
    using the AIOfficeAssistant logic.
    """
    log = CommunicationLog.objects.get(pk=log_id)
    payload = log.payload or {}
    print("DEBUG >> Using AIOfficeAssistant:", AIOfficeAssistant)
    print("DEBUG: running classify_and_autoreply for log", log_id)    # --- Extract incoming text safely ---
    text = ""
    if log.type == "sms":
        sms_rel = getattr(log, "sms_messages", None)
        if sms_rel and sms_rel.exists():
            text = sms_rel.first().body
    elif log.type == "email":
        email_rel = getattr(log, "emails", None)
        if email_rel and email_rel.exists():
            text = email_rel.first().body_text or ""

    if not text:
        log.payload = {**payload, "auto_reply_status": "no_text_found"}
        log.save(update_fields=["payload"])
        return

    # --- Run the AI Office Assistant ---
    ai = AIOfficeAssistant(
        org={"name": getattr(log.office, "name", "My Office")},
        user=getattr(log.staff, "name", "Staff"),
        context={"source": log.type},
    )
    decision = ai.classify_or_reply(text)
    
    #---- Normalize the decision ----
    action = None
    reply_body = ""
    # --- Interpret AI Decision ---
    if isinstance(decision, str):
        reply_body = decision
    elif isinstance(decision, dict):
        action = decision.get("action")
        reply_body = decision.get("text") or decision.get("message", "")
    else:
        reply_body = ""
    
    # Abort if action is mossing or unrecognized
    allowed_actions ={"reply_sms", "reply_email"}
    if action not in allowed_actions:
        log.playload = {**payload, "auto_reply_status": f"ignor_action_{action or 'none'}"}
        log.save(update_fields=["payload"])
        return
    
    if not reply_body:
        log.payload = {**payload, "auto_reply_status": "no_reply_generated"}
        log.save(update_fields=["payload"])
        return

    # --- Handle SMS Replies ---
    if action == "reply_sms" and log.type == "sms":
        sms_rel = getattr(log, "sms_messages", None)
        if sms_rel and sms_rel.exists():
            from_number = sms_rel.first().from_number
            new_log = CommunicationLog.objects.create(
                office=log.office,
                type="sms",
                direction="outbound",
                status="queued",
                payload={"reply_to": log.id, "text": reply_body},
            )
            send_sms_task.delay(new_log.id, from_number, reply_body)

    # --- Handle Email Replies ---
    elif action == "reply_rmail" and log.type == "email":
        email_rel = (
            getattr(log, "emails", None) or getattr(log, "emails_messages", None)
        )
        if email_rel and email_rel.exists():
            email_obj = email_rel.first()
            from_email = getattr(email_obj, "from_email", None)
            subject = f"Re: {getattr(email_obj, 'subject', 'Your message')}"
            if from_email:
                new_log = CommunicationLog.objects.create(
                    office=log.office,
                    type="email",
                    direction="outbound",
                    status="queued",
                    payload={"reply_to": log.id, "text": reply_body},
                )
            send_email_task.delay(new_log.id, [from_email], subject, reply_body)

    # --- Mark success ---
    log.payload = {**payload, "auto_reply_status": "reply_sent"}
    log.save(update_fields=["payload"])
