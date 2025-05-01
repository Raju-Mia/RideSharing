import json
import requests


def calculate_distance(location1, location2):
    """
    Calculates distance between two locations.
    """
    location1 = location1.replace(" ", "").strip()
    location2 = location2.replace(" ", "").strip()
    url = (
        "https://maps.googleapis.com/maps/api/distancematrix/json?units=imperial&origins="
        + location1
        + "&destinations="
        + location2
        + "&key=AIzaSyAKSPz1gj2oXdJ9Usl9x_dlBrYA_6PdsO4"
    )
    response = requests.get(url)
    data = json.loads(response.text)
    try:
        distance = data["rows"][0]["elements"][0]["distance"]["value"]
        time = data["rows"][0]["elements"][0]["duration"]["value"]
        return distance, time
    except:
        return None





