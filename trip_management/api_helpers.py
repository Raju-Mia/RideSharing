import requests
from trip_management.helpers import calculate_distance_and_time
from uc_back import settings
from asgiref.sync import sync_to_async
from .models import Trip, TripBreak, ExtraCharge
from decimal import Decimal
import googlemaps
import logging
import re
# from accounts.models import VehicleTypes, VehicleModel
from shapely.geometry import Point, Polygon
from trip_management.polygons import CONGESTION_ZONE
from driver_app.models import (
    Driver,
    DriverStatus,
    # DriverAttachmentStatus,
    # Manufacturer,
    Vehicle,
    VehicleModel,
    VehicleStatus,
    VehicleTypes,
    # VehicleTypesInfo,
    AttachmentStatus,
)

from shapely.geometry import Point
from trip_management.polygons import POLYGONS
from .models import TripMethod, DistanceTypes
from rest_framework import status

api_key = settings.GOOGLE_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import requests
from django.conf import settings

# def fetch_location_information_from_place_id(place_id):
#     url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}"

#     response = requests.get(url)

#     if response.status_code != 200:
#         return {"error": "Failed to fetch data from Google Places API"}

#     data = response.json()

#     if "result" not in data:
#         return {"error": "Invalid place_id or no data found"}

#     result = data["result"]
#     address_components = {comp["types"][0]: comp["long_name"] for comp in result.get("address_components", [])}
#     location_name = result.get("name")
#     street_name= address_components.get("route")
#     route= address_components.get("route")
#     post_code= address_components.get("postal_code")
#     locality= address_components.get("locality")
#     city= address_components.get("administrative_area_level_2")
#     country= address_components.get("country")
#     return location_name, street_name, route, post_code, locality, city, country


def validate_trip_method(trip_method):
    if trip_method not in [method[0] for method in TripMethod.choices]:
        return {"error": "Invalid trip_method"}, status.HTTP_400_BAD_REQUEST
    return None


def validate_required_fields(data, trip_method, is_get_request=False):
    required_fields = {
        TripMethod.AIRPORT_TRANSFER: [
            "pickup_location_name",
            "pickup_location_lat",
            "pickup_location_lng",
            "initial_dropoff_location_name",
            "initial_dropoff_location_lat",
            "initial_dropoff_location_lng",
            "flight_number",
        ],
        TripMethod.ONE_WAY: [
            "pickup_location_name",
            "pickup_location_lat",
            "pickup_location_lng",
            "initial_dropoff_location_name",
            "initial_dropoff_location_lat",
            "initial_dropoff_location_lng",
        ],
        TripMethod.AS_DIRECTED: [
            "pickup_location_name",
            "pickup_location_lat",
            "pickup_location_lng",
            "approximate_duration",
        ],
    }

    if not is_get_request:
        passenger_fields = [
            "passenger_name",
            "passenger_phone_number",
            "passenger_email",
            "number_of_adult_passengers",
            "number_of_child_passengers",
        ]
        for fields in required_fields.values():
            fields.extend(passenger_fields)

    missing_fields = []
    for field in required_fields.get(trip_method, []):
        if field not in data or data.get(field) is None or data.get(field) == "":
            missing_fields.append(field)

    if missing_fields:
        return {
            field: "This field is required." for field in missing_fields
        }, status.HTTP_400_BAD_REQUEST

    return None


