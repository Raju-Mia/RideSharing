from rest_framework import serializers
from decimal import Decimal
from location.models import LocationInfo
from trip_management.helpers.api_helpes import format_decimal
from trip_management.models import (Trip, CancelTrip,TripBreak, ExtraChargePicture,
                                    ExtraCharge, DeclineTrip, )




class TripBreakSerializer(serializers.ModelSerializer):
    break_duration = serializers.SerializerMethodField()
    class Meta:
        model = TripBreak
        fields = '__all__'
    
    def get_break_duration(self, obj):
        return obj.break_duration


class ExtraChargePictureSerializer(serializers.ModelSerializer):
    picture_url = serializers.SerializerMethodField()

    class Meta:
        model = ExtraChargePicture
        fields = ['id', 'picture_url']

    def get_picture_url(self, obj):
        request = self.context.get('request')
        if obj.picture:
            return request.build_absolute_uri(obj.picture.url)
        return None

class ExtraChargeSerializer(serializers.ModelSerializer):
    pictures = ExtraChargePictureSerializer(many=True, read_only=True)

    class Meta:
        model = ExtraCharge
        fields = '__all__'

class TripSerializer(serializers.ModelSerializer):
    trip_breaks = TripBreakSerializer(
        many=True, read_only=True, source='tripbreak_set')
    extra_charges = ExtraChargeSerializer(
        many=True, read_only=True, source='extracharge_set')

    class Meta:
        model = Trip
        fields = '__all__'



class LocationInfoSerializer(serializers.ModelSerializer):
    route = serializers.SerializerMethodField()

    class Meta:
        model = LocationInfo
        fields = [
            "place_id", "name", "latitude", "longitude",
            "route", "post_code", "city", "country", "address"
        ]

    def get_route(self, obj):
        import json
        try:
            return json.loads(obj.route)
        except Exception:
            return [obj.route] if obj.route else []




from rest_framework import serializers

class TripListForDriverSerializer(serializers.ModelSerializer):
    pickup_location_name = serializers.SerializerMethodField()
    dropoff_location_name = serializers.SerializerMethodField()
    terminal = serializers.SerializerMethodField()
    total_distance = serializers.SerializerMethodField()
    total_minutes = serializers.SerializerMethodField()
    final_fare = serializers.SerializerMethodField()
    trip_status = serializers.SerializerMethodField()
    trip_method = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "pickup_time",
            "pickup_location_name",
            "dropoff_location_name",
            "terminal",
            "total_distance",
            "dropoff_time",
            "trip_status",
            "trip_method",
            "total_minutes",
            "final_fare",

        ]

    def get_trip_method(self, obj):
        trip_method = obj.trip_method
        trip_method = trip_method.split("_")
        trip_method = " ".join([word.capitalize() for word in trip_method])
        return trip_method
    def get_trip_status(self, obj):
        trip_status = obj.trip_status
        if trip_status == "APPROVED_BY_DRIVER":
            trip_status = "Upcoming"
        trip_status = trip_status.split("_")
        trip_status = " ".join([word.capitalize() for word in trip_status])
        return trip_status

    def get_total_distance(self, obj):
        return format_decimal(obj.total_distance)

    def get_total_minutes(self, obj):
        return format_decimal(obj.total_minutes)

    def get_final_fare(self, obj):
        return format_decimal(obj.final_fare)

    def get_pickup_location_name(self, obj):
        place_id = obj.pickup_place_id
        location_map = self.context.get("location_info_map", {})
        return location_map.get(place_id).name if place_id in location_map else None

    def get_dropoff_location_name(self, obj):
        place_id = obj.dropoff_place_id
        location_map = self.context.get("location_info_map", {})
        return location_map.get(place_id).name if place_id in location_map else None

    def get_terminal(self, obj):
        terminal = "Terminal 4"
        return terminal



    

