from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    # def ready(self):
    #     from .signals import (
    #         # send_notification,
    #         # delete_notification,
    #         populate_drivers_attachment_status,
    #         # populate_vehicle_attachment_status,
    #         # recalculate_max_min_fare,
    #         update_driver_status_for_attchaments_update,
    #     )
    #     from driver_app.models import (
    #         Driver,
    #         # Notification,
    #         Vehicle,
    #         VehicleModel,
    #         DriverAttachmentStatus,
    #     )



    #     post_save.connect(
    #         update_driver_status_for_attchaments_update,
    #         sender=DriverAttachmentStatus,
    #         dispatch_uid="update_driver_status_for_attchaments_update",
    #     )

    #     # post_save.connect(
    #     #     recalculate_max_min_fare,
    #     #     sender=VehicleModel,
    #     #     dispatch_uid="recalculate_max_min_fare",
    #     # )

    #     # post_delete.connect(
    #     #     recalculate_max_min_fare,
    #     #     sender=VehicleModel,
    #     #     dispatch_uid="recalculate_max_min_fare_after_delete",
    #     # )

    #     post_save.connect(
    #         populate_drivers_attachment_status,
    #         sender=Driver,
    #         dispatch_uid="populate_drivers_attachment_status",
    #     )
    #     # post_save.connect(
    #     #     populate_vehicle_attachment_status,
    #     #     sender=Vehicle,
    #     #     dispatch_uid="populate_vehicle_attachment_status",
    #     # )
    #     # post_save.connect(
    #     #     send_notification,
    #     #     sender=Notification,
    #     #     dispatch_uid="send notifications to sockets",
    #     # )
    #     # post_delete.connect(
    #     #     delete_notification, sender=Notification, dispatch_uid="o_0"
    #     # )
