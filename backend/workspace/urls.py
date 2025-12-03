from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import OfficeViewSet, RoomViewSet, PresenceViewSet, CityViewSet, WorkerViewSet
from aistaff.views import ReceptionistRespondView, AssistantTypeMapView, AssistantLogListView, AIAssistantRespondView
router = DefaultRouter()
router.register(r"offices", OfficeViewSet, basename="office")
router.register(r"rooms", RoomViewSet, basename="room")
router.register(r"presence", PresenceViewSet, basename="presence")
router.register(r"cities", CityViewSet, basename="city")
router.register(r"workers", WorkerViewSet, basename="worker")

urlpatterns = router.urls

