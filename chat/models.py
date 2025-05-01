from django.conf import settings
from django.db import models

from trip_management.models import Trip


class Text(models.Model):
    text = models.TextField()
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT)
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
