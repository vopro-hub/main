from django.urls import path
from . import views_public

urlpatterns = [
    path("cities/", views_public.PublicCitiesView.as_view(), name="public-cities"),
    path("city/<slug:slug>/", views_public.PublicCityOfficesView.as_view(), name="public-city-offices"),
    path("offices/<slug:slug>/", views_public.PublicOfficeDetailView.as_view(), name="public-office-detail"),
    path("rooms/", views_public.PublicRoomView.as_view(), name="public-office-rooms"),
    path("workers/", views_public.PublicWorkerView.as_view(), name="public-workers"),
    path("worker/login/", views_public.WorkerPresenceViewSet.as_view({"post": "login"}), name="worker-presence-login"),
    path("worker/logout/", views_public.WorkerPresenceViewSet.as_view({"post": "logout"}), name="worker-presence-logout"),
    path("rooms/submit_access/<int:room_id>/", views_public.PublicRoomAccessSubmit.as_view(), name="public-room-submit-access"),
    path("rooms/validate_access/", views_public.PublicRoomAccessValidate.as_view(), name="public-room-validate-access"),
    path("receptionist/office/", views_public.GetCurrentOffice.as_view(), name="office"),

]
