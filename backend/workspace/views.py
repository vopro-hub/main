from rest_framework import viewsets, permissions, generics, status
from .models import Office, Room, Membership, Presence, OfficeCity, Worker
from .serializers import OfficeSerializer, RoomSerializer, CitySerializer, PresenceSerializer, WorkerSerializer
from django.db.models import Q, Count
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import OfficeCity


class CityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OfficeCity.objects.all()
    serializer_class = CitySerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return OfficeCity.objects.annotate(
            offices_count=Count("offices", filter=Q(offices__public=True))
        )


class OfficeViewSet(viewsets.ModelViewSet):
    serializer_class = OfficeSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Office.objects.filter(
            Q(memberships__user=self.request.user) | Q(owner=self.request.user)
        ).distinct()

    def perform_create(self, serializer):
        office = serializer.save(owner=self.request.user)
        Membership.objects.create(user=self.request.user, office=office, role="OWNER")
        Room.objects.create(office=office, name="Lobby")
        Room.objects.create(office=office, name="Meeting Room")

    @action(detail=True, methods=["post"])
    def toggle_public(self, request, pk=None):
        office = self.get_object()
        office.public = not office.public
        office.save()
        return Response(OfficeSerializer(office).data)


class RoomViewSet(viewsets.ModelViewSet):
    serializer_class = RoomSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Room.objects.filter(office__memberships__user=self.request.user)
        office_id = self.request.query_params.get("office")
        if office_id:
            qs = qs.filter(office_id=office_id)
        return qs

    @action(detail=False, methods=["post"])
    def save_layout(self, request):
        rooms_data = request.data.get("rooms", [])
        for r in rooms_data:
            try:
                room = Room.objects.get(
                    id=r["id"], office__memberships__user=request.user
                )
                room.x = r.get("x", room.x)
                room.y = r.get("y", room.y)
                room.width = r.get("width", room.width)
                room.height = r.get("height", room.height)
                room.config = r.get("config", room.config)
                room.access_policy = r.get("access_policy", room.access_policy)
                room.access_config = r.get("access_config", room.access_config)
                room.save()
            except Room.DoesNotExist:
                continue
        return Response({"status": "layout saved"}, status=status.HTTP_200_OK)


class PresenceViewSet(viewsets.ModelViewSet):
    serializer_class = PresenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Presence.objects.filter(office__memberships__user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class WorkerViewSet(viewsets.ModelViewSet):
    serializer_class = WorkerSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Worker.objects.filter(
            office__memberships__user=self.request.user
        )

    def perform_create(self, serializer):
        serializer.save()
       
    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)