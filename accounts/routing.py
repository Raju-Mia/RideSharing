from django.urls import path
from .consumers import *


websocket_urlpatterns = [
    # path("notification/", NotificationConsumer.as_asgi()),
    # path("driver-assignment/", DriverAssignRequestConsumer.as_asgi()),

    path('ws/user-status/', TrackUserLocationAndStatusConsumer.as_asgi()),
]
