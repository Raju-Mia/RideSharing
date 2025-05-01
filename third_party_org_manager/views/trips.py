from organization_manager.models import Organization
from trip_management.models import Trip
from rest_framework.views import APIView
from django.db.models import Q

# from accounts.models import VehicleModel
from datetime import timedelta
from driver_app.models import (
    Driver,
    DriverStatus,
    # DriverAttachmentStatus,
    # Manufacturer,
    Vehicle,
    VehicleModel,
    VehicleStatus,
    # VehicleTypesInfo,
    AttachmentStatus,
)
from django.utils import timezone
from third_party_org_manager.models import OrganizationCustomer

from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal
from accounts.models import Services
from trip_management.models import Trip, TripStatus, DistanceTypes, TripMethod
from third_party_org_manager.serializers.trip_serializers import (
    TripListSerializer,
    TripRequestSerializer,
    TripDetailSerializer,
)

from utils.pagination import CustomPageNumberPagination

# from trip_management.views.client_views import BOOKING_FEE
from trip_management.api_helpers import (
    calculate_distance_and_time,
    get_distance_type_from_location,
    validate_trip_method,
    get_estimated_fares,
    validate_required_fields,
)
from rest_framework.parsers import JSONParser


class OrganizationTripRequestView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser]

    def get(self, request):
        data = request.query_params
        user = request.user
        print(user.username)
        trip_method = data.get("trip_method")

        # Validate trip_method
        validation_error = validate_trip_method(trip_method)
        if validation_error:
            return Response(*validation_error)

        validation_error = validate_required_fields(
            data, trip_method, is_get_request=True
        )
        if validation_error:
            return Response(*validation_error)

        pickup_lat = data.get("pickup_location_lat")
        pickup_lng = data.get("pickup_location_lng")
        dropoff_lat = data.get("initial_dropoff_location_lat")
        dropoff_lng = data.get("initial_dropoff_location_lng")

        try:
            approximate_distance_covered, approximate_duration = (
                calculate_distance_and_time(
                    pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
                )
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        distance_type = get_distance_type_from_location(pickup_lat, pickup_lng)
        if distance_type not in [choice[0] for choice in DistanceTypes.choices]:
            return Response(
                {"error": "Invalid distance_type"}, status=status.HTTP_400_BAD_REQUEST
            )

        # booking_fee = BookingFeeSchedule.get_current_booking_fee(trip_method)

        vehicle_fares, error_response = get_estimated_fares(data, trip_method)
        if error_response:
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        response_data = {
            "trip_info": {
                "distance_type": distance_type,
                "pickup_location_name": data.get("pickup_location_name"),
                "pickup_location_lat": pickup_lat,
                "pickup_location_lng": pickup_lng,
                "initial_dropoff_location_name": data.get(
                    "initial_dropoff_location_name"
                ),
                "initial_dropoff_location_lat": dropoff_lat,
                "initial_dropoff_location_lng": dropoff_lng,
                "approximate_distance_covered": approximate_distance_covered,
                "approximate_duration": approximate_duration,
                "trip_method": trip_method,
            },
            "vehicle_fares": vehicle_fares,
            "status": status.HTTP_200_OK,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request):
        user = request.user
        org_commission = user.organization.org_commission
        data = request.data.copy()
        trip_method = data.get("trip_method")
        services = data.get("services")
        if not services:
            return Response(
                {"error": "Services list must be provided."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            data["services"] = services

        validation_error = validate_trip_method(trip_method)
        if validation_error:
            return Response(*validation_error)

        validation_error = validate_required_fields(data, trip_method)
        if validation_error:
            return Response(*validation_error)

        # Set pickup time
        if data.get("is_instant_trip", True):
            pickup_time = timezone.now() + timedelta(minutes=10)
        elif not data.get("pickup_time"):
            return Response(
                {
                    "error": "This (pickup_time) field is required for non-instant trips."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            pickup_time = (
                timezone.datetime.fromisoformat(data["pickup_time"])
                if isinstance(data["pickup_time"], str)
                else data["pickup_time"]
            )

        # Ensure `approximate_duration` is an integer
        approximate_duration = data.get("approximate_duration", 0)
        try:
            approximate_duration = int(approximate_duration)
        except ValueError:
            return Response(
                {"error": "Invalid approximate_duration format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Calculate `initial_dropoff_time`
        initial_dropoff_time = pickup_time + timedelta(minutes=approximate_duration)
        data["initial_dropoff_time"] = initial_dropoff_time

        # Update other required fields
        data.update(
            {
                "service_type": data.get("service_type"),
                "distance_type": data.get("distance_type"),
                "estimated_fare": data.get("estimated_fare"),
                "approximate_distance_covered": data.get(
                    "approximate_distance_covered"
                ),
                "approximate_duration": data.get("approximate_duration"),
                "per_mile_cost": data.get("per_mile_cost"),
                "per_hour_cost": data.get("per_hour_cost"),
                "booking_fee": data.get("booking_fee"),
                "congestion_charge": data.get("congestion_charge"),
            }
        )

        passenger_phone_number = data.get("passenger_phone_number")
        passenger_email = data.get("passenger_email")
        passenger_name = data.get("passenger_name")
        passenger_address = data.get("passenger_address")
        print(
            passenger_phone_number, passenger_email, passenger_name, passenger_address
        )

        # Create OrganizationCustomer if passenger_name does not exist
        if (
            passenger_name
            and not OrganizationCustomer.objects.filter(
                organization=user.organization, name=passenger_name
            ).exists()
        ):
            OrganizationCustomer.objects.create(
                organization=user.organization,
                name=passenger_name,
                address=passenger_address or None,
                phone_number=passenger_phone_number or None,
                email=passenger_email or None,
                company_name=passenger_name,
            )

        serializer = TripRequestSerializer(data=data)
        if serializer.is_valid():
            passenger_data = {
                "passenger_phone_number": passenger_phone_number,
                "passenger_email": passenger_email,
                "passenger_name": passenger_name,
                "passenger_address": passenger_address,
            }

            trip = serializer.save(
                user=user, org_commission_rate=org_commission, **passenger_data
            )

            message = f"Trip created successfully {trip.id}"
            return Response(message, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # permission_classes = [IsAuthenticated]

    # def post(self, request, *args, **kwargs):
    #     data = request.data
    #     user = request.user

    #     org_commission  = user.organization.org_commission

    #     trip_method_validation = validate_trip_method(data.get('trip_method'))
    #     if trip_method_validation:
    #         return Response(trip_method_validation, status=status.HTTP_400_BAD_REQUEST)

    #     trip_method = data.get('trip_method')

    #     required_fields_validation = validate_required_fields(
    #         data, trip_method)
    #     if required_fields_validation:
    #         return Response(required_fields_validation, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         pickup_lat = float(data.get('pickup_location_lat'))
    #         pickup_lng = float(data.get('pickup_location_lng'))
    #         dropoff_lat = float(data.get('initial_dropoff_location_lat'))
    #         dropoff_lng = float(data.get('initial_dropoff_location_lng'))
    #     except (TypeError, ValueError):
    #         return Response({"error": "Invalid latitude or longitude values."}, status=status.HTTP_400_BAD_REQUEST)

    #     try:
    #         distance_miles, time_minutes = calculate_distance_and_time(
    #             pickup_lat, pickup_lng, dropoff_lat, dropoff_lng)
    #     except ValueError as ve:
    #         return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
    #     except Exception as e:
    #         return Response({"error": "Failed to calculate distance and time."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    #     distance_type = get_distance_type_from_location(pickup_lat, pickup_lng)
    #     if distance_type not in [choice[0] for choice in DistanceTypes.choices]:
    #         return Response({"error": "Invalid distance_type determined."}, status=status.HTTP_400_BAD_REQUEST)

    #     serializer = TripRequestSerializer(data={**data, "services": Services.concierge_service},context={'request': request})

    #     if serializer.is_valid():
    #         with transaction.atomic():
    #             trip = serializer.save()

    #             service_type = serializer.validated_data.get('service_type')
    #             vehicle = VehicleModel.objects.filter(
    #                 service_type=service_type).first()
    #             if not vehicle:
    #                 return Response({"error": "Selected service type not found."}, status=status.HTTP_400_BAD_REQUEST)

    #             CONGESTION_CHARGE = Decimal('15.00')
    #             SERVICE_PERCENTAGE = Decimal('5.00')
    #             VAT_PERCENTAGE = Decimal('20.00')

    #             fares = {
    #                 DistanceTypes.INNER_LONDON: vehicle.inner_london_fare,
    #                 DistanceTypes.CENTRAL_LONDON: vehicle.central_london_fare,
    #                 DistanceTypes.ORBITAL_LONDON: vehicle.orbital_london_fare,
    #                 DistanceTypes.GREATER_LONDON: vehicle.greater_london_fare,
    #                 DistanceTypes.OUTER_LONDON: vehicle.outer_london_fare,
    #                 DistanceTypes.OUTER_LONDON_CIRCLE_ONE: vehicle.outer_london_circle_one_fare,
    #                 DistanceTypes.OUTER_LONDON_CIRCLE_TWO: vehicle.outer_london_circle_two_fare,
    #             }

    #             fare_info = fares.get(distance_type, {})
    #             if not fare_info:
    #                 return Response({"error": f"No fare information for distance type '{distance_type}' and service type '{service_type}'."}, status=status.HTTP_400_BAD_REQUEST)

    #             per_mile = Decimal(fare_info.get("per_mile", "0"))
    #             per_hour = Decimal(fare_info.get("per_hour", "0"))

    #             fare_for_distance = per_mile * Decimal(distance_miles)
    #             fare_for_time = (per_hour / Decimal('60')) * \
    #                 Decimal(time_minutes)
    #             booking_fee = BookingFeeSchedule.get_current_booking_fee(trip_method)
    #             base_fare = fare_for_distance + fare_for_time + booking_fee

    #             total_fare = base_fare + CONGESTION_CHARGE
    #             service_charge = (SERVICE_PERCENTAGE /
    #                               Decimal('100')) * total_fare
    #             total_fare += service_charge
    #             vat = (VAT_PERCENTAGE / Decimal('100')) * total_fare
    #             total_fare += vat

    #             estimated_fare = total_fare.quantize(Decimal('0.01'))

    #             trip.approximate_distance_covered = Decimal(distance_miles)
    #             trip.approximate_duration = Decimal(time_minutes)
    #             trip.distance_type = distance_type
    #             trip.estimated_fare = estimated_fare
    #             trip.per_mile_cost = per_mile
    #             trip.per_hour_cost = per_hour
    #             trip.org_commission_rate = org_commission
    #             trip.booking_fee = booking_fee
    #             trip.trip_for_others = True

    #             trip.save()

    #             message = "Trip requested by organization successfully"
    #             return Response({
    #                 "message": message,
    #                 "trip_id": trip.unique_id,
    #                 "estimated_fare": str(trip.estimated_fare),
    #                 "trip_per_mile_cost": trip.per_mile_cost,
    #                 "trip_per_hour_cost": trip.per_hour_cost,
    #                 "trip.org_commission_rate": trip.org_commission_rate,
    #             }, status=status.HTTP_201_CREATED)

    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OrganizationTripListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        user = request.user
        organization_id = user.organization.id

        trip_status = request.query_params.get("trip_status", None)
        trip_method = request.query_params.get("trip_method", None)
        search_query = request.query_params.get("search", None)

        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return Response(
                {"error": "Organization not found."}, status=status.HTTP_404_NOT_FOUND
            )

        queryset = Trip.objects.filter(user__organization_id=organization_id).order_by(
            "-booking_time"
        )

        if trip_status == "Upcoming":
            queryset = queryset.exclude(
                trip_status__in=[
                    TripStatus.CANCELLED,
                    TripStatus.CANCELLED_BY_DRIVER,
                    TripStatus.COMPLETED,
                ]
            )
        elif trip_status == "Cancelled":
            queryset = queryset.filter(
                trip_status__in=[TripStatus.CANCELLED, TripStatus.CANCELLED_BY_DRIVER]
            )
        elif trip_status == "Completed":
            queryset = queryset.filter(trip_status=TripStatus.COMPLETED)

        if trip_method:
            queryset = queryset.filter(trip_method=trip_method)

        if search_query:
            queryset = queryset.filter(
                Q(passenger_name__icontains=search_query)
                | Q(pickup_location_name__icontains=search_query)
                | Q(final_dropoff_location_name__icontains=search_query)
            )

        paginator = self.pagination_class()
        paginated_trips = paginator.paginate_queryset(queryset, request)

        serializer = TripListSerializer(paginated_trips, many=True)
        return paginator.get_paginated_response(serializer.data)


class OrganizationTripdetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TripDetailSerializer

    def get(self, request, *args, **kwargs):
        trip_id = self.kwargs.get("id")
        try:
            trip = Trip.objects.get(pk=trip_id)
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = TripDetailSerializer(trip)
        return Response(serializer.data)
