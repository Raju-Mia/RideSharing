from django.db import models

# Create your models here.
class LocationInfo(models.Model):
    """Model to store location information from Google Maps API"""
    place_id = models.CharField(max_length=255, unique=True, primary_key=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    name = models.CharField(max_length=255, blank=True)
    route = models.TextField(blank=True)
    post_code = models.CharField(max_length=20, blank=True)
    city = models.CharField(max_length=255, blank=True)
    country = models.CharField(max_length=255, blank=True)
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.place_id})"