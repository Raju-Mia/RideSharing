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
    ServiceType,
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
# from trip.serializers import GetAllTripSerializer, RatingSerializer, StopSerializer
# from utils.fare import get_fare
from utils.validators import (
    file_extension_validator,
    file_size_validator,
    image_extension_validator,
)
from uc_admin.validators import email_is_valid
from uc_admin.models import (
    PermissionChoices,
    RejectedDriverInfo,
    RejectedFields,
    OperatorPermission,
)

User = get_user_model()




# class VehicleManufacturerListSerializer(serializers.ModelSerializer):
#     models = serializers.SerializerMethodField()

#     class Meta:
#         model = Manufacturer
# #         fields = ["id", "manufacturer", "models"]

#     def get_models(self, obj):
#         return VehicleModel.objects.filter(manufacturer=obj).values("model", "id")






class TripListSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    user_id = serializers.SerializerMethodField()
    phone = serializers.CharField(source="passenger_phone_number")
    email = serializers.CharField(source="passenger_email")
    drivers_full_name = serializers.SerializerMethodField()
    drivers_phone_number = serializers.SerializerMethodField()
    gender = serializers.SerializerMethodField()
    drivers_gender = serializers.SerializerMethodField()
    manufacturer = serializers.SerializerMethodField()
    registration_number = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "gender",
            "drivers_gender",
            "drivers_phone_number",
            "manufacturer",
            "registration_number",
            "unique_id",
            "pickup_location_name",
            "drop_off_location_name",
            "fare",
            "date",
            "pickup_time",
            "full_name",
            "user_id",
            "trip_status",
            "service_type",
            "drivers_full_name",
            "payment_status",
            "email",
            "phone",
            "number_of_passengers",
            "trip_date_time",
            "estimated_fare",
        ]

    def get_gender(self, obj):
        if obj.driver:
            return obj.driver.gender
        return ""

    def get_manufacturer(self, obj):
        if obj.driver:
            vehicle = obj.driver.vehicle
            if vehicle:
                return vehicle.model.manufacturer.manufacturer
        return ""

    def get_registration_number(self, obj):
        if obj.driver:
            vehicle = obj.driver.vehicle
            if vehicle:
                return vehicle.vehicle_registration_number
        return ""

    def get_drivers_full_name(self, obj):
        if obj.driver:
            return obj.driver.user.full_name
        return ""

    def get_drivers_gender(self, obj):
        if obj.driver:
            return obj.driver.gender
        return ""

    def get_drivers_phone_number(self, obj):
        if obj.driver:
            return obj.driver.user.phone
        return ""

    def get_user_id(self, obj):
        return obj.user.id

    def get_full_name(self, obj):
        return obj.user.full_name


# class AdminsFeedbackOnTripCancellationSerializer(serializers.ModelSerializer):
#     status = serializers.ChoiceField(choices=TripCancellationChoices)

#     class Meta:
#         model = CancelledTripsOfDriver
#         fields = ["status"]


class AssignVehicleSerializer(serializers.Serializer):
    trip_id = serializers.UUIDField()
    driver_id = serializers.UUIDField()

    class Meta:
        fields = ["trip_id", "driver_id", "vehicle_id"]


class EditTripsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"


# class DriverInfoStatusSerializer(serializers.ModelSerializer):
#     status = serializers.ChoiceField(choices=STATUS)

#     class Meta:
#         model = DataForOrganizationsDriverRegistration
#         fields = ["status"]


class NearestDriversVehicleSerializer(serializers.ModelSerializer):
    has_child_seat = serializers.SerializerMethodField()
    manufacturer = serializers.SerializerMethodField()
    service_type = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "manufacturer",
            "service_type",
            "maximum_passengers",
            "luggage_capacity",
            "has_child_seat",
        ]

    def get_has_child_seat(self, obj: Vehicle):
        return obj.number_of_child_seat > 0

    def get_vehicle_type(self, obj: Vehicle):
        return obj.model.service_type

    def get_manufacturer(self, obj: Vehicle):
        return obj.model.manufacturer.manufacturer


class NearestDriverSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source="user.full_name")
    email = serializers.CharField(source="user.email")
    phone = serializers.CharField(source="user.phone")
    org_name = serializers.CharField(
        source="organization.organization_name", allow_null=True
    )

    class Meta:
        model = Driver
        fields = [
            "id",
            "pp_size_driver_image",
            "unique_id",
            "full_name",
            "email",
            "phone",
            "gender",
            "status",
            "org_name",
        ]


class DriverListSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source="user.full_name")
    email = serializers.CharField(source="user.email")
    phone = serializers.CharField(source="user.phone")
    org_name = serializers.CharField(source="organization.organization_name")

    class Meta:
        model = Driver
        fields = [
            "id",
            "full_name",
            "unique_id",
            "email",
            "phone",
            "gender",
            "status",
            "org_name",
        ]


class NearestDriversInfoSerializer(serializers.ModelSerializer):
    vehicle = NearestDriversVehicleSerializer()
    driver = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = ["driver", "vehicle"]

    def get_driver(self, obj):
        serializer = NearestDriverSerializer(obj)
        return serializer.data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        trip = self.context["trip"]
        estimated_fare = get_fare(
            trip.estimated_distance_to_drop_off,
            trip.estimated_time_to_drop_off,
            instance.vehicle,
            BookingMethod.one_way,
            trip.distance_type,
        )
        data["vehicle"]["estimated_fare"] = round(estimated_fare, 2)
        return data


class InProgressTripLocationSerializers(serializers.ModelSerializer):
    vehicle_location = serializers.ReadOnlyField(
        source="driver.vehicle.current_location", read_only=True
    )
    driver_id = serializers.ReadOnlyField(source="driver.id", read_only=True)
    driver_name = serializers.ReadOnlyField(
        source="driver.user.first_name", read_only=True
    )
    vehicle_name = serializers.ReadOnlyField(
        source="driver.vehicle.manufacturer", read_only=True
    )

    class Meta:
        model = Trip
        fields = [
            "id",
            "vehicle_location",
            "driver_id",
            "pickup_location",
            "drop_off_location",
            "driver_name",
            "distance",
            "pickup_location_name",
            "drop_off_location_name",
            "vehicle_name",
        ]


# class ClientInfoSerailizer(serializers.ModelSerializer):
#     trip_set = GetAllTripSerializer(many=True)
#     client = serializers.SerializerMethodField()
#     rating_and_review = serializers.SerializerMethodField()

#     class Meta:
#         model = User
#         fields = ["client", "rating_and_review", "trip_set"]

#     def get_client(self, obj):
#         user_serializer = UserSerializer(obj)
#         return user_serializer.data

#     def get_rating_and_review(self, obj):
#         ratings = obj.rating_set.filter(user_rates_driver=False)
#         serializer = RatingSerializer(ratings, many=True)
#         return serializer.data


# class DriverInfoSerializer(serializers.ModelSerializer):
#     driver = serializers.SerializerMethodField()
#     vehicle = VehicleSerializer()
#     trip_set = GetAllTripSerializer(many=True)
#     rating_and_review = serializers.SerializerMethodField()

#     class Meta:
#         model = Driver
#         fields = [
#             "driver",
#             "rating_and_review",
#             "vehicle",
#             "trip_set",
#             "average_rating",
#         ]

#     def get_driver(self, obj):
#         serializer = DriverSerializer(obj)
#         return serializer.data

#     def get_rating_and_review(self, obj):
#         ratings = obj.rating_set.filter(user_rates_driver=True)
#         serializer = RatingSerializer(ratings, many=True)
#         return serializer.data


class DriverListSerializer(serializers.ModelSerializer):
    first_name = serializers.ReadOnlyField(source="user.first_name")
    last_name = serializers.ReadOnlyField(source="user.last_name")
    phone = serializers.ReadOnlyField(source="user.phone")
    organization_name = serializers.ReadOnlyField(
        source="organization.organization_name"
    )

    class Meta:
        model = Driver
        fields = [
            "id",
            "unique_id",
            "first_name",
            "last_name",
            "organization_name",
            "phone",
            "status",
        ]


class DriverProfileSerializer(serializers.ModelSerializer):
    driver = serializers.SerializerMethodField()
    vehicle = VehicleSerializer()
    rating_and_review = serializers.SerializerMethodField()

    class Meta:
        model = Driver
        fields = [
            "driver",
            "rating_and_review",
            "vehicle",
            "trip_set",
            "average_rating",
            "pp_size_driver_image",
        ]

    def get_driver(self, obj):
        serializer = DriverSerializer(obj)
        return serializer.data

    def get_rating_and_review(self, obj):
        ratings = obj.rating_set.filter(user_rates_driver=True)
        serializer = RatingSerializer(ratings, many=True)
        return serializer.data


