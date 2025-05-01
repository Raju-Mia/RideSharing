from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from dateutil.relativedelta import relativedelta
from datetime import datetime, date
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from trip_management.models import Trip
from utils.validators import (
    file_extension_validator,
    file_size_validator,
    image_extension_validator,
    password_validator,
)
from .models import (
    Organization,
    GENDER,
    Services,
)

from accounts.models import SavedPlace
from driver_app.models import (
    Driver,
    # DriverAttachmentStatus,
    Vehicle,
    LuggageCapacity,
    VehicleModel,
    # VehicleTypesInfo,
    CommunicationMethod
)


from .validators import email_validator
from utils.validators import validate_phone_number



# ==============Custom User Model=============
User = get_user_model()







class UserSignUpSerializerForDriver(serializers.Serializer):
    phone = serializers.CharField(required=True)
    password = serializers.CharField(validators=[password_validator], required=True)
    service = serializers.CharField(required=True)
    date_of_birth = serializers.CharField(required=True)  # Changed to CharField

    def validate_date_of_birth(self, value):
        """Validate the date format and ensure the user is at least 21 years old."""
        try:
            date_of_birth = datetime.strptime(value, '%d/%m/%Y').date()
        except ValueError:
            raise ValidationError(
                "Invalid date format. Use DD/MM/YYYY."
            )

        today = date.today()
        age = relativedelta(today, date_of_birth).years
        if age < 21:
            raise ValidationError("Driver must be at least 21 years old.")  # Fixed missing raise
        return date_of_birth  # Return the parsed date object

# #========== User Registration (New) ====S===
# class UserRegistrationSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['phone', 'email', 'service']

#     def validate(self, data):
#         phone = data.get('phone')
#         email = data.get('email')

#         if not phone and not email:
#             raise serializers.ValidationError("At least one of 'phone' or 'email' must be provided.")

#         return data
        
    
        
        
# class UserRegistrationVerifyOTPSerializer(serializers.Serializer):
#     user_id = serializers.UUIDField()
#     verification_otp = serializers.CharField(max_length=6)

#     class Meta:
#         fields = ["user_id","verification_otp"]
        


class UserProfileCreateSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField()
    token_id = serializers.UUIDField()
    full_name = serializers.CharField(required=True)
    
    class Meta:
        model = User
        fields = ['user_id', 'token_id', 'full_name', 'phone', 'email', 'picture']
        
        

#========== User Registration (New) ====E====



class SocialLoginSerializer(serializers.Serializer):
    token = serializers.CharField()
    service = serializers.ChoiceField(choices=Services.choices)


class EmailExistsSerializer(serializers.Serializer):
    email = serializers.EmailField()
    service = serializers.ChoiceField(choices=Services.choices, default="")


class PhoneExistsSerializer(serializers.Serializer):
    phone = serializers.CharField()
    service = serializers.ChoiceField(choices=Services.choices, default="")


# Client/User Signup Serializer
class SignUpSerializer(serializers.ModelSerializer):
    service = serializers.ChoiceField(choices=Services.choices, required=True)

    class Meta:
        model = User
        fields = [
            "email",
            "full_name",
            "password",
            "service",
        ]
        
        

    def validate_phone_address(self, phone: str, service: str):
        try:
            _ = User.objects.get(phone=phone, is_active=True, service=service)
            raise serializers.ValidationError("This phone number Already Exists")
        except User.DoesNotExist:
            return

    
    
    def validate(self, attrs):
        # Check if 'service' field is provided
        if 'service' not in attrs:
            raise serializers.ValidationError("Service field is required.")

        # Validate password
        if not password_validator(value=attrs.get("password")):
            raise serializers.ValidationError(
                "Password must contain at least 8 characters including uppercase, lowercase, and numbers!"
            )
        
        # Check if the provided service choice is valid
        service_choice = attrs['service']
        if service_choice not in dict(Services.choices):
            raise serializers.ValidationError(f"Invalid service choice: {service_choice}.")
            
        return attrs




class AdminSignsUpUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[email_validator])

    class Meta:
        model = User
        fields = ["email", "first_name", "last_name", "phone", "address"]


class OnlineUsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["first_name", "email", "last_seen"]


class DriverSignupSerializer(serializers.ModelSerializer):
    address = serializers.CharField(required=False)
    gender = serializers.ChoiceField(choices=GENDER)

    class Meta:
        model = Driver
        fields = [
            "gender",
            "address",
            "national_insurance",
            "driving_license_front_image",
            "driving_license_number",
            "driving_license_back_image",
            "pp_size_driver_image",
            "criminal_record_book",
            # "pco_license_file",
            "dbl_file",
            "tax_number",
            "dbs_image",
            "date_of_birth",
        ]





class OrganizationSignUpSerializer(serializers.ModelSerializer):
    organization_phone = serializers.CharField(source="phone")
    organization_address = serializers.CharField(source="address")

    class Meta:
        model = Organization
        fields = [
            "organization_phone",
            "whatsapp",
            "organization_name",
            "organization_address",
            "bank_name",
            "bank_account_number",
            "license_number",
            "license_file",
        ]




# Change will be here.
class TokenValidationSerializer(serializers.Serializer):
    token = serializers.CharField()
    id = serializers.UUIDField()

    class Meta:
        fields = ["token", "id"]



class OtpValidationSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    verification_otp = serializers.CharField(max_length=6)

    class Meta:
        fields = ["user_id","verification_otp"]




class ChangePasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField()
    password = serializers.CharField()
    service = serializers.ChoiceField(choices=Services.choices, default="")

    class Meta:
        fields = ["email", "code", "password"]




class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token["email"] = user.email
        token["address"] = user.address
        token["phone"] = user.phone

        return token


class UserSerializer(serializers.ModelSerializer):
    designation = serializers.SerializerMethodField()
    profile_image = serializers.SerializerMethodField()

    class Meta:
        model = User  # Assuming this is your CustomUser model
        fields = [
            "id",
            "email",
            "full_name",
            "phone",
            "address",
            "is_active",
            "picture",
            "email_is_verified",
            "designation",  # Added field
            "profile_image",  # Added field
        ]

    def get_designation(self, obj):
        # Check if the user has a profile and return the designation
        if hasattr(obj, 'profile') and obj.profile.designation:
            return obj.profile.designation
        return None

    def get_profile_image(self, obj):
        # Check if the user has a profile and return the profile image URL
        if hasattr(obj, 'profile') and obj.profile.profile_image:
            return obj.profile.profile_image.url if obj.profile.profile_image else None
        return None




class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "phone",
            "address",
            "average_rating",
            "is_active",
            "picture",
        ]
        read_only_fields = ["id", "email", "average_rating", "is_active"]


# class LoginSerializer(serializers.ModelSerializer):
#     phone_or_email = serializers.CharField()
#     service = serializers.ChoiceField(choices=Services.choices, default="", required=False)

#     class Meta:
#         model = User
#         fields = ["password", "service", "phone_or_email"]


from notification_manager.models import DEVICE_TYPES

class LoginSerializer(serializers.Serializer):
    phone_or_email = serializers.CharField()
    service = serializers.ChoiceField(choices=Services.choices, default="", required=False)
    password = serializers.CharField(write_only=True)

    # Extra Fields for Push Notification
    endpoint = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    p256dh = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    auth = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    # New fields for enhanced notification management
    browser_name = serializers.CharField(required=False, max_length=100, allow_blank=True, allow_null=True)
    operating_systems = serializers.CharField(required=False, max_length=100, allow_blank=True, allow_null=True)
    device_type = serializers.ChoiceField(
        required=False, choices=DEVICE_TYPES, allow_blank=True, allow_null=True
    )  # E.g., "mobile", "desktop"
    device_model = serializers.CharField(required=False, max_length=50, allow_blank=True, allow_null=True)
    device_os_version = serializers.CharField(required=False, max_length=50, allow_blank=True, allow_null=True)
    device_vendor = serializers.CharField(required=False, max_length=100, allow_blank=True, allow_null=True)
    device_id = serializers.CharField(required=False, max_length=100, allow_blank=True, allow_null=True)
    pv4_address = serializers.CharField(required=False, max_length=100, allow_blank=True, allow_null=True)
    IP_location = serializers.CharField(required=False, max_length=255, allow_blank=True, allow_null=True)
    user_agent = serializers.CharField(required=False, allow_blank=True, allow_null=True)  # Use CharField instead of TextField
    device_location_latitude = serializers.FloatField(required=False, allow_null=True)
    device_location_longitude = serializers.FloatField(required=False, allow_null=True)
    notification_enabled = serializers.BooleanField(required=False, default=True)





    
