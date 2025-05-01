import datetime
import json

from django.contrib import auth
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
import jwt

from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import permissions, status
from rest_framework.exceptions import PermissionDenied
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    GenericAPIView,
    RetrieveAPIView,
    get_object_or_404,
    ListAPIView,
    CreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import viewsets
from utils.pagination import CustomPageNumberPagination



from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt import views, serializers
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


from utils.helpers import generate_otp
from utils.validators import password_validator
from utils.mail import send_email_verification_token
from utils.sms import send_phone_verification_sms, sms_token_is_verified
from driver_app.serializers import DriverProfileEditRequestSerializer, AdminApprovalSerializer
from driver_app.models import (
    Driver,
    AttachmentStatus,
    DriverProfileEditRequest,
    DriverStatus,
    # DriverAttachmentStatus,
    )


from accounts.helpers import (
    create_user,
    get_attachments_status,
    get_user_details,
    info_from_google,
    send_reset_password_code,
    update_driver_vehicle_info_status,
)


from accounts.mail import send_mail



from accounts.permissions import (
    IsDriver,
    IsNotDriver,
    IsOrganization,
    is_driver,
    DriverWithNoRegisteredVehicle,
)

from accounts.signals import send_mail_verification_update_to_driver

User = get_user_model()


class DriverProfileDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user

        name = user.full_name
        phone = user.phone
        sum_of_ratings = user.sum_of_ratings        
        if user.picture:
            photo = request.build_absolute_uri(user.picture.url) if hasattr(user.picture, 'url') else None
        else:
            photo = None
            
        data = {
            "name": name,
            "phone": phone,
            "rating": sum_of_ratings,
            "profile_photo": photo,
        }
        return Response(data, status=status.HTTP_200_OK)


class DriverProfileEditRequestView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = DriverProfileEditRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, status=AttachmentStatus.submitted)
            return Response({"message": "Edit request submitted successfully!"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class AdministrationDriverProfileEditRequestListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        paginator = CustomPageNumberPagination()
        status_filter = request.query_params.get('status', None)
        if status_filter:
            edit_requests = DriverProfileEditRequest.objects.filter(status=status_filter).order_by('-created_at')
        else:
            edit_requests = DriverProfileEditRequest.objects.all().order_by('-created_at')
        paginated_requests = paginator.paginate_queryset(edit_requests, request)
        serializer = AdminApprovalSerializer(paginated_requests, many=True)
        return paginator.get_paginated_response(serializer.data)
    

class AdministrationEditRequestDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            edit_request = DriverProfileEditRequest.objects.get(id=pk)
        except DriverProfileEditRequest.DoesNotExist:
            return Response({"error": "Edit request not found."}, status=404)

        serializer = AdminApprovalSerializer(edit_request)
        return Response(serializer.data, status=status.HTTP_200_OK)


class AdminDriverProfileEditRequestApprovalView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, pk):
        try:
            edit_request = DriverProfileEditRequest.objects.get(id=pk)
        except DriverProfileEditRequest.DoesNotExist:
            return Response(
                {"message": "Edit request not found or already processed."}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        approval_status = request.data.get('status')
        admin_comment = request.data.get('admin_comment', '')
        

        
        edit_request.status = approval_status
        edit_request.admin_comment = admin_comment
        edit_request.save()
        
        if approval_status == "verified":
            user = edit_request.user
            try:
                driver = user.driver  # Access the related Driver instance
                if edit_request.picture:
                    user.picture = edit_request.picture
                    user.save()  # Save changes to the user instance
            except Driver.DoesNotExist:
                return Response(
                    {"message": "Associated driver profile not found."}, 
                    status=status.HTTP_404_NOT_FOUND
                )
        
        message = {"message": f"Request {approval_status.lower()} successfully!"}
        return Response(message, status=status.HTTP_200_OK)


