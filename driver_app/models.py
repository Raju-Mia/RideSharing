from django.db import models
import datetime
import uuid
import os
from PIL import Image
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.timezone import timedelta
from rest_framework_simplejwt.tokens import RefreshToken
import secrets
import string

#import
from simple_history.models import HistoricalRecords
from organization_manager.models import Organization

from accounts.models import GENDER, Services


STATUS = (
    ("unverified", "Unverified"),  # user has not verified his email
    ("pending","Pending",),  # user has verified his email but his account is not approved by admin
    ("verified", "Verified"),  # user account is approved by admin but not active
    ("active", "Active"),  # user has a vehicle and is active
    ("rejected", "Rejected"),  # user has been rejected by admin
    )




class DriverStatus(models.TextChoices):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"
    rejected_documents = "rejected_documents"

class VehicleStatus(models.TextChoices): 
    unverified = "unverified"
    pending = "pending"
    verified = "verified"
    rejected_documents = "rejected_documents"  


class AttachmentStatus(models.TextChoices):
    required = "required"
    pending = "pending"
    submitted = "submitted"
    verified = "verified"
    rejected = "rejected"
    resubmitted = "resubmitted"
    expired = "expired",




def driver_file_path(instance, filename):
    if instance and instance.unique_id:  # Ensure owner exists
        return f"driver/files/{instance.unique_id}/{filename}"
    return f"driver/files/uncategorized/{filename}"

    

class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unique_id = models.CharField(unique=True, blank=True, null=True, max_length=250)
    
    address = models.CharField(max_length=250, blank=True, null=True)
    state = models.CharField(max_length=30, blank=True, null=True)
    city = models.CharField(max_length=30, blank=True, null=True)
    country = models.CharField(max_length=30, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=15, choices=GENDER, default="Male")
    total_earned = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE) #user
    organization = models.ForeignKey(Organization, on_delete=models.PROTECT, blank=True, null=True)
    status = models.CharField(max_length=20, choices=DriverStatus.choices, default=DriverStatus.unverified)
    
    driving_license_number = models.CharField(max_length=250, blank=True, null=True)
    driving_license_no_status = models.CharField(max_length=20, choices=AttachmentStatus.choices, default=AttachmentStatus.required)
    
    dvla_plastic_driving_licence_front = models.FileField(upload_to=driver_file_path,blank=True, null=True)
    dvla_plastic_driving_licence_back = models.FileField(upload_to=driver_file_path,blank=True, null=True)
    dvla_plastic_driving_licence_status = models.CharField(max_length=20, choices=AttachmentStatus.choices, default=AttachmentStatus.required)
    dvla_plastic_driving_licence_last_update = models.DateField(blank=True, null=True)
    dvla_plastic_driving_licence_expired_date = models.DateField(blank=True, null=True)
    dvla_plastic_driving_licence_comment = models.TextField(blank=True, null=True)

    private_hire_driving_licence = models.FileField(upload_to=driver_file_path,blank=True, null=True)
    private_hire_driving_licence_status = models.CharField(max_length=20, choices=AttachmentStatus.choices, default=AttachmentStatus.required)
    private_hire_driving_licence_last_update = models.DateField(blank=True, null=True)
    private_hire_driving_licence_expired_date = models.DateField(blank=True, null=True)
    private_hire_driving_licence_comment = models.TextField(blank=True, null=True)


    # profile_photo
    # the profile photo is users profile photo


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        if self.user.email:
            return f"{self.user.email} ({self.id})"
        elif self.user.phone:
            return f"{self.user.phone} ({self.id})"
        else:
            return str(self.id)
        
    @staticmethod
    def generate_unique_id(length=5):
        characters = string.ascii_uppercase + string.digits
        return ''.join(secrets.choice(characters) for _ in range(length))

    def save(self, *args, **kwargs):
        if not self.unique_id:
            while True:
                unique_id = self.generate_unique_id()
                if not Driver.objects.filter(unique_id=unique_id).exists():
                    self.unique_id = unique_id
                    break

        vehicle_status = None
        if hasattr(self, 'vehicles') and self.vehicles:
            self.vehicles.refresh_from_db()
            vehicle_status = self.vehicles.status

        attachments = [
            self.driving_license_no_status,
            self.dvla_plastic_driving_licence_status,
            self.private_hire_driving_licence_status,
        ]

        if (vehicle_status == VehicleStatus.verified and 
            all(status == AttachmentStatus.verified for status in attachments)):
            self.status = DriverStatus.verified
        # elif any(status in [AttachmentStatus.expired, AttachmentStatus.rejected] for status in attachments) or (
        #     vehicle_status is not None and vehicle_status != VehicleStatus.verified
        # ):
        #     self.status = DriverStatus.unverified
        else:
            self.status = self.status

        super().save(*args, **kwargs)



