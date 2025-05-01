
from http.client import HTTPException
from decimal import Decimal

import stripe
from uc_back import settings
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
# from stripe.error import InvalidRequestError

#Import
from payment.helpers import create_connected_account, create_account_link, is_stripe_customer
from payment.serializers import CardSerializer, BookingPaymentSerializer, ChargeSerializer

from payment.models import ClientWallet, DriverWallet, OrganizationWallet, Transaction
# from accounts.models import Employee
from trip_management.models import PaymentMethods, PaymentStatus, Trip

User = get_user_model()
# Stripe Account Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY
from django.core.exceptions import ValidationError



def trip_payment_method_type(trip):
    """
    This function checks the payment method.
    """

    if trip.payment_method == PaymentMethods.CARD:
        return trip.payment_method

    elif trip.payment_method == PaymentMethods.CASH:
        return trip.payment_method

    else:
        return trip.payment_method


def trip_payment_method_id(trip):
    """
    This function checks the payment method Id.
    """

    if trip.payment_card_id:
        return trip.payment_card_id


    if trip.payment_card_id is None:
            message = "No payment card ID is associated with the trip."
            return None




def check_sufficient_funds(user, amount):
    """
    Check if the user's default payment method has sufficient funds to cover the amount.
    
    :param user: The user object containing the Stripe customer ID.
    :param amount: The amount to check against the available balance.
    :return: True if sufficient funds are available, False otherwise.
    """
    
    # Note: Stripe does not provide an API to check balance directly. Typically, this is managed by the issuing bank.
    # For this example, we will assume that the check is abstracted as `check_sufficient_funds` function.
    
    print("Now, I am calling check the user sufficient funds.")

    try:
        # Retrieve the Stripe customer
        customer = stripe.Customer.retrieve(user.stripe_id)
        print("Stripe Customer is: ")
        
        # Get the default payment method
        default_payment_method_id = customer.invoice_settings.default_payment_method
        if not default_payment_method_id:
            print("No default payment method found.")
            return False
        
        print("default_payment_method_id: ", default_payment_method_id)
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









def check_trip_payment_method(trip, user, amount):
    # Step 1: Check if the trip has a valid payment method type (card or cash)
    if not trip.payment_method == "Card":
        return {"message": "Payment method type is cash."}
    
    # Step 2: Check if the payment method ID is associated with the trip
    payment_method_id = trip.payment_method_id
    if not payment_method_id:
        return {"message": "No payment method ID associated with this trip."}
    
    # Step 3: Verify if the user has the payment method
    try:
        customer_payment_methods = stripe.PaymentMethod.list(
            customer=user.stripe_id
        )
        
        # Check if the payment method ID is one of the user's saved payment methods
        user_payment_method_ids = [pm['id'] for pm in customer_payment_methods['data']]
        if payment_method_id not in user_payment_method_ids:
            return {"message": "Payment method id not found for this user."}
        
    except stripe.error.StripeError as e:
        return {"message": f"Stripe error: {str(e)}"}
    except Exception as e:
        return {"message": f"An error occurred: {str(e)}"}
    
    # Step 4: Check if the card has sufficient balance for the trip amount
    # Note: Stripe does not provide an API to check balance directly. Typically, this is managed by the issuing bank.
    # For this example, we will assume that the check is abstracted as `check_sufficient_funds` function.
    if not check_sufficient_funds(user, amount):
        return {"message": "Insufficient funds on the payment method."}
    
    # Step 5: Return the payment method ID if all checks pass
    return {"payment_method_id": payment_method_id}






class HoldPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        print("I am calling PaymentHoldView.")
        print("trip_id: ", trip_id)
        user = request.user
        print("user: ", user)
        try:
            trip = Trip.objects.get(id=trip_id, user=user)
            print("Trip is: ", trip)
            
            wallet = None
            if user.service == "united-chauffeur":
                wallet = ClientWallet.objects.get(user=user)
            elif user.service == "united-rydr-driver":
                wallet = DriverWallet.objects.get(user=user)
            else:
                return Response({"message": "Invalid service type or something is worng!"}, status=status.HTTP_400_BAD_REQUEST)
            
            
            if not wallet:
                return Response({"message": "User Don't have customer wallet!"}, status=status.HTTP_400_BAD_REQUEST)
            
            # if trip.payment_status != 'hold': #this status wise payment action will be process.
            #     return Response({"error": "Trip status is not on hold."}, status=status.HTTP_400_BAD_REQUEST)
            
            amount = int(50)
            
            trip_payment_method_type_is = trip_payment_method_type(trip)
            print("trip_payment_method_type_is: ", trip_payment_method_type_is)
            trip_payment_method_id_is = trip_payment_method_id(trip) 
            print("trip_payment_method_id_is: ", trip_payment_method_id_is)
            
            if not trip_payment_method_type_is == "Card" and trip_payment_method_id_is is None:
                return Response({"message": "Payment type is not Card and payment method is None."}, status=status.HTTP_400_BAD_REQUEST)
                
            
            # Use the function to check the payment method and balance
            if trip_payment_method_type_is == "Card" and trip_payment_method_id_is: # card amout will hold from Specific card.
                pass


            # # Check if the client's default card has sufficient funds
            # if not check_sufficient_funds(user, amount):
            #     return Response({"message": "Insufficient funds on the default payment method."}, status=status.HTTP_400_BAD_REQUEST)
            
            
            # Retrieve the Stripe customer
            customer = stripe.Customer.retrieve(user.stripe_id)
            print("Stripe Customer is: ")
            
            # Get the default payment method
            default_payment_method_id = customer.invoice_settings.default_payment_method
            if not default_payment_method_id:
                print("No default payment method found.")
                return False
            
            
            
            try:
                # Create a PaymentIntent to hold the amount
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

                    print("payment_intent:---creaded the payment intent- withhold Amount--")
                    print("payment_intent_id is: ", payment_intent.id)
                    if payment_intent:
                        # print("payment_intent: ", payment_intent)
                        print("payment_intent status: ", payment_intent.status)
                        print("payment_intent amount: ", payment_intent.amount)
                        print("payment_intent currency: ", payment_intent.currency)
                        print("payment_intent customer: ", payment_intent.customer)
                        print("payment_intent payment_method: ", payment_intent.payment_method)
                        
                        # Save the payment intent ID in the Trip model
                        print("========I am Here==========")
                        trip.payment_intent_id = payment_intent.id
                        trip.payment_status = PaymentStatus.ON_HOLD
                        trip.save()
                        print("Trip Updated Successfully by hold the payment! Also update the Trip payment status.")
                        return Response({"message": "Payment authorized and held successfully.", "payment_intent_id is: ": payment_intent.id}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Insufficient funds on the default payment method."}, status=status.HTTP_400_BAD_REQUEST)
            
        
            
            except stripe.error.CardError as e:
                # Card was declined or insufficient funds
                print(f"Card error: {e}")
                return Response({"message": "Something is wrong!", "payment_hold_status": False}, status=status.HTTP_200_OK)
            
        
            
            
        except Trip.DoesNotExist:
            return Response({"message": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"message": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






# class CompletePaymentView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request, trip_id):
#         user = request.user
#         print("=== I am calling PaymentCompleteView. ===")
        
#         try:
#             print("user: ", user)
#             trip = Trip.objects.get(id=trip_id, user=user)
#             print("Trip is: ", trip)
            
            
#             # Assuming wallet and payment_method_id are set up similarly to your previous examples
#             user_wallet = ClientWallet.objects.get(user=user) if user.service == "united-chauffeur" else DriverWallet.objects.get(user=user)
#             print("Wallet: ", user_wallet)
#             payment_method_id = user_wallet.default_payment_method_id
#             print("Payment Method ID: ", payment_method_id)
            
#             trip_driver = trip.driver.user
#             print("Trip Driver: ", trip_driver)
#             driver_wallet = DriverWallet.objects.get(user=trip_driver)
#             driver_stripe_customer_id = driver_wallet.stripe_customer_id
#             print("Driver Wallet: ", driver_wallet)
#             print("Driver Wallet Stripe customer id: ", driver_wallet.stripe_customer_id)
            
            
            
#             # Retrieve the PaymentIntent by ID (You might get it from trip)
#             # payment_intent_id = 'pi_3PqUT6GZW19xRTao0633y4Tj'  # Replace with dynamic value
#             payment_intent_id = trip.payment_intent_id  # Replace with dynamic value
#             print("payment_intent_id: ", payment_intent_id)
#             payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
#             if payment_intent:
#                 print("Yes, Found the payment_intent: ")

#             if payment_intent.status != 'requires_capture':
#                 return Response({"error": "Payment intent not in a capturable state."}, status=status.HTTP_400_BAD_REQUEST)
            

#             print("==payment_intent status: ", payment_intent.status)
#             print("==payment_intent amount: ", payment_intent.amount)
#             print("==payment_intent currency: ", payment_intent.currency)

            
#             # Calculate amounts for driver and platform fee
#             held_amount = payment_intent.amount / 100  # Convert to dollars
#             final_fare = int(2)  # Replace with dynamic value
            
#             print("i am here!--1---")
#             if final_fare > held_amount:
#                 print("I am here--- final_fare > held_amount")
#                 # Capture the held amount and create a new PaymentIntent for the difference
#                 stripe.PaymentIntent.capture(payment_intent.id, amount=int(held_amount * 100))
#                 print("I am ready to capture the held amount for payment")
#                 remaining_amount = final_fare - held_amount
#                 new_payment_intent = stripe.PaymentIntent.create(
#                     amount=int(remaining_amount * 100),
#                     currency='usd',
#                     customer=user.stripe_id,
#                     payment_method=payment_method_id,
#                     off_session=True,
#                     confirm=True,
#                     capture_method='automatic',  # Automatically capture the remaining amount
#                 )
#                 amount = held_amount + new_payment_intent.amount_received / 100

            
#             elif final_fare < held_amount:
#                 print("== Holded amount is bigger than final fare ")
#                 # Capture only the final fare amount
#                 stripe.PaymentIntent.capture(payment_intent.id, amount=int(final_fare * 100))
#                 amount = final_fare

#             else:
#                 # Capture the full held amount
#                 print("== Holded amount is equal to final fare ")
#                 stripe.PaymentIntent.capture(payment_intent.id)
#                 amount = held_amount
                
#             print("i am here!--3---")
#             # Distribute funds between driver and company
#             driver_amount = amount * 0.8 # 80% goes to driver
#             company_amount = amount * 0.2 # 20% goes to company
            
            
#             print("i am here!--4---")
            
#             # # If the user or deriver, ensure the connected account exists
#             # if not wallet.stripe_connected_account_id:
#             #     # Create the connected account
#             #     print("Created: connected_account_id for Driver!")
#             #     connected_account_id = create_connected_account(wallet.user.email)
#             #     if connected_account_id:
#             #         wallet.stripe_connected_account_id = connected_account_id
#             #         wallet.save()

            

#             # # Transfer to the driver's account
#             # stripe.Transfer.create(
#             #     amount=int(driver_amount * 100),  # Amount in cents
#             #     currency='usd',
#             #     destination=driver_stripe_customer_id,  # Replace with actual driver Stripe account ID
#             #     transfer_group="trip_id",  # Optional grouping by trip ID
#             # )
            
            
#             # # Transfer 80% to the driver's Stripe account
#             # stripe.Transfer.create(
#             #     amount=int(driver_amount * 100),  
#             #     currency='usd',
#             #     destination=driver_wallet.stripe_customer_id,
#             #     transfer_group=f"trip_{trip_id}",
#             # )
            
#             # print("Transfer to the driver's account is done --")
            
            
            
#             print("i am here!--5---")
#             # Transfer to the company's Stripe account
#             # stripe.Transfer.create(
#             #     amount=int(company_amount * 100),  # Amount in cents
#             #     currency='usd',
#             #     destination='COMPANY_STRIPE_ACCOUNT_ID',  # Replace with actual company Stripe account ID
#             #     transfer_group="trip_id",  # Optional grouping by trip ID
#             # )

#             return Response({"message": "Payment captured and distributed successfully."}, status=status.HTTP_200_OK)

#         except Trip.DoesNotExist:
#             return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
#         except stripe.error.StripeError as e:
#             return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
#         except Exception as e:
#             return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)






class CompletePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, trip_id):
        user = request.user
        print("=== I am calling CompletePaymentView. ===")
        
        try:
            # Retrieve the trip
            print("user: ", user)
            trip = Trip.objects.get(id=trip_id, user=user)
            print("Trip is: ", trip)
            
            # Retrieve the user's wallet and payment method
            user_wallet = ClientWallet.objects.get(user=user) if user.service == "united-chauffeur" else DriverWallet.objects.get(user=user)
            print("Wallet: ", user_wallet)
            payment_method_id = user_wallet.default_payment_method_id
            print("Payment Method ID: ", payment_method_id)
            
            # Retrieve the driver's wallet
            trip_driver = trip.driver.user
            print("Trip Driver: ", trip_driver)
            driver_wallet = DriverWallet.objects.get(user=trip_driver)
            # driver_stripe_account_id = driver_wallet.stripe_customer_id
            driver_stripe_account_id = driver_wallet.stripe_customer_id
            
            driver_stripe_connected_account_id = driver_wallet.stripe_connected_account_id
            print("Driver Wallet: ", driver_wallet)
            print("Driver Wallet Stripe Account ID: ", driver_wallet.stripe_customer_id)
            
            # Retrieve the PaymentIntent
            payment_intent_id = trip.payment_intent_id  # Replace with dynamic value
            print("Payment Intent ID: ", payment_intent_id)
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            
            if not payment_intent or payment_intent.status != 'requires_capture':
                return Response({"error": "Payment intent not in a capturable state."}, status=status.HTTP_400_BAD_REQUEST)

            print("Payment Intent Status: ", payment_intent.status)
            print("Payment Intent Amount: ", payment_intent.amount)
            print("Payment Intent Currency: ", payment_intent.currency)

            # Calculate amounts for driver and platform fee
            held_amount = payment_intent.amount / 100  # Convert to dollars
            final_fare = trip.final_fare  # Assume this is stored in the Trip model
            
            print("Held Amount: ", held_amount)
            print("Final Fare: ", final_fare)

            if final_fare > held_amount:
                print("=======i am here!===1==")
                # Capture the held amount and charge the remaining
                stripe.PaymentIntent.capture(payment_intent.id, amount=int(held_amount * 100))
                remaining_amount = final_fare - held_amount
                new_payment_intent = stripe.PaymentIntent.create(
                    amount=int(remaining_amount * 100),
                    currency='usd',
                    customer=user.stripe_id,
                    payment_method=payment_method_id,
                    off_session=True,
                    confirm=True,
                    capture_method='automatic',  # Automatically capture the remaining amount
                )
                total_amount = held_amount + new_payment_intent.amount_received / 100
            elif final_fare < held_amount:
                print("=======i am here!===2==")
                # Capture only the final fare
                stripe.PaymentIntent.capture(payment_intent.id, amount=int(final_fare * 100))
                total_amount = final_fare
                print("Total Amount: ", total_amount)
            else:
                print("=======i am here!===1==")
                # Capture the full held amount
                stripe.PaymentIntent.capture(payment_intent.id)
                total_amount = held_amount

            print("Total Amount: ", total_amount)

            # # Calculate distribution
            # driver_amount = total_amount * 0.8  # 80% to driver
            # company_amount = total_amount * 0.2  # 20% to company
            

            driver_amount = Decimal(total_amount) * Decimal('0.8')  # 80% to driver
            company_amount = Decimal(total_amount) * Decimal('0.2')  # 20% to company



            print("Driver Amount: ", driver_amount)
            print("Company Amount: ", company_amount)

            # Transfer funds to driver's connected Stripe account
            transfer = stripe.Transfer.create(
                amount=int(driver_amount * 100),  # Convert to cents
                currency="usd",
                destination=driver_stripe_connected_account_id,
                description=f"Payment for Trip {trip_id}"
            )
            print("Transfer to Driver: ", transfer)

            # The 20% company share remains in the platform's main Stripe balance

            return Response({"message": "Payment captured and distributed successfully."}, status=status.HTTP_200_OK)

        except Trip.DoesNotExist:
            return Response({"error": "Trip not found."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





class HeldPaymentsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        print("I am calling HeldPayments List View.")
        user = request.user
        print("user.stripe_id", user.stripe_id)
        try:
            # Retrieve the list of PaymentIntents for the user
            payment_intents = stripe.PaymentIntent.list(
                customer=user.stripe_id,
                limit=10  # Adjust as needed or paginate the results
            )

            # Filter manually for PaymentIntents with manual capture and status 'requires_capture'
            held_payments = [
                {
                    "id": intent.id,
                    "amount": intent.amount / 100,  # Convert from cents to main currency unit
                    "currency": intent.currency,
                    "status": intent.status,
                    "created_at": intent.created,  # Timestamp for when the hold was created
                    "payment_method": intent.payment_method
                }
                for intent in payment_intents['data']
                if intent.capture_method == 'manual' and intent.status == 'requires_capture'
            ]

            return Response({"held_payments": held_payments}, status=200)

        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=400)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=500)
