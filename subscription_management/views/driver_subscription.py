# ✅ Checking if the user has a Stripe customer account, and creating one if they don’t.
# ✅ Checking if the user has a saved payment card and attempting an automatic charge.
# ✅ If no card is available, generating a Stripe payment link.
# ✅ Creating a subscription entry but deactivating it until payment is successful.
# ✅ Deleting any previous unpaid subscriptions before creating a new one.
# ✅ If a user renews the same subscription, it extends the previous one instead of creating a new


# 🚀 Auto payment using the primary card
# 🚀 If failed, generate a Stripe Checkout one-time link
# 🚀 Handles payment cancellation with a cancel message
# 🚀 Deletes unpaid subscriptions after cancellation


import stripe
from django.conf import settings
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from subscription_management.models import SubscriptionPlan, DriverSubscription


import stripe
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone

# Stripe Account Secret Key
stripe.api_key = settings.STRIPE_SECRET_KEY
import time




from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from payment.models import DriverWallet
from subscription_management.models import DriverSubscription, SubscriptionPlan, DriverTransaction
from subscription_management.serializers import CreateSubscriptionSerializer, ActivateSubscriptionSerializer, SubscriptionSerializer, TransactionSerializer



# Persmission 
from subscription_management.decorators import active_subscription_status
from subscription_management.permissions import HasActiveSubscription

class SubscriptionListView(generics.ListAPIView):
    """List all subscriptions for the authenticated driver"""
    serializer_class = SubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self): 
        return DriverSubscription.objects.filter(driver=self.request.user).order_by('-start_date')


class TransactionListView(generics.ListAPIView):
    """List all transactions for the authenticated driver"""
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return DriverTransaction.objects.filter(driver=self.request.user).order_by('-created_at')