LUGGAGE_CAPACITY = (("large", "Large"), ("medium", "Medium"), ("small", "Small")) #no need-


class LuggageCapacity(models.TextChoices):
    cabin = "cabin"
    medium = "medium"
    large = "large"




class CommunicationMethod(models.TextChoices): # no need-
    sms = "sms"
    email = "email"


 


class Manufacturer(models.Model): #
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    manufacturer = models.CharField(max_length=100, unique=True)

    def save(self, *args, **kwargs):
        self.manufacturer = self.manufacturer.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.manufacturer


class VehicleTypes(models.TextChoices): #
    super_lux = "SUPER LUX"
    xl_lux = "XL LUX"
    lux = "LUX"
    executive = "EXECUTIVE"
    xl_eco = "XL ECO"
    x_eco = "X ECO"

class ServiceType(models.Model): # (service type service Pricing)
    service_type = models.CharField(max_length=100,blank=True,null=True,)
    inner_london_fare = models.JSONField(blank=True, null=True)
    central_london_fare = models.JSONField(blank=True, null=True)
    orbital_london_fare = models.JSONField(blank=True, null=True)
    greater_london_fare = models.JSONField(blank=True, null=True)
    outer_london_fare = models.JSONField(blank=True, null=True)
    outer_london_circle_one_fare = models.JSONField(blank=True, null=True)
    outer_london_circle_two_fare = models.JSONField(blank=True, null=True)
    out_of_zone_fare = models.JSONField(blank=True, null=True)
    

    booking_fee = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    congestion_charge = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    
    updated_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def save(self, *args, **kwargs):
        if self.service_type:
            self.service_type = self.service_type.upper()
        super().save(*args, **kwargs)
    def __str__(self):
        return str(self.id)




class VehicleModel(models.Model):  # (Vehicle service Pricing)
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)

    manufacturer = models.CharField(max_length=100, null=True, blank=True)
    model = models.CharField(max_length=100, null=True, blank=True)
    year_of_manufacture = models.PositiveIntegerField(null=True, blank=True)


    service_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
    )
    inner_london_fare = models.JSONField(blank=True, null=True)
    central_london_fare = models.JSONField(blank=True, null=True)
    orbital_london_fare = models.JSONField(blank=True, null=True)
    greater_london_fare = models.JSONField(blank=True, null=True)
    outer_london_fare = models.JSONField(blank=True, null=True)
    outer_london_circle_one_fare = models.JSONField(blank=True, null=True)
    outer_london_circle_two_fare = models.JSONField(blank=True, null=True)

    booking_fee = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    congestion_charge = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    
    updated_date = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.model:
            self.model = self.model.upper()
        if self.manufacturer:
            self.manufacturer = self.manufacturer.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.id)



def vehicle_file_path(instance, filename):
    if instance.owner and instance.owner.unique_id:  # Ensure owner exists
        return f"vehicle/files/{instance.owner.unique_id}/{filename}"
    return f"vehicle/files/uncategorized/{filename}"

