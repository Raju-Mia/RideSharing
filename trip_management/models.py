from django.db import models
from uc_back import settings
import uuid
from accounts.models import CustomUser
from django.core.exceptions import ValidationError
from driver_app.models import (
    Driver,
    DriverStatus,
    # DriverAttachmentStatus,
    # Manufacturer,
    Vehicle,
    VehicleModel,
    VehicleStatus,
    VehicleTypes,
    # VehicleTypesInfo,
    AttachmentStatus,
)
from decimal import Decimal

from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
from simple_history.models import HistoricalRecords
from django.utils import timezone
from uc_back import settings
from django.contrib.postgres.fields import ArrayField
import secrets
import string
from accounts.models import Services
# Create your models here.




class TripStatus(models.TextChoices):
    IN_PROGRESS = "IN_PROGRESS"  # Driver has started the trip
    REQUESTED = "REQUESTED"  # Client has requested a trip
    PENDING = "PENDING"  # Client has pendign a trip
    
    APPROVED_BY_DRIVER = "APPROVED_BY_DRIVER"  # Driver has approved the trip
    WAITING = "WAITING"  # driver is waiting for passenger to drive
    OFF_TO_PICKUP = "OFF_TO_PICKUP"  # Driver is on the way to pickup location

    HALFWAY_COMPLETED = "HHALFWAY_COMPLETED"  # Driver has completed the first half of the trip
    COMPLETED = "COMPLETED"  # Trip is completed
    BREAK = "BREAK" 
    RETURN_IN_PROGRESS = "RETURN_IN_PROGRESS"
    PROCESSING_PAYMENT = "PROCESSING_PAYMENT"  # Driver has completed the trip and is processing payment
    CANCELLED = "CANCELLED"  # Client has cancelled the trip
    CANCELLED_BY_DRIVER = "CANCELLED_BY_DRIVER"
    ABANDONED = "ABANDONED"  # Trip is abandoned


class TripMethod(models.TextChoices):
    AIRPORT_TRANSFER = "AIRPORT_TRANSFER"
    ONE_WAY = "ONE_WAY"
    ROUND_TRIP = "ROUND_TRIP"
    AS_DIRECTED = "AS_DIRECTED"


class PaymentMethods(models.TextChoices):
    CASH = "Cash"
    CARD = "Card"

class PaymentStatus(models.TextChoices):
    UNPAID = "UNPAID"
    PAID = "PAID"
    ON_HOLD = "ON_HOLD"
    IN_REVIEW = "IN_REVIEW"

class DistanceTypes(models.TextChoices):
    INNER_LONDON = "INNER_LONDON"
    ORBITAL_LONDON = "ORBITAL_LONDON"
    CENTRAL_LONDON = "CENTRAL_LONDON"
    GREATER_LONDON = "GREATER_LONDON"
    OUTER_LONDON = "OUTER_LONDON"
    OUTER_LONDON_CIRCLE_ONE = "OUTER_LONDON_CIRCLE_ONE"
    OUTER_LONDON_CIRCLE_TWO = "OUTER_LONDON_CIRCLE_TWO"
    OUT_OF_ZONE = "OUT_OF_ZONE"
class CanceledByStatus(models.TextChoices):
    Driver = "Driver"
    Client = "Client"
    System = "System"

class DeclinedByStatus(models.TextChoices):
    Driver = "Driver"
    Client = "Client"
    System = "System"
