import re

from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _

from django.core.exceptions import ValidationError
import magic

from rest_framework import serializers

from accounts.models import Organization

User = get_user_model()


# class CustomPasswordValidator:
#     def __init__(self, min_length=8):
#         self.min_length = min_length

#     def validate(self, password, user=None):
#         regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$"
#         if not re.match(regex, password):
#             raise ValidationError(
#                 _(
#                     "Password must contain at least %(min_length)d characters including uppercase,lowercase and number"
#                 )
#                 % {"min_length": self.min_length}
#             )

#     def get_help_text(self):
#         return _(
#             "Your password must contain at least %(min_length)d characters."
#             % {"min_length": self.min_length}
#         )



class CustomPasswordValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length

    def validate(self, password, user=None):
        # Updated regex to allow special characters
        regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&#])[A-Za-z\d@$!%*?&#]{8,}$"
        if not re.match(regex, password):
            raise ValidationError(
                _(
                    "Password must contain at least %(min_length)d characters, including an uppercase letter, a lowercase letter, a number, and a special character."
                )
                % {"min_length": self.min_length}
            )

    def get_help_text(self):
        return _(
            "Your password must contain at least %(min_length)d characters, including an uppercase letter, a lowercase letter, a number, and a special character."
            % {"min_length": self.min_length}
        )





def phone_number_validator(value):
    print("-----phone_number_validator Calling--------")
    phone = value.replace(" ", "")
    code, number = phone[:3], phone[3:]
    if code != "+44" and code != "+33":
        raise serializers.ValidationError("Phone number must start with +44 or +33")
    if not number.isdigit():
        raise serializers.ValidationError("Phone number should be digits only")
    if len(number) != 10:
        raise serializers.ValidationError(
            "Phone number should be 10 digits long ie. +44 1234567890"
        )


def email_validator(value):
    """
    Check if user with given email already exists
    Args:
        value:
    """
    if User.objects.filter(email=value, is_active=True).exists():
        raise serializers.ValidationError("Email already Exists!")


def organization_code_validator(value):
    if not Organization.objects.filter(code=value).exists():
        raise serializers.ValidationError("Invalid Code")


def validate_file_type(value):
    """
    Validator function to check if the uploaded file is an image or PDF file.
    """
    valid_mime_types = ["image/jpeg", "image/png", "application/pdf"]
    file_mime_type = magic.from_buffer(value.read(1024), mime=True)
    if file_mime_type not in valid_mime_types:
        raise ValidationError(
            _("File type not supported. Only image and PDF files are allowed.")
        )


class CircleFareSerializer(serializers.Serializer):
    per_mile = serializers.DecimalField(decimal_places=2, max_digits=10)
    per_hour = serializers.DecimalField(decimal_places=2, max_digits=10)

    class Meta:
        fields = ["per_mile", "per_hour"]


def validate_circle_fare(value):
    serializer = CircleFareSerializer(data=value)
    serializer.is_valid(raise_exception=True)
    for field in value.keys():
        if field not in ["per_mile", "per_hour"]:
            raise ValidationError(field + " is not defined")
