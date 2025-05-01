
from rest_framework import serializers
from notification_manager.models import VapidKey


class VapidKeySerializer(serializers.ModelSerializer):
    class Meta:
        model = VapidKey
        fields = ['id', 'public_key', 'private_key', 'created_at']
