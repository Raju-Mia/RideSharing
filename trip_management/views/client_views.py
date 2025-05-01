from django.shortcuts import render
from trip_management.serializers.client_serializers import (
    TripListForClientSerializar,
    TripDetailForClientSerializer,
)
from trip_management.serializers.driver_serializers import TripSerializer
from trip_management.models import BookingFeeSchedule

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from datetime import timedelta
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404
from trip_management.models import (
    PaymentMethods,
    Trip,
    TripStatus,
    TripBreak,
    ExtraCharge,
    DistanceTypes,
    TripMethod,
)

# from accounts.models import VehicleTypes, VehicleModel

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

from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from trip_management.api_helpers import (
    validate_trip_method,
    validate_required_fields,
    get_estimated_fares,
    get_distance_type_from_location,
    calculate_distance_and_time,
)
from utils.pagination import CustomPageNumberPagination
from django.db.models import Q, F, Case, When, DecimalField
from rest_framework.parsers import JSONParser
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import TokenError

# Create your views here.


class TripRequest(APIView):
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

        # Validate required fields for GET request
        validation_error = validate_required_fields(
            data, trip_method, is_get_request=True
        )
        if validation_error:
            return Response(*validation_error)

        # Extract pickup and dropoff coordinates
        pickup_lat = data.get("pickup_location_lat")
        pickup_lng = data.get("pickup_location_lng")
        dropoff_lat = data.get("initial_dropoff_location_lat")
        dropoff_lng = data.get("initial_dropoff_location_lng")

        # Calculate approximate distance and duration
        try:
            approximate_distance_covered, approximate_duration = (
                calculate_distance_and_time(
                    pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
                )
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # Determine the distance_type based on pickup location
        distance_type = get_distance_type_from_location(pickup_lat, pickup_lng)
        if distance_type not in [choice[0] for choice in DistanceTypes.choices]:
            return Response(
                {"error": "Invalid distance_type"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Calculate fares
        # booking_fee = BookingFeeSchedule.get_current_booking_fee(trip_method)

        vehicle_fares, error_response = get_estimated_fares(data, trip_method)
        if error_response:
            return Response(error_response, status=status.HTTP_400_BAD_REQUEST)

        # Prepare the response data
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

        data["payment_method"] = data.get("payment_method", PaymentMethods.CARD)

        if data.get("is_instant_trip", True):
            data["pickup_time"] = timezone.now() + timezone.timedelta(minutes=10)
        elif not data.get("pickup_time"):
            return Response(
                {
                    "error": "This (pickup_time) field is required for non-instant trips."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        pickup_time = data["pickup_time"]
        if isinstance(pickup_time, str):
            pickup_time = timezone.datetime.fromisoformat(pickup_time)

        approximate_duration = data.get("approximate_duration", 0)
        try:
            approximate_duration = int(approximate_duration)
        except ValueError:
            return Response(
                {"error": "Invalid approximate_duration format."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data["initial_dropoff_time"] = pickup_time + timedelta(
            minutes=approximate_duration
        )

        if data["payment_method"] == PaymentMethods.CARD:
            payment_card_id = data.get("payment_card_id")
            if not payment_card_id:
                return Response(
                    {"error": "Payment card must be provided for card payments."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

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

        serializer = TripSerializer(data=data)
        if serializer.is_valid():
            trip = serializer.save(user=request.user)
            return Response(
                {"message": "Trip created successfully"}, status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TripListForClient(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trip_status = request.query_params.get("trip_status")
        try:
            user = request.user
            trips = Trip.objects.filter(user=user).order_by("-booking_time")
            if trip_status and trip_status.lower() == "upcoming":
                trips = trips.filter(
                    trip_status__in=[
                        TripStatus.OFF_TO_PICKUP,
                        TripStatus.REQUESTED,
                        TripStatus.APPROVED_BY_DRIVER,
                    ]
                )
            if trip_status and trip_status.lower() == "cancelled":
                trips = trips.filter(
                    trip_status__in=[
                        TripStatus.CANCELLED_BY_DRIVER,
                        TripStatus.CANCELLED,
                    ]
                )
            if trip_status and trip_status.lower() == "completed":
                trips = trips.filter(trip_status=TripStatus.COMPLETED)

            paginator = CustomPageNumberPagination()
            paginated_trips = paginator.paginate_queryset(trips, request)
            serializer = TripListForClientSerializar(paginated_trips, many=True)
            return paginator.get_paginated_response(serializer.data)
        except Exception as e:
            return Response(
                {"error": f"Something went wrong: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TripDetailForClient(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TripDetailForClientSerializer

    def get(self, request, *args, **kwargs):
        trip_id = self.kwargs.get("trip_id")
        try:
            trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND
            )
        serializer = TripDetailForClientSerializer(trip)
        return Response(serializer.data)
