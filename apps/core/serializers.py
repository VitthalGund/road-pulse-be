from rest_framework import serializers
from .models import Trip, Vehicle, Carrier, DutyStatus, ELDLog


# Custom field to correctly serialize a GeoDjango PointField to a list
class PointField(serializers.Field):
    """
    A custom field to serialize a GeoDjango Point object to a [lon, lat] list.
    """

    def to_representation(self, value):
        if value is None:
            return None
        return [value.x, value.y]


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = "__all__"


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = "__all__"


class TripSerializer(serializers.ModelSerializer):
    # --- Read-only fields for displaying data ---
    vehicle = VehicleSerializer(read_only=True)
    current_location = PointField(read_only=True)
    pickup_location = PointField(read_only=True)
    dropoff_location = PointField(read_only=True)

    # --- Write-only fields for creating/updating a trip ---
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset=Vehicle.objects.all(), source="vehicle", write_only=True
    )
    current_location_input = serializers.ListField(
        child=serializers.FloatField(), write_only=True
    )
    pickup_location_input = serializers.ListField(
        child=serializers.FloatField(), write_only=True
    )
    dropoff_location_input = serializers.ListField(
        child=serializers.FloatField(), write_only=True
    )

    class Meta:
        model = Trip
        fields = [
            "id",
            "driver",
            "vehicle",
            "vehicle_id",
            "current_location_name",
            "current_location",
            "current_location_input",
            "pickup_location_name",
            "pickup_location",
            "pickup_location_input",
            "dropoff_location_name",
            "dropoff_location",
            "dropoff_location_input",
            "current_cycle_hours",
            "start_time",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ("driver",)

    def create(self, validated_data):
        driver = self.context["request"].user.driver

        current_coords = validated_data.pop("current_location_input")
        pickup_coords = validated_data.pop("pickup_location_input")
        dropoff_coords = validated_data.pop("dropoff_location_input")

        vehicle_instance = validated_data.pop("vehicle")

        trip = Trip.objects.create(
            driver=driver,
            vehicle=vehicle_instance,
            current_longitude=current_coords[0],
            current_latitude=current_coords[1],
            pickup_longitude=pickup_coords[0],
            pickup_latitude=pickup_coords[1],
            dropoff_longitude=dropoff_coords[0],
            dropoff_latitude=dropoff_coords[1],
            **validated_data
        )
        return trip


class DutyStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = DutyStatus
        fields = "__all__"


class ELDLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = ELDLog
        fields = "__all__"
