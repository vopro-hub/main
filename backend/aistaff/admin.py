from django.contrib import admin
from .models import (
    ReceptionistLog, 
    AssistantLog, 
    AssistantActionType, 
    AssistantActionSubtype,
    AIAgent, 
    AIAgentActionCost,
    Task,
    Meeting,
    Note,
    Resource,
    FileRecord,
    EmailDraft
)

@admin.register(ReceptionistLog)
class ReceptionistLogAdmin(admin.ModelAdmin):
    list_display = ("office_id", "message", "response", "visitor", "created_at")
    search_fields = ("office_id", "message", "created_at")
    


@admin.register(AssistantActionType)
class AssistantActionTypeAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "label")
    search_fields = ("name", "label")


@admin.register(AssistantActionSubtype)
class AssistantActionSubtypeAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "name", "label")
    list_filter = ("type",)
    search_fields = ("name", "label")


@admin.register(AssistantLog)
class AssistantLogAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "input_text", "response_text", "action_data", "type", "subtype", "created_at")
    list_filter = ("type", "subtype")
    search_fields = ("input_text", "response_text")


@admin.register(AIAgent)
class AIAgentAdmin(admin.ModelAdmin):
    list_display = ("agent", "label", "description", "is_active")
    list_editable = ("label", "description", "description", "is_active")
    search_fields = ("agent", "label")
    list_filter = ("agent", "is_active")

@admin.register(AIAgentActionCost)
class AIAgentActionCostAdmin(admin.ModelAdmin):
    list_display = ("agent_key", "action_key", "label", "cost", "is_active")
    list_editable = ("cost", "is_active")
    search_fields = ("agent_key", "action_key", "label")
    list_filter = ("agent_key", "is_active")

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "description", "due_date", "assigned_to", "created_at", "status")
    search_fields = ("title", "assigned_to", "status")
    list_filter = ("due_date", "status")

@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ("topic", "start_time", "end_time", "participants", "created_by", "created_at")
    search_fields = ("topic", "created_by", "start_time")
    list_filter = ("topic", "start_time")

@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ("content", "created_by", "created_at")
    search_fields = ("created_by",)
    
@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ("name", "quantity")
    search_fields = ("name",)

@admin.register(FileRecord)
class FileRecordAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "metadata", "uploaded_by", "created_at")
    search_fields = ("title", "uploaded_by")

@admin.register(EmailDraft)
class EmailDraftAdmin(admin.ModelAdmin):
    list_display = ("subject", "body", "to", "created_by", "created_at")
    search_fields = ("title", "uploaded_by")