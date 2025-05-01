from django.shortcuts import render

from django.shortcuts import render
from django.http import Http404
from django.conf import settings
from utils.pagination import CustomPageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

from django.contrib.auth import authenticate
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

#Import
from accounts.helpers import (
    create_user,
    get_attachments_status,
    get_user_details,
    info_from_google,
    send_reset_password_code,
    update_driver_vehicle_info_status,
)

from utils.mail import send_mail, send_otp_mail, send_resend_otp_mail
from accounts.views.accounts_helper import send_phone_verification_otp, sms_otp_is_verified, mail_otp_is_verified
from django.contrib.auth import get_user_model
User = get_user_model()



from client_app.serializers.profile import ClientProfileUpdateSerializer




# Create your views here.
#============== Operator Profile Update ============== 
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from accounts.models import UserProfile


class ClientProfileUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = ClientProfileUpdateSerializer(user, data=request.data, partial=True, context={'request': request})
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Profile updated successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response({
            "message": "Failed to update profile.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)