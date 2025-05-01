
from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenVerifyView

from notification_manager.views import (
    android_push_notification,
    concierge_web,
    whatsapp_notification,
    notification,
    webPushnotificaiton_view,
    administration_notification,
    test
    )


from notification_manager.views.setup import (
    GenerateVapidKeyView,
)

# App Name
app_name = "notification_manager"


urlpatterns = [
    
    # ====For Generate Vapid Key for web push notification
    path('v1/administration-settings/generate-vapid-key/', GenerateVapidKeyView.as_view(), name='generate_vapid_key'),
    
    
    
    # ===============  For Driver App ===============
    path('v1/notification/create-token/', android_push_notification.CreateFCMTokenView.as_view()),
    path('v1/notification/send-notification/', android_push_notification.SendPushNotificationView.as_view()),
    path('v1/notification/send-single-user-message/', android_push_notification.SingleUserPushNotificationSend.as_view()),
    path('v1/notification/send-multi-user-message/', android_push_notification.MultiUserPushNotificationSend.as_view()),
    path("v1/notification/get-all-notification/", notification.GetAllNotifications.as_view()),
    
    path('v1/driver/web-signle-push-notification/app-to-administration/', administration_notification.DriverAppToAdministrationWebPushNotification.as_view()),
    
    
    # Administration API==========================
    path('v1/administration/web-push-notification-subscriptions/', concierge_web.WebPushSubscriptionListCreateView.as_view()),
    path('v1/administration/web-push-notification-subscriptions/<str:pk>/', concierge_web.WebPushSubscriptionDetailView.as_view()),
    
    
    # Administration Driver API==========================
    
    
    
    # Administration Client API==========================
    path("v1/user/web-push-subscription/manage/", webPushnotificaiton_view.WebPushSubscriptionManageView.as_view()),
    path('v1/user/web-push-subscription/send-single-user-push-notification/', webPushnotificaiton_view.SendSingleUserPushNotificationAPIView.as_view(), name='send_push_notification'),
    
    
    # ======= Concierge Web Application Notification ====== Version_1 =====
    path('v1/concierge/test-notification/', concierge_web.TestWebNotificationView.as_view()),
    
    # path('v1/web-push/test-notification/send-maltiple-users', test.WebPushMalipleUsersNotification.as_view()),
    path('v1/web-push/test-notification/send-single-user/', test.WebPushSingleUserNotification.as_view()),
    
    
    

    
    
    #============ Whats App Api Integration ===============
    path('v1/whatsapp/send-message/', whatsapp_notification.SendWhatsAppTemplateMessageView.as_view()),
    path('v1/read-notification/<uuid:notification_id>/', notification.UserReadNotification.as_view()),
    
]
