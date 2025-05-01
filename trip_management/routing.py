from django.urls import path
# from .consumers import TripTrackingAsyncConsumerForPassenger
from trip_management.consumers import TripRequestConsumer, TripLocationConsumer

websocket_urlpatterns = [
    # path('ws/trip/<uuid:trip_id>/', TripTrackingAsyncConsumerForPassenger.as_asgi()),
    path('ws/trip/<uuid:user_id>/', TripRequestConsumer.as_asgi()),
    path('ws/update-trip-travel-path/<uuid:trip_id>/', TripLocationConsumer.as_asgi()),
    
]
