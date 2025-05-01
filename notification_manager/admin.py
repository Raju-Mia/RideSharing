from django.contrib import admin

# Register your models here.
from notification_manager.models import (
    VapidKey,
    FCMToken, 
    WebPushSubscription,
    Notification, 
    NotificationLog,
    DriverNotification,
    ClientNotification, 
    AdminNotification, 
    ConciergeNotification, 
    NotificationTrigger,
    NotificationPreference,
    NotifyMessage
    ) 

admin.site.register(VapidKey)
admin.site.register(FCMToken)
admin.site.register(WebPushSubscription)
admin.site.register(Notification)
admin.site.register(NotificationLog)
admin.site.register(AdminNotification)
admin.site.register(DriverNotification)
admin.site.register(ClientNotification)
admin.site.register(ConciergeNotification)
admin.site.register(NotificationTrigger)
admin.site.register(NotificationPreference)
admin.site.register(NotifyMessage)