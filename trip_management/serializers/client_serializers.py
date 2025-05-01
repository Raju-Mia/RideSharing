from rest_framework import serializers
from decimal import Decimal
from trip_management.models import Trip, TripBreak, ExtraCharge





class TripListForClientSerializar(serializers.ModelSerializer):
    """
    trip list for client exclude completed trips.
    """
    driver_name = serializers.CharField(
        source='driver.user.full_name', read_only=True)
    dropoff_location_name = serializers.SerializerMethodField()
    fare = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "unique_id",
            "driver_name",
            "pickup_location_name",
            "dropoff_location_name",
            "trip_status",
            "trip_method",
            "pickup_time",
            "fare",
        ]

    def get_dropoff_location_name(self, obj):
        return obj.final_dropoff_location_name or obj.initial_dropoff_location_name

    def get_fare(self, obj):
        if obj.final_fare != 0:
            return obj.final_fare
        if obj.fare != 0:
            return obj.fare
        return obj.estimated_fare

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)

    #     def format_decimal(value):
    #         return "{:.2f}".format(float(value))
    #     if representation.get('fare') is not None:
    #         representation['fare'] = format_decimal(representation['fare'])




class TripDetailForClientSerializer(serializers.ModelSerializer):
    driver_name = serializers.CharField(
        source='driver.user.first_name', read_only=True)
    driver_phone = serializers.CharField(
        source='driver.user.phone', read_only=True)
    dropoff_location_name = serializers.SerializerMethodField()
    fare = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id',
            'unique_id',
            'trip_method',
            'pickup_time',
            'booking_time',
            'final_dropoff_time',
            'pickup_location_name',
            'dropoff_location_name',
            'luggage_type',
            'trip_status',
            'driver_name',
            'driver_phone',
            'number_of_adult_passengers',
            'number_of_child_passengers',
            'flight_number',
            'service_type',
            'fare',
            'flight_number',
        ]

    def get_dropoff_location_name(self, obj):
        return obj.final_dropoff_location_name or obj.initial_dropoff_location_name

    def get_fare(self, obj):
        if obj.final_fare != 0:
            return obj.final_fare
        if obj.fare != 0:
            return obj.fare
        return obj.estimated_fare

    # def to_representation(self, instance):
    #     representation = super().to_representation(instance)

    #     def format_decimal(value):
    #         return "{:.2f}".format(float(value))
    #     if representation.get('fare') is not None:
    #         representation['fare'] = format_decimal(representation['fare'])
