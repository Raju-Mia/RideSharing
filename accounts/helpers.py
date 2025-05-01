import requests
import uuid
from urllib.parse import unquote
import random
import string
from math import radians, sin, cos, sqrt, atan2
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from rest_framework import serializers
from utils.mail import send_email_verification_token, send_reset_password_code_mail
from utils.sms import send_phone_verification_sms, send_reset_password_code_sms


from accounts.views.accounts_helper import send_phone_verification_otp

from .permissions import is_driver
from .serializers import UserSerializer
from driver_app.models import (
    AttachmentStatus,
    CommunicationMethod,
    Driver,
    # DriverAttachmentStatus,
    Vehicle,
)

User = get_user_model()


def generate_prefix(name):
    if len(name) == 0:
        raise ValueError("Name is too short to generate a prefix")
    if len(name) == 1:
        prefix = name[0]
    else:
        prefix = name[:2]
    # hash_value = hashlib.sha256(name.encode()).hexdigest()
    # prefix += hash_value[:2]

    # Add a unique identifier to the prefix
    unique_id = str(uuid.uuid4().int)[:3]
    prefix += unique_id

    return prefix.upper()





# User Create Funtion==============
def create_user(serializer, is_driver=False):
    password = serializer.validated_data.pop("password")
    user = User(**serializer.validated_data, is_active=False)
    user.set_password(password)
    user.save()
    print("====Driver Register Saved Successfully=======")
    
    if is_driver:
        print("=== Is Driver True, then only phone verification will be work!===")
        send_phone_verification_otp(user=user)
        return user
    
    send_phone_verification_otp(user)
    return user




def create_driver_user(data, is_driver=False):
    """
    Create and return a user instance. Accepts either a serializer or a dictionary as input.
    """
    if isinstance(data, serializers.Serializer):  # Check if data is a serializer instance
        validated_data = data.validated_data
    elif isinstance(data, dict):  # If data is a dictionary
        validated_data = data
    else:
        raise TypeError("Data must be either a serializer instance or a dictionary")

    password = validated_data.pop("password")
    user = User(**validated_data, is_active=True)
    user.set_password(password)
    user.save()
    print("==== Driver Register Saved Successfully =======")

    if is_driver:
        print("=== Is Driver True, then only phone verification will work! ===")
        send_phone_verification_otp(user=user)
        return user

    send_phone_verification_otp(user)
    return user




# function to generate OTP
def get_n_length_random_string(n):
    """
    Generate n length random string containing uppercase, lower case and numbers
    Args:
        n: length of expected random sting

    Returns: n length random string

    """
    return "".join(
        random.choices(
            string.ascii_uppercase + string.ascii_uppercase + string.digits, k=n
        )
    )


def info_from_google(token: str):
    base_url = "https://www.googleapis.com/oauth2/v3/userinfo?access_token="
    url = base_url + str(unquote(token))
    data = requests.get(url, timeout=5).json()
    try:
        out = {
            "first_name": data["given_name"],
            "last_name": data["family_name"],
            "email": data["email"],
        }
    except KeyError:
        return None
    return out



# Get user model
# def get_user_details(user):
#     print("======== get_user_details Callign ========")
#     tokens = user.tokens
#     driver: bool = is_driver(user)
#     data = {
#         "user_info": UserSerializer(user).data,
#         "access": tokens["access"],
#         "refresh": tokens["refresh"],
#         "is_driver": driver,
#         "is_admin": hasattr(user, "admin"),
#         "is_organization": hasattr(user, "organization"),
#     }
#     if user.service == "":
#         if driver:
#             vehicle = Vehicle.objects.filter(owner=user.driver).first()
#         else:
#             vehicle = None
#         if vehicle:
#             data["has_vehicle"] = True
#             data["vehicle_verification_status"] = vehicle.status
#         else:
#             data["has_vehicle"] = False
#         if driver:
#             data["driver_profile_picture"] = user.driver.pp_size_driver_image.url
#             data["driver_verification_status"] = user.driver.status
#         else:
#             data["driver_profile_picture"] = ""
#             data["driver_verification_status"] = ""
#     if hasattr(user, "organization"):
#         data["key"] = (
#             user.organization.source.key if hasattr(user, "organization") else None
#         )
#         data["organization_id"] = user.organization.id
#     return data




