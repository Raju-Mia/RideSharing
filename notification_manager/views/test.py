

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

from notification_manager.webPushNotificaiton_helper import (
    send_web_push_notification_to_single_user,
    )






class WebPushSingleUserNotification(APIView):
    permission_classes = [IsAuthenticated]
    
    """
    API View to send a web push notification to a single user.
    """
    
    def post(self, request, *args, **kwargs):
        # Get the user ID of the current authenticated user
        user_id = request.user.id
        print("user id is: ", user_id)

        # Notification payload
        payload = {
            "notification": {
                "title": "Test Notification",
                "body": "This is a test push notification!",
                "icon": "https://example.com/icon.png",  # Ensure this is a valid URL
                "url": "https://example.com"            # Ensure this is a valid URL
            }
        }


        try:
            # Send push notification to the user
            response = send_web_push_notification_to_single_user(user_id, payload)
            print("response is: ", response)

            if response.get("success"):
                return Response(
                    {"message": response.get("message", "Notification sent successfully!")},
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    {"error": response.get("error", "Failed to send notification.")},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as ex:
            print(f"Error sending notification: {str(ex)}")
            return Response(
                {"error": "Failed to send notification.", "details": str(ex)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
