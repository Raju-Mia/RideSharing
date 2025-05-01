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
    ChangePasswordSerializer,
    DriverInfoForVerificationSerializer,
    DriverSignupSerializer,
    EmailSerializer,
    InfoForVerificationSerializer,

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
    ResetPasswordSerializer,
    ValidateResetPasswordOtpSerializer,
    ResendOtpSerializer,
    SendMailVerificationSerializer,
    WhatsappNumberSerializer,
    # DriverDocumentsExpiredDateSerializer,
    # VehicleDocumentsExpiredDateSerializer,
    
    
    ValidateResetPasswordCodeSerializer
    
    
    
)

from accounts.models import (
    PhoneEmailChangeState,
    VerificationOTP,
    VerificationTokens,
    TokenTypes,

)

from driver_app.models import (
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



from accounts.permissions import (
    IsDriver,
    IsNotDriver,
    IsOrganization,
    is_driver,
    DriverWithNoRegisteredVehicle,
)

# from accounts.serializers import SourceSerializer
from accounts.signals import send_mail_verification_update_to_driver

User = get_user_model()








class RegisterHotel(CreateAPIView):
    serializer_class = SignUpSerializer

    def perform_create(self, serializer):
        serializer.save(is_hotel=True)


class OrganizationSignUp(APIView):
    def post(self, request):
        user_serializer = SignUpSerializer(data=request.data)
        user_serializer.is_valid(raise_exception=True)
        org_serializer = OrganizationSignUpSerializer(data=request.data)
        org_serializer.is_valid(raise_exception=True)
        user = create_user(user_serializer)
        org_serializer.save(user=user)
        data = {"id": user.id}
        return Response(data, status=status.HTTP_201_CREATED)


# Social Auth
class SocialLoginRegister(APIView):
    def post(self, request, provider):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        data = None
        if provider == "google":
            data = info_from_google(token)
        if not data:
            data = {"details": ":)"}
            return Response(data, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.get(
                email=data["email"],
                is_active=True,
                service=serializer.validated_data["service"],
            )
            return Response(get_user_details(user), status=status.HTTP_200_OK)
        except User.DoesNotExist:
            user = User.objects.create(
                email=data["email"],
                full_name=data["first_name"] + " " + data["last_name"],
                is_active=True,
                service=serializer.validated_data["service"],
                email_is_verified=True,
            )
            return Response(get_user_details(user), status=status.HTTP_201_CREATED)



# APi view for user Details
class UserDetailAPI(APIView):
    def get(self, request, *args, **kwargs):
        user = User.objects.all()
        serializer = UserSerializer(user, many=True)
        return Response(serializer.data)


# API view for Driver Details
class DriverDetailAPI(APIView):
    def get(self, request, *args, **kwargs):
        user = Driver.objects.all()
        serializer = DriverSerializer(user, many=True)
        return Response(serializer.data)





        
        

# =========== UC Administration Admin Login ======2(future implement)=======
from accounts.models import CustomUser, Admin
class SuperAdminLoginView(APIView):
    def post(self, request):
        print("-========== Super Admin login View ============== ")

        serializer = SuperAdminLoginSerializer(data=request.data)
        print(serializer)
        serializer.is_valid(raise_exception=True)

        phone_or_email = serializer.validated_data.get("phone_or_email")
        password = serializer.validated_data.get("password")

        user = None
        if "@" in phone_or_email:
            try:
                user = CustomUser.objects.get(email=phone_or_email)
            except CustomUser.DoesNotExist:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        else:
            try:
                user = CustomUser.objects.get(phone=phone_or_email)
            except CustomUser.DoesNotExist:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Manually check the password
        if user and user.check_password(password):
            if hasattr(user, 'admin') and user.admin.authority_level == 'superuser':
                if hasattr(user, "organization") and not user.organization.is_verified:
                    return Response(
                        {"error": "Organization is not verified yet"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                return Response(get_user_details(user), status=status.HTTP_200_OK)
            else:
                return Response({"error": "User is not a superadmin"}, status=status.HTTP_403_FORBIDDEN)
        
        return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
    







class UserCratesDriver(CreateAPIView):
    serializer_class = DriverSerializerV2
    permission_classes = [IsNotDriver]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)




class ValidateToken(APIView):
    def post(self, request):
        print("=========== User sign-up ValidateToken Calling ==========")
        
        serializer = TokenValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            user = User.objects.get(id=serializer.validated_data["id"])
            print("----------user is: ", user)
        except User.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "User does not exist"},
            )

        try:
            token = VerificationTokens.objects.get(
                user=user, token=serializer.validated_data["token"]
            )
            print("----------token-------- is: ", token)
            
        except VerificationTokens.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={"message": "Token does not exist"},
            )
            
            
        if token.is_valid:
            change_obj: PhoneEmailChangeState = PhoneEmailChangeState.objects.filter(user=user).first()
            print("======= change_obj ========", change_obj)
        
            # if change_obj:
            #     user.email = change_obj.new_email
            #     user.save()
            #     return Response(
            #         data=get_user_details(user),
            #         status=status.HTTP_200_OK,
            #     )
                
            token.delete()
            user.is_active = True
            user.email_is_verified = True
            user.save()
            print("===========here---2==========")

            '''
            This function is responsible for triggering a notification to a user (driver) to verify their email address using Django Channels.
            It's likely part of a larger system for handling user interactions in real-time. 
            '''
            send_mail_verification_update_to_driver(user) # ??? (I Don't no why!)
            print("===========here---3==========")
            
            # return Response(
            #     data=get_user_details(user),
            #     status=status.HTTP_200_OK,
            # )
            
            return Response(
                data={
                    "user": get_user_details(user),
                    "message":"Your email has been successfully verified."
                },
                status=status.HTTP_200_OK,
            )
            
            
            
        return Response(
            {"message": "Token is Expired"}, status=status.HTTP_400_BAD_REQUEST
        )










class ValidateTokenFromUrl(APIView):
    def get(self, request, user_id, token):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            token = VerificationTokens.objects.get(user=user, token=token)
        except VerificationTokens.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if token.is_valid:
            token.delete()
            user.is_active = True
            user.email_is_verified = True
            user.save()
            return Response(
                {
                    "message": "Token is valid, You have successfully completed your registration"
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"message": "Token is Expired"}, status=status.HTTP_400_BAD_REQUEST
        )


