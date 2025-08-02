from django.db import models
from django.contrib.auth.models import User


class Carrier(models.Model):
    name = models.CharField(max_length=255)
    main_office_address = models.CharField(max_length=255)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name


class Driver(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    carrier = models.ForeignKey(
        Carrier, on_delete=models.CASCADE, related_name="drivers"
    )
    license_number = models.CharField(max_length=50, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["license_number"]),
        ]

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.license_number})"


class Vehicle(models.Model):
    carrier = models.ForeignKey(
        Carrier, on_delete=models.CASCADE, related_name="vehicles"
    )
    vehicle_number = models.CharField(max_length=50, unique=True)
    license_plate = models.CharField(max_length=20)
    state = models.CharField(max_length=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["vehicle_number"]),
        ]

    def __str__(self):
        return f"{self.vehicle_number} ({self.license_plate})"


class Trip(models.Model):
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name="trips")
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name="trips")
    current_longitude = models.FloatField()
    current_latitude = models.FloatField()
    current_location_name = models.CharField(max_length=255, blank=True)
    pickup_longitude = models.FloatField()
    pickup_latitude = models.FloatField()
    pickup_location_name = models.CharField(max_length=255, blank=True)
    dropoff_longitude = models.FloatField()
    dropoff_latitude = models.FloatField()
    dropoff_location_name = models.CharField(max_length=255, blank=True)
    current_cycle_hours = models.FloatField(default=0.0)
    start_time = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("PLANNED", "Planned"),
            ("IN_PROGRESS", "In Progress"),
            ("COMPLETED", "Completed"),
        ],
        default="PLANNED",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["driver", "start_time"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"Trip {self.id} for {self.driver}"

    def get_current_location(self):
        return [self.current_longitude, self.current_latitude]

    def get_pickup_location(self):
        return [self.pickup_longitude, self.pickup_latitude]

    def get_dropoff_location(self):
        return [self.dropoff_longitude, self.dropoff_latitude]


class DutyStatus(models.Model):
    trip = models.ForeignKey(
        Trip, on_delete=models.CASCADE, related_name="duty_statuses"
    )
    status = models.CharField(
        max_length=20,
        choices=[
            ("OFF_DUTY", "Off Duty"),
            ("SLEEPER_BERTH", "Sleeper Berth"),
            ("DRIVING", "Driving"),
            ("ON_DUTY_NOT_DRIVING", "On Duty Not Driving"),
        ],
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    longitude = models.FloatField()
    latitude = models.FloatField()
    location_description = models.CharField(max_length=255)
    remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["trip", "start_time"]),
        ]

    def get_location(self):
        return [self.longitude, self.latitude]

    def __str__(self):
        return f"{self.status} for Trip {self.trip.id}"


class ELDLog(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="eld_logs")
    date = models.DateField()
    total_miles = models.FloatField()
    fuel_consumed = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Fuel consumed in gallons",
        null=True,
        blank=True,
    )
    total_engine_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total engine hours for the day",
        null=True,
        blank=True,
    )
    total_idle_hours = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total engine idle hours for the day",
        null=True,
        blank=True,
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("trip", "date")
        db_table = "eld_logs"
        indexes = [
            models.Index(fields=["trip", "date"]),
        ]

    def __str__(self):
        return f"ELD Log for Trip {self.trip.id} on {self.date}"