class TripDetailForDriverSerializer(serializers.ModelSerializer):
    pickup_location = serializers.SerializerMethodField()
    dropoff_location = serializers.SerializerMethodField()
    stopages = serializers.SerializerMethodField()
    total_distance = serializers.SerializerMethodField()
    total_minutes = serializers.SerializerMethodField()
    fare = serializers.SerializerMethodField()
    final_fare = serializers.SerializerMethodField()
    terminal = serializers.SerializerMethodField()
    trip_status = serializers.SerializerMethodField()
    trip_method = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "pickup_time",
            "pickup_location",
            "stopages",
            "dropoff_location",
            "terminal",
            "trip_status",
            "trip_method",
            "total_distance",
            "total_minutes",
            "fare",
            "final_fare",
        ]

    def _get_location(self, place_id):
        location_info_map = self.context.get("location_info_map", {})
        return location_info_map.get(place_id)

    def get_pickup_location(self, obj):
        location = self._get_location(obj.pickup_place_id)
        return LocationInfoSerializer(location).data if location else None

    def get_dropoff_location(self, obj):
        location = self._get_location(obj.dropoff_place_id)
        return LocationInfoSerializer(location).data if location else None
    
    def get_terminal(self, obj):
        terminal = "Terminal 4"
        return terminal


    def get_total_distance(self, obj):
        return format_decimal(obj.total_distance)

    def get_total_minutes(self, obj):
        return format_decimal(obj.total_minutes)

    def get_fare(self, obj):
        return format_decimal(obj.fare)

    def get_final_fare(self, obj):
        return format_decimal(obj.final_fare)
    def get_stopages(self, obj):
        stopages = []
        stopage_data = obj.stopage_place_ids or {}
        location_info_map = self.context.get("location_info_map", {})

        for key in sorted(stopage_data.keys()):
            place_id = stopage_data[key]
            location = location_info_map.get(place_id)

            stopages.append({
                "label": key,
                "place_id": place_id,
                "location": LocationInfoSerializer(location).data if location else None
            })

        return stopages
    
    def get_trip_method(self, obj):
        trip_method = obj.trip_method
        trip_method = trip_method.split("_")
        trip_method = " ".join([word.capitalize() for word in trip_method])
        return trip_method
    def get_trip_status(self, obj):
        trip_status = obj.trip_status
        trip_status = trip_status.split("_")
        trip_status = " ".join([word.capitalize() for word in trip_status])
        return trip_status

class CompletedTripDetailForDriverSerializer(serializers.ModelSerializer):
    """
    Serializer for completed trip details with enhanced location information and stopages.
    """
    pickup_location = serializers.SerializerMethodField()
    dropoff_location = serializers.SerializerMethodField()
    stopages = serializers.SerializerMethodField()
    total_distance = serializers.SerializerMethodField()
    total_minutes = serializers.SerializerMethodField()
    
    # extra_charges = ExtraChargeSerializer(
    #     many=True, read_only=True, source='extracharge_set')
    terminal = serializers.SerializerMethodField()
    client_rating = serializers.SerializerMethodField()
    client_picture = serializers.SerializerMethodField()
    trip_status = serializers.SerializerMethodField()
    trip_method = serializers.SerializerMethodField()
    client_name = serializers.CharField(source='user.full_name')
    fare = serializers.SerializerMethodField()
    congestion_charge_amount = serializers.SerializerMethodField()
    total_with_congestion_charge = serializers.SerializerMethodField()
    service_charge_amount = serializers.SerializerMethodField()
    total_with_service_charge = serializers.SerializerMethodField()
    vat_amount = serializers.SerializerMethodField()
    total_fare_with_vat = serializers.SerializerMethodField()
    org_commission_rate = serializers.SerializerMethodField()
    client_tip = serializers.SerializerMethodField()
    org_commission_amount = serializers.SerializerMethodField()
    final_fare = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "id",
            "unique_id",
            "payment_method",
            "pickup_time",
            "pickup_location",
            "dropoff_location",
            "stopages",
            "trip_status",
            "trip_method",
            "total_distance",
            "total_minutes",
            
            "client_rating",
            "client_picture",
            "client_name",

            "fare",
            "congestion_charge_amount",
            "total_with_congestion_charge",
            "service_charge_amount",
            "total_with_service_charge",
            "vat_amount",
            "total_fare_with_vat",
            "org_commission_rate",
            "client_tip",
            "org_commission_amount",
            "terminal",
            # "congestion_charge",
            # "subtotal_with_congestion_charge",
            # "service_charge",
            # "fare_with_service_charge",
            # "vat",
            "final_fare",
            "payment_status",
            # "extra_charges",
        ]

    def get_total_minutes(self, obj):
        return format_decimal(obj.total_minutes)
    def get_total_distance(self, obj):
        return format_decimal(obj.total_distance)
    def get_client_rating(self, obj):
        return 0.00
    def get_trip_method(self, obj):
        trip_method = obj.trip_method
        trip_method = trip_method.split("_")
        trip_method = " ".join([word.capitalize() for word in trip_method])
        return trip_method
    def get_trip_status(self, obj):
        trip_status = obj.trip_status
        trip_status = trip_status.split("_")
        trip_status = " ".join([word.capitalize() for word in trip_status])
        return trip_status
        
    def get_client_picture(self, obj):
        if obj.user.picture:
            return obj.user.picture.url
        return None
    def get_terminal(self, obj):
        terminal = "Terminal 4"
        return terminal
    
    def _get_location(self, place_id):
        """Helper method to get location info from context."""
        location_info_map = self.context.get("location_info_map", {})
        return location_info_map.get(place_id)

    def get_pickup_location(self, obj):
        location = self._get_location(obj.pickup_place_id)
        return LocationInfoSerializer(location).data if location else {
            "name": obj.pickup_location_name,
            "lat": obj.pickup_location_lat,
            "lng": obj.pickup_location_lng
        }

    def get_dropoff_location(self, obj):
        location = self._get_location(obj.dropoff_place_id)
        return LocationInfoSerializer(location).data if location else {
            "name": self.get_dropoff_location_name(obj),
            "lat": self.get_dropoff_location_lat(obj),
            "lng": self.get_dropoff_location_lng(obj)
        }

    def get_stopages(self, obj):
        stopages = []
        stopage_data = obj.stopage_place_ids or {}
        location_info_map = self.context.get("location_info_map", {})
        
        for key in sorted(stopage_data.keys()):
            place_id = stopage_data[key]
            location = location_info_map.get(place_id)
            stopages.append({
                "label": key,
                "place_id": place_id,
                "location": LocationInfoSerializer(location).data if location else None
            })
        
        return stopages
    

    
    def get_final_fare(self, obj):
        return format_decimal(obj.final_fare or 0.00)
    def get_fare(self, obj):
        return format_decimal(obj.fare or 0.00)
    def get_client_tip(self, obj):
        return format_decimal(obj.client_tip or 0.00)
    def get_congestion_charge_amount(self, obj):
        return format_decimal(obj.congestion_charge_amount or 0.00)
    def get_total_with_congestion_charge(self, obj):
        return format_decimal(obj.fare + obj.total_with_congestion_charge or 0.00)
    def get_service_charge_amount(self, obj):
        return format_decimal(obj.service_charge_amount or 0.00)
    def get_total_with_service_charge(self, obj):
        return format_decimal(obj.total_with_service_charge or 0.00)
    def get_vat_amount(self, obj):
        return format_decimal(obj.vat_amount or 0.00)
    def get_total_fare_with_vat(self, obj):
        return format_decimal(obj.total_fare_with_vat or 0.00)
    def get_org_commission_rate(self, obj):
        return format_decimal(obj.org_commission_rate or 0.00)
    def get_org_commission_amount(self, obj):
        return format_decimal(obj.org_commission_amount or 0.00)
    



