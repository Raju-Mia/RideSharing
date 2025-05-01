# from accounts.models import Employee
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

from payment.helpers import create_connected_account, create_account_link, is_stripe_customer
from payment.serializers import CardSerializer, BookingPaymentSerializer, ChargeSerializer
from trip_management.models import Trip


from payment.models import ClientWallet, DriverWallet, OrganizationWallet, Transaction
User = get_user_model()

# Stripe Account Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY




#==== CreateStripeCustomer ================(new) RR
class CreateStripeCustomer(APIView): #phase - 0
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        print("The user is: ", user, user.service)

        if user.stripe_id:
            return Response({"message": "Stripe customer already exists."}, status=status.HTTP_403_FORBIDDEN)

        try:
            print("Create Sripe Customer ----------here---1--")
            
            # Create a new Stripe customer
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
                
                # Example of usage after driver registration
                if not wallet.stripe_connected_account_id:
                    print("Created: connected_account_id, for user!")
                    connected_account_id = create_connected_account(wallet.user.email)
                    if connected_account_id:
                        wallet.stripe_connected_account_id = connected_account_id
                        wallet.save()

                        
                
            elif user.service == "united-rydr-driver":
                print("User service is: united-rydr-driver")
                # Create or get the driver's wallet
                wallet, created = DriverWallet.objects.get_or_create(user=user)
                wallet.stripe_customer_id = customer.id
                wallet.save()
                
                
                # Example of usage after driver registration
                if not wallet.stripe_connected_account_id:
                    print("Created: connected_account_id for Driver!")
                    connected_account_id = create_connected_account(wallet.user.email)
                    if connected_account_id:
                        wallet.stripe_connected_account_id = connected_account_id
                        wallet.save()




            else:
                return Response({"message": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
            
            
            print("Create Sripe Customer ----------here---3--")
            intent = stripe.SetupIntent.create(payment_method_types=["card"], customer=str(request.user.stripe_id))
            data = {
                "client_secret": intent.client_secret,
                "message": "Stripe customer account created successfully."
                }
            
            print("stripe_customer_id:", customer.id)
            return Response(data=data, status=status.HTTP_201_CREATED)
        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    
    



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

        
        






class VerifyPaymentMethodView(APIView): # Unknown Phase (for Driver Verification)
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        wallet = None
        
        print("User service is: ", user.service, type(user.service))
        
        try:
            if user.service == "united-chauffeur":
                wallet = ClientWallet.objects.get(user=user)
                payment_method_id = wallet.default_payment_method_id
            elif user.service == "united-rydr-driver":
                wallet = DriverWallet.objects.get(user=user)
                payment_method_id = wallet.default_payment_method_id
            else:
                return Response({"message": "Invalid service type."}, status=status.HTTP_400_BAD_REQUEST)
        except (ClientWallet.DoesNotExist, DriverWallet.DoesNotExist):
            return Response({"message": "Wallet not found."}, status=status.HTTP_400_BAD_REQUEST)
        
        if not wallet.stripe_customer_id:
            return Response({"message": "Stripe customer not found."}, status=status.HTTP_400_BAD_REQUEST)
    
        if not payment_method_id:
            return Response({"message": "No default payment method found."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Create a PaymentIntent to verify the payment method
            print("I am here-1-")
            payment_intent = stripe.PaymentIntent.create(
                amount=100,  # $1.00
                currency='usd',
                payment_method=payment_method_id,
                customer=wallet.stripe_customer_id,
                confirm=True,
                setup_future_usage='off_session',  # Optional: Setup for future off-session use
                automatic_payment_methods={
                    'enabled': True,
                    'allow_redirects': 'never',
                }
            )
            print("I am here-2-")

            # Refund the PaymentIntent immediately
            stripe.Refund.create(payment_intent=payment_intent.id)
            print("I am here-3-")
            # =========== Update wallet Verification Status ============
            wallet.default_payment_verified = True
            wallet.save()
            
            return Response({"message": "Payment method verified and amount refunded successfully."}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)








class ChargeClientCardView(APIView): #phase-6
    permission_classes = [IsAuthenticated]
    
    '''
    Summary:
    Client Completes Trip: After the trip, the client presses a button to trigger the payment.
    Call ChargeClientCardView: This view handles charging the client’s card via Stripe.
    Payment Processing: The view will:
    Create a PaymentIntent to handle the charge.
    Deduct the trip cost from the client’s card.
    Update the organization’s wallet with the trip cost.
    Record the transaction.
    '''

    def post(self, request):
        serializer = ChargeSerializer(data=request.data)
        
        if serializer.is_valid():
            client_wallet = ClientWallet.objects.get(user=request.user)
            trip_cost = serializer.validated_data['amount']
            driver_id = serializer.validated_data['driver_id'] #Which Driver trip.

            # Ensure the client has a payment method and retrieve it
            if not client_wallet.stripe_customer_id:
                return Response({"message": "Client does not have a Stripe customer ID."}, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                # Create a PaymentIntent
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(trip_cost * 100),  # Amount in cents
                    currency='usd',
                    customer=client_wallet.stripe_customer_id,
                    payment_method=request.data.get('payment_method_id'),
                    off_session=True,  # This is important for automatic payments
                    confirm=True
                )
                
                # Handle successful payment
                if payment_intent.status == 'succeeded':
                    # Find the driver and update their wallet
                    driver_wallet = DriverWallet.objects.get(user_id=driver_id)
                    
                    # Transfer funds to the organization wallet
                    organization_wallet = OrganizationWallet.objects.first()  # Assuming a single organization wallet
                    organization_wallet.balance += trip_cost
                    organization_wallet.save()

                    # Log the transaction
                    Transaction.objects.create(
                        transaction_type='booking_payment',
                        amount=trip_cost,
                        client_wallet=client_wallet,
                        driver_wallet=driver_wallet
                    )

                    return Response({"message": "Payment processed successfully."}, status=status.HTTP_200_OK)
                else:
                    return Response({"message": "Payment failed."}, status=status.HTTP_400_BAD_REQUEST)

            except stripe.error.StripeError as e:
                return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class RefundPaymentView(APIView): #phase-6
    '''
    Purpose: Refund the trip amount to the client’s default verified card.
    '''
    permission_classes = [IsAuthenticated]

    def post(self, request):
        charge_id = request.data.get("charge_id")
        amount = request.data.get("amount")  # amount in cents, e.g., 5000 for $50.00

        if not charge_id:
            return Response({"message": "Charge ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            refund = stripe.Refund.create(
                charge=charge_id,
                amount=amount  # Optional: If not provided, full amount will be refunded
            )
            return Response({"message": "Refund processed successfully.", "refund": refund}, status=status.HTTP_200_OK)
        except stripe.error.StripeError as e:
            return Response({"message": f"Stripe error: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)







# Set Up Webhooks
'''
Purpose: Automatically handle events from Stripe such as successful payments, refunds, etc.
Steps:
Create a View: Define a view to handle webhook events from Stripe.
Update Models: Update your models based on the events received (e.g., successful payments).
'''
class StripeWebhookView(APIView):
    
    # permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.headers.get('Stripe-Signature')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, "your_stripe_webhook_secret"
            )
        except ValueError as e:
            return Response({"message": "Invalid payload."}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response({"message": "Invalid signature."}, status=status.HTTP_400_BAD_REQUEST)

        # Handle the event
        if event['type'] == 'payment_intent.succeeded':
            # Handle successful payment
            refund_data = event['data']['object']
            # Process the refund event, e.g., update your database
            # refund_data contains messages about the refund
            pass

        elif event['type'] == 'payment_intent.failed':
            # Handle failed payment
            pass

        return Response({"message": "Event received."}, status=status.HTTP_200_OK)












# Implement Earnings Transfer
class EarningsTransferView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        driver_id = request.data.get('driver_id')
        amount = request.data.get('amount')

        try:
            driver_wallet = DriverWallet.objects.get(user_id=driver_id)
            organization_wallet = OrganizationWallet.objects.first()  # Assuming a single organization wallet

            # Check if the organization wallet has sufficient funds
            if organization_wallet.balance < amount:
                return Response({"message": "Insufficient funds in organization wallet."}, status=status.HTTP_400_BAD_REQUEST)

            # Transfer funds
            organization_wallet.balance -= amount
            organization_wallet.save()

            driver_wallet.balance += amount
            driver_wallet.save()

            # Log the transaction
            Transaction.objects.create(
                transaction_type='earnings_transfer',
                amount=amount,
                driver_wallet=driver_wallet
            )

            return Response({"message": "Earnings transferred successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



#Implement Withdrawals
class WithdrawalView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        driver_id = request.data.get('driver_id')
        amount = request.data.get('amount')

        try:
            driver_wallet = DriverWallet.objects.get(user_id=driver_id)

            # Check if the driver wallet has sufficient funds
            if driver_wallet.balance < amount:
                return Response({"message": "Insufficient funds in driver wallet."}, status=status.HTTP_400_BAD_REQUEST)

            # Deduct funds from driver wallet
            driver_wallet.balance -= amount
            driver_wallet.save()

            # Log the transaction
            Transaction.objects.create(
                transaction_type='withdrawal',
                amount=amount,
                driver_wallet=driver_wallet
            )

            # Process the payout (requires integration with Stripe or another payment provider)
            # For example: stripe.Payout.create(amount=amount, currency='usd', destination=destination_account_id)

            return Response({"message": "Withdrawal processed successfully."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)









# Implement the Booking Payment View ( Wallet payment--future emplement)
class BookingPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BookingPaymentSerializer(data=request.data)
        if serializer.is_valid():
            client_wallet = ClientWallet.objects.get(user=request.user)
            trip_cost = serializer.validated_data['amount']
            driver_id = serializer.validated_data['driver_id']

            if client_wallet.balance < trip_cost:
                return Response({"message": "Insufficient funds."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                # Deduct the amount from the client's wallet
                client_wallet.balance -= trip_cost
                client_wallet.save()

                # Find the driver and their wallet
                driver_wallet = DriverWallet.objects.get(user_id=driver_id)
                
                # Transfer funds to the organization wallet
                organization_wallet = OrganizationWallet.objects.first()  # Assuming a single organization wallet
                organization_wallet.balance += trip_cost
                organization_wallet.save()

                # Log the transaction
                Transaction.objects.create(
                    transaction_type='booking_payment',
                    amount=trip_cost,
                    client_wallet=client_wallet,
                    driver_wallet=driver_wallet
                )

                return Response({"message": "Booking payment processed successfully."}, status=status.HTTP_200_OK)
            except Exception as e:
                return Response({"message": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)