class UserLoginSerializer(serializers.Serializer):
    phone_or_email = serializers.CharField()
    service = serializers.ChoiceField(choices=Services.choices, default="", required=False)

    class Meta:
        model = User
        fields = ['phone_or_email', 'service']

    def create(self, validated_data):
        phone_or_email = validated_data['phone_or_email']
        service = validated_data.get('service', '')
        user = User(
            phone=phone_or_email if "@" not in phone_or_email else None,
            email=phone_or_email if "@" in phone_or_email else None,
            service=service
        )
        user.save()
        return user




class UserLoginVerificationSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    verification_otp = serializers.CharField(max_length=6,required=True)
    # user_active_status = serializers.BooleanField(required=True)
    # user_is_verified = serializers.BooleanField(required=True)

    # class Meta:
    #     fields = ["user_id", "verification_otp", "user_active_status", "user_is_verified"]

    
    
    
    

# Admin Login Serializer
class SuperAdminLoginSerializer(serializers.Serializer):
    phone_or_email = serializers.CharField()
    password = serializers.CharField(max_length=30, write_only=True)
    # service = serializers.ChoiceField(choices=Services.choices, default="", required=False)
    
    class Meta:
        model = User
        fields = ["password", "phone_or_email"]
    


class LogoutSerializer(serializers.ModelSerializer):
    refresh = serializers.CharField()
    default_error_messages = {"bad_token": "Token is expired or invalid"}

    class Meta:
        model = User
        fields = ["refresh"]

    def validate(self, attrs):
        self.token = attrs["refresh"]
        return attrs

    def save(self, **kwargs):
        try:
            RefreshToken(self.token).blacklist()
        except Exception:
            self.fail("bad_token")




class DriverSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="user.full_name")
    total_earned = serializers.DecimalField(
        max_digits=10, decimal_places=2, read_only=True
    )
    rating = serializers.IntegerField(max_value=10, min_value=0, read_only=True)
    trips = serializers.IntegerField(read_only=True)
    status = serializers.CharField(read_only=True)
    phone = serializers.CharField(source="user.phone", read_only=True)
    address = serializers.CharField(source="user.address", read_only=True)
    email = serializers.CharField(source="user.email", read_only=True)
    whatsapp = serializers.CharField(source="user.whatsappnumber", read_only=True)
    picture = serializers.ImageField(
        source="user.picture", read_only=True
    )
    is_email_verified = serializers.BooleanField(
        source="user.is_active", read_only=True
    )
    unique_id = serializers.CharField(read_only=True)

    class Meta:
        model = Driver
        fields = [
            "whatsapp",
            "id",
            "national_insurance",
            "total_earned",
            "rating",
            "trips",
            "full_name",
            "status",
            "gender",
            "phone",
            "address",
            "email",
            "picture",
            "driving_license_front_image",
            "driving_license_back_image",
            "pco_license_file",
            "average_rating",
            "unique_id",
            "is_email_verified",
        ]
        ref_name = "AccountsDriverSerializer"
        def validate(self, attrs):
            if attrs["gender"] not in ["Male", "Female", "Others"]:
                raise serializers.ValidationError("Incorrect Gender Value")
            return super().validate(attrs)


# class PaperSerializer(serializers.ModelSerializer):
#     vehicle = serializers.CharField(source="vehicle.id", read_only=True)

#     class Meta:
#         model = Paper
#         fields = ["vehicle", "paper_name", "paper"]


class VehicleSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.user.email")
    vehicle_manufacturer = serializers.SerializerMethodField()
    vehicle_model = serializers.SerializerMethodField()
    service_type = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "vehicle_manufacturer",
            "vehicle_model",
            "service_type",
            "id",
            "owner",
            # "bluebook",
            "color",
            "poc_file",
            "mot",
            "vehicle_registration_number",
            "maximum_passengers",
            "luggage_capacity",
            "vehicle_insurance",
            "vehicle_front_image",
            "vehicle_back_image",
            # "vehicle_left_image",
            # "vehicle_left_image",
            # "vehicle_right_image",
            "vehicle_interior_image",
            "service_type",
            "status",
        ]

    def get_vehicle_model(self, obj):
        return obj.model.model if obj.model else ""

    def get_vehicle_manufacturer(self, obj):
        if obj.model:
            return obj.model.manufacturer.manufacturer
        return ""

    def get_vehicle_type(self, obj):
        if obj.model:
            return obj.model.service_type
        return ""

    def validate(self, attrs):
        if attrs["maximum_passengers"] < 1 or attrs["maximum_passengers"] > 16:
            raise serializers.ValidationError(
                "Maximum passengers must be greater than 0 and less than 16"
            )
        return attrs


class VehicleDetailsSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source="owner.user.email")

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "owner",
            "vehicle_class",
            "mot",
            "has_child_seat",
            "maximum_passengers",
            "luggage_capacity",
            "service_type",
            "vehicle_registration_number",
            "vehicle_front_image",
            "vehicle_back_image",
            # "vehicle_left_image",
            # "vehicle_right_image",
            "vehicle_interior_image",
            "vehicle_insurance",
            "color",
            "poc_file"
            # "bluebook",
        ]


# class StopSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Stops
#         fields = ["location"]


# class VehicleAssignWaitingListSerializer(serializers.ModelSerializer):
#     driver_full_name = serializers.ReadOnlyField(source="driver.user.full_name")
#     date_of_trip = serializers.ReadOnlyField(source="trip.date")
#     pickup_time = serializers.ReadOnlyField(source="trip.pickup_time")
#     driver_id = serializers.ReadOnlyField(source="driver.id")
#     drivers_unique_id = serializers.ReadOnlyField(source="driver.unique_id")
#     trips_unique_id = serializers.ReadOnlyField(source="trip.unique_id")

#     class Meta:
#         model = VehicleAssignWaitingList
#         fields = (
#             "id",
#             "driver_full_name",
#             "date_of_trip",
#             "pickup_time",
#             "status",
#             "trip",
#             "created_at",
#             "driver_id",
#             "drivers_unique_id",
#             "trips_unique_id",
#         )


class UpdatedVehicleSerializer(serializers.ModelSerializer):
    poc_file = serializers.FileField(required=True)
    vehicle_insurance = serializers.FileField(required=True)
    vehicle_front_image = serializers.FileField(required=True)
    vehicle_back_image = serializers.FileField(required=True)
    # vehicle_left_image = serializers.FileField(required=True)
    # vehicle_right_image = serializers.FileField(required=True)
    vehicle_interior_image = serializers.FileField(required=True)
    mot = serializers.FileField(required=True)

    class Meta:
        model = Vehicle
        fields = [
            "vehicle_class",
            # "bluebook",
            "poc_file"

            "mot",
            "vehicle_registration_number",
            "has_child_seat",
            "maximum_passengers",
            "luggage_capacity",
            "vehicle_insurance",
            "vehicle_front_image",
            "vehicle_back_image",
            # "vehicle_left_image",
            # "vehicle_right_image",
            "vehicle_interior_image",
            "service_type",
        ]

    def validate(self, attrs):
        if attrs["maximum_passengers"] < 1 or attrs["maximum_passengers"] > 16:
            raise serializers.ValidationError(
                "Maximum passengers must be greater than 0 and less than 16"
            )
        return attrs





