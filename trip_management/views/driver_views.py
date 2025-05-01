from location.models import LocationInfo
from trip_management.serializers.driver_serializers import (TripSerializer,DeclineTripSerializer, TripListForDriverSerializer, 
                                                            TripDetailForDriverSerializer,CancelTripListSerializer,
                                                            TripBreakSerializer,ExtraChargeSerializer,TripSummarySerializer,
                                                            CompletedTripDetailForDriverSerializer, CancellationReasonSerializer)

from utils.constants import DRIVER_CANCELLATION_REASONS
import traceback
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from datetime import timedelta
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.shortcuts import get_object_or_404
import asyncio
from trip_management.models import (Trip,DeclineTrip, DeclinedByStatus, TripStatus, TripBreak,CanceledByStatus, 
                                    TripMethod, CancelTrip,ExtraChargePicture)
from threading import Thread

from trip_management.async_helpers import run_immediate_deletion

from django.db import transaction
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from trip_management.helpers import calculate_distance_and_time
from utils.pagination import CustomPageNumberPagination
from django.db.models import Q, F, Case, When, DecimalField, Value
from django.db.models.functions import Coalesce

from decimal import Decimal
import logging
logger = logging.getLogger(__name__)
# Create your views here.
from django.contrib.auth import get_user_model
User = get_user_model()

class TripDelete(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, trip_id):
        try:
            trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        if trip.user != request.user:
            return Response({"error": "You are not authorized to delete this trip."}, status=status.HTTP_403_FORBIDDEN)
        trip.delete()
        return Response({"message": "Trip deleted successfully."}, status=status.HTTP_200_OK)


