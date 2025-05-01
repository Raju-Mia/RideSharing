from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.core.cache import cache
from utils.pagination import CustomPageNumberPagination
# from accounts.models import Driver

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


from trip_management.models import Trip, TripBreak, ExtraCharge, TripStatus, TripMethod
from uc_admin.serializers.trip_serializers import TripListSerializer, DriverSerializer
from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import Http404
from django.db.models import Q
from django.shortcuts import get_object_or_404
User = get_user_model()






class DriverListCreateEditDelete(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination


    def post(self, request):
        full_name = request.data.get('full_name')
        phone = request.data.get('phone')
        date_of_birth = request.data.get('date_of_birth') 
        if date_of_birth is None:
            date_of_birth = datetime.strptime("22.04.1987", "%d.%m.%Y").date()



        if not full_name or not phone:
            return Response({"message": "Full name and phone are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create(
            full_name=full_name,
            phone=phone,
            whatsappnumber=phone,
        )

        driver = Driver.objects.create(user=user, date_of_birth=date_of_birth)

        # serializer = DriverSerializer(driver)
        message = "Created driver successfully"

        return Response(message, status=status.HTTP_201_CREATED)
    

    def get(self, request):
        drivers = Driver.objects.filter(Q(user__email__isnull=True) | Q(user__email=""))

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(drivers, request)
        
        serializer = DriverSerializer(page, many=True)
        data = serializer.data

        return paginator.get_paginated_response(data)
    




    

    def delete(self, request, driver_id=None):
        if not driver_id:
            return Response({"error": "Driver ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            driver = get_object_or_404(Driver, id=driver_id)
            user = driver.user
            user.delete()                
            return Response({"message": "Driver and associated user successfully deleted."}, status=status.HTTP_200_OK)
        except Http404:
            return Response({"error": "Driver not found."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
    
    
    def put(self, request, driver_id):
        try:
            driver = Driver.objects.get(id=driver_id)
        except Driver.DoesNotExist:
            return Response({"message": "Driver not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = DriverSerializer(driver, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)