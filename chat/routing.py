from django.urls import path
from . import consumers


websocket_urlpatterns = [
    path("chat/<uuid:trip_id>/", consumers.ChatConsumer.as_asgi()),
]