class CreateSubscriptionView(generics.CreateAPIView):  # new
    serializer_class = CreateSubscriptionSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        package_id = request.data.get('package_id')
        duration_day = int(request.data.get('duration_day', 0))
        payment_from = request.data.get('payment_from', 'web')  # 'web' or 'app'

        print("User: ", user)
        print("Plan ID: ", package_id)
        print("Duration Day: ", duration_day, type(duration_day))
        print("Payment From: ", payment_from)

        if user.service == "united-chauffeur":
            return Response({'message': 'You are not a driver!'}, status=status.HTTP_400_BAD_REQUEST)

        # Duration mapping
        duration_mapping = {
            7: 'weekly',
            14: 'bi_weekly',
            30: 'monthly',
            90: 'quarterly',
            182: 'half_yearly',
            365: 'yearly',
        }

        duration_key = duration_mapping.get(duration_day)
        print("Duration Key: ", duration_key)

        if not duration_key:
            return Response({'message': 'Invalid duration selected!'}, status=status.HTTP_400_BAD_REQUEST)

        plan = get_object_or_404(SubscriptionPlan, id=package_id)

        price_mapping = {
            'weekly': plan.weekly_final_price,
            'bi_weekly': plan.bi_weekly_final_price,
            'monthly': plan.monthly_final_price,
            'quarterly': plan.quarterly_final_price,
            'half_yearly': plan.half_yearly_final_price,
            'yearly': plan.yearly_final_price,
        }

        total_price = price_mapping.get(duration_key)
        print(f"Total Price for {duration_key}: {total_price}")

        # Step 1: Check if user has a Stripe customer ID
        wallet, created = DriverWallet.objects.get_or_create(user=user)
        if not wallet.stripe_customer_id:
            customer = stripe.Customer.create(email=user.email, name=user.get_full_name())
            wallet.stripe_customer_id = customer['id']
            wallet.save()
            print("Driver Customer ID: ", wallet.stripe_customer_id)

        user.stripe_id = str(wallet.stripe_customer_id)
        user.save()

        # Step 2: Get any active subscription
        active_subscription = DriverSubscription.objects.filter(driver=user, is_active=True).first()

        remaining_days = 0
        if active_subscription:
            remaining_days = (active_subscription.end_date - timezone.now()).days if active_subscription.end_date else 0
            if remaining_days < 0:
                remaining_days = 0

        # Step 3: Create new subscription (inactive initially)
        new_total_days = duration_day + remaining_days  # Add remaining days to new plan
        new_subscription = DriverSubscription.objects.create(
            driver=user,
            package=plan,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=new_total_days),
            total_days=new_total_days,
            total_price=total_price,
            status=False,
            is_active=False
        )

        # Retrieve primary card for automatic payment using a separate method
        payment_method = self.get_primary_payment_method(wallet)

        print("payment_method: ", payment_method)

        if payment_method:
            try:
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(total_price * 100),  # Amount in cents
                    currency="gbp",
                    customer=wallet.stripe_customer_id,
                    payment_method=payment_method.id,
                    off_session=True,
                    confirm=True
                )

                # Deactivate old subscription and activate new one
                if active_subscription:
                    active_subscription.is_active = False
                    active_subscription.status = False
                    active_subscription.save()

                new_subscription.is_active = True
                new_subscription.status = True
                new_subscription.stripe_payment_id = payment_intent['id']
                new_subscription.save()


                return Response({'message': 'Subscription successfully activated!'}, status=status.HTTP_201_CREATED)
            

            except stripe.error.CardError as e:
                print("Auto payment failed, generating manual payment link.", e)
        else:
            # Handle response based on payment_from parameter
            if payment_from == 'web':
                # Return Stripe Checkout URL for Web payment
                return self.create_checkout_session(wallet, plan, total_price, new_subscription)

            else:
                payment_intent = stripe.PaymentIntent.create(
                    amount=int(total_price * 100),  # Amount in cents
                    currency="gbp",
                    customer=wallet.stripe_customer_id,
                    payment_method_types=['card']

                    # line_items=[{
                    #     'price_data': {
                    #         'currency': 'gbp',
                    #         'product_data': {'name': plan.title},
                    #         'unit_amount': int(total_price * 100),
                    #     },
                    #     'quantity': 1
                    # }],
                )

                print("============= app payment intent saved ========")
                new_subscription.stripe_payment_id = payment_intent['id']
                new_subscription.save()


                # Return client_secret for Flutter App
                return self.handle_flutter_payment(payment_intent)

        # If no card found or auto-payment fails, create a Stripe Checkout session
        return self.create_checkout_session(wallet, plan, total_price)

    def get_primary_payment_method(self, wallet):
        """Retrieve the primary payment method for the user."""
        payment_methods = stripe.PaymentMethod.list(
            customer=wallet.stripe_customer_id,
            type="card"
        )
        if payment_methods.data:
            return payment_methods.data[0]
        return None

    def handle_flutter_payment(self, payment_intent):
        """Handle Flutter payment using client_secret."""
        return Response({
            'message': 'Subscription successfully activated!',
            'client_secret': payment_intent.client_secret  # Return client_secret for app
            
        }, status=status.HTTP_201_CREATED)

    def create_checkout_session(self, wallet, plan, total_price, new_subscription):
        """Create a Stripe Checkout session for manual payment."""
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            customer=wallet.stripe_customer_id,
            success_url=f"http://127.0.0.1:9090/api/subscription/v1/driver-subscription/activate/?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"http://127.0.0.1:9090/api/subscription/v1/driver-subscription/cancel/?session_id={{CHECKOUT_SESSION_ID}}",
            line_items=[{
                'price_data': {
                    'currency': 'gbp',
                    'product_data': {'name': plan.title},
                    'unit_amount': int(total_price * 100),
                },
                'quantity': 1
            }],
        )

        print("===== stripe checkout session saved ========")
        new_subscription.stripe_payment_id = checkout_session['id']
        new_subscription.save()
        print("success_url: ")

        return Response({
            'message': 'Payment required',
            'payment_url': checkout_session.url,  # Return the payment URL for Web
        }, status=status.HTTP_200_OK)





