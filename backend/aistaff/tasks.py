# sales/tasks.py
from celery import shared_task
from django.utils import timezone
from django.conf import settings
from .models import SalesLead
import json
import traceback

@shared_task(bind=True, max_retries=3)
def send_delayed_follow_up(self, org_data):
    """
    Celery task that automatically triggers AI-written follow-ups 
    for leads that are due, using AISalesAgent intelligence.

    org_data: dict or JSON string containing the organization's info.
    """

    try:
        # --- Load org info ---
        if isinstance(org_data, str):
            org_data = json.loads(org_data)
        org_id = org_data.get("id")

        # --- Select leads that need follow-up ---
        due_leads = SalesLead.objects.filter(
            org_id=org_id,
            status__in=["new", "contacted", "pending"]
        )

        now = timezone.now()
        for lead in due_leads:
            interval = getattr(lead, "follow_up_interval_hours", 24)
            last_contact = lead.last_contacted or (lead.created_at if hasattr(lead, "created_at") else None)

            # Skip if too soon to follow up
            if last_contact and (now - last_contact).total_seconds() < interval * 3600:
                continue

            # --- Summarize previous follow-up history ---
            prev_msgs = []
            if hasattr(lead, "followups"):
                last_followups = lead.followups.order_by("-created_at")[:3]
                prev_msgs = [f"{f.channel.upper()}: {f.message}" for f in last_followups]

            context_summary = "\n".join(prev_msgs) if prev_msgs else "No previous conversation yet."

            # --- Instantiate the AI Sales Agent ---
            from aistaff.services.sales_agent import AISalesAgent;
            agent = AISalesAgent(org=org_data)

            # --- Ask the AI to write a natural follow-up message ---
            prompt = f"""
            You are the sales AI for {org_data.get('name')}.
            The lead is {lead.name} ({lead.email}) interested in {lead.product_interest}.
            Previous conversations:
            {context_summary}

            Write a short, warm follow-up message that tries to move the lead closer to a decision.
            If the lead seems cold, re-engage politely.
            """

            ai_reply = agent.respond(prompt)

            # --- Trigger follow-up automatically using agent logic ---
            result = agent.follow_up({
                "email": lead.email,
                "message": ai_reply,
            })

            print(f"[AutoFollowUp] Lead: {lead.email} → {result}")

            # --- Update timestamps ---
            lead.last_contacted = now
            lead.save()

        return f"[AutoFollowUp] Completed for org_id={org_id}"

    except Exception as e:
        print(f"[AutoFollowUp ERROR]: {e}\n{traceback.format_exc()}")
        raise self.retry(exc=e, countdown=300)