class TripInfo(serializers.ModelSerializer):
    distance = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    profile_picture = serializers.SerializerMethodField()
    # stops_set = StopSerializer(many=True)

    class Meta:
        model = Trip
        fields = [
            "id",
            "date",
            "pickup_time",
            "pickup_location",
            "drop_off_location",
            "pickup_location_name",
            "drop_off_location_name",
            # "stops_set",
            "fare",
            "payment_method",
            "distance",
            "estimated_time",
            "rating",
            "full_name",
            "profile_picture",
            "passenger_name",
            "trip_for_others",
            "passenger_phone_number",
            "airport_pickup",
        ]

    def get_profile_picture(self, obj):
        return obj.user.picture

    def get_full_name(self, obj):
        return obj.user.first_name + " " + obj.user.last_name

    def get_rating(self, obj):
        out = obj.user.sum_of_ratings
        return "{: .1f}".format(out)

    def get_distance(self, obj):
        subs = obj.distance.partition(".")
        return subs[0] + subs[1] + subs[2][:2]


# class AssignInfo(serializers.Serializer):
#     id = serializers.UUIDField()
#     created_at = serializers.DateTimeField()
#     seen = serializers.BooleanField(default=False)
#     distance_and_time_to_pickup_location = serializers.SerializerMethodField()
#     trip = TripInfo()

#     class Meta:
#         model = VehicleAssignWaitingList
#         fields = [
#             "id",
#             "created_at",
#             "trip",
#             "distance_and_time_to_pickup_location",
#             "seen",
#         ]

#     def get_distance_and_time_to_pickup_location(self, obj):
#         try:
#             vehicle = obj.driver.vehicle
#         except AttributeError:
#             return ""
#         if vehicle.current_location:
#             try:
#                 distance, time = calculate_distance(
#                     vehicle.current_location, obj.trip.pickup_location
#                 )
#                 return str(distance) + "," + str(time)
#             except TypeError:
#                 return ""
#         return ""


class DriverSerializerV2(serializers.ModelSerializer):
    gender = serializers.ChoiceField(choices=GENDER)

    class Meta:
        model = Driver
        fields = [
            "gender",
            "driving_license_front_image",
            "driving_license_back_image",
            "pp_size_driver_image",
            "national_insurance",
            # "is_condemned_prior",
            # "bank_account_number",
            # "pco_license_number",
            "criminal_record_book",
        ]


status_choices = (
    ("accept", "Accept"),
    ("deny", "Deny"),
)


class AcceptDenySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=status_choices)

    class Meta:
        fields = ["status"]


# class DriverRegistrationOfOrganizationSerializer(serializers.ModelSerializer):
#     gender = serializers.ChoiceField(choices=GENDER)

#     class Meta:
#         model = DataForOrganizationsDriverRegistration
#         fields = [
#             "gender",
#             "driving_license_front_image",
#             "driving_license_back_image",
#             "pp_size_driver_image",
#             "national_insurance",
#             "is_condemned_prior",
#             "drivers_bank_account_number",
#             "drivers_pco_license_number",
#         ]


# class NotificationSerializer(serializers.Serializer):
#     id = serializers.UUIDField()
#     title = serializers.CharField()
#     senders_first_name = serializers.CharField()
#     senders_last_name = serializers.CharField()
#     senders_profile_picture = serializers.URLField()
#     sender_id = serializers.UUIDField()
#     trip_id = serializers.UUIDField()
#     trip_status = serializers.CharField()
#     message = serializers.CharField()
#     is_seen = serializers.BooleanField()
#     created_at = serializers.DateTimeField()
#     is_hidden = serializers.BooleanField()

#     class Meta:
#         fields = [
#             "id",
#             "title",
#             "senders_first_name",
#             "senders_last_name",
#             "senders_profile_picture",
#             "sender_id",
#             "trip_id",
#             "message",
#             "is_seen",
#             "created_at",
#             "trip_status",
#             "is_hidden",
#         ]


# class SavedAddressSerializer(serializers.ModelSerializer):
#     id = serializers.UUIDField(read_only=True)
#     title = serializers.CharField()
#     address = serializers.CharField()

#     class Meta:
#         model = SavedAddress
#         fields = ["title", "address", "id"]


# class SourceSerializer(serializers.ModelSerializer):
#     """
#     Serializer to create source
#     """

#     class Meta:
#         model = Source
#         fields = "__all__"


class OrganizationValidationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id"]






class TheVehicleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleModel
        fields = ['id', 'model']

