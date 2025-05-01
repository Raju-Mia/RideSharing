import asyncio
import httpx
from uc_back import settings
from asgiref.sync import sync_to_async
from .models import Trip, DeclineTrip, TripStatus, DeclinedByStatus
from decimal import Decimal
import googlemaps
import logging
from shapely.geometry import Point
from trip_management.polygons import POLYGONS
from channels.layers import get_channel_layer
from django.db import transaction
from django.contrib.auth import get_user_model
User = get_user_model()
api_key = settings.GOOGLE_API_KEY
# gmaps = googlemaps.Client(key=api_key)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)






async def calculate_distance_and_time_async(lat1, lng1, lat2, lng2):
    """ Asynchronous distance and time calculation using Google Maps Distance Matrix API. """
    if not api_key:
        raise ValueError("Google Maps API key not found.")

    url = (
        f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial"
        f"&origins={lat1},{lng1}&destinations={lat2},{lng2}&key={api_key}"
    )
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    
    if response.status_code != 200:
        return None, None

    data = response.json()
    try:
        elements = data["rows"][0]["elements"][0]
        if "distance" in elements and "duration" in elements:
            distance = elements["distance"]["value"]
            time = elements["duration"]["value"]
            distance_miles = distance / 1609.34
            time_minutes = time / 60
            return round(distance_miles, 2), round(time_minutes, 2)
        else:
            return None, None
    except (KeyError, IndexError):
        return None, None
    




def run_schedule_deletion(user_id, trip_id):
    # Check the trip status before scheduling deletion
    try:
        trip = Trip.objects.get(id=trip_id)
        if trip.trip_status in [TripStatus.APPROVED_BY_DRIVER, TripStatus.REQUESTED]:
            print(f"Skipping schedule deletion for trip {trip_id}, status: {trip.trip_status}")
            return
    except Trip.DoesNotExist:
        print(f"Trip {trip_id} does not exist. No action taken.")
        return

    asyncio.run(schedule_deletion(user_id, trip_id))


async def schedule_deletion(user_id, trip_id):
    try:
        await asyncio.sleep(180)

        trip = await sync_to_async(Trip.objects.get)(id=trip_id)

        if trip.trip_status == "Pending":
            user = await sync_to_async(User.objects.get)(id=user_id)            
            @sync_to_async
            def update_trip_and_create_decline():
                with transaction.atomic():
                    trip.trip_status = TripStatus.REQUESTED
                    DeclineTrip.objects.create(
                        trip=trip,
                        user=user,
                        decline_reason="No Response",
                        declined_by=DeclinedByStatus.System,
                    )
                    trip.driver = None
                    trip.save()

            await update_trip_and_create_decline()

            channel_layer = get_channel_layer()
            room_group_name = f'driver_trip_{user_id}'
            await channel_layer.group_send(
                room_group_name,
                {
                    'type': 'delete_trip_message',
                    'trip_id': str(trip_id),
                }
            )
        else:
            print(f"Trip {trip_id} already has an action taken.")
    except Trip.DoesNotExist:
        print(f"Trip {trip_id} does not exist. No action taken.")
    except Exception as e:
        print(f"Error in async deletion scheduling: {str(e)}")


def run_immediate_deletion(user_id, trip_id):
    asyncio.run(immediate_deletion(user_id, trip_id))

async def immediate_deletion(user_id, trip_id):
    try:
        trip = await sync_to_async(Trip.objects.select_related('user').get)(id=trip_id)
        user = await sync_to_async(User.objects.get)(id=user_id)
        channel_layer = get_channel_layer()
        room_group_name = f'driver_trip_{user_id}'


        message = {
                'type': 'delete_trip_message',
                'trip_id': str(trip_id),
                'trip_status': str(trip.trip_status)
        }

        await channel_layer.group_send(room_group_name, message)

    except Trip.DoesNotExist:
        print(f"Immediate Deletion Error: Trip {trip_id} does not exist.")
    except Exception as e:
        print(f"Unexpected Error in Immediate Deletion: {str(e)}")
