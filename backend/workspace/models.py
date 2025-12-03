import uuid
from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.utils import timezone
from django.contrib.postgres.fields import JSONField 


User = settings.AUTH_USER_MODEL

class OfficeCity(models.Model):
    country = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=250, blank=True)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    lat = models.FloatField(blank=True, null=True)
    lng = models.FloatField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.city)
        super().save(*args, **kwargs)
    
    class Meta:
        unique_together = ("country", "city")  # prevent duplicates
        ordering = ["country", "city"]

    def __str__(self):
        return f"{self.city}, {self.country}"
  
        
class Office(models.Model):
    name = models.CharField(max_length=120)
    city = models.ForeignKey(OfficeCity, on_delete=models.SET_NULL, null=True, blank=True, related_name="offices")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="offices")
    details = models.TextField(blank=True, null=True)
    faqs = models.JSONField(default=list, blank=True)
    booking_rules = models.JSONField(default=list, blank=True)
    public = models.BooleanField(default=False)
    public_slug = models.SlugField(max_length=50, unique=True, blank=True, null=True)
    services = models.JSONField(default=dict, blank=True)  # optional
    coordinates = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        if self.public and not self.public_slug:
            # short random slug
            self.public_slug = uuid.uuid4().hex[:10]
        if not self.public:
            # optional: clear slug if made private
            self.public_slug = None
        super().save(*args, **kwargs)
        
    def __str__(self): 
        return f"{self.name} ({self.city})"

class Membership(models.Model):
    ROLE_CHOICES = (("OWNER","Owner"), ("MEMBER","Member"), ("GUEST","Guest"))
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name="memberships")
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default="MEMBER")
    joined_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ("user","office")

class Room(models.Model):
    ACCESS_POLICIES = [
        ("free", "Free Access"),
        ("form", "Form Required"),
        ("approval", "Staff Approval"),
        ("locked", "Access Code"),
    ]
    office = models.ForeignKey(Office, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=120)
    capacity = models.IntegerField(default=1)
    x = models.FloatField(default=0)
    y = models.FloatField(default=0)
    width = models.FloatField(default=150)
    height = models.FloatField(default=100)
    config = models.JSONField(default=dict, blank=True)
    access_policy = models.CharField(max_length=20, choices=ACCESS_POLICIES, default="free")
    access_config = models.JSONField(default=dict, blank=True)  
    def __str__(self): 
        return f"{self.office.name} / {self.name}"

class RoomBooking(models.Model):
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    visitor_name = models.CharField(max_length=255)
    visitor_email = models.EmailField()
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed = models.BooleanField(default=False)

class cityLobby(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.ForeignKey(OfficeCity, on_delete=models.CASCADE, related_name="city_lobby")
    def __str__(self): return f"{self.user} / {self.city}"

class Presence(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    office = models.ForeignKey(Office, null=True, blank=True, on_delete=models.CASCADE, related_name="presence")
    city = models.ForeignKey(OfficeCity, null=True, blank=True, on_delete=models.CASCADE, related_name="presence")
    status = models.CharField(max_length=20, default="online")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta: 
        unique_together = ("office","user", "city")
        
class Worker(models.Model):
    office = models.ForeignKey("Office", on_delete=models.CASCADE, related_name="workers")
    name = models.CharField(max_length=255)
    rooms = models.ManyToManyField("Room", related_name="workers")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="workers")
    added_at = models.DateTimeField(auto_now=True)

    worker_id = models.CharField(max_length=50, unique=True, editable=False)

    def save(self, *args, **kwargs):
        if not self.worker_id:
            # --- Generate prefix ---
            words = self.office.name.upper().split()
            if len(words) == 1:
                prefix = words[0][:2]  # First 2 letters
            else:
                prefix = "".join(w[0] for w in words[:2])  # First letters of first 2 words

            # --- Sequence count ---
            count = Worker.objects.filter(office=self.office).count() + 1

            # --- Final ID ---
            self.worker_id = f"{prefix}{self.office.id}-{count:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.worker_id} - {self.name} ({self.office.name})"


class WorkerPresence(models.Model):
    worker = models.OneToOneField("Worker", on_delete=models.CASCADE, related_name="presence")
    is_presence = models.BooleanField(default=False)
    last_login_time = models.DateTimeField(null=True, blank=True)
    last_logout_at = models.DateTimeField(null=True, blank=True)

    def login(self):
        self.is_online = True
        self.last_login_time = timezone.now()
        self.save()

    def logout(self):
        self.is_online = False
        self.last_logout_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.worker.name} ({'Online' if self.is_presence else 'Offline'})"

    

class VisitorAccessSubmission(models.Model):
    room = models.ForeignKey("Room", on_delete=models.CASCADE, related_name="access_submissions")
    visitor_id = models.CharField(max_length=255, null=True, blank=True)  # optional visitor token
    data = models.JSONField(default=dict)  # requires Django 3.1+ or use django.contrib.postgres JSONField
    name = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    email = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    phone = models.CharField(max_length=50, null=True, blank=True, db_index=True)
    approved = models.BooleanField(default=False)  
    revoked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Submission {self.id} for {self.room.name}"


class SupportTicket(models.Model):
    STATUS_CHOICES = [
        ("open", "Open"),
        ("in_progress", "In Progress"),
        ("resolved", "Resolved"),
        ("closed", "Closed"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="support_tickets")
    subject = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open")
    assigned_to = models.ForeignKey( User, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_tickets")

    def __str__(self):
        return f"Ticket #{self.id} - {self.subject} ({self.status})"