class Trip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    booking_fee = models.DecimalField(max_digits=20, decimal_places=6, default=0.00)
    unique_id = models.CharField(max_length=25,null=True,blank=True, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.PROTECT, blank=True, null=True, related_name='trip_passenger') # passenger
    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, null=True, blank=True, related_name='trip_driver')
    service_type = models.CharField(max_length=100, blank=True, null=True)

    is_instant_trip = models.BooleanField(default=True)

    booking_time = models.DateTimeField(auto_now_add=True)

    trip_status = models.CharField(max_length=30, choices=TripStatus.choices, default=TripStatus.REQUESTED)
    trip_method = models.CharField(
        max_length=30, choices=TripMethod.choices, blank=True, null=True)
    services = models.CharField(max_length=100, choices=Services.choices, blank=True, null=True)



    pickup_time = models.DateTimeField(blank=True, null=True)
    pickup_place_id = models.CharField(max_length=255, blank=True, null=True)
    stopage_place_ids = models.JSONField(default=dict, blank=True)



    dropoff_time = models.DateTimeField(null=True, blank=True)
    dropoff_place_id = models.CharField(max_length=255, blank=True, null=True)



    is_discounted = models.BooleanField(default=False)
    discount_amount = models.DecimalField(
        max_digits=10, decimal_places=6, default=0)

    number_of_adult_passengers = models.IntegerField(default=1)
    number_of_child_passengers = models.IntegerField(default=0)
    luggage_type = models.CharField(max_length=30, blank=True)

    travel_path = models.JSONField(default=list, blank=True, null=True)  
    total_distance = models.DecimalField(
        max_digits=20, decimal_places=6, default=0) # join of travel path in miles # no need
    total_minutes = models.DecimalField(
        max_digits=20, decimal_places=6, default=0) # minutes
    minute_fare = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    milage_fare = models.DecimalField(max_digits=20, decimal_places=6, default=0)
    fare = models.DecimalField(max_digits=20, decimal_places=6, default=0) # minutes_fare + milage_fare + booking fee
    



    congestion_charge_amount = models.DecimalField(max_digits=20, decimal_places=6, default=15) # not %
    total_with_congestion_charge = models.DecimalField(max_digits=20, decimal_places=6, default=0) # fare + congestion charge
    service_charge_amount = models.DecimalField(max_digits=20, decimal_places=6, default=5) # % of service charge
    total_with_service_charge = models.DecimalField(max_digits=20, decimal_places=6, default=0) # % of service charge
    vat_amount = models.DecimalField(max_digits=20,decimal_places=6, default=20) # % of vat
    total_fare_with_vat = models.DecimalField(max_digits=20, decimal_places=6, default=0) # % of vat
    org_commission_rate = models.DecimalField(max_digits=20, decimal_places=6, default=0.00)  
    org_commission_amount = models.DecimalField(max_digits=20, decimal_places=6, default=0.00)  # % of commission amount
    total_with_org_commission = models.DecimalField(max_digits=20, decimal_places=6, blank=True, null=True)
    final_fare = models.DecimalField(max_digits=20, decimal_places=6, default=0.00)  # % of commission amount


    client_tip = models.DecimalField(max_digits=10, decimal_places=6, default=0.00)

    cancelletion_reason = models.CharField(max_length=250, blank=True)

    # If user/org books the trip for others
    trip_for_others = models.BooleanField(default=False)
    passenger_name = models.CharField(max_length=255, blank=True, null=True)
    passenger_phone_number = models.CharField(max_length=250, blank=True, null=True)
    passenger_email = models.EmailField(blank=True, null=True)
    passenger_address = models.CharField(max_length=500, blank=True, null=True)

    flight_number = models.CharField(max_length=250, blank=True)
    flight_arrival_time = models.CharField(max_length=250, blank=True)


    payment_status = models.CharField(max_length=25,choices=PaymentStatus.choices,default=PaymentStatus.UNPAID)
    payment_intent_id = models.CharField(max_length=255, blank=True, null=True) #After Hold the amout, Hold ID will be store Here.
    payment_card_id = models.CharField(max_length=255, blank=True, null=True)
    payment_method = models.CharField(
        max_length=50, choices=PaymentMethods.choices, default=PaymentMethods.CARD)
    # history = HistoricalRecords()


    def update_travel_path(self, latitude, longitude, time):
        self.travel_path.append(
            {'lat': latitude,
            'lng': longitude,
            'trip_status': self.trip_status,
            'time': time,  
            })
        self.save()


    @staticmethod
    def generate_unique_id(length=6):
        #punctuation = r"""#$%&@"""
        characters = string.ascii_uppercase + string.digits #+ punctuation
        unique_id = ''.join(secrets.choice(characters) for _ in range(length))
        return unique_id

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = self.generate_unique_id()
        super().save(*args, **kwargs)
    
    @property
    def total_extra_charge(self):
        return sum(charge.charge_amount for charge in self.extracharge_set.all()if charge.verified)
    @property
    def total_break_time(self):
        breaks = self.tripbreak_set.all()
        total_minutes = 0
        
        for trip_break in breaks:
            if trip_break.start_time and trip_break.end_time:
                break_duration = trip_break.end_time - trip_break.start_time
                total_minutes += break_duration.total_seconds() / 60
        
        return round(total_minutes, 2)
    @property
    def total_journey_time(self):
        return max(0, self.total_minutes - self.total_break_time)


