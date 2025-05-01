

from rest_framework import serializers
from accounts.validators import email_validator

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from notification_manager.models import NotifyMessage, WebPushSubscription



from django.contrib.auth import get_user_model
User = get_user_model()

#Import
from organization_manager.models import Organization


class NotifyMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotifyMessage
        fields = "__all__"
        
        
        


class WebPushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WebPushSubscription
        fields = '__all__'
