# from accounts.models import Vehicle, Driver
# # from trip_management.model_helpers import calculate_distance
# from uc_admin.serializers.old_views_serializers import NearestDriversInfoSerializer
# # from trip_management.helpers import trip_conflict_existsV3
# from trip_management.models import Trip


# def get_drivers_for_dispatch(trip):
#     pickup_location = trip.pickup_location
#     drop_off_location = trip.drop_off_location
#     duration = int(trip.estimated_time) / 3600
#     all_available_drivers = Driver.objects.filter(status="verified")

#     driver_data = []
#     for driver in all_available_drivers:
#         if hasattr(driver, "vehicle"):
#             calculated_distance, apprx_duration_from_pickup_point = calculate_distance(
#                 pickup_location.strip(), driver.vehicle.current_location.strip()
#             )
#             serializer = NearestDriversInfoSerializer(driver)
#             new_dict = {"distance_from_location": float(calculated_distance) / 1609.344}
#             new_dict.update(serializer.data)
#             driver_data.append(new_dict)
#         else:
#             pass

#     sorted_data = sorted(driver_data, key=lambda d: d["distance_from_location"])
#     return sorted_data


# def get_drivers_v2(trip_id):
#     """
#     Return sorted list of drivers those matches the given trip requirements
#     Args:
#         required_vehicle_type:
#         pickup_location:
#         required_vehicle_capacity:
#         required_vehicle_luggage_capacity:

#     Returns:

#     """
#     trip = Trip.objects.get(id=trip_id)

#     required_vehicle_type = trip.vehicle_type
#     pickup_location = trip.pickup_location
#     drop_off_location = trip.drop_off_location
#     required_vehicle_capacity = trip.number_of_passengers
#     required_vehicle_luggage_capacity = trip.luggage_size if trip.luggage_size else None
#     duration = int(trip.estimated_time) / 3600
#     all_available_drivers = Driver.objects.filter(status="verified")
#     if required_vehicle_luggage_capacity is not None:
#         eligible_drivers = Driver.objects.filter(
#             vehicle__vehicle_type=required_vehicle_type,
#             vehicle__maximum_passengers__gte=required_vehicle_capacity,
#             status="verified",
#         )
#         driver_data = []
#         for driver in eligible_drivers:
#             has_conflict, note = trip_conflict_existsV3(
#                 trip.date, trip.pickup_time, duration, user=driver, driver=True
#             )
#             if has_conflict:
#                 continue
#             else:
#                 (
#                     calculated_distance,
#                     apprx_duration_from_pickup_point,
#                 ) = calculate_distance(
#                     pickup_location.strip(), driver.vehicle.current_location.strip()
#                 )
#                 serializer = NearestDriversInfoSerializer(driver)
#                 new_dict = {
#                     "distance_from_location": int(float(calculated_distance) / 1609.344)
#                 }
#                 new_dict.update(serializer.data)
#                 driver_data.append(new_dict)

#         sorted_data = sorted(driver_data, key=lambda d: d["distance_from_location"])
#         return sorted_data
#     else:
#         eligible_drivers = Driver.objects.filter(
#             vehicle__vehicle_type=required_vehicle_type,
#             vehicle__maximum_passengers__gte=required_vehicle_capacity,
#             status="verified",
#         )
#         driver_data = []
#         for driver in eligible_drivers:
#             has_conflict, note = trip_conflict_existsV3(
#                 trip.date, trip.pickup_time, duration, user=driver
#             )
#             if has_conflict:
#                 continue
#             else:
#                 (
#                     calculated_distance,
#                     apprx_duration_from_pickup_point,
#                 ) = calculate_distance(
#                     pickup_location.strip(), driver.vehicle.current_location.strip()
#                 )
#                 serializer = NearestDriversInfoSerializer(driver)
#                 new_dict = {
#                     "distance_from_location": int(float(calculated_distance) / 1609.344)
#                 }
#                 new_dict.update(serializer.data)
#                 driver_data.append(new_dict)

#         sorted_data = sorted(driver_data, key=lambda d: d["distance_from_location"])
#         return sorted_data
