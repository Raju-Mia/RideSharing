import datetime
import re

from django.utils import timezone

from rest_framework import serializers


def validate_trip_date_time(value: datetime.datetime) -> None:
    if value < timezone.now():
        raise serializers.ValidationError("Can not be past date time")


def file_size_validator(value) -> None:
    limit = 12 * 1024 * 1024
    if value.size > limit:
        raise serializers.ValidationError(
            "File too large. Size should not exceed 2 MiB."
        )


def image_extension_validator(value) -> None:
    allowed_types = [
        "image/jpeg",
        "image/jpg",
        "image/webp",
        "image/JPG",
        "image/JPEG",
        "image/WEBP",
    ]
    if value.content_type not in allowed_types:
        raise serializers.ValidationError("This image type is not allowed")


def file_extension_validator(value):
    allowed_types = [
        "image/jpeg",
        "image/jpg",
        "image/webp",
        "image/JPG",
        "image/JPEG",
        "image/WEBP",
        "application/pdf",
    ]
    if value.content_type not in allowed_types:
        raise serializers.ValidationError("This file type is not allowed")


def password_validator(value):
    """
    Validate that the password meets all the following criteria:
      - At least 8 characters long
      - Contains at least one uppercase letter
      - Contains at least one lowercase letter
      - Contains at least one digit
      - Contains at least one special character from @$!%*?&
    """
    if len(value) < 8:
        raise serializers.ValidationError("Password must be at least 8 characters long.")

    if not re.search(r'[A-Z]', value):
        raise serializers.ValidationError("Password must contain at least one uppercase letter.")

    if not re.search(r'[a-z]', value):
        raise serializers.ValidationError("Password must contain at least one lowercase letter.")

    if not re.search(r'\d', value):
        raise serializers.ValidationError("Password must contain at least one digit.")

    if not re.search(r'[@$!%*?&]', value):
        raise serializers.ValidationError("Password must contain at least one special character (e.g., @$!%*?&).")

    return value


def validate_phone_number(value):
    # Check if the phone number starts with the country code for Bangladesh or England
    if not value.startswith(("+880", "+44")):
        raise serializers.ValidationError("Invalid phone number")

    # Check the length of the phone number based on the country code and validate format
    if value.startswith("+880"):  # +880 is the country code for Bangladesh
        if len(value) != 14 or not value[1:].isdigit():
            raise serializers.ValidationError("Invalid phone number")

    elif value.startswith("+44"):  # +44 is the country code for England
        if len(value) != 13 or not value[1:].isdigit():
            raise serializers.ValidationError("Invalid phone number")

    else:
        raise serializers.ValidationError("Invalid phone number")
