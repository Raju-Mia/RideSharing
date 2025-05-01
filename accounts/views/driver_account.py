import datetime
import json

from django.contrib import auth
from django.contrib.auth import get_user_model
from django.conf import settings
from django.utils import timezone
import jwt
from django.core.files.storage import default_storage
from rest_framework.exceptions import ValidationError
from django.db import transaction  # Make sure this is imported
from rest_framework.parsers import MultiPartParser, FormParser
from django.core.exceptions import ObjectDoesNotExist
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


from driver_app.models import (
    STATUS,
    Driver,
    DriverStatus,
    # DriverAttachmentStatus,
    # Manufacturer,
    Vehicle,
    VehicleModel,
    VehicleStatus,
    # VehicleTypesInfo,
    AttachmentStatus,
)



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
    create_driver_user,
    get_attachments_status,
    get_user_details,
    info_from_google,
    send_reset_password_code,
    update_driver_vehicle_info_status,
)


from accounts.mail import send_mail
from accounts.serializers import (
    ChangePasswordSerializer,
    DriverInfoForVerificationSerializer,
    DriverSignupSerializer,
    EmailSerializer,
    InfoForVerificationSerializer,
    # NamePictureChangeStateSerializer,
    # NotificationSettingsSerializer,
    OnlineUsersSerializer,
    OrganizationSignUpSerializer,
    PhoneExistsSerializer,
    PhoneNumberSerializer,
    # SavedAddressSerializer,
    SignUpSerializer,
    TokenValidationSerializer,
    DriverSerializerV2,
    AcceptDenySerializer,
    # DriverRegistrationOfOrganizationSerializer,
    DriverSerializer,
    LoginSerializer,
    SuperAdminLoginSerializer,
    LogoutSerializer,
    MyTokenObtainPairSerializer,
    UserSerializer,
    VehicleInfoForVerificationSerializer,
    # VehicleModelsSerializer,
    VehicleSerializer,
    # VehicleAssignWaitingListSerializer,
    UserUpdateSerializer,
    # VehicleRegistrationSerializer,
    UserSignUpSerializerForDriver,
    SocialLoginSerializer,
    EmailExistsSerializer,
    DriverResetPasswordSerializer,

    DriverSetNewPasswordSerializer,
    
    ResetPasswordSerializer,
    ValidateResetPasswordOtpSerializer,
    ResendOtpSerializer,
    SendMailVerificationSerializer,
    WhatsappNumberSerializer,
    # DriverDocumentsExpiredDateSerializer,
    # VehicleDocumentsExpiredDateSerializer,
    
    
    ValidateResetPasswordCodeSerializer
    
    
    
)



from accounts.permissions import (
    IsDriver,
    IsNotDriver,
    IsOrganization,
    is_driver,
    DriverWithNoRegisteredVehicle,
)

from accounts.views.accounts_helper import send_phone_verification_otp,sms_otp_is_verified
from accounts.serializers import OtpValidationSerializer
from accounts.models import VerificationOTP, VerificationTokens, TokenTypes



User = get_user_model()




#============= Driver Regisration ===================


class UserSignUpForDriverView(APIView):
    def post(self, request):
        print("====== Driver Account Registration Calling =====")
        serializer = UserSignUpSerializerForDriver(data=request.data)

        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)  # Debugging validation errors
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validated_data = serializer.validated_data
            phone = validated_data['phone']

            existing_user = User.objects.filter(phone=phone,  phone_is_verified=True).first()
            if existing_user:
                if hasattr(existing_user, 'driver'):
                    return Response(
                        {
                            "message": "Phone number is already used.",
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            with transaction.atomic():
                print('Validated Data:', validated_data)

                user_data = {
                    'phone': phone,
                    'password': validated_data['password'],
                    'service': validated_data['service'],
                }
                print("User Data:", user_data)

                # Create user
                user = create_driver_user(user_data)  # Ensure this function handles user as a driver creation
                print("Created User:", user)

                # Create driver profile
                driver = Driver.objects.create(
                    user=user,
                    date_of_birth=validated_data['date_of_birth']
                )
                print("Created Driver:", driver)

                return Response(
                    {
                        "user_id": user.id,
                        "driver_id": driver.id
                    },
                    status=status.HTTP_201_CREATED
                )

        except Exception as e:
            print("Exception:", str(e))
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


class ValidateTokenFromSMS(APIView):
    def post(self, request):
        serializer = OtpValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(id=serializer.validated_data["user_id"])
        except User.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "User does not exist"},
            )
        
        
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
            
            if is_driver(user):
                driver = Driver.objects.get(user=user)
                driver.status = "unverified"
                driver.save()
                
            return Response(data=get_user_details(user),status=status.HTTP_200_OK)
            
        return Response({"message": otp_verified_message},status=status.HTTP_400_BAD_REQUEST)




#============= Resend OTP for Driver Number Verification  ===================
class ResendOtpForNumberVerification(APIView):
    def get(self, request, user_id):
        print("============Resend Otp For Number Verification calling ==============")
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"message": "User Does Not Exit."},status=status.HTTP_400_BAD_REQUEST)
        
        
        try:
            # Filter all VerificationOTP objects for the given user
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
            user_verification_otp_objects.delete()

            print("Here---")
            # Call for new otp Generate
            # TODO: if user.user_is_verified:
            send_phone_verification_otp(user=user)
            
            response_data = {
                "message": "Reset OTP successfuly send your number.",
                "user_id": user.id
            }
            return Response(
                response_data,
                status=status.HTTP_200_OK,
                )

            
        except VerificationOTP.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        





