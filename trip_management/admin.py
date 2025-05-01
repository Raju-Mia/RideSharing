from django.contrib import admin
from .models import (Trip, ExtraCharge, TripBreak, DeclineTrip, 
                     CancelTrip, ExtraChargePicture, BookingFeeSchedule,
                     )
# Register your models here.


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('id','unique_id', 'user', 'driver', 'trip_method', 'is_instant_trip', 'booking_time', 'pickup_time', 'booking_time', 'trip_status')
    list_filter = ('user','unique_id', 'trip_method', 'is_instant_trip', 'booking_time')
    search_fields = ('user__email','unique_id', 'trip_method', 'booking_time','id')
    ordering = ('-booking_time',)
    readonly_fields = ('id',)

@admin.register(ExtraCharge)
class ExtraChargeAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'charge_amount', 'charge_type', 'charge_reason')
    list_filter = ('trip', 'charge_type')
    search_fields = ('trip__id', 'charge_type', 'charge_reason')

@admin.register(TripBreak)
class TripBreakAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'start_time', 'end_time', 'break_location_name')
    list_filter = ('trip', 'start_time', 'end_time')
    search_fields = ('trip__id', 'break_location_name')


@admin.register(DeclineTrip)
class DeclineTripAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'decline_reason', 'declined_by')
    list_filter = ('trip', 'decline_reason', 'declined_by')

@admin.register(CancelTrip)
class CancelTripAdmin(admin.ModelAdmin):
    list_display = ('id', 'trip', 'cancel_reason', 'canceled_by')

@admin.register(ExtraChargePicture)
class ExtraChargePictureAdmin(admin.ModelAdmin):
    list_display = ('id',)
    list_filter = ('id',)
    search_fields = ('id',)


@admin.register(BookingFeeSchedule)
class BookingFeeScheduleAdmin(admin.ModelAdmin):
    list_display = ('start_time', 'end_time', 'airport_transfer_fee', 'one_way_fee', 
                   'round_trip_fee', 'as_directed_fee', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('start_time', 'end_time')
