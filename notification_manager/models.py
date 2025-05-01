from django.db import models

# Create your models here.
from django.contrib.auth import get_user_model
import uuid
User = get_user_model()


class VapidKey(models.Model):
    public_key = models.TextField()
    private_key = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"VAPID Key created on {self.created_at}"
    
    
    

OPERATING_SYSTEMS = [
    ('android', 'Android'),
    ('ios', 'iOS'),
    ('linux', 'Linux'),
    ('web', 'Web'),
    ('windows', 'Windows'),
    ('macos', 'macOS'),
    ('other', 'Other')
]

DEVICE_TYPES = [
    ('mobile', 'mobile'),
    ('tablet', 'Tablet'),
    ('laptop', 'Laptop'),
    ('desktop', 'Desktop'),
    ('other', 'Other')
]



class FCMToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='fcm_tokens')
    fcm_token = models.TextField(null=True, blank=True)
    
    # New fields for enhanced notification management
    browser_name = models.CharField(max_length=100, blank=True, null=True)
    operating_systems = models.CharField(max_length=100, blank=True, null=True)
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES, blank=True, null=True) # mobile, desktop
    device_model = models.CharField(max_length=50, blank=True, null=True)  # Device model (e.g., iPhone 12)
    device_os_version = models.CharField(max_length=50, blank=True, null=True)  # OS version (e.g., iOS 14.0)
    device_vendor = models.CharField(max_length=100, blank=True, null=True) #Samsung
    device_id = models.CharField(max_length=100, blank=True, null=True)  # Unique device identifier
    pv4_address = models.CharField(max_length=100, blank=True, null=True) #118.179.64.3
    IP_location = models.CharField(max_length=255, blank=True, null=True) #Dhaka, Dhaka (BD)
    user_agent = models.TextField(blank=True, null=True) #details
    
    device_location_latitude = models.FloatField(null=True, blank=True)  # Latitude of the device
    device_location_longitude = models.FloatField(null=True, blank=True)  # Longitude of the device
    notification_enabled = models.BooleanField(default=False)  # User's preference for receiving notifications
    last_active = models.DateTimeField(auto_now=True)  # Last interaction time with the device
    active_status = models.BooleanField(default=True)
    block_status = models.BooleanField(default=False)
    verification_required = models.BooleanField(default=False)
    verification_status = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"Name: {self.user.username} - Email:{self.user.email} -Organization: {self.user.organization}"




class WebPushSubscription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscription')
    
    endpoint = models.TextField(null=True, blank=True)
    p256dh = models.TextField(null=True, blank=True)
    auth = models.TextField(null=True, blank=True)
    
    # New fields for enhanced notification management
    browser_name = models.CharField(max_length=100, blank=True, null=True)
    operating_systems = models.CharField(max_length=100, blank=True, null=True)
    device_type = models.CharField(max_length=50, choices=DEVICE_TYPES, blank=True, null=True) # mobile, desktop
    device_model = models.CharField(max_length=50, blank=True, null=True)  # Device model (e.g., iPhone 12)
    device_os_version = models.CharField(max_length=50, blank=True, null=True)  # OS version (e.g., iOS 14.0)
    device_vendor = models.CharField(max_length=100, blank=True, null=True) #Samsung
    device_id = models.CharField(max_length=100, blank=True, null=True)  # Unique device identifier
    pv4_address = models.CharField(max_length=100, blank=True, null=True) #118.179.64.3
    IP_location = models.CharField(max_length=255, blank=True, null=True) #Dhaka, Dhaka (BD)
    user_agent = models.TextField(blank=True, null=True) #details
    
    device_location_latitude = models.FloatField(null=True, blank=True)  # Latitude of the device
    device_location_longitude = models.FloatField(null=True, blank=True)  # Longitude of the device
    notification_enabled = models.BooleanField(default=False)  # User's preference for receiving notifications
    last_active = models.DateTimeField(auto_now=True)  # Last interaction time with the device
    active_status = models.BooleanField(default=True)
    block_status = models.BooleanField(default=False)
    verification_required = models.BooleanField(default=False)
    verification_status = models.BooleanField(default=True)
    status = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user} - {self.notification_enabled} -- {self.browser_name}"






