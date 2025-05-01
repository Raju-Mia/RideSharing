import datetime
import uuid
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

#import
from simple_history.models import HistoricalRecords
from organization_manager.models import Organization

from utils.storage_file_path import phone_email_change_state_file_path
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver





#============================ User START ========================
GENDER = (("male", "Male"), ("female", "Female"), ("others", "Others"))

class Services(models.TextChoices):
    united_administration = "united-administration"
    united_chauffeur = "united-chauffeur"
    concierge_service = "concierge-service"
    united_rydr_client = "united-rydr-client"
    united_rydr_driver = "united-rydr-driver"
    chauffeurs_driven = "chauffeurs-driven"
    kingdom_chauffeur = "kingdom-tours-and-travel"
    royal_chauffeur = "royal-chauffeur"
    city_chauffeur = "city-transfer-and-travel-limited"
    all_chauffeur_cars = "all-chauffeur-cars"
    bro_cab = "bro-cab"
    buses = "buses"
    echo_drive = "echo-drive"
    hello_mini_cab = "hello-mini-cab"
    luxury_cruise_experience = "luxury-cruise-experience"
    rainbow_chauffeurs = "rainbow-chauffeurs"
    redlimos = "redlimos"
    royale_limousine_service = "royale-limousine-service"
    street_mini_cabs = "street-mini-cabs"


class CustomUser(AbstractUser):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    username = models.CharField(max_length=150, blank=True, unique=True)
    full_name = models.CharField(max_length=500)
    email = models.EmailField(blank=True,null=True)
    phone = models.CharField(max_length=20,blank=True,null=True)
    
    service = models.CharField(
        max_length=250,
        choices=Services.choices,
        blank=True,
    )
    
    address = models.TextField(blank=True)
    picture = models.FileField(blank=True)
    stripe_id = models.CharField(max_length=250, blank=True)
    
    
    is_hotel = models.BooleanField(default=False)
    is_operator = models.BooleanField(default=False)
    blacklisted = models.BooleanField(default=False)
    
    sum_of_ratings = models.FloatField(default=0)
    number_of_ratings = models.FloatField(default=0)
    average_rating = models.FloatField(default=0)
    
    
    email_is_verified = models.BooleanField(default=False)
    phone_is_verified = models.BooleanField(default=False)
    user_is_verified = models.BooleanField(default=False)
    whatsappnumber = models.CharField(blank=True, max_length=15)
    password_has_changed = models.BooleanField(default=False)

    status = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    one_time_password_status = models.BooleanField(default=False)
    attemp_count = models.IntegerField(blank=True,null=True)
    terminated_status = models.BooleanField(default=False)
    terminated_resone = models.CharField(max_length=256,blank=True,null=True)
    terminated_at = models.DateTimeField(null=True, blank=True)
    
    created_by = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True,blank=True,null=True)


    last_activity = models.DateTimeField(default=timezone.now)
    is_online = models.BooleanField(default=False)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)

    telegram_chat_id = models.CharField(max_length=100, blank=True, null=True)
    
    
    # Each user belongs to an organization
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    
    # Role management to differentiate between admin and regular users
    is_organization_admin = models.BooleanField(default=False)
    
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["email_is_verified", "email", "service"],
                condition=Q(email_is_verified=True),
                name="unique_verified_email_service"
            ),
            models.UniqueConstraint(
                fields=["phone_is_verified", "phone", "service"],
                condition=Q(phone_is_verified=True),
                name="unique_verified_phone_service"
            )
        ]




    def save(self, *args, **kwargs):
        if not self.username:  # Only generate username if it's not provided
            # self.username = self.full_name + str(uuid.uuid4())
            self.username = self.full_name + str(uuid.uuid4())[:8]
        super().save(*args, **kwargs)




    def __str__(self):
        if self.email:
            x = self.email
        elif self.phone:
            x = self.phone
        else:
            x = str(self.id)
        return x
    
    
    @property
    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        
        
        
    def get_full_name(self):
        """
        Returns the user's full name.
        If full_name is not set, fallback to username, email, or phone.
        """
        if self.full_name:
            return self.full_name
        elif self.username:
            return self.username
        elif self.email:
            return self.email
        elif self.phone:
            return self.phone
        else:
            return str(self.id)  # Fallback to UUID if no other info is available




class UserProfile(models.Model): #TODO For user Profile.
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile', blank=True)
    
    # Profile Information
    designation = models.CharField(max_length=255, blank=True, null=True)
    contact = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)

    # Image Field
    profile_image = models.ImageField(upload_to='user_profile_pictures/', blank=True, null=True)


    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.full_name}'s Profile"


#============================ User END ========================






#============================ OTP START ========================
class TokenTypes(models.TextChoices):
    email_verification = "email verification"
    password_reset = "password reset"
    phone_number_verification = "phone number verification"


class VerificationTokens(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    token_type = models.CharField(max_length=100, choices=TokenTypes.choices)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.CharField(max_length=250, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    token_life_time = models.IntegerField(default=5)

    def __str__(self):
        if self.user.email:
            x = self.user.email
        else:
            x = str(self.id)
        return self.token_type + " " + str(x) + str(self.created_at)

    @property
    def is_valid(self):
        """
        checks tokens validity
        """
        otp_life_time = 5
        return self.created_at + timedelta(minutes=otp_life_time) > timezone.now()

    def code_is_valid(self):
        code_life_time = 10
        return self.created_at + timedelta(minutes=code_life_time) > timezone.now()
    
    
    def token_is_valid(self):
        if self.created_at + timedelta(minutes=self.token_life_time) > timezone.now():
            return True, "Token is valid"
        else:
            return False, "Token has expired"



class OtpTypes(models.TextChoices):
    email_verification = "Email Verification"
    password_reset = "Password Reset"
    phone_number_verification = "Phone Number Verification"



class VerificationOTP(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    otp_type = models.CharField(max_length=100, choices=OtpTypes.choices)
    message_sid = models.CharField(max_length=256, blank=True,null=True)
    verification_otp = models.CharField(max_length=6, blank=True,null=True)
    verification_otp_life_time = models.IntegerField(default=5)
    verification_otp_timestamp = models.DateTimeField(null=True, blank=True)
    used_status = models.BooleanField(default=False)

    updated_at = models.DateTimeField(auto_now=True,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user.email:
            x = self.user.email
        else:
            x = str(self.id)
        return str(x) + str(self.created_at)

    @property
    def is_valid(self):
        """
        checks tokens validity
        """
        verification_otp_life_time = 5
        return self.created_at + timedelta(minutes=verification_otp_life_time) > timezone.now()

    def otp_is_valid(self):
        verification_otp_life_time = 10
        return self.created_at + timedelta(minutes=verification_otp_life_time) > timezone.now()

#========================== OTP END ==========================






AUTHORITIES = (("superuser", "Super User"), ("operator", "Operator"))
class Admin(models.Model):
    authority_level = models.CharField(
        max_length=30, choices=AUTHORITIES, default="operator"
    )
    designation_name = models.CharField(max_length=50)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
















class PhoneEmailChangeState(models.Model): #no Need ||
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    image_is = models.ImageField(upload_to=phone_email_change_state_file_path, blank=True, null=True)
    file_is = models.FileField(upload_to=phone_email_change_state_file_path, blank=True, null=True)
    
    
    
    new_number = models.CharField(max_length=30, blank=True)
    new_email = models.EmailField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)



class SavedPlace(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=255)
    lat = models.CharField(max_length=50) 
    lon = models.CharField(max_length=50)
    icon = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.user.full_name}'s {self.name} saved place and id: {self.id}"

