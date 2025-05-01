from django.contrib import admin

# Register your models here.
from driver_app.models import (
    Driver,
    DriverStatus,
    # DriverAttachmentStatus,
    # Manufacturer,
    Vehicle,
    ServiceType,
    VehicleModel,
    VehicleStatus,
    # VehicleTypesInfo,
    DriverProfileEditRequest,
)


admin.site.register(Driver)
# admin.site.register(DriverAttachmentStatus)

admin.site.register(ServiceType)
admin.site.register(VehicleModel)
# admin.site.register(VehicleTypesInfo)

admin.site.register(Vehicle)
admin.site.register(DriverProfileEditRequest)
