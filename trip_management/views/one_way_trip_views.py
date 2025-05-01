from collections import defaultdict
from django.utils import timezone
from decimal import Decimal
from driver_app.models import ServiceType
from trip_management.helpers import (
    fetch_location_information_from_place_id,
    calculate_distance_and_minutes_between_two_location,
    calculate_minute_and_mileage_based_fare,
    calculate_congestion_charge, 
    add_vat_and_service_charge,
    calculate_fare_details,
    add_concierge_service_charge,
    calculate_route_segments,
)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from trip_management.models import Trip




class OneWayTripFareCalculation(APIView):
    def post(self, request):
        pickup_place_id = request.data.get("pickup_place_id")
        stopage_place_ids_dict = request.data.get("stopage_place_ids", {})
        dropoff_place_id = request.data.get("dropoff_place_id")
        stopage_place_ids = [stopage_place_ids_dict[key] for key in sorted(stopage_place_ids_dict.keys(), key=lambda x: int(x))]
        all_place_ids = [pickup_place_id] + stopage_place_ids + [dropoff_place_id]
        all_locations = [fetch_location_information_from_place_id(place_id) for place_id in all_place_ids]
        segmented_trip_minutes = defaultdict(float)
        segmented_trip_distance = defaultdict(float)
        for i in range(len(all_locations) - 1):
            start = all_locations[i]
            end = all_locations[i + 1]
            route_result = calculate_route_segments(start["lat"], start["lon"], end["lat"], end["lon"])
            for seg in route_result["segments"]:
                segmented_trip_minutes[seg["zone"]] += seg["time_minutes"]
                segmented_trip_distance[seg["zone"]] += seg["distance_miles"]
        minute_fares, milage_fares = calculate_minute_and_mileage_based_fare(segmented_trip_minutes, segmented_trip_distance)
        all_charges = [calculate_congestion_charge(location) for location in all_locations]
        combined_congestion_charges = {}
        for service_type in set(minute_fares.keys()).union(milage_fares.keys()):
            service_key = service_type.upper()
            combined_congestion_charges[service_key] = max(charges.get(service_key, 0.0) for charges in all_charges)
        fare_details = {}
        for service_type in minute_fares:
            service_key = service_type.upper()
            service = ServiceType.objects.get(service_type=service_type)
            minute_fare = Decimal(str(round(minute_fares[service_type], 2)))
            milage_fare = Decimal(str(round(milage_fares.get(service_type, 0.0), 2)))
            booking_fee = Decimal(str(service.booking_fee))
            booking_fee += Decimal("5.00") * len(stopage_place_ids)
            congestion_charge = Decimal(str(round(combined_congestion_charges.get(service_key, 0.0), 2)))
            fare_details[service_type] = calculate_fare_details(service_type, minute_fare, milage_fare, booking_fee, congestion_charge)
        final_fares = add_vat_and_service_charge(fare_details)
        final_fares = add_concierge_service_charge(request, final_fares)
        result = {
            "pickup_place_id": pickup_place_id,
            "stopage_place_ids": stopage_place_ids_dict,
            "dropoff_place_id": dropoff_place_id,
            "fare_details": final_fares,
            "total_minutes": round(sum(segmented_trip_minutes.values()), 2),
            "total_distance": round(sum(segmented_trip_distance.values()), 2),
        }
        return Response(result, status=status.HTTP_200_OK)







class OneWayTripRequest(APIView):
    def post(self, request):
        data = request.data
        user = request.user

        is_instant_trip = data.get("is_instant_trip", True)

        if is_instant_trip:
            pickup_time = timezone.now() + timezone.timedelta(minutes=10)
        elif not data.get("pickup_time"):
            return Response(
                {"error": "The 'pickup_time' field is required for non-instant trips."},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            pickup_time = data.get("pickup_time")

        # Ensure user is authenticated and org exists
        org_commission_rate = Decimal(str(getattr(user.organization, "org_commission", 0.0)))

        services = data.get("services")
        pickup_place_id = data.get("pickup_place_id")
        stopage_place_ids = data.get("stopage_place_ids", {})
        dropoff_place_id = data.get("dropoff_place_id")
        fare_details = data.get("fare_details")
        total_minutes = data.get("total_minutes")
        total_distance = data.get("total_distance")

        if not all([pickup_place_id, dropoff_place_id, fare_details]):
            return Response({"detail": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

        # Parse service type from fare_details
        service_type = next(iter(fare_details), None)
        if not service_type:
            return Response({"error": "Invalid fare_details format."}, status=status.HTTP_400_BAD_REQUEST)

        selected_fare = fare_details[service_type]

        try:
            trip = Trip.objects.create(
                user=user,
                services=services,
                pickup_place_id=pickup_place_id,
                stopage_place_ids=stopage_place_ids,
                dropoff_place_id=dropoff_place_id,
                booking_time=timezone.now(),
                pickup_time=pickup_time,
                trip_method="ONE_WAY",
                total_minutes=Decimal(str(total_minutes)),
                total_distance=Decimal(str(total_distance)),
                dropoff_time = pickup_time + timezone.timedelta(minutes=total_minutes),
                service_type=service_type,
                minute_fare=Decimal(str(selected_fare["minute_fare"])),
                milage_fare=Decimal(str(selected_fare["milage_fare"])),
                booking_fee=Decimal(str(selected_fare["booking_fee"])),
                fare=Decimal(str(selected_fare["total_fare"])),
                congestion_charge_amount=Decimal(str(selected_fare["congestion_charge"])),
                total_with_congestion_charge=Decimal(str(selected_fare["total_with_congestion_charge"])),
                service_charge_amount=Decimal(str(selected_fare["service_charge"])),
                total_with_service_charge=Decimal(str(selected_fare["fare_with_service_charge_subtotal"])),
                vat_amount=Decimal(str(selected_fare["vat"])),
                total_fare_with_vat=Decimal(str(selected_fare["total_fare_with_vat"])),
                org_commission_rate=org_commission_rate,
                org_commission_amount=Decimal(str(selected_fare["concierge_service_charge"])),
                total_with_org_commission=Decimal(str(selected_fare["totatotal_fare_with_concierge_service_chargel_fare_with_org_commission"])),
                final_fare=Decimal(str(selected_fare["total_fare_with_concierge_service_charge"])),
                trip_status="REQUESTED"
            )
        except KeyError as e:
            return Response({"error": f"Missing fare detail field: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "detail": "Trip requested successfully.",
            "trip_id": trip.id,
        }, status=status.HTTP_201_CREATED)