from django.urls import path, include
from rest_framework.routers import DefaultRouter
from workspace.views_public import GetCurrentOffice
from .views import (
    AIAssistantRespondView,
    AssistantTypeMapView,
    AIAssistantMeetingView,
    AssistantLogListView,
    ReceptionistRespondView,
    SalesAgentViewSet,
)

# DRF router for ViewSets
router = DefaultRouter()
router.register(r"sales/agent/logs", SalesAgentViewSet, basename="sales-agent_logs")
router.register(r"sales/agent/instruct", SalesAgentViewSet, basename="sales-agent-instruct")
router.register(r"sales/agent/add-lead", SalesAgentViewSet, basename="sales-agent-add_lead")

urlpatterns = [
    # --- AI Office Assistant (Secretary) ---
    path("assistant/respond/", AIAssistantRespondView.as_view(), name="assistant-respond"),
    path("assistant/types/", AssistantTypeMapView.as_view(), name="assistant-types"),
    path("assistant/meeting/", AIAssistantMeetingView.as_view(), name="assistant-meeting"),
    path("assistant/logs/", AssistantLogListView.as_view(), name="assistant-logs"),

    # --- AI Receptionist ---
    path("receptionist/office/", GetCurrentOffice.as_view(), name="office"),
    path("receptionist/respond/", ReceptionistRespondView.as_view(), name="receptionist-respond"),

    # --- AI Sales Agent (with router actions) ---
    path("", include(router.urls)),
]


