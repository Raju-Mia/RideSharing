import uuid
from django.db import models
from django.conf import settings
from django.db.models import Q

# from accounts.models import Driver
from driver_app.models import (
    Driver,
    DriverStatus,
    # DriverAttachmentStatus,
    # Manufacturer,
    Vehicle,
    VehicleModel,
    VehicleStatus,
    VehicleTypes,
    # VehicleTypesInfo,
    AttachmentStatus,
)


class PermissionChoices(models.TextChoices):
    change_trip_status = "change trip status"
    view_trip_history = "view trip history"
    assign_driver = "assign driver"
    driver_verification = "driver verification"
    pricing = "pricing"
    job_dispatch = "job dispatch"
    organization_management = "organization management"
    operator_management = "operator management"
    book_a_trip = "book a trip"


class OperatorPermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    permission = models.CharField(max_length=500, choices=PermissionChoices.choices)

    def __str__(self):
        return self.permission


class DriverInfoRejectedFields(models.TextChoices):
    driving_license_front_image = "driving_license_front_image"
    driving_license_back_image = "driving_license_back_image"
    pp_size_driver_image = "pp_size_driver_image"
    national_insurance = "national_insurance"
    criminal_record_book = "criminal_record_book"
    dbl_file = "dbl_file"
    dbs_image = "dbs_image"
    date_of_birth = "date_of_birth"
    pco_license_number = "pco_license_number"
    # pco_license_file = "pco_license_file"



class RejectedDriverInfo(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["active", "driver"],
                condition=Q(active=True),
                name="one driver object can have one active resubmission",
            )
        ]


class RejectedFields(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    rejected_driver_info = models.ForeignKey(
        RejectedDriverInfo, on_delete=models.CASCADE
    )
    field = models.CharField(max_length=500, choices=DriverInfoRejectedFields.choices)
    reason = models.CharField(max_length=500)
