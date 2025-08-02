# apps/core/views.py

from rest_framework import viewsets, permissions, generics, status
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Trip, DutyStatus, Vehicle, Carrier, ELDLog
from .serializers import (
    TripSerializer,
    DutyStatusSerializer,
    VehicleSerializer,
    CarrierSerializer,
    ELDLogSerializer,
)
from rest_framework.views import APIView
from datetime import date
from .hos_logic import HOSCalculator
from drf_yasg.utils import swagger_auto_schema  # FIX: Added missing import

User = get_user_model()


class IsAdminOrDriverForRead(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_staff:
            return True
        if (
            hasattr(request.user, "driver")
            and request.method in permissions.SAFE_METHODS
        ):
            return True
        return False


class UserInfoView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response(
            {
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "is_admin": user.is_staff or user.is_superuser,
                "has_driver": hasattr(user, "driver"),
            }
        )


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAdminOrDriverForRead]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Vehicle.objects.all()
        if hasattr(user, "driver") and user.driver.carrier:
            return Vehicle.objects.filter(carrier=user.driver.carrier)
        return Vehicle.objects.none()

    def perform_create(self, serializer):
        if not self.request.user.is_staff:
            raise PermissionDenied("You do not have permission to create a vehicle.")
        serializer.save()


class CarrierViewSet(viewsets.ModelViewSet):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    permission_classes = [permissions.IsAdminUser]


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Trip.objects.all()
        if hasattr(user, "driver"):
            return Trip.objects.filter(driver=user.driver)
        return Trip.objects.none()

    def perform_create(self, serializer):
        user = self.request.user
        if hasattr(user, "driver"):
            serializer.save(driver=user.driver)
        else:
            raise PermissionDenied("You must be a driver to create a trip.")


class DutyStatusViewSet(viewsets.ModelViewSet):
    serializer_class = DutyStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return DutyStatus.objects.filter(trip_id=self.kwargs["trip_pk"])

    def perform_create(self, serializer):
        trip = Trip.objects.get(id=self.kwargs["trip_pk"])
        serializer.save(trip=trip)


class ELDLogViewSet(viewsets.ModelViewSet):
    serializer_class = ELDLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ELDLog.objects.filter(trip_id=self.kwargs["trip_pk"])

    def create(self, request, *args, **kwargs):
        trip_id = self.kwargs.get("trip_pk")
        trip = Trip.objects.get(id=trip_id)
        log_date = request.data.get("date", timezone.now().date())
        log, created = ELDLog.objects.get_or_create(
            trip=trip, date=log_date, defaults={"total_miles": 185.2}
        )
        serializer = self.get_serializer(log)
        status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(serializer.data, status=status_code)


class ELDLogGenerateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Generate ELD log data for a trip on a specific date.",
        responses={201: ELDLogSerializer, 400: "Invalid input", 404: "Trip not found"},
    )
    def post(self, request, trip_id):
        print("Request user:", request.user)
        try:
            if request.user.is_staff:
                trip = Trip.objects.get(id=trip_id)
            else:
                trip = Trip.objects.get(id=trip_id, driver=request.user.driver)
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND
            )

        date_str = request.data.get("date")
        if not date_str:
            return Response(
                {"error": "Date is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            log_date = date.fromisoformat(date_str)
        except ValueError:
            return Response(
                {"error": "Invalid date format"}, status=status.HTTP_400_BAD_REQUEST
            )

        calculator = HOSCalculator(
            start_time=trip.start_time,
            current_cycle_hours=trip.current_cycle_hours,
            pickup_location=trip.get_pickup_location(),
            dropoff_location=trip.get_dropoff_location(),
        )
        route_data = calculator.plan_trip()
        total_miles = route_data.get("total_miles", 0)
        total_idle_hours = request.data.get("total_idle_hours", 0)
        total_engine_hours = request.data.get("total_engine_hours", 0)
        fuel_consumed = request.data.get("fuel_consumed", 0.0)

        eld_log, created = ELDLog.objects.get_or_create(
            trip=trip,
            date=log_date,
            total_idle_hours=total_idle_hours,
            total_engine_hours=total_engine_hours,
            fuel_consumed=fuel_consumed,
            defaults={"total_miles": total_miles},
        )

        serializer = ELDLogSerializer(eld_log, context={"request": request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ELDLogListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List ELD logs for a trip.",
        responses={200: ELDLogSerializer(many=True)},
    )
    def get(self, request, trip_id):
        print("Request user:", request.user)
        try:
            if request.user.is_staff:
                trip = Trip.objects.get(id=trip_id)
            else:
                trip = Trip.objects.get(id=trip_id, driver=request.user.driver)
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND
            )

        eld_logs = ELDLog.objects.filter(trip=trip)
        serializer = ELDLogSerializer(eld_logs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class RouteCalculationAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Calculate route and HOS-compliant schedule for a trip.",
        responses={
            200: DutyStatusSerializer(many=True),
            404: "Trip not found",
            500: "Route calculation failed",
        },
    )
    def post(self, request, trip_id):
        try:
            if request.user.is_staff:
                trip = Trip.objects.get(id=trip_id)
            else:
                trip = Trip.objects.get(id=trip_id, driver=request.user.driver)
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            calculator = HOSCalculator(
                start_time=trip.start_time,
                current_cycle_hours=trip.current_cycle_hours,
                pickup_location=trip.get_pickup_location(),
                dropoff_location=trip.get_dropoff_location(),
            )
            route_data = calculator.plan_trip()
            duty_statuses = route_data.get("duty_statuses", [])
            serializer = DutyStatusSerializer(duty_statuses, many=True)
            return Response(
                {
                    "duty_statuses": serializer.data,
                    "total_miles": route_data.get("total_miles", 0),
                },
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