class DateSerializerForRevenue(serializers.Serializer):
    start_date = serializers.DateField()
    end_date = serializers.DateField()

    class Meta:
        fields = ["start_date", "end_date"]


# class AdminBooksTripSerailizer(serializers.ModelSerializer):
#     email = serializers.EmailField(write_only=True, validators=[email_is_valid])
#     # Trip Related Data
#     booking_method = serializers.ChoiceField(choices=BookingMethod.choices)
#     vehicle_type = serializers.ChoiceField(choices=VEHICLE_TYPE)
#     number_of_passengers = serializers.IntegerField(
#         required=True, min_value=1, max_value=16
#     )
#     stops = StopSerializer(many=True, required=False)
#     key = serializers.CharField(write_only=True, required=True)

#     class Meta:
#         model = Trip
#         fields = [
#             "email",
#             "date",
#             "booking_method",
#             "hours",
#             "pickup_location",
#             "drop_off_location",
#             "pickup_time",
#             "pickup_location_name",
#             "drop_off_location_name",
#             "number_of_passengers",
#             "luggage_size",
#             "vehicle_type",
#             "distance",
#             "estimated_time",
#             "is_discounted",
#             "discount_amount",
#             "approximate_duration",
#             "airport_pickup",
#             "flight_number",
#             "flight_arrival_time",
#             "return_date",
#             "return_time",
#             "stops",
#             "key",
#         ]

#     def validate(self, data):
#         drop_off_location = data.get("drop_off_location", None)
#         drop_off_location_name = data.get("drop_off_location_name", None)
#         if data["booking_method"] == "as directed" and (
#             drop_off_location_name or drop_off_location
#         ):
#             raise serializers.ValidationError(
#                 "drop off location and name shouldn't be provided with As_Directed booking method"
#             )

#         # Validating the source key
#         source_key = data.get("key", None)
#         if source_key is None:
#             raise serializers.ValidationError("Service key is required to book a trip!")
#         try:
#             source = Source.objects.get(key=source_key)
#             data["source"] = source
#         except Source.DoesNotExist:
#             raise serializers.ValidationError("Invalid service key!")

#         # Raising Validation Error if drop off location or name isn't provided with other types of booking method
#         if data["booking_method"] != "as directed":
#             if not drop_off_location_name:
#                 raise serializers.ValidationError(
#                     "drop_off_location_name must be provided"
#                 )
#             if not drop_off_location:
#                 raise serializers.ValidationError("drop_off_location must be provided")

#         if data["booking_method"] == "round trip":
#             try:
#                 if data["return_date"] is None or data["return_time"] is None:
#                     raise serializers.ValidationError(
#                         "return_date and return_time must be provided"
#                     )
#                 if data["return_date"] < data["date"]:
#                     raise serializers.ValidationError(
#                         "return_date cannot be before first trip date"
#                     )
#             except KeyError:
#                 raise serializers.ValidationError(
#                     "return_date and return_time must be provided"
#                 )

#         if (
#             data.get("airport_pickup", False)
#             and data.get("flight_number", None) is None
#         ):
#             raise serializers.ValidationError("flight_number must be provided")

#         # checking if date and time is valid
#         date = data.get("date")
#         if datetime.date.today() < date:
#             return super().validate(data)
#         if datetime.date.today() == date:
#             if datetime.datetime.now().time() < data.get("pickup_time"):
#                 return super().validate(data)
#             else:
#                 raise serializers.ValidationError("Pickup time cannot be in the past")
#         else:
#             raise serializers.ValidationError("Date cannot be in the past")

#     def create(self, validated_data):
#         stops = None
#         validated_data.pop("key", None)
#         if validated_data.get("stops", None):
#             stops = validated_data.pop("stops")
#         del validated_data["email"]
#         trip = Trip.objects.create(**validated_data)
#         if stops:
#             for stop in stops:
#                 Stops.objects.create(trip=trip, location=stop["location"])
#         return trip


class OnlineUsersSerializer(serializers.ModelSerializer):
    is_driver = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "first_name", "email", "is_driver", "last_seen"]

    def get_is_driver(self, object):
        return is_driver(object)


