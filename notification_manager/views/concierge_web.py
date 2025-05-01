

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

import firebase_admin
from firebase_admin import messaging, credentials
from notification_manager.firebase_init import initialize_firebase
initialize_firebase()

from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
User = get_user_model()


import base64  # Add this import
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from pywebpush import webpush, WebPushException
import json
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec



from notification_manager.utils_helper import send_push_notification
from notification_manager.models import VapidKey, FCMToken, NotifyMessage, WebPushSubscription
from notification_manager.serializers.serializers import WebPushSubscriptionSerializer





class TestWebNotificationView(APIView):
    def post(self, request, *args, **kwargs):
        subscription_info = request.data
        # print("Subscription Info:", subscription_info)
        
        # Fetch the VAPID keys from the database
        vapid_key = VapidKey.objects.first()
        if not vapid_key:
            return Response({"error": "VAPID keys not found. Generate them first."}, status=status.HTTP_400_BAD_REQUEST)

        # Extract VAPID keys
        VAPID_PUBLIC_KEY = vapid_key.public_key
        VAPID_PRIVATE_KEY = vapid_key.private_key

        if not subscription_info:
            return Response({"error": "Subscription information is missing."}, status=status.HTTP_400_BAD_REQUEST)
        
        
        # print("Subscription Info:", subscription_info)

        # Validate subscription
        if 'endpoint' not in subscription_info or 'keys' not in subscription_info or \
           'auth' not in subscription_info['keys'] or 'p256dh' not in subscription_info['keys']:
            return Response({"error": "Invalid subscription data."}, status=status.HTTP_400_BAD_REQUEST)

        # Notification payload
        payload = {
            "title": "Test Notification",
            "body": "This is a test push notification!",
            "icon": "https://example.com/icon.png",
            "url": "https://example.com"
        }

        try:
            # Send push notification
            print("Sending push notification...")
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=VAPID_PRIVATE_KEY,
                vapid_claims={"sub":"noreply@projectsolutions.com"},
            )
            return Response({"message": "Notification sent successfully!"}, status=status.HTTP_200_OK)
        except WebPushException as ex:

            print(f"Error sending notification: {str(ex)}")
            return Response({"error": "Failed to send notification.", "details": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)










class WebPushSubscriptionListCreateView(APIView):
    def get(self, request, *args, **kwargs):
        subscriptions = WebPushSubscription.objects.all()
        serializer = WebPushSubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = WebPushSubscriptionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class WebPushSubscriptionDetailView(APIView):
    def get(self, request, pk, *args, **kwargs):
        subscription = get_object_or_404(WebPushSubscription, pk=pk)
        serializer = WebPushSubscriptionSerializer(subscription)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        subscription = get_object_or_404(WebPushSubscription, pk=pk)
        serializer = WebPushSubscriptionSerializer(subscription, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        subscription = get_object_or_404(WebPushSubscription, pk=pk)
        subscription.delete()
        return Response({"message": "Deleted successfully"}, status=status.HTTP_204_NO_CONTENT)



