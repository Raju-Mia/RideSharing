from django.shortcuts import render
from django.core.exceptions import ValidationError

from rest_framework.permissions import IsAuthenticated


# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


import firebase_admin
from firebase_admin import messaging, credentials
from notification_manager.firebase_init import initialize_firebase
initialize_firebase()

from notification_manager.utils_helper import send_push_notification
from notification_manager.models import FCMToken, NotifyMessage

from django.contrib.auth import get_user_model
User = get_user_model()



class CreateFCMTokenView(APIView):
    permission_classes = [IsAuthenticated]
    """
    API view to create or update an FCM token for a user.
    """

    def post(self, request, *args, **kwargs):
        user = request.user
        print("User is: ", user)
        fcm_token = request.data.get('fcm_token')
        print("fcm_token: ", fcm_token)

        if not fcm_token:
            print(" i am here---1")
            return Response({"error": "FCM token is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Save or update the FCM token
        FCMToken.objects.update_or_create(user=user, defaults={'fcm_token': fcm_token})

        return Response({"message": "FCM token created/updated successfully"}, status=status.HTTP_200_OK)



class SendPushNotificationView(APIView):
    permission_classes = [IsAuthenticated]
    """
    API view to send a push notification to a single device.
    """

    def post(self, request, *args, **kwargs):
        user = request.user
        print("I AM EXAMPLE 2 ")
        try:
            print(" i am here---1")
            fcm_token = FCMToken.objects.get(user=user).fcm_token
            print(" i am here---2")
        except FCMToken.DoesNotExist:
            print(" i am here---3")
            return Response({"error": "FCM token not found for the user"}, status=status.HTTP_404_NOT_FOUND)
        print(" i am here---4")
        # Create the message payload
        message = messaging.Message(
            notification=messaging.Notification(
                title="Hello!",
                body="This is a test notification.",
            ),
            token=fcm_token,
        )

        try:
            # Send the notification
            response = messaging.send(message)
            return Response({"message": "Notification sent successfully", "response": response}, status=status.HTTP_200_OK)
        except firebase_admin._messaging_utils.ApiCallError as e:
            return Response({"error": "Failed to send notification", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# Single Notification Send to User
class SingleUserPushNotificationSend(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        print("hellow, ")
        sender = request.user
        print("hello--")
        user_id = request.data.get('user_id')
        print("user_id", user_id)
        title = request.data.get('title', '')
        content = request.data.get('content', '')
        
        try:
            user = User.objects.get(id=user_id)
            print("the user is : ", user)
            NotifyMessage.objects.create(user=user, title=title, content=content)
            send_push_notification(user, title, content)
            return Response({"message": "Push Notification Message sent successfully"}, status=status.HTTP_201_CREATED)
        except User.DoesNotExist:
            return Response({"error": "Receiver not found"}, status=status.HTTP_404_NOT_FOUND)




# Malti User Notification Send 
class MultiUserPushNotificationSend(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        sender = request.user
        
        user_ids = request.data.get('user_ids', [])
        title = request.data.get('title', '')
        content = request.data.get('content', '')
        
        if not user_ids:
            return Response({"error": "No receivers specified"}, status=status.HTTP_400_BAD_REQUEST)
        
        for user_id in user_ids:
            try:
                user = User.objects.get(id=user_id)
                NotifyMessage.objects.create(user=user, title=title, content=content)
                send_push_notification(user, title, content)
            except User.DoesNotExist:
                continue
        
        return Response({"message": "Push Notification Messages sent successfully"}, status=status.HTTP_201_CREATED)



