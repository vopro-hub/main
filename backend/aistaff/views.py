# receptionist/views.py
from argparse import Action
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, generics, viewsets, permissions, filters
from .services.ai_receptionist import AIReceptionist
from .models import ReceptionistLog
from workspace.models import Office
from .services.ai_secretary import AIOfficeAssistant
from .services.sales_agent import AISalesAgent
import json
from django.shortcuts import get_object_or_404
from datetime import timedelta
from django.utils.timezone import now
from django.db import models
from .serializers import (
    AssistantLogSerializer,
    SalesLeadSerializer, 
    SalesLeadFollowUpSerializer, 
    SalesAgentLogSerializer
)
from .models import (
AssistantLog, 
AssistantActionType, 
Meeting, 
SalesLead, 
SalesLeadFollowUp, 
SalesAgentLog
)
from django.utils.dateparse import parse_datetime

class AIAssistantRespondView(APIView):
    permission_classes = []  # restrict as you need

    def post(self, request):
        message = request.data.get("message")
        if not message:
            return Response({"error": "message required"}, status=400)

        # discover org/office id from session (or pass office in body)
        office_id = request.session.get("current_office_id") or request.data.get("office_id")
        office = None
        if office_id:
            office = get_object_or_404(Office, pk=office_id)
        org = {"id": office.id if office else None, "name": getattr(office, "name", "Organization"), "details": getattr(office, "details", "")}

        assistant = AIOfficeAssistant(org=org, staff_user=request.user if request.user.is_authenticated else None, session=request.session)
        resp = assistant.respond(message)
        return Response(resp)

class AssistantTypeMapView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = {}
        for t in AssistantActionType.objects.prefetch_related("subtypes"):
            data[t.name] = [s.name for s in t.subtypes.all()]
        return Response(data)



class AIAssistantMeetingView(APIView):
    """
    Handles retrieval of a meeting.
    Called by AI assistant or frontend after successful scheduling.
    """
    permission_classes = [permissions.IsAuthenticated]

    
   
class AssistantLogListView(generics.ListAPIView):
    serializer_class = AssistantLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = AssistantLog.objects.filter(user=self.request.user)
        print("bug:", self.request.query_params.get("type"))
        log_type = self.request.query_params.get("type")
        if log_type and log_type != "all":
            qs = qs.filter(type=log_type)
           

        days = self.request.query_params.get("days")
        if days and days.isdigit():
            cutoff = now() - timedelta(days=int(days))
            qs = qs.filter(created_at__gte=cutoff)

        keyword = self.request.query_params.get("q")
        if keyword:
            qs = qs.filter(
                models.Q(input_text__icontains=keyword) |
                models.Q(response_text__icontains=keyword)
            )

        return qs




class SalesAgentViewSet(viewsets.ModelViewSet):
    
    """
     ViewSet for managing Sales Agent activities, leads, and logs.
     Supports filtering by lead status and manual instructions.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SalesLeadSerializer
    queryset = SalesLead.objects.all().order_by('-last_follow_up')
    
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "email", "phone", "product_interest", "status"]
    ordering_fields = ["created_at", "last_follow_up"]

    def get_queryset(self):
        qs = super().get_queryset()
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs

    @action(detail=False, methods=["get"])
    def followups(self, request):
        """
        Retrieve all follow-up records (including scheduled).
        """
        status_filter = request.query_params.get("status")
        qs = SalesLeadFollowUp.objects.select_related("lead").order_by("-created_at")
        if status_filter:
            qs = qs.filter(lead__status=status_filter)
        serializer = SalesLeadFollowUpSerializer(qs, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["post"])
    def instruct(self, request):
        """
        Allow user to send direct instructions to the AI sales agent.
        """
        org = request.data.get("org")
        message = request.data.get("message")
        if not org or not message:
            return Response({"error": "Missing org or message."}, status=status.HTTP_400_BAD_REQUEST)

        agent = AISalesAgent(org=org)
        reply = agent.respond(message)
        return Response({"reply": reply})

    @action(detail=False, methods=["post"])
    def add_lead(self, request):
        """
        Allow manual lead addition from frontend.
        """
        serializer = SalesLeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "✅ Lead added successfully!", "lead": serializer.data})


class ReceptionistRespondView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        message = request.data.get("message")
        office_id = request.session.get("current_office_id")

        if not message or not office_id:
            return Response({"error": "Message and office_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            office = Office.objects.get(id=office_id)
        except Office.DoesNotExist:
            return Response({"error": "Office not found"}, status=status.HTTP_404_NOT_FOUND)

        org = {
            "name": office.name,
            "details": office.details,
        }

        ai = AIReceptionist(
            org=org,
            city=office.city,
            faqs=office.faqs,
            bookings=office.booking_rules,
        )
        response = ai.respond(message)
  
         # ✅ Fake AI response for testing only
        #fake_responses = {
        #    "hello": f"👋 Hi! Welcome to {office.name}.",
        #    "hours": "We are open from 9 AM to 6 PM, Monday to Friday.",
        #    "book": "📅 Sure! You can book a visit by telling me your preferred time.",
        #}
        #response = fake_responses.get(message.lower(), f"🤖 I received: {message}")
        ReceptionistLog.objects.create(
           office_id=office_id,
           message=message,
           response=response,
           visitor=request.META.get("REMOTE_ADDR"),
        )
        return Response({"response": response})
        
        
