from django.urls import path



#Import
from client_app.views.views import (
    ClientProfileUpdateView,
    )

#App Name
app_name = 'client_app'

urlpatterns = [
    path('v1/client/myself-profile/update/', ClientProfileUpdateView.as_view()),
    
]

