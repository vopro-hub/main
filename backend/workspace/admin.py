from django.contrib import admin
from .models import Office, Room, Worker, WorkerPresence, cityLobby, Membership, Presence, OfficeCity, VisitorAccessSubmission, SupportTicket


@admin.register(Office)
class OfficeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "city", "owner")
    search_fields = ("name", "city", "owner__username")
    list_filter = ("city",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "office", "x", "y", "width", "height", "config", "access_policy", "access_config")
    search_fields = ("name", "office__name")
    list_filter = ("office",)

@admin.register(cityLobby)
class cityLobbyAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "city")
    search_fields = ("user", "city")
    list_filter = ("city",)


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "office", "role")
    search_fields = ("user__username", "office__name", "role")
    list_filter = ("role", "office")


@admin.register(Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "office", "status")
    search_fields = ("user__username", "office__name", "status")
    list_filter = ("status", "office")

@admin.register(OfficeCity)
class CityAdmin(admin.ModelAdmin):
    list_display = ("city", "country")
    search_fields = ("city", "country")

@admin.register(Worker)
class WorkerAdmin(admin.ModelAdmin):
    list_display = ( "worker_id", "name", "office")
    search_fields = ("name", "room")

@admin.register(WorkerPresence)
class WorkerPresenceAdmin(admin.ModelAdmin):
    list_display = ( "worker", "is_presence", "last_login_time", "last_logout_at")
   
@admin.register(VisitorAccessSubmission)
class VisitorAccessSubmissionAdmin(admin.ModelAdmin):
    list_display = ("room", "visitor_id", "data", "name", "email", "phone", "approved", "revoked", "created_at")
   
 
@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "subject", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("subject", "message", "user__email")
