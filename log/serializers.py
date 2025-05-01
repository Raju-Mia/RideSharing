from rest_framework import serializers

from accounts.models import Driver, Vehicle
from trip_management.models import Trip


class VehicleHistorySerializer(serializers.Serializer):
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()
    id = serializers.CharField()
    history_user = serializers.CharField()
    history_id = serializers.IntegerField()
    changed_fields = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "history_date",
            "history_type",
            "id",
            "history_user",
            "history_id",
            "changed_fields",
        ]

    def get_changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return delta.changed_fields
        return []


class VehicleAssignSerializer(serializers.Serializer):
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()
    id = serializers.CharField()
    history_user = serializers.CharField()
    history_id = serializers.IntegerField()
    changed_fields = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "history_date",
            "history_type",
            "id",
            "history_user",
            "history_id",
            "changed_fields",
        ]

    def get_changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return delta.changed_fields
        return []


class DetailsOfVehicleHistory(serializers.ModelSerializer):
    class Meta:
        model = Vehicle.history.model
        fields = "__all__"


# class DetailVehicleAssign(serializers.ModelSerializer):
#     class Meta:
#         model = VehicleAssignWaitingList
#         fields = "__all__"


class DetailsOfDriverHistory(serializers.ModelSerializer):
    class Meta:
        model = Driver.history.model
        fields = "__all__"


# class DetailOfTripHistory(serializers.ModelSerializer):
#     class Meta:
#         model = Trip.history.model
#         fields = "__all__"


class HistoryOfSpecificVehileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle.history.model
        fields = "__all__"


class DriverHistorySerializer(serializers.Serializer):
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()
    id = serializers.CharField()
    history_user = serializers.CharField()
    history_id = serializers.IntegerField()
    changed_fields = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "history_date",
            "history_type",
            "id",
            "history_user",
            "history_id",
            "changed_fields",
        ]

    def get_changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return delta.changed_fields
        return []


class TripHistorySerializer(serializers.Serializer):
    history_date = serializers.DateTimeField()
    history_type = serializers.CharField()
    id = serializers.CharField()
    history_user = serializers.CharField()
    history_id = serializers.IntegerField()
    changed_fields = serializers.SerializerMethodField()

    class Meta:
        fields = [
            "history_date",
            "history_type",
            "id",
            "history_user",
            "history_id",
            "changed_fields",
        ]

    def get_changed_fields(self, obj):
        if obj.prev_record:
            delta = obj.diff_against(obj.prev_record)
            return delta.changed_fields
        return []
