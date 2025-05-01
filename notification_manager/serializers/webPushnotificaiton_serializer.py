from rest_framework import serializers
from notification_manager.models import WebPushSubscription



class WebPushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebPushSubscription
        fields = [
            "id",
            "endpoint",
            "p256dh",
            "auth",
            "browser_name",
            "operating_systems",
            "device_type",
            "device_model",
            "device_os_version",
            "device_vendor",
            "device_id",
            "pv4_address",
            "IP_location",
            "user_agent",
            "device_location_latitude",
            "device_location_longitude",
            "notification_enabled",
            # "last_active",
            # "active_status",
            # "block_status",
            # "verification_required",
            # "verification_status",
            # "status",
            
        ]
