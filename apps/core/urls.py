from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TripViewSet,
    DutyStatusViewSet,
    ELDLogGenerateView,
    ELDLogListView,
    RouteCalculationAPIView,
    CarrierViewSet,
    VehicleViewSet,
)

router = DefaultRouter()
router.register(r"trips", TripViewSet, basename="trip")
router.register(
    r"trips/(?P<trip_id>\d+)/duty-status", DutyStatusViewSet, basename="duty-status"
)
router.register(r"carriers", CarrierViewSet, basename="carrier")
router.register(r"vehicles", VehicleViewSet, basename="vehicle")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "trips/<int:trip_id>/eld-logs/generate/",
        ELDLogGenerateView.as_view(),
        name="eld-log-generate",
    ),
    path(
        "trips/<int:trip_id>/eld-logs/", ELDLogListView.as_view(), name="eld-log-list"
    ),
    path(
        "trips/<int:trip_id>/route/",
        RouteCalculationAPIView.as_view(),
        name="route-calculation",
    ),
]
