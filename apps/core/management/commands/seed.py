from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.core.models import Carrier, Driver, Vehicle

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds the database with a rich set of initial data for testing"

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("--- Seeding Database ---"))

        # Clear existing data to ensure a clean slate
        User.objects.all().delete()
        Carrier.objects.all().delete()
        Driver.objects.all().delete()
        Vehicle.objects.all().delete()
        self.stdout.write(self.style.SUCCESS("Cleared existing data."))

        # --- Create Admin User ---
        User.objects.create_superuser("admin", "admin@example.com", "password123")
        self.stdout.write(self.style.SUCCESS("Successfully created admin user."))

        # --- Create Carrier 1 and its Driver/Vehicles ---
        carrier1 = Carrier.objects.create(
            name="Rapid Logistics",
            main_office_address="100 Freight Way, Los Angeles, CA",
        )
        driver1_user = User.objects.create_user(
            username="driver1",
            password="password123",
            email="driver1@example.com",
            first_name="John",
            last_name="Smith",
        )
        Driver.objects.create(
            user=driver1_user, license_number="RL-JS123", carrier=carrier1
        )
        Vehicle.objects.create(
            vehicle_number="RL-T01",
            license_plate="RAPID1",
            state="CA",
            carrier=carrier1,
        )
        Vehicle.objects.create(
            vehicle_number="RL-T02",
            license_plate="RAPID2",
            state="CA",
            carrier=carrier1,
        )
        self.stdout.write(
            self.style.SUCCESS("Created Rapid Logistics with 1 driver and 2 vehicles.")
        )

        # --- Create Carrier 2 and its Driver/Vehicles ---
        carrier2 = Carrier.objects.create(
            name="Cross Country Haulers",
            main_office_address="200 Long Rd, New York, NY",
        )
        driver2_user = User.objects.create_user(
            username="driver2",
            password="password123",
            email="driver2@example.com",
            first_name="Jane",
            last_name="Doe",
        )
        Driver.objects.create(
            user=driver2_user, license_number="CCH-JD456", carrier=carrier2
        )
        Vehicle.objects.create(
            vehicle_number="CCH-V1", license_plate="HAUL1", state="NY", carrier=carrier2
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Created Cross Country Haulers with 1 driver and 1 vehicle."
            )
        )

        self.stdout.write(self.style.SUCCESS("--- Database Seeding Complete ---"))