# class ActivateSubscriptionView(generics.GenericAPIView): # new(main)
#     serializer_class = ActivateSubscriptionSerializer
#     # permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         """Handles GET request for activating a subscription"""
#         session_id = request.query_params.get('session_id')
#         session_id = request.query_params.get('session_id')
#         print("Get session id: ", session_id)
#         if not session_id:
#             return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

#         return self.activate_subscription(session_id)

#     def post(self, request, *args, **kwargs):
#         """Handles POST request for activating a subscription"""
#         print("I am here for activating the subscription!")
#         serializer = self.get_serializer(data=request.data)

#         if serializer.is_valid():
#             stripe_payment_intent_id = serializer.validated_data['stripe_payment_intent_id']
#             return self.activate_subscription(stripe_payment_intent_id)

#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

#     def activate_subscription(self, session_id):
#         """Handles the logic of activating the subscription and creating a transaction"""
#         try:
#             session = stripe.checkout.Session.retrieve(session_id)
#             print("Session is: ", session)


#             if session.payment_status == "paid":
#                 print("session.url: ", session.url)
#                 # Find the new subscription that was paid for
#                 new_subscription = DriverSubscription.objects.filter(stripe_payment_id=session_id, is_active=False).first()

#                 if new_subscription:
#                     # Deactivate any old active subscription before activating the new one
#                     old_subscription = DriverSubscription.objects.filter(driver=new_subscription.driver, is_active=True).first()
#                     if old_subscription:
#                         old_subscription.is_active = False
#                         old_subscription.status = False
#                         old_subscription.save()

#                     # Activate the new subscription
#                     new_subscription.is_active = True
#                     new_subscription.status = True
#                     new_subscription.save()

#                     # Create a transaction record
#                     transaction = DriverTransaction.objects.create(
#                         driver=new_subscription.driver,
#                         subscription=new_subscription,
#                         amount=new_subscription.total_price,
#                         store_amount=new_subscription.total_price,
#                         tran_id=session.payment_intent,
#                         stripe_payment_intent_id=session.payment_intent,
#                         stripe_charge_id=session.payment_intent,
#                         stripe_customer_id=session.customer,
#                         stripe_payment_method_id=session.payment_method_types[0] if session.payment_method_types else None,
#                         stripe_receipt_url=session.url,
#                         payment_status="success",
#                         transaction_category="payment"
#                     )

#                     return Response({
#                         'message': 'Subscription activated successfully!',
#                         'transaction_id': transaction.tran_id
#                     }, status=status.HTTP_200_OK)

#                 return Response({'error': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)

#             else:
#                 return Response({'error': 'Payment not completed'}, status=status.HTTP_400_BAD_REQUEST)

#         except stripe.error.InvalidRequestError:
#             return Response({'error': 'Invalid payment session'}, status=status.HTTP_400_BAD_REQUEST)





