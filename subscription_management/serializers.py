import datetime
from rest_framework import serializers, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now



from rest_framework import serializers
from django.conf import settings
import stripe
from subscription_management.models import DriverSubscription, SubscriptionPlan, Coupon, DriverTransaction
from django.utils import timezone

import stripe
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# Stripe Account Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY
import time




# Coupon Serializer
class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'

# SubscriptionPlan Serializer
# class SubscriptionPlanSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = SubscriptionPlan
#         fields = '__all__'



class SubscriptionPlanSerializer(serializers.ModelSerializer):
    sub_status = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = '__all__'  # keep this as is

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['sub_status'] = self.get_sub_status(instance)
        return representation

    def get_sub_status(self, obj):
        user = self.context['request'].user
        if user and user.is_authenticated:
            return DriverSubscription.objects.filter(
                driver=user,
                package=obj,
                is_active=True,
                status=True
            ).exists()
        return False




class CreateSubscriptionSerializer(serializers.ModelSerializer):
    package_id = serializers.PrimaryKeyRelatedField(
        queryset=SubscriptionPlan.objects.all(), source='package'
    )
    duration_day = serializers.IntegerField(write_only=True, required=True)  # Required field


    class Meta:
        model = DriverSubscription
        fields = ['package_id', 'duration_day']  # Use package_id instead of package



class ActivateSubscriptionSerializer(serializers.Serializer):
    stripe_payment_intent_id = serializers.CharField()



class SubscriptionSerializer(serializers.ModelSerializer):
    package_title = serializers.CharField(source='package.title', read_only=True)

    class Meta:
        model = DriverSubscription
        fields = ['id', 'package_title', 'start_date', 'end_date', 'total_days', 'total_price', 'is_active', 'status']


class TransactionSerializer(serializers.ModelSerializer):
    subscription_title = serializers.CharField(source='subscription.package.title', read_only=True)

    class Meta:
        model = DriverTransaction
        fields = ['id', 'subscription_title', 'amount', 'payment_status', 'transaction_category', 'created_at']
