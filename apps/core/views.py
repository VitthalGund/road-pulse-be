from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from .models import Trip, DutyStatus, ELDLog, Carrier, Vehicle
from .serializers import (
    TripSerializer,
    DutyStatusSerializer,
    ELDLogSerializer,
    CarrierSerializer,
    VehicleSerializer,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from datetime import date
from .hos_logic import HOSCalculator
from rest_framework.permissions import IsAdminUser


class TripViewSet(ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Trip.objects.filter(driver=self.request.user.driver)

    @swagger_auto_schema(
        operation_description="Create a new trip for the authenticated driver.",
        responses={201: TripSerializer, 400: "Invalid input"},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="List all trips for the authenticated driver. Filter by status using ?status=PLANNED, etc.",
        responses={200: TripSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        status = request.query_params.get("status")
        if status:
            self.queryset = self.queryset.filter(status=status)
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Retrieve a specific trip.",
        responses={200: TripSerializer, 404: "Trip not found"},
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Update a trip's status or other fields.",
        responses={200: TripSerializer, 400: "Invalid input"},
    )
    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Delete a trip.",
        responses={204: "Trip deleted", 404: "Trip not found"},
    )
    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class DutyStatusViewSet(ModelViewSet):
    serializer_class = DutyStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        trip_id = self.kwargs.get("trip_id")
        return DutyStatus.objects.filter(
            trip__id=trip_id, trip__driver=self.request.user.driver
        )

    @swagger_auto_schema(
        operation_description="Log a duty status change for a trip.",
        responses={201: DutyStatusSerializer, 400: "Invalid input"},
    )
    def create(self, request, *args, **kwargs):
        request.data["trip"] = self.kwargs["trip_id"]
        return super().create(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="List duty statuses for a trip.",
        responses={200: DutyStatusSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


class ELDLogGenerateView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Generate ELD log data for a trip on a specific date.",
        responses={201: ELDLogSerializer, 400: "Invalid input", 404: "Trip not found"},
    )
    def post(self, request, trip_id):
        try:
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

        duty_statuses = DutyStatus.objects.filter(trip=trip, start_time__date=log_date)
        calculator = HOSCalculator(trip)
        _, _, total_miles = calculator.calculate_route()  # Get total miles from route

        eld_log, created = ELDLog.objects.get_or_create(
            trip=trip, date=log_date, defaults={"total_miles": total_miles}
        )

        serializer = ELDLogSerializer(eld_log, context={"request": request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ELDLogListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List ELD logs for a trip.",
        responses={200: ELDLogSerializer(many=True)},
    )
    def get(self, request, trip_id):
        try:
            trip = Trip.objects.get(id=trip_id, driver=request.user.driver)
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND
            )

        eld_logs = ELDLog.objects.filter(trip=trip)
        serializer = ELDLogSerializer(eld_logs, many=True, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class RouteCalculationAPIView(APIView):
    permission_classes = [IsAuthenticated]

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
            trip = Trip.objects.get(id=trip_id, driver=request.user.driver)
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found"}, status=status.HTTP_404_NOT_FOUND
            )

        try:
            calculator = HOSCalculator(trip)
            duty_statuses, geometry = calculator.plan_trip()
            serializer = DutyStatusSerializer(duty_statuses, many=True)
            return Response(
                {"duty_statuses": serializer.data, "geometry": geometry},
                status=status.HTTP_200_OK,
            )
        except ValueError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CarrierViewSet(ModelViewSet):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]

    @swagger_auto_schema(
        operation_description="List all carriers (admin only).",
        responses={200: CarrierSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new carrier (admin only).",
        responses={201: CarrierSerializer, 400: "Invalid input"},
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


class VehicleViewSet(ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_staff:
            return Vehicle.objects.all()
        return Vehicle.objects.filter(carrier=self.request.user.driver.carrier)

    @swagger_auto_schema(
        operation_description="List vehicles for the authenticated driver's carrier or all vehicles (admin).",
        responses={200: VehicleSerializer(many=True)},
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_description="Create a new vehicle (admin only).",
        responses={201: VehicleSerializer, 400: "Invalid input"},
    )
    def create(self, request, *args, **kwargs):
        if not request.user.is_staff:
            return Response({"error": "Admin only"}, status=status.HTTP_403_FORBIDDEN)
        return super().create(request, *args, **kwargs)