# class TheManufacturerSerializer(serializers.ModelSerializer):
#     models = TheVehicleModelSerializer(many=True, source='vehiclemodel_set')  # Serialize related vehicle models

#     class Meta:
#         model = Manufacturer
#         fields = ['id', 'manufacturer', 'models']






# class VehicleRegistrationSerializer(serializers.ModelSerializer):
#     mot = serializers.FileField(
#         validators=[file_size_validator, file_extension_validator]
#     )
#     vehicle_insurance = serializers.FileField(
#         validators=[file_size_validator, file_extension_validator]
#     )
#     vehicle_front_image = serializers.ImageField(
#         validators=[file_size_validator, image_extension_validator]
#     )
#     vehicle_back_image = serializers.ImageField(
#         validators=[file_size_validator, image_extension_validator]
#     )
    
#     # vehicle_left_image = serializers.ImageField(
#     #     validators=[file_size_validator, image_extension_validator]
#     # )
#     # vehicle_right_image = serializers.ImageField(
#     #     validators=[file_size_validator, image_extension_validator]
#     # )
    
#     vehicle_interior_image = serializers.ImageField(
#         validators=[file_size_validator, image_extension_validator]
#     )
#     vehicle_log_book_V5C = serializers.FileField(
#         validators=[file_size_validator, file_extension_validator]
#     )
#     vehicle_model = serializers.UUIDField(required=False, write_only=True)
#     luggage_capacity = serializers.ChoiceField(choices=LuggageCapacity, required=True)

#     class Meta:
#         model = Vehicle
#         fields = [
#             "vehicle_model",
#             "unverified_manufacturer",
#             # "bluebook",
#             # "vehicle_registration_file",
            
#             "color",
#             "poc_file",
#             "vehicle_log_book_V5C",


#             "unverified_vehicle_model",
#             "mot",
#             "maximum_passengers",
#             "luggage_capacity",
#             "vehicle_insurance",
#             "vehicle_front_image",
#             "vehicle_back_image",
            
#             # "vehicle_left_image",
#             # "vehicle_right_image",
            
#             "vehicle_interior_image",
#             "model_year",
#             "number_of_child_seat",
#             "vehicle_registration_number",
#         ]

#     def validate(self, attrs):

#         if "vehicle_model" in attrs.keys():
#             try:
#                 model = VehicleModel.objects.get(
#                     id=attrs.pop("vehicle_model"),
#                 )
#                 attrs["model"] = model
#             except VehicleModel.DoesNotExist:
#                 raise serializers.ValidationError("Model does not exist")
#             attrs.pop("unverified_manufacturer", None)
#             attrs.pop("unverified_vehicle_model", None)
#             return attrs
#         else:
#             if (
#                 "unverified_manufacturer" not in attrs.keys()
#                 or "unverified_vehicle_model" not in attrs.keys()
#             ):
#                 raise serializers.ValidationError(
#                     "either model or unverified model and unverified manufacturer must be provided"
#                 )

#         return attrs



class DriverResetPasswordSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=24)
    service = serializers.ChoiceField(choices=Services.choices)
    




class DriverSetNewPasswordSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    token_id = serializers.UUIDField()
    password = serializers.CharField(write_only=True)
    
    
    class Meta:
        fields = ["user_id", "token_id", "password"]


    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value
    
    


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    service = serializers.ChoiceField(choices=Services.choices, default="")
    method = serializers.ChoiceField(choices=CommunicationMethod.choices, default=CommunicationMethod.email)


class ValidateResetPasswordOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()
    service = serializers.ChoiceField(choices=Services.choices, default="")


class ResendOtpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    service = serializers.ChoiceField(choices=Services.choices, required=True)
    method = serializers.ChoiceField(
        choices=CommunicationMethod.choices, default=CommunicationMethod.email
    )


class DriverInfoForVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            "driving_license_front_image",
            "driving_license_back_image",
            "pp_size_driver_image",
            "national_insurance",
            "criminal_record_book",
            "dbl_file",
            "dbs_image",
            # "pco_license_file",
        ]

    def get_attachment_data(self, obj, field_name):
        data = {"attachment": getattr(obj, field_name).url}
        data.update(getattr(obj.driverattachmentstatus, field_name))
        return data

    def to_representation(self, instance):
        data = {}
        rejected_count = 0
        for field in self.fields:
            data[field] = self.get_attachment_data(instance, field)
            if data[field]["status"] == "rejected":
                rejected_count += 1
        data["rejected_driver_info"] = rejected_count
        return data




class VehicleInfoForVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            "mot",
            # "bluebook",
            # "vehicle_registration_file",
            
            "vehicle_log_book_V5C",
            "poc_file",

            "vehicle_insurance",
            "vehicle_front_image",
            "vehicle_back_image",
            # "vehicle_left_image",
            # "vehicle_right_image",
            "vehicle_interior_image",
        ]

    def get_attachment_data(self, obj, field_name):
        # Access the related VehicleAttachmentStatus using the correct related_name
        vehicle_attachments = getattr(obj, 'Vehicles_attachments', None)
        
        if vehicle_attachments:
            attachment_status = getattr(vehicle_attachments, field_name, None)
            if attachment_status is None:
                attachment_status = {}
            data = {
                "attachment": getattr(obj, field_name).url,
                "status": attachment_status.get("status", "pending"),
                "comment": attachment_status.get("comment", "")
            }
        else:
            data = {
                "attachment": getattr(obj, field_name).url,
                "status": "pending",  # Default status if attachment data is missing
                "comment": ""
            }
    
        # def get_attachment_data(self, obj, field_name):
        #     data = {"attachment": getattr(obj, field_name).url}
        #     data.update(getattr(obj.vehicleattachmentstatus, field_name))
        #     return data

        return data




    def to_representation(self, instance):
        data = {}
        rejected_count = 0
        for field in self.fields:
            data[field] = self.get_attachment_data(instance, field)
            if data[field]["status"] == "rejected":
                rejected_count += 1
        data["rejected_vehicle_info"] = rejected_count
        return data



class InfoForVerificationSerializer(serializers.Serializer):
    driver = serializers.SerializerMethodField()
    vehicle = serializers.SerializerMethodField()

    class Meta:
        fields = ["driver", "vehicle"]

    def get_driver(self, obj):
        return DriverInfoForVerificationSerializer(obj).data

    # def get_vehicle(self, obj):
    #     try:
    #         vehicle = obj.vehicle
    #     except AttributeError:
    #         print(" i am here==========")
    #         return None
    #     return VehicleInfoForVerificationSerializer(obj).data


    def get_vehicle(self, obj):
        vehicle = Vehicle.objects.filter(owner=obj).first()
        if vehicle:
            return VehicleInfoForVerificationSerializer(vehicle).data
        return None






# class VehicleModelsSerializer(serializers.ModelSerializer):
#     models = serializers.SerializerMethodField()

#     class Meta:
#         model = Manufacturer
#         fields = ["id", "manufacturer", "models"]

    def get_models(self, obj):
        return VehicleModel.objects.filter(manufacturer=obj).values("model", "id")





# class NotificationSerializerForSocket(serializers.ModelSerializer):
#     class Meta:
#         model = Notification
#         fields = ["id", "title", "message"]


class SendMailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField(default=None)

    class Meta:
        fields = ["email"]


# class NotificationSettingsSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = NotificationSettings
#         fields = ["call", "message", "job_alert"]


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(validators=[validate_phone_number])

    class Meta:
        fields = ["phone_number"]


class EmailSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
        fields = ["email"]


class WhatsappNumberSerializer(serializers.Serializer):
    whatsapp_number = serializers.CharField(validators=[validate_phone_number])

    class Meta:
        fields = ["whatsapp_number"]


# class NamePictureChangeStateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = NamePictureChangeState
#         fields = ["name", "picture"]

# class DriverDocumentsExpiredDateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = DriverDocument
#         fields = '__all__'
       
# class VehicleDocumentsExpiredDateSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = VehicleDocument
#         fields = '__all__'
        
        
        
        



class ValidateResetPasswordCodeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    OTP = serializers.CharField()



class SavedPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedPlace
        fields = [ 'name', 'location', 'lat', 'lon', 'icon','id']

