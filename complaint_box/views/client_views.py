from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from complaint_box.models import ComplaintBox, ComplaintPicture
from complaint_box.serializers.client_serializers import ComplaintBoxSerializer, TripSerializer, ComplaintBoxDetailSerializer
from trip_management.models import Trip
from utils.pagination import CustomPageNumberPagination
from django.db.models import Q
from datetime import timedelta
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated

class RegisterComplain(APIView):
    def post(self, request, *args, **kwargs):
        user = request.user
        data = request.data.copy()
        print(data)
        
        trip_id = data.get('trip_id')
        if trip_id:
            try:
                trip = Trip.objects.get(id=trip_id)
                data['trip'] = trip.id
            except Trip.DoesNotExist:
                return Response(
                    {"error": "The specified trip does not exist."},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        data['case_id'] = ComplaintBox.generate_case_id()
        
        if user.is_authenticated:
            data['author'] = user.id
            data['author_name'] = user.full_name
            data['author_phone'] = user.phone
            data['author_email'] = user.email or None
            data['services'] = user.service
        else:
            data['services'] = request.data.get('services') or None
            if not all(key in data for key in ['author_name', 'author_phone', 'author_email']):
                return Response(
                    {"error": "Author details (name, phone, email) are required for anonymous users."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        serializer = ComplaintBoxSerializer(data=data)
        if serializer.is_valid():
            complaint = serializer.save()
            
            pictures = request.FILES.getlist('attachments')
            print(f"Received pictures: {pictures}")
            for picture in pictures:
                ComplaintPicture.objects.create(complaint=complaint, picture=picture)
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClientComplaintList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        complaints = ComplaintBox.objects.filter(author=user).order_by('-updated_at')
        paginator = CustomPageNumberPagination()
        paginated_complaints = paginator.paginate_queryset(complaints, request)
        serializer = ComplaintBoxSerializer(paginated_complaints, many=True)
        return paginator.get_paginated_response(serializer.data)



class ClientComplaintDetail(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, complaint_id):
        try:
            user = request.user
            complaint = ComplaintBox.objects.get(id=complaint_id, author=user)

            serializer = ComplaintBoxDetailSerializer(complaint)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ComplaintBox.DoesNotExist:
            return Response(
                {"detail": "Complaint not found or access denied."},
                status=status.HTTP_404_NOT_FOUND
            )



class TripList(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        thirty_days_ago = now() - timedelta(days=30)
        trips = Trip.objects.filter(user=user, pickup_time__date__gte=thirty_days_ago).order_by('-pickup_time')
        
        search_query = request.query_params.get('search', None)
        if search_query:
            trips = trips.filter(
                Q(unique_id__icontains=search_query) |
                Q(vehicle_type__icontains=search_query) |
                Q(booking_time__icontains=search_query) |
                Q(distance_type__icontains=search_query) |
                Q(pickup_time__icontains=search_query)
            )
        
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
