from django.urls import path
from .views import ContactView, NewsletterView, Complaint, ComplaintDetails

urlpatterns = [
    path("contact/", ContactView.as_view(), name="contact"),
    path("newsletter/", NewsletterView.as_view(), name="newsletter"),
    path("v1/complaint/", Complaint.as_view(), name="complaint"),
    path("v1/complaint/<uuid:id>/", ComplaintDetails.as_view(), name="complaint"),
]
