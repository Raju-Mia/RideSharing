from location.models import LocationInfo




from .models import LocationInfo

def get_location_info_from_db(place_id):
    """
    Check if the location already exists in the DB.
    Return a dictionary if found, else None.
    """
    try:
        location = LocationInfo.objects.get(place_id=place_id)
        return {
            "lat": location.latitude,
            "lon": location.longitude,
            "name": location.name,
            "address_components": {
                "post_code": location.post_code,
                "route": location.route,
                "city": location.city,
                "country": location.country,
            },
            "address": location.address,
        }
    except LocationInfo.DoesNotExist:
        return None


def save_location_info(
    place_id, name, address, post_code, route,
    city, country, latitude, longitude
):
    """
    Save or update LocationInfo object.
    """
    location, _ = LocationInfo.objects.update_or_create(
        place_id=place_id,
        defaults={
            "name": name,
            "address": address,
            "post_code": post_code,
            "route": route,
            "city": city,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
        }
    )
    return location