class RegisterHotelSerializer(serializers.ModelSerializer):
    hotel_name = serializers.CharField(required=True)

    class Meta:
        model = User
        fields = ["email", "hotel_name", "password"]

    def validate(self, data):
        if User.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError("Email already exists")
        if User.objects.filter(username=data["email"]).exists():
            raise serializers.ValidationError("User already exists")
        return data


class OperatorCreationSerializer(serializers.Serializer):
    full_name = serializers.CharField()
    email = serializers.EmailField(validators=[email_validator])
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=PermissionChoices.choices)
    )


class OperatorUpdateSerializer(serializers.Serializer):
    full_name = serializers.CharField(required=False)
    email = serializers.EmailField(validators=[email_validator], required=False)
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=PermissionChoices.choices), required=False
    )


class OperatorViewingSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    joined_at = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["email", "full_name", "joined_at", "id", "permissions"]

    def get_permissions(self, obj):
        return OperatorPermission.objects.filter(user=obj).values_list(
            "permission", flat=True
        )

    def get_joined_at(self, obj):
        return obj.created_at.date()


class AdminRegisterVehicleSerializer(serializers.ModelSerializer):
    service_type = serializers.CharField(required=True)
    mot = serializers.FileField(
        validators=[file_size_validator, file_extension_validator]
    )
    vehicle_insurance = serializers.FileField(
        validators=[file_size_validator, file_extension_validator]
    )
    vehicle_front_image = serializers.ImageField(
        validators=[file_size_validator, image_extension_validator]
    )
    vehicle_back_image = serializers.ImageField(
        validators=[file_size_validator, image_extension_validator]
    )
    # vehicle_left_image = serializers.ImageField(
    #     validators=[file_size_validator, image_extension_validator]
    # )
    # vehicle_right_image = serializers.ImageField(
    #     validators=[file_size_validator, image_extension_validator]
    # )
    vehicle_interior_image = serializers.ImageField(
        validators=[file_size_validator, image_extension_validator]
    )

    class Meta:
        model = Vehicle
        fields = [
            # "bluebook",
            
            "color",
            "poc_file",
            "vehicle_log_book_V5C",



            "model",
            "mot",
            "vehicle_registration_number",
            "maximum_passengers",
            "luggage_capacity",
            "vehicle_insurance",
            "vehicle_front_image",
            "service_type",
            "vehicle_back_image",
            # "vehicle_left_image",
            # "vehicle_right_image",
            "vehicle_interior_image",
            "model_year",
            "number_of_child_seat",
        ]


class VehicleListSerializer(serializers.ModelSerializer):
    owned_by = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "unverified_vehicle_model",
            "status",
            "service_type",
            "owned_by",
            "id",
        ]

    def get_owned_by(self, obj):
        return "Driver" if obj.owner else "Organization"


class VehicleSerializer(serializers.ModelSerializer):
    manufacturer = serializers.SerializerMethodField()
    model = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = [
            "manufacturer",
            # "bluebook",
            # "vehicle_registration_file",
            "color",
            "poc_file",
            "vehicle_log_book_V5C",
            "mot",
            "maximum_passengers",
            "luggage_capacity",
            "vehicle_insurance",
            "vehicle_front_image",
            "vehicle_back_image",
            # "vehicle_left_image",
            # "vehicle_right_image",
            "vehicle_interior_image",
            "service_type",
            "status",
            "model",
            "unverified_manufacturer",
            "unverified_vehicle_model",
        ]

    def get_manufacturer(self, obj):
        if not obj.model:
            return ""
        return obj.model.manufacturer.manufacturer

    def get_model(self, obj):
        if not obj.model:
            return ""
        return obj.model.model


class VehicleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = VehicleModel
        fields = [
            "manufacturer",
            "model",
            "service_type",
            "inner_london",
            "outer_london_below_50",
            "outer_london_below_100",
            "outer_london_over_100",
        ]


# class ManufacturerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Manufacturer
#         fields = ["manufacturer"]


class RejectedFieldsSerializer(serializers.ModelSerializer):
    class Meta:
        model = RejectedFields
        fields = ["field", "reason"]


class RejectDriverInfoSerializer(serializers.ModelSerializer):
    rejected_fields = RejectedFieldsSerializer(many=True, source="rejected_fields_set")

    class Meta:
        model = RejectedDriverInfo
        fields = ["driver", "rejected_fields"]

    def create(self, validated_data):
        rejected_fields_data = validated_data.pop("rejected_fields_set")
        rejected_driver_info = RejectedDriverInfo.objects.create(**validated_data)
        for field_data in rejected_fields_data:
            RejectedFields.objects.create(
                rejected_driver_info=rejected_driver_info, **field_data
            )
        return rejected_driver_info