def get_estimated_fares(data, trip_method):
    pickup_lat = data.get("pickup_location_lat")
    pickup_lng = data.get("pickup_location_lng")
    dropoff_lat = data.get("initial_dropoff_location_lat")
    dropoff_lng = data.get("initial_dropoff_location_lng")

    SERVICE_PERCENTAGE = 5
    VAT_PERCENTAGE = 20

    try:
        distance_miles, time_minutes = calculate_distance_and_time(
            pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
        )
    except Exception as e:
        distance_miles, time_minutes = 0, 0

    if trip_method == TripMethod.AS_DIRECTED:
        try:
            time_minutes = float(data.get("approximate_duration", 0))
        except ValueError:
            return (
                None,
                {"error": "Invalid approximate_duration format."},
                status.HTTP_400_BAD_REQUEST,
            )
        distance_miles = 0

    distance_type = get_distance_type_from_location(pickup_lat, pickup_lng)

    if distance_type not in [choice[0] for choice in DistanceTypes.choices]:
        return None, {"error": "Invalid distance_type"}, status.HTTP_400_BAD_REQUEST

    vehicles = VehicleModel.objects.filter(service_type__isnull=False)
    service_type_groups = {}
    in_congestion_zone = is_in_congestion_zone(
        pickup_lat, pickup_lng
    ) or is_in_congestion_zone(dropoff_lat, dropoff_lng)

    for vehicle in vehicles:
        booking_fee = float(vehicle.booking_fee)
        CONGESTION_CHARGE = (
            float(vehicle.congestion_charge) if in_congestion_zone else 0.00
        )
        fares = {
            DistanceTypes.INNER_LONDON: vehicle.inner_london_fare,
            DistanceTypes.CENTRAL_LONDON: vehicle.central_london_fare,
            DistanceTypes.ORBITAL_LONDON: vehicle.orbital_london_fare,
            DistanceTypes.GREATER_LONDON: vehicle.greater_london_fare,
            DistanceTypes.OUTER_LONDON: vehicle.outer_london_fare,
            DistanceTypes.OUTER_LONDON_CIRCLE_ONE: vehicle.outer_london_circle_one_fare,
            DistanceTypes.OUTER_LONDON_CIRCLE_TWO: vehicle.outer_london_circle_two_fare,
        }

        fare_info = fares.get(distance_type, {})
        if fare_info:
            per_mile = float(fare_info.get("per_mile", 0))
            per_hour = float(fare_info.get("per_hour", 0))

            fare_for_distance = per_mile * distance_miles
            fare_for_time = (per_hour / 60) * time_minutes
            base_fare = (
                float(fare_for_distance) + float(fare_for_time) + float(booking_fee)
            )

            total_fare = base_fare + CONGESTION_CHARGE
            total_fare += (SERVICE_PERCENTAGE / 100) * total_fare
            total_fare += (VAT_PERCENTAGE / 100) * total_fare

            vehicle_info = {
                "year_of_manufacture": vehicle.year_of_manufacture,
                "model": vehicle.model,
                "manufacturer": vehicle.manufacturer,
                "per_mile": per_mile,
                "per_hour": per_hour,
                "booking_fee": booking_fee,
                "congestion_charge": CONGESTION_CHARGE,
                "estimated_fare": round(total_fare, 2),
            }

            if vehicle.service_type not in service_type_groups:
                service_type_groups[vehicle.service_type] = {
                    "service_type": vehicle.service_type,
                    "estimated_fare_min": total_fare,
                    "estimated_fare_max": total_fare,
                    "vehicles": [],
                }

            group = service_type_groups[vehicle.service_type]
            group["estimated_fare_min"] = min(group["estimated_fare_min"], total_fare)
            group["estimated_fare_max"] = max(group["estimated_fare_max"], total_fare)
            group["vehicles"].append(vehicle_info)

    vehicle_fares = list(service_type_groups.values())
    for group in vehicle_fares:
        group["estimated_fare_min"] = round(group["estimated_fare_min"], 2)
        group["estimated_fare_max"] = round(group["estimated_fare_max"], 2)

    if not vehicle_fares:
        return (
            None,
            {"error": "No fare information found for the specified distance type"},
            status.HTTP_404_NOT_FOUND,
        )

    return vehicle_fares, None


def is_in_congestion_zone(lat, lng):
    """
    Check if a given latitude and longitude falls within the congestion zone.
    """
    point = Point(lat, lng)
    result = CONGESTION_ZONE.contains(point)
    return result


def get_distance_type_from_location(lat, lng):
    """
    Returns the distance type (e.g., INNER_LONDON, OUTER_LONDON) based on the provided latitude and longitude.
    """
    point = Point(lng, lat)
    for distance_type, polygon in POLYGONS.items():
        if polygon.contains(point):
            return distance_type
    return "Greater London"


# def get_distance_type_from_location(lat, lng):
#     """
#     Determines the distance type based on the pickup location coordinates.
#     This is a placeholder function. Implement the actual logic as per your requirements.
#     """
#     # Example logic (replace with real implementation)
#     if 51.50 <= lat <= 51.52 and -0.12 <= lng <= -0.10:
#         return DistanceTypes.INNER_LONDON
#     elif 51.40 <= lat <= 51.49 and -0.15 <= lng <= -0.05:
#         return DistanceTypes.CENTRAL_LONDON
#     # Add more conditions based on your distance type definitions
#     else:
#         return DistanceTypes.GREATER_LONDON
