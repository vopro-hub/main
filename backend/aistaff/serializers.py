from rest_framework import serializers
from .models import AssistantLog, SalesLead, SalesLeadFollowUp, SalesAgentLog

class AssistantLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssistantLog
        fields = ["id", "user", "input_text", "response_text", "action_data", "type", "subtype", "created_at"]

class SalesLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesLead
        fields = "__all__"
        

class SalesLeadFollowUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesLeadFollowUp
        fields = "__all__"

class SalesAgentLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesAgentLog
        fields = "__all__"