class DeclineTripSerializer(serializers.ModelSerializer):
    trip_fare = serializers.SerializerMethodField()
    pickup_location_name = serializers.SerializerMethodField()
    dropoff_location_name = serializers.SerializerMethodField()
    pickup_time = serializers.SerializerMethodField()

    class Meta:
        model = DeclineTrip
        fields = '__all__'  # includes the SerializerMethodFields

    def get_trip_fare(self, obj):
        return format_decimal(obj.trip.final_fare) if obj.trip.final_fare else None

    def get_pickup_location_name(self, obj):
        location = LocationInfo.objects.filter(place_id=obj.trip.pickup_location_id).first()
        return location.name if location else None

    def get_dropoff_location_name(self, obj):
        location = LocationInfo.objects.filter(place_id=obj.trip.dropoff_location_id).first()
        return location.name if location else None

    def get_pickup_time(self, obj):
        return obj.trip.pickup_time



class CancelTripListSerializer(serializers.ModelSerializer):
    """
    Serializer for the CancelTrip model.
    """
    class Meta:
        model = CancelTrip
        fields = '__all__'



class TripSummarySerializer(serializers.ModelSerializer):
    fare = serializers.SerializerMethodField()
    congestion_charge = serializers.SerializerMethodField()
    subtotal_with_congestion_charge = serializers.SerializerMethodField()
    service_charge = serializers.SerializerMethodField()
    service_charge_amount = serializers.SerializerMethodField()
    fare_with_service_charge = serializers.SerializerMethodField()
    vat = serializers.SerializerMethodField()
    vat_amount = serializers.SerializerMethodField()
    final_fare = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            "trip_status",
            "fare",
            "congestion_charge",
            "subtotal_with_congestion_charge",
            "service_charge",
            "service_charge_amount",
            "fare_with_service_charge",
            "vat",
            "vat_amount",
            "final_fare",
        ]


    def get_fare(self, obj):
        return format_decimal(obj.fare)

    def get_congestion_charge(self, obj):
        return format_decimal(obj.congestion_charge)

    def get_subtotal_with_congestion_charge(self, obj):
        return format_decimal(obj.fare + obj.congestion_charge)

    def get_service_charge(self, obj):
        return format_decimal(obj.service_charge)

    def get_service_charge_amount(self, obj):
        return format_decimal(obj.service_charge_amount)
    def get_fare_with_service_charge(self, obj):
        return format_decimal(obj.fare_with_service_charge)

    def get_vat(self, obj):
        return format_decimal(obj.vat)

    def get_vat_amount(self, obj):
        return format_decimal(obj.vat_amount)

    def get_final_fare(self, obj):
        return format_decimal(obj.final_fare or 0.00)




class CancellationReasonSerializer(serializers.Serializer):
    reasons = serializers.ListField(child=serializers.CharField())