



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






def check_sufficient_funds(user, amount):
    """
    Check if the user's default payment method has sufficient funds to cover the amount.
    
    :param user: The user object containing the Stripe customer ID.
    :param amount: The amount to check against the available balance.
    :return: True if sufficient funds are available, False otherwise.
    """
    try:
        # Retrieve the Stripe customer
        customer = stripe.Customer.retrieve(user.stripe_id)
        
        # Get the default payment method
        default_payment_method_id = customer.invoice_settings.default_payment_method
        if not default_payment_method_id:
            print("No default payment method found.")
            return False
        
        # Create a PaymentIntent with manual capture to check for available funds
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Amount in cents
                currency='gbp',  # Use GBP as the currency (or 'usd')
                customer=user.stripe_id,
                payment_method=default_payment_method_id,
                off_session=True,
                capture_method='manual',  # Only authorize the amount, don't capture yet
                confirm=True,
            )
            
            # If the PaymentIntent's status is 'requires_capture', the funds are available
            if payment_intent.status == 'requires_capture':
                return True
            else:
                return False
        
        except stripe.error.CardError as e:
            # Card was declined or insufficient funds
            print(f"Card error: {e}")
            return False
        
    except stripe.error.StripeError as e:
        print(f"Stripe error: {e}")
        return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False

class HoldPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        user = request.user
        try:
            trip = Trip.objects.get(id=trip_id, user=user)
            
            wallet = None
            if user.service == "united-chauffeur":
                wallet = ClientWallet.objects.get(user=user)
            elif user.service == "united-rydr-driver":
                wallet = DriverWallet.objects.get(user=user)
            else:
                return Response({"message": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
            
            if trip.payment_status != 'hold':
                return Response({"error": "Trip status is not on hold."}, status=status.HTTP_400_BAD_REQUEST)

            amount = trip.final_fare

            # Check if the client's default card has sufficient funds
            if not check_sufficient_funds(user, amount):
                return Response({"error": "Insufficient funds on the default payment method."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create a PaymentIntent to hold the amount
            payment_intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Amount in cents
                currency='gbp',  # Use GBP as the currency (or 'usd')
                customer=user.stripe_id,
                payment_method=wallet.default_payment_method_id,
                off_session=True,
                capture_method='manual',  # Only authorize the amount, don't capture yet
            )
            trip.payment_intent_id = payment_intent.id
            trip.save()

            return Response({"message": "Payment authorized and held successfully."}, status=status.HTTP_200_OK)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class CompletePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        user = request.user
        
        try:
            
            wallet = None
            if user.service == "united-chauffeur":
                wallet = ClientWallet.objects.get(user=user)
                payment_method_id = wallet.default_payment_method_id
            elif user.service == "united-rydr-driver":
                wallet = DriverWallet.objects.get(user=user)
                payment_method_id = wallet.default_payment_method_id
            else:
                return Response({"message": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
            
            
            
            trip = Trip.objects.get(id=trip_id, user=user)
            if trip.payment_status != 'complete':
                return Response({"error": "Trip status is not complete."}, status=status.HTTP_400_BAD_REQUEST)


            payment_intent = stripe.PaymentIntent.retrieve(trip.payment_intent_id)
            if payment_intent.status == 'requires_capture':
                held_amount = payment_intent.amount / 100  # Convert to dollars
                final_fare = trip.final_fare

                if final_fare > held_amount:
                    # Capture the held amount and create a new PaymentIntent for the difference
                    stripe.PaymentIntent.capture(payment_intent.id, amount=int(held_amount * 100))

                    remaining_amount = final_fare - held_amount
                    new_payment_intent = stripe.PaymentIntent.create(
                        amount=int(remaining_amount * 100),
                        currency='usd',
                        customer=request.user.stripe_id,
                        payment_method=request.user.clientwallet.default_payment_method_id,
                        off_session=True,
                        capture_method='automatic',  # Automatically capture the remaining amount
                    )
                    amount = held_amount + new_payment_intent.amount_received / 100

                elif final_fare < held_amount:
                    # Capture only the final fare amount
                    stripe.PaymentIntent.capture(payment_intent.id, amount=int(final_fare * 100))
                    amount = final_fare

                else:
                    # Capture the full held amount
                    stripe.PaymentIntent.capture(payment_intent.id)
                    amount = held_amount

                driver_amount = amount * 0.8
                company_amount = amount * 0.2

                # Transfer 80% to the driver's account
                stripe.Transfer.create(
                    amount=int(driver_amount * 100),  # Amount in cents
                    currency='usd',
                    destination=trip.driver.stripe_account_id,
                    transfer_group=trip.id,
                )

                # Transfer 20% to the company's Stripe account
                stripe.Transfer.create(
                    amount=int(company_amount * 100),  # Amount in cents
                    currency='usd',
                    destination='COMPANY_STRIPE_ACCOUNT_ID',
                    transfer_group=trip.id,
                )

                return Response({"message": "Payment captured and distributed successfully."}, status=status.HTTP_200_OK)

            return Response({"error": "Payment intent not in a capturable state."}, status=status.HTTP_400_BAD_REQUEST)
        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