# Driver Profile=========================
class SignUpAsDriverView(CreateAPIView):
    permission_classes = [IsAuthenticated & IsNotDriver]
    serializer_class = DriverSignupSerializer
    
    def perform_create(self, serializer):
        self.request.user.address = serializer.validated_data.pop("address", "")
        self.request.user.save()
        print("driver profile data set successfully.!")
        serializer.save(user=self.request.user)



# ==================== Manefacture and vehicle list ===================
# from accounts.serializers import TheManufacturerSerializer

# class ManufacturerWiseVehiclesList(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         # Query manufacturers that have associated VehicleModels
#         manufacturers = Manufacturer.objects.filter(vehiclemodel__isnull=False).distinct()
#         serializer = TheManufacturerSerializer(manufacturers, many=True)
#         return Response(serializer.data)




# ==================== Driver Vehicle Register ===================
# class RegisterVehicleView(CreateAPIView):
#     permission_classes = [DriverWithNoRegisteredVehicle]
#     serializer_class = VehicleRegistrationSerializer

#     def perform_create(self, serializer):
#         print("driver Vehicle Register Calling")
#         owner: Driver = self.request.user.driver
#         owner.status = DriverStatus.pending
#         owner.save()
#         serializer.save(owner=owner)





# # ========== Driver info and driver vehical approve status check =============


class VerificationStatusView(APIView):
    permission_classes = [IsAuthenticated, IsDriver]

    def get(self, request):
        try:
            # Initialize the data dictionary
            data = {}

            # Get the authenticated user
            user = request.user
            print("User:", user)
            
            # Access the driver's profile linked to the user
            driver = user.driver
            print("Driver Status:", driver.status)

            # Driver verification status
            # data["driver_profile_picture"] = driver.pp_size_driver_image.url if driver.pp_size_driver_image else None
            data["driver_verification_status"] = driver.status
            
            # Vehicle verification status
            vehicle = Vehicle.objects.filter(owner=driver).first() if user.service else None
            
            if vehicle:
                data["has_vehicle"] = True
                data["vehicle_verification_status"] = vehicle.status
            else:
                data["has_vehicle"] = False

            # Return the response with a 200 OK status
            return Response(data, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            # Handle the case where the driver or vehicle does not exist
            return Response(status=status.HTTP_404_NOT_FOUND, data={"message": "Driver or vehicle not found"})
        
        except Exception as e:
            # Handle any other unexpected errors
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR, data={"message": str(e)})






    

# Driver Reset Password =========================

class DriverResetPasswordView(APIView):
    def post(self, request):
        print("Driver Reset Password ==========Calling")
        serializer = DriverResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # print("serializer.validated_data["service"]")
        try:
            user = User.objects.get(
                phone=serializer.validated_data["phone_number"],
                is_active=True,
                service=serializer.validated_data["service"],
            )
        except User.DoesNotExist:
            return Response(
                {"message": "Requested user does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        try:
            # Filter all VerificationOTP objects for the given user
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user)
            user_verification_otp_objects.delete()


            print("I am here--")


            # Call for new otp Generate
            # TODO: if user.user_is_verified:
            if user.user_is_verified:
                send_phone_verification_otp(user=user)
            else:
                return Response({"message":"You are Not Verified User!"},status=status.HTTP_400_BAD_REQUEST)
            
            response_data = {
                "message": "Reset OTP sended successfully!",
                "user_id": user.id
            }
            return Response(
                response_data,
                status=status.HTTP_200_OK,
                )
            
        except VerificationOTP.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)



class DriverPasswordResetVerification(APIView):
    def post(self, request):
        print("========= DriverPasswordResetVerification =========")
        serializer = OtpValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = User.objects.get(id=serializer.validated_data["user_id"])
        except User.DoesNotExist:
            return Response(
                {"message": "User does not exist"},
                status=status.HTTP_400_BAD_REQUEST
                
            )
        otp_verified_status,otp_obj_id,otp_verified_message = sms_otp_is_verified(user,serializer.validated_data["verification_otp"])

        if otp_verified_status and otp_obj_id is not None:
            # Filter all VerificationOTP objects for the given user
            user_verification_otp_objects = VerificationOTP.objects.filter(user=user,id=otp_obj_id).first()
            user_verification_otp_objects.delete()

            user.is_active = True
            user.phone_is_verified = True
            user.user_is_verified = True
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
                "message":"Password Reset Verification Successfully Verified."
                }
            return Response(response_data,status=status.HTTP_200_OK)
        
        

        return Response({"message": otp_verified_message},status=status.HTTP_400_BAD_REQUEST)




class DriverPasswordChnage(APIView):
    def post(self, request):
        print("============= Driver Reset Password change ========calling==")
        serializer = DriverSetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        print(serializer.data)
        
        try:
            user = User.objects.get(id=serializer.validated_data["user_id"])
        except User.DoesNotExist:
            return Response(
                {"message": "User does not Exist!"},
                status=status.HTTP_400_BAD_REQUEST
            )
        

        try:
            verification_access_token = VerificationTokens.objects.get(id=serializer.validated_data["token_id"],user=user)
        except VerificationTokens.DoesNotExist:
            return Response({"message": "Verification Token does not Exit!"},status=status.HTTP_400_BAD_REQUEST,)
        
        # Token Verification status check.
        token_verified, token_message = verification_access_token.token_is_valid()
        
        if token_verified:
            user.set_password(serializer.validated_data["password"])
            user.password_has_changed = True
            user.save()
            # Delete Verification Access Token
            verification_access_token.delete()
            
            response_data={
                "message": "Password has been successfully changed."
                }
                           
            return Response(
                response_data,
                status=status.HTTP_200_OK
                )
        return Response({"message": "Reset Password Permission Expired"},status=status.HTTP_400_BAD_REQUEST,)
    
    
    
