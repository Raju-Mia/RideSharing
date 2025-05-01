from django.contrib import admin

from .models import LocationInfo

@admin.register(LocationInfo)
class LocationInfoAdmin(admin.ModelAdmin):
    list_display = ('name', 'place_id', 'city', 'country', 'latitude', 'longitude')
    search_fields = ('place_id', 'name', 'city', 'country')
