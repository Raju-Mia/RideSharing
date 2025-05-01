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
from payment.helpers import (
    create_connected_account,
    create_account_link, 
    is_stripe_customer,
    create_stripe_account,
    get_the_user_wallet,
    )



User = get_user_model()
# Stripe Account Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY



class DriverBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print("==========i am here!---")
        user = request.user

        # Ensure the user has a Stripe customer account
        try:
            stripe_id = create_stripe_account(user)
        except Exception as e:
            print(f"Error creating Stripe customer or wallet: {str(e)}")
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_200_OK)


        try:
            print("stripe_id is: ", stripe_id)
            # Retrieve the customer object from Stripe
            customer = stripe.Customer.retrieve(stripe_id)

            # Get the balance in pounds (convert from cents to pounds)
            balance = customer.balance / 100  # Convert to dollars, assumed as USD
            balance_in_pounds = balance * 0.78  # Example conversion rate to GBP

            # Retrieve all charges and filter them for the specific customer
            charges = stripe.Charge.list()
            total_spent = sum(charge.amount for charge in charges['data'] if charge.customer == stripe_id) / 100
            total_spent_in_pounds = total_spent * 0.78  # Convert to GBP

            # Retrieve all refunds and filter them for the specific customer
            refunds = stripe.Refund.list()
            total_refunds = sum(refund.amount for refund in refunds['data'] if refund.charge in [charge.id for charge in charges['data']]) / 100
            total_refunds_in_pounds = total_refunds * 0.78  # Convert to GBP

            # Return a response with the balance, total spent, and total refunds in pounds
            return Response({
                "stripe_customer_id": request.user.stripe_id,
                "email": request.user.email,

                "balance_in_pounds": round(balance_in_pounds, 2),
                "total_spent_in_pounds": round(total_spent_in_pounds, 2),
                "total_refunds_in_pounds": round(total_refunds_in_pounds, 2)
            }, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        


class DriverTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            # Ensure the user has a Stripe customer account
            try:
                stripe_id = create_stripe_account(user)
            except Exception as e:
                print(f"Error creating Stripe customer or wallet: {str(e)}")
                return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_200_OK)
            
            
            try:
                # Fetch all charges related to this customer
                charges = stripe.Charge.list(
                    customer=stripe_id,
                    limit=100  # Adjust the limit as needed
                )
            
            except Exception as e:
                print(f"Error creating Stripe customer charges list: {str(e)}")
                return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_200_OK)
            
            
            transactions = []
            # Conversion rate from USD to GBP (example conversion rate)
            conversion_rate_to_gbp = 0.78 # 1 USD = 0.78 GBP

            # Add charges to the transaction list
            for charge in charges.data:
                amount_in_pounds = (charge.amount / 100) * conversion_rate_to_gbp  # Convert cents to GBP
                
                utc_time = datetime.fromtimestamp(charge.created, tz=pytz.UTC)
                bd_time = utc_time.astimezone(pytz.timezone('Asia/Dhaka')).strftime('%Y-%m-%d %H:%M:%S')
                
                
                transactions.append({
                    'id': charge.id,
                    'object': 'charge',
                    'amount': f"£{amount_in_pounds:.2f}",
                    'currency': 'GBP',
                    'status': charge.status,
                    'created': bd_time,
                    'description': charge.description,
                    'receipt_url': charge.receipt_url,
                })
                
            # Sort transactions by creation date (most recent first)
            transactions.sort(key=lambda x: x['created'], reverse=True)

            return Response({"transactions": transactions}, status=status.HTTP_200_OK)
        
        except (ClientWallet.DoesNotExist, DriverWallet.DoesNotExist):
            return Response({"message": "Wallet not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)










class DriverEarningsView(APIView):
    permission_classes = [IsAuthenticated]
    """
    View to retrieve driver earnings directly from Stripe using filter options.
    """

    def post(self, request, *args, **kwargs):
        user = request.user

        if not user.stripe_id:
            return Response({"message": "Stripe Customer Account not found."}, status=status.HTTP_200_OK)

        try:
            wallet = None
            wallet = get_the_user_wallet(user)
            stripe_connected_account_id = wallet.stripe_connected_account_id

        except Exception as e:
            print(f"Error creating Stripe customer or wallet: {str(e)}")
            return Response({"message": "Wallet not found."}, status=status.HTTP_200_OK)

        print("---------I am here-- 0--")

        try:
            # Get parameters from the request body (JSON payload)
            driver_stripe_account = stripe_connected_account_id  # Driver's Stripe connected account ID
            filter_type = request.data.get("filter_type", "weekly")  # Default to "weekly"
            date = request.data.get("date", str(datetime.now().date()))  # Default to today's date

            print("filter_type", filter_type)
            print("date", date)

            # Validate Stripe account ID
            if not driver_stripe_account:
                return JsonResponse({"error": "Stripe account ID is required."}, status=400)

            # Validate and parse date
            try:
                selected_date = parse_date(date)
                if not selected_date:
                    raise ValueError("Invalid date format.")
            except ValueError as e:
                return JsonResponse({"error": str(e)}, status=400)

            # Define time ranges for Stripe API query
            if filter_type == "daily":
                start_time = int(datetime.combine(selected_date, datetime.min.time()).timestamp())
                end_time = int(datetime.combine(selected_date, datetime.max.time()).timestamp())

            elif filter_type == "weekly":
                print("---------I am here-- 1--")
                # Convert selected_date to a datetime object
                start_datetime = datetime.combine(selected_date - timedelta(days=6), datetime.min.time())
                end_datetime = datetime.combine(selected_date, datetime.max.time())
                
                # Get timestamps
                start_time = int(start_datetime.timestamp())
                end_time = int(end_datetime.timestamp())

                print("Start time:", start_time)
                print("End time:", end_time)
                print("---------I am here-- 3--")

                

            elif filter_type == "monthly":
                print("I am here-- monthly2--")
                start_time = int(datetime(selected_date.year, selected_date.month, 1).timestamp())
                next_month = selected_date.month % 12 + 1
                next_month_year = selected_date.year + (1 if selected_date.month == 12 else 0)
                end_time = int(datetime(next_month_year, next_month, 1).timestamp()) - 1

            elif filter_type == "yearly":
                start_time = int(datetime(selected_date.year, 1, 1).timestamp())
                end_time = int(datetime(selected_date.year + 1, 1, 1).timestamp()) - 1

            else:
                return JsonResponse({"error": "Invalid filter type."}, status=400)

            # Fetch transactions from Stripe
            transactions = stripe.BalanceTransaction.list(
                created={"gte": start_time, "lte": end_time},
                stripe_account=driver_stripe_account,
                limit=100  # Adjust as needed
            )

            # Process transactions to calculate earnings
            earnings = {}
            for tx in transactions.auto_paging_iter():
                tx_date = datetime.fromtimestamp(tx["created"]).date()
                tx_amount = tx["amount"] / 100  # Stripe returns amount in cents
                earnings[tx_date] = earnings.get(tx_date, 0) + tx_amount

            # Prepare response
            sorted_earnings = [
                {"date": str(date), "total": total}
                for date, total in sorted(earnings.items())
            ]

            return JsonResponse({
                "success": True,
                "filter_type": filter_type,
                "earnings": sorted_earnings,
                "date": date,
                
                
            }, status=200)

        except stripe.error.StripeError as e:
            return JsonResponse({"error": f"Stripe API error: {str(e)}"}, status=500)

        except Exception as e:
            return JsonResponse({"error": f"An unexpected error occurred: {str(e)}"}, status=500)




class DriverPayoutRequestTransactionListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        print(" i am here!!!")
        user = request.user
        
        if not user.stripe_id:
            return Response({"message": "Stripe Customer Account not found."}, status=status.HTTP_200_OK)
        
        try:
            wallet = None
            wallet = get_the_user_wallet(user)
            stripe_customer_id = wallet.stripe_customer_id
            stripe_connected_account_id = wallet.stripe_connected_account_id
            
        except Exception as e:
            print(f"Error creating Stripe customer or wallet: {str(e)}")
            return Response({"message": "Wallet not found."}, status=status.HTTP_200_OK)
        
        print("stripe_id is: ", stripe_connected_account_id)
        # Retrieve the list of payout requests for the driver
        payout_requests = stripe.Payout.list(
            stripe_account=stripe_connected_account_id
        )
        return Response(payout_requests)



class DriverSuccessfulPayoutTransactionListView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        print(" i am here!!!")
        user = request.user
        
        if not user.stripe_id:
            return Response({"message": "Stripe Customer Account not found."}, status=status.HTTP_200_OK)
        
        try:
            wallet = None
            wallet = get_the_user_wallet(user)
            stripe_customer_id = wallet.stripe_customer_id
            stripe_connected_account_id = wallet.stripe_connected_account_id
            
        except Exception as e:
            print(f"Error creating Stripe customer or wallet: {str(e)}")
            return Response({"message": "Wallet not found."}, status=status.HTTP_200_OK)
        

        # Retrieve all successful payouts for the driver
        successful_payouts = stripe.Payout.list(
            stripe_account=stripe_connected_account_id,
            status="paid"
        )
        return Response(successful_payouts)





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

        if not wallet is None or not stripe_customer_id:
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
                print("new_balance", new_balance)
                

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






# class DriverWithdrawFundsFromCustomerStripeAccount(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user

#         if not user.stripe_id:
#             return Response({"message": "Stripe Customer Account not found."}, status=status.HTTP_400_BAD_REQUEST)
        
#         try:
#             wallet = None
#             wallet = get_the_user_wallet(user)
#             stripe_customer_id = wallet.stripe_customer_id
#             payment_method_id = wallet.default_payment_method_id
            
#         except Exception as e:
#             print(f"Error creating Stripe customer or wallet: {str(e)}")
#             return Response({"message": "Wallet not found."}, status=status.HTTP_200_OK)
        

#         if not wallet.stripe_customer_id:
#             return Response({"message": "Stripe customer not found."}, status=status.HTTP_400_BAD_REQUEST)
    
#         if not payment_method_id:
#             return Response({"message": "No default payment method found."}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             # Amount to withdraw
#             # amount = int(request.data.get("amount", 0))  # Amount in dollars
#             # amount = int(5)  # Amount in dollars
            
#             amount = int(5)
#             conversion_rate_to_gbp = int(0.78)
#             amount_in_pounds = (amount / 100) * conversion_rate_to_gbp  # Convert cents to GBP
            
            
            
#             if amount <= 0:
#                 return Response({"message": "Invalid amount!"}, status=status.HTTP_400_BAD_REQUEST)
            
#             # Check the customer's available balance before processing the withdrawal
#             customer = stripe.Customer.retrieve(wallet.stripe_customer_id)
#             current_balance = int(customer.balance / 100)  # Convert from cents to dollars
#             print("current_balance", current_balance)
            
#             if current_balance < amount:
#                 return Response({"message": "Insufficient balance."}, status=status.HTTP_400_BAD_REQUEST)
            
#             # Create a PaymentIntent to charge the default payment method
#             payment_intent = stripe.PaymentIntent.create(
#                 amount=amount_in_pounds,  # Amount in GBP
#                 currency='GBP',
#                 customer=wallet.stripe_customer_id,
#                 payment_method=payment_method_id,
#                 confirm=True,
#                 capture_method='automatic',
#                 description="Withdrawal from Stripe balance to default card",
#                 automatic_payment_methods={
#                     'enabled': True,
#                     'allow_redirects': 'never'
#                 },
#             )
            
#             # # If the payment is successful, create a refund to mimic the withdrawal
#             # if payment_intent.status == 'succeeded':
#             #     refund = stripe.Refund.create(
#             #         payment_intent=payment_intent.id,
#             #         amount=amount * 100,  # Amount in cents
#             #         reason="requested_by_customer",
#             #     )

#             #     # Manually deduct the amount from the customer's Stripe balance
#             #     print("current_balance", current_balance)
#             #     print("amount is ", amount)
#             #     try:
#             #         print("i am here--1--")
#             #         stripe.Customer.modify(
#             #             wallet.stripe_customer_id,
#             #             balance=int((current_balance - amount) * 100) # Deducting the withdrawal amount from the customer's balance
#             #         )
#             #         print("i am here--3--")
#             #     except stripe.error.StripeError as e:
#             #         print("i am here-555--")
#             #         return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

#             #     if refund.status == 'succeeded':
#             #         return Response({"message": "Withdrawal completed successfully.", "amount_withdrawn": amount}, status=status.HTTP_200_OK)
#             #     else:
#             #         return Response({"message": "Refund failed."}, status=status.HTTP_400_BAD_REQUEST)
#             # else:
#             #     return Response({"message": "Payment failed."}, status=status.HTTP_400_BAD_REQUEST)
            
            
            
            

#         except stripe.error.StripeError as e:
#             return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




class DriverWithdrawFundsFromCustomerStripeAccount(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.stripe_account_id:
            return Response({"message": "Driver does not have a connected Stripe account."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            wallet = get_the_user_wallet(user)

            # Amount to withdraw
            amount = int(request.data.get("amount", 0)) * 100  # Convert dollars to cents
            if amount <= 0:
                return Response({"message": "Invalid amount!"}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve platform's balance
            balance = stripe.Balance.retrieve()
            available_balance = sum([b['amount'] for b in balance['available'] if b['currency'] == 'usd'])
            if available_balance < amount:
                return Response({"message": "Insufficient platform balance."}, status=status.HTTP_400_BAD_REQUEST)

            # Create a transfer to the connected driver's account
            transfer = stripe.Transfer.create(
                amount=amount,
                currency='usd',
                destination=user.stripe_account_id,
                description="Driver withdrawal",
            )

            return Response({"message": "Withdrawal successful.", "transfer": transfer}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from django.core.exceptions import ValidationError
# from time import time



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import stripe
import time
from django.conf import settings
from django.urls import reverse

class DriverConnectingAccountUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        print(" I am here!")
        user = request.user  # Assuming the user is authenticated
        ip_address = request.META.get('REMOTE_ADDR', '0.0.0.0')  # Capture IP address
        
        # Ensure the user has a Stripe customer ID
        if not user.stripe_id:
            return Response(
                {"error": "User does not have a Stripe customer ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Retrieve the driver's wallet
            wallet = DriverWallet.objects.get(user=user)
        except DriverWallet.DoesNotExist:
            return Response(
                {"error": "User does not have a Stripe Connected customer ID."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Proceed to update the connected account if a valid wallet is found
        try:
            # Check if the account is in an onboarding state
            connected_account = stripe.Account.retrieve(wallet.stripe_connected_account_id)
            print("connected_account is: ", connected_account)

            if connected_account["requirements"]["current_deadline"]:
                # If there is a current deadline for requirements (e.g., missing ToS acceptance)
                return Response(
                    {
                        "message": "Driver needs to complete Stripe's onboarding process.",
                        "account_id": connected_account["id"],
                        "onboarding_url": connected_account["links"]["account_onboarding"],
                    },
                    status=status.HTTP_200_OK,
                )

            # Proceed to update the account
            connected_account = stripe.Account.modify(
                wallet.stripe_connected_account_id,  # Existing connected account ID from wallet
                email=user.email,
                business_profile={
                    "name": "United Chauffeur",
                    "product_description": "Ride-sharing services",
                },
                capabilities={
                    "transfers": {"requested": True},
                    "card_payments": {"requested": True},
                },
            )

            # Update the wallet with the new connected account ID (if modified)
            wallet.stripe_connected_account_id = connected_account["id"]
            wallet.save()

            return Response(
                {
                    "message": "Driver's connected account updated successfully.",
                    "account_id": connected_account["id"],
                },
                status=status.HTTP_200_OK,
            )

        except stripe.error.StripeError as e:
            return Response(
                {"error": f"Stripe error: {e.user_message}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
