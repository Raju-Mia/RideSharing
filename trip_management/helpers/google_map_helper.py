import requests
from shapely.geometry import Point, Polygon

from location.helpers import get_location_info_from_db, save_location_info
from uc_back import settings
from trip_management.polygons import POLYGONS, ZONE_ORDER, CONGESTION_ZONE
from trip_management.helpers.api_helpes import plain_text_from_html

import polyline
from geopy.distance import distance


def fetch_location_information_from_place_id_using_google_map_api(place_id):
    # First: check if data already exists in DB
    existing_data = get_location_info_from_db(place_id)
    if existing_data:
        return existing_data

    # Otherwise: call Google Maps API
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("Google Maps API key not found.")

    url = f"https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&key={api_key}"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": "Failed to fetch data from Google Places API"}

    data = response.json()
    if "result" not in data:
        return {"error": "Invalid place_id or no data found"}

    result = data["result"]
    location_name = result.get("name", "")
    latitude = result.get("geometry", {}).get("location", {}).get("lat")
    longitude = result.get("geometry", {}).get("location", {}).get("lng")
    address = plain_text_from_html(result["adr_address"])

    post_code = ""
    route = []
    city = ""
    country = ""

    for component in result.get("address_components", []):
        if "postal_code" in component["types"]:
            post_code = component["long_name"]
        elif "route" in component["types"]:
            route.append(component["long_name"])
        elif "postal_town" in component["types"]:
            city = component["long_name"]
        elif "administrative_area_level_2" in component["types"] and not city:
            city = component["long_name"]
        elif "country" in component["types"]:
            country = component["long_name"]

    # Save to DB
    save_location_info(place_id=place_id,name=location_name,address=address,post_code=post_code,route=route,city=city,country=country,latitude=latitude,longitude=longitude)

    return {
        "lat": latitude,
        "lon": longitude,
        "name": location_name,
        "address_components": {
            "post_code": post_code,
            "route": route,
            "city": city,
            "country": country,
        },
        "address": address,
    }

def calculate_distance_and_time(lat1, lng1, lat2, lng2):
    """
    Calculates distance (in miles) and time (in minutes) between two locations using Google Maps Distance Matrix API.
    """

    api_key = settings.GOOGLE_API_KEY

    if not api_key:
        raise ValueError("Google Maps API key not found.")

    url = (
        f"https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial"
        f"&origins={lat1},{lng1}&destinations={lat2},{lng2}&key={api_key}"
    )
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception(
            f"Failed to fetch distance and time. Status Code: {response.status_code}"
        )

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
    except (KeyError, IndexError) as e:
        return None, None


def get_zone(lat, lon):
    """Return the smallest zone containing the point, or 'Out of Zone' if none."""
    point = Point(lon, lat)
    for zone_name, poly in POLYGONS.items():
        if poly.contains(point):
            return zone_name
    return "OUT_OF_ZONE"

def calculate_route_segments(lat1, lon1, lat2, lon2):
    """Calculate distance and time per zone along the route."""
    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("Google Maps API key not found.")

    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={lat1},{lon1}&destination={lat2},{lon2}&key={api_key}"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch directions. Status: {response.status_code}")
    data = response.json()
    if data["status"] != "OK":
        raise Exception(f"Directions API error: {data['status']}")

    route = data["routes"][0]
    legs = route["legs"]
    small_segments = []

    for leg in legs:
        steps = leg["steps"]
        for step in steps:
            points = polyline.decode(step["polyline"]["points"])
            step_distance_meters = step["distance"]["value"]
            step_duration_seconds = step["duration"]["value"]

            for i in range(len(points) - 1):
                p1 = points[i]
                p2 = points[i + 1]
                d_meters = distance(p1, p2).meters
                mid_lat = (p1[0] + p2[0]) / 2
                mid_lon = (p1[1] + p2[1]) / 2
                zone = get_zone(mid_lat, mid_lon)
                if zone is None:
                    continue
                t_seconds = (d_meters / step_distance_meters) * step_duration_seconds if step_distance_meters > 0 else 0
                small_segments.append((zone, d_meters, t_seconds))

    # Group segments by zone
    segments = []
    if small_segments:
        current_zone = small_segments[0][0]
        current_distance = small_segments[0][1]
        current_time = small_segments[0][2]

        for zone, d, t in small_segments[1:]:
            if zone == current_zone:
                current_distance += d
                current_time += t
            else:
                segments.append({
                    "zone": current_zone,
                    "distance_miles": round(current_distance / 1609.34, 2),
                    "time_minutes": round(current_time / 60, 2)
                })
                current_zone = zone
                current_distance = d
                current_time = t

        segments.append({
            "zone": current_zone,
            "distance_miles": round(current_distance / 1609.34, 2),
            "time_minutes": round(current_time / 60, 2)
        })
    total_distance = sum(seg["distance_miles"] for seg in segments)
    total_time = sum(seg["time_minutes"] for seg in segments)
    return {
        "total_distance_miles": round(total_distance, 2),
        "total_time_minutes": round(total_time, 2),
        "segments": segments
        }

def is_in_congestion_zone(lat, lng):
    """
    Check if a given latitude and longitude falls within the congestion zone.
    """
    point = Point(lat, lng)
    result = CONGESTION_ZONE.contains(point)
    return result