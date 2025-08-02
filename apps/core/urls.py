from django.urls import path, include
from rest_framework_nested import routers
from .views import (
    TripViewSet,
    DutyStatusViewSet,
    VehicleViewSet,
    CarrierViewSet,
    ELDLogViewSet,
    UserInfoView,
    ELDLogGenerateView,
    ELDLogListView,
    RouteCalculationAPIView,
)

# Main router for top-level resources
router = routers.DefaultRouter()
router.register(r"trips", TripViewSet, basename="trip")
router.register(r"vehicles", VehicleViewSet, basename="vehicle")
router.register(r"carriers", CarrierViewSet, basename="carrier")

# Nested router for resources within a trip
trips_router = routers.NestedSimpleRouter(router, r"trips", lookup="trip")
trips_router.register(r"duty-status", DutyStatusViewSet, basename="trip-duty-statuses")
trips_router.register(r"eld-logs", ELDLogViewSet, basename="trip-eld-logs")

# URL patterns for the core app
urlpatterns = [
    path("user-info/", UserInfoView.as_view(), name="user-info"),
    # FIX: Correctly wired up the standalone views
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
    path("", include(router.urls)),
    path("", include(trips_router.urls)),
]
