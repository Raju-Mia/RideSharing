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
        


#==== Create Stripe connected Account ======= 0
class DriverStripeAccountWallet(APIView): #phase - 0
    permission_classes = [IsAuthenticated]
    

    def get(self, request):
        user = request.user
        print("I am here for driver account create== Calling post method")
        print("user is ", user)
        if user.service != "united-rydr-driver":
            return Response({"message": "You don't have a Service!"}, status=status.HTTP_200_OK)
        
        if not user.stripe_id:
            print("New Driver Account Create---0---")
            try:
                # account = stripe.Account.create(
                #     type="express",
                #     country="GB", #GB
                #     email=user.email,
                #     business_type="individual",
                #     capabilities={
                #         "card_payments": {"requested": True},
                #         "transfers": {"requested": True}
                #     },

                #     # business_profile={
                #     #     "url": "https://stripe.com",  # Use a generic Stripe link
                #     #     "product_description": "Driver using Rydr App for ride-sharing services.",
                #     # },

                    
                #     # tos_acceptance={
                #     #     "service_agreement": "full",
                #     #     "date": int(time.time()),  # Add current time in seconds
                #     #     "ip": ip_address or "0.0.0.0",  # Add IP address, fallback to default
                #     # }

                #     )
                
                account = stripe.Account.create(
                    type="express",
                    country="GB",  
                    email=user.email,
                    business_type="individual",
                    capabilities={
                        "card_payments": {"requested": True},
                        "transfers": {"requested": True}
                    },
                    
                    # ✅ Auto-fill business details so the driver doesn’t have to enter them manually
                    business_profile={
                        "mcc": "4121",  # Merchant Category Code for "Taxicabs and Ride-Sharing"
                        "product_description": "Driver using Rydr App for ride-sharing services.",
                        "url": "https://rydr-app.com",  # A generic link, prevents Stripe from asking for it
                    },
                    
                )
                print("New Driver Account Create---1---")
                # Save the account ID to the driver's wallet model
                driver_wallet, _ = DriverWallet.objects.get_or_create(user=user)
                driver_wallet.stripe_connected_account_id = account["id"]
                driver_wallet.save()
                print("New Driver Account Create---2---")
                
                # Update the user's Stripe ID(This is Connected Account ID)
                user.stripe_id = account["id"]
                user.save()
                print("New Driver Account Create---3---")
                

                # return Response(
                #     {"message": "Connected account created successfully.", "account_id": account["id"]},
                #     status=status.HTTP_201_CREATED,
                # )
                
                
                try:
                    # Fetch the driver's wallet and connected account ID
                    driver_wallet = DriverWallet.objects.get(user=user)
                    account_id = driver_wallet.stripe_connected_account_id

                    # Retrieve account details from Stripe
                    account = stripe.Account.retrieve(account_id)

                    # Extract capabilities and requirements
                    requirements = account.get("requirements", {})
                    capabilities = {
                        "charges_enabled": account.get("charges_enabled", False),
                        "transfers_enabled": account.get("transfers_enabled", False),
                    }

                    # Determine onboarding status
                    onboarding_complete = (
                        not requirements.get("currently_due")
                        and not requirements.get("past_due")
                        and not requirements.get("pending_verification")
                    )
                    print("New Driver Account Create---1---")
                    
                    
                    # Fetch balance
                    balance = stripe.Balance.retrieve(stripe_account=account_id)

                    # Fetch transaction list
                    transactions = stripe.BalanceTransaction.list(
                        limit=10, stripe_account=account_id
                    )
                    transaction_list = [txn for txn in transactions.get("data", [])]


                    print("New Driver Account Create---2---")

                    # Construct the driver's account overview
                    data = {
                        "balance": balance.get("available", [{"amount": 0}])[0]["amount"] / 100,  # Default to 0
                        "transactions": transaction_list if transaction_list else None,
                        
                        "onboarding_complete": onboarding_complete,
                        "charges_enabled": capabilities["charges_enabled"],
                        "transfers_enabled": capabilities["transfers_enabled"],
                        "requirements": {
                            "currently_due": requirements.get("currently_due", []),
                            "past_due": requirements.get("past_due", []),
                            "pending_verification": requirements.get("pending_verification", []),
                            "errors": requirements.get("errors", []),
                        },
                        "disabled_reason": account.get("disabled_reason", None),
                    }

                    return Response({"wallet": data}, status=status.HTTP_200_OK)


                except Exception as e:
                    # Catch unexpected errors
                    return Response(
                        {"error": f"An unexpected error occurred: {str(e)}"},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )
                
                


            except stripe.error.StripeError as e:
                return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            
        elif user.stripe_id:
            print("Already Driver Account Created---0---")
            try:
                # Fetch the driver's wallet and connected account ID
                driver_wallet = DriverWallet.objects.get(user=user)
                account_id = driver_wallet.stripe_connected_account_id

                # Retrieve account details from Stripe
                account = stripe.Account.retrieve(account_id)

                # Extract capabilities and requirements
                requirements = account.get("requirements", {})
                capabilities = {
                    "charges_enabled": account.get("charges_enabled", False),
                    "transfers_enabled": account.get("transfers_enabled", False),
                }

                # Determine onboarding status
                onboarding_complete = (
                    not requirements.get("currently_due")
                    and not requirements.get("past_due")
                    and not requirements.get("pending_verification")
                )
                print("Already Driver Account Created---1---")
                
                
                # Fetch balance
                balance = stripe.Balance.retrieve(stripe_account=account_id)

                # Fetch transaction list
                transactions = stripe.BalanceTransaction.list(
                    limit=10, stripe_account=account_id
                )
                transaction_list = [txn for txn in transactions.get("data", [])]


                print("Already Driver Account Created---2---")

                # Construct the driver's account overview
                data = {
                    "balance": balance.get("available", [{"amount": 0}])[0]["amount"] / 100,  # Default to 0
                    "transactions": transaction_list if transaction_list else None,
                    
                    "onboarding_complete": onboarding_complete,
                    "charges_enabled": capabilities["charges_enabled"],
                    "transfers_enabled": capabilities["transfers_enabled"],
                    "requirements": {
                        "currently_due": requirements.get("currently_due", []),
                        "past_due": requirements.get("past_due", []),
                        "pending_verification": requirements.get("pending_verification", []),
                        "errors": requirements.get("errors", []),
                    },
                    "disabled_reason": account.get("disabled_reason", None),
                }

                return Response({"wallet": data}, status=status.HTTP_200_OK)

            except DriverWallet.DoesNotExist:
                return Response(
                    {"error": "Driver wallet not found for this user."},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except stripe.error.InvalidRequestError as e:
                # Handle specific Stripe API errors (e.g., invalid account ID)
                return Response(
                    {"error": f"Stripe error: {e.user_message or str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            except stripe.error.StripeError as e:
                # Catch other Stripe-related errors
                return Response(
                    {"error": f"An error occurred while communicating with Stripe: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            except Exception as e:
                # Catch unexpected errors
                return Response(
                    {"error": f"An unexpected error occurred: {str(e)}"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
                
        else:
            return Response({"message": "Something went wrong!"}, status=status.HTTP_403_FORBIDDEN)
            
 
        
        
    
# Driver Stripe Account Onboarding Completed====== 1
# class DriverAccountOnboardingComplate(APIView):
#     """
#     Generate an account onboarding link for the driver.
#     """
    
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         print("I am here for driver account onboarding== Calling get method")
#         user = request.user
#         driver_wallet = DriverWallet.objects.get(user=user)
#         account_id = driver_wallet.stripe_connected_account_id
#         print("account_id: ", account_id)
#         try:
#             link = stripe.AccountLink.create(
#                 account=account_id,
#                 refresh_url="http://0.0.0.0:9090/api/payments/v1/driver/onboarding/refresh/",
#                 return_url="http://0.0.0.0:9090/api/payments/v1/driver/onboarding/complete/",
#                 type="account_onboarding",
#             )
#             return Response({'url': link['url']}, status=status.HTTP_200_OK)

#         except stripe.error.StripeError as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



from rest_framework.authtoken.models import Token

class DriverAccountOnboardingComplate(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        driver_wallet = DriverWallet.objects.get(user=user)
        account_id = driver_wallet.stripe_connected_account_id

        # Get or create the authentication token for the user
        token, created = Token.objects.get_or_create(user=user)

        try:
            link = stripe.AccountLink.create(
                account=account_id,
                # refresh_url="https://dev-api.uc.co.uk/api/payments/v1/driver/onboarding/refresh/",
                # return_url=f"https://dev-api.uc.co.uk/api/payments/v1/driver/onboarding/complete/?token={token.key}",

                refresh_url="https://dev.rydr.app/drive/verify-info/",
                return_url=f"https://dev.rydr.app/drive/verify-info/?token={token.key}",

                type="account_onboarding",
            )
            return Response({'url': link['url']}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



# Driver Stripe Account Bank Account list ====== 2
class DriverBankAccountListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        print("I am here for driver bank account list== Calling get method")
        try:
            # Fetch the driver object
            wallet = DriverWallet.objects.get(user=user)

            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch all external bank accounts for the connected account
            external_accounts = stripe.Account.list_external_accounts(
                wallet.stripe_connected_account_id,
                object="bank_account"
            )
        


            # Prepare response data
            bank_accounts = [
                {
                    "id": account.id,
                    "last4": account.last4,
                    "bank_name": account.bank_name,
                    "status": account.status,
                    "currency": account.currency,
                    "country": account.country,
                    

                    "object": account.object,
                    "account": account.account,
                    "available_payout_methods": account.available_payout_methods,
                    "default_for_currency": account.default_for_currency,
                    "fingerprint": account.fingerprint,
                    "metadata": {},
                    "routing_number": account.routing_number,

            
            
            
                }
                for account in external_accounts["data"]
            ]

            return Response(
                {"bank_accounts": bank_accounts if bank_accounts else None},
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




# Driver Stripe Account Bank Account Detail ====== 3
class DriverBankAccountDetails(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, bank_account_id):
        user = request.user
        print("I am here for driver bank account details== Calling get method")
        try:
            # Fetch the driver object
            wallet = DriverWallet.objects.get(user=user)



            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch specific bank account details
            bank_account = stripe.Account.retrieve_external_account(
                wallet.stripe_connected_account_id,
                bank_account_id,
            )
            


            # Prepare response data
            bank_account_details = {
                "id": bank_account.id,
                "last4": bank_account.last4,
                "bank_name": bank_account.bank_name,
                "status": bank_account.status,
                "currency": bank_account.currency,
                "country": bank_account.country,
                "routing_number": bank_account.routing_number,
                # "bank_accounts": bank_account['data']
            }
            

            return Response(
                {"bank_account_details": bank_account_details},
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





class DriverStripeAccountStatusView(APIView): #main
    # permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        try:
            # Fetch the driver wallet object
            wallet = DriverWallet.objects.get(user=user)

            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Retrieve connected account details
            account = stripe.Account.retrieve(wallet.stripe_connected_account_id)

            # Check if the account is active
            account_status_details = {
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "requirements_due": account.requirements.currently_due,
            }

            # Account is active if charges and payouts are enabled, and no requirements are due
            account_active = (
                account.charges_enabled
                and account.payouts_enabled
                and not account.requirements.currently_due
            )

            return Response(
                {
                    "account_status": "active" if account_active else "inactive",
                    "details": account_status_details,
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
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# from rest_framework.authentication import TokenAuthentication
# from rest_framework.authtoken.models import Token

# class DriverStripeAccountStatusView(APIView): #Test
#     authentication_classes = [TokenAuthentication]  # Enable token authentication
#     permission_classes = [IsAuthenticated]

#     def get(self, request):
#         # Manually authenticate using token from query parameters
#         token_key = request.GET.get("token")
#         if not token_key:
#             return Response({"error": "Authentication token is missing."}, status=status.HTTP_401_UNAUTHORIZED)

#         try:
#             token = Token.objects.get(key=token_key)
#             user = token.user  # Retrieve user from token
#             request.user = user  # Manually set the user

#             # Fetch the driver wallet object
#             wallet = DriverWallet.objects.get(user=user)

#             if not wallet.stripe_connected_account_id:
#                 return Response(
#                     {"error": "Driver does not have a connected Stripe account."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#             # Retrieve connected account details
#             account = stripe.Account.retrieve(wallet.stripe_connected_account_id)

#             account_status_details = {
#                 "charges_enabled": account.charges_enabled,
#                 "payouts_enabled": account.payouts_enabled,
#                 "requirements_due": account.requirements.currently_due,
#             }

#             account_active = (
#                 account.charges_enabled
#                 and account.payouts_enabled
#                 and not account.requirements.currently_due
#             )

#             return Response(
#                 {
#                     "account_status": "active" if account_active else "inactive",
#                     "details": account_status_details,
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except Token.DoesNotExist:
#             return Response({"error": "Invalid authentication token."}, status=status.HTTP_401_UNAUTHORIZED)
#         except DriverWallet.DoesNotExist:
#             return Response({"error": "Driver wallet not found."}, status=status.HTTP_404_NOT_FOUND)
#         except stripe.error.StripeError as e:
#             return Response({"error": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# Payout or Withdraw Eligibility
class DriverPayoutEligibilityView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        try:
            # Fetch the driver wallet object
            wallet = DriverWallet.objects.get(user=user)
            
            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Retrieve the balance of the connected account
            balance = stripe.Balance.retrieve(stripe_account=wallet.stripe_connected_account_id)
            available_balance = balance['available'][0]['amount'] / 100  # Convert from cents to pounds

            # Check if the balance is sufficient for withdrawal
            withdrawal_threshold = 50  # Minimum balance required for withdrawal in pounds
            eligible = available_balance >= withdrawal_threshold

            return Response(
                {
                    "withdrawal_eligible": eligible,
                    "available_balance": available_balance,
                    "minimum_threshold": withdrawal_threshold,
                },
                status=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )




class DriverPayoutScheduleStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        try:
            # Retrieve the driver's wallet and connected account ID
            wallet = DriverWallet.objects.get(user=user)
            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Fetch connected account details from Stripe
            account = stripe.Account.retrieve(wallet.stripe_connected_account_id)

            # Extract payout schedule details
            payout_schedule = account.settings.payouts.schedule.interval

            return Response(
                {
                    "payout_schedule": payout_schedule  # "daily", "weekly", or "manual"
                },
                status=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )




# Setting Payout Schedule Setup
class DriverPayoutScheduleSetupView(APIView):
    permission_classes = [IsAuthenticated]
    
    '''
    After setting the payout schedule to manual, implement a separate endpoint where drivers can request their payout. 
    This will create a Stripe Payout from the connected account to the driver's bank account.
    
    "manual": Payouts are initiated manually through API requests.
    "daily": Payouts are automatically processed daily.
    "weekly": Payouts are automatically processed weekly.
    '''

    def post(self, request):
        user = request.user
        payout_schedule = request.data.get("payout_schedule", "manual")  # Default to 'manual'

        if payout_schedule not in ["daily", "weekly", "manual"]:
            return Response(
                {"error": "Invalid payout schedule. Options are: 'daily', 'weekly', 'manual'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            wallet = DriverWallet.objects.get(user=user)

            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Update payout schedule for the connected account
            stripe.Account.modify(
                wallet.stripe_connected_account_id,
                settings={"payouts": {"schedule": {"interval": payout_schedule}}},
            )

            return Response(
                {"message": f"Payout schedule set to '{payout_schedule}'."},
                status=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )





# Manual Payout Request
class DriverManualPayoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        amount = request.data.get("amount")  # Amount in pounds (£)

        try:
            # Validate the amount input
            if not amount:
                return Response(
                    {"error": "Amount is required."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            
            try:
                amount = float(amount)
            except ValueError:
                return Response(
                    {"error": "Invalid amount format."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if amount <= 0:
                return Response(
                    {"error": "Withdrawal amount must be greater than zero."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Minimum withdrawal threshold
            MIN_WITHDRAWAL_THRESHOLD = 50.0

            wallet = DriverWallet.objects.get(user=user)
            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Retrieve the balance of the connected account
            balance = stripe.Balance.retrieve(stripe_account=wallet.stripe_connected_account_id)
            
            # Convert available balance from cents to pounds
            available_balance = balance['available'][0]['amount'] / 100

            # Check if the available balance meets the minimum withdrawal threshold
            if available_balance < MIN_WITHDRAWAL_THRESHOLD:
                return Response(
                    {"error": f"Insufficient balance. Minimum available balance required is £{MIN_WITHDRAWAL_THRESHOLD}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Check if the requested amount exceeds the available balance
            if amount > available_balance:
                return Response(
                    {"error": f"Requested amount (£{amount}) exceeds available balance (£{available_balance})."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Convert amount to cents and create a payout
            amount_in_cents = int(amount * 100)

            # Create payout to the connected account's default bank account
            stripe.Payout.create(
                amount=amount_in_cents,
                currency="gbp",
                stripe_account=wallet.stripe_connected_account_id,
            )

            return Response(
                {"message": f"Payout of £{amount} initiated successfully."},
                status=status.HTTP_200_OK,
            )

        except DriverWallet.DoesNotExist:
            return Response(
                {"error": "Driver wallet not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )





# Stripe’s Hosted Dashboard Link: Stripe Express Dashboard
class DriverStripeExpressDashboard(APIView):
    permission_classes = [IsAuthenticated]
    
    '''
    Drivers can manage their payout settings, including adding or updating bank accounts, directly through this dashboard.
    '''

    def get(self, request):
        try:
            user = request.user
            wallet = DriverWallet.objects.get(user=user)

            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Generate the login link for the Stripe Express Dashboard
            login_link = stripe.Account.create_login_link(wallet.stripe_connected_account_id)

            return Response(
                {"dashboard_url": login_link.url},
                status=status.HTTP_200_OK
            )

        except DriverWallet.DoesNotExist:
            return Response({"error": "Driver wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# DriverAllTransactionsListView
class DriverAllTransactionsListView(APIView):
    permission_classes = [IsAuthenticated]
    
    '''
    This view retrieves all transactions related to a driver's connected Stripe account.
    '''

    def get(self, request):
        user = request.user
        try:
            wallet = DriverWallet.objects.get(user=user)

            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Retrieve all transactions for the connected account
            transactions = stripe.BalanceTransaction.list(
                stripe_account=wallet.stripe_connected_account_id
            )

            return Response(
                {"transactions": transactions['data']},
                status=status.HTTP_200_OK,
            )

        except DriverWallet.DoesNotExist:
            return Response(
                {"error": "Driver wallet not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )




# DriverPayoutRequestTransactionListView
class DriverPayoutRequestTransactionListView(APIView):
    permission_classes = [IsAuthenticated]
    
    '''
    This view fetches only transactions categorized as payout requests (pending payouts).
    '''

    def get(self, request):
        user = request.user
        try:
            wallet = DriverWallet.objects.get(user=user)

            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Retrieve pending payout transactions for the connected account
            payouts = stripe.Payout.list(
                stripe_account=wallet.stripe_connected_account_id,
                status='pending'  # Filter by pending payouts
            )

            return Response(
                {"payout_requests": payouts['data']},
                status=status.HTTP_200_OK,
            )

        except DriverWallet.DoesNotExist:
            return Response(
                {"error": "Driver wallet not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


# DriverSuccessfulPayoutTransactionListView
class DriverSuccessfulPayoutTransactionListView(APIView):
    permission_classes = [IsAuthenticated]
    
    '''
    This view lists completed (successful) payouts for the driver.
    '''

    def get(self, request):
        user = request.user
        try:
            wallet = DriverWallet.objects.get(user=user)

            if not wallet.stripe_connected_account_id:
                return Response(
                    {"error": "Driver does not have a connected Stripe account."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Retrieve successful payouts for the connected account
            successful_payouts = stripe.Payout.list(
                stripe_account=wallet.stripe_connected_account_id,
                status='paid'  # Filter by successful payouts
            )

            return Response(
                {"successful_payouts": successful_payouts['data']},
                status=status.HTTP_200_OK,
            )

        except DriverWallet.DoesNotExist:
            return Response(
                {"error": "Driver wallet not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"Internal server error: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



# Driver  weekly, monthly, and yearly earnings
class DriverEarningsDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    
    '''
    Time Range Calculation:
    Defined appropriate time ranges for daily, weekly, monthly, and yearly earnings using timestamps.
    Ensured all days or months are included even if they have zero earnings.
    
    Transaction Processing:
    Organized earnings data into dictionaries for days (weekly), dates (monthly), or months (yearly).
    Ensured earnings are aggregated for each day/month.
    
    Structured Responses:
    Weekly: Outputs earnings for each day of the week.
    Monthly: Provides earnings for each day in the month and includes the total monthly earnings.
    Yearly: Summarizes earnings for each month and calculates the total yearly earnings.
        
    '''

    def post(self, request, *args, **kwargs):
        user = request.user
        
        print

        if not user.stripe_id:
            return Response({"error": "Stripe Customer Account not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet = DriverWallet.objects.get(user=user)
            stripe_connected_account_id = wallet.stripe_connected_account_id

            if not stripe_connected_account_id:
                return Response({"error": "Stripe connected account not found."}, status=status.HTTP_400_BAD_REQUEST)

        except DriverWallet.DoesNotExist:
            return Response({"error": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)

        filter_type = request.data.get("filter_type", "weekly")  # Default to "weekly"
        date = request.data.get("date", str(datetime.now().date()))  # Default to today's date

        try:
            selected_date = parse_date(date)
            if not selected_date:
                raise ValueError("Invalid date format.")
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Define time ranges for Stripe API query
            if filter_type == "daily":
                start_time = int(datetime.combine(selected_date, datetime.min.time()).timestamp())
                end_time = int(datetime.combine(selected_date, datetime.max.time()).timestamp())

            elif filter_type == "weekly":
                start_datetime = datetime.combine(selected_date - timedelta(days=selected_date.weekday()), datetime.min.time())
                end_datetime = start_datetime + timedelta(days=6, hours=23, minutes=59, seconds=59)
                start_time, end_time = int(start_datetime.timestamp()), int(end_datetime.timestamp())

            elif filter_type == "monthly":
                start_time = int(datetime(selected_date.year, selected_date.month, 1).timestamp())
                next_month = selected_date.month % 12 + 1
                next_month_year = selected_date.year + (1 if selected_date.month == 12 else 0)
                end_time = int(datetime(next_month_year, next_month, 1).timestamp()) - 1

            elif filter_type == "yearly":
                start_time = int(datetime(selected_date.year, 1, 1).timestamp())
                end_time = int(datetime(selected_date.year + 1, 1, 1).timestamp()) - 1

            else:
                return Response({"error": "Invalid filter type."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch transactions from Stripe
            transactions = stripe.BalanceTransaction.list(
                created={"gte": start_time, "lte": end_time},
                stripe_account=stripe_connected_account_id,
                limit=100  # Adjust as needed
            )

            # Process transactions to calculate earnings
            earnings = defaultdict(float)

            for tx in transactions.auto_paging_iter():
                tx_date = datetime.fromtimestamp(tx["created"]).date()
                tx_amount = tx["amount"] / 100  # Stripe returns amount in cents
                
                if filter_type == "weekly":
                    day_name = tx_date.strftime("%A")
                    earnings[day_name] += tx_amount
                elif filter_type == "monthly":
                    earnings[str(tx_date)] += tx_amount
                elif filter_type == "yearly":
                    month_name = tx_date.strftime("%B")
                    earnings[month_name] += tx_amount

            # Prepare response based on filter type
            if filter_type == "weekly":
                # The week in the United Kingdom generally starts on Monday and ends on Sunday.
                # Ensure all days are present in the response
                days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                data = [{"day": day, "earnings": round(earnings[day], 2)} for day in days_of_week]
                total_earnings = round(sum(earnings.values()), 2)
                return Response({"success": True, "filter_type": "weekly", "total_earnings": total_earnings, "currency": "GBP", "data": data}, status=status.HTTP_200_OK)

            elif filter_type == "monthly":
                data = [{"date": date, "earnings": round(total, 2)} for date, total in sorted(earnings.items())]
                total_earnings = round(sum(earnings.values()), 2)
                return Response({"success": True, "filter_type": "monthly", "total_earnings": total_earnings, "currency": "GBP", "data": data}, status=status.HTTP_200_OK)

            elif filter_type == "yearly":
                months_of_year = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                data = [{"month": month, "earnings": round(earnings[month], 2)} for month in months_of_year]
                total_earnings = round(sum(earnings.values()), 2)
                return Response({"success": True, "filter_type": "yearly", "total_earnings": total_earnings, "currency": "GBP", "data": data}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": f"Stripe API error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#========== Driver Eearing overview Details for this week, this month, this Year==
# Driver  weekly, monthly, and yearly earnings
class DriverEarningsDetailsOverView(APIView):
    permission_classes = [IsAuthenticated]
    
    '''
        
    '''

    def post(self, request, *args, **kwargs):
        user = request.user
        
        print

        if not user.stripe_id:
            return Response({"error": "Stripe Customer Account not found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet = DriverWallet.objects.get(user=user)
            stripe_connected_account_id = wallet.stripe_connected_account_id

            if not stripe_connected_account_id:
                return Response({"error": "Stripe connected account not found."}, status=status.HTTP_400_BAD_REQUEST)

        except DriverWallet.DoesNotExist:
            return Response({"error": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)

        filter_type = request.data.get("filter_type", "weekly")  # Default to "weekly"
        date = request.data.get("date", str(datetime.now().date()))  # Default to today's date

        try:
            selected_date = parse_date(date)
            if not selected_date:
                raise ValueError("Invalid date format.")
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Define time ranges for Stripe API query
            if filter_type == "daily":
                start_time = int(datetime.combine(selected_date, datetime.min.time()).timestamp())
                end_time = int(datetime.combine(selected_date, datetime.max.time()).timestamp())

            elif filter_type == "weekly":
                start_datetime = datetime.combine(selected_date - timedelta(days=selected_date.weekday()), datetime.min.time())
                end_datetime = start_datetime + timedelta(days=6, hours=23, minutes=59, seconds=59)
                start_time, end_time = int(start_datetime.timestamp()), int(end_datetime.timestamp())

            elif filter_type == "monthly":
                start_time = int(datetime(selected_date.year, selected_date.month, 1).timestamp())
                next_month = selected_date.month % 12 + 1
                next_month_year = selected_date.year + (1 if selected_date.month == 12 else 0)
                end_time = int(datetime(next_month_year, next_month, 1).timestamp()) - 1

            elif filter_type == "yearly":
                start_time = int(datetime(selected_date.year, 1, 1).timestamp())
                end_time = int(datetime(selected_date.year + 1, 1, 1).timestamp()) - 1

            else:
                return Response({"error": "Invalid filter type."}, status=status.HTTP_400_BAD_REQUEST)

            # Fetch transactions from Stripe
            transactions = stripe.BalanceTransaction.list(
                created={"gte": start_time, "lte": end_time},
                stripe_account=stripe_connected_account_id,
                limit=100  # Adjust as needed
            )

            # Process transactions to calculate earnings
            earnings = defaultdict(float)


            # Driver Total Trip (this week, this month, this year).
            driver = Driver.objects.get(user=user)
            if driver:
                # print("The driver is: ", driver)
                # total_trips = Trip.objects.filter(driver=driver, trip_status="Completed").first()
                # print("Total trip count booking_time: ", total_trips.booking_time)


                # Trips within this week (Monday to Saturday, inclusive)

                # Convert Unix timestamps to aware datetime objects
                timezone = pytz.UTC
                start_time = make_aware(datetime.fromtimestamp(start_time), timezone)
                end_time = make_aware(datetime.fromtimestamp(end_time), timezone)

                # Extract only the date part for filtering
                start_date = start_time.date()
                end_date = end_time.date()

                print("Start Date:", start_date)
                print("End Date:", end_date)

                

                if filter_type == "weekly":
                    # Weekly trips (Monday to Saturday, inclusive)
                    trips_this_week = Trip.objects.filter(
                        driver=driver,
                        trip_status="Completed",
                        pickup_time__date__range=[start_date, end_date]
                    ).count()

                    print(f"Trips this week (Monday to {end_date.strftime('%A')}): {trips_this_week}")

                elif filter_type == "monthly":
                    # # Monthly filter: First and last dates of the month
                    # first_day_of_month = start_time.replace(day=1).date()
                    # last_day_of_month = end_time.replace(day=1).date().replace(month=end_time.month + 1 if end_time.month < 12 else 1) - timedelta(days=1)


                    # print("first_day_of_month:", first_day_of_month)
                    # print("last_day_of_month", last_day_of_month)


                    # Total trips for the current month using `__date` lookup
                    total_trips_this_month = Trip.objects.filter(
                        driver=driver,
                        trip_status="Completed",
                        pickup_time__date__range=[start_date, end_date]
                    ).count()

                    print("Total trips this month:", total_trips_this_month)

                elif filter_type == "yearly":
                    # # Yearly filter: First and last dates of the year
                    # first_day_of_year = start_time.replace(month=1, day=1).date()
                    # last_day_of_year = end_time.replace(month=1, day=1).date().replace(year=end_time.year + 1) - timedelta(days=1)

                    # print("first_day_of_year:", first_day_of_year)
                    # print("last_day_of_year", last_day_of_year)

                    # Total trips for the current year using `__date` lookup
                    total_trips_this_year = Trip.objects.filter(
                        driver=driver,
                        trip_status="Completed",
                        pickup_time__date__range=[start_date, end_date]
                    ).count()

                    print("Total trips this year:", total_trips_this_year)

                else:
                    return Response({"error": "Invalid filter type."}, status=status.HTTP_400_BAD_REQUEST)
                
                



            else:
                return Response({"error": "You don't have driver profile!"}, status=status.HTTP_400_BAD_REQUEST)

            for tx in transactions.auto_paging_iter():
                tx_date = datetime.fromtimestamp(tx["created"]).date()
                tx_amount = tx["amount"] / 100  # Stripe returns amount in cents
                
                if filter_type == "weekly":
                    day_name = tx_date.strftime("%A")
                    earnings[day_name] += tx_amount
                elif filter_type == "monthly":
                    earnings[str(tx_date)] += tx_amount
                elif filter_type == "yearly":
                    month_name = tx_date.strftime("%B")
                    earnings[month_name] += tx_amount

            # Prepare response based on filter type
            if filter_type == "weekly":
                # The week in the United Kingdom generally starts on Monday and ends on Sunday.
                # Ensure all days are present in the response
                days_of_week = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
                data = [{"day": day, "earnings": round(earnings[day], 2)} for day in days_of_week]
                total_earnings = round(sum(earnings.values()), 2)
                return Response({"success": True, "filter_type": "weekly", "total_earnings": total_earnings, "currency": "GBP", "total_trips": trips_this_week, "active_time": "30 hrs"}, status=status.HTTP_200_OK)

            elif filter_type == "monthly":
                data = [{"date": date, "earnings": round(total, 2)} for date, total in sorted(earnings.items())]
                total_earnings = round(sum(earnings.values()), 2)
                return Response({"success": True, "filter_type": "monthly", "total_earnings": total_earnings, "currency": "GBP", "total_trips": total_trips_this_month, "active_time": "30 hrs"}, status=status.HTTP_200_OK)

            elif filter_type == "yearly":
                months_of_year = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
                data = [{"month": month, "earnings": round(earnings[month], 2)} for month in months_of_year]
                total_earnings = round(sum(earnings.values()), 2)
                return Response({"success": True, "filter_type": "yearly", "total_earnings": total_earnings, "currency": "GBP", "total_trips": total_trips_this_year, "active_time": "30 hrs"}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"error": f"Stripe API error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






#===================================================
#---------------- SRIPE CUSTOMER ACCOUNT SETTINGS ------------------
#===================================================


# Set Default Payout Bank Account
class SetDefaultBankAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Set a specific bank account as the default payout account.
        """
        try:
            user = request.user
            wallet = DriverWallet.objects.get(user=user)
            bank_account_id = request.data.get("bank_account_id")
            print("bank_account_id",bank_account_id)
            
            
            if not wallet.stripe_connected_account_id or not bank_account_id:
                return Response(
                    {"error": "Missing connected account or bank account ID."},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Set the bank account as default for payouts
            stripe.Account.modify_external_account(
                wallet.stripe_connected_account_id,
                bank_account_id,
                default_for_currency=True
            )

            return Response(
                {"message": "Default payout bank account set successfully!"},
                status=status.HTTP_200_OK
            )

        except DriverWallet.DoesNotExist:
            return Response({"error": "Driver wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






# User Cusotmer Secret key
class StripeUserSecret(APIView): #phase-1
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        wallet = None
        # Check if the user has a Stripe ID
        if not user.stripe_id:
            try:
                
                # Create a new Stripe customer TODO: Get the email or number 
                customer = stripe.Customer.create(email=user.email)
                user.stripe_id = str(customer.id)
                user.save()
            

                print("User service is: ", user.service, type(user.service))
                if user.service == "united-chauffeur":
                    # Create or get the user's wallet
                    print("User service is: united-chauffeur")
                    wallet, created = ClientWallet.objects.get_or_create(user=user)
                    wallet.stripe_customer_id = customer.id
                    wallet.save()
                    
                elif user.service == "united-rydr-driver":
                    print("User service is: united-rydr-driver")
                    # Create or get the driver's wallet
                    print("------i am here-- 0--")
                    wallet, created = DriverWallet.objects.get_or_create(user=user)
                    print("------i am here-- 00--")
                    wallet.stripe_customer_id = customer.id
                    print("------i am here-- 000--")
                    wallet.save()
                    print("------i am here-- 1--")
                    
                    # Example of usage after driver registration
                    if not wallet.stripe_connected_account_id:
                        print("Created: connected_account_id for Driver!")
                        connected_account_id = create_connected_account(wallet.user.email)
                        if connected_account_id:
                            wallet.stripe_connected_account_id = connected_account_id
                            wallet.save()
                            
                        
                else:
                    return Response({"message": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
                
            except stripe.error.StripeError as e:
                return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"message": "An error occurred while creating the Stripe customer."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        print("------i am here-- 2--")
        try:
            # Create a SetupIntent for the customer
            user = request.user
            print("------i am here-- 3--")
            intent = stripe.SetupIntent.create(
                payment_method_types=["card"], 
                customer=user.stripe_id
            )
            print("------i am here-- 4--")
            
            print("intent.client_secret: ", intent.client_secret)
            data = {
                "client_secret": intent.client_secret,
                "message": "Stripe customer created successfully." if not user.stripe_id else "SetupIntent created successfully."
            }
            return Response(data=data, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": "An error occurred while creating the SetupIntent."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





# Add Payment method. --2nd
class AddPaymentMethodView(APIView): #phase - 2 (Client/Customer)
    permission_classes = [IsAuthenticated]
    
    def get(self, request): # no need
        user = request.user
        wallet = None
        if not request.user.stripe_id:
            customer = stripe.Customer.create()
            user.stripe_id = str(customer.id)
            user.save()
            
            # Store the customer ID in the user's wallet
            print("Create Sripe Customer ----------here---2--")
            print("User service is: ", user.service, type(user.service))
            if user.service == "united-chauffeur":
                print("i am here--as client")
                # Create or get the user's wallet
                wallet, created = ClientWallet.objects.get_or_create(user=user)
                wallet.stripe_customer_id = customer.id
                wallet.save()
                
            elif user.service == "united-rydr-driver":
                print("i am here--as driver")
                # Create or get the driver's wallet
                wallet, created = DriverWallet.objects.get_or_create(user=user)
                wallet.stripe_customer_id = customer.id
                wallet.save()
            else:
                return Response({"message": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
            
                
        intent = stripe.SetupIntent.create(
            payment_method_types=["card"], customer=str(request.user.stripe_id)
            )
        data = {
            "client_secret": intent.client_secret,
            "message": "Stripe customer created successfully."
            }
        return Response(status=status.HTTP_200_OK, data=data)
    
    

    def post(self, request):
        user = request.user
        wallet = None
        print("User service is: ", user.service, type(user.service))
        try:
            if user.service == "united-chauffeur":
                wallet = ClientWallet.objects.get(user=user)
            elif user.service == "united-rydr-driver":
                wallet = DriverWallet.objects.get(user=user)
            else:
                return Response({"message": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
        except ClientWallet.DoesNotExist or DriverWallet.DoesNotExist:
            return Response({"message": "Wallet not found."}, status=status.HTTP_400_BAD_REQUEST)
                
        if not wallet.stripe_customer_id:
            return Response({"message": "Stripe customer not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        print("wallet is ", wallet)
        
        
        payment_method_id = request.data.get("payment_method_id") #payment method id mean: default card id.
        # payment_method_id = str("pm_1PpmC5GZW19xRTaoKWjygIA9")
        print("payment_method_id", payment_method_id)
        if not payment_method_id:
            print("Payment Method id is not provide!")
            return Response({"message": "Payment method ID is required."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            print("--i am here--1")
            # Attach the payment method to the Stripe customer
            stripe.PaymentMethod.attach(
                payment_method_id,
                customer=wallet.stripe_customer_id,
            )
            print("--i am here--2")
            
            # Fetch the current default payment method
            customer = stripe.Customer.retrieve(wallet.stripe_customer_id)
            default_payment_method_id = customer.invoice_settings.default_payment_method
            
            # If there's no default payment method, set the new one as default
            if not default_payment_method_id:
                stripe.Customer.modify(
                    wallet.stripe_customer_id,
                    invoice_settings={
                        'default_payment_method': payment_method_id,
                    },
                )
                
                # Update the wallet with the new default payment method
                wallet.default_payment_method_id = payment_method_id
                wallet.save()    
                print("--In wallet Primary payment method  card id set successfully--")
            
            
                print("--i am here--3")
                message = "Payment method added and set as default."
            else:
                print("--i am here--4")
                message = "New Payment method added successfully."
            
            return Response({"message": message}, status=status.HTTP_201_CREATED)
        
        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








class ViewUserCardsInfo(APIView):  #Phase-3
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        wallet = None
        
        
        try:
            print(" i ma here--1")
            if not user.stripe_id:
                print(" i ma here--2")

                customer = stripe.Customer.create()
                user.stripe_id = str(customer.id)
                user.save()
                
                print("User service is: ", user.service, type(user.service))
                if user.service == "united-chauffeur":
                    # Create or get the user's wallet
                    print("User service is: united-chauffeur")
                    wallet, created = ClientWallet.objects.get_or_create(user=user)
                    wallet.stripe_customer_id = customer.id
                    wallet.save()
                    
                elif user.service == "united-rydr-driver":
                    print("User service is: united-rydr-driver")
                    # Create or get the driver's wallet
                    wallet, created = DriverWallet.objects.get_or_create(user=user)
                    wallet.stripe_customer_id = customer.id
                    wallet.save()
                else:
                    return Response({"error": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
                
                
                
                
            else:
                print(" i ma here--3")
                customer = stripe.Customer.retrieve(request.user.stripe_id)
                print(" i ma here--4")
                

            payment_methods = stripe.PaymentMethod.list(
                customer=customer.id, type="card"
            )
            payment_method_objects = payment_methods.data
            payload = []
            
            card_logos = {
                "visa": "https://drive.google.com/uc?export=view&id=1ngjJ-okelAQ3Ir13dm6xKrIkdKJCC7Gb",
                "mastercard": "https://drive.google.com/uc?export=view&id=1Vayk-L92CjrGk-ZjYLIlxw9XEwnS3X4G",
                "amex": "https://drive.google.com/uc?export=view&id=1JOlwvY8oI6UlM6Pn1ymGft650ilEfumT",
                "discover": "https://drive.google.com/uc?export=view&id=15XnJS04RsVmf-cq5N6VMzRKUulwHYr-0",
                "diners_club": "https://drive.google.com/uc?export=view&id=190EAGJy6bE2p9TrpI99FllkcFJ6h3cNk",
                "jcb": "https://drive.google.com/uc?export=view&id=1mSqQ8bLXH-v4piIXDEH_FaOrH1n-4f_i",
                "maestro": "https://drive.google.com/uc?export=view&id=1LAaGfquaj5LHBdLYFMVkVhYapb3Kw0xF",
                "unionpay": "https://drive.google.com/uc?export=view&id=1KqWnslX1GytGrHWXNqZroiwf2DozWhNB",
                "solo": "https://drive.google.com/uc?export=view&id=1d1JVaarj4hVi4r1y46l5wPtccYPwMNnY",
                "visa_electron": "https://drive.google.com/uc?export=view&id=1mO9gzVqEDv0xhrFtKDChw7iRtDAe-ld7",
                "amazon": "https://drive.google.com/uc?export=view&id=12e-mldOXU7lB31q1fYEjB4uWL3ISfqyH",
                "circus": "https://drive.google.com/uc?export=view&id=1WYsLzWgEfw42DtYfQaPXgWJ1OQtj52HU",
                "direct_debit": "https://drive.google.com/uc?export=view&id=1VJSEYe-ZGk06dJURkVdNVZIQz2CQsU7e",
                "ebuy": "https://drive.google.com/uc?export=view&id=1RHijU04CEDx99Spmfls4fmYvleqDA1lV",
                "eway": "https://drive.google.com/uc?export=view&id=1jhWFM4fpzD41t2CcQcsC6mJwHcDUpBrC",
                "google_wallet": "https://drive.google.com/uc?export=view&id=1olVJNh1Kjw9yerZW_YsRG9tTW0rhWCuD",
                "moneybookers": "https://drive.google.com/uc?export=view&id=1BnClkJaWrDwlq5_QPGtYKAivwrDJJjE2",
                "paypal": "https://drive.google.com/uc?export=view&id=1rt-psVjKL-27PH8ZP5MjP_3P9o4r1-Hv",
                "sage": "https://drive.google.com/uc?export=view&id=11Zs7ryXwYXU2L7MAw45KxRIuuK6pmMv-",
                "shopify": "https://drive.google.com/uc?export=view&id=1ERlcbCMO-vaIx6SFpNTpolSJpPh8eI1z",
                "skrill": "https://drive.google.com/uc?export=view&id=1ucL9JgIgpIYVIJQyNNNOQFb2y5ZJbyfE",
                "worldpay": "https://drive.google.com/uc?export=view&id=1NLNT5dfS6IZWuGiWrIe5aqkZKy4dY1N1",
                "default": "https://drive.google.com/uc?export=view&id=1ngjJ-okelAQ3Ir13dm6xKrIkdKJCC7Gb"  # Add a generic card logo URL here
            }

            for payment_method in payment_method_objects:
                card_brand = payment_method.card.brand.lower()
                logo_url = card_logos.get(card_brand, card_logos["default"])
                
                payload.append(
                    {
                        "id": payment_method.id,
                        "brand": payment_method.card.brand,
                        "last4": payment_method.card.last4,
                        "exp_month": payment_method.card.exp_month,
                        "exp_year": payment_method.card.exp_year,
                        "funding": payment_method.card.funding,
                        "name": payment_method.billing_details.name,
                        "address_line1": payment_method.billing_details.address.line1,
                        "address_line2": payment_method.billing_details.address.line2,
                        "address_city": payment_method.billing_details.address.city,
                        "address_state": payment_method.billing_details.address.state,
                        "address_postal_code": payment_method.billing_details.address.postal_code,
                        "address_country": payment_method.billing_details.address.country,
                        "logo": logo_url,
                        "is_primary": payment_method.id == customer.invoice_settings.default_payment_method,
                    }
                )
            payload.sort(key=lambda x: not x['is_primary'])
            
            return Response({"cards": payload}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data=str(e))







        

class SetPrimaryCard(APIView): #phase - 4
    permission_classes = [IsAuthenticated]

    def post(self, request, payment_method_id):
        user = request.user
        
        try:
            # Fetch the correct wallet based on the user's service type
            if user.service == "united-chauffeur":
                wallet = ClientWallet.objects.get(user=user)
            elif user.service == "united-rydr-driver":
                wallet = DriverWallet.objects.get(user=user)
            else:
                return Response({"message": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Modify the Stripe customer's default payment method
            stripe.Customer.modify(
                user.stripe_id,
                invoice_settings={
                    "default_payment_method": payment_method_id
                }
            )

            # Update the wallet with the new default payment method
            wallet.default_payment_method_id = payment_method_id
            wallet.save()
            print("--In wallet Primary payment method  card id set successfully--")

            return Response(
                {"message": "Primary card set successfully"},
                status=status.HTTP_200_OK
            )
        except ClientWallet.DoesNotExist:
            return Response({"message": "Client wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        except DriverWallet.DoesNotExist:
            return Response({"message": "Driver wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class RemoveUuserCard(APIView):  # Phase-5
    permission_classes = [IsAuthenticated]

    def delete(self, request, payment_method_id):
        user = request.user

        if not user.stripe_id:
            return Response({"message": "User has no Stripe account!"}, status=status.HTTP_403_FORBIDDEN)

        try:
            # Retrieve the customer's details from Stripe
            customer = stripe.Customer.retrieve(user.stripe_id)
            default_payment_method_id = customer.invoice_settings.default_payment_method
            
            # Check if the card to be deleted is the default payment method
            if payment_method_id == default_payment_method_id:
                return Response({"message": "Cannot delete the default payment method. Please set another card as default first."}, status=status.HTTP_403_FORBIDDEN)

            # Retrieve the payment method to ensure it exists
            _ = stripe.PaymentMethod.retrieve(payment_method_id)

            # Detach the payment method (remove it from the customer's account)
            stripe.PaymentMethod.detach(payment_method_id)
            
            return Response(status=status.HTTP_200_OK, data={"detail": "Card removed successfully"})
        
        except stripe.error.InvalidRequestError:
            return Response({"message": "Invalid payment method ID or something went wrong!"}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        


class DriverAddFundsToCustomerStripeAccount(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.stripe_id:
            return Response({"message": "Stripe Customer Account not found."}, status=status.HTTP_200_OK)
        
        
        try:
            wallet = None
            wallet = get_the_user_wallet(user)
            stripe_customer_id = wallet.stripe_customer_id
            payment_method_id = wallet.default_payment_method_id
            
        except Exception as e:
            print(f"Error creating Stripe customer or wallet: {str(e)}")
            return Response({"message": "Wallet not found."}, status=status.HTTP_200_OK)

        print("stripe_customer_id: ", stripe_customer_id)
        print("payment_method_id: ", payment_method_id)

        # if not wallet is None or not stripe_customer_id:
        #     return Response({"message": "Stripe customer not found."}, status=status.HTTP_200_OK)


        if not wallet or not stripe_customer_id:
            return Response({"message": "Stripe customer not found."}, status=status.HTTP_200_OK)

            
        if not payment_method_id:
            return Response({"message": "No default payment method found."}, status=status.HTTP_200_OK)

        try:
            # Amount to add as fund
            # amount = int(request.data.get("amount", 0))  # Amount in dollars
            amount = int(250)
            conversion_rate_to_gbp = int(0.78)
            amount_in_pounds = (amount / 100) * conversion_rate_to_gbp  # Convert cents to GBP
            
            if amount <= 0:
                return Response({"message": "Invalid amount!"}, status=status.HTTP_400_BAD_REQUEST)

            # Create a PaymentIntent to charge the default payment method
            print("i am here--1---")
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_in_pounds,  # Amount in GBP
                currency='GBP',
                customer=stripe_customer_id,
                payment_method=payment_method_id,
                confirm=True,
                description="Adding funds to Stripe balance",
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never'
                },
            )
            print("i am here--2---")

            if payment_intent.status == 'succeeded':
                print("i am here--3--")
                
                # Retrieve the current customer balance
                customer = stripe.Customer.retrieve(wallet.stripe_customer_id)
                current_balance = customer.balance
                print("current_balance", current_balance)

                # Add the new amount to the current balance
                new_balance = current_balance + payment_intent.amount  # Amount is in cents
                print("new_balance: ", new_balance)
                

                # Update the customer's Stripe balance
                stripe.Customer.modify(
                    wallet.stripe_customer_id,
                    balance=new_balance,  # This amount is in cents
                )
                
            
                
                print("i am here--4--")




                return Response({"message": "Funds added successfully.", "amount_added": round(amount, 2)}, status=status.HTTP_200_OK)
            else:
                return Response({"message": "Payment failed."}, status=status.HTTP_400_BAD_REQUEST)

        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



