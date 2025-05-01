import decimal
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


from driver_app.models import (
    Driver,
    DriverStatus,
    # DriverAttachmentStatus,
    # Manufacturer,
    Vehicle,
    VehicleModel,
    VehicleStatus,
    # VehicleTypesInfo,
    AttachmentStatus,
)


from .helpers import generate_prefix
from trip_management import models as trip_models
import random

User = get_user_model()


# noinspection PyArgumentList
def send_mail_verification_update_to_driver(user: User):
    print("========== send_mail_verification_update_to_driver calling =======", user)
    channel_layer = get_channel_layer()
    channel_group_name = str(user.id)
    async_to_sync(channel_layer.group_send)(
        channel_group_name,
        {
            "type": "send_email_verification_notification",
            "text": None,
        },
    )


# def populate_drivers_attachment_status(sender, instance, created, **kwargs):
#     if created:
#         # DriverCount.objects.get_or_create(organization=None)
#         json = {"status": AttachmentStatus.pending, "comment": ""}
#         DriverAttachmentStatus.objects.create(
#             driver=instance,
#             driving_license_front_image=json,
#             driving_license_back_image=json,
#             pp_size_driver_image=json,
#             national_insurance=json,
#             criminal_record_book=json,
#             dbl_file=json,
#             dbs_image=json,
#             # pco_license_file=json,
#         )


# def get_or_create_vehicle_type_info(vehicle_type: str, vehicle: Vehicle | None = None):
#     try:
#         return VehicleTypesInfo.objects.get(vehicle_type=vehicle_type)
#     except VehicleTypesInfo.DoesNotExist:
#         return VehicleTypesInfo.objects.create(
#             vehicle_type=vehicle_type,
#             max_min_fare={},
#             max_passengers=vehicle.maximum_passengers if vehicle else 0,
#             max_child_seats=vehicle.number_of_child_seat if vehicle else 0,
#             max_luggage_capacity=vehicle.luggage_capacity if vehicle else 0,
#         )


# def calculate_max_passenger_and_luggage(sender, instance: Vehicle, created, **kwargs):
#     vehicle_type_info = get_or_create_vehicle_type_info(instance.vehicle_type, instance)
#     vehicle_type_info.max_passengers = max(
#         instance.maximum_passengers, vehicle_type_info.max_passengers
#     )
#     vehicle_type_info.max_child_seats = max(
#         instance.number_of_child_seat, vehicle_type_info.max_child_seats
#     )
#     vehicle_type_info.max_luggage_capacity = max(
#         instance.luggage_capacity, vehicle_type_info.max_luggage_capacity
#     )
#     vehicle_type_info.save()


