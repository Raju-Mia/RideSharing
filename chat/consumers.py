import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from django.utils import timezone
from rest_framework.generics import get_object_or_404

from trip_management.models import Trip
from .models import Text
from .serializers import TextSerializer


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        if self.scope["user"].is_anonymous:
            self.close()
        self.user = self.scope["user"]
        trip_id = self.scope["url_route"]["kwargs"]["trip_id"]
        self.trip = get_object_or_404(Trip, id=trip_id)
        if self.trip is None:
            self.close()
        if self.trip.user != self.user and self.trip.driver.user != self.user:
            self.close()
        self.group_name = str(self.trip.id)
        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        self.accept()
        self.send_previous_texts()

    def disconnect(self, close_code):
        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    # Receive message from WebSocket
    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        Text.objects.create(trip=self.trip, sender=self.user, text=message)
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            {
                "type": "chat_message",
                "message": message,
            },
        )

    # Receive message from room group
    def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        self.send(
            text_data=json.dumps(
                {
                    "message": message,
                    "sender": str(self.user.id),
                    "created_at": str(timezone.now()),
                }
            )
        )

    def send_previous_texts(self):
        data = self.trip.text_set.all().order_by("created_at")
        serializer = TextSerializer(data, many=True)
        self.send(text_data=json.dumps({"messages": serializer.data}))
