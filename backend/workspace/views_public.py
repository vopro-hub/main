from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action
from rest_framework import viewsets, status
from django.utils.timezone import now, timedelta
import jwt
from django.conf import settings

from .utils.presence import broadcast_presence 
from .models import OfficeCity, Office, Room, Worker, WorkerPresence, VisitorAccessSubmission
from .serializers import (
    CitySerializer, 
    PublicOfficeSerializer, 
    RoomSerializer,
    WorkerSerializer,
    WorkerPresenceSerializer,
    VisitorAccessSubmissionSerializer
)

SECRET = settings.SECRET_KEY  # or a dedicated JWT secret
OFFICE_SESSION_KEY= "current_office_id"

class PublicCitiesView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        cities = OfficeCity.objects.filter(offices__public=True).distinct()
        serializer = CitySerializer(cities, many=True)
        return Response(serializer.data)


class PublicCityOfficesView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, slug):
        city = get_object_or_404(OfficeCity, slug=slug)
        offices = city.offices.filter(public=True)
        serializer = PublicOfficeSerializer(offices, many=True)
        return Response({"city": city.city, "offices": serializer.data})


class PublicOfficeDetailView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        office = get_object_or_404(Office, public_slug=slug, public=True)
        self.request.session[OFFICE_SESSION_KEY] = office.id
        self.request.session.modified = True
        self.request.session.save()
        serializer = PublicOfficeSerializer(office)
        return Response(serializer.data)

class GetCurrentOffice(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        office_id = self.request.session.get(OFFICE_SESSION_KEY)
        print("➡️ Session contents:", self.request.session.get('current_office_id'))
        if not office_id:
            return Response({"detail": "no office set"}, status=404)
        office = Office.objects.filter(id=office_id, public=True).first()
        if not office:
            return Response({"detail": "no office found"}, status=404)
        serializer = PublicOfficeSerializer(office)
        return Response({"id": office.id, "office": serializer.data})

        


class PublicRoomView(ListAPIView):
    serializer_class = RoomSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        office_id = self.request.query_params.get("office")
        if office_id:
            return Room.objects.filter(office_id=office_id, office__public=True)
        return Room.objects.none()


class RoomAccessView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, slug, room_id):
        room = get_object_or_404(Room, id=room_id, office__public_slug=slug, office__public=True)

        policy = room.access_policy
        config = room.access_config or {}

        if policy == "free":
            return Response({"access": "granted"})

        elif policy == "form":
            # check form fields
            required = config.get("form_fields", [])
            missing = [f for f in required if f not in request.data]
            if missing:
                return Response({"error": f"Missing fields: {', '.join(missing)}"}, status=400)
            return Response({"access": "granted"})

        elif policy == "approval":
            # TODO: hook up to receptionist dashboard
            return Response({"access": "pending", "message": "Approval required"})

        elif policy == "locked":
            code = config.get("code")
            if not code or request.data.get("code") != code:
                return Response({"error": "Invalid or missing code"}, status=403)
            return Response({"access": "granted"})

        return Response({"error": "Unknown access policy"}, status=500)

class PublicWorkerView(ListAPIView):
    serializer_class = WorkerSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        office_id = self.request.query_params.get("office")
        if office_id:
            return Worker.objects.filter(office_id=office_id, office__public=True)
        return Worker.objects.none()



