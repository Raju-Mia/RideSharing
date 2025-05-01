from http.client import HTTPException
from decimal import Decimal

from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views import View
from django.utils.dateparse import parse_date


import pytz
import stripe
from uc_back import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
# from stripe.error import InvalidRequestError
from payment.helpers import create_account_link, is_stripe_customer
from payment.serializers import CardSerializer, BookingPaymentSerializer, ChargeSerializer


from payment.models import ClientWallet, DriverWallet, OrganizationWallet, Transaction
# from accounts.models import Employee
from trip_management.models import Trip

from driver_app.models import Driver

User = get_user_model()
# Stripe Account Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY





class DriverAccountCreateView(APIView): #--1
    """
    Create a Stripe Connected Account for the driver.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        print("I am here for driver account create== Calling post method")
        try:
            account = stripe.Account.create(
                type="express",
                country="US",
                email=user.email,
                business_type="individual",
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True}
                }
            )
            print("I am here!---1")
            # Save the account ID to the driver's wallet model
            driver_wallet, _ = DriverWallet.objects.get_or_create(user=user)
            driver_wallet.stripe_connected_account_id = account["id"]
            driver_wallet.save()
            print("I am here!---2")

            return Response(
                {"message": "Connected account created successfully.", "account_id": account["id"]},
                status=status.HTTP_201_CREATED,
            )

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)




class DriverAccountUpdateView(APIView):
    """
    Update a driver's Stripe Connected Account manually.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        data = request.data

        try:
            driver_wallet = DriverWallet.objects.get(user=user)
            account_id = driver_wallet.stripe_connected_account_id
            print("account_id: ", account_id)

            # Update the Stripe Connected Account
            stripe.Account.modify(
                account_id,
                
                # individual={
                #     "first_name": data.get("first_name"),
                #     "last_name": data.get("last_name"),
                #     "email": user.email,
                #     "dob": {
                #         "day": data.get("dob_day"),
                #         "month": data.get("dob_month"),
                #         "year": data.get("dob_year"),
                #     },
                #     "address": {
                #         "line1": data.get("address_line1"),
                #         "city": data.get("address_city"),
                #         "state": data.get("address_state"),
                #         "postal_code": data.get("address_postal_code"),
                #         "country": "US",
                #     },
                #     "phone": data.get("phone"),
                #     "ssn_last_4": data.get("ssn_last_4"),
                # },
                
                
                external_account={
                    "object": "bank_account",
                    "country": "US",
                    "currency": "usd",
                    "account_number": data.get("account_number"),
                    "routing_number": data.get("routing_number"),
                },
                tos_acceptance={
                    "date": int(data.get("tos_date")),
                    "ip": request.META.get("REMOTE_ADDR"),
                },
            )

            return Response({"message": "Account updated successfully."}, status=status.HTTP_200_OK)

        except DriverWallet.DoesNotExist:
            return Response({"error": "Driver wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)








class DriverAccountStatusView(APIView):
    """
    Retrieve the driver's Stripe account status.
    """

    def get(self, request):
        user = request.user
        print("I am here for driver account status== Calling get method")

        try:
            driver_wallet = DriverWallet.objects.get(user=user)
            account_id = driver_wallet.stripe_connected_account_id

            account = stripe.Account.retrieve(account_id)

            # Provide an overview
            overview = {
                "onboarding_complete": len(account.get("requirements", {}).get("currently_due", [])) == 0,
                "charges_enabled": account.get("charges_enabled", False),
                "transfers_enabled": account.get("transfers_enabled", False),
                "requirements": account.get("requirements", {}),
            }

            return Response({"overview": overview}, status=status.HTTP_200_OK)

        except DriverWallet.DoesNotExist:
            return Response({"error": "Driver wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





class DriverDepositView(APIView):
    """
    Allow drivers to deposit funds for eligibility.
    """

    def post(self, request):
        user = request.user
        data = request.data

        try:
            # Create a PaymentIntent for the deposit
            intent = stripe.PaymentIntent.create(
                amount=int(data.get("amount")) * 100,  # Amount in cents
                currency="usd",
                payment_method=data.get("payment_method"),
                confirm=True,
                customer=user.stripe_customer_id,
            )

            # Update eligibility
            driver_wallet = DriverWallet.objects.get(user=user)
            driver_wallet.cash_trip_deposit += int(data.get("amount"))
            driver_wallet.save()

            return Response({"message": "Deposit successful."}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)





class DriverAccountOnboardingView(APIView):
    """
    Generate an account onboarding link for the driver.
    """
    
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print("I am here for driver account onboarding== Calling get method")
        user = request.user
        driver_wallet = DriverWallet.objects.get(user=user)
        account_id = driver_wallet.stripe_connected_account_id
        print("account_id: ", account_id)
        try:
            link = stripe.AccountLink.create(
                account=account_id,
                refresh_url="http://0.0.0.0:9090/api/payments/v1/driver/onboarding/refresh/",
                return_url="http://0.0.0.0:9090/api/payments/v1/driver/onboarding/complete/",
                type="account_onboarding",
            )
            return Response({'url': link['url']}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)







class DriverDepositView(APIView):
    """
    Allow the driver to deposit money for cash trip eligibility.
    """

    def post(self, request):
        data = request.data
        try:
            # Create a PaymentIntent for the deposit
            payment_intent = stripe.PaymentIntent.create(
                amount=25000,  # £250 in pence
                currency="gbp",
                customer=data['customer_id'],  # Stripe customer ID for the driver
                payment_method=data['payment_method_id'],  # Saved card
                confirm=True,
                metadata={"purpose": "cash_trip_deposit"},
            )
            return Response({'payment_intent': payment_intent}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class TripPaymentDistributionView(APIView):
    """
    Distribute trip revenue between driver and company.
    """

    def post(self, request):
        data = request.data
        try:
            trip_amount = data['trip_amount']  # Total trip fare in pence
            driver_share = int(trip_amount * 0.8)  # 80% for the driver
            company_share = int(trip_amount * 0.2)  # 20% for the company

            # Transfer driver share to their connected account
            stripe.Transfer.create(
                amount=driver_share,
                currency="gbp",
                destination=data['driver_account_id'],  # Driver's Stripe Connected Account ID
                metadata={"purpose": "trip_payment"},
            )

            # Company share remains in the platform's Stripe balance

            return Response({'message': 'Payment distributed successfully'}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class AddBankAccountView(APIView):
    """
    Add a bank account to the driver's Stripe Connected Account.
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        driver_wallet = DriverWallet.objects.get(user=user)
        account_id = driver_wallet.stripe_connected_account_id
        print("account_id: ", account_id)
        try:
            # stripe.Account.create_external_account(
            #     data['account_id'],  # Driver's Stripe Connected Account ID
            #     external_account={
            #         "object": "bank_account",
            #         "country": "GB",
            #         "currency": "gbp",
            #         "account_number": data['account_number'],
            #         "routing_number": data['routing_number'],
            #     },
            # )
            
            stripe.Account.create_external_account(
                account_id,
                external_account={
                    "object": "bank_account",
                    "country": "US",
                    "currency": "usd",
                    "account_number": "000123456",
                    "routing_number": "110000000"
                }
            )



            return Response({'message': 'Bank account added successfully'}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



class DriverAddBankAccountView(APIView):
    """
    Add or update a bank account for the driver's Stripe connected account.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("=========I am here for bank account add=================")
        user = request.user
        driver_wallet = DriverWallet.objects.get(user=user)
        account_id = driver_wallet.stripe_connected_account_id

        # Test bank account details
        bank_account_data = {
            "object": "bank_account",
            "country": "US",
            "currency": "usd",
            "account_number": "000123456",
            "routing_number": "110000000",
        }

        try:
            stripe.Account.create_external_account(
                account_id,
                external_account=bank_account_data
            )
            return Response({"message": "Bank account added successfully."}, status=200)

        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=400)







class DriverPayoutView(APIView):
    """
    Initiate a payout to the driver's bank account.
    """

    def post(self, request):
        data = request.data
        try:
            payout = stripe.Payout.create(
                amount=data['amount'],  # Amount to payout in pence
                currency="gbp",
                stripe_account=data['account_id'],  # Driver's Stripe Connected Account ID
                metadata={"purpose": "driver_payout"},
            )
            return Response({'payout': payout}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



#==================== Test ====================

class CustomerPaymentView(APIView):
    """
    Handle a customer payment and distribute funds between the driver and platform.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("I am here for customer payment== Calling post method")
        try:
            # Get data from the request
            customer_id = request.data.get("customer_id")
            driver_account_id = request.data.get("driver_account_id")
            amount = request.data.get("amount")  # in cents ($100 => 10000)

            if not all([customer_id, driver_account_id, amount]):
                return Response({"error": "Missing required fields."}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve the default payment method for the customer
            customer = stripe.Customer.retrieve(customer_id)
            default_payment_method = customer.get("invoice_settings", {}).get("default_payment_method")

            if not default_payment_method:
                return Response(
                    {"error": "Customer does not have a default payment method set."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Calculate the platform’s fee (20%)
            platform_fee = int(amount * 0.2)

            # Step 1: Create a PaymentIntent for the customer
            payment_intent = stripe.PaymentIntent.create(
                amount=amount,  # Total amount in cents
                currency="usd",
                customer=customer_id,  # Attach the customer
                payment_method=default_payment_method,
                confirm=True,
                automatic_payment_methods={
                    "enabled": True,
                    "allow_redirects": "never",  # Disable redirect-based payment methods
                },
                application_fee_amount=platform_fee,  # 20% to the platform
                transfer_data={
                    "destination": driver_account_id,  # Automatically transfer 80% to the driver
                },
            )

            return Response(
                {
                    "message": "Payment successful!",
                    "payment_intent": payment_intent,
                },
                status=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class DriverAccountInfoView(APIView):
    def get(self, request, driver_id):
        try:
            # Fetch the driver object
            driver = Driver.objects.get(id=driver_id)

            if not driver.connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch account details
            account = stripe.Account.retrieve(driver.connected_account_id)

            # Check onboarding status
            onboarding_complete = (
                account.get("requirements", {}).get("currently_due") == []
                and account.get("charges_enabled")
                and account.get("payouts_enabled")
            )

            if not onboarding_complete:
                return Response(
                    {"message": "Driver onboarding not complete."}, status=status.HTTP_200_OK
                )

            # Fetch balance
            balance = stripe.Balance.retrieve(stripe_account=driver.connected_account_id)

            # Fetch transaction list
            transactions = stripe.BalanceTransaction.list(
                limit=10, stripe_account=driver.connected_account_id
            )
            transaction_list = [txn for txn in transactions.get("data", [])]

            return Response(
                {
                    "balance": balance.get("available", [{"amount": 0}])[0]["amount"] / 100,  # Default to 0
                    "transactions": transaction_list if transaction_list else None,
                },
                status=status.HTTP_200_OK,
            )

        except Driver.DoesNotExist:
            return Response(
                {"error": "Driver not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
