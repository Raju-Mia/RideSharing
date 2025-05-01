from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenVerifyView

from mail_management.views import (
    MailSendCheck,
    SendEmailView,
)


# App Name
app_name = "mail_management"


urlpatterns = [
    path("send/", SendEmailView.as_view()),

]