class WorkerPresenceViewSet(viewsets.ModelViewSet):
    serializer_class = WorkerPresenceSerializer
    queryset = WorkerPresence.objects.all()
    permission_classes = [AllowAny]  # public workers can log in

    @action(detail=False, methods=["post"], url_path="login")
    def login(self, request):
        work_id = request.data.get("work_id")
        if not work_id:
            return Response({"error": "Work ID required"}, status=status.HTTP_400_BAD_REQUEST)

        worker = Worker.objects.filter(worker_id=work_id).first()
        if not worker:
            return Response({"error": "Worker not found"}, status=status.HTTP_404_NOT_FOUND)

        presence, _ = WorkerPresence.objects.get_or_create(worker=worker)
        presence.login()  # should set is_online + timestamp
        broadcast_presence(worker, "login")
        return Response(WorkerPresenceSerializer(presence).data)

    @action(detail=False, methods=["post"], url_path="logout")
    def logout(self, request):
        print("LOGOUT PAYLOAD:", request.data)
        work_id = request.data.get("work_id")
        if not work_id:
            return Response({"error": "Work ID required"}, status=status.HTTP_400_BAD_REQUEST)

        worker = Worker.objects.filter(worker_id=work_id).first()
        if not worker:
            return Response({"error": "Worker not found"}, status=status.HTTP_404_NOT_FOUND)

        presence, _ = WorkerPresence.objects.get_or_create(worker=worker)
        presence.logout()
        broadcast_presence(worker, "logout")
        return Response(WorkerPresenceSerializer(presence).data)
 

class PublicRoomAccessSubmit(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, room_id):
        """
        Public endpoint to submit an access form for a room.
        Expects JSON: { data: { fieldName1: value1, ... }, visitor_id?: "..." }
        Returns submission + signed JWT token.
        """
        room = get_object_or_404(Room, pk=room_id, office__public=True)
        payload = request.data or {}
        data = payload.get("data") or {}
        visitor_id = payload.get("visitor_id")

        if not isinstance(data, dict):
            return Response(
                {"error": "Invalid data"}, status=status.HTTP_400_BAD_REQUEST
            )

        access_policy = getattr(room, "access_policy", "free")
        access_config = getattr(room, "access_config", {}) or {}

        # Normalize form_fields if string
        form_fields = access_config.get("form_fields", [])
        if isinstance(form_fields, str):
            form_fields = [f.strip() for f in form_fields.split(",") if f.strip()]

        # Validate required form fields
        if access_policy == "form":
            missing = [f for f in form_fields if not str(data.get(f, "")).strip()]
            if missing:
                return Response(
                    {"error": "Missing required fields", "missing": missing},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # Extract common fields heuristically
        def extract_first(keys):
            for k in keys:
                if k in data and data[k]:
                    return str(data[k])
                for dk in data:  # case-insensitive
                    if dk.lower() == k.lower() and data[dk]:
                        return str(data[dk])
            return None

        name = extract_first(["name", "full_name", "fullname"])
        email = extract_first(["email", "e-mail"])
        phone = extract_first(["phone", "mobile", "phone_number", "tel"])

        # Save submission
        submission = VisitorAccessSubmission.objects.create(
            room=room,
            visitor_id=visitor_id,
            data=data,
            name=name,
            email=email,
            phone=phone,
        )

        # Expiry logic: approval lasts longer, others shorter
        if access_policy == "approval":
            exp = now() + timedelta(days=7)
        else:  # free, form, unlock
            exp = now() + timedelta(hours=24)

        payload = {
            "submission_id": submission.id,
            "room_id": room.id,
            "exp": int(exp.timestamp()),
        }

        token = jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

        serializer = VisitorAccessSubmissionSerializer(submission)
        return Response(
            {"submission": serializer.data, "token": token},
            status=status.HTTP_201_CREATED,
        )


class PublicRoomAccessValidate(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        """
        Validate a visitor's access token.
        Expects: { "token": "..." }
        """
        token = request.data.get("token")
        if not token:
            return Response({"error": "Token required"}, status=400)

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            sub = VisitorAccessSubmission.objects.filter(
                id=payload["submission_id"], room_id=payload["room_id"], revoked=False
            ).first()
            if not sub:
                return Response({"error": "Submission not found"}, status=404)

            # Check approval if required
            if sub.room.access_policy == "approval" and not sub.approved:
                return Response({"detail": "Waiting for approval"}, status=403)

            return Response({"valid": True, "room": sub.room.id})
        except jwt.ExpiredSignatureError:
            return Response({"error": "Token expired"}, status=401)
        except Exception:
            return Response({"error": "Invalid token"}, status=400)