class TripBreak(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    break_before_trip_status = models.CharField(max_length=30, choices=TripStatus.choices, default=TripStatus.REQUESTED)

    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True)
    break_location_name = models.CharField(max_length=255, blank=True)
    break_location_lat = models.FloatField(blank=True, null=True)
    break_location_lng = models.FloatField(blank=True, null=True)
    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='tripbreak_requested_by')

    @property
    def break_duration(self):
        """
        Return the duration of the break in a human-readable format (HH:MM:SS).
        If the break hasn't ended yet (end_time is None), return 'Ongoing'.
        """
        if self.end_time:
            duration = self.end_time - self.start_time
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"Hours:{hours:02}, Minutes:{minutes:02}, Seconds:{seconds:02}"
        return "Ongoing"


class ExtraCharge(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    charge_amount = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    charge_type = models.CharField(max_length=50)
    charge_reason = models.CharField(max_length=400, null=True, blank=True)
    verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)



class ExtraChargePicture(models.Model):
    extra_charge = models.ForeignKey(
        ExtraCharge, 
        related_name='pictures', 
        on_delete=models.CASCADE
    )
    def extra_charge_file_path(instance, filename):
    # Check if extra_charge and trip exist to prevent potential errors
        if instance.extra_charge and instance.extra_charge.trip:
            return f'extra_charge/{instance.extra_charge.trip.id}/{filename}'
        return f'extra_charge/uncategorized/{filename}'
    picture = models.FileField(upload_to=extra_charge_file_path)

    def __str__(self):
        return f"Picture for Extra Charge {self.extra_charge_id}"
@receiver(post_delete, sender=ExtraChargePicture)
def delete_file_on_model_delete(sender, instance, **kwargs):
    if instance.picture:
        instance.picture.delete(save=False)

@receiver(pre_delete, sender=ExtraChargePicture)
def delete_file_on_model_update(sender, instance, **kwargs):
    if instance.picture:
        instance.picture.delete(save=False)
class DeclineTrip(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    decline_reason = models.CharField(max_length=250, null=True, blank=True)

    declined_by = models.CharField(max_length=30, choices=DeclinedByStatus.choices, default=DeclinedByStatus.Driver)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)





class CancelTrip(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    cancel_reason = models.CharField(max_length=250, null=True, blank=True)


    canceled_by = models.CharField(max_length=30, choices=CanceledByStatus.choices, default=CanceledByStatus.System)


    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)





class BookingFeeSchedule(models.Model):
    start_time = models.TimeField()
    end_time = models.TimeField()
    airport_transfer_fee = models.DecimalField(max_digits=10, decimal_places=2)
    one_way_fee = models.DecimalField(max_digits=10, decimal_places=2)
    round_trip_fee = models.DecimalField(max_digits=10, decimal_places=2)
    as_directed_fee = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_time']



    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @staticmethod
    def get_current_booking_fee(trip_method):
        current_time = timezone.localtime().time()
        try:
            schedule = BookingFeeSchedule.objects.filter(
                start_time__lte=current_time,
                end_time__gt=current_time,
                is_active=True
            ).first()
            
            # if not schedule:
            #     schedule = BookingFeeSchedule.objects.filter(
            #         start_time__gt=end_time,
            #         is_active=True
            #     ).first()

            if schedule:
                fee_mapping = {
                    TripMethod.AIRPORT_TRANSFER: schedule.airport_transfer_fee,
                    TripMethod.ONE_WAY: schedule.one_way_fee,
                    TripMethod.ROUND_TRIP: schedule.round_trip_fee,
                    TripMethod.AS_DIRECTED: schedule.as_directed_fee,
                }
                return fee_mapping.get(trip_method, Decimal('0.00'))
        except BookingFeeSchedule.DoesNotExist:
            pass
        
        default_fees = {
            TripMethod.AIRPORT_TRANSFER: Decimal('50.00'),
            TripMethod.ONE_WAY: Decimal('30.00'),
            TripMethod.ROUND_TRIP: Decimal('40.00'),
            TripMethod.AS_DIRECTED: Decimal('100.00'),
        }
        return default_fees.get(trip_method, Decimal('0.00'))
















