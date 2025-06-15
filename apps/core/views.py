from rest_framework.viewsets import ModelViewSet
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
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
from datetime import date
from .hos_logic import HOSCalculator


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


class UserInfoView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "user_id": request.user.id,
                "username": request.user.username,
                "has_driver": hasattr(request.user, "driver"),
                "email": request.user.email,
                "first_name": request.user.first_name,
                "last_name": request.user.last_name,
                "is_admin": request.user.is_staff,
            }
        )


class TripViewSet(viewsets.ModelViewSet):
    queryset = Trip.objects.all()
    serializer_class = TripSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Trip.objects.all()
        return Trip.objects.filter(driver__user=user)

    @action(detail=True, methods=["post"])
    def calculate_route(self, request, pk=None):
        trip = self.get_object()
        calculator = HOSCalculator(
            trip.start_time,
            trip.current_cycle_hours,
            trip.pickup_location,
            trip.dropoff_location,
        )
        route_data = calculator.plan_trip()
        return Response(route_data)


class VehicleViewSet(viewsets.ModelViewSet):
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAdminUser]


class CarrierViewSet(viewsets.ModelViewSet):
    queryset = Carrier.objects.all()
    serializer_class = CarrierSerializer
    permission_classes = [permissions.IsAdminUser]


class DutyStatusViewSet(viewsets.ModelViewSet):
    queryset = DutyStatus.objects.all()
    serializer_class = DutyStatusSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        trip_id = self.kwargs["trip_pk"]
        return DutyStatus.objects.filter(trip_id=trip_id)


class ELDLogViewSet(viewsets.ModelViewSet):
    queryset = ELDLog.objects.all()
    serializer_class = ELDLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        trip_id = self.kwargs["trip_pk"]
        return ELDLog.objects.filter(trip_id=trip_id)
