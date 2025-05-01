import asyncio
import json
from channels.generic.websocket import AsyncWebsocketConsumer, AsyncJsonWebsocketConsumer
from asgiref.sync import sync_to_async
from .models import Trip, TripStatus
from django.db import connection
from channels.db import database_sync_to_async
from django.utils import timezone
import logging
logger = logging.getLogger(__name__)
# class TripTrackingAsyncConsumerForPassenger(AsyncWebsocketConsumer):
#     async def connect(self):
#         self.user = self.scope['user']
        
#         if not self.user.is_authenticated:
#             await self.close()
#             return
        
#         self.trip_id = self.scope['url_route']['kwargs']['trip_id']
#         self.room_group_name = f'trip_{self.trip_id}'

#         await self.channel_layer.group_add(
#             self.room_group_name,
#             self.channel_name
#         )

#         await self.accept()

#         trip_data = await get_trip_data(self.trip_id)
#         if trip_data:
#             await self.send(text_data=json.dumps({
#                 'type': 'trip_data',
#                 'data': trip_data
#             }))

#     async def trip_update(self, event):
#         trip_data = event['trip_data']
#         await self.send(text_data=json.dumps({
#             'type': 'trip_update',
#             'data': trip_data
#         }))




class TripRequestConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'driver_trip_{self.user_id}'        
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()
    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.close_database_connection() 
    @database_sync_to_async
    def close_database_connection(self):
        from django.db import connection
        connection.close() 
    async def ping(self):
        while True:
            await asyncio.sleep(30)
            await self.send(text_data="ping")
    async def receive_json(self, content):
        message_type = content.get('type', 'broadcast_trip_message')        
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': message_type,
                'content': content,
            }
        )
    async def broadcast_trip_message(self, event):
        await self.send_json({
            'type': 'broadcast_trip_message',
            'content': event.get('content'),
        })
    async def trip_update(self, event):
        await self.send_json({
            'type': 'trip_update',
            'content': event.get('content'),
        })
    async def delete_trip_message(self, event):
        await self.send_json({
            'type': 'delete_trip_message',
            'trip_id': event.get('trip_id'),
            'message': 'Delete existing messages for the trip.',
        })



class TripLocationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.trip_id = self.scope['url_route']['kwargs']['trip_id']
        self.room_group_name = f'trip{self.trip_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        await self.close_database_connection() 
    @database_sync_to_async
    def close_database_connection(self):
        from django.db import connection
        connection.close() 

    async def ping(self):
        while True:
            await asyncio.sleep(30)
            await self.send(text_data="ping")

    async def receive(self, text_data):
        data = json.loads(text_data)
        lat = data.get('latitude')
        lng = data.get('longitude')
        current_time = timezone.now().isoformat()

        await self.update_trip_travel_path(lat, lng, current_time)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'trip_message',
                'latitude': lat,
                'longitude': lng,
                'timestamp': current_time
            }
        )

    async def trip_message(self, event):
        await self.send(text_data=json.dumps({
            'latitude': event['latitude'],
            'longitude': event['longitude'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def get_trip(self):
        return Trip.objects.get(id=self.trip_id)

    async def update_trip_travel_path(self, latitude, longitude, timestamp):
        try:
            trip = await self.get_trip()
            logger.info(f"Trip Status: {trip.trip_status}") 
            if trip.trip_status not in self.allowed_statuses():
                return

            await self._update_path(trip, latitude, longitude, timestamp)
        except Trip.DoesNotExist:
            pass

    @staticmethod
    def allowed_statuses():
        return {
            TripStatus.OFF_TO_PICKUP,
            TripStatus.WAITING,
            TripStatus.IN_PROGRESS,
            TripStatus.BREAK,
            TripStatus.RETURN_IN_PROGRESS,
            TripStatus.PROCESSING_PAYMENT
        }

    @database_sync_to_async
    def _update_path(self, trip, latitude, longitude, timestamp):
        if not isinstance(trip.travel_path, list):
            trip.travel_path = []

        trip.travel_path.append({
            'lat': latitude,
            'lng': longitude,
            'trip_status': trip.trip_status,
            'timestamp': timestamp
        })
        trip.save()