# def calculate_max_min_fare_of_a_vehicle_type(vehicle_type: str) -> None:
#     circles = [
#         "inner_london_fare",
#         "central_london_fare",
#         "orbital_london_fare",
#         "greater_london_fare",
#         "outer_london_fare",
#         "outer_london_circle_one_fare",
#         "outer_london_circle_two_fare",
#     ]
#     vehicle_type_info = get_or_create_vehicle_type_info(vehicle_type)
#     vehicle_models = VehicleModel.objects.filter(vehicle_type=vehicle_type)
#     for model in vehicle_models:
#         for circle in circles:
#             fare_data = getattr(model, circle)
#             try:
#                 _ = vehicle_type_info.max_min_fare[circle]
#             except KeyError:
#                 vehicle_type_info.max_min_fare[circle] = {
#                     "max_fare_per_hour": str(decimal.Decimal("-inf")),
#                     "max_fare_per_mile": str(decimal.Decimal("-inf")),
#                     "min_fare_per_hour": str(decimal.Decimal("inf")),
#                     "min_fare_per_mile": str(decimal.Decimal("inf")),
#                 }
#                 vehicle_type_info.save()
#             vehicle_type_info.max_min_fare[circle]["max_fare_per_hour"] = str(
#                 max(
#                     decimal.Decimal(
#                         vehicle_type_info.max_min_fare[circle]["max_fare_per_hour"]
#                     ),
#                     decimal.Decimal(fare_data["per_hour"]),
#                 ),
#             )
#             vehicle_type_info.max_min_fare[circle]["max_fare_per_mile"] = str(
#                 max(
#                     decimal.Decimal(
#                         vehicle_type_info.max_min_fare[circle]["max_fare_per_mile"]
#                     ),
#                     decimal.Decimal(fare_data["per_mile"]),
#                 ),
#             )
#             vehicle_type_info.max_min_fare[circle]["min_fare_per_hour"] = str(
#                 min(
#                     decimal.Decimal(
#                         vehicle_type_info.max_min_fare[circle]["min_fare_per_hour"]
#                     ),
#                     decimal.Decimal(fare_data["per_hour"]),
#                 ),
#             )
#             vehicle_type_info.max_min_fare[circle]["min_fare_per_mile"] = str(
#                 min(
#                     decimal.Decimal(
#                         vehicle_type_info.max_min_fare[circle]["min_fare_per_mile"]
#                     ),
#                     decimal.Decimal(fare_data["per_mile"]),
#                 ),
#             )
#     vehicle_type_info.save()


# def recalculate_max_min_fare(sender, instance: VehicleModel, **kwargs) -> None:
#     calculate_max_min_fare_of_a_vehicle_type(instance.vehicle_type)


def actions_to_perform_on_vhehicle_save(
    sender, instance: Vehicle, created: bool, **kwargs
):
    if not created:
        pass


# def populate_vehicle_attachment_status(sender, instance, created, **kwargs):
#     if created:
#         data = {"status": AttachmentStatus.pending, "comment": ""}
        # VehicleAttachmentStatus.objects.create(
        #     vehicle=instance,
        #     # bluebook=data,
        #     poc_file=data,
        #     mot=data,
        #     # vehicle_registration_file=data,
        #     vehicle_log_book_V5C=data,
        #     vehicle_insurance=data,
        #     vehicle_front_image=data,
        #     vehicle_back_image=data,
        #     # vehicle_right_image=data,
        #     # vehicle_left_image=data,
        #     vehicle_interior_image=data,
        # )


def create_drivers_account_in_stripe(sender, instance, created, **kwargs):
    if not created:
        if not instance.user.stripe_id:
            pass
            # customer_id = create_stripe_customer()
            # instance.user.stripe_id = customer_id
            # instance.user.save()
            # country = 'US'
            # currency = 'usd'
            # routing_number = "110000000"
            # account_holder_name = instance.user.first_name
            # account_holder_type = "individual"
            # token = create_bank_account_token(account_number=instance.bank_account_number, country=country,
            #                                   currency=currency, routing_number=routing_number,
            #                                   account_holder_name=account_holder_name,
            #                                   account_holder_type=account_holder_type)
            # add_bank_account_to_a_customer(token, customer_id)


def update_rating_info(sender, instance, created, **kwargs):
    """
    Updates rating information in user model everytime new rating is added.
    """
    if instance.user_to_driver:
        driver = instance.driver
        driver.sum_of_ratings += instance.rating
        driver.number_of_ratings += 1
        try:
            driver.rating = driver.sum_of_ratings / driver.number_of_ratings
        except ZeroDivisionError:
            driver.rating = 0.0
        driver.save()
    else:
        user = instance.user
        user.sum_of_ratings += instance.rating
        user.number_of_ratings += 1
        try:
            user.rating = user.sum_of_ratings / user.number_of_ratings
        except ZeroDivisionError:
            user.rating = 0.0
        user.save()


@receiver(post_delete, sender=Driver)
def delete_driver(sender, instance, **kwargs):
    """
    Deletes driver from database when driver is deleted
    """
    instance.user.delete()


