import datetime
import uuid

from django.contrib.auth import get_user_model
from django.db import models
from rest_framework import serializers

# from accounts.models import (
#     Manufacturer,
#     STATUS,
#     # DataForOrganizationsDriverRegistration,
#     Driver,
#     VehicleTypes,
#     Vehicle,
#     VEHICLE_TYPE,
#     VehicleAttachmentStatus,
#     VehicleModel,
#     DriverAttachmentStatus,
#     AttachmentStatus,
#     VehicleStatus,
# )

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



from accounts.serializers import UserSerializer, VehicleSerializer, DriverSerializer
from accounts.permissions import is_driver
from accounts.validators import email_validator, validate_circle_fare

from trip_management.models import (
    # BookingMethod,
    # Source,
    # Stops,
    # TripCancellationChoices,
    # CancelledTripsOfDriver,
    Trip,
    TripStatus,
)
# from trip_management.serializers import GetAllTripSerializer, RatingSerializer, StopSerializer
# from utils.fare import get_fare
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError



from utils.validators import (
    file_extension_validator,
    file_size_validator,
    image_extension_validator,
    password_validator,
)

from django.contrib.auth.hashers import make_password


from uc_admin.validators import email_is_valid
from uc_admin.models import (
    PermissionChoices,
    RejectedDriverInfo,
    RejectedFields,
    OperatorPermission,
)

from accounts.models import CustomUser
User = get_user_model()





#Admin Operator List Serializer 
class AdminOperatorsUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'full_name', 'phone', 'is_operator', 'is_active']  # Add the fields you want to include






class AdminOperatorSignUpSerializerForAdministration(serializers.ModelSerializer):
    username = serializers.CharField(required=True)
    email = serializers.EmailField(validators=[email_validator], required=False)
    password = serializers.CharField(validators=[password_validator], required=True)
    whatsappnumber = serializers.CharField(required=True, max_length=15)

    class Meta:
        model = User
        fields = ["username", "email", "full_name", "phone", "password", "whatsappnumber"]
        
        
        
    # ------Test Purpose ----
    # def validate_password(self, value):
    #     # Add custom password validation logic here if needed
    #     return make_password(value)


    # def create(self, validated_data):
    #     # This method will create the user and return it
    #     return User.objects.create(**validated_data, is_operator=True, is_active=True)
    # ---------- Test Purpose ---------
    
    

    def validate_username(self, value):
        """ Check if the username is already in use. """
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError({"message": "Username already taken!"})
        return value

    def validate(self, attrs):
        # Validate email and phone for uniqueness
        email = attrs.get('email')
        phone = attrs.get('phone')
        self.validate_email_and_phone(email, phone)
        return attrs

    def validate_email_and_phone(self, email: str, phone: str):
        """ Validate email and phone for uniqueness. """
        # Check if the phone is already in use and verified
        if User.objects.filter(phone=phone, phone_is_verified=True).exists():
            raise serializers.ValidationError({"message": "Phone number already used!"})
        
        # Check if the email is already in use and verified
        if email and User.objects.filter(email=email, email_is_verified=True).exists():
            raise serializers.ValidationError({"message": "Email already used!"})




class AdminOperatorDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id", "username", "email", "full_name", "phone", "whatsappnumber", "service", 
            "address", "picture", "stripe_id", "is_hotel", "is_operator", "blacklisted", 
            "sum_of_ratings", "number_of_ratings", "average_rating", "email_is_verified", 
            "phone_is_verified", "user_is_verified", "status", "is_active", "is_staff", 
            "is_superuser", "one_time_password_status", "attemp_count", "terminated_status", 
            "terminated_resone", "terminated_at", "created_by", "updated_at", "created_at",
            "last_activity", "is_online", "latitude", "longitude", "last_location_update"
        ]



class AdminOperatorUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "username", "email", "full_name", "phone", "whatsappnumber", "service", 
            "address", "picture", "stripe_id", "is_hotel", "blacklisted", 
            "sum_of_ratings", "number_of_ratings", "average_rating", 
            "email_is_verified", "phone_is_verified", "user_is_verified", 
            "status", "is_active", "is_staff", "is_superuser", 
            "one_time_password_status", "attemp_count", "terminated_status", 
            "terminated_resone", "terminated_at", "created_by", "updated_at", 
            "created_at", "last_activity", "is_online", "latitude", "longitude", 
            "last_location_update"
        ]

    def validate_username(self, value):
        """ Check if the username is already in use by another user. """
        if User.objects.filter(username=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError({"username": "Username already taken!"})
        return value

    def validate_email_and_phone(self, email: str, phone: str):
        """ Validate email and phone for uniqueness. """
        if email and User.objects.filter(email=email).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError({"email": "Email already used!"})
        if User.objects.filter(phone=phone).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError({"phone": "Phone number already used!"})
        return email, phone









class AdminOperatorPasswordChangeSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, required=True)

    def validate_new_password(self, value):
        """ Validate the new password with custom criteria. """
        try:
            validate_password(value)
        except ValidationError as e:
            # Provide custom error messages
            if 'password too short' in str(e):
                raise serializers.ValidationError("Password must contain at least 8 characters.")
            if 'common password' in str(e):
                raise serializers.ValidationError("Password is too common.")
            if 'numeric' in str(e):
                raise serializers.ValidationError("Password should not be entirely numeric.")
            if 'password too similar' in str(e):
                raise serializers.ValidationError("Password is too similar to your other passwords.")
            raise serializers.ValidationError("Password must meet complexity requirements.")
        return value



class AdminOperatorPasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        """ Check if the email exists in the database. """
        if not User.objects.filter(email=value, is_operator=True).exists():
            raise serializers.ValidationError("No user with this email found.")
        return value
