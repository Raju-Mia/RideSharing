import datetime
import json

from django.contrib import auth
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
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


from utils.pagination import CustomPageNumberPagination #RM Add



from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt import views, serializers
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

# from trip_management.models import Source, VehicleAssignWaitingList
# from uc_admin.serializers.old_views_serializers import ClientInfoSerailizer, DriverProfileSerializer
from utils.helpers import generate_otp
from utils.validators import password_validator
from utils.mail import send_email_verification_token
from utils.sms import send_phone_verification_sms, sms_token_is_verified



from accounts.helpers import (
    create_user,
    get_attachments_status,
    get_user_details,
    info_from_google,
    send_reset_password_code,
    update_driver_vehicle_info_status,
)


from accounts.mail import send_mail
from accounts.serializers import (

    
    LoginSerializer,


    
)


from accounts.permissions import (
    IsDriver,
    IsNotDriver,
    IsOrganization,
    is_driver,
    DriverWithNoRegisteredVehicle,
)

# from accounts.serializers import SourceSerializer
from accounts.signals import send_mail_verification_update_to_driver
from accounts.views.accounts_helper import send_phone_verification_otp,sms_otp_is_verified
from accounts.models import VerificationOTP
from accounts.views.accounts_helper import user_exists

#FCM Token Register
from notification_manager.views.fcm_token_register import register_fcm_token

from rest_framework_simplejwt.tokens import RefreshToken
User = get_user_model()


from notification_manager.webPushNotificaiton_helper import registerWebPushSubscription, send_web_push_notification


# =========== Driver and Administration login ======main=======
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator



@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        print("==== Login calling ======")
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():

            print("i am here!")
            phone_or_email = serializer.validated_data['phone_or_email']
            password = serializer.validated_data['password']
            print("I am here: ")
            service = serializer.validated_data.get('service', '')
            print("service is: ", service)
            
            user = authenticate(request, phone_or_email=phone_or_email, password=password, service=service)

            if user:
                #========== User Register For Web Push Notification Subscription =========
                payload = request.data
                response = registerWebPushSubscription(user, payload)
                print("The Response: ", response)
                
                # ===User Notification FCM Token Register==
                fcm_token = request.data.get('device_token')
                print("fcm_token: ", fcm_token)
                
                
                if fcm_token:
                    token_instance, is_new = register_fcm_token(user, fcm_token)
                    if is_new:
                        # Handle the case where a new token was created (e.g., log, notify, etc.)
                        message= "New device registered with FCM token."
                    else:
                        message = "Existing FCM token found."
                return Response(get_user_details(user), status=status.HTTP_200_OK)
            
            
            else:
                print("--here-2-")
                # Custom error messages based on the type of failure
                user_model = get_user_model()
                try:
                    if "@" in phone_or_email:
                        user = user_model.objects.get(email=phone_or_email, terminated_status=False)
                    else:
                        user = user_model.objects.get(phone=phone_or_email, terminated_status=False)

                    if not user.is_active:
                        return Response({'message': 'User account is inactive'}, status=status.HTTP_400_BAD_REQUEST)
                    if not user.check_password(password):
                        return Response({'message': 'Incorrect password'}, status=status.HTTP_400_BAD_REQUEST)
                    if not user.is_superuser and user.service != service:
                        return Response({'message': 'Invalid credentials, Service mismatch!'}, status=status.HTTP_400_BAD_REQUEST)
                    if not user.is_superuser and "@" in phone_or_email and not user.email_is_verified:
                        return Response({'message': 'Email is not verified'}, status=status.HTTP_400_BAD_REQUEST)
                    if not user.is_superuser and not "@" in phone_or_email and not user.phone_is_verified:
                        return Response({'message': 'Phone number is not verified'}, status=status.HTTP_400_BAD_REQUEST)
                    if not user.is_superuser and not user.user_is_verified:
                        return Response({'message': 'User is not verified'}, status=status.HTTP_400_BAD_REQUEST)
                except user_model.DoesNotExist:
                    print(" i am here!======",user_model.DoesNotExist)
                    return Response({'message': 'User does not exist'}, status=status.HTTP_400_BAD_REQUEST)

                return Response({'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    