class ResendToken(APIView):
    def post(self, request):
        try:
            user_id = request.data["id"]
        except KeyError:
            return Response(
                {"message": "Id is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = get_object_or_404(User, id=user_id)
        except User.DoesNotExist:
            return Response(
                {"Report": "Requested user does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        VerificationTokens.objects.filter(user=user).delete()
        send_email_verification_token(user)
        return Response(
            {"message": "Token has been sent to your email"}, status=status.HTTP_200_OK
        )


#  This function is used to create OTP in purpose of reseting password
class ResetPasswordAPIView(APIView):
    def post(self, request):
        print("================ResetPasswordAPIView Calling ===============")
        
        
            
        try:
            serializer = ResendOtpSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            errors = [str(detail) for detail in e.detail]
            error_data = {
                "data": request.data,
                "message": "field_validation_error",
                "errors": errors
            }
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)


                    

        try:
            user = User.objects.get(
                email=serializer.validated_data["email"],
                is_active=True,
                service=serializer.validated_data["service"],
            )
        except User.DoesNotExist:
            return Response(
                {"Report": "Requested user does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        
        
        try:
            email = request.data["email"]
        except KeyError:
            return Response(
                {"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )
            
        try:
            service = request.data["service"]
        except KeyError:
            return Response(
                {"message": "service is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        
            
        if user:
            # Generating New OTP
            otp = generate_otp()

            # Deleting ALL previous OTPs
            VerificationOTP.objects.filter(user_data=user).delete()
            # Saving New OTP to DB
            VerificationOTP.objects.create(user_data=user, otp=otp)
            
            # subject = "New OTP arrived"
            # message = f"Your new password reset OTP is: " + otp
            # send_mail(email, subject, message)

            
            code = otp
            payload = {"recipient_list": [email], "code": code, "mail_type": "password reset"}
            send_mail(payload)
            
            response_data = {
                "email": email,
                "service": service,
                "message": "New password reset token has been sent to your email",
            }
            return Response(response_data, status=status.HTTP_200_OK)
        
        


class ResetPasswordV2(APIView):
    def post(self, request):
        print("ResetPasswordV2==========Calling")
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # print("serializer.validated_data["service"]")
        try:
            user = User.objects.get(
                email=serializer.validated_data["email"],
                is_active=True,
                service=serializer.validated_data["service"],
            )
        except User.DoesNotExist:
            return Response(
                {"error_msg": "Requested user does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        print("here-----------")
        VerificationTokens.objects.filter(
            user=user, token_type=TokenTypes.password_reset
        ).delete()
        
        
        send_reset_password_code(user, serializer.validated_data["method"])
        
        print("----ResetPasswordV2---Mail successfully send ")
        return Response(status=status.HTTP_200_OK)






# Validating OTP for password reset ----Update code =----RM
class ValidateResetPasswordOTP(APIView):
    def post(self, request):
        print("=========== ValidateResetPasswordOTP calling ===========")
        
        try:
            otp = request.data["otp"]  # Corrected key: "OTP"
            email = request.data["email"]  # Corrected key: "email"
            service = request.data["service"]  # Corrected key: "service"
            
        except KeyError as e:
            # Missing one or more required fields
            missing_fields = []
            if "email" not in request.data:
                missing_fields.append("email")
            if "otp" not in request.data:
                missing_fields.append("otp")
            if "service" not in request.data:
                missing_fields.append("service")
            return Response(
                {"message": f"The following fields are required: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        user = None
        try:
            user = get_object_or_404(User, email=email, is_active=True, service=service)

        except:
            return Response(
                {"error_msg": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )

        
        try:
            VerificationOTP_obj = get_object_or_404(VerificationOTP, user_data=user, otp=otp)
            created = VerificationOTP_obj.creation_time
            
        except:
            return Response(
                {"error_msg": "OTP is invalid"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        
        if VerificationOTP_obj:
            code = VerificationOTP_obj.code
            response_data = {
                "message": "Your OTP Successfully Verified",
                "code": code,
             }
            return Response(response_data,status=status.HTTP_200_OK)
        
        else:
            response_data = {
                "message": "Validation error",
                "errors": "OTP time expired."
            }
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

                
        

        
        
        
    





class ValidateResetPasswordOTPV2(APIView):
    def post(self, request):
        print("======= ValidateResetPasswordOTPV2 Calling 1=========")
        serializer = ValidateResetPasswordOtpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        
        try:
            user = User.objects.get(
                email=serializer.validated_data["email"],
                is_active=True,
                service=serializer.validated_data["service"],
            )
        except User.DoesNotExist:
            return Response(
                {"error_msg": "Invalid email"}, status=status.HTTP_400_BAD_REQUEST
            )
            
        # print("here-----------")
        # VerificationTokens.objects.filter(
        #     user=user, token_type=TokenTypes.password_reset
        # ).delete()
        
        
        try:
            otp = VerificationTokens.objects.get(
                user=user, token=serializer.validated_data["otp"]
            )
        except VerificationTokens.DoesNotExist:
            return Response(
                {"error_msg": "Invalid otp"}, status=status.HTTP_400_BAD_REQUEST
            )
        if otp.is_valid:
            out = {"unique_code": str(otp.id)}
            return Response(out, status=status.HTTP_200_OK)
        out = {"error_msg": "OTP Expired!"}
        print("OTP updated")
        return Response(out, status=status.HTTP_400_BAD_REQUEST)





# Resetting password reset OTP
class ResendOTP(APIView):
    def post(self, request):
        print("=============ResendOTP==== Calling ===========")
        
            
        try:
            serializer = ResendOtpSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
        except serializers.ValidationError as e:
            errors = [str(detail) for detail in e.detail]
            error_data = {
                "data": request.data,
                "message": "field_validation_error",
                "errors": errors
            }
            return Response(error_data, status=status.HTTP_400_BAD_REQUEST)
            
            
        print("here-------1----***///")
        try:
            user = User.objects.get(
                email=serializer.validated_data["email"],
                is_active=True,
                service=serializer.validated_data["service"],
            )
        except User.DoesNotExist:
            return Response(
                {"Report": "Requested user does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        print("here-------2----***///")
        
        VerificationTokens.objects.filter(
            user=user, token_type=TokenTypes.password_reset
        ).delete()
        
  
        
        try:
            email = request.data["email"]
        except KeyError:
            return Response(
                {"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            service = request.data["service"]
        except KeyError:
            return Response(
                {"message": "service is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        
        
        
            
        send_reset_password_code(user, serializer.validated_data["method"])
        
        print("----ResetPasswordV2--resend-Mail successfully send ")
        return Response(status=status.HTTP_200_OK)

            
        






# API FOR CHANGING PASSWORD ============
class ChangePassword(APIView):
    # permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        print("============ChangePassword is calling =======")
        try:
            email = request.data["email"]
            password = request.data["password"]
            code = request.data["code"] #String
            service = request.data["service"]
            
        except KeyError as e:
            # Missing one or more required fields
            missing_fields = []
            if "email" not in request.data:
                missing_fields.append("email")
            if "password" not in request.data:
                missing_fields.append("password")
            if "code" not in request.data:
                missing_fields.append("code")
            if "service" not in request.data:
                missing_fields.append("service")
            return Response(
                {"message": f"The following fields are required: {', '.join(missing_fields)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # try:
        #     email = request.data["email"]
        # except KeyError:
        #     return Response(
        #         {"message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST
        #     )
            
            
        try:
            user = get_object_or_404(User, email=email, service=service, is_active=True)
            otp = get_object_or_404(VerificationOTP, user_data=user)
            otp_code = otp.code
            otp_code = str(otp_code)
            
            
        except Exception as e:
            return Response(
                {"Report": "Requested user does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )
            
        if not password_validator(value=request.data.get("password")):
            return Response(
                {
                    "Report": "Password must be 8 characters long and must contain at least one uppercase, one lowercase, and one digit !"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # if otp.is_used and otp.is_valid:
        if otp_code == code:
            user.set_password(password)
            user.save()
            otp.delete()
            
            response_data = {
                "user": user
            }

            response_data = {
                    "message": "Password has been changed Successfully"
                }
            return Response(response_data,status=status.HTTP_200_OK)
        
        

        else:
            return Response(
                {"message": "OTP Authentication failed or expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )





class ChangePasswordV2(APIView):
    def post(self, request):
        print("--------ChangePasswordV2---------")
        
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = get_object_or_404(
            User,
            email=serializer.validated_data["email"],
            is_active=True,
            service=serializer.validated_data["service"],
        )
        try:
            otp = VerificationTokens.objects.get(id=serializer.validated_data["code"])
        except VerificationTokens.DoesNotExist:
            return Response(
                status=status.HTTP_400_BAD_REQUEST, data={"error_msg": "Invalid code"}
            )
        if otp.code_is_valid():
            user.set_password(serializer.validated_data["password"])
            user.password_has_changed = True
            user.save()
            otp.delete()
            return Response(
                status=status.HTTP_200_OK, data={"message": "Password has been changed"}
            )
        return Response({"error_msg": "code is expired"})


class EmailExists(APIView):
    """
    Updated API code for CheckEmailIfExists
    """

    def post(self, request):
        serializer = EmailExistsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        out = {
            "email_exists": User.objects.filter(
                email=serializer.validated_data["email"],
                email_is_verified=True,
                service=serializer.validated_data["service"],
            ).exists()
        }
        return Response(out, status=status.HTTP_200_OK)


class PhoneExists(APIView):
    """
    Updated API code for CheckPhoneIfExists
    """

    def post(self, request):
        serializer = PhoneExistsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        out = {
            "phone_exists": User.objects.filter(
                phone=serializer.validated_data["phone"],
                phone_is_verified=True,
                service=serializer.validated_data["service"],
            ).exists()
        }
        return Response(out, status=status.HTTP_200_OK)


class UserProfileAPIView(APIView):
    """
    Returns user profile
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CheckIfUserIsDriver(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = {"is_driver": is_driver(self.request.user)}
        return Response(data, status=status.HTTP_200_OK)


class OrganizationVerifiesDriver(APIView):
    def post(self, request, driver_id):
        serializer = AcceptDenySerializer(request.data)
        serializer.is_valid(raise_exception=True)
        driver = get_object_or_404(Driver, id=driver_id)
        driver.verified_by_organization = True
        driver.save()
        return Response(status=status.HTTP_200_OK)


class DriversVerificationStatus(APIView):
    permission_classes = [IsDriver]

    def get(self, request):
        driver = self.request.user.driver
        data = {"status": driver.status}
        return Response(data, status=status.HTTP_200_OK)


# class OrganizationRegistersDriver(CreateAPIView):
#     permission_classes = [IsOrganization]
#     serializer_class = DriverRegistrationOfOrganizationSerializer

#     def perform_create(self, serializer):
#         serializer.save(organization=self.request.user.organization)


class AcceptOrDenyVehicleAssignRequest(APIView):
    """
    Accepts or Denies Vehicle Assign Request
    """

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        pass
        # try:
        #     driver = Driver.objects.get(user=request.user)
        #     vehicle_assign_request = VehicleAssignWaitingList.objects.get(driver=driver)

        # except Driver.DoesNotExist:
        #     return Response(
        #         {"message": "You Do Not Have Any Request"},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )
        # try:
        #     if (
        #         request.data["status"] == "accepted"
        #         or request.data["status"] == "rejected"
        #     ):
        #         vehicle_assign_request.status = request.data["status"]
        #         vehicle_assign_request.save()

        #         return Response(
        #             {"message": "Request Updated"}, status=status.HTTP_200_OK
        #         )
        #     else:
        #         return Response(
        #             {"message": "1. Invalid Status"}, status=status.HTTP_400_BAD_REQUEST
        #         )
        # except Exception as e:
        #     return Response(
        #         {"message": "Invalid Status"}, status=status.HTTP_400_BAD_REQUEST
        #     )


class GetAllVehicles(ListAPIView):
    """
    Returns all vehicles
    """

    permission_classes = [permissions.IsAuthenticated]
    queryset = Vehicle.objects.all()
    serializer_class = VehicleSerializer
    pagination_class = LimitOffsetPagination



class GetDriversTripList(APIView):
    """
    Returns all trips for a driver
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        pass
        # try:
        #     driver = Driver.objects.get(user=request.user)
        #     trips = VehicleAssignWaitingList.objects.filter(driver=driver)
        #     serializer = VehicleAssignWaitingListSerializer(trips, many=True)
        #     return Response(serializer.data, status=status.HTTP_200_OK)
        # except Driver.DoesNotExist:
        #     return Response(
        #         {"message": "Driver not found"}, status=status.HTTP_404_NOT_FOUND
        #     )


class ListOfOnlineUsers(APIView):
    def get(self, request):
        all_users = User.objects.filter(is_active=True)
        users = [user for user in all_users if user.online]
        return Response(
            OnlineUsersSerializer(users, many=True).data, status=status.HTTP_200_OK
        )


# class ListCreateAddress(ListCreateAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = SavedAddressSerializer

#     def get_queryset(self):
#         return self.request.user.savedaddress_set.filter(deleted=False)

#     def perform_create(self, serializer):
#         serializer.save(user=self.request.user)


# class GetUpdateAddress(RetrieveUpdateAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = SavedAddressSerializer

#     def get_object(self):
#         id = self.kwargs["address_id"]
#         return get_object_or_404(
#             SavedAddress, id=id, deleted=False, user=self.request.user
#         )


class DeleteAddress(APIView):
    """
    Deletes saved addresses of users. Changes deleted to True instead of deleting the object
    """

    def get(self, request, address_id):
        pass
        # obj = get_object_or_404(
        #     SavedAddress, id=address_id, deleted=False, user=self.request.user
        # )
        # obj.deleted = True
        # obj.save()
        # return Response(status=status.HTTP_200_OK)


# class ClientInfo(RetrieveAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = ClientInfoSerailizer

#     def get_object(self):
#         return self.request.user


class UpdateUserInfo(UpdateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UserUpdateSerializer

    def get_object(self):
        return self.request.user


# class RegisterSource(viewsets.ModelViewSet):
#     """
#     API for registering source
#     """

#     queryset = Source.objects.all()
#     serializer_class = SourceSerializer


# class DriverInfoAPIView(RetrieveAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = DriverProfileSerializer

#     def get_object(self):
#         return get_object_or_404(Driver, id=self.request.user.driver.id)


# class UpdateDriverProfile(APIView):
#     permission_classes = [permissions.IsAuthenticated]
#
#     def post(self, request):
#         driver = get_object_or_404(Driver, id=self.request.user.driver.id)
#         # Make sure all the keys are same as object property names
#         files = {
#             "pp_size_driver_image": request.data.get("profile_picture", False),
#             "driving_license_front_image": request.data.get("license_front", False),
#             "driving_license_back_image": request.data.get("license_back", False),
#         }
#         # Check any of the file is missing
#         for key, value in files.items():
#             if not value:
#                 return Response(
#                     {"message": f"{key} is missing"}, status=status.HTTP_400_BAD_REQUEST
#                 )
#
#         upload_file_to_firebase(files, driver)
#
#         return Response(status=status.HTTP_200_OK)


class CheckVehicleAPIView(APIView):
    def get(self, request, *args, **kwargs):
        # get id from query params
        user_id = self.kwargs.get("id", None)
        if not user_id:
            return Response(
                {"message": "Id is required"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {"message": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST
            )
        try:
            driver = Driver.objects.get(user=user)
        except Driver.DoesNotExist:
            return Response(
                {"message": "You are not a driver"}, status=status.HTTP_400_BAD_REQUEST
            )

        # access_token = get_access_token()
        # print(access_token)

        if hasattr(driver, "vehicle"):
            return Response(
                {"has_vehicle": True},
                status=status.HTTP_200_OK,
            )
        # get access token

        return Response({"has_vehicle": False}, status=status.HTTP_200_OK)



# class GetManufacturer(ListAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = VehicleModelsSerializer
#     pagination_class = None

#     def get_queryset(self):
#         return Manufacturer.objects.all()





# class GetModels(ListAPIView):
#     permission_classes = [permissions.IsAuthenticated]
#     serializer_class = VehicleModelsSerializer
#     pagination_class = None

#     def get_queryset(self):
#         return Manufacturer.objects.all()





class GetTokenForWebSocket(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        payload = {
            "user_id": str(self.request.user.id),
            "token_type": "websocket",
            "exp": timezone.now() + datetime.timedelta(minutes=5),
        }
        token = jwt.encode(payload=payload, key=settings.SECRET_KEY, algorithm="HS256")
        return Response({"token": token}, status=status.HTTP_200_OK)


# class HasVehicleView(APIView):
#     permission_classes = [IsDriver]

#     def get(self, request):
#         return Response(
#             {"has_vehicle": Vehicle.objects.filter(owner=request.user.driver).exists()},
#             status=status.HTTP_200_OK,
#         )


from django.db import DatabaseError
class HasVehicleView(APIView):
    permission_classes = [IsDriver]

    def get(self, request):
        try:
            # Check if the user has a vehicle
            has_vehicle = Vehicle.objects.filter(owner=request.user.driver).exists()
            return Response({"has_vehicle": has_vehicle}, status=status.HTTP_200_OK)
        
        except AttributeError:
            # Handle cases where `request.user` or `request.user.driver` does not exist
            return Response(
                {"error": "Driver profile not found for the authenticated user."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        except DatabaseError:
            # Handle database-related errors
            return Response(
                {"error": "A database error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        except Exception as e:
            # Handle any other unforeseen exceptions
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )






# Send verification Mail ----------------
class SendVerificationMail(APIView):
    # permission_classes = [permissions.IsAuthenticated]
    serializer_class = SendMailVerificationSerializer

    def post(self, request):
        print("==== SendVerificationMail Calling======")
        if request.user.email_is_verified:
            raise PermissionDenied("Email is already verified")
        
        serializer = SendMailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if User.objects.filter(
            email=serializer.validated_data["email"], email_is_verified=True, service=""
        ).exists():
            raise serializers.ValidationError("email already exists")
        if serializer.validated_data["email"]:
            if request.user.email != serializer.data["email"]:
                request.user.email = serializer.data["email"]
                request.user.save()
                
        # Send Mail
        send_email_verification_token(request.user)
        return Response(status=status.HTTP_200_OK, data={"message": "Email sent"})





class VehicleTypesListView(APIView):
    def get(self, request):
        pass
        # vehicle_types_list = [choice for choice, _ in VehicleTypes.choices]
        # return Response(vehicle_types_list, status=status.HTTP_200_OK)


# class GetUpdateNotificationSettingsView(RetrieveUpdateAPIView):
#     serializer_class = NotificationSettingsSerializer
#     permission_classes = [IsAuthenticated]

#     def get_object(self):
#         obj, _ = NotificationSettings.objects.get_or_create(user=self.request.user)
#         return obj


class ChangePhoneNumber(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PhoneNumberSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.driver:
            try:
                _ = User.objects.get(
                    phone=serializer.validated_data["phone_number"],
                    phone_is_verified=True,
                    service="",
                )
                raise serializers.ValidationError(
                    {"phone_number": ["Phone already exists"]}
                )
            except User.DoesNotExist:
                pass
        else:
            try:
                _ = User.objects.get(
                    phone=serializer.validated_data["phone_number"],
                    phone_is_verified=True,
                    service=request.user.service,
                )
                raise serializers.ValidationError(
                    {"phone_number": ["Phone already exists"]}
                )
            except User.DoesNotExist:
                pass

        send_phone_verification_sms(
            phone_number=serializer.validated_data["phone_number"]
        )
        PhoneEmailChangeState.objects.filter(user=self.request.user).delete()
        PhoneEmailChangeState.objects.create(
            user=self.request.user, new_number=serializer.validated_data["phone_number"]
        )
        return Response(status=status.HTTP_200_OK)


class ChangeEmail(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if request.user.driver:
            try:
                _ = User.objects.get(
                    email=serializer.validated_data["email"],
                    phone_is_verified=True,
                    service="",
                )
                raise serializers.ValidationError({"email": ["Email already exists"]})
            except User.DoesNotExist:
                pass
        else:
            try:
                _ = User.objects.get(
                    email=serializer.validated_data["email"],
                    phone_is_verified=True,
                    service=request.user.service,
                )
                raise serializers.ValidationError({"email": ["Email already exists"]})
            except User.DoesNotExist:
                pass
        send_email_verification_token(
            self.request.user, serializer.validated_data["email"]
        )
        PhoneEmailChangeState.objects.filter(user=self.request.user).delete()
        PhoneEmailChangeState.objects.create(
            user=self.request.user, new_email=serializer.validated_data["email"]
        )
        return Response(status=status.HTTP_200_OK)


# class ChangeNamePictureRequestView(CreateAPIView):
#     permission_classes = [IsDriver]
#     serializer_class = NamePictureChangeStateSerializer

#     def perform_create(self, serializer):
#         NamePictureChangeState.objects.filter(driver=self.request.user.driver).delete()
#         serializer.save(driver=self.request.user.driver)


# class VerificationStatusView(APIView):
#     permission_classes = [IsDriver]

#     def get(self, request):
#         data = {"driver_verification_status": self.request.user.driver.status}
#         if self.request.user.driver.vehicle:
#             data[
#                 "vehicle_verification_status"
#             ] = self.request.user.driver.vehicle.status
#         else:
#             data["vehicle_verification_status"] = ""
#         return Response(status=status.HTTP_200_OK, data=data)






# # ====================RM==========================
# class ListCreateDriverDocumentsExpiredDateView(APIView):
#     permission_classes = [IsAuthenticated]
#     pagination_class = CustomPageNumberPagination  
    
#     def get(self, request):
#         documents = DriverDocument.objects.all()
        
#         # Use the custom paginator
#         paginator = self.pagination_class()
#         paginated_documents = paginator.paginate_queryset(documents, request)
        
#         # Serialize the paginated queryset
#         serializer = DriverDocumentsExpiredDateSerializer(paginated_documents, many=True)
        
#         # Return a paginated response
#         return paginator.get_paginated_response(serializer.data)
    
    
        
    
#     def post(self, request):
#         serializer = DriverDocumentsExpiredDateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(status=status.HTTP_200_OK, data={"message": "Documents expired date created successfully"}) 
    
    
    

    
     
# class UpdateDeleteDriverDocumentsExpiredDateView(APIView):
#     permissions_classes = [IsAuthenticated]
    
#     def get_object(self):
#         return get_object_or_404(DriverDocument, id=self.kwargs["id"])
    
#     def get(self, request, id):
#         document = self.get_object()
#         serializer = DriverDocumentsExpiredDateSerializer(document)
#         return Response(serializer.data, status=status.HTTP_200_OK)
    
#     def patch(self, request, id):
#         document = self.get_object()
#         serializer = DriverDocumentsExpiredDateSerializer(document, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
        
#         serializer.save()
        
#         # Check if expiration dates are being updated
#         if 'driving_license_front_image_expired_date' in request.data:
#             if document.driving_license_front_image_status == "pending" and document.driving_license_front_image_expired_date <= serializer.validated_data['driving_license_front_image_expired_date']:
#                 document.driving_license_front_image_status = "valid"                
#         if 'driving_license_back_image_expired_date' in request.data:
#             if document.driving_license_back_image_status == "pending" and document.driving_license_back_image_expired_date <= serializer.validated_data['driving_license_back_image_expired_date']:
#                 document.driving_license_back_image_status = "valid"                

#         if 'national_insurance_expired_date' in request.data:
#             if document.national_insurance_status == "pending" and document.national_insurance_expired_date <= serializer.validated_data['national_insurance_expired_date']:
#                 document.national_insurance_status = "valid"

#         if 'criminal_record_book_expired_date' in request.data:
#             if document.criminal_record_book_status == "pending" and document.criminal_record_book_expired_date <= serializer.validated_data['criminal_record_book_expired_date']:
#                 document.criminal_record_book_status = "valid"
        
#         if 'dbl_file_expired_date' in request.data:
#             if document.dbl_file_status == "pending" and document.dbl_file_expired_date <= serializer.validated_data['dbl_file_expired_date']:
#                 document.dbl_file_status = "valid"
        
#         if 'pco_license_file_expired_date' in request.data:
#             if document.pco_license_file_status == "pending" and document.pco_license_file_expired_date <= serializer.validated_data['pco_license_file_expired_date']:
#                 document.pco_license_file_status = "valid"  
                
#         if 'driving_license_front_image_status' and 'driving_license_front_image_issue_reason' in request.data:
#             if document.driving_license_front_image_status == "pending" and request.data['driving_license_front_image_status'] == "issue":
#                 document.driving_license_front_image_status = "issue"
#                 document.driving_license_front_image_issue_reason = request.data['driving_license_front_image_issue_reason']
                
#         if 'driving_license_back_image_status' and 'driving_license_back_image_issue_reason' in request.data:
#             if document.driving_license_back_image_status == "pending" and request.data['driving_license_back_image_status'] == "issue":
#                 document.driving_license_back_image_status = "issue"
#                 document.driving_license_back_image_issue_reason = request.data['driving_license_back_image_issue_reason']
        
#         if 'national_insurance_status' and 'national_insurance_issue_reason' in request.data:
#             if document.national_insurance_status == "pending" and request.data['national_insurance_status'] == "issue":
#                 document.national_insurance_status = "issue"
#                 document.national_insurance_issue_reason = request.data['national_insurance_issue_reason']             
        
#         if  'criminal_record_book_status' and 'criminal_record_book_issue_reason' in request.data:
#             if document.criminal_record_book_status == "pending" and request.data['criminal_record_book_status'] == "issue":               
#                 document.criminal_record_book_status = "issue"
#                 document.criminal_record_book_issue_reason = request.data['criminal_record_book_issue_reason']
        
#         if 'dbl_file_status' and 'dbl_file_issue_reason' in request.data:
#             if document.dbl_file_status == "pending" and request.data['dbl_file_status'] == "issue":
#                 document.dbl_file_status = "issue"
#                 document.dbl_file_issue_reason = request.data['dbl_file_issue_reason']
        
#         if 'pco_license_file_status' and 'pco_license_file_issue_reason' in request.data:
#             if document.pco_license_file_status == "pending" and request.data['pco_license_file_status'] == "issue":
#                 document.pco_license_file_status = "issue"
#                 document.pco_license_file_issue_reason = request.data['pco_license_file_issue_reason']           
                      
        
#         document.save()
        
#         return Response(status=status.HTTP_200_OK, data={"message": "Documents expired date updated successfully"})
    
#     def delete(self, request, id):
#         document = self.get_object()
#         document.delete()
#         return Response(status=status.HTTP_200_OK, data={"message": "Documents expired date deleted successfully"})             

# # Driver Documents View
# class DriverDocumentsView(APIView):
#     permission_classes = [IsDriver]
    
#     parser_classes = (MultiPartParser, FormParser)

#     def get(self, request):
#         driver = request.user.driver
#         documents = DriverDocument.objects.filter(driver=driver).first()
        
#         if documents:
#             today = datetime.date.today()

#             # Update driving_license_front_image_status
#             if documents.driving_license_front_image_status == "valid":
#                 expiration_date = documents.driving_license_front_image_expired_date
#                 one_month_before = expiration_date - datetime.timedelta(days=30)               

#                 if today >= one_month_before:
#                     documents.driving_license_front_image_status = "renewal"
#                 else: documents.driving_license_front_image_status = "valid"
            
#             if documents.driving_license_front_image_status == "renewal":
#                 expiration_date = documents.driving_license_front_image_expired_date
#                 one_month_after = expiration_date +  datetime.timedelta(days=30)

#                 if today >= one_month_after:
#                     documents.driving_license_front_image_status = "expired"
#                 else: documents.driving_license_front_image_status = "renewal"

#             # Update driving_license_back_image_status
#             if documents.driving_license_back_image_status == "valid":
#                 expiration_date = documents.driving_license_back_image_expired_date
#                 one_month_before = expiration_date - datetime.timedelta(days=30)
                
                
                
#                 print(today, one_month_before, expiration_date)

#                 if today >= one_month_before:
#                     documents.driving_license_back_image_status = "renewal"
#                 else: documents.driving_license_back_image_status = "valid"
                
#             if documents.driving_license_back_image_status == "renewal":
#                 expiration_date = documents.driving_license_back_image_expired_date
#                 one_month_after = expiration_date + datetime.timedelta(days=30)
                
#                 if today >= one_month_after:
#                     documents.driving_license_back_image_status = "expired"
#                 else: documents.driving_license_back_image_status = "renewal"

#             # Update national_insurance_status
#             if documents.national_insurance_status == "valid":
#                 expiration_date = documents.national_insurance_expired_date
#                 one_month_before = expiration_date - datetime.timedelta(days=30)

#                 if today >= one_month_before:
#                     documents.national_insurance_status = "renewal"
#                 else: documents.national_insurance_status = "valid"
#             if documents.national_insurance_status == "renewal":
#                 expiration_date = documents.national_insurance_expired_date
#                 one_month_after = expiration_date + datetime.timedelta(days=30)
                
#                 if today >= one_month_after:
#                     documents.national_insurance_status = "expired"
#                 else: documents.national_insurance_status = "renewal"

#             # Update criminal_record_book_status
#             if documents.criminal_record_book_status == "valid":
#                 expiration_date = documents.criminal_record_book_expired_date
#                 one_month_before = expiration_date - datetime.timedelta(days=30)               

#                 if today >= one_month_before:
#                     documents.criminal_record_book_status = "renewal"
#                 else: documents.criminal_record_book_status = "valid"
            
#             if documents.criminal_record_book_status == "renewal":
#                 expiration_date = documents.criminal_record_book_expired_date
#                 one_month_after = expiration_date + datetime.timedelta(days=30)

#                 if today >= one_month_after:
#                     documents.criminal_record_book_status = "expired"
#                 else: documents.criminal_record_book_status = "renewal"

#             # Update dbl_file_status
#             if documents.dbl_file_status == "valid":
#                 expiration_date = documents.dbl_file_expired_date
#                 one_month_before = expiration_date - datetime.timedelta(days=30)

#                 if today >= one_month_before:
#                     documents.dbl_file_status = "renewal"
#                 else: documents.dbl_file_status = "valid"
            
#             if documents.dbl_file_status == "renewal":
#                 expiration_date = documents.dbl_file_expired_date
#                 one_month_after = expiration_date + datetime.timedelta(days=30)

#                 if today >= one_month_after:
#                     documents.dbl_file_status = "expired"
#                 else: documents.dbl_file_status = "renewal"

#             # Update pco_license_file_status
#             if documents.pco_license_file_status == "valid":
#                 expiration_date = documents.pco_license_file_expired_date
#                 one_month_before = expiration_date - datetime.timedelta(days=30)

#                 if today >= one_month_before:
#                     documents.pco_license_file_status = "renewal"
#                 else: documents.pco_license_file_status = "valid"
            
#             if documents.pco_license_file_status == "renewal":
#                 expiration_date = documents.pco_license_file_expired_date
#                 one_month_after = expiration_date + datetime.timedelta(days=30)

#                 if today >= one_month_after:
#                     documents.pco_license_file_status = "expired"
#                 else: documents.pco_license_file_status = "renewal"

#             # Save the updated document status
#             documents.save()

#         data = {
#             "driving_license_front_image": {
#                 "status": documents.driving_license_front_image_status if documents else None,
#                 "expired_date": documents.driving_license_front_image_expired_date.strftime('%Y-%m-%d') if documents and documents.driving_license_front_image_expired_date else None,
#                 "file": driver.driving_license_front_image.url if driver and driver.driving_license_front_image else None,
#                 "is_editable": True if documents.driving_license_front_image_status not in ["valid", "pending", "expired"] else False if documents else None,
#                 "issue_reason": documents.driving_license_front_image_issue_reason if documents else ""
#             },
#             "driving_license_back_image": {
#                 "status": documents.driving_license_back_image_status if documents else None,
#                 "expired_date": documents.driving_license_back_image_expired_date.strftime('%Y-%m-%d') if documents and documents.driving_license_back_image_expired_date else None,
#                 "file": driver.driving_license_back_image.url if driver and driver.driving_license_back_image else None,
#                 "is_editable": True if documents.driving_license_back_image_status not in ["valid", "pending", "expired"] else False if documents else None,
#                 "issue_reason": documents.driving_license_back_image_issue_reason if documents else ""
#             },
#             "national_insurance": {
#                 "status" : documents.national_insurance_status if documents else None,
#                 "expired_date": documents.national_insurance_expired_date.strftime('%Y-%m-%d') if documents and documents.national_insurance_expired_date else None,
#                 "file": driver.national_insurance.url if driver and driver.national_insurance else None,
#                 "is_editable": True if documents.national_insurance_status not in ["valid", "pending", "expired"] else False if documents else None,
#                 "issue_reason": documents.national_insurance_issue_reason if documents else ""
#             },
#             "criminal_record_book": {
#                 "status": documents.criminal_record_book_status if documents else None,
#                 "expired_date": documents.criminal_record_book_expired_date.strftime('%Y-%m-%d') if documents and documents.criminal_record_book_expired_date else None,
#                 "file": driver.criminal_record_book.url if driver and driver.criminal_record_book else None,
#                 "is_editable": True if documents.criminal_record_book_status not in ["valid", "pending", "expired"] else False if documents else None,
#                 "issue_reason": documents.criminal_record_book_issue_reason if documents else ""
#             },
#             "dbl_file": {
#                 "status": documents.dbl_file_status if documents else None,
#                 "expired_date": documents.dbl_file_expired_date.strftime('%Y-%m-%d') if documents and documents.dbl_file_expired_date else None,
#                 "file": driver.dbl_file.url if driver and driver.dbl_file else None,
#                 "is_editable": True if documents.dbl_file_status not in ["valid", "pending", "expired"] else False if documents else None,
#                 "issue_reason": documents.dbl_file_issue_reason if documents else ""
#             },
#             "pco_license_file": {
#                 "status": documents.pco_license_file_status if documents else None,
#                 "expired_date": documents.pco_license_file_expired_date.strftime('%Y-%m-%d') if documents and documents.pco_license_file_expired_date else None,
#                 "file": driver.pco_license_file.url if driver and driver.pco_license_file else None,
#                 "is_editable": True if documents.pco_license_file_status not in ["valid", "pending", "expired"] else False if documents else None,
#                 "issue_reason": documents.pco_license_file_issue_reason if documents else ""
#             }
#         }

#         return Response(data, status=status.HTTP_200_OK)
    
#     def post(self, request):
#         driver = request.user.driver
#         documents = DriverDocument.objects.filter(driver=driver).first()
#         if not documents:
#             return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Driver documents not found."})

#         # Assuming the request data contains information about which document to update and the new file
#         document_type = request.data.get('document_type')
#         new_file = request.data.get('new_file')
        

#         # Check if the requested document type is valid and is editable
#         if document_type not in ['driving_license_front_image', 'driving_license_back_image', 'national_insurance', 'criminal_record_book', 'dbl_file', 'pco_license_file']:
#             return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Invalid document type."})
        
#         is_editable_field = f"{document_type}_status"
#         is_editable_issue_reason = f"{document_type}_issue_reason"
        
#         current_status = getattr(documents, is_editable_field, None)
#         if current_status == 'renewal':
#             setattr(documents, is_editable_field, 'pending')
#         if current_status == 'issue':
#             setattr(documents, is_editable_field, 'pending')
#             setattr(documents, is_editable_issue_reason, '')
#         if current_status == 'expired':
#             return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Document is expired."})
            

#         # Update the document file and status
#         file_field = document_type
#         setattr(driver, file_field, new_file)
#         # setattr(documents, is_editable_field, 'waiting')
#         driver.save()
#         documents.save()
        

#         return Response({"is_editable": is_editable_field},  status=status.HTTP_200_OK)

# class ListCreateVehicleDocumentsExpiredDateView(APIView):
#     permissions_classes = [IsAuthenticated]
#     pagination_class = CustomPageNumberPagination  
    
    
#     def get(self, request):
#         documents = VehicleDocument.objects.all()
    
#         # Use the custom paginator
#         paginator = self.pagination_class()
#         paginated_documents = paginator.paginate_queryset(documents, request)
        
#         # Serialize the paginated queryset
#         serializer = VehicleDocumentsExpiredDateSerializer(paginated_documents, many=True)
        
#         # Return a paginated response
#         return paginator.get_paginated_response(serializer.data)
    
    
#     def post(self, request):
#         serializer = VehicleDocumentsExpiredDateSerializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(status=status.HTTP_200_OK, data={"message": "Documents expired date created successfully"})



# class UpdateDeleteVehicleDocumentsExpiredDateView(APIView):
#     permissions_classes = [IsAuthenticated]
    
#     def get_object(self):
#         return get_object_or_404(VehicleDocument, id=self.kwargs["id"])
    
#     def get(self, request, id):
#         document = self.get_object()
#         serializer = VehicleDocumentsExpiredDateSerializer(document)
#         return Response(serializer.data, status=status.HTTP_200_OK)
    
#     def patch(self, request, id):
#         document = self.get_object()
#         serializer = VehicleDocumentsExpiredDateSerializer(document, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
        
#         # Check if expiration dates are being updated
#         if 'bluebook_expired_date' in request.data:
#             if document.bluebook_status == "pending" and document.bluebook_expired_date <= serializer.validated_data['bluebook_expired_date']:
#                 document.bluebook_status = "valid"
        
#         if 'mot_expired_date' in request.data:
#             if document.mot_status == "pending" and document.mot_expired_date <= serializer.validated_data['mot_expired_date']:
#                 document.mot_status = "valid"
        
#         if 'vehicle_registration_file_expired_date' in request.data:
#             if document.vehicle_registration_file_status == "pending" and document.vehicle_registration_file_expired_date <= serializer.validated_data['vehicle_registration_file_expired_date']:
#                 document.vehicle_registration_file_status = "valid"
        
#         if 'vehicle_insurance_expired_date' in request.data:
#             if document.vehicle_insurance_status == "pending" and document.vehicle_insurance_expired_date <= serializer.validated_data['vehicle_insurance_expired_date']:
#                 document.vehicle_insurance_status = "valid"
        
#         document.save()
        
#         return Response(status=status.HTTP_200_OK, data={"message": "Documents expired date updated successfully"})
    
#     def delete(self, request, id):
#         document = self.get_object()
#         document.delete()
#         return Response(status=status.HTTP_200_OK, data={"message": "Documents expired date deleted successfully"})

# class VehicleDocumentsView(APIView):
    # permission_classes = [IsDriver]
    
    # parser_classes = (MultiPartParser, FormParser)

    # def get(self, request):
    #     driver = request.user.driver
    #     vehicle = driver.vehicle
    #     documents = VehicleDocument.objects.filter(vehicle=vehicle).first()
        
    #     if documents:
    #         today = datetime.date.today()
            
    #         # Update bluebook_status
    #         if documents.bluebook_status == "valid":
    #             expiration_date = documents.bluebook_expired_date
    #             one_month_before = expiration_date - datetime.timedelta(days=30)               

    #             if today >= one_month_before:
    #                 documents.bluebook_status = "renewal"
    #             else: documents.bluebook_status = "valid"
            
    #         if documents.bluebook_status == "renewal":
    #             expiration_date = documents.bluebook_expired_date
    #             one_month_after = expiration_date +  datetime.timedelta(days=30)

    #             if today >= one_month_after:
    #                 documents.bluebook_status = "expired"
    #             else: documents.bluebook_status = "renewal"
            
    #         # Update mot_status
    #         if documents.mot_status == "valid":
    #             expiration_date = documents.mot_expired_date
    #             one_month_before = expiration_date - datetime.timedelta(days=30)

    #             if today >= one_month_before:
    #                 documents.mot_status = "renewal"
    #             else: documents.mot_status = "valid"
                
    #         if documents.mot_status == "renewal":
    #             expiration_date = documents.mot_expired_date
    #             one_month_after = expiration_date + datetime.timedelta(days=30)
                
    #             if today >= one_month_after:
    #                 documents.mot_status = "expired"
    #             else: documents.mot_status = "renewal"
            
    #         # Update vehicle_registration_file_status
    #         if documents.vehicle_registration_file_status == "valid":
    #             expiration_date = documents.vehicle_registration_file_expired_date
    #             one_month_before = expiration_date - datetime.timedelta(days=30)

    #             if today >= one_month_before:
    #                 documents.vehicle_registration_file_status = "renewal"
    #             else: documents.vehicle_registration_file_status = "valid"
            
    #         if documents.vehicle_registration_file_status == "renewal":
    #             expiration_date = documents.vehicle_registration_file_expired_date
    #             one_month_after = expiration_date + datetime.timedelta(days=30)

    #             if today >= one_month_after:
    #                 documents.vehicle_registration_file_status = "expired"
    #             else: documents.vehicle_registration_file_status = "renewal"
            
    #         # Update vehicle_insurance_status
    #         if documents.vehicle_insurance_status == "valid":
    #             expiration_date = documents.vehicle_insurance_expired_date
    #             one_month_before = expiration_date - datetime.timedelta(days=30)

    #             if today >= one_month_before:
    #                 documents.vehicle_insurance_status = "renewal"
    #             else: documents.vehicle_insurance_status = "valid"
            
    #         if documents.vehicle_insurance_status == "renewal":
    #             expiration_date = documents.vehicle_insurance_expired_date
    #             one_month_after = expiration_date + datetime.timedelta(days=30)

    #             if today >= one_month_after:
    #                 documents.vehicle_insurance_status = "expired"
    #             else: documents.vehicle_insurance_status = "renewal"
            
    #         # Save the updated document status
    #         documents.save()        
        
    #     data = {
    #         "bluebook" : {
    #             "status": documents.bluebook_status if documents else None,
    #             "expired_date": documents.bluebook_expired_date.strftime('%Y-%m-%d') if documents and documents.bluebook_expired_date else None,
    #             "file": driver.vehicle.bluebook.url if driver.vehicle.bluebook else None,
    #             "is_editable": True if documents.bluebook_status not in ["valid", "pending", "expired"] else False if documents else None,
    #             "issue_reason": documents.bluebook_issue_reason if documents else ""
    #         },
    #         "mot": {
    #             "status": documents.mot_status if documents else None,
    #             "expired_date": documents.mot_expired_date.strftime('%Y-%m-%d') if documents and documents.mot_expired_date else None,
    #             "file": driver.vehicle.mot.url if driver.vehicle.mot else None,
    #             "is_editable": True if documents.mot_status not in ["valid", "pending", "expired"] else False if documents else None,
    #             "issue_reason": documents.mot_issue_reason if documents else ""
    #         },
    #         "vehicle_registration_file" : {
    #             "status": documents.vehicle_registration_file_status if documents else None,
    #             "expired_date": documents.vehicle_registration_file_expired_date.strftime('%Y-%m-%d') if documents and documents.vehicle_registration_file_expired_date else None,
    #             "file": driver.vehicle.vehicle_registration_file.url if driver.vehicle.vehicle_registration_file else None,
    #             "is_editable": True if documents.vehicle_registration_file_status not in ["valid", "pending", "expired"] else False if documents else None,
    #             "issue_reason": documents.vehicle_registration_file_issue_reason if documents else ""
    #         },
    #         "vehicle_insurance": {
    #             "status": documents.vehicle_insurance_status if documents else None,
    #             "expired_date": documents.vehicle_insurance_expired_date.strftime('%Y-%m-%d') if documents and documents.vehicle_insurance_expired_date else None,
    #             "file": driver.vehicle.vehicle_insurance.url if driver.vehicle.vehicle_insurance else None,
    #             "is_editable": True if documents.vehicle_insurance_status not in ["valid", "pending", "expired"] else False if documents else None,
    #             "issue_reason": documents.vehicle_insurance_issue_reason if documents else ""
    #         },
    #         "vehicle" : {
    #             "front_image": driver.vehicle.vehicle_front_image.url if driver.vehicle.vehicle_front_image else None,
    #             "back_image": driver.vehicle.vehicle_back_image.url if driver.vehicle.vehicle_back_image else None,
    #             # "left_image": driver.vehicle.vehicle_left_image.url if driver.vehicle.vehicle_left_image else None,
    #             # "right_image": driver.vehicle.vehicle_right_image.url if driver.vehicle.vehicle_right_image else None,
    #         }
    #     }
        
    #     return Response(data, status=status.HTTP_200_OK)
    
    # def post(self, request):
        driver = request.user.driver
        vehicle = driver.vehicle
        documents = VehicleDocument.objects.filter(vehicle=vehicle).first()        
        
        if not documents:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Vehicle documents not found."})
        
        # Assuming the request data contains information about which document to update and the new file
        document_type = request.data.get('document_type')
        new_file = request.data.get('new_file')
        
        # Check if the requested document type is valid and is editable
        if document_type not in ['bluebook', 'mot', 'vehicle_registration_file', 'vehicle_insurance']:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Invalid document type."})
        
        is_editable_field = f"{document_type}_status"
        is_editable_issue_reason = f"{document_type}_issue_reason"
        
        current_status = getattr(documents, is_editable_field, None)
        if current_status == 'renewal':
            setattr(documents, is_editable_field, 'pending')
        if current_status == 'issue':
            setattr(documents, is_editable_field, 'pending')
            setattr(documents, is_editable_issue_reason, '')
        if current_status == 'expired':
            return Response(status=status.HTTP_400_BAD_REQUEST, data={"message": "Document is expired."})
        
        # Update the document file and status
        file_field = document_type
        setattr(vehicle, file_field, new_file)
        # setattr(documents, is_editable_field, 'waiting')
        driver.save()
        vehicle.save()
        documents.save()
        
        return Response({"is_editable": is_editable_field},  status=status.HTTP_200_OK)