# from accounts.models import Employee
from http.client import HTTPException
from datetime import datetime, timedelta
from django.utils.dateparse import parse_date
from collections import defaultdict
from django.utils.timezone import now
from datetime import timedelta
from django.utils.timezone import make_aware
import pytz

import stripe
from uc_back import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from payment.helpers import (
    create_connected_account,
    create_account_link, 
    is_stripe_customer,
    create_stripe_account,
    get_the_user_wallet,
    )

from payment.serializers import CardSerializer, BookingPaymentSerializer, ChargeSerializer
from trip_management.models import Trip
from driver_app.models import Driver


from payment.models import ClientWallet, DriverWallet, OrganizationWallet, Transaction
User = get_user_model()

# Stripe Account Secret Key
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
import time
        




#===================================================
#--------- Driver SRIPE CUSTOMER ACCOUNT SETTINGS --
#===================================================


class DriverCreateStripeCustomer(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        print("The user is: ", user, user.service)

        if user.service == "united-chauffeur":
            return Response({'message': 'You are not a driver!'}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Step 1: Check if user has a Stripe customer ID
            wallet, created = DriverWallet.objects.get_or_create(user=user)

            if not wallet.stripe_customer_id:
                customer = stripe.Customer.create(email=user.email, name=user.get_full_name())
                wallet.stripe_customer_id = customer['id']
                wallet.save()
                print("New Stripe Customer ID Created: ", wallet.stripe_customer_id)
            else:
                customer = stripe.Customer.retrieve(wallet.stripe_customer_id)
                print("Existing Stripe Customer Retrieved: ", wallet.stripe_customer_id)

            # Save Stripe ID to user model
            user.stripe_id = str(wallet.stripe_customer_id)
            user.save()

            # Step 2: Create a SetupIntent for Payment Methods
            intent = stripe.SetupIntent.create(payment_method_types=["card"], customer=wallet.stripe_customer_id)
            print("Stripe SetupIntent Created")

            data = {
                "client_secret": intent.client_secret,
                "stripe_customer_id": wallet.stripe_customer_id,
                "message": "Stripe customer account created successfully."
            }

            return Response(data=data, status=status.HTTP_201_CREATED)

        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