class ActivateSubscriptionView(generics.GenericAPIView):  # Updated
    serializer_class = ActivateSubscriptionSerializer

    def get(self, request, *args, **kwargs):
        """Handles GET request for activating a subscription (used for web payments)"""
        session_id = request.query_params.get('session_id')
        print("Get session id: ", session_id)

        if not session_id:
            return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        return self.activate_subscription(session_id)

    def post(self, request, *args, **kwargs):
        """Handles POST request for activating a subscription (used for app payments)"""
        print("I am here for activating the subscription!")
        serializer = self.get_serializer(data=request.data)

        print("Serializer: ", serializer)

        if serializer.is_valid():
            stripe_payment_id = serializer.validated_data['stripe_payment_intent_id']
            return self.activate_subscription(stripe_payment_id)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def activate_subscription(self, stripe_payment_id):
        """Handles the logic of activating the subscription for both Web and App payments"""
        try:
            if stripe_payment_id.startswith("cs_"):
                # Handling Checkout Session (Web)
                session = stripe.checkout.Session.retrieve(stripe_payment_id)
                print("Checkout Session: ", session)

                if session.payment_status == "paid":
                    stripe_customer_id = session.customer
                    stripe_payment_intent_id = session.payment_intent
                    stripe_receipt_url = session.url
                    stripe_payment_method_id = session.payment_method_types[0] if session.payment_method_types else None
                else:
                    return Response({'error': 'Payment not completed'}, status=status.HTTP_400_BAD_REQUEST)

            elif stripe_payment_id.startswith("pi_"):
                # Handling PaymentIntents (Flutter/App)
                payment_intent = stripe.PaymentIntent.retrieve(stripe_payment_id)
                print("Payment Intent=====: ", payment_intent)

                if payment_intent.status == "succeeded":
                    print("------i am here!---")
                    stripe_customer_id = payment_intent.customer
                    print("------i am here!--1-")
                    stripe_payment_intent_id = payment_intent.id
                    # stripe_receipt_url = payment_intent.charges.data[0].receipt_url if payment_intent.charges.data else None
                    stripe_payment_method_id = payment_intent.payment_method
                    print("------i am here!--2-")
                else:
                    return Response({'error': 'Payment not completed'}, status=status.HTTP_400_BAD_REQUEST)

            else:
                return Response({'error': 'Invalid Stripe payment ID format'}, status=status.HTTP_400_BAD_REQUEST)

            # Find the new subscription that was paid for
            new_subscription = DriverSubscription.objects.filter(
                stripe_payment_id=stripe_payment_id, is_active=False
            ).first()

            if new_subscription:
                # Deactivate old active subscription before activating the new one
                old_subscription = DriverSubscription.objects.filter(driver=new_subscription.driver, is_active=True).first()
                if old_subscription:
                    old_subscription.is_active = False
                    old_subscription.status = False
                    old_subscription.save()

                # Activate the new subscription
                new_subscription.is_active = True
                new_subscription.status = True
                new_subscription.save()

                # Create a transaction record
                transaction = DriverTransaction.objects.create(
                    driver=new_subscription.driver,
                    subscription=new_subscription,
                    amount=new_subscription.total_price,
                    store_amount=new_subscription.total_price,
                    tran_id=stripe_payment_intent_id,
                    stripe_payment_intent_id=stripe_payment_intent_id,
                    stripe_charge_id=stripe_payment_intent_id,
                    stripe_customer_id=stripe_customer_id,
                    stripe_payment_method_id=stripe_payment_method_id,
                    # stripe_receipt_url=stripe_receipt_url,
                    payment_status="success",
                    transaction_category="payment"
                )

                return Response({
                    'message': 'Subscription activated successfully!',
                    'transaction_id': transaction.tran_id
                }, status=status.HTTP_200_OK)

            return Response({'error': 'Subscription not found'}, status=status.HTTP_404_NOT_FOUND)

        except stripe.error.InvalidRequestError:
            return Response({'error': 'Invalid payment session or payment intent'}, status=status.HTTP_400_BAD_REQUEST)






class CancelSubscriptionView(APIView):
    # permission_classes = [IsAuthenticated]


    # @active_subscription_status()
    def get(self, request, *args, **kwargs):
        session_id = request.query_params.get('session_id')

        if not session_id:
            return Response({'error': 'Session ID is required'}, status=status.HTTP_400_BAD_REQUEST)

        # Find the subscription that was not completed
        subscription = DriverSubscription.objects.filter(stripe_payment_id=session_id, is_active=False).first()

        if subscription:
            subscription.delete()  # Delete the unpaid subscription
            return Response({'message': 'Payment was cancelled. Subscription not created.'}, status=status.HTTP_200_OK)

        return Response({'error': 'Subscription not found or already activated.'}, status=status.HTTP_404_NOT_FOUND)