class DriverTripAccept(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        try:
            user = request.user
            driver = user.driver
            user_id = user.id
            print(user_id)
        except AttributeError:
            return Response({"error": "User is not a driver."}, status=status.HTTP_403_FORBIDDEN)

        try:
            trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        if trip.driver != driver:
            return Response({"error": "This job has already been taken."}, status=status.HTTP_400_BAD_REQUEST)
        if trip.trip_status not in [TripStatus.PENDING]:
            return Response({"error": "This trip is not available for acceptance."}, status=status.HTTP_400_BAD_REQUEST)


        try:
            with transaction.atomic():
                trip.trip_status = TripStatus.APPROVED_BY_DRIVER
                trip.save()

                Thread(
                    target=run_immediate_deletion,
                    args=(user_id, trip_id)
                ).start()

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        serializer = TripSerializer(trip)
        return Response(
            {"message": "Trip approved by driver.", "trip": serializer.data},
            status=status.HTTP_200_OK
        )


class DriverDeclineTrip(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, trip_id):
        try:
            user = request.user
            driver = user.driver
            user_id = user.id
        except AttributeError:
            return Response({"error": "User is not a driver."}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        
        if trip.driver != driver:
            return Response({"error": "This trip is not assigned to you."}, status=status.HTTP_400_BAD_REQUEST)
        
        if trip.trip_status not in [TripStatus.PENDING, TripStatus.REQUESTED]:
            return Response({"error": "This trip is not available for decline."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                DeclineTrip.objects.create(
                    trip=trip,
                    user=user,
                    decline_reason="No interest in this trip.",
                    declined_by=DeclinedByStatus.Driver,
                )
                
                trip.driver = None
                trip.trip_status = TripStatus.REQUESTED
                trip.save()
                
                Thread(
                    target=run_immediate_deletion,
                    args=(user_id, trip_id)
                ).start()
            
            return Response({"message": "Trip declined."}, status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response({"error": f"Something went wrong: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class DeclineTripListByDriverAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        declined_trips = DeclineTrip.objects.filter(declined_by=DeclinedByStatus.Driver, user=user)
        paginator = CustomPageNumberPagination()
        paginated_trips = paginator.paginate_queryset(declined_trips, request)
        serializer = DeclineTripSerializer(paginated_trips, many=True)
        return paginator.get_paginated_response(serializer.data)

class DeclineTripListBySystemAPIView(APIView):  # missed Trips
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        declined_trips = DeclineTrip.objects.filter(declined_by=DeclinedByStatus.System, user=user)
        paginator = CustomPageNumberPagination()
        paginated_trips = paginator.paginate_queryset(declined_trips, request)
        serializer = DeclineTripSerializer(paginated_trips, many=True)
        return paginator.get_paginated_response(serializer.data)

    

class DriverTripStatusUpdate(APIView):
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def patch(self, request, trip_id):
        user = request.user
        new_status = request.data.get('trip_status')

        if not new_status:
            return Response({"error": "Trip status is required."}, status=status.HTTP_400_BAD_REQUEST)

        trip = get_object_or_404(Trip, id=trip_id)

        if trip.driver != user.driver:
            return Response({"error": "You are not authorized to update this trip."}, status=status.HTTP_403_FORBIDDEN)

        ten_days_ago = timezone.now() - timedelta(days=10)
        existing_trips = Trip.objects.filter(
            driver=user.driver,
            trip_status__in=[TripStatus.IN_PROGRESS, TripStatus.WAITING, TripStatus.OFF_TO_PICKUP,TripStatus.BREAK,
                                                           TripStatus.HALFWAY_COMPLETED, TripStatus.RETURN_IN_PROGRESS, TripStatus.PROCESSING_PAYMENT],
            booking_time__gte=ten_days_ago
        )
        if new_status in [TripStatus.IN_PROGRESS, TripStatus.OFF_TO_PICKUP, TripStatus.HALFWAY_COMPLETED,]:
            first_existing_trip = existing_trips.first()
            if first_existing_trip and first_existing_trip.id!= trip_id:

                if existing_trips.exists():
                    return Response({
                        "error": f"You have an existing trip with status '{first_existing_trip.trip_status}' from the last 10 days, so you cannot update this trip to '{new_status}'."
                    }, status=status.HTTP_400_BAD_REQUEST)

        trip.trip_status = new_status
        if new_status == TripStatus.IN_PROGRESS:
            trip.pickup_location_name = request.data.get('pickup_location_name')
            trip.pickup_location_lat = request.data.get('pickup_location_lat')
            trip.pickup_location_lng = request.data.get('pickup_location_lng')
            trip.pickup_time = timezone.now()
            trip.save()
            print("------------------pickup time: " + str(trip.pickup_time))

        if new_status == TripStatus.PROCESSING_PAYMENT:
            trip.final_dropoff_location_name = request.data.get('final_dropoff_location_name') or trip.initial_dropoff_location_name
            trip.final_dropoff_location_lat = request.data.get('final_dropoff_location_lat') or trip.initial_dropoff_location_lat
            trip.final_dropoff_location_lng = request.data.get('final_dropoff_location_lng') or trip.initial_dropoff_location_lng
            trip.save()

            pickup_lat = trip.pickup_location_lat
            pickup_lng = trip.pickup_location_lng
            dropoff_lat = trip.final_dropoff_location_lat
            dropoff_lng = trip.final_dropoff_location_lng
            print('-------------$$$$$$-------------------')
            print(f"pickup_lat: {pickup_lat}, pickup_lng: {pickup_lng}, dropoff_lat: {dropoff_lat}, dropoff_lng: {dropoff_lng}")

            if None in [pickup_lat, pickup_lng, dropoff_lat, dropoff_lng]:
                return Response({
                    "error": "Pickup and dropoff coordinates must be set to calculate distance and time."
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                final_distance_covered, _ = calculate_distance_and_time(
                    pickup_lat, pickup_lng, dropoff_lat, dropoff_lng
                )
            except Exception as e:
                return Response({
                    "error": f"Failed to calculate distance and time: {str(e)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            trip.final_distance_covered = Decimal(
                str(final_distance_covered)).quantize(Decimal('0.000001'))
            trip.final_dropoff_time = timezone.now()

            final_duration = Decimal(str(
                (trip.final_dropoff_time - trip.pickup_time).total_seconds() / 60)).quantize(Decimal('0.000001'))

            trip.final_duration = final_duration

            per_mile_cost = trip.per_mile_cost
            per_hour_cost = trip.per_hour_cost

            duration_hours = (final_duration / Decimal('60')
                              ).quantize(Decimal('0.000001'))
            distance_cost = (
                per_mile_cost * trip.final_distance_covered).quantize(Decimal('0.000001'))
            time_cost = (per_hour_cost *
                         duration_hours).quantize(Decimal('0.000001'))

            fare = (trip.booking_fee + distance_cost +
                    time_cost).quantize(Decimal('0.000001'))
            trip.fare = fare
            congestion_charge = trip.congestion_charge
            fare_with_congestion = (
                fare + congestion_charge).quantize(Decimal('0.000001'))

            service_charge = ((trip.service_charge / Decimal('100'))
                              * fare_with_congestion).quantize(Decimal('0.000001'))

            fare_with_service = (fare_with_congestion +
                                 service_charge).quantize(Decimal('0.000001'))

            vat = ((trip.vat / Decimal('100')) *
                   fare_with_service).quantize(Decimal('0.000001'))

            final_fare = (trip.client_tip + fare_with_service +
                          vat).quantize(Decimal('0.000001'))
            trip.final_fare = final_fare

        if new_status == TripStatus.COMPLETED:
            trip.trip_status = new_status
            # fare = (trip.fare + trip.total_extra_charge or 0).quantize(Decimal('0.000001'))
            # congestion_charge = trip.congestion_charge
            # fare_with_congestion = (
            #     fare + congestion_charge).quantize(Decimal('0.000001'))
            # service_charge = ((trip.service_charge / Decimal('100'))
            #                   * fare_with_congestion).quantize(Decimal('0.000001'))
            # fare_with_service = (fare_with_congestion +
            #                      service_charge).quantize(Decimal('0.000001'))
            # vat = ((trip.vat / Decimal('100')) *
            #        fare_with_service).quantize(Decimal('0.000001'))
            # final_fare = (trip.client_tip + fare_with_service +
            #               vat).quantize(Decimal('0.000001'))
            # trip.final_fare = trip.final_fare + trip.total_extra_charge or 0 + trip.client_tip or 0
        trip.save()
        return Response({"message": "Trip status updated successfully."}, status=status.HTTP_200_OK)

class TripCancelByDriver(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, trip_id):
        cancel_reason = request.data.get('cancel_reason')
        try:
            user = request.user
            driver = user.driver
        except AttributeError:
            return Response({"error": "User not found."}, status=status.HTTP_404_NOT_FOUND)
        try:
            trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        if trip.driver!= driver:
            return Response({"error": "You are not authorized to cancel this trip."}, status=status.HTTP_403_FORBIDDEN)
        try:
            with transaction.atomic():
                CancelTrip.objects.create(trip=trip,
                                          user=user,
                                          cancel_reason = cancel_reason,
                                          canceled_by = CanceledByStatus.Driver)
                trip.trip_status = TripStatus.CANCELLED
                trip.save()
            return Response({"message": "Trip calceled"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Failed to cancel the trip: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CancelTripList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
            user = request.user
            try:
                queryset = CancelTrip.objects.filter(user=user)
                paginator = CustomPageNumberPagination()
                paginated_data = paginator.paginate_queryset(queryset, request)
                serializer = CancelTripListSerializer(paginated_data, many=True)
                return paginator.get_paginated_response(serializer.data) 
            except Exception as e:
                return Response({"error": f"Failed to retrieve cancel trip list: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)           

class TakeTripBreak(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        user = request.user

        try:
            trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)

        if trip.driver != user.driver:
            return Response({"error": "You are not authorized to update this trip."}, status=status.HTTP_403_FORBIDDEN)

        if TripBreak.objects.filter(trip=trip, end_time__isnull=True).exists():
            return Response({"error": "Trip is already in a break."}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data.copy()
        data['trip'] = trip.id
        data['break_before_trip_status'] = trip.trip_status
        data['requested_by'] = user.id
        serializer = TripBreakSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            trip.trip_status = TripStatus.BREAK
            trip.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EndTripBreak(APIView):
    permission_classes = [IsAuthenticated]


    def patch(self, request, trip_id, break_id):
        user = request.user
        try:
            trip = Trip.objects.get(id=trip_id)

        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        if trip.driver != user.driver:
            return Response({"error": "You are not authorized to update this trip."}, status=status.HTTP_403_FORBIDDEN)
        try:
            trip_break = TripBreak.objects.get(trip=trip, id=break_id)
            
        except TripBreak.DoesNotExist:
            return Response({"error": "No ongoing break found with the provided ID."}, status=status.HTTP_404_NOT_FOUND)

        end_time = timezone.now()
        trip_break.end_time = end_time
        trip_break.save()
        trip.trip_status = trip_break.break_before_trip_status
        trip.save()
        serializer = TripBreakSerializer(trip_break)
        return Response(serializer.data, status=status.HTTP_200_OK)



class TripAddExtraCharge(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        user = request.user
        try:
            trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)

        if trip.driver != user.driver:
            return Response({"error": "You are not authorized to update this trip."}, status=status.HTTP_403_FORBIDDEN)

        data = {
            'trip': trip.id,
            'charge_amount': request.data.get('charge_amount'),
            'charge_type': request.data.get('charge_type'),
            'verified': True,
            'verified_by': None
        }

        serializer = ExtraChargeSerializer(data=data)
        if serializer.is_valid():
            extra_charge = serializer.save()
            pictures = request.FILES.getlist('pictures')
            picture_objects = []
            for picture in pictures:
                picture_objects.append(
                    ExtraChargePicture.objects.create(
                        extra_charge=extra_charge, 
                        picture=picture
                    )
                )
            response_serializer = ExtraChargeSerializer(
                extra_charge, 
                context={'request': request}
            )
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class TripListForDriver(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        trip_status_filter = request.query_params.get("trip_status")
        trip_method_filter = request.query_params.get("trip_method")
        order_by = request.query_params.get("order_by", "-pickup_time")
        order_direction = request.query_params.get("order_direction", "asc")

        user = request.user
        if not hasattr(user, "driver"):
            return Response({"error": "User is not a driver."}, status=status.HTTP_400_BAD_REQUEST)

        trips = Trip.objects.filter(driver=user.driver).order_by('-pickup_time')

        # Apply trip_status filter
        if trip_status_filter:
            if trip_status_filter == "Upcoming":
                trips = trips.filter(trip_status__in=[
                    TripStatus.OFF_TO_PICKUP,
                    TripStatus.WAITING,
                    TripStatus.APPROVED_BY_DRIVER
                ])
            elif trip_status_filter == "Ongoing":
                trips = trips.filter(trip_status__in=[
                    TripStatus.IN_PROGRESS,
                    TripStatus.WAITING,
                    TripStatus.OFF_TO_PICKUP,
                    TripStatus.BREAK,
                    TripStatus.HALFWAY_COMPLETED,
                    TripStatus.RETURN_IN_PROGRESS,
                    TripStatus.PROCESSING_PAYMENT
                ])
            elif trip_status_filter in dict(TripStatus.choices):
                trips = trips.filter(trip_status=trip_status_filter)

        # Apply trip_method filter
        if trip_method_filter and trip_method_filter in dict(TripMethod.choices):
            trips = trips.filter(trip_method=trip_method_filter)

        # Annotate fare if needed
        
        if order_by == "fare":
            trips = trips.annotate(
                effective_fare=Coalesce(
                    Case(
                        When(final_fare__gt=0, then=F("final_fare")),
                        default=Value(0),
                        output_field=DecimalField()
                    ),
                    Value(0),
                    output_field=DecimalField()
                )
            )
            order_field = "effective_fare"
        else:
            order_field = "pickup_time"


        if order_direction == "asc":
            trips = trips.order_by(F(order_field).asc(nulls_last=True))
        else:
            trips = trips.order_by(F(order_field).desc(nulls_last=True))

        # Paginate results
        paginator = CustomPageNumberPagination()
        paginated_trips = paginator.paginate_queryset(trips, request)

        # Gather unique place_ids from paginated results
        place_ids = set()
        for trip in paginated_trips:
            if trip.pickup_place_id:
                place_ids.add(trip.pickup_place_id)
            if trip.dropoff_place_id:
                place_ids.add(trip.dropoff_place_id)

        # Fetch and map LocationInfo for serializer context
        location_info_map = {}
        if place_ids:
            locations = LocationInfo.objects.filter(place_id__in=place_ids)
            location_info_map = {loc.place_id: loc for loc in locations}

        serializer = TripListForDriverSerializer(
            paginated_trips,
            many=True,
            context={"location_info_map": location_info_map}
        )
        return paginator.get_paginated_response(serializer.data)
class TripDetailForDriver(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, trip_id):
        try:
            trip = Trip.objects.get(id=trip_id)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)

        # Collect all place_ids
        place_ids = set()
        if trip.pickup_place_id:
            place_ids.add(trip.pickup_place_id)
        if trip.dropoff_place_id:
            place_ids.add(trip.dropoff_place_id)

        stopage_data = trip.stopage_place_ids or {}
        place_ids.update(stopage_data.values())

        # Fetch all relevant LocationInfo objects
        location_info_map = {}
        if place_ids:
            location_objects = LocationInfo.objects.filter(place_id__in=place_ids)
            location_info_map = {loc.place_id: loc for loc in location_objects}

        serializer = TripDetailForDriverSerializer(
            trip,
            context={"location_info_map": location_info_map}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)


class CompletedTripDetailForDriver(APIView):
    """
    API view to retrieve detailed information for a completed trip for a driver,
    including enhanced location information and stopages.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, trip_id):
        user = request.user
        
        try:
            # Get the trip belonging to the current driver
            trip = Trip.objects.get( id=trip_id)
            
            # Check if trip is completed
            if trip.trip_status != 'COMPLETED':
                return Response(
                    {"error": "Trip is not completed."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Collect all place_ids
            place_ids = set()
            if hasattr(trip, 'pickup_place_id') and trip.pickup_place_id:
                place_ids.add(trip.pickup_place_id)
            if hasattr(trip, 'dropoff_place_id') and trip.dropoff_place_id:
                place_ids.add(trip.dropoff_place_id)
            
            # Handle stopages if available
            stopage_data = {}
            if hasattr(trip, 'stopage_place_ids'):
                stopage_data = trip.stopage_place_ids or {}
                place_ids.update(stopage_data.values())
            
            # Fetch all relevant LocationInfo objects
            location_info_map = {}
            if place_ids:
                location_objects = LocationInfo.objects.filter(place_id__in=place_ids)
                location_info_map = {loc.place_id: loc for loc in location_objects}
            
            # Serialize the trip with the location context
            serializer = CompletedTripDetailForDriverSerializer(
                trip, 
                context={"location_info_map": location_info_map}
            )
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except Trip.DoesNotExist:
            return Response(
                {"error": "Trip not found."},
                status=status.HTTP_404_NOT_FOUND
            )
    

class TripSummary(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, trip_id):
        user = request.user
        trip = get_object_or_404(Trip, id=trip_id)
        serializer = TripSummarySerializer(trip)
        return Response(serializer.data)
    


class CancellationReasonsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        serializer = CancellationReasonSerializer({'reasons': DRIVER_CANCELLATION_REASONS})
        return Response(serializer.data)