class UnverifiedDriverSerializer(serializers.ModelSerializer):
    applied_at = serializers.DateTimeField(source="created_at")
    full_name = serializers.CharField(source="user.full_name")
    id = serializers.ReadOnlyField(source="user.id")

    class Meta:
        model = Driver
        fields = ["id", "unique_id", "applied_at", "status", "full_name"]


class UnverifiedVehicleSerializer(serializers.ModelSerializer):
    applied_at = serializers.DateTimeField(source="created_at")
    owner = serializers.SerializerMethodField()

    class Meta:
        model = Vehicle
        fields = ["id", "unique_id", "applied_at", "status", "owner"]

    def get_owner(self, obj):
        if obj.owner:
            return {"full_name": obj.owner.user.full_name, "is_org": False}
        else:
            return {"full_name": "United Chauffeur", "is_org": True}


class DVLAVehicleEnquirySerializer(serializers.Serializer):
    registration_number = serializers.CharField()


class SetModelSerializer(serializers.Serializer):
    vehicle_id = serializers.UUIDField()
    model_id = serializers.UUIDField()


# class ManufacturerSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Manufacturer
#         fields = ["id", "manufacturer"]



class VehicleModelSerializer(serializers.ModelSerializer):
    inner_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    central_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    orbital_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    greater_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    outer_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    outer_london_circle_one_fare = serializers.JSONField(
        validators=[validate_circle_fare]
    )
    outer_london_circle_two_fare = serializers.JSONField(
        validators=[validate_circle_fare]
    )

    class Meta:
        model = VehicleModel
        fields = [
            "id",
            "manufacturer",
            "year_of_manufacture",
            "model",
            "service_type",
            "inner_london_fare",
            "central_london_fare",
            "orbital_london_fare",
            "greater_london_fare",
            "outer_london_fare",
            "outer_london_circle_one_fare",
            "outer_london_circle_two_fare",
            "booking_fee",
            "congestion_charge",
        ]




class VehicleModelSerializerForUpdate(serializers.ModelSerializer):
    inner_london_fare = serializers.JSONField(
        validators=[validate_circle_fare], required=False
    )
    central_london_fare = serializers.JSONField(
        validators=[validate_circle_fare], required=False
    )
    orbital_london_fare = serializers.JSONField(
        validators=[validate_circle_fare], required=False
    )
    greater_london_fare = serializers.JSONField(
        validators=[validate_circle_fare], required=False
    )
    outer_london_fare = serializers.JSONField(
        validators=[validate_circle_fare], required=False
    )
    outer_london_circle_one_fare = serializers.JSONField(
        validators=[validate_circle_fare], required=False
    )
    outer_london_circle_two_fare = serializers.JSONField(
        validators=[validate_circle_fare], required=False
    )
    booking_fee = serializers.CharField(required=False) 

    class Meta:
        model = VehicleModel
        fields = [
            "service_type",
            "inner_london_fare",
            "central_london_fare",
            "orbital_london_fare",
            "greater_london_fare",
            "outer_london_fare",
            "outer_london_circle_one_fare",
            "outer_london_circle_two_fare",
            "booking_fee",
            "congestion_charge",
        ]



class ServiceTypeSerializer(serializers.ModelSerializer):
    inner_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    central_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    orbital_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    greater_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    outer_london_fare = serializers.JSONField(validators=[validate_circle_fare])
    outer_london_circle_one_fare = serializers.JSONField(validators=[validate_circle_fare])
    outer_london_circle_two_fare = serializers.JSONField(validators=[validate_circle_fare])

    class Meta:
        model = ServiceType
        fields = [
            "id",
            "service_type",
            "inner_london_fare",
            "central_london_fare",
            "orbital_london_fare",
            "greater_london_fare",
            "outer_london_fare",
            "outer_london_circle_one_fare",
            "outer_london_circle_two_fare",
            "booking_fee",
            "congestion_charge",
            "created_at",
            "updated_date",
        ]


class TripFilterAll(models.TextChoices):
    all = "All"


class TripFilteringQuerySerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=TripStatus.choices + TripFilterAll.choices)
