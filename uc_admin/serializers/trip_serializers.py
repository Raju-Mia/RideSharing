from decimal import Decimal
from rest_framework import serializers
from location.models import LocationInfo
from trip_management.helpers.api_helpes import format_decimal
from trip_management.models import Trip, ExtraCharge
# from accounts.models import Driver

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



from django.contrib.auth import get_user_model

User = get_user_model()
from accounts.serializers import UserSerializer


class DriverSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(source="user.id", read_only=True)
    whatsapp = serializers.CharField(
        source="user.whatsappnumber", required=True)
    full_name = serializers.CharField(source="user.full_name", required=True)
    phone = serializers.CharField(source="user.phone", required=True)
    # address = serializers.CharField(source="user.address", read_only=True, required=False)
    email = serializers.CharField(
        source="user.email", read_only=True, required=False)
    # picture = serializers.ImageField(
    #     source="user.driver.pp_size_driver_image", read_only=True, required=False
    # )

    class Meta:
        model = Driver
        fields = [
            "id",
            "user_id",
            "whatsapp",
            "full_name",
            "phone",
            # "address",
            "email",
            # "picture",
        ]








class ExtraChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExtraCharge
        fields = [
            'id',
            'charge_amount',
            'pictures',
            'charge_type',
            'charge_reason',
            'verified',
            'verified_by',
            'trip'
        ]
        read_only_fields = ['verified_by', 'trip']  # Make 'verified_by' and 'trip' read-only

    def create(self, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        verified = validated_data.pop('verified', False)

        pictures = validated_data.pop('pictures', [])

        extra_charge = ExtraCharge.objects.create(verified=verified, **validated_data)

        for picture in pictures:
            extra_charge.pictures.append(picture)
        extra_charge.save()

        if verified:
            if user and user.is_authenticated:
                extra_charge.verified_by = user
                extra_charge.save()
            else:
                raise serializers.ValidationError({
                    'verified_by': 'Cannot set verified without an authenticated user.'
                })

        return extra_charge

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user = request.user if request else None

        pictures = validated_data.pop('pictures', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if pictures is not None:
            instance.pictures = pictures

        verified = validated_data.get('verified', instance.verified)
        if verified and not instance.verified:
            if user and user.is_authenticated:
                instance.verified_by = user
            else:
                raise serializers.ValidationError({
                    'verified_by': 'Cannot set verified without an authenticated user.'
                })
        elif not verified:
            instance.verified_by = None

        instance.save()
        return instance

    # def validate_verified(self, value):
    #     """
    #     If 'verified' is being set to True, ensure the user has permission.
    #     """
    #     request = self.context.get('request')
    #     user = request.user if request else None

    #     if value and not (user and user.is_staff):
    #         raise serializers.ValidationError("Only staff users can verify extra charges.")
    #     return value
    
class TripListSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    driver = DriverSerializer()
    extra_charges = ExtraChargeSerializer(
        many=True, read_only=True, source='extracharge_set'
    )
    organization_name = serializers.CharField(
        source='user.organization.name', read_only=True
    )
    pickup_location_name = serializers.SerializerMethodField()
    dropoff_location_name = serializers.SerializerMethodField()
    total_with_congestion_charge = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    total_with_service_charge = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    milage_fare = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    minute_fare = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    passenger_name = serializers.SerializerMethodField()
    final_fare = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = Trip
        fields = ["id","unique_id", "pickup_location_name", "dropoff_location_name", "pickup_time","dropoff_time", 
                "organization_name","passenger_name", "trip_method", "trip_status","milage_fare", "minute_fare","payment_method",
                "total_with_congestion_charge","total_with_service_charge","final_fare","extra_charges","user","driver"]

    def get_passenger_name(self, obj):
        return obj.passenger_name or (obj.user.full_name if obj.user else None)


    def get_pickup_location_name(self, obj):
        pickup_place_id = obj.pickup_place_id
        pickup_location_name = LocationInfo.objects.filter(place_id=pickup_place_id).values_list('name', flat=True).first()
        return pickup_location_name if pickup_location_name else None
    def get_dropoff_location_name(self, obj):
        dropoff_place_id = obj.dropoff_place_id
        dropoff_location_name = LocationInfo.objects.filter(place_id=dropoff_place_id).values_list('name', flat=True).first()
        return dropoff_location_name if dropoff_location_name else None

    




class TripDetailEditSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    driver = DriverSerializer()
    extra_charges = ExtraChargeSerializer(
        many=True, read_only=True, source='extracharge_set'
    )
    organization_name = serializers.CharField(
        source='user.organization.name', read_only=True
    )
    total_extra_charge = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    fare_subtotal = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    subtotal_with_congestion_charge = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    fare_with_service_charge = serializers.DecimalField(read_only=True, max_digits=10, decimal_places=2)
    final_fare_with_org_commission_rate = serializers.DecimalField(read_only=True, max_digits=5, decimal_places=2)

    class Meta:
        model = Trip
        fields = '__all__'

    def get_passenger_name(self, obj):
        return obj.passenger_name or (obj.user.full_name if obj.user else None)

    def get_total_extra_charge(self, obj):
        return obj.total_extra_charge if obj.total_extra_charge is not None else Decimal('0.00')

    def get_fare_subtotal(self, obj):
        return obj.fare_subtotal if obj.fare_subtotal is not None else Decimal('0.00')

    def get_subtotal_with_congestion_charge(self, obj):
        return obj.subtotal_with_congestion_charge if obj.subtotal_with_congestion_charge is not None else Decimal('0.00')

    def get_fare_with_service_charge(self, obj):
        return obj.fare_with_service_charge if obj.fare_with_service_charge is not None else Decimal('0.00')

    def get_final_fare_with_org_commission_rate(self, obj):
        return obj.final_fare_with_org_commission_rate if obj.final_fare_with_org_commission_rate is not None else Decimal('0.00')
   
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        # Helper function to round and format to 2 decimal places
        def format_decimal(value):
            return "{:.2f}".format(float(value))

        # Apply formatting for the relevant fields
        if representation.get('total_extra_charge') is not None:
            representation['total_extra_charge'] = format_decimal(representation['total_extra_charge'])
        
        if representation.get('fare_subtotal') is not None:
            representation['fare_subtotal'] = format_decimal(representation['fare_subtotal'])
        
        if representation.get('subtotal_with_congestion_charge') is not None:
            representation['subtotal_with_congestion_charge'] = format_decimal(representation['subtotal_with_congestion_charge'])
        
        if representation.get('fare_with_service_charge') is not None:
            representation['fare_with_service_charge'] = format_decimal(representation['fare_with_service_charge'])
        
        if representation.get('final_fare_with_org_commission_rate') is not None:
            representation['final_fare_with_org_commission_rate'] = format_decimal(representation['final_fare_with_org_commission_rate'])

        return representation



class AssignDriverSerializer(serializers.Serializer):
    trip_id = serializers.UUIDField()
    driver_id = serializers.UUIDField()



class TripListForOrgSerializer(serializers.ModelSerializer):
    booked_by = serializers.CharField(source='user.full_name', read_only=True)
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)

    dropoff_location_name = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "unique_id",
            "pickup_location_name",
            "dropoff_location_name",
            "booking_time",
            "booked_by",
            "passenger_name",
            "trip_method",
            "final_fare",
            "trip_method",
            "trip_status",
            "driver_name"

        ]


    def get_dropoff_location_name(self, obj):
        return obj.final_dropoff_location_name or obj.initial_dropoff_location_name
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        def format_decimal(value):
                return "{:.2f}".format(float(value))
        if representation.get('final_fare') is not None:
            representation['final_fare'] = format_decimal(representation['final_fare'])

        return representation


