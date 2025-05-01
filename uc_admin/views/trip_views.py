import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch, Q
from django.core.cache import cache
from utils.pagination import CustomPageNumberPagination
from trip_management.models import Trip, TripBreak, ExtraCharge, TripStatus, TripMethod
from uc_admin.serializers.trip_serializers import (TripListSerializer, TripDetailEditSerializer,
                                                   ExtraChargeSerializer, AssignDriverSerializer,
                                                   TripListForOrgSerializer)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from twilio_ac.rest import Client
from django.conf import settings
from threading import Thread
from django.shortcuts import get_object_or_404
from trip_management.async_helpers import run_schedule_deletion
# from accounts.models import Driver
from django.contrib.postgres.search import SearchVector, SearchQuery
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

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db import transaction
from trip_management.helpers import calculate_distance_and_time
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from notification_manager.models import FCMToken, NotifyMessage
from notification_manager.utils_helper import send_push_notification
from trip_management.models import TripStatus

import json
from decimal import Decimal
from uuid import UUID
from django.core.serializers.json import DjangoJSONEncoder


User = get_user_model()


class CustomJSONEncoder(DjangoJSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class TripList(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        trips = Trip.objects.all().order_by('-pickup_time')

        search_query = request.query_params.get('search')
        if search_query:
            trips = Trip.objects.annotate(
                search=SearchVector(
                    'passenger_name',
                    'flight_number',
                    'pickup_location_name',
                    'dropoff_location_name',
                    'unique_id',
                    'user__full_name',
                    'driver__user__full_name',
                    'user__organization__name'
                )
            ).filter(search=SearchQuery(search_query))

        filter_conditions = Q()

        trip_status = request.query_params.get('trip_status')
        if trip_status:
            filter_conditions &= Q(trip_status=trip_status)

        trip_method = request.query_params.get('trip_method')
        if trip_method:
            filter_conditions &= Q(trip_method=trip_method)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            filter_conditions &= Q(pickup_time__gte=start_date)
        if end_date:
            filter_conditions &= Q(pickup_time__lte=end_date)
        org_id = request.query_params.get('org_id')
        if org_id:
            filter_conditions &= Q(user__organization__id=org_id)
        trips = trips.filter(filter_conditions).order_by('-pickup_time')

        paginator = self.pagination_class()
        paginated_trips = paginator.paginate_queryset(trips, request)
        serializer = TripListSerializer(paginated_trips, many=True)
        return paginator.get_paginated_response(serializer.data)


class TripDetailEdit(APIView):
    permission_classes = [IsAuthenticated]

    """
    Retrieve or update a trip instance.
    """

    def get(self, request, trip_id, format=None):
        trip = get_object_or_404(Trip, id=trip_id)
        serializer = TripDetailEditSerializer(trip)
        return Response(serializer.data)

    def patch(self, request, trip_id, format=None):
        trip = get_object_or_404(Trip, id=trip_id)
        serializer = TripDetailEditSerializer(
            trip, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        validated_data = serializer.validated_data

        if self._update_final_fare(trip, validated_data):
            pass

        if self._handle_pickup_updates(trip, validated_data):
            pass

        if self._handle_dropoff_updates(trip, validated_data):
            pass

        trip = serializer.save()
        trip.refresh_from_db()

        if self._should_recalculate(validated_data):
            recalculation_result = self._recalculate_fare(trip, validated_data)
            if isinstance(recalculation_result, Response):
                return recalculation_result  # Return error response if recalculation failed

        return Response(
            {"detail": f"Trip updated successfully. Final fare is: {trip.final_fare}"},
            status=status.HTTP_200_OK
        )

    def _update_final_fare(self, trip, data):
        if 'final_fare' in data:
            trip.final_fare = data['final_fare']
            trip.congestion_charge_amount = Decimal('0')
            trip.service_charge_amount = Decimal('0')
            trip.vat_amount = Decimal('0')
            trip.save()
            return True
        return False

    def _handle_pickup_updates(self, trip, data):
        pickup_fields = ['pickup_location_name',
                         'pickup_location_lat', 'pickup_location_lng']
        if any(field in data for field in pickup_fields):
            if 'pickup_location_name' in data:
                if not all(field in data for field in ['pickup_location_lat', 'pickup_location_lng']):
                    raise ValidationError({
                        "detail": "When changing pickup_location_name, both pickup_location_lat and pickup_location_lng must be provided."
                    })
            elif any(field in data for field in ['pickup_location_lat', 'pickup_location_lng']):
                if not all(field in data for field in ['pickup_location_lat', 'pickup_location_lng']):
                    raise ValidationError({
                        "detail": "Both pickup_location_lat and pickup_location_lng must be provided when updating pickup location coordinates."
                    })
            return True
        return False

    def _handle_dropoff_updates(self, trip, data):
        dropoff_fields = ['final_dropoff_location_name',
                          'final_dropoff_location_lat', 'final_dropoff_location_lng']
        if any(field in data for field in dropoff_fields):
            if 'final_dropoff_location_name' in data:
                if not all(field in data for field in ['final_dropoff_location_lat', 'final_dropoff_location_lng']):
                    data['final_dropoff_location_lat'] = trip.initial_dropoff_location_lat
                    data['final_dropoff_location_lng'] = trip.initial_dropoff_location_lng
            elif any(field in data for field in ['final_dropoff_location_lat', 'final_dropoff_location_lng']):
                if not all(field in data for field in ['final_dropoff_location_lat', 'final_dropoff_location_lng']):
                    data['final_dropoff_location_lat'] = trip.initial_dropoff_location_lat
                    data['final_dropoff_location_lng'] = trip.initial_dropoff_location_lng
            return True
        return False

    def _should_recalculate(self, data):
        recalculation_fields = [
            'per_mile_cost', 'per_hour_cost',
            'congestion_charge', 'service_charge', 'vat'
        ]
        pickup_fields = ['pickup_location_name',
                         'pickup_location_lat', 'pickup_location_lng']
        dropoff_fields = ['final_dropoff_location_name',
                          'final_dropoff_location_lat', 'final_dropoff_location_lng']
        return (
            any(field in data for field in pickup_fields) or
            any(field in data for field in dropoff_fields) or
            any(field in data for field in recalculation_fields)
        )

    def _recalculate_fare(self, trip, data):
        try:
            pickup_lat = trip.pickup_location_lat
            pickup_lng = trip.pickup_location_lng
            final_dropoff_lat = trip.final_dropoff_location_lat or trip.initial_dropoff_location_lat
            final_dropoff_lng = trip.final_dropoff_location_lng or trip.initial_dropoff_location_lng

            distance, duration = calculate_distance_and_time(
                pickup_lat, pickup_lng, final_dropoff_lat, final_dropoff_lng
            )

            if distance is None or duration is None:
                return Response(
                    {"detail": "Unable to calculate distance and duration with the provided locations."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            distance_decimal = Decimal(str(distance))
            duration_decimal = Decimal(str(duration))

            trip.final_distance_covered = distance_decimal
            trip.final_duration = duration_decimal

            per_mile_cost = data.get('per_mile_cost', trip.per_mile_cost)
            per_hour_cost = data.get('per_hour_cost', trip.per_hour_cost)

            trip.fare = (per_mile_cost * distance_decimal) + \
                (per_hour_cost * (duration_decimal / Decimal('60')))
            print("fare :", trip.fare)
            client_tip = trip.client_tip or Decimal('0')
            print('client_tip', client_tip)
            total_extra_charge = trip.total_extra_charge or Decimal(
                '0')  # Read-only property
            print("total_extra_charge", total_extra_charge)
            congestion_charge = data.get(
                'congestion_charge', trip.congestion_charge)
            service_charge = data.get('service_charge', trip.service_charge)
            vat = data.get('vat', trip.vat)

            total = trip.fare + client_tip + total_extra_charge + congestion_charge
            print('Total', total)
            sub_total = (service_charge / Decimal('100')) * total + total
            print('sub_total', sub_total)
            trip.final_fare = (vat / Decimal('100')) * sub_total + sub_total
            print('final_fare1', trip.final_fare)
            trip.save()
            print('final_fare2', trip.final_fare)

            return None  # Indicate success

        except (InvalidOperation, ValueError) as e:
            return Response(
                {"detail": f"Error in calculations: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"Error calculating distance and time: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

#     def handle_exception(self, exc):
#         if isinstance(exc, ValidationError):
#             return Response(exc.detail, status=status.HTTP_400_BAD_REQUEST)
#         return super().handle_exception(exc)
# class ValidationError(Exception):
#     def __init__(self, detail):
#         self.detail = detail


class AddExtraChargeFromAdministration(APIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticated]

    """
    List all extra charges for a trip or create a new extra charge.
    """

    def post(self, request, trip_id, format=None):
        trip = get_object_or_404(Trip, id=trip_id)
        data = request.data.copy()
        data['trip'] = trip.id
        serializer = ExtraChargeSerializer(data=data)
        if serializer.is_valid():
            serializer.save(trip=trip)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ExtraChargeEditDeleteFromAdministration(APIView):
    permission_classes = [IsAuthenticated]

    """
    Retrieve, update, or delete an extra charge instance.
    """

    def get_object(self, trip_id, id):
        return get_object_or_404(ExtraCharge, trip__id=trip_id, id=id)

    # def get(self, request, trip_id, id, format=None):
    #     extra_charge = self.get_object(trip_id, id)
    #     serializer = ExtraChargeSerializer(extra_charge)
    #     return Response(serializer.data)

    def patch(self, request, trip_id, id, format=None):
        extra_charge = self.get_object(trip_id, id)
        serializer = ExtraChargeSerializer(
            extra_charge, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, trip_id, id, format=None):
        extra_charge = self.get_object(trip_id, id)
        extra_charge.delete()
        message = "Deleted "
        return Response(message, status=status.HTTP_204_NO_CONTENT)


class AssignDriver(APIView):
    def post(self, request):
        serializer = AssignDriverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        trip_id = serializer.validated_data['trip_id']
        driver_id = serializer.validated_data['driver_id']

        try:
            with transaction.atomic():
                trip = get_object_or_404(Trip, id=trip_id)
                driver = get_object_or_404(Driver, id=driver_id)
                trip.driver = driver

                trip.trip_status = TripStatus.PENDING
                trip.save()


                user = driver.user
                user_id = user.id

                title = f"Hey {user.full_name}, you have been assigned a new trip!"
                content = "You are assign for driving the trip!"

                json_content = {
                'type': 'trip',
                'trip_id': str(trip.id),
                'pickup_location_name': trip.pickup_location_name,
                'pickup_time': trip.pickup_time.isoformat() if trip.pickup_time else None,
                'estimated_fare': trip.estimated_fare,
                     }

                NotifyMessage.objects.create(
                    user=user,
                    title=title,
                    content=content,
                    json_content=json.loads(json.dumps(json_content, cls=CustomJSONEncoder))
                )


                message = {
                    'trip_id': str(trip_id),
                    'trip_status': str(trip.trip_status),
                    'client_name': str(trip.user.full_name),
                    'client_picture': trip.user.picture.url if trip.user.picture else None,
                    'ratings': f"{5.00:.2f}",
                    'rated_by': str(13),
                    'pickup_location_name': trip.pickup_location_name,
                    'pickup_location_lat': f"{float(trip.pickup_location_lat or 0)}",
                    'pickup_location_lng': f"{float(trip.pickup_location_lng or 0)}",
                    'dropoff_location_name': trip.initial_dropoff_location_name,
                    'dropoff_location_lat': f"{float(trip.initial_dropoff_location_lat or 0)}",
                    'dropoff_location_lng': f"{float(trip.initial_dropoff_location_lng or 0)}",
                    'pickup_time': trip.pickup_time.isoformat() if trip.pickup_time else None,
                    'distance': f"{float(trip.approximate_distance_covered or 0):.2f}",
                    'duration': f"{float(trip.approximate_duration or 0):.2f}",  
                    'estimated_fare': f"{float(trip.estimated_fare or 0):.2f}" if trip.estimated_fare else None,  
                }
                print(message)

                channel_layer = get_channel_layer()
                room_group_name = f'driver_trip_{user_id}'
                async_to_sync(channel_layer.group_send)(
                    room_group_name,
                    {'type': 'trip_update', 'content': message},
                )
                Thread(
                    target=run_schedule_deletion,
                    args=(user_id, trip_id)
                ).start()
                return Response(
                    {"message": "Driver assigned successfully."},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            # Debugging: print the error for more detailsssss
            print(f"Error: {str(e)}")
            return Response(
                {"message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TripListForOrganization(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get(self, request, org_id):
        trips = Trip.objects.filter(
            user__organization_id=org_id).order_by('-booking_time')

        search_query = request.query_params.get('search')
        if search_query:
            trips = trips.annotate(
                search=SearchVector(
                    'passenger_name',
                    'flight_number',
                    'pickup_location_name',
                    'final_dropoff_location_name',
                    'unique_id',
                    'user__full_name',
                    'driver__user__full_name',
                    'user__organization__name'
                )
            ).filter(search=SearchQuery(search_query))

        filter_conditions = Q()

        trip_status = request.query_params.get('trip_status')
        if trip_status:
            filter_conditions &= Q(trip_status=trip_status)

        trip_method = request.query_params.get('trip_method')
        if trip_method:
            filter_conditions &= Q(trip_method=trip_method)

        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            filter_conditions &= Q(booking_time__gte=start_date)
        if end_date:
            filter_conditions &= Q(booking_time__lte=end_date)

        trips = trips.filter(filter_conditions).order_by('-booking_time')

        paginator = self.pagination_class()
        paginated_trips = paginator.paginate_queryset(trips, request)
        serializer = TripListForOrgSerializer(paginated_trips, many=True)
        return paginator.get_paginated_response(serializer.data)
