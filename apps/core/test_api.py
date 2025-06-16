from django.contrib.auth import get_user_model
from django.contrib.gis.geos import Point
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.core.models import Carrier, Driver, Vehicle, Trip
from datetime import datetime, timedelta

User = get_user_model()


class RoadPulseAPITestCase(APITestCase):
    """
    Comprehensive test suite for the RoadPulse API using Django's APITestCase.
    """

    def setUp(self):
        """Set up a rich test environment with multiple users, carriers, and vehicles."""
        self.client = APIClient()

        # Admin User
        self.admin_user = User.objects.create_superuser(
            "admin", "admin@example.com", "adminpass"
        )

        # Carrier 1
        self.carrier1 = Carrier.objects.create(
            name="Rapid Logistics", main_office_address="123 Rapid St"
        )
        self.driver1_user = User.objects.create_user(
            "driver1", "driver1@example.com", "driverpass"
        )
        self.driver1 = Driver.objects.create(
            user=self.driver1_user, license_number="D1", carrier=self.carrier1
        )
        self.vehicle1 = Vehicle.objects.create(
            vehicle_number="V1", license_plate="V1LP", state="CA", carrier=self.carrier1
        )

        # Carrier 2
        self.carrier2 = Carrier.objects.create(
            name="Cross Country", main_office_address="456 Cross St"
        )
        self.driver2_user = User.objects.create_user(
            "driver2", "driver2@example.com", "driverpass"
        )
        self.driver2 = Driver.objects.create(
            user=self.driver2_user, license_number="D2", carrier=self.carrier2
        )
        self.vehicle2 = Vehicle.objects.create(
            vehicle_number="V2", license_plate="V2LP", state="NY", carrier=self.carrier2
        )

        # Log in as driver1 to create the initial trip via the API
        self._login_as("driver1")
        trip_data = {
            "vehicle_id": self.vehicle1.id,
            "start_time": datetime.now().isoformat() + "Z",
            "current_cycle_hours": 10,
            "current_location_name": "Los Angeles, CA",
            "current_location_input": [-118.0, 34.0],
            "pickup_location_name": "Los Angeles, CA",
            "pickup_location_input": [-118.0, 34.0],
            "dropoff_location_name": "San Francisco, CA",
            "dropoff_location_input": [-122.0, 37.0],
        }
        response = self.client.post("/api/trips/", trip_data, format="json")
        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
            f"Failed to create trip in setUp. Errors: {response.data}",
        )
        self.trip1 = Trip.objects.get(id=response.data["id"])

    def _login_as(self, user_type):
        """Helper to log in as a specific user type."""
        if user_type == "admin":
            self.client.force_authenticate(user=self.admin_user)
        elif user_type == "driver1":
            self.client.force_authenticate(user=self.driver1_user)
        elif user_type == "driver2":
            self.client.force_authenticate(user=self.driver2_user)
        else:
            self.client.force_authenticate(user=None)

    # --- Vehicle API Tests ---
    def test_admin_can_list_all_vehicles(self):
        self._login_as("admin")
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_driver_cannot_list_vehicles(self):
        self._login_as("driver1")
        response = self.client.get("/api/vehicles/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_vehicle(self):
        self._login_as("admin")
        data = {
            "vehicle_number": "V3",
            "license_plate": "V3LP",
            "state": "TX",
            "carrier": self.carrier1.id,
        }
        response = self.client.post("/api/vehicles/", data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Vehicle.objects.count(), 3)

    def test_driver_cannot_create_vehicle(self):
        self._login_as("driver1")
        data = {
            "vehicle_number": "V3",
            "license_plate": "V3LP",
            "state": "TX",
            "carrier": self.carrier1.id,
        }
        response = self.client.post("/api/vehicles/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Carrier API Tests ---
    def test_admin_can_list_carriers(self):
        self._login_as("admin")
        response = self.client.get("/api/carriers/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_driver_cannot_create_carrier(self):
        self._login_as("driver1")
        data = {"name": "Rogue Carrier", "main_office_address": "1 Hacker Way"}
        response = self.client.post("/api/carriers/", data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    # --- Trip API Tests ---
    def test_driver_can_create_trip(self):
        self._login_as("driver1")
        trip_count_before = Trip.objects.count()
        data = {
            "vehicle_id": self.vehicle1.id,  # <-- FIX: Corrected key
            "start_time": (datetime.now() + timedelta(days=1)).isoformat() + "Z",
            "current_cycle_hours": 20,
            "current_location_name": "LA",
            "current_location_input": [-118.0, 34.0],
            "pickup_location_name": "LA",
            "pickup_location_input": [-118.0, 34.0],
            "dropoff_location_name": "NYC",
            "dropoff_location_input": [-74.0, 40.0],
        }
        response = self.client.post("/api/trips/", data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Trip.objects.count(), trip_count_before + 1)

    def test_driver_can_list_only_their_own_trips(self):
        self._login_as("driver1")
        response = self.client.get("/api/trips/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], self.trip1.id)

    def test_driver_cannot_view_another_drivers_trip(self):
        self._login_as("driver2")
        response = self.client.get(f"/api/trips/{self.trip1.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_view_any_trip(self):
        self._login_as("admin")
        response = self.client.get(f"/api/trips/{self.trip1.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_trip_update_and_delete(self):
        self._login_as("driver1")
        # Test PATCH
        response = self.client.patch(
            f"/api/trips/{self.trip1.id}/", {"status": "IN_PROGRESS"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "IN_PROGRESS")

        # Test DELETE
        response = self.client.delete(f"/api/trips/{self.trip1.id}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Trip.objects.count(), 0)

    def test_unauthenticated_access_is_denied(self):
        self._login_as(None)  # Log out
        response = self.client.get("/api/trips/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
