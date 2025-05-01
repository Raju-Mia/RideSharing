from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


def email_is_valid(email):
    try:
        User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        raise serializers.ValidationError("Invalid Email")
