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

from notification_manager.utils_helper import send_push_notification
from notification_manager.models import FCMToken, NotifyMessage

from django.contrib.auth import get_user_model
User = get_user_model()

from notification_manager.serializers.serializers import NotifyMessageSerializer



class GetAllNotifications(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination  # Your custom pagination class

    def get(self, request, *args, **kwargs):
        user = request.user
        notifications = NotifyMessage.objects.filter(user=user).order_by('-created_at')
        paginator = CustomPageNumberPagination()
        
        # Paginate the queryset
        page = paginator.paginate_queryset(notifications, request)
        
        if page is not None:
            serializer = NotifyMessageSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        # If no pagination is needed, return the full dataset
        serializer = NotifyMessageSerializer(notifications, many=True)
        return Response(serializer.data)
    



class UserReadNotification(APIView):     # user means they can driver or client
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        notification_id = self.kwargs.get('notification_id')
        try:
            notification = NotifyMessage.objects.get(id=notification_id, user=request.user)
        except NotifyMessage.DoesNotExist:
            return Response({'error': 'Notification not found.'}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save()

        return Response({'message': 'Notification marked as read.'}, status=status.HTTP_200_OK)