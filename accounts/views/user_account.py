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


from utils.pagination import CustomPageNumberPagination #RM Add



from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt import views, serializers
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken

# from trip.models import Source, VehicleAssignWaitingList
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
    SignUpSerializer,

    UserLoginSerializer,
    UserLoginVerificationSerializer,
    
    UserSerializer,

    
    
    
)

from accounts.models import (
    VerificationTokens,
    TokenTypes,

)
from accounts.permissions import (
    IsDriver,
    IsNotDriver,
    IsOrganization,
    is_driver,
    DriverWithNoRegisteredVehicle,
)

# from accounts.serializers import SourceSerializer
from django.contrib.auth import authenticate

User = get_user_model()





# ============Client/User Registration =================
class SignUpUser(APIView):
    def post(self, request):
        print("========== Client/User SignUpUser Calling ==========")
        serializer = SignUpSerializer(data=request.data)
          
                
        # Check if serializer data is valid
        if not serializer.is_valid():
            # Construct error response
            errors = serializer.errors
            print("Serializer data error: ", errors)
            
            # Extract error messages and format them as specified
            error_details = []
            for field, messages in errors.items():
                for message in messages:
                    error_details.append({"field": field, "issue": message})
                    
            # Construct response data
            response_data = {
                "error": {
                    "code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                    "message": "Validation Error",
                    "details": error_details
                    }
                }
            return Response(response_data, status=status.HTTP_422_UNPROCESSABLE_ENTITY) 
                
        
        # Serializer is valid.
        serializer.is_valid(raise_exception=True)
        serializer.validate_email_address(
            serializer.validated_data["email"], serializer.validated_data["service"]
        )
        

        # Create user
        try:
            user = create_user(serializer)
            user_serializer = UserSerializer(user)  # Assuming UserSerializer is your serializer
            response_data = {
                "user": user_serializer.data,
                "messages": "User Successfully Created."
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response({"message": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





from accounts.serializers import UserProfileCreateSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.views.accounts_helper import send_phone_verification_otp,sms_otp_is_verified
from accounts.models import VerificationOTP

# from accounts.serializers import SourceSerializer
# from accounts.signals import send_mail_verification_update_to_driver
from accounts.views.accounts_helper import user_exists
from django.views.decorators.csrf import csrf_exempt


#FCM Token Register
from notification_manager.views.fcm_token_register import register_fcm_token




# =============== User/Client Login. =================== 
class UserLogin(APIView):
    def post(self, request, *args, **kwargs):
        print("==== User Login calling ==11===")
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            phone_or_email = serializer.validated_data['phone_or_email']
            service = serializer.validated_data.get('service', '')
            
            user_already_exit = user_exists(phone_or_email)
            # print("user_already_exit status: ", user_already_exit)
            
            # user_active_status = serializer.validated_data['user_active_status']
            # user_is_verified = serializer.validated_data['user_is_verified']

            
            if user_already_exit:
                # print("i am here=========/0202//====")
                user = authenticate(request, phone_or_email=phone_or_email, service=service)
                if user:
                    if user.terminated_status:
                        return Response({"message": "Account has been terminated"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    if "@" in phone_or_email and not user.email_is_verified:
                        return Response({"message": "Email is not verified"}, status=status.HTTP_400_BAD_REQUEST)
                    if not "@" in phone_or_email and not user.phone_is_verified:
                        return Response({"message": "Phone number is not verified"}, status=status.HTTP_400_BAD_REQUEST)
                    if not user.user_is_verified:
                        return Response({"message": "User is not verified"}, status=status.HTTP_400_BAD_REQUEST)
                    
                    VerificationOTP.objects.filter(user=user).delete()
                    send_phone_verification_otp(user)
                    
                    response_data = {
                        "user_id": user.id,
                        "message": "Login OTP Send Successfully."
                    }
                    # print("---------020202------------")
                    
                    # ===User Notification FCM Token Register==
                    fcm_token = request.data.get('fcm_token')
                    if fcm_token:
                        token_instance, is_new = register_fcm_token(user, fcm_token)
                        if is_new:
                            # Handle the case where a new token was created (e.g., log, notify, etc.)
                            message= "New device registered with FCM token."
                        else:
                            message = "Existing FCM token found."
                            
                        
                    return Response(response_data, status=status.HTTP_200_OK)
                else:
                    return Response({'message': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)
                
            else:
                print("--New User Saved Successfully.--")
                user = serializer.save()
                VerificationOTP.objects.filter(user=user).delete()
                
                if user:
                    send_phone_verification_otp(user)
                else:
                    return Response({"message": "User does not created!"}, status=status.HTTP_400_BAD_REQUEST)
                
                response_data = {
                    "user_id": user.id,
                    "message": "Login OTP Send Successfully."
                }
                return Response(response_data, status=status.HTTP_200_OK)
            
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



# =============== User/Client Verification. =================== 
class UserLoginVerification(APIView):
    def post(self, request, *args, **kwargs):
        print("==== User Login Verification calling ===verification===")
        serializer = UserLoginVerificationSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user = User.objects.get(id=serializer.validated_data["user_id"])
            except User.DoesNotExist:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={"message": "User does not exist"},
                )
                    
            
            if user.user_is_verified:
                print("-- login---")
                otp_verified_status,otp_obj_id,otp_verified_message = sms_otp_is_verified(user,serializer.validated_data["verification_otp"])
                # print("otp_verified_status,otp_obj_id,otp_verified_message", otp_verified_status,otp_obj_id,otp_verified_message)
                
                
                if otp_verified_status and otp_obj_id is not None:
                    # Filter all VerificationOTP objects for the given user
                    user_verification_otp_objects = VerificationOTP.objects.filter(user=user,id=otp_obj_id).first()
                    user_verification_otp_objects.delete()

                    user.is_active = True
                    user.phone_is_verified = True
                    user.user_is_verified = True
                    user.save()
                        
                    return Response(data=get_user_details(user),status=status.HTTP_200_OK)
                
                return Response({"message": otp_verified_message},status=status.HTTP_400_BAD_REQUEST)
        
        
            elif not user.user_is_verified:
                print("-- New User Create---")
                
                print("i am here=======1====ok=== ")
                otp_verified_status,otp_obj_id,otp_verified_message = sms_otp_is_verified(user,serializer.validated_data["verification_otp"])
                # print("otp_verified_status,otp_obj_id,otp_verified_message", otp_verified_status,otp_obj_id,otp_verified_message)
                
                
                if otp_verified_status and otp_obj_id is not None:
                    print("i am here=======2======= ")
                    
                    # Filter all VerificationOTP objects for the given user
                    user_verification_otp_objects = VerificationOTP.objects.filter(user=user,id=otp_obj_id).first()
                    user_verification_otp_objects.delete()


                    user.is_active = True
                    user.phone_is_verified = True
                    # user.user_is_verified = True
                    user.save()
                    
                    # one Time VerificationTokens Gerate.
                    token = VerificationTokens.objects.create(
                        user=user,
                        token_type=TokenTypes.password_reset,
                        token=generate_otp(),
                        token_life_time=int(60)
                        )

                    # return Response(data=get_user_details(user),status=status.HTTP_200_OK)
                    response_data = {
                        "user_id": user.id,
                        "token_id":token.id,
                        "message":"Verification Successfully Verified."
                        }
                    return Response(response_data,status=status.HTTP_200_OK)
                
                else:
                    print("i am here=======3======= ")
                    return Response({"message":otp_verified_message},status=status.HTTP_400_BAD_REQUEST)
                
                
            else:
                return Response({'message': "Invaild Credencial"}, status=status.HTTP_400_BAD_REQUEST)
                    
        
        return Response({'message': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)





class ResendOtpForUserVerificaiton(APIView):
    
        def post(self, request, user_id):
            print("============Resend Otp For user verfication ==============")
            
            try:
                user = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({"message": "User Does Not Exit."},status=status.HTTP_400_BAD_REQUEST)
            
            
            if user:
                # Filter all VerificationOTP objects for the given user
                user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
                user_verification_otp_objects.delete()

                print("Here---")
                # Call for new otp Generate
                # TODO: if user.user_is_verified:
                send_phone_verification_otp(user=user)
                
                response_data = {
                    "message": "Resend OTP successfuly send your number.",
                    "user_id": user.id
                }
                return Response(
                    response_data,
                    status=status.HTTP_200_OK,
                    )

                
            else:
                response_data = {
                    "message": "User does not exit."
                }
                return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
        







# =============== User/Client Profile Create. =================== 
# class UserProfileCreateView(APIView):
#     def post(self, request):
#         print(" ====User Profile Update =========== Calling ==")
        
#         serializer = UserProfileCreateSerializer(data=request.data)
        
#         if serializer.is_valid(raise_exception=True):
#             print("serializer is vaild!")
#             # print("Profile data: ", serializer.data)
            
#             full_name_is = serializer.validated_data['full_name']
#             phone_is = serializer.validated_data['phone']
#             email_is = serializer.validated_data['email']
#             picture_is = serializer.validated_data['picture']

            
#             try:
#                 user = User.objects.get(id=serializer.validated_data["user_id"])
#             except User.DoesNotExist:
#                 return Response(
#                     status=status.HTTP_400_BAD_REQUEST,
#                     data={"message": "User does not exist"})
                
#             try:
#                 verification_access_token = VerificationTokens.objects.get(id=serializer.validated_data["token_id"],user=user)
#             except VerificationTokens.DoesNotExist:
#                 return Response({"message": "Verification Token does not Exit!"},status=status.HTTP_400_BAD_REQUEST,)
            
#             # Token Verification status check.
#             token_verified, token_message = verification_access_token.token_is_valid()
            
#             if user.phone == phone_is and token_verified:
#                 user.full_name = full_name_is
#                 user.phone = phone_is
#                 user.email = email_is
#                 user.picture = picture_is
                
#                 user.is_active = True
#                 user.phone_is_verified = True
#                 user.user_is_verified = True
#                 user.save()
                
#                 # Delete Verification Access Token
#                 verification_access_token.delete()
                    
#                 return Response(data=get_user_details(user),status=status.HTTP_200_OK)
#             else:
#                 return Response(
#                     status=status.HTTP_400_BAD_REQUEST,
#                     data={"message": "Something is wrong,please check your credentials!"})
            
#         return Response({"message": serializer.error_messages},status=status.HTTP_400_BAD_REQUEST)
    
    
    
class UserProfileCreateView(APIView):
    def post(self, request):
        print("==== User Profile Update =========== Calling ===")
        
        serializer = UserProfileCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                user_id = serializer.validated_data["user_id"]
                token_id = serializer.validated_data["token_id"]
                full_name_is = serializer.validated_data["full_name"]
                phone_is = serializer.validated_data.get("phone")
                email_is = serializer.validated_data.get("email")
                picture_is = serializer.validated_data.get("picture")
                
                # Check if the user exists
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    return Response({"error": "User does not exist."}, status=status.HTTP_404_NOT_FOUND)
                
                # Check if the verification token exists
                try:
                    verification_access_token = VerificationTokens.objects.get(id=token_id, user=user)
                except VerificationTokens.DoesNotExist:
                    return Response(
                        {"error": "Verification token does not exist."},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                
                # Token verification status check
                token_verified, token_message = verification_access_token.token_is_valid()
                if not token_verified:
                    return Response(
                        {"error": f"Token verification failed: {token_message}"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
                # Ensure phone matches
                if user.phone != phone_is:
                    return Response(
                        {"error": "The phone number does not match the user's record."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                
                # Update user details
                user.full_name = full_name_is
                user.phone = phone_is
                user.email = email_is
                user.picture = picture_is
                user.is_active = True
                user.phone_is_verified = True
                user.user_is_verified = True
                user.save()

                # Delete verification token
                verification_access_token.delete()

                return Response(data=get_user_details(user), status=status.HTTP_200_OK)
            
            except KeyError as e:
                return Response(
                    {"error": f"Missing required field: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except Exception as e:
                return Response(
                    {"error": f"An unexpected error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        else:
            # Return detailed field errors
            return Response(
                {"errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
    
    
    




class UserDetailsView(APIView):
    def get(self, request):
        users = User.objects.all()
        data = [
            {
                'id': user.id,
                'full_name': f"{user.first_name} {user.last_name}",
                'username': user.username,
            }
            for user in users
        ]
        return Response(data, status=status.HTTP_200_OK)