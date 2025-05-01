
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from urllib.parse import parse_qs
# from .models import Notification
import asyncio
# from .serializers import NotificationSerializerForSocket
import json
import datetime
from channels.generic.websocket import AsyncWebsocketConsumer, WebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from jwt import decode as jwt_decode
from django.conf import settings
from django.db import connection
from .helpers import haversine_distance
from driver_app.models import Driver
from trip_management.models import Trip, TripStatus
User = get_user_model()


@database_sync_to_async
def get_user(token):
    try:
        decoded_data = jwt_decode(
            token, settings.SECRET_KEY, algorithms=["HS256"])
    except Exception as e:
        print(f"Token decode error: {e}")
        return AnonymousUser()

    try:
        token_type = decoded_data["token_type"]
    except KeyError:
        return AnonymousUser()

    if token_type != "websocket":
        return AnonymousUser()

    try:
        user = User.objects.get(id=decoded_data["user_id"])
    except User.DoesNotExist:
        return AnonymousUser()

    return user


class TrackUserLocationAndStatusConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.user = self.scope["user"]

        print(f"User object: {self.user}")
        print(f"Is user authenticated? {self.user.is_authenticated}")

        if self.user.is_authenticated:
            print("Authenticated user")
            await self.channel_layer.group_add(
                "user_status",
                self.channel_name
            )
            await self.accept()
            await self.broadcast_status()
        else:
            print("User is not authenticated.")
            await self.close()

    async def receive(self, text_data):
        if not self.user.is_authenticated:
            await self.close()
            return

        data = json.loads(text_data)
        if 'latitude' in data and 'longitude' in data:
            latitude = data['latitude']
            longitude = data['longitude']
            is_online = data['is_online']

            await self.update_user_location_and_status(latitude, longitude, is_online)

            await self.send(text_data=json.dumps({
                "user_id": str(self.user.id),
                "username": self.user.username,
                "full_name": self.user.full_name,
                "latitude": self.user.latitude,
                "longitude": self.user.longitude,
                "is_online": self.user.is_online
            }))

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.update_user_status(False)
            await self.broadcast_status()

            await self.send(text_data=json.dumps({
                "user_id": str(self.user.id),
                "username": self.user.username,
                "full_name": self.user.full_name,
                "is_online": self.user.is_online
            }))
            await self.channel_layer.group_discard(
                "user_status",
                self.channel_name
            )
        await self.close_database_connection() 
    @database_sync_to_async
    def close_database_connection(self):
        from django.db import connection
        connection.close() 

    async def ping(self):
        while True:
            await asyncio.sleep(10)
            await self.send(text_data="ping")

    @database_sync_to_async
    def update_user_status(self, is_online):
        if self.user.is_authenticated:
            self.user.is_online = is_online
            self.user.last_activity = timezone.now()
            self.user.save()

    @database_sync_to_async
    def update_user_location_and_status(self, latitude, longitude, is_online):
        if self.user.is_authenticated:
            self.user.latitude = latitude
            self.user.longitude = longitude
            self.user.is_online = is_online
            self.user.last_location_update = timezone.now()


            self.user.save()


    async def broadcast_status(self):
        if self.user.is_authenticated:
            await self.channel_layer.group_send(
                "user_status",
                {
                    "type": "user_status_update",
                    "user_id": str(self.user.id),
                    "username": self.user.username,
                    "full_name": self.user.full_name,
                    "is_online": self.user.is_online,
                }
            )

    async def user_status_update(self, event):
        await self.send(text_data=json.dumps(event))