# def send_notification_v2(sender, instance, created, **kwargs):
#     if created:
#         send_notification(
#             data=NotificationSerializer(instance).data,
#             notification_type="trip",
#             user=instance.user,
#         )


def send_notification(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        channel_group_name = str(instance.user.id)
        async_to_sync(channel_layer.group_send)(
            channel_group_name,
            {
                "type": "send_notification",
                "text": None,
            },
        )


def delete_notification(sender, instance, *args, **kwargs):
    pass
    # print('sender', sender)
    # print('instance', instance)
    # delete_notification(instance.user.id, instance.id)


def delete_files_when_driver_data_is_deleted(instance, **kwargs):
    # instance.driving_license_front_image.delete()
    # instance.driving_license_back_image.delete()
    # instance.pp_size_driver_image.delete()
    pass


# @receiver(post_save, sender=Organization)
# def create_source(sender, instance, created, **kwargs):
#     """
#     Creates source for organization when organization is created
#     """
#     if created:
#         trip_models.Source.objects.create(
#             name=instance.organization_name, organization=instance, is_active=False
#         )

#     if (not created and instance.is_verified and not instance.source.is_active) or (
#         created
#         and instance.is_verified
#         and instance.user.is_hotel
#         and not instance.source.is_active
#     ):
#         source = instance.source
#         try:
#             prefix = generate_prefix(instance.organization_name)

#             # Generate a random 6-digit number
#             random_num = str(random.randint(100000, 999999))
#             # Concatenate the prefix and the random number
#             key = f"{prefix.upper()}{random_num}"

#             source.prefix = prefix
#             source.key = key
#             source.is_active = True
#             source.save()
#         except:
#             print("Error in creating source")


# from django.db.models import Max
# @receiver(post_save, sender=Driver)
# def add_unique_id(sender, instance, **kwargs):
#     if not instance.unique_id and not instance.count:
#         if not instance.organization:
#             pass
#         max_count = Driver.objects.filter(organization=instance.organization).aggregate(max_count=Max('count'))['max_count']
#         instance.count = 1 if max_count is None else max_count + 1
#         source = trip_models.Source.objects.get(organization=instance.organization)
#         new_unique_id = f"{source.prefix.upper()}{instance.count}"
#         # Set the unique ID field
#         instance.unique_id = new_unique_id


# DriversAllTripsSerializer


# def update_driver_status_for_attchaments_update(
#     sender: DriverAttachmentStatus, instance, created, **kwargs
# ):
#     if created:
#         return
#     fields = [
#         "driving_license_front_image",
#         "driving_license_back_image",
#         "pp_size_driver_image",
#         "national_insurance",
#         "criminal_record_book",
#         "dbl_file",
#         "pco_license_file",
#     ]
#     rejected = False
#     resubmitted = False
#     for field in fields:
#         if getattr(instance, field)["status"] == AttachmentStatus.pending:
#             instance.driver.status = DriverStatus.pending
#             instance.driver.save()
#             return
#         if getattr(instance, field)["status"] == AttachmentStatus.rejected:
#             rejected = True

#         if getattr(instance, field)["status"] == AttachmentStatus.resubmitted:
#             resubmitted = True

#     if rejected:
#         instance.driver.status = DriverStatus.rejected_documents
#         instance.driver.save()
#         return
#     if resubmitted:
#         instance.driver.status = DriverStatus.pending
#         instance.driver.save()


#=============== updated==========
# def update_driver_status_for_attchaments_update(
#     sender: DriverAttachmentStatus, instance, created, **kwargs
#     ):
#     if created:
#         return

#     fields = [
#         "driving_license_front_image",
#         "driving_license_back_image",
#         "pp_size_driver_image",
#         "national_insurance",
#         "criminal_record_book",
#         "dbl_file",
#         "dbs_image",
#         # "pco_license_file",
#     ]
#     rejected = False
#     resubmitted = False




