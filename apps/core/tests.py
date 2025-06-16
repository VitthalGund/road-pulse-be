# from django.test import TestCase
# from .hos_logic import HOSCalculator
# from datetime import datetime


# class HOSTestCase(TestCase):
#     def test_short_trip(self):
#         """
#         Tests a short trip that should not require any breaks.
#         """
#         calculator = HOSCalculator(
#             start_time=datetime(2023, 1, 1, 8, 0, 0),
#             current_cycle_hours=10,
#             pickup_location=(34.0522, -118.2437),
#             dropoff_location=(34.1522, -118.2437),
#         )
#         result = calculator.plan_trip()
#         self.assertEqual(len(result["duty_statuses"]), 2)
#         self.assertLess(result["total_miles"], 10)

#     def test_30_min_break(self):
#         """
#         Tests a trip long enough to require a 30-minute break.
#         """
#         calculator = HOSCalculator(
#             start_time=datetime(2023, 1, 1, 8, 0, 0),
#             current_cycle_hours=10,
#             pickup_location=(34.0522, -118.2437),  # Los Angeles
#             dropoff_location=(38.5816, -121.4944),  # Sacramento (~380 miles)
#         )
#         result = calculator.plan_trip()

#         # Debugging: Print duty statuses before assertion
#         print("\nDuty Statuses Before Assertion:")
#         for duty in result["duty_statuses"]:
#             print(f"Description: {duty['location_description']}")

#         # The plan should include a 30-minute break, check for substring match
#         self.assertTrue(
#             any(
#                 "30-minute break" in d["location_description"].lower()
#                 for d in result["duty_statuses"]
#             ),
#             "Expected to find '30-minute break' in duty statuses",
#         )

#     def test_10_hour_reset(self):
#         """
#         Tests a multi-day trip that requires a 10-hour reset.
#         """
#         calculator = HOSCalculator(
#             start_time=datetime(2023, 1, 1, 8, 0, 0),
#             current_cycle_hours=10,
#             pickup_location=(34.0522, -118.2437),  # Los Angeles
#             dropoff_location=(40.7128, -74.0060),  # New York (~2800 miles)
#         )
#         result = calculator.plan_trip()
#         # The plan must be long enough to contain multiple driving segments
#         # due to the mandatory 10-hour breaks.
#         self.assertGreater(len(result["duty_statuses"]), 5)