class Notification(models.Model):
    CATEGORY_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ]
    TYPE_CHOICES = [
        ('push', 'Push Notification'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('in_app', 'In-App Notification'),
        ('third_party', 'Third-party Notification'),
    ]
    
    NOTIFICATION_PLATFORMS = [
        ('administration', 'Administation'),
        ('rydr_driver_app', 'RYDR Driver App'),
        ('rydr_driver_web', 'RYDR Driver Web'),
        ('rydr_client_app', 'RYDR Client App'),
        ('rydr_client_web', 'RYDR Client Web'),
        ('concierge_service', 'Concierge Service'),
        ('others', 'Others'),
        ('custom', 'Custom Platform'),
    ]
    
    SEND_STATUS = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('deleted', 'Deleted'),
        ('pending', 'Pending'),
        ('sented', 'Sented'),
        ('failed', 'Failed'),
    ]
    
    PRIORITY = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
        
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    title = models.CharField(max_length=255, blank=True, null=True)
    message = models.TextField(blank=True, null=True)
    json_content = models.JSONField(null=True, blank=True)
    image = models.ImageField(upload_to='notification_images/', null=True, blank=True)
    file = models.FileField(upload_to='notification_files/', null=True, blank=True)
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='info')
    notification_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='in_app')
    notification_platform = models.CharField(max_length=50, choices=NOTIFICATION_PLATFORMS, blank=True, null=True)
    priority = models.CharField(max_length=10, choices=PRIORITY, default='medium')

    url = models.URLField(null=True, blank=True)  # Optional action URL
    is_read = models.BooleanField(default=False)
    is_hidden = models.BooleanField(default=False)
    is_seen = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SEND_STATUS, default='sented')  # pending, sented, failed
    
    created_at = models.DateTimeField(auto_now_add=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)  # For scheduled notifications

    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient}"



class NotificationLog(models.Model):
    notification = models.ForeignKey(Notification, on_delete=models.CASCADE, related_name='logs')
    event = models.CharField(max_length=50, choices=[('sent', 'Sent'), ('delivered', 'Delivered'), ('read', 'Read')])
    timestamp = models.DateTimeField(auto_now_add=True)

class AdminNotification(models.Model):
    notification = models.OneToOneField(Notification, on_delete=models.CASCADE, related_name='admin_notification')
    is_high_priority = models.BooleanField(default=False)

class ClientNotification(models.Model):
    notification = models.OneToOneField(Notification, on_delete=models.CASCADE, related_name='client_notification')
    trip_id = models.PositiveIntegerField(blank=True, null=True)
    
class DriverNotification(models.Model):
    notification = models.OneToOneField(Notification, on_delete=models.CASCADE, related_name='driver_notification')
    trip_id = models.PositiveIntegerField(blank=True, null=True)


class ConciergeNotification(models.Model):
    notification = models.OneToOneField(Notification, on_delete=models.CASCADE, related_name='concierge_notification')
    trip_id = models.PositiveIntegerField(blank=True, null=True)
    payment_status = models.CharField(max_length=50, blank=True, null=True)



class NotificationTrigger(models.Model):
    TRIGGER_TYPES = [
        ('driver_registration', 'Driver Registration'),
        ('document_update', 'Document Update'),
        ('trip_booking', 'Trip Booking'),
        ('trip_status_update', 'Trip Status Update'),
        ('payment_update', 'Payment Update'),
        ('due_limit', 'Due Limit Warning'),
    ]
    
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPES)
    is_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.get_trigger_type_display()



class NotificationPreference(models.Model): #Each user can have preferences for receiving specific types of notifications.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    receive_push = models.BooleanField(default=True)
    receive_email = models.BooleanField(default=True)
    receive_sms = models.BooleanField(default=True)
    receive_in_app = models.BooleanField(default=True)
    language = models.CharField(max_length=10, default='en')  # Support for multilingual notifications

    def __str__(self):
        return f"{self.user}'s Preferences"



class NotifyMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(User, related_name='received_user', on_delete=models.CASCADE)
    title = models.CharField(max_length=250, blank=True, null=True)
    content = models.TextField(blank=True, null=True)
    json_content = models.JSONField(null=True, blank=True)
    is_read = models.BooleanField(default=False)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self):
        return f"{self.user.email}"


