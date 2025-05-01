
from django.contrib.auth import get_user_model
from django.db.models.functions import Upper
from django.contrib.postgres.aggregates import ArrayAgg

from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from rest_framework.filters import OrderingFilter, SearchFilter
from accounts.helpers import haversine_distance
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import permissions, status
from rest_framework.response import Response
from trip_management.models import Trip

from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import (
    GenericAPIView,
    RetrieveAPIView,
    get_object_or_404,
    ListAPIView,
    CreateAPIView,
    ListCreateAPIView,
    RetrieveUpdateAPIView,
    UpdateAPIView,
)
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import LimitOffsetPagination
from rest_framework import viewsets
from utils.pagination import CustomPageNumberPagination #RM Add

from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.exceptions import ValidationError
# from rest_framework.permissions import IsAdmin



from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt import views, serializers
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
# from rest_framework.pagination import PageNumberPagination



from utils.helpers import generate_otp
from utils.validators import password_validator
from utils.mail import send_email_verification_token
from utils.sms import send_phone_verification_sms, sms_token_is_verified



from accounts.helpers import (
    create_user,
    get_attachments_status,
    get_user_details,
    info_from_google,
    send_reset_password_code,
    update_driver_vehicle_info_status,
)


from accounts.mail import send_mail

from driver_app.models import (
    Driver,
    Vehicle,
    DriverProfileEditRequest,
    AttachmentStatus,
)

from uc_back import settings
from payment.models import ClientWallet, DriverWallet, OrganizationWallet, Transaction
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
import time




from accounts.permissions import (
    IsDriver,
    IsNotDriver,
    IsOrganization,
    is_driver,
    DriverWithNoRegisteredVehicle,
)



from driver_app.serializers import (
    DriversToAssignTripSerializer,
    
    )

User = get_user_model()





# =========== Verifited Driver list============
from django.db.models import Q
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError

import firebase_admin
from firebase_admin import messaging, credentials
from notification_manager.firebase_init import initialize_firebase
initialize_firebase()

from notification_manager.utils_helper import send_push_notification
from notification_manager.models import FCMToken, NotifyMessage

from django.contrib.auth import get_user_model
User = get_user_model()

   


class GetAllVerifiedDriversToAssignTrip(ListAPIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination
    serializer_class = DriversToAssignTripSerializer

 
    def get_queryset(self):
        trip_id = self.kwargs.get('trip_id')
        if not trip_id:
            raise ValidationError({"message": "Trip ID is required."})
        trip = get_object_or_404(Trip, id=trip_id)
        driver = Driver.objects.all().order_by('-updated_at')
        return driver

    def get(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()
            if not queryset:
                return Response(
                    {"message": "No drivers found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except DatabaseError as e:
            return Response(
                {"message": "A database error occurred. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {"message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




class DriverVehicleStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        driver = Driver.objects.filter(user=user).first()
        if DriverProfileEditRequest.objects.filter(user=driver.user).exists():
            driver_profile_edit_request = DriverProfileEditRequest.objects.filter(user=driver.user).last()
            driver_profile_picture_status = driver_profile_edit_request.status
            print(driver_profile_edit_request.id)
        else:
            driver_profile_picture_status = 'required'

        if driver:
            driver_document_statuses = [
                driver.driving_license_no_status,
                driver.dvla_plastic_driving_licence_status,
                driver.private_hire_driving_licence_status,
                driver_profile_picture_status,
            ]
            if all(status == AttachmentStatus.verified for status in driver_document_statuses):
                driver_status = "Completed"
            elif any(status in [AttachmentStatus.submitted, AttachmentStatus.resubmitted, AttachmentStatus.rejected, AttachmentStatus.expired] for status in driver_document_statuses):
                driver_status = "In Review"
            else:
                driver_status = "Required"
        else:
            driver_status = "Required"
        
        vehicle = Vehicle.objects.filter(owner=driver).first() if driver else None
        if vehicle:
            vehicle_document_statuses = [
                vehicle.vehicle_reg_no_status,
                vehicle.insurance_certificate_status,
                vehicle.mot_test_certificate_status,
                vehicle.private_hire_vehicle_licence_status,
                vehicle.log_book_V5C_status
            ]
            if all(status == AttachmentStatus.verified for status in vehicle_document_statuses):
                vehicle_status = "Completed"
            elif any(status in [AttachmentStatus.submitted, AttachmentStatus.resubmitted,  AttachmentStatus.rejected, AttachmentStatus.expired] for status in vehicle_document_statuses):
                vehicle_status = "In Review"
            else:
                vehicle_status = "Required"
        else:
            vehicle_status = "Required"

        customer_account_status = False
        card_added_status = False
        payouts_enabled = False

        try:
            wallet = DriverWallet.objects.get(user=user)

            if wallet.stripe_customer_id:
                customer_account_status = True

                payment_methods = stripe.PaymentMethod.list(
                    customer=wallet.stripe_customer_id,
                    type="card"
                )

                if payment_methods.get("data"):
                    card_added_status = True

            if not wallet.stripe_connected_account_id:
                return Response(
                    {
                        "driver_status": driver_status,
                        "vehicle_status": vehicle_status,
                        "stripe_account_status": "inactive",
                        "stripe_details": {"error": "Driver does not have a connected Stripe account."},
                        "customer_account_status": customer_account_status,
                        "card_added_status": card_added_status,
                        "driver": "unverified",
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )

            account = stripe.Account.retrieve(wallet.stripe_connected_account_id)

            account_status_details = {
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "requirements_due": account.requirements.currently_due,
            }

            payouts_enabled = account.payouts_enabled

            account_active = (
                account.charges_enabled
                and account.payouts_enabled
                and not account.requirements.currently_due
            )

            stripe_response = {
                "account_status": "active" if account_active else "inactive",
                "details": account_status_details,
            }

        except DriverWallet.DoesNotExist:
            stripe_response = {
                "account_status": "inactive",
                "details": {"error": "Driver wallet not found."}
            }

        except stripe.error.StripeError as e:
            stripe_response = {
                "account_status": "inactive",
                "details": {"error": f"Stripe error: {str(e)}"}
            }

        except Exception as e:
            stripe_response = {
                "account_status": "inactive",
                "details": {"error": str(e)}
            }

        if driver_status == "Completed" and vehicle_status == "Completed" and payouts_enabled:
            driver_verification_status = "verified"
        else:
            driver_verification_status = "unverified"

        return Response(
            {
                "driver_status": driver_status,
                "vehicle_status": vehicle_status,
                "stripe_account_status": stripe_response["account_status"],
                "stripe_details": stripe_response["details"],
                "customer_account_status": customer_account_status,
                "card_added_status": card_added_status,
                "driver": driver_verification_status,
            },
            status=status.HTTP_200_OK
        )
