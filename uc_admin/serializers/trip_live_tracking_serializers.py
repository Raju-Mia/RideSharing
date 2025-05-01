from django.contrib.auth import get_user_model
from rest_framework import serializers
from trip_management.models import Trip
from driver_app.models import Driver
from trip_management.helpers import calculate_distance_and_time
import math
class TripListSerializer(serializers.ModelSerializer):  
    dropoff_time = serializers.SerializerMethodField()
    dropoff_location_name = serializers.SerializerMethodField()


    class Meta:
        model = Trip
        fields = [
            'id', 'unique_id', 'trip_status','trip_method', 'pickup_time',
            'pickup_location_name', 'dropoff_time', 'dropoff_location_name',
        ]  

    def get_dropoff_location_name(self, obj):
        return obj.final_dropoff_location_name or obj.initial_dropoff_location_name
    
    def get_dropoff_time(self, obj):
        return obj.final_dropoff_time or obj.initial_dropoff_time

    
class TripCurrentLocationSerializer(serializers.ModelSerializer):
    current_location = serializers.SerializerMethodField()
    driver_full_name = serializers.CharField(source='driver.user.full_name', read_only=True)
    driver_picture = serializers.ImageField(
        source="driver.user.picture", read_only=True
    )

    class Meta:
        model = Trip
        fields = [
            'id', 'unique_id', 'current_location', 'driver_full_name', 'driver_picture'
        ]  

    def get_current_location(self, obj):
        if obj.travel_path and isinstance(obj.travel_path, list):
            return obj.travel_path[-1] if obj.travel_path else None
        return None


class TripInfoForLiveTrackingSerializer(serializers.ModelSerializer):
    current_location = serializers.SerializerMethodField()
    driver = serializers.SerializerMethodField()
    trip_details = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = ['current_location', 'driver', 'trip_details']

    def get_current_location(self, obj):
        current_location = self.get_current_location_data(obj)
        if current_location:
            return {
                "latitude": current_location.get('lat'),
                "longitude": current_location.get('lng'),
            }
        return None

    def get_driver(self, obj):
        if obj.driver:
            return {
                "id": str(obj.driver.id),
                "full_name": obj.driver.user.full_name,
                "phone": obj.driver.user.phone,
                "email": obj.driver.user.email,
                "picture": obj.driver.user.picture.url if obj.driver.user.picture else None,
                # "vehicle_image": obj.driver.vehicles.vehicle_front_image.url if obj.driver.vehicles.vehicle_front_image else None,
                "address": obj.driver.address,
                "vehicle_registration_number": obj.driver.vehicles.vehicle_registration_number if obj.driver.vehicles else None,
                "average_rating": obj.driver.user.average_rating,
                "total_earned": obj.driver.total_earned,

            }
        return None

    def get_trip_details(self, obj):
        return {
            "id": str(obj.id),
            "trip_method": obj.trip_method,
            "trip_status": obj.trip_status,
            "flight_number": obj.flight_number,
            "pickup_location": {
                "latitude": obj.pickup_location_lat,
                "longitude": obj.pickup_location_lng,
                "name": obj.pickup_location_name,
            },
            "dropoff_location": {
                "latitude": self.get_dropoff_location_lat(obj),
                "longitude": self.get_dropoff_location_lng(obj),
                "name": self.get_dropoff_location_name(obj),
            },
            "remaining_distance_km": round(self.get_remaining_distance(obj), 2) if self.get_remaining_distance(obj) else None,
            "remaining_time_seconds": round(self.get_remaining_time(obj), 2) if self.get_remaining_time(obj) else None,
            "total_distance_km": obj.final_distance_covered or obj.approximate_distance_covered,
            "estimated_time_minutes": obj.final_duration or obj.approximate_duration,
            "passenger": {
                "name": obj.passenger_name or (obj.user.full_name if obj.user else None),
                "email": obj.passenger_email or (obj.user.email if obj.user else None),
                "phone_number": obj.passenger_phone_number or (obj.user.phone_number if obj.user else None),
                "number_of_adults": obj.number_of_adult_passengers,
                "picture": obj.user.picture.url if obj.user and obj.user.picture else None,
            },
        }

    # Methods to calculate or retrieve specific data remain unchanged.
    def get_dropoff_location_name(self, obj):
        return obj.final_dropoff_location_name or obj.initial_dropoff_location_name

    def get_dropoff_location_lat(self, obj):
        return obj.final_dropoff_location_lat or obj.initial_dropoff_location_lat

    def get_dropoff_location_lng(self, obj):
        return obj.final_dropoff_location_lng or obj.initial_dropoff_location_lng

    def get_current_location_data(self, obj):
        if obj.travel_path and isinstance(obj.travel_path, list):
            return obj.travel_path[-1] if obj.travel_path else None
        return None

    def get_remaining_distance(self, obj):
        current_location = self.get_current_location_data(obj)
        if not current_location:
            return None
        try:
            lat1, lng1 = float(current_location.get('lat')), float(current_location.get('lng'))
            lat2 = obj.final_dropoff_location_lat or obj.initial_dropoff_location_lat
            lng2 = obj.final_dropoff_location_lng or obj.initial_dropoff_location_lng
            if lat1 and lng1 and lat2 and lng2:
                distance, _ = self.distance_and_time(lat1, lng1, lat2, lng2)
                return distance
        except (TypeError, ValueError):
            return None

    def get_remaining_time(self, obj):
        current_location = self.get_current_location_data(obj)
        if not current_location:
            return None
        try:
            lat1, lng1 = float(current_location.get('lat')), float(current_location.get('lng'))
            lat2 = obj.final_dropoff_location_lat or obj.initial_dropoff_location_lat
            lng2 = obj.final_dropoff_location_lng or obj.initial_dropoff_location_lng
            if lat1 and lng1 and lat2 and lng2:
                _, time = self.distance_and_time(lat1, lng1, lat2, lng2)
                return time
        except (TypeError, ValueError):
            return None

    def distance_and_time(self, lat1, lng1, lat2, lng2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lng2 - lng1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             (math.sin(dlon / 2) ** 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        distance = R * c

        estimated_speed = 50
        time = (distance / estimated_speed) * 3600

        return distance, time






