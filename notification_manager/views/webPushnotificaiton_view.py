import requests
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

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from notification_manager.models import WebPushSubscription
from notification_manager.serializers.webPushnotificaiton_serializer import WebPushSubscriptionSerializer

from notification_manager.webPushNotificaiton_helper import send_web_push_notification_to_single_user

class WebPushSubscriptionManageView(APIView):
    permission_classes = [IsAuthenticated]

    
    def post(self, request):
        """
        Handles WebPushSubscription creation or updating.
        If the same user and endpoint are found, updates the existing object.
        Otherwise, creates a new subscription.
        """
        user = request.user  # Authenticated user from the request
        # endpoint = request.data.get("endpoint")
        id = request.data.get("id")
        subscription = request.data
        print("subscription", subscription)

        # if not endpoint or not id:
        #     return Response(
        #         {"error": "Endpoint is a required field."},
        #         status=status.HTTP_400_BAD_REQUEST,
        #     )

        # Try to find an existing subscription for the user and endpoint
        subscription = WebPushSubscription.objects.filter(id=id, user=user).first()

        if subscription:
            # Update the existing subscription
            serializer = WebPushSubscriptionSerializer(subscription, data=request.data, partial=True)
        else:
            # Create a new subscription without passing 'user' in the data
            serializer = WebPushSubscriptionSerializer(data=request.data)

        if serializer.is_valid():
            # Explicitly set the user for the new subscription or updated subscription
            serializer.save(user=user)
            action = "updated" if subscription else "created"
            return Response(
                {"message": f"Subscription {action} successfully.", "data": serializer.data},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def get(self, request):
        """
        Fetches all WebPushSubscription objects for the authenticated user.
        """
        subscriptions = WebPushSubscription.objects.filter(user=request.user)
        serializer = WebPushSubscriptionSerializer(subscriptions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)








class SendSingleUserPushNotificationAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    
    """
    API View to send push notifications to a single user.

    POST payload example:
    {
        "notification": {
            "title": "New Alert",
            "body": "You have a new message!",
            "icon": "https://example.com/icon.png",
            "url": "https://example.com/notification-click"
        }
    }
    """

    def post(self, request, *args, **kwargs):
        # Extract data from the request
        user_id = request.user.id
        print("user_id", user_id)
        notification_payload = request.data.get("notification")

        if not user_id or not notification_payload:
            return Response(
                {
                    "success": False,
                    "message": "Both 'user_id' and 'notification' are required fields."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Build the payload
        payload = {"notification": notification_payload}

        # Call the notification sending function
        result = send_web_push_notification_to_single_user(user_id, payload)

        # Return the response
        if result["success"]:
            return Response(
                {
                    "success": True,
                    "message": "Notifications processed.",
                    "details": result["results"],
                },
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                {
                    "success": False,
                    "message": "Failed to send notifications.",
                    "error": result.get("error"),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
