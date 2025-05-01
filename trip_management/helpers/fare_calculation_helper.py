import requests
from decimal import Decimal, ROUND_HALF_UP
from driver_app.models import ServiceType
from trip_management.helpers.google_map_helper import (
    calculate_distance_and_time,
    fetch_location_information_from_place_id_using_google_map_api,
    is_in_congestion_zone,
)
from trip_management.models import DistanceTypes
from uc_back import settings


def fetch_location_information_from_place_id(place_id):

    # First find the place from database
    # If not found, fetch the data from google map api.

    fetched_location_id = fetch_location_information_from_place_id_using_google_map_api(
        place_id
    )
    # Todo: add to db

    return fetched_location_id


def calculate_distance_and_minutes_between_two_location(a_lat_lon, b_lat_lon):
    """
    Calculates distance (in miles) and time (in minutes) between two locations using Google Maps Distance Matrix API.
    """
    a_lat, a_lon = a_lat_lon["lat"], a_lat_lon["lon"]
    b_lat, b_lon = b_lat_lon["lat"], b_lat_lon["lon"]
    distance_in_mile, time_in_minutes = calculate_distance_and_time(a_lat, a_lon, b_lat, b_lon)
    print('--------------------------------', distance_in_mile, time_in_minutes)
    return distance_in_mile,time_in_minutes



zone_field_map = {
        DistanceTypes.INNER_LONDON: "inner_london_fare",
        DistanceTypes.ORBITAL_LONDON: "orbital_london_fare",
        DistanceTypes.CENTRAL_LONDON: "central_london_fare",
        DistanceTypes.GREATER_LONDON: "greater_london_fare",
        DistanceTypes.OUTER_LONDON: "outer_london_fare",
        DistanceTypes.OUTER_LONDON_CIRCLE_ONE: "outer_london_circle_one_fare",
        DistanceTypes.OUTER_LONDON_CIRCLE_TWO: "outer_london_circle_two_fare",
        DistanceTypes.OUT_OF_ZONE: "out_of_zone_fare",
    }

def calculate_minute_and_mileage_based_fare(segmented_trip_minutes, segmented_trip_distance):
    """
    Calculate minute and mileage based fare for each service type. with booking fee
    """
    minute_fares = {}
    milage_fares = {}
    try:
        service_types = ServiceType.objects.all()
        if not service_types.exists():
            raise ValueError("No service types found in the database.")
    except Exception as e:
        raise Exception(f"Error fetching service types: {str(e)}")

    for service in service_types:
        service_name = service.service_type
        total_minute_fare = Decimal('0.00')
        total_mileage_fare = Decimal('0.00')
        for zone, minutes in segmented_trip_minutes.items():
            field_name = zone_field_map.get(zone)
            if field_name:
                fare_data = getattr(service, field_name) or {}
                hour_rate = Decimal(str(fare_data.get("per_hour", 0)))
                fare = round(Decimal(str(minutes)) * (hour_rate/ 60), 2)
                total_minute_fare += fare
        
        for zone, distance in segmented_trip_distance.items():
            field_name = zone_field_map.get(zone)
            if field_name:
                fare_data = getattr(service, field_name) or {}
                mile_rate = Decimal(str(fare_data.get("per_mile", 0)))
                fare = round(Decimal(str(distance)) * mile_rate, 2)
                total_mileage_fare += fare

        minute_fares[service_name] = round(total_minute_fare, 2)
        milage_fares[service_name] = round(total_mileage_fare, 2)
    return minute_fares, milage_fares



def calculate_congestion_charge(location):
    """
    Given a location (dict with lat/lon), return congestion charges per service type
    if the location is in the congestion zone.
    """
    if is_in_congestion_zone(location["lat"], location["lon"]):
        service_types = ServiceType.objects.all()
        return {
            service.service_type.upper(): float(service.congestion_charge)
            for service in service_types
        }
    return {}


def add_vat_and_service_charge(vehicle_based_price_list):
    updated_fares = {}
    for service_type, price_data in vehicle_based_price_list.items():
        total_with_cc = Decimal(str(price_data["total_with_congestion_charge"]))
        service_charge = (total_with_cc * Decimal("0.05")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        subtotal = total_with_cc + service_charge
        vat = (subtotal * Decimal("0.20")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        grand_total = subtotal + vat
        updated_fares[service_type] = {
            **price_data,
            "service_charge": float(service_charge),
            "fare_with_service_charge_subtotal": float(subtotal),
            "vat": float(vat),
            "total_fare_with_vat": float(grand_total)
        }
    return updated_fares


def add_concierge_service_charge(request, fare_details):
    """
    Add concierge service charge to the fare details if the user is a concierge.
    Args:
        request: The HTTP request object containing user information.
        fare_details: Dictionary of fare details per service type.
    Returns:
        Updated fare details with concierge service charge added.
    """
    updated_fares = {}
    user = request.user

    for service_type, price_data in fare_details.items():
        final_fare = Decimal(str(price_data["total_fare"]))
        grand_total = Decimal(str(price_data["total_fare_with_vat"]))

        if user.is_authenticated and user.organization:
            org_commission_rate = Decimal(str(user.organization.org_commission)) or 0 # e.g., 10 for 10%
            concierge_service_charge = (final_fare * (org_commission_rate / Decimal('100'))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            final_fare = grand_total + concierge_service_charge
        else:
            # If no organization (not a concierge), use the grand total as is
            concierge_service_charge = Decimal(0.00)
            final_fare = grand_total
        # Update fare details with concierge charge
        updated_fares[service_type] = {
            **price_data,
            "concierge_service_charge": float(concierge_service_charge),
            "total_fare_with_concierge_service_charge": float(final_fare)
        }

    return updated_fares

def calculate_fare_details(service_type, minute_fare, milage_fare, booking_fee, congestion_charge):
    total_fare = minute_fare + milage_fare + booking_fee
    total_with_cc = total_fare + congestion_charge
    return {
        "minute_fare": float(minute_fare),
        "milage_fare": float(milage_fare),
        "booking_fee": float(booking_fee),
        "total_fare": float(total_fare),
        "congestion_charge": float(congestion_charge),
        "total_with_congestion_charge": float(total_with_cc),
    }