#====================== New updated code ==============
def get_user_details(user):
    print("======== get_user_details Calling ========")
    
    tokens = user.tokens
    driver: bool = is_driver(user)

    # Initial data structure
    data = {
        "message": "Successfully Login",
        "user_info": UserSerializer(user).data,
        "access": tokens["access"],
        "refresh": tokens["refresh"],
        "is_driver": driver,
        "is_admin": hasattr(user, "admin"),
        "is_organization": hasattr(user, "organization"),
    }

        
    # Add organization name if the user has an organization and it's not None
    if user.organization:
        data["organization_id"] = user.organization.id  # Include organization ID
        data["organization_name"] = user.organization.name
        data["organization_picture"] = user.organization.picture.url if user.organization.picture else None
        
        if user.is_organization_admin:
            data["organization_admin"] = True 
            data["organization_operator"] = False 
            
        else:
            data["organization_admin"] = False 
            data["organization_operator"] = True
             

    if user.service:
        if driver:
            vehicle = Vehicle.objects.filter(owner=user.driver).first()
        else:
            vehicle = None
        
        if vehicle:
            data["has_vehicle"] = True
            data["vehicle_verification_status"] = vehicle.status
        else:
            data["has_vehicle"] = False
        
        if driver:
            data["driver_verification_status"] = user.driver.status
        else:
            data["driver_verification_status"] = ""
    
    return data


    # if hasattr(user, "organization"):
    #     data["key"] = (
    #         user.organization.source.key if hasattr(user, "organization") else None
    #     )
    #     data["organization_id"] = user.organization.id


def send_reset_password_code(user: User, method: CommunicationMethod):
    if method == CommunicationMethod.email:
        send_reset_password_code_mail(user)
    if method == CommunicationMethod.sms:
        send_reset_password_code_sms(user)


def update_driver_vehicle_info_status(info_status, fields):
    for field in fields:
        try:
            current_field = getattr(info_status, field)
            if current_field["status"] != AttachmentStatus.rejected:
                raise ValidationError(f"{field} can not be modified")
        except AttributeError:
            raise ValidationError(f"{field} does not exists")
        setattr(
            info_status,
            field,
            {
                "status": AttachmentStatus.resubmitted,
                "comment": current_field["comment"],
            },
        )
    info_status.save()


# def update_vehicle_info_status(vehicle: Vehicle, fields):
#     info_status = vehicle.vehicleattachmentstatus
#     for field in fields:
#         try:
#             current_field = getattr(info_status, field)
#             if current_field["status"] != AttachmentStatus.rejected:
#                 raise ValidationError(f"{field} can not be modified")
#         except AttributeError:
#             raise ValidationError(f"{field} does not exists")
#         setattr(
#             info_status,
#             field,
#             {"status": AttachmentStatus.pending, "comment": current_field["comment"]},
#         )
#     info_status.save()


def check_phone_email_uniqueness(
    service: str,
    phone: str | None = None,
    email: str | None = None,
    whatsapp_number: str | None = None,
) -> None:
    if phone:
        user = User.objects.filter(
            phone=phone, phone_is_verified=True, service=service
        ).first()
        if user:
            raise ValidationError({"phone_number": ["Phone already exists"]})
    if whatsapp_number:
        user = User.objects.filter(whatsappnumber=whatsapp_number)


# def get_attachments_status(driver: Driver, vehicle: Vehicle | None) -> dict:
#     vehicle_fields = [
#         "vehicle_registration_file",
#         "vehicle_front_image",
#         "vehicle_back_image",
#         # "vehicle_left_image",
#         # "vehicle_right_image",
#         "vehicle_interior_image",
#         "vehicle_insurance",
#         "mot",
#         "bluebook",
#     ]

#     driver_fields = [
#         "driving_license_front_image",
#         "driving_license_back_image",
#         "pp_size_driver_image",
#         "national_insurance",
#         "criminal_record_book",
#         "dbl_file",
#         "pco_license_file",
#     ]
#     if vehicle:
#         for field in vehicle_fields:
#             if getattr(vehicle.vehicleattachmentstatus, field)["status"] == "rejected":
#                 return {"rejected_remains": True}
#     for field in driver_fields:
#         if getattr(driver.driverattachmentstatus, field)["status"] == "rejected":
#             return {"rejected_remains": True}
#     return {"rejected_remains": False}



def get_attachments_status(driver: Driver, vehicle: Vehicle | None) -> dict:
    vehicle_fields = [
        # "vehicle_registration_file",
        "vehicle_front_image",
        "vehicle_back_image",
        # "vehicle_left_image",
        # "vehicle_right_image",
        "vehicle_interior_image",
        "vehicle_insurance",
        "mot",
        "vehicle_log_book_V5C",
        "poc_file",
        # "bluebook",
    ]

    driver_fields = [
        "driving_license_front_image",
        "driving_license_back_image",
        "pp_size_driver_image",
        "national_insurance",
        "criminal_record_book",
        "dbs_image",
        "dbl_file",
        # "pco_license_file",
    ]

    if vehicle:
        for field in vehicle_fields:
            # Use the correct related name 'Vehicles_attachments'
            if getattr(vehicle.Vehicles_attachments, field)["status"] == "rejected":
                return {"rejected_remains": True}
    
    for field in driver_fields:
        if getattr(driver.driverattachmentstatus, field)["status"] == "rejected":
            return {"rejected_remains": True}
    
    return {"rejected_remains": False}







def haversine_distance(lat1, lon1, lat2, lon2):
    
    R = 6371.0  # Radius of Earth in kilometers
    lat1_rad = radians(lat1)
    lon1_rad = radians(lon1)
    lat2_rad = radians(lat2)
    lon2_rad = radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c  # Distance in kilometers



