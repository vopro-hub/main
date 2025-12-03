from django.contrib.auth.models import AbstractUser
import uuid
from decimal import Decimal
from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

@receiver(post_save, sender=AbstractUser)
def create_auth_token( sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.get_or_create(user=instance)
        
        
class User(AbstractUser):
    class Roles(models.TextChoices):
        OWNER = "OWNER","Owner"
        MEMBER = "MEMBER","Member"
        GUEST = "GUEST","Guest"
    role = models.CharField(max_length=12, choices=Roles.choices, default=Roles.MEMBER)
    def __str__(self): return self.username


DECIMAL_ZERO = Decimal("0.00")


class InsufficientCredits(Exception):
    pass


class ReservationNotFound(Exception):
    pass


class UserWallet(models.Model):
    """Each user automatically gets a wallet to store prepaid credits."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="wallet")
    total_credits = models.DecimalField(max_digits=12, decimal_places=2, default=DECIMAL_ZERO)
    reserved_credits = models.DecimalField(max_digits=12, decimal_places=2, default=DECIMAL_ZERO)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Wallet({self.user}) balance={self.available():.2f} reserved={self.reserved_credits:.2f}"

    def available(self):
        """Credits available for reservation."""
        return (self.total_credits - (self.reserved_credits or DECIMAL_ZERO)).quantize(Decimal("0.01"))

class CreditTransaction(models.Model):
    TYPE_PURCHASE = "purchase"
    TYPE_RESERVE = "reserve"
    TYPE_REFUND = "refund"
    TYPE_DEDUCT = "deduct"

    TYPE_CHOICES = [
        (TYPE_PURCHASE, "Purchase"),
        (TYPE_RESERVE, "Reserve"),
        (TYPE_REFUND, "Refund"),
        (TYPE_DEDUCT, "Deduct"),
    ]

    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_REFUND = "refund"
    STATUS_FAILED = "failed"

    wallet = models.ForeignKey("UserWallet", on_delete=models.CASCADE, related_name="transactions")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    type = models.CharField(max_length=32, choices=TYPE_CHOICES)
    status = models.CharField(max_length=32, default=STATUS_PENDING)
    task = models.ForeignKey("AIAssistantTask", null=True, blank=True, on_delete=models.SET_NULL, related_name="transactions")
    AI_staff = models.CharField(max_length=100, null=True, blank=True)
    meta = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tx({self.type} {self.amount} {self.status})"

class PaystackTransaction(models.Model):
    def generate_ref():
        return str(uuid.uuid4()).replace("-", "")[:12]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    reference = models.CharField(max_length=20, default=generate_ref, unique=True)
    amount = models.PositiveIntegerField()  # in kobo/pesewas
    credits_to_add = models.PositiveIntegerField()
    verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class AIAssistantTask(models.Model):
    """Tracks AI assistant task attempts linked to wallet credits."""
    TASK_PENDING = "pending"
    TASK_SUCCESS = "success"
    TASK_FAILED = "failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="ai_tasks")
    agent = models.CharField(max_length=64, default="receptionist")
    task_type = models.CharField(max_length=64, default="generic")
    reserved_amount = models.DecimalField(max_digits=12, decimal_places=2, default=DECIMAL_ZERO)
    status = models.CharField(max_length=16, choices=[
        (TASK_PENDING, "Pending"),
        (TASK_SUCCESS, "Success"),
        (TASK_FAILED, "Failed"),
    ], default=TASK_PENDING)
    result = models.JSONField(default=dict, blank=True)
    failed_reason = models.CharField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Task({self.task_type}, user={self.user})"

# -------------------------------------------------------------------
# 🔹 AUTO-CREATE WALLET ON USER CREATION
# -------------------------------------------------------------------
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_wallet_for_user(sender, instance, created, **kwargs):
    if created:
        UserWallet.objects.get_or_create(user=instance)


