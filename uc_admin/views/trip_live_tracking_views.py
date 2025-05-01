import logging
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Prefetch, Q
from django.core.cache import cache
from utils.pagination import CustomPageNumberPagination
from trip_management.models import Trip, TripBreak, ExtraCharge, TripStatus, TripMethod
from uc_admin.serializers.trip_live_tracking_serializers import (TripListSerializer, TripInfoForLiveTrackingSerializer,
                                                                 TripCurrentLocationSerializer)
from django.shortcuts import get_object_or_404

class TripListForLiveTracking(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search_query = request.query_params.get('search', None)
        trip_method_filter = request.query_params.get('trip_method', None)

        allowed_statuses = [
            TripStatus.IN_PROGRESS, 
            TripStatus.WAITING, 
            TripStatus.OFF_TO_PICKUP, 
            TripStatus.RETURN_IN_PROGRESS, 
            TripStatus.PROCESSING_PAYMENT,
            TripStatus.BREAK,
            TripStatus.HALFWAY_COMPLETED
        ]
        trips = Trip.objects.filter(trip_status__in=allowed_statuses).order_by('-booking_time')

        if search_query:
            trips = trips.filter(
                Q(unique_id__icontains=search_query) |
                Q(booking_time__icontains=search_query) |
                Q(pickup_location_name__icontains=search_query) |
                Q(final_dropoff_location_name__icontains=search_query) |
                Q(initial_dropoff_location_name__icontains=search_query) |
                Q(pickup_time__icontains=search_query)
            )

        if trip_method_filter:
            trips = trips.filter(trip_method=trip_method_filter)

        paginator = CustomPageNumberPagination()
        paginated_trips = paginator.paginate_queryset(trips, request)

        if paginated_trips is not None:
            serializer = TripListSerializer(paginated_trips, many=True)
            return paginator.get_paginated_response(serializer.data)

        return paginator.get_paginated_response([])
    

class TripCurrentLocation(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        allowed_statuses = [
            TripStatus.IN_PROGRESS, 
            TripStatus.WAITING, 
            TripStatus.OFF_TO_PICKUP, 
            TripStatus.RETURN_IN_PROGRESS, 
            TripStatus.PROCESSING_PAYMENT,
            TripStatus.BREAK,
            TripStatus.HALFWAY_COMPLETED
        ]
        trips = Trip.objects.filter(trip_status__in=allowed_statuses).order_by('-booking_time')
        serializer = TripCurrentLocationSerializer(trips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




class TripInfoForLiveTracking(APIView):
    permission_classes = [IsAuthenticated]
    """
    API view to retrieve trip information for live tracking.
    """
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id)        
        serializer = TripInfoForLiveTrackingSerializer(trip)
        return Response(serializer.data, status=status.HTTP_200_OK)