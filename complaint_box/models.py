from django.db import models
from django.conf import settings
from accounts.models import Services
import uuid
import secrets
from trip_management.models import Trip
import string
from django.db.models.signals import post_delete, pre_delete
from django.dispatch import receiver
# Create your models here.
class TITLE(models.TextChoices):
    REPORT = "Report", "Report"
    LOST_AND_FOUND = "Lost And Found", "Lost And Found"


class REPORT_SUBCATEGORIES(models.TextChoices):
    LATE_ARRIVAL = "Late Arrival", "Late Arrival"
    UNSAFE_DRIVING = "Unsafe Driving", "Unsafe Driving"
    UNPAID_FEES = "Unpaid Fees", "Unpaid Fees"
    UNWARRANTED_CRITICISM = "Unwarranted Criticism", "Unwarranted Criticism"
    VEHICLE_CLEANLINESS = "Vehicle Cleanliness Complaints", "Vehicle Cleanliness Complaints"
    VEHICLE_CONDITION = "Vehicle Condition Issues", "Vehicle Condition Issues"
    COMMUNICATION_CHALLENGES = "Communication Challenges", "Communication Challenges"
    MISBEHAVIOR_HARASSMENT = "Misbehavior and Harassment", "Misbehavior and Harassment"
    BILLING_HICCUPS = "Billing Hiccups", "Billing Hiccups"
    CHAUFFEUR_NO_SHOW = "Chauffeur No Show", "Chauffeur No Show"
    MESSY_VEHICLE = "Messy Vehicle", "Messy Vehicle"
    LACK_OF_GRATUITY = "Lack of Gratuity", "Lack of Gratuity"
    OTHER = "Other", "Other"



class LOST_AND_FOUND_SUBCATEGORIES(models.TextChoices):
    WALLET = "Wallet", "Wallet"
    WATCH = "Watch", "Watch"
    CLOTH = "Cloth", "Cloth"
    PHONE = "Phone", "Phone"
    BAG = "Bag", "Bag"
    OTHER = "Other", "Other"

class ComplaintStatus(models.TextChoices):
    SUBMITTED = "Submitted", "Submitted"
    UNDER_REVIEW = "Under Review", "Under Review"
    IN_PROGRESS = "In Progress", "In Progress"
    INVALID = "Invalid", "Invalid"
    SOLVED = "Solved", "Solved"



class ComplaintBox(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_id = models.CharField(max_length=25,null=True,blank=True, unique=True)

    trip = models.ForeignKey(Trip,on_delete=models.SET_NULL, null=True, blank=True)
    pickup_date = models.DateField(null=True, blank=True)
    dropoff_date = models.DateField(null=True, blank=True)
    pickup_location = models.CharField(max_length=25,null=True,blank=True)
    dropoff_location = models.CharField(max_length=25,null=True,blank=True)
    
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    author_name = models.CharField(max_length=155, blank=True, null=True)
    author_phone = models.CharField(max_length=30, blank=True, null=True)
    author_email = models.EmailField(max_length=50, blank=True, null=True)

    services = models.CharField(max_length=100, choices=Services.choices, null=True, blank=True)
    
    complaint_title = models.CharField(max_length=30, choices=TITLE.choices, null=True, blank=True)
    title_subcategory = models.CharField(max_length=50, null=True, blank=True)
    description = models.TextField()


    complaint_status = models.CharField(max_length=30, choices=ComplaintStatus.choices, default=ComplaintStatus.SUBMITTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @staticmethod
    def generate_case_id(length=8):
        characters = string.ascii_uppercase + string.digits
        case_id = ''.join(secrets.choice(characters) for _ in range(length))
        return case_id
    


class ComplaintPicture(models.Model):
    complaint = models.ForeignKey(ComplaintBox, on_delete=models.CASCADE, related_name='complaint_pictures')

    def complaint_file_path(instance, filename):
        if instance.complaint and instance.complaint.case_id:
            return f'complaint/{instance.complaint.case_id}/{filename}'
        return f'complaint/uncategorized/{filename}'

    picture = models.FileField(upload_to=complaint_file_path)

@receiver(post_delete, sender=ComplaintBox)
def delete_file_on_model_delete(sender, instance, **kwargs):
    if instance.picture:
        instance.picture.delete(save=False)

@receiver(pre_delete, sender=ComplaintBox)
def delete_file_on_model_update(sender, instance, **kwargs):
    if instance.picture:
        instance.picture.delete(save=False)

class Remark(models.Model):
    complaint = models.ForeignKey(ComplaintBox, on_delete=models.SET_NULL, null=True, blank=True, related_name='remarks')
    remark = models.TextField()
    complaint_box_status = models.CharField(max_length=30, choices=ComplaintStatus.choices, blank=True, null=True)
    remark_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)




