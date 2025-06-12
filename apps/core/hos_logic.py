from datetime import timedelta
from django.conf import settings
import requests
from .models import DutyStatus


class HOSCalculator:
    def __init__(self, trip):
        self.trip = trip
        self.api_key = settings.GRAPHHOPPER_API_KEY
        self.headers = {"User-Agent": settings.NOMINATIM_USER_AGENT}

    def geocode_location(self, location_name):
        url = (
            f"https://nominatim.openstreetmap.org/search?q={location_name}&format=json"
        )
        response = requests.get(url, headers=self.headers)
        data = response.json()
        if data:
            return float(data[0]["lon"]), float(data[0]["lat"])
        raise ValueError(f"Could not geocode location: {location_name}")

    def calculate_route(self):
        coords = [
            (self.trip.current_longitude, self.trip.current_latitude),
            (self.trip.pickup_longitude, self.trip.pickup_latitude),
            (self.trip.dropoff_longitude, self.trip.dropoff_latitude),
        ]
        url = (
            f"https://graphhopper.com/api/1/route?point={coords[0][1]},{coords[0][0]}"
            f"&point={coords[1][1]},{coords[1][0]}&point={coords[2][1]},{coords[2][0]}"
            f"&vehicle=truck&key={self.api_key}"
        )
        response = requests.get(url)
        data = response.json()
        if "paths" not in data:
            raise ValueError("Failed to calculate route")
        distance = data["paths"][0]["distance"] / 1000
        duration = data["paths"][0]["time"] / 3600 / 1000
        geometry = data["paths"][0]["points"]
        return distance, duration, geometry

    def get_interpolated_location(self, geometry, fraction):
        lon = (
            self.trip.pickup_longitude
            + (self.trip.dropoff_longitude - self.trip.pickup_longitude) * fraction
        )
        lat = (
            self.trip.pickup_latitude
            + (self.trip.dropoff_latitude - self.trip.pickup_latitude) * fraction
        )
        return [lon, lat]

    def plan_trip(self):
        distance, duration, geometry = self.calculate_route()
        current_time = self.trip.start_time
        duty_statuses = []
        total_miles = distance * 0.621371

        duty_statuses.append(
            {
                "status": "ON_DUTY_NOT_DRIVING",
                "start_time": current_time,
                "end_time": current_time + timedelta(hours=1),
                "longitude": self.trip.pickup_longitude,
                "latitude": self.trip.pickup_latitude,
                "location_description": "Pickup",
            }
        )
        current_time += timedelta(hours=1)

        fueling_stops = int(distance / 1609.34)
        driving_hours = 0
        on_duty_hours = 1
        remaining_cycle = 70 - self.trip.current_cycle_hours
        distance_covered = 0

        for i in range(fueling_stops + 1):
            segment_distance = min(1609.34, distance - (i * 1609.34))
            segment_duration = (segment_distance / distance) * duration
            distance_covered += segment_distance
            fraction = distance_covered / distance

            if driving_hours + segment_duration > 8:
                interpolated = self.get_interpolated_location(geometry, fraction)
                duty_statuses.append(
                    {
                        "status": "OFF_DUTY",
                        "start_time": current_time,
                        "end_time": current_time + timedelta(minutes=30),
                        "longitude": interpolated[0],
                        "latitude": interpolated[1],
                        "location_description": "Rest Break",
                    }
                )
                current_time += timedelta(minutes=30)
                on_duty_hours += 0.5

            interpolated = self.get_interpolated_location(geometry, fraction)
            duty_statuses.append(
                {
                    "status": "DRIVING",
                    "start_time": current_time,
                    "end_time": current_time + timedelta(hours=segment_duration),
                    "longitude": interpolated[0],
                    "latitude": interpolated[1],
                    "location_description": "Driving",
                }
            )
            current_time += timedelta(hours=segment_duration)
            driving_hours += segment_duration
            on_duty_hours += segment_duration

            if i < fueling_stops:
                interpolated = self.get_interpolated_location(geometry, fraction)
                duty_statuses.append(
                    {
                        "status": "ON_DUTY_NOT_DRIVING",
                        "start_time": current_time,
                        "end_time": current_time + timedelta(hours=1),
                        "longitude": interpolated[0],
                        "latitude": interpolated[1],
                        "location_description": "Fueling Stop",
                    }
                )
                current_time += timedelta(hours=1)
                on_duty_hours += 1

        duty_statuses.append(
            {
                "status": "ON_DUTY_NOT_DRIVING",
                "start_time": current_time,
                "end_time": current_time + timedelta(hours=1),
                "longitude": self.trip.dropoff_longitude,
                "latitude": self.trip.dropoff_latitude,
                "location_description": "Dropoff",
            }
        )
        on_duty_hours += 1

        if on_duty_hours > remaining_cycle:
            raise ValueError("Trip exceeds 70-hour limit")

        for status in duty_statuses:
            DutyStatus.objects.create(
                trip=self.trip,
                status=status["status"],
                start_time=status["start_time"],
                end_time=status["end_time"],
                longitude=status["longitude"],
                latitude=status["latitude"],
                location_description=status["location_description"],
                remarks=status.get("remarks", ""),
            )

        return duty_statuses, geometry, total_miles
