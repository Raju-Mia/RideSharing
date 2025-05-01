import googlemaps
from django.conf import settings


# Inport the Google API
gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)



# ===== Get the Distance and Time. =============
def get_distance_and_time(
    origin: tuple[float, float], destination: tuple[float, float]
) -> tuple[float, float] | tuple[None, None]:
    
    print("===========get_distance_and_time Calling ============")
    origin = str(origin[0]) + "," + str(origin[1])
    print("---origin----: ",origin)
    
    destination = str(destination[0]) + "," + str(destination[1])
    print("---destination----: ",destination)
    
    result = gmaps.distance_matrix(
        origins=[origin], destinations=[destination], mode="driving"
    )
    
    print("Google gmaps result: ", result)
    try:
        duration_seconds = result["rows"][0]["elements"][0]["duration"]["value"]
        distance_meters = result["rows"][0]["elements"][0]["distance"]["value"]
    except KeyError:
        return None, None
    return distance_meters, duration_seconds
