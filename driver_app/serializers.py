

from django.contrib.auth import get_user_model
from notification_manager.models import FCMToken, NotifyMessage
from notification_manager.utils_helper import send_push_notification
from rest_framework import serializers
from datetime import date
from accounts.models import (
    CustomUser,
)

from driver_app.models import (
    Driver,
    DriverProfileEditRequest,
    Vehicle,
    VehicleModel,
    AttachmentStatus,
)


import firebase_admin
from firebase_admin import messaging, credentials
from notification_manager.firebase_init import initialize_firebase
initialize_firebase()


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'full_name', 'email',
                  'phone', 'service', 'address', 'picture', 'is_active']


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = [
            'id','username','full_name','email','phone','service','address','picture','stripe_id','is_hotel',
            'is_operator','blacklisted','sum_of_ratings','number_of_ratings','average_rating','email_is_verified',
            'phone_is_verified','user_is_verified','status','is_active','is_staff','is_superuser','terminated_status',
            'terminated_resone','terminated_at','created_at','updated_at',
        ]


class DriversToAssignTripSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    sum_of_ratings = serializers.CharField(
        source='user.sum_of_ratings', read_only=True)
    number_of_ratings = serializers.CharField(
        source='user.number_of_ratings', read_only=True)
    average_rating = serializers.CharField(
        source='user.average_rating', read_only=True)

    class Meta:
        model = Driver
        fields = ['id', 'unique_id', 'gender', 'user', 'date_of_birth',
                  'total_earned', 'status', 'sum_of_ratings', 'number_of_ratings', 'average_rating',]


class DriverProfileEditRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfileEditRequest
        fields = ['id', 'picture', 'status', 'admin_comment', 'created_at']
        read_only_fields = ['status', 'admin_comment', 'created_at']


class AdminApprovalSerializer(serializers.ModelSerializer):
    old_picture = serializers.SerializerMethodField()
    driver_fullname = serializers.CharField(
        source='user.full_name', read_only=True)

    class Meta:
        model = DriverProfileEditRequest
        fields = '__all__'
        read_only_fields = ['id', 'old_picture']

    def get_old_picture(self, obj):
        # Retrieve the associated driver's current profile picture
        driver = getattr(obj.user, 'driver', None)
        if driver:
            return driver.user.picture.url if driver.user.picture else None
        return None


class DriverDocumentSubmitReSubmitSerializer(serializers.ModelSerializer):
    dvla_plastic_driving_licence_front = serializers.FileField(required=False)
    dvla_plastic_driving_licence_back = serializers.FileField(required=False)
    private_hire_driving_licence = serializers.FileField(required=False)

    class Meta:
        model = Driver
        fields = [
            'dvla_plastic_driving_licence_front',
            'dvla_plastic_driving_licence_back',
            'private_hire_driving_licence'
        ]


class VehicleDocumentSubmitReSubmitSerializer(serializers.ModelSerializer):
    insurance_certificate = serializers.FileField(required=False)
    mot_test_certificate = serializers.FileField(required=False)
    private_hire_vehicle_licence = serializers.FileField(required=False)
    log_book_V5C = serializers.FileField(required=False)
    log_book_V5C_back = serializers.FileField(required=False)

    class Meta:
        model = Vehicle
        fields = [
            'insurance_certificate','mot_test_certificate','private_hire_vehicle_licence',
            'log_book_V5C','log_book_V5C_back'
        ]


class VehicleDocumentDetailSerializer(serializers.ModelSerializer):
    manufacturer = serializers.CharField(
        source='model.manufacturer', read_only=True)
    model = serializers.CharField(source='model.model', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'vehicle_registration_number', 'vehicle_reg_no_status', 'color', 'fuel_type', 'year_of_manufacture',
            'mot_status', 'insurance_certificate', 'insurance_certificate_status', 'insurance_certificate_last_update',
            'insurance_certificate_comment', 'manufacturer', 'model',
            'mot_test_certificate', 'mot_test_certificate_status', 'mot_test_certificate_last_update',
            'mot_test_certificate_comment', 'private_hire_vehicle_licence', 'private_hire_vehicle_licence_status',
            'private_hire_vehicle_licence_last_update', 'private_hire_vehicle_licence_comment',
            'log_book_V5C', 'log_book_V5C_back', 'log_book_V5C_status', 'log_book_V5C_last_update',
            'log_book_V5C_comment', 'last_date_of_V5C_issued'
        ]


class DriverInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Driver
        fields = [
            'driving_license_number','postal_code','date_of_birth',
            'dvla_plastic_driving_licence_expired_date'
        ]


class DriverDetailsSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField(source="user.full_name")

    class Meta:
        model = Driver
        fields = [
            'full_name','driving_license_number','driving_license_no_status','address',
            'postal_code','date_of_birth','gender','status',
            'dvla_plastic_driving_licence_front','dvla_plastic_driving_licence_back',
            'dvla_plastic_driving_licence_expired_date','dvla_plastic_driving_licence_last_update',
            'dvla_plastic_driving_licence_status','dvla_plastic_driving_licence_comment',
            'private_hire_driving_licence','private_hire_driving_licence_last_update',
            'private_hire_driving_licence_status','private_hire_driving_licence_comment'
        ]


class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Driver
        fields = [
            'id', 'user', 'unique_id', 'address', 'state', 'city', 'country', 'postal_code',
            'date_of_birth', 'gender', 'status',
            'driving_license_number', 'driving_license_no_status',
            'dvla_plastic_driving_licence_front', 'dvla_plastic_driving_licence_back',
            'dvla_plastic_driving_licence_status', 'dvla_plastic_driving_licence_last_update',
            'dvla_plastic_driving_licence_expired_date', 'dvla_plastic_driving_licence_comment',
            'private_hire_driving_licence', 'private_hire_driving_licence_status',
            'private_hire_driving_licence_last_update', 'private_hire_driving_licence_expired_date',
            'private_hire_driving_licence_comment', 'created_at', 'updated_at'
        ]


class VehicleSerializer(serializers.ModelSerializer):
    owner_id = serializers.UUIDField(source='owner.id', read_only=True)

    class Meta:
        model = Vehicle
        fields = [
            'id', 'vehicle_registration_number', 'vehicle_reg_no_status',
            'owner_id', 'status', 'color', 'fuel_type', 'year_of_manufacture',
            'mot_status', 'month_of_first_dvla_registration', 'insurance_certificate',
            'insurance_certificate_status', 'insurance_certificate_last_update',
            'insurance_certificate_expired_date', 'insurance_certificate_comment',
            'mot_test_certificate', 'mot_test_certificate_status', 'mot_test_certificate_last_update',
            'mot_test_certificate_expired_date', 'mot_test_certificate_comment',
            'private_hire_vehicle_licence', 'private_hire_vehicle_licence_status',
            'private_hire_vehicle_licence_last_update', 'private_hire_vehicle_licence_expired_date',
            'private_hire_vehicle_licence_comment', 'log_book_V5C', 'log_book_V5C_back',
            'log_book_V5C_status', 'log_book_V5C_last_update', 'log_book_V5C_expired_date',
            'log_book_V5C_comment', 'last_date_of_V5C_issued', 'number_of_child_seat',
            'maximum_passengers', 'luggage_capacity', 'created_at', 'updated_at'
        ]



class DriverVehicleDocumentDetailSerializer(serializers.ModelSerializer):
    driver = DriverDetailsSerializer()
    vehicle = VehicleSerializer()

    class Meta:
        model = Driver
        fields = [
            'id', 'driver', 'vehicle'
        ]