class Vehicle(models.Model): 
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    vehicle_registration_number = models.CharField(max_length=50)
    vehicle_reg_no_status = models.CharField(max_length=20, choices=AttachmentStatus.choices, default=AttachmentStatus.required)

    model = models.ForeignKey(VehicleModel, on_delete=models.CASCADE, null=True, blank=True)
    owner = models.OneToOneField(Driver, on_delete=models.CASCADE, blank=True, null=True, related_name='vehicles')
    status = models.CharField(max_length=20, choices=VehicleStatus.choices, default=VehicleStatus.pending)


    color = models.CharField(max_length=50, blank=True, null=True)
    
    fuel_type = models.CharField(max_length=50, blank=True, null=True)
    year_of_manufacture = models.PositiveIntegerField(null=True, blank=True)
    mot_status = models.CharField(max_length=500, blank=True, null=True)
    month_of_first_dvla_registration = models.CharField(max_length=30, blank=True, null=True)    

    insurance_certificate = models.FileField(upload_to=vehicle_file_path, blank=True, null=True)
    insurance_certificate_status = models.CharField(max_length=20, choices=AttachmentStatus.choices, default=AttachmentStatus.required)
    insurance_certificate_last_update = models.DateField(blank=True, null=True)
    insurance_certificate_expired_date = models.DateField(blank=True, null=True)
    insurance_certificate_comment = models.TextField(blank=True, null=True)

    mot_test_certificate = models.FileField(upload_to=vehicle_file_path, blank=True, null=True)
    mot_test_certificate_status = models.CharField(max_length=20, choices=AttachmentStatus.choices, default=AttachmentStatus.required)
    mot_test_certificate_last_update = models.DateField(blank=True, null=True)
    mot_test_certificate_expired_date = models.DateField(blank=True, null=True)
    mot_test_certificate_comment = models.TextField(blank=True, null=True)

    private_hire_vehicle_licence = models.FileField(upload_to=vehicle_file_path, blank=True, null=True)
    private_hire_vehicle_licence_status = models.CharField(max_length=20, choices=AttachmentStatus.choices, default=AttachmentStatus.required)
    private_hire_vehicle_licence_last_update = models.DateField(blank=True, null=True)
    private_hire_vehicle_licence_expired_date = models.DateField(blank=True, null=True)
    private_hire_vehicle_licence_comment = models.TextField(blank=True, null=True)

    log_book_V5C = models.FileField(upload_to=vehicle_file_path, blank=True, null=True)
    log_book_V5C_back = models.FileField(upload_to=vehicle_file_path, blank=True, null=True)
    log_book_V5C_status = models.CharField(max_length=20, choices=AttachmentStatus.choices, default=AttachmentStatus.required)
    log_book_V5C_last_update = models.DateField(blank=True, null=True)
    log_book_V5C_expired_date = models.DateField(blank=True, null=True)
    log_book_V5C_comment = models.TextField(blank=True, null=True)
    last_date_of_V5C_issued = models.DateField(blank=True, null=True)

    number_of_child_seat = models.IntegerField(default=0)
    maximum_passengers = models.IntegerField(default=0)
    luggage_capacity = models.CharField(choices=LuggageCapacity.choices, default="", max_length=50)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    history = HistoricalRecords()

    def __str__(self):
        return str(self.vehicle_registration_number) + "------" + str(self.owner.user.phone) + "------" + str(self.owner.id)
    def save(self, *args, **kwargs):
        statuses = [
            self.log_book_V5C_status,
            self.private_hire_vehicle_licence_status,
            self.vehicle_reg_no_status,
            self.insurance_certificate_status,
            self.mot_test_certificate_status,
        ]


        if all(status == AttachmentStatus.verified for status in statuses):
            self.status = VehicleStatus.verified
        # elif any(status in [AttachmentStatus.expired, AttachmentStatus.rejected] for status in statuses):
        #     self.status = VehicleStatus.unverified
        else:
            self.status = self.status

        super().save(*args, **kwargs)

        if self.owner:
            self.owner.refresh_from_db()
            self.owner.save()




def edit_request_picture_upload_to(instance, filename):
    return f"edit_requests/{instance.user.id}/{filename}"

class DriverProfileEditRequest(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="edit_requests")
    picture = models.ImageField(upload_to=edit_request_picture_upload_to, blank=True, null=True)
    status = models.CharField(max_length=20, choices=AttachmentStatus.choices, default=AttachmentStatus.required)

    admin_comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"EditRequest for {self.user.get_full_name()} - {self.status} -{self.id}"
