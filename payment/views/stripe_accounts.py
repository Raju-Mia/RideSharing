



from http.client import HTTPException

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



User = get_user_model()
# Stripe Account Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY



class MerchantAccountBalance(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Retrieve the balance from Stripe
            balance = stripe.Balance.retrieve()

            # Extract available balance in each currency
            available_balance = balance['available']
            
            # Construct a response with the available balance details
            balance_info = {
                'usd': next((item['amount'] for item in available_balance if item['currency'] == 'usd'), 0) / 100,
                'eur': next((item['amount'] for item in available_balance if item['currency'] == 'eur'), 0) / 100,
                # Add other currencies as needed
            }

            return Response(balance_info, status=status.HTTP_200_OK)
        
        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        



class CustomerBalanceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customer_id = request.user.stripe_id  # Assuming the Stripe customer ID is stored in the user model

        if not customer_id:
            return Response({"message": "Customer ID not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Retrieve the customer object from Stripe
            customer = stripe.Customer.retrieve(customer_id)

            # Get the balance, which represents the total outstanding balance on the customer's account
            # A positive balance is money owed by the customer (e.g., from unpaid invoices).
            # A negative balance is credit available to the customer (e.g., from overpayments or refunds).
            balance = customer.balance / 100  # Convert from cents to dollars
            
            # Retrieve all charges and filter them for the specific customer
            charges = stripe.Charge.list()
            total_spent = sum(charge.amount for charge in charges['data'] if charge.customer == customer_id) / 100  # Convert from cents to dollars

            # Retrieve all refunds and filter them for the specific customer
            refunds = stripe.Refund.list()
            total_refunds = sum(refund.amount for refund in refunds['data'] if refund.charge in [charge.id for charge in charges['data'] if charge.customer == customer_id]) / 100  # Convert from cents to dollars

            

            data = {
                "stripe_customer_id": request.user.stripe_id,
                "customer_name": request.user.full_name,
                "email": request.user.email,
                "number": request.user.phone,
                "balance": balance,  # This is the total available balance or outstanding amount
                
                "total_spent": total_spent,
                "total_refunds": total_refunds,
                
                
            }

            return Response(data, status=status.HTTP_200_OK)
        
        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class CustomerHasBalance(APIView):  # dont know what is this
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print('You dont have stripe ID ', request.user.stripe_id or ' ') 

        user = self.request.user
        
        try:
            fare = int(100)
            # fare = request.data.get("fare")

        except InvalidRequestError:
            return Response({"message": "Invalid Fare Amount!"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        print("fare is ", fare)
        if not user.stripe_id:
            return Response({"message": "Stripe customer not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            print(" i am here---1---")
            balance = stripe.Balance.retrieve()
            print(" i am here---2---")
            balance = balance["available"][0]["amount"]
            print(" i am here---3---", balance)
        except InvalidRequestError:
            return Response({"message": "Stripe Blance Retrieve have problem!"}, status=status.HTTP_400_BAD_REQUEST)
        
        
        if int(balance) > int(fare):
            data = {
                "balance": balance,
                "has_balance": False,
                "message": "Fare amount is sufficient"
                }
            return Response(data, status=status.HTTP_200_OK)
        else:
            data = {
                "balance": balance,
                "has_balance": False,
                "message": "Fare amount is bigger than user balance"
                }
            return Response(data, status=status.HTTP_200_OK)
            
            





class CustomerTransactionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        try:
            # Get the customer's wallet
            if user.service == "united-chauffeur":
                wallet = ClientWallet.objects.get(user=user)
            elif user.service == "united-rydr-driver":
                wallet = DriverWallet.objects.get(user=user)
            else:
                return Response({"message": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Fetch all payment intents related to this customer
            payment_intents = stripe.PaymentIntent.list(
                customer=wallet.stripe_customer_id,
                limit=100  # Adjust the limit as needed
            )
            
            # Fetch all charges related to this customer
            charges = stripe.Charge.list(
                customer=wallet.stripe_customer_id,
                limit=100  # Adjust the limit as needed
            )
            
            transactions = []

            # Add payment intents to the transaction list
            for intent in payment_intents.data:
                transactions.append({
                    'id': intent.id,
                    'object': 'payment_intent',
                    'amount': intent.amount,
                    'currency': intent.currency,
                    'status': intent.status,
                    'created': intent.created,
                    'description': intent.description,
                })

            # Add charges and associated refunds to the transaction list
            for charge in charges.data:
                transactions.append({
                    'id': charge.id,
                    'object': 'charge',
                    'amount': charge.amount,
                    'currency': charge.currency,
                    'status': charge.status,
                    'created': charge.created,
                    'description': charge.description,
                    'receipt_url': charge.receipt_url,
                })
                
                # Fetch refunds associated with this charge
                refunds = stripe.Refund.list(charge=charge.id)
                for refund in refunds.data:
                    transactions.append({
                        'id': refund.id,
                        'object': 'refund',
                        'amount': refund.amount,
                        'currency': refund.currency,
                        'status': refund.status,
                        'created': refund.created,
                        'charge_id': refund.charge,
                        'reason': refund.reason,
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






# Utility function to check if user is a Stripe customer
def is_stripe_customer(user):
    return bool(user.stripe_id)

class UserHasCard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Check if the user has a Stripe ID (is a Stripe customer)
        if not is_stripe_customer(user):
            print(f'User {user} does not have a Stripe ID.')
            return Response({"has_card": False, "message": "User is not a Stripe customer."}, status=status.HTTP_200_OK)

        try:
            # Retrieve the user's Stripe customer object
            customer = stripe.Customer.retrieve(user.stripe_id)
            
            # Retrieve the list of cards (payment methods) associated with the customer
            payment_methods = stripe.PaymentMethod.list(
                customer=user.stripe_id,
                type="card"
            )

            if payment_methods.data:
                return Response({"has_card": True}, status=status.HTTP_200_OK)
            else:
                return Response({"has_card": False, "message": "No card associated with this user."}, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
