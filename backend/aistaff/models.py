from django.db import models
from django.conf import settings
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class ReceptionistLog(models.Model):
    office_id = models.PositiveIntegerField()
    visitor = models.CharField(max_length=255, null=True, blank=True)
    message = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"[{self.created_at}] {self.visitor or 'Unknown'}"


#---- AI SECRETARY----

class Task(models.Model):
    title = models.CharField(max_length=512)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    assigned_to = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=32, default="open")

class Meeting(models.Model):
    topic = models.CharField(max_length=512)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    participants = models.JSONField(default=list)  # list of emails
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

class Note(models.Model):
    content = models.TextField()
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

class Resource(models.Model):
    name = models.CharField(max_length=255)
    quantity = models.IntegerField(default=0)

class FileRecord(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField(blank=True, null=True)
    metadata = models.JSONField(default=dict)
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

class EmailDraft(models.Model):
    subject = models.CharField(max_length=512)
    body = models.TextField()
    to = models.JSONField(default=list)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

class AssistantActionType(models.Model):
    name = models.CharField(max_length=50, unique=True)   # e.g., "task", "meeting"
    label = models.CharField(max_length=100)              # Human-friendly, e.g., "Task"

    def __str__(self):
        return self.label or self.name


class AssistantActionSubtype(models.Model):
    type = models.ForeignKey(AssistantActionType, related_name="subtypes", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)    # e.g., "completed", "rescheduled"
    label = models.CharField(max_length=100)  # Human-friendly, e.g., "Completed Task"

    class Meta:
        unique_together = ("type", "name")

    def __str__(self):
        return f"{self.type.name}:{self.name}"

class AssistantLog(models.Model):
    user = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    input_text = models.TextField()
    response_text = models.TextField(blank=True)
    action_data = models.JSONField(default=dict, blank=True)

    type = models.ForeignKey(
        "AssistantActionType",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="logs"
    )
    subtype = models.ForeignKey(
        "AssistantActionSubtype",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="logs"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.type} log by {self.user} at {self.created_at}"


class SalesLead(models.Model):
    STATUS_CHOICES =[
        ("new", "New"),
        ("contacted", "Contacted"),
        ("interested", "Interested"),
        ("negotiateing", "Negotiateing"),
        ("closed", "Closed"),
        ("lost", "Lost")
        
    ]
    org = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    product_interest = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="new")
    last_follow_up = models.DateTimeField(blank=True, null=True)
    next_follow_up = models.DateTimeField(blank=True, null=True)
    last_message =  models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

class LeadsFollowUpRule(models.Model):
    status = models.CharField(max_length=50, choices=SalesLead.STATUS_CHOICES, unique=True)
    interval_hours = models.PositiveIntegerField(default=24)
    active = models.BooleanField(default=True)
    
class SalesLeadFollowUp(models.Model):
    lead = models.ForeignKey(SalesLead, on_delete=models.CASCADE, related_name="followups")
    channel = models.CharField(max_length=20, choices=[("sms", "SMS"), ("whatsapp", "WhatsApp"), ("email", "Email")])
    message = models.TextField()
    status = models.CharField(max_length=20, default="sent")
    timestamp = models.DateTimeField(default=timezone.now)
    meta = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.channel.upper()} → {self.lead.name} @ {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

class SalesAgentLog(models.Model):
    agent_name = models.CharField(max_length=100, default="AI Sales Agent")
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=100)  # e.g., "follow_up", "capture_lead", "escalate_sale"
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default="success")  # success, failed, pending
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.created_at:%Y-%m-%d %H:%M}] {self.agent_name}: {self.action}"

class AIAgent(models.Model):
    """
    Represent an AI agent type
    """
    agent = models.CharField(max_length=100, unique=True, default="*")
    label = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.label or self.agent
    
class AIAgentActionCost(models.Model):
    """
    Stores dynamic pricing (in credits) for each AI agent/action pair.
    If agent_key='*', it acts as a global default.
    """
    agent_key = models.ForeignKey(AIAgent, on_delete=models.CASCADE, related_name="action_cost")  # e.g. 'AIOfficeAssistant' or '*'
    action_key = models.CharField(max_length=100)              # e.g. 'schedule_meeting'
    label = models.CharField(max_length=150, blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=1.0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("agent_key", "action_key")
        verbose_name = "AI Agent Action Cost"
        verbose_name_plural = "AI Agent Action Costs"

    def __str__(self):
        return f"{self.agent_key}:{self.action_key} → {self.cost} credits"
