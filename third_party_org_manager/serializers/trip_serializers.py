from rest_framework import serializers
from trip_management.models import Trip
from decimal import Decimal
# from accounts.models import VehicleModel

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




class TripRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Trip
        fields = "__all__"
    # class Meta:
    #     model = Trip
    #     fields = [
    #         'trip_method',
    #         'pickup_location_name', 
    #         'pickup_location_lat',
    #         'pickup_location_lng',
    #         'initial_dropoff_location_name',
    #         'initial_dropoff_location_lat',
    #         'initial_dropoff_location_lng', 
    #         'pickup_time', 
    #         'passenger_phone_number', 
    #         'passenger_name',
    #         'service_type', 
    #         'passenger_email', 
    #         'passenger_address',
    #         'number_of_adult_passengers', 
    #         'number_of_child_passengers', 
    #         'luggage_type',
    #         'flight_number',
    #         'per_mile_cost',
    #         'per_hour_cost',
    #         'org_commission_rate',
    #         'services', 

    #     ]

    # def create(self, validated_data):
    #     user = self.context['request'].user
    #     validated_data['user'] = user
    #     return super().create(validated_data)
    
    # def validate_service_type(self, value):
    #     """
    #     Ensure that the selected service type exists in the VehicleModel.
    #     """
    #     if not VehicleModel.objects.filter(service_type=value).exists():
    #         raise serializers.ValidationError("Selected service_type does not exist.")
    #     return value


class TripListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='user.organization.name', read_only=True)
    dropoff_location_name = serializers.SerializerMethodField()
    final_fare = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id',
            'unique_id',
            'trip_method',
            'pickup_time',
            'pickup_location_name',
            'final_dropoff_time',
            'dropoff_location_name',
            'passenger_name',
            'luggage_type',
            'final_fare',
            'trip_status',
            'payment_status',
            'organization_name',
        ]

    def get_dropoff_location_name(self, obj):
        return obj.final_dropoff_location_name or obj.initial_dropoff_location_name

    def get_final_fare(self, obj):
        if obj.final_fare != 0:
            return obj.final_fare
        if obj.fare != 0:
            return obj.fare
        return obj.estimated_fare
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)

        def format_decimal(value):
            try:
                return "{:.2f}".format(float(value))
            except (TypeError, ValueError):
                return value  # If the value is None or invalid, return as is

        # Format final_fare if present and valid
        if representation.get('final_fare') is not None:
            representation['final_fare'] = format_decimal(representation['final_fare'])

        return representation




class TripDetailSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='user.organization.name', read_only=True)
    driver_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    driver_phone = serializers.CharField(source='driver.user.phone', read_only=True)
    dropoff_location_name = serializers.SerializerMethodField()
    final_fare = serializers.SerializerMethodField()
    fare_with_org_commission_rate = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id',
            'unique_id', 
            'trip_method',
            'pickup_time',
            'pickup_location_name',
            'final_dropoff_time',
            'dropoff_location_name',
            'passenger_name', 
            'luggage_type',
            'final_fare',
            'fare_with_org_commission_rate',
            'org_commission_rate',
            'trip_status',
            'trip_method',
            'organization_name',
            'driver_name',
            'driver_phone',
            'number_of_adult_passengers', 
            'number_of_child_passengers', 
            'flight_number',
            'service_type',
        ]

    def get_dropoff_location_name(self, obj):
        return obj.final_dropoff_location_name or obj.initial_dropoff_location_name
    
    def get_final_fare(self, obj):
        if obj.final_fare != 0:
            return obj.final_fare
        if obj.fare != 0:
            return obj.fare
        return obj.estimated_fare
    
    def get_fare_with_org_commission_rate(self, obj):
        if obj.final_fare_with_org_commission_rate != 0:
            return obj.final_fare_with_org_commission_rate
        return obj.estimated_fare_with_org_commission_rate
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        
        def format_decimal(value):

            return "{:.2f}".format(float(value))
        
        final_fare = self.get_final_fare(instance)
        if final_fare is not None:
            representation['final_fare'] = format_decimal(final_fare)
        
        fare_with_org_commission_rate = self.get_fare_with_org_commission_rate(instance)
        if fare_with_org_commission_rate is not None:
            representation['fare_with_org_commission_rate'] = format_decimal(fare_with_org_commission_rate)
        
        if representation.get('org_commission_rate') is not None:
            representation['org_commission_rate'] = format_decimal(representation['org_commission_rate'])

        return representation
 


