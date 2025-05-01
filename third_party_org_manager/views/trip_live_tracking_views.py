from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from utils.pagination import CustomPageNumberPagination
from third_party_org_manager.models import Organization
from trip_management.models import Trip,TripStatus
from django.shortcuts import get_object_or_404
from third_party_org_manager.serializers.trip_live_tracking_serializers import (OrganizationTripListForLiveTrackingSerializer,
                                                                                OrganizationTripCurrentLocationSerializer, OrganizationTripInfoForLiveTrackingSerializer)
from django.db.models import Q











class OrganizationTripListForLiveTracking(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination


    def get(self, request, *args, **kwargs):
        user = request.user
        organization_id = user.organization.id
        search_query = request.query_params.get('search', None)


        allowed_statuses = [
            TripStatus.IN_PROGRESS, TripStatus.WAITING, TripStatus.OFF_TO_PICKUP, TripStatus.BREAK,
            TripStatus.HALFWAY_COMPLETED, TripStatus.RETURN_IN_PROGRESS, TripStatus.PROCESSING_PAYMENT
        ]


        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)

        queryset = Trip.objects.filter(
            user__organization_id=organization_id, trip_status__in=allowed_statuses).order_by('-booking_time')


        if search_query:
            queryset = queryset.filter(
                Q(passenger_name__icontains=search_query) |
                Q(pickup_location_name__icontains=search_query) |
                Q(final_dropoff_location_name__icontains=search_query)
            )

        paginator = self.pagination_class()
        paginated_trips = paginator.paginate_queryset(queryset, request)

        serializer = OrganizationTripListForLiveTrackingSerializer(paginated_trips, many=True)
        return paginator.get_paginated_response(serializer.data)




class OrganizationTripCurrentLocation(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        organization_id = user.organization.id

        allowed_statuses = [
            TripStatus.IN_PROGRESS, 
            TripStatus.WAITING, 
            TripStatus.OFF_TO_PICKUP, 
            TripStatus.RETURN_IN_PROGRESS, 
            TripStatus.BREAK,
            TripStatus.HALFWAY_COMPLETED
        ]

        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)
        trips = Trip.objects.filter(user__organization_id=organization_id, trip_status__in=allowed_statuses).order_by('-booking_time')
        serializer = OrganizationTripCurrentLocationSerializer(trips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    

class OrganizationTripInfoForLiveTracking(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, trip_id):
        trip = get_object_or_404(Trip, id=trip_id, user__organization_id=request.user.organization.id)        
        serializer = OrganizationTripInfoForLiveTrackingSerializer(trip)
        return Response(serializer.data, status=status.HTTP_200_OK)







