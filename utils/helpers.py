import random
import string

import requests

from uc_back import settings


def generate_otp() -> str:
    """
    Generate 6 digits random number.
    Returns: string containing 6 digit random number
    """
    return "".join(random.choices(string.digits, k=6))


def get_dvla_data_for_vehicle(registration_number):
    """
    Get DVLA data using the registration number.
    Returns: DVLA data in JSON format

    """
    url = settings.DVLA_URL
    payload = {"registrationNumber": registration_number}
    headers = {"x-api-key": settings.DVLA_API_KEY, "Content-Type": "application/json"}

    try:
        timeout = 5  # You can adjust this value based on your requirements
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if response.status_code == 200:
            return True, response.json()

        elif response.status_code == 404:
            return False, {"error": "Vehicle Not Found"}
        elif response.status_code == 400:
            return False, {"error": "Bad Request"}
        elif response.status_code == 500:
            return False, {"error": "Internal Server Error"}
        else:
            return False, {"error": "Service Unavailable"}
    except requests.RequestException as e:
        return False, {"error": str(e)}


Int_Month_To_String = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}

String_Month_To_Int = {
    "January": 1,
    "February": 2,
    "March": 3,
    "April": 4,
    "May": 5,
    "June": 6,
    "July": 7,
    "August": 8,
    "September": 9,
    "October": 10,
    "November": 11,
    "December": 12,
}

Months_Of_An_Year = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]




