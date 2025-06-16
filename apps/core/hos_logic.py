import math
from datetime import datetime, timedelta


class HOSCalculator:
    def __init__(
        self, start_time, current_cycle_hours, pickup_location, dropoff_location
    ):
        self.start_time = start_time
        self.current_cycle_hours = current_cycle_hours
        self.pickup_location = pickup_location
        self.dropoff_location = dropoff_location
        self.duty_statuses = []
        self.miles_since_last_fuel_stop = 0.0

    def calculate_distance(self, coord1, coord2):
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        R = 6371  # Radius of the earth in km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + math.cos(
            math.radians(lat1)
        ) * math.cos(math.radians(lat2)) * math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c * 0.621371  # convert km to miles
        return distance

    def plan_trip(self):
        total_miles = self.calculate_distance(
            self.pickup_location, self.dropoff_location
        )
        avg_speed = 50.0  # mph
        total_driving_hours = total_miles / avg_speed

        current_time = self.start_time
        driving_in_shift = 0.0
        on_duty_in_shift = 0.0
        driving_since_break = 0.0

        # 1. Pickup (1 hour, on-duty not driving)
        self.add_duty_status(
            "ON_DUTY_NOT_DRIVING",
            current_time,
            current_time + timedelta(hours=1),
            "Pickup",
        )
        current_time += timedelta(hours=1)
        on_duty_in_shift += 1.0

        # If the trip is very short, skip the main driving loop
        if total_driving_hours < 1.0:
            self.add_duty_status(
                "ON_DUTY_NOT_DRIVING",
                current_time,
                current_time + timedelta(hours=1),
                "Dropoff",
            )
            current_time += timedelta(hours=1)
            return {"total_miles": total_miles, "duty_statuses": self.duty_statuses}

        # 2. Main Driving Loop
        while total_driving_hours > 0:
            print(f"Starting loop with {total_driving_hours:.2f} hours left")
            print(
                f"Driving time this shift: {driving_in_shift:.2f} hours, On-duty time: {on_duty_in_shift:.2f} hours"
            )

            # Check for end-of-shift (11-hour driving or 14-hour on-duty limit)
            if driving_in_shift >= 11.0 or on_duty_in_shift >= 14.0:
                self.add_duty_status(
                    "OFF_DUTY",
                    current_time,
                    current_time + timedelta(hours=10),
                    "10-hour Reset",
                )
                current_time += timedelta(hours=10)
                driving_in_shift = 0.0
                on_duty_in_shift = 0.0
                driving_since_break = 0.0
                continue

            if self.miles_since_last_fuel_stop >= 1000:
                self.add_duty_status(
                    "ON_DUTY_NOT_DRIVING",
                    current_time,
                    current_time + timedelta(minutes=30),
                    "Fueling Stop",
                )
                current_time += timedelta(minutes=30)
                on_duty_in_shift += 0.5
                self.miles_since_last_fuel_stop = 0.0
                continue

            # Determine the maximum time we can drive before hitting the next limit
            time_to_11h_limit = 11.0 - driving_in_shift
            time_to_14h_limit = 14.0 - on_duty_in_shift
            time_to_break_needed = 8.0 - driving_since_break

            # Drive duration should be the minimum of these limits
            drive_duration = min(
                total_driving_hours,
                time_to_11h_limit,
                time_to_14h_limit,
                time_to_break_needed,
            )

            print(f"Drive duration for this loop: {drive_duration:.2f} hours")

            if drive_duration > 0:
                self.add_duty_status(
                    "DRIVING",
                    current_time,
                    current_time + timedelta(hours=drive_duration),
                    "Driving",
                )
                current_time += timedelta(hours=drive_duration)
                driving_in_shift += drive_duration
                on_duty_in_shift += drive_duration
                driving_since_break += drive_duration
                total_driving_hours -= drive_duration

                print(f"After driving: {driving_since_break:.2f} hours since break")

            # Check if a break is required after driving 8 hours
            if driving_since_break >= 8.0 and total_driving_hours > 0:
                print(
                    f"Taking 30-minute break after {driving_since_break:.2f} hours of driving."
                )
                self.add_duty_status(
                    "ON_DUTY_NOT_DRIVING",
                    current_time,
                    current_time + timedelta(minutes=30),
                    "30-minute break",
                )
                current_time += timedelta(minutes=30)
                on_duty_in_shift += 0.5
                driving_since_break = 0.0  # Reset the break clock

        # Debugging: Final check before returning result
        print("\nFinal Duty Statuses:")
        for duty in self.duty_statuses:
            print(f"Description: {duty['location_description']}")

        # 3. Dropoff (1 hour, on-duty not driving)
        self.add_duty_status(
            "ON_DUTY_NOT_DRIVING",
            current_time,
            current_time + timedelta(hours=1),
            "Dropoff",
        )

        # Debugging: Final check before returning result
        print("\nFinal Duty Statuses Before Returning:")
        for duty in self.duty_statuses:
            print(f"Description: {duty['location_description']}")

        return {"total_miles": total_miles, "duty_statuses": self.duty_statuses}

    def add_duty_status(self, status, start, end, description):
        self.duty_statuses.append(
            {
                "status": status,
                "start_time": start.isoformat(),
                "end_time": end.isoformat(),
                "location_description": description,
            }
        )
        # Add debug print to show the description being added
        print(f"Added duty status: {description}")
