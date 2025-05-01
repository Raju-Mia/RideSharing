from django.shortcuts import render
from django.core.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from utils.pagination import CustomPageNumberPagination

import firebase_admin
from firebase_admin import messaging, credentials
from notification_manager.firebase_init import initialize_firebase
initialize_firebase()


from pywebpush import webpush, WebPushException
import json
from django.db import IntegrityError

from notification_manager.models import VapidKey, FCMToken, NotifyMessage, WebPushSubscription
from django.contrib.auth import get_user_model
User = get_user_model()




class DriverAppToAdministrationWebPushNotification(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user

        # Fetch the latest WebPushSubscription object for the user
        try:
            latest_subscription = WebPushSubscription.objects.filter(user=user).latest("created_at")
            if not latest_subscription:
                return Response({"error": "No active subscription found for this user."}, status=status.HTTP_404_NOT_FOUND)
        except WebPushSubscription.DoesNotExist:
            return Response({"error": "No subscription found for this user."}, status=status.HTTP_404_NOT_FOUND)

        subscription_info = {
            "endpoint": latest_subscription.endpoint,
            "keys": {
                "p256dh": latest_subscription.p256dh,
                "auth": latest_subscription.auth
            }
        }
        
        print("Subscription Info:", subscription_info)

        # Fetch the VAPID keys from the database
        vapid_key = VapidKey.objects.first()
        if not vapid_key:
            return Response({"error": "VAPID keys not found. Generate them first."}, status=status.HTTP_400_BAD_REQUEST)

        # Notification payload
        payload = request.data.get("payload", {})
        if not payload or "title" not in payload or "body" not in payload:
            return Response({"error": "Invalid payload data."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Send push notification
            webpush(
                subscription_info=subscription_info,
                data=json.dumps(payload),
                vapid_private_key=vapid_key.private_key,
                vapid_claims={"sub": "mailto:noreply@projectsolutions.com"},
            )
            return Response({"message": "Notification sent successfully!"}, status=status.HTTP_200_OK)
        except WebPushException as ex:
            return Response({"error": "Failed to send notification.", "details": str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
