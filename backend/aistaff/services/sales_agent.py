from openai import OpenAI
from django.conf import settings
from django.utils import timezone
from .pay_per_success import pay_per_success
from aistaff.models import SalesLead, SalesLeadFollowUp, LeadsFollowUpRule, SalesAgentLog
from workspace.models import SupportTicket
from twilio.rest import Client
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from aistaff.tasks import send_delayed_follow_up
from decimal import Decimal
import json

client = "OpenAI(api_key=settings.OPENAI_API_KEY)"
twilio_client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)


class AISalesAgent:
    def __init__(self, org, products=None, pricing=None, session=None, staff=None):
        self.org = org
        self.products = products or {}
        self.pricing = pricing or {}
        self.session = session or {}
        self.staff = staff

    # ---------------- CONTEXT ----------------
    def build_context(self, lead=None):
        remembered = ""
        if lead:
            remembered = f"""
            Known lead info:
            Name: {lead.name}
            Email: {lead.email}
            Phone: {lead.phone or 'N/A'}
            Status: {lead.status}
            """

        elif self.session.get("lead_name") or self.session.get("lead_email"):
            remembered = f"""
            Known lead info:
            Name: {self.session.get('lead_name')}
            Email: {self.session.get('lead_email')}
            """

        return f"""
        You are the AI Sales Agent for {self.org['name']}.
        Your mission: convert leads into paying customers, politely and effectively.

        - Be empathetic, consultative, and persuasive.
        - Mention relevant products: {json.dumps(self.products)}
        - Use pricing data if asked: {json.dumps(self.pricing)}
        - Always maintain context from previous interactions.

        JSON actions:
        - "capture_lead"
        - "follow_up"
        - "close_deal"
        - "escalate_sale"
        {remembered}
        """

    # ---------------- RESPONSE ----------------
    def respond(self, message: str):
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.build_context()},
                {"role": "user", "content": message},
            ],
            max_tokens=600,
        )
        reply = resp.choices[0].message.content.strip()

        if reply.startswith("{") and "action" in reply:
            try:
                data = json.loads(reply)
                action = data["action"]
                if action == "capture_lead": return self.capture_lead(data)
                elif action == "follow_up": return self.follow_up(data)
                elif action == "close_deal": return self.close_deal(data)
                elif action == "escalate_sale": return self.escalate_sale(data)
            except Exception as e:
                return f"⚠️ Could not process: {e}"

        self.detect_and_remember_lead(message)
        return reply

    # ---------------- MEMORY ----------------
    def detect_and_remember_lead(self, message: str):
        msg = message.lower()
        if "name is" in msg:
            name = message.split("name is")[-1].strip().split()[0:3]
            self.session["lead_name"] = " ".join(name)
        if "@" in message:
            email = [w for w in message.split() if "@" in w]
            if email:
                self.session["lead_email"] = email[0]

    # ---------------- ACTIONS ----------------

    @pay_per_success(task_type="capture_lead")
    def capture_lead(self, data):
        name = data.get("name") or self.session.get("lead_name", "Unknown Lead")
        email = data.get("email") or self.session.get("lead_email", "unknown@example.com")
        phone = data.get("phone", "")
        product_interest = data.get("product_interest", "General")

        lead, created = SalesLead.objects.get_or_create(
            org_id=self.org["id"],
            email=email,
            defaults={"name": name, "phone": phone, "product_interest": product_interest},
        )

        if created:
            lead.status = "new"
            lead.save()
            self.schedule_follow_up(lead)
            return f"✅ Lead captured and first follow-up scheduled for {email}."
        return f"ℹ️ Lead {email} already exists."

    @pay_per_success(task_type="follow_up")
    def follow_up(self, data):
        email = data.get("email") or self.session.get("lead_email")
        if not email:
            return "⚠️ I need an email or phone number to follow up."

        try:
            lead = SalesLead.objects.get(email=email, org_id=self.org["id"])
        except SalesLead.DoesNotExist:
            return "⚠️ No matching lead found."

        # Build smart message using AI context
        history = "\n".join(f"- {f.message}" for f in lead.followups.all())
        context = self.build_context(lead)
        prompt = f"""
        Previous conversation:
        {history or 'No past messages.'}

        Generate a warm, personalized follow-up for this lead.
        """
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": context}, {"role": "user", "content": prompt}],
            max_tokens=300,
        )
        message = resp.choices[0].message.content.strip()

        sent, channel = self._send_message(lead, message)
        SalesLeadFollowUp.objects.create(
            lead=lead,
            channel=channel,
            message=message,
            status="sent" if sent else "failed",
        )

        if sent:
            lead.status = "contacted" if lead.status == "new" else lead.status
            lead.last_contacted = timezone.now()
            lead.save()
            self.schedule_follow_up(lead)
            return f"✅ {channel.upper()} follow-up sent to {lead.name}."
        else:
            return f"⚠️ Could not reach {lead.name}."

    @pay_per_success(task_type="close_deal")
    def close_deal(self, data):
        email = data.get("email") or self.session.get("lead_email")
        status = data.get("status", "won")

        try:
            lead = SalesLead.objects.get(email=email, org_id=self.org["id"])
        except SalesLead.DoesNotExist:
            return "⚠️ No lead found."

        lead.status = "won" if status == "won" else "lost"
        lead.save()
        return f"🎉 Deal {'closed successfully' if status == 'won' else 'lost'} for {lead.name}."

    @pay_per_success(task_type="escalate_sale")
    def escalate_sale(self, data):
        message = data.get("message", "Lead requires human follow-up.")
        visitor_name = self.session.get("lead_name", "Unknown")
        visitor_email = self.session.get("lead_email", "unknown@example.com")

        ticket = SupportTicket.objects.create(
            user=self.staff,
            subject=f"Sales Escalation from {visitor_name}",
            message=f"{visitor_name} ({visitor_email}) → {message}",
            status="open",
        )
        return f"🙋 Escalation logged. Ticket #{ticket.id} created."

    # ---------------- HELPERS ----------------

    def _send_message(self, lead, message):
        """Try WhatsApp, SMS, or email automatically."""
        sent, channel = False, None

        if lead.phone:
            try:
                twilio_client.messages.create(
                    from_=settings.TWILIO_PHONE_NUMBER,
                    to=lead.phone,
                    body=message,
                )
                channel = "sms"
                sent = True
            except Exception as e:
                print("Twilio error:", e)

        if not sent and lead.email:
            try:
                sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
                mail = Mail(
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to_emails=lead.email,
                    subject=f"Follow-up from {self.org['name']}",
                    html_content=f"<p>{message}</p>",
                )
                sg.send(mail)
                channel = "email"
                sent = True
            except Exception as e:
                print("SendGrid error:", e)

        return sent, channel or "unknown"

    def schedule_follow_up(self, lead):
        """Use LeadFollowUpRule to determine interval and schedule Celery task."""
        rule = LeadFollowUpRule.objects.filter(status=lead.status, active=True).first()
        if not rule:
            interval_hours = 24  # default
        else:
            interval_hours = rule.interval_hours

        follow_up_time = timezone.now() + timedelta(hours=interval_hours)
        lead.next_follow_up = follow_up_time
        lead.save()

        send_delayed_follow_up.apply_async(
            (self.org, lead.email, f"Just following up, {lead.name}!"),
            eta=follow_up_time,
        )