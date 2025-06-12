from rest_framework import serializers
from .models import Carrier, Driver, Vehicle, Trip, DutyStatus, ELDLog
from django.contrib.gis.geos import Point


class CarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrier
        fields = ["id", "name", "main_office_address"]


class DriverSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.get_full_name", read_only=True)

    class Meta:
        model = Driver
        fields = ["id", "full_name", "license_number", "carrier"]


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = ["id", "vehicle_number", "license_plate", "state", "carrier"]


class TripSerializer(serializers.ModelSerializer):
    driver = DriverSerializer(read_only=True)
    vehicle = VehicleSerializer(read_only=True)
    current_location = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2, write_only=False
    )
    pickup_location = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2, write_only=False
    )
    dropoff_location = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2, write_only=False
    )

    class Meta:
        model = Trip
        fields = [
            "id",
            "driver",
            "vehicle",
            "current_location",
            "pickup_location",
            "dropoff_location",
            "current_cycle_hours",
            "start_time",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["driver", "created_at", "updated_at"]

    def validate(self, data):
        if (
            data.get("current_cycle_hours", 0) < 0
            or data.get("current_cycle_hours", 0) > 70
        ):
            raise serializers.ValidationError(
                "Current cycle hours must be between 0 and 70."
            )
        vehicle = data.get("vehicle")
        if vehicle and vehicle.carrier != self.context["request"].user.driver.carrier:
            raise serializers.ValidationError(
                "Vehicle must belong to the driver's carrier."
            )
        for field in ["current_location", "pickup_location", "dropoff_location"]:
            coords = data.get(field)
            if coords:
                lon, lat = coords
                if not (-180 <= lon <= 180):
                    raise serializers.ValidationError(
                        {field: "Longitude must be between -180 and 180."}
                    )
                if not (-90 <= lat <= 90):
                    raise serializers.ValidationError(
                        {field: "Latitude must be between -90 and 90."}
                    )
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["current_location"] = [
            instance.current_longitude,
            instance.current_latitude,
        ]
        data["pickup_location"] = [instance.pickup_longitude, instance.pickup_latitude]
        data["dropoff_location"] = [
            instance.dropoff_longitude,
            instance.dropoff_latitude,
        ]
        return data

    def create(self, validated_data):
        current_location = validated_data.pop("current_location")
        pickup_location = validated_data.pop("pickup_location")
        dropoff_location = validated_data.pop("dropoff_location")
        validated_data["driver"] = self.context["request"].user.driver
        trip = Trip.objects.create(
            current_longitude=current_location[0],
            current_latitude=current_location[1],
            pickup_longitude=pickup_location[0],
            pickup_latitude=pickup_location[1],
            dropoff_longitude=dropoff_location[0],
            dropoff_latitude=dropoff_location[1],
            **validated_data
        )
        return trip

    def update(self, instance, validated_data):
        current_location = validated_data.pop("current_location", None)
        pickup_location = validated_data.pop("pickup_location", None)
        dropoff_location = validated_data.pop("dropoff_location", None)
        if current_location:
            instance.current_longitude = current_location[0]
            instance.current_latitude = current_location[1]
        if pickup_location:
            instance.pickup_longitude = pickup_location[0]
            instance.pickup_latitude = pickup_location[1]
        if dropoff_location:
            instance.dropoff_longitude = dropoff_location[0]
            instance.dropoff_latitude = dropoff_location[1]

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class DutyStatusSerializer(serializers.ModelSerializer):
    location = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2, write_only=False
    )

    class Meta:
        model = DutyStatus
        fields = [
            "id",
            "trip",
            "status",
            "start_time",
            "end_time",
            "location",
            "location_description",
            "remarks",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def validate(self, data):
        if data["start_time"] >= data["end_time"]:
            raise serializers.ValidationError("End time must be after start time.")
        coords = data.get("location")
        if coords:
            lon, lat = coords
            if not (-180 <= lon <= 180):
                raise serializers.ValidationError(
                    {"location": "Longitude must be between -180 and 180."}
                )
            if not (-90 <= lat <= 90):
                raise serializers.ValidationError(
                    {"location": "Latitude must be between -90 and 90."}
                )
        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["location"] = [instance.longitude, instance.latitude]
        return data

    def create(self, validated_data):
        location = validated_data.pop("location")
        duty_status = DutyStatus.objects.create(
            longitude=location[0], latitude=location[1], **validated_data
        )
        return duty_status


class ELDLogSerializer(serializers.ModelSerializer):
    duty_statuses = DutyStatusSerializer(many=True, read_only=True)

    class Meta:
        model = ELDLog
        fields = [
            "id",
            "trip",
            "date",
            "total_miles",
            "duty_statuses",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["created_at", "updated_at"]
