
import datetime
import json
import requests
from django.contrib import auth
from django.contrib.auth import get_user_model
from uc_back import settings
from django.utils import timezone
import jwt
from django.core.files.storage import default_storage
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.db import transaction



from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import permissions, status
from rest_framework.response import Response

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

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.exceptions import ValidationError
# from rest_framework.permissions import IsAdmin



from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt import views, serializers
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken



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
# from accounts.models import (
#     Driver,
#     DriverStatus,
#     VehicleStatus,

#     Vehicle,
#     VehicleAttachmentStatus,
#     DriverAttachmentStatus,
# )

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



from driver_app.serializers import (
    DriverDocumentSubmitReSubmitSerializer,
    VehicleDocumentSubmitReSubmitSerializer,
    VehicleDocumentDetailSerializer,
    DriverSerializer, 
    )

User = get_user_model()
today = datetime.date.today()


from accounts.serializers import (

    DriverInfoForVerificationSerializer,
    InfoForVerificationSerializer,
    
)



class VehicleRegisterView(APIView):
    permission_classes = [IsAuthenticated]

    def get_mot_details(self, registration_number):
        """Get vehicle make, model and year from MOT API"""
        url = settings.MICROSOFTONLINE_API
        headers = {
            "content-type": "application/x-www-form-urlencoded"
        }
        data = {
            "grant_type": "client_credentials",
            "client_id": settings.MICROSOFTONLINE_CLIENT_ID,
            "client_secret": settings.MICROSOFTONLINE_CLIENT_SECRET,
            "scope": "https://tapi.dvsa.gov.uk/.default"
        }

        try:
            response = requests.post(url, headers=headers, data=data)
            response_data = response.json()

            if "access_token" not in response_data:
                raise ValueError("Access token not found")
                
            access_token = response_data["access_token"]
            
            vehicle_url = f"{settings.MOT_API_URL}{registration_number}"
            vehicle_headers = {
                "accept": "application/json",
                "x-api-key": settings.MOT_API_KEY,
                "Authorization": f"Bearer {access_token}"
            }
            
            vehicle_response = requests.get(vehicle_url, headers=vehicle_headers)
            vehicle_data = vehicle_response.json()
            
            if "errorCode" in vehicle_data:
                error_message = vehicle_data.get("errorMessage", "Unknown error occurred")
                raise ValueError(error_message)
            
            if isinstance(vehicle_data, dict) and "vehicle_data" in vehicle_data:
                if "errorCode" in vehicle_data["vehicle_data"]:
                    error_message = vehicle_data["vehicle_data"].get("errorMessage", "Unknown error occurred")
                    raise ValueError(error_message)

            return {
                "make": vehicle_data.get("make", "").upper(),
                "model": vehicle_data.get("model", "").upper(),
                "year": vehicle_data.get("manufactureDate", "").split("-")[0]
            }
                
        except requests.RequestException as e:
            raise ValueError(f"Failed to get MOT data: {str(e)}")

    def post(self, request, *args, **kwargs):
        registration_number = request.data.get("registrationNumber")
        if not registration_number:
            return Response(
                {"error": "Registration number is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if Vehicle.objects.filter(vehicle_registration_number=registration_number, vehicle_reg_no_status= AttachmentStatus.verified).exists():
            return Response(
                {"error": "Vehicle with this registration number already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            try:
                mot_details = self.get_mot_details(registration_number)
            except ValueError as mot_error:
                return Response(
                    {"error": str(mot_error)},
                    status=status.HTTP_404_NOT_FOUND
                )

            api_url = settings.VEHICLE_VERIFICATION_API_URL
            headers = {
                "x-api-key": settings.VEHICLE_VERIFICATION_API_KEY,
                "Content-Type": "application/json",
            }
            payload = {"registrationNumber": registration_number}
            
            response = requests.post(api_url, json=payload, headers=headers)
            
            if response.status_code != 200:
                return Response(
                    {"error": "Failed to verify vehicle details"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            verification_data = response.json()
            print(mot_details["year"],'--------------------------------')
            with transaction.atomic():
                driver = Driver.objects.get(user=request.user)

                vehicle_model, _ = VehicleModel.objects.get_or_create(
                    manufacturer=mot_details["make"],
                    model=mot_details["model"],
                    year_of_manufacture=mot_details["year"]
                )

                vehicle_data = {
                    "vehicle_registration_number": registration_number,
                    "model": vehicle_model,
                    "year_of_manufacture":  mot_details["year"],
                    "color": verification_data.get("colour"),
                    "fuel_type": verification_data.get("fuelType"),
                    "mot_status": verification_data.get("motStatus"),
                    "month_of_first_dvla_registration": verification_data.get("monthOfFirstRegistration"),
                    "last_date_of_V5C_issued": verification_data.get("dateOfLastV5CIssued"),
                    "vehicle_reg_no_status": AttachmentStatus.required,
                    "owner": driver
                }

                vehicle = Vehicle.objects.filter(owner=driver).first()
                if vehicle:
                    for key, value in vehicle_data.items():
                        setattr(vehicle, key, value)
                    vehicle.save()
                    message = "Vehicle details updated successfully."
                else:
                    vehicle = Vehicle.objects.create(**vehicle_data)
                    message = "Vehicle registered successfully."

                response_data = {
                    "message": message,
                    "vehicle_id": str(vehicle.id),
                    "vehicle_details": {
                        "registration_number": vehicle.vehicle_registration_number,
                        "manufacturer": vehicle_model.manufacturer,
                        "vehicle_reg_no_status": vehicle.vehicle_reg_no_status,
                        "model": vehicle_model.model,
                        "year": vehicle_model.year_of_manufacture,
                        "color": vehicle.color,
                        "fuel_type": vehicle.fuel_type,
                        "mot_status": vehicle.mot_status,
                        "month_of_first_registration": vehicle.month_of_first_dvla_registration,
                        "last_v5c_date": vehicle.last_date_of_V5C_issued
                    }
                }

                return Response(response_data, status=status.HTTP_201_CREATED)

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "An error occurred while connecting to the vehicle API", "details": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class VehicleDocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            driver = request.user.driver
            vehicle = Vehicle.objects.filter(owner=driver).first()

            if not vehicle:
                return Response({"error": "No vehicle found for this driver."}, status=status.HTTP_404_NOT_FOUND)

            serializer = VehicleDocumentDetailSerializer(vehicle)
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        except AttributeError:
            return Response({"error": "User is not associated with a driver."}, status=status.HTTP_403_FORBIDDEN)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class VehicleDocumentUploadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        try:
            driver = request.user.driver

            vehicle = Vehicle.objects.filter(owner=driver).first()
            if not vehicle:
                return Response({"error": "No vehicle registered for this driver."}, status=status.HTTP_400_BAD_REQUEST)

            files_to_check = {
                'insurance_certificate': {
                    'status_field': 'insurance_certificate_status',
                    'update_field': 'insurance_certificate_last_update'
                },
                'mot_test_certificate': {
                    'status_field': 'mot_test_certificate_status',
                    'update_field': 'mot_test_certificate_last_update'
                },
                'private_hire_vehicle_licence': {
                    'status_field': 'private_hire_vehicle_licence_status',
                    'update_field': 'private_hire_vehicle_licence_last_update'
                },
                'log_book_V5C': {
                    'status_field': 'log_book_V5C_status',
                    'update_field': 'log_book_V5C_last_update'
                },
                'log_book_V5C_back': {
                    'status_field': 'log_book_V5C_status',
                    'update_field': 'log_book_V5C_last_update'
                }
            }

            for doc_field, fields in files_to_check.items():
                if doc_field in request.FILES:
                    if doc_field in ['log_book_V5C', 'log_book_V5C_back']:
                        if vehicle.log_book_V5C or vehicle.log_book_V5C_back:
                            setattr(vehicle, fields['status_field'], 'resubmitted')
                        else:
                            setattr(vehicle, fields['status_field'], 'submitted')
                    else:
                        if getattr(vehicle, doc_field):
                            setattr(vehicle, fields['status_field'], 'resubmitted')
                        else:
                            setattr(vehicle, fields['status_field'], 'submitted')

                    setattr(vehicle, fields['update_field'], timezone.now().date())

            serializer = VehicleDocumentSubmitReSubmitSerializer(vehicle, data=request.data, partial=True)

            if serializer.is_valid():
                with transaction.atomic():
                    serializer.save()

                return Response({"message": "Documents uploaded successfully.", "data": serializer.data}, status=status.HTTP_200_OK)

            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        except AttributeError:
            return Response({"error": "User is not associated with a driver."}, status=status.HTTP_403_FORBIDDEN)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



class VehicleStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print("now i am here!")
        try:
            if not hasattr(request.user, 'driver'):
                return Response({"error": "User is not a driver"}, status=status.HTTP_403_FORBIDDEN)

            driver = request.user.driver
            vehicle = Vehicle.objects.filter(owner=driver).first()

            if not vehicle:
                vehicle_status_data = {
                "vehicle_reg_no_status": AttachmentStatus.required,
                "insurance_certificate_status": AttachmentStatus.required,
                "mot_test_certificate_status": AttachmentStatus.required,
                "private_hire_vehicle_licence_status": AttachmentStatus.required,
                "log_book_V5C_status": AttachmentStatus.required,
            }

                return Response(vehicle_status_data, status=status.HTTP_200_OK)

            vehicle_status_data = {
                "vehicle_reg_no_status": vehicle.vehicle_reg_no_status,
                "insurance_certificate_status": vehicle.insurance_certificate_status,
                "mot_test_certificate_status": vehicle.mot_test_certificate_status,
                "private_hire_vehicle_licence_status": vehicle.private_hire_vehicle_licence_status,
                "log_book_V5C_status": vehicle.log_book_V5C_status,
            }

            return Response(vehicle_status_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class DriverVehicle(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            driver = request.user.driver
            vehicle = Vehicle.objects.filter(owner=driver).last()
            
            if vehicle:
                data = {
                    "manufacturer": vehicle.model.manufacturer if vehicle.model else None,
                    "model": vehicle.model.model if vehicle.model else None,
                    "year_of_manufacture": vehicle.year_of_manufacture,
                    "vehicle_registration_number": vehicle.vehicle_registration_number,
                    "mot_status": vehicle.mot_status,
                    "month_of_first_dvla_registration": vehicle.month_of_first_dvla_registration,
                    "color": vehicle.color,
                    "fuel_type": vehicle.fuel_type,
                }
                return Response({"vehicle": data}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "No vehicle found for the driver."}, status=status.HTTP_404_NOT_FOUND)
        except AttributeError:
            return Response({"error": "Driver profile not found for the user."}, status=status.HTTP_400_BAD_REQUEST)




class UpdateVehicleRegNoStatus(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request):
        try:
            driver = request.user.driver
            vehicle = Vehicle.objects.filter(owner=driver).first()
            
            if not vehicle:
                return Response({"error": "Vehicle not found or not owned by the driver."}, status=status.HTTP_404_NOT_FOUND)
            
            vehicle.vehicle_reg_no_status = "verified"
            vehicle.save()
            
            return Response({"message": "Vehicle registration number verified."}, status=status.HTTP_200_OK)
        except AttributeError:
            return Response({"error": "Driver profile not found for the user."}, status=status.HTTP_400_BAD_REQUEST)
