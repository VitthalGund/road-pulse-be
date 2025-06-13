from rest_framework import serializers
from .models import Carrier, Driver, Vehicle, Trip, DutyStatus, ELDLog


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
    vehicle = serializers.PrimaryKeyRelatedField(queryset=Vehicle.objects.all())
    current_location = serializers.SerializerMethodField()
    pickup_location = serializers.SerializerMethodField()
    dropoff_location = serializers.SerializerMethodField()
    current_location_input = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2, write_only=True, required=False
    )
    pickup_location_input = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2, write_only=True, required=False
    )
    dropoff_location_input = serializers.ListField(
        child=serializers.FloatField(), min_length=2, max_length=2, write_only=True, required=False
    )

    class Meta:
        model = Trip
        fields = [
            "id",
            "driver",
            "vehicle",
            "current_location",
            "current_location_input",
            "current_location_name",
            "pickup_location",
            "pickup_location_input",
            "pickup_location_name",
            "dropoff_location",
            "dropoff_location_input",
            "dropoff_location_name",
            "current_cycle_hours",
            "start_time",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["driver", "created_at", "updated_at"]

    def get_current_location(self, obj):
        return [obj.current_longitude, obj.current_latitude]

    def get_pickup_location(self, obj):
        return [obj.pickup_longitude, obj.pickup_latitude]

    def get_dropoff_location(self, obj):
        return [obj.dropoff_longitude, obj.dropoff_latitude]

    def validate(self, data):
        for field in [
            "current_location_input",
            "pickup_location_input",
            "dropoff_location_input",
        ]:
            coords = data.get(field)
            if coords:
                lon, lat = coords
                if not (-180 <= lon <= 180):
                    raise serializers.ValidationError({field: "Longitude must be between -180 and 180."})
                if not (-90 <= lat <= 90):
                    raise serializers.ValidationError({field: "Latitude must be between -90 and 90."})

        if data.get("current_cycle_hours", 0) < 0 or data.get("current_cycle_hours", 0) > 70:
            raise serializers.ValidationError("Current cycle hours must be between 0 and 70.")

        vehicle = data.get("vehicle")
        if vehicle and vehicle.carrier != self.context["request"].user.driver.carrier:
            raise serializers.ValidationError("Vehicle must belong to the driver's carrier.")
        return data

    def create(self, validated_data):
        current_location = validated_data.pop("current_location_input", None)
        pickup_location = validated_data.pop("pickup_location_input", None)
        dropoff_location = validated_data.pop("dropoff_location_input", None)

        validated_data["driver"] = self.context["request"].user.driver

        trip = Trip.objects.create(
            current_longitude=current_location[0] if current_location else None,
            current_latitude=current_location[1] if current_location else None,
            pickup_longitude=pickup_location[0] if pickup_location else None,
            pickup_latitude=pickup_location[1] if pickup_location else None,
            dropoff_longitude=dropoff_location[0] if dropoff_location else None,
            dropoff_latitude=dropoff_location[1] if dropoff_location else None,
            **validated_data
        )
        return trip

    def update(self, instance, validated_data):
        current_location = validated_data.pop("current_location_input", None)
        pickup_location = validated_data.pop("pickup_location_input", None)
        dropoff_location = validated_data.pop("dropoff_location_input", None)

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
