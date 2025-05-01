from django.db import models
from django.contrib.auth import get_user_model
from trip_management.models import Trip
import uuid
from simple_history.models import HistoricalRecords

User = get_user_model()

STATUS = (
    ("pending", "Pending"),
    ("processing", "Processing"),
    ("resolved", "Resolved"),
    ("unsolved", "Unsolved"),
)


class Contact(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class Newsletter(models.Model):
    email = models.EmailField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ComplaintBox(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    issue = models.TextField()
    status = models.CharField(max_length=100, choices=STATUS, default="pending")
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="complaint_created_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    history = HistoricalRecords()

    def __str__(self):
        return self.title
