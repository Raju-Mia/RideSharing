

import uuid
from django.utils import timezone
import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404

from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal

from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated



#Import
from organization_manager.models import Organization, OrganizationAccount, OrganizationTransaction
from trip_management.models import PaymentStatus, TripStatus, Trip




class CreateOrganizationPaymentLinkView(APIView):  # Payment by payment link
    permission_classes = [IsAuthenticated]

    def post(self, request):
        print("============i am here===============")
        # Get the authenticated user and organization
        user = request.user
        try:
            organization = user.organization  # Access the related organization directly
            print("Organization is:", organization)
        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        # Step 1: Create Stripe Customer for the organization (if not already created)
        if not organization.stripe_organization_id:
            try:
                customer = stripe.Customer.create(
                    name=organization.name,
                    email=organization.email,
                )
                organization.stripe_organization_id = customer['id']
                organization.save()
            except stripe.error.StripeError as e:
                return Response({'error': f"Failed to create Stripe customer: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # Step 2: Calculate total fare from trip IDs provided in the request data
        trip_ids = request.data.get('trip_ids', [])
        
        
        if not trip_ids:
            return Response({'error': 'A list of trip IDs is required to calculate the total fare.'}, status=status.HTTP_400_BAD_REQUEST)

        total_fare = self.calculate_total_fare(user, trip_ids)
        print("=======total_fare==here===: ", total_fare)
        
        if total_fare is None:
            return Response({'error': 'Failed to calculate total fare. Please check trip IDs.'}, status=status.HTTP_400_BAD_REQUEST)

        amount_in_cents = int(total_fare * 100)  # Convert to cents for Stripe

        try:
            # Step 3: Create a checkout session with the calculated fixed amount in GBP
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                customer=organization.stripe_organization_id,  # Use existing Stripe customer ID
                line_items=[{
                    'price_data': {
                        'currency': 'gbp',  # Currency in GBP
                        'product_data': {
                            'name': f"Payment for {organization.name}",
                        },
                        'unit_amount': amount_in_cents,
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=settings.PAYMENT_SUCCESS_URL,  # Your success page URL
                cancel_url=settings.PAYMENT_CANCEL_URL,  # Your cancel page URL
                billing_address_collection='auto',  # Optionally collect billing address
                metadata={  # Send organization ID and trip IDs as metadata for tracking
                    'organization_id': str(organization.id),
                    'trip_ids': ','.join(map(str, trip_ids)),  # Send trip IDs as comma-separated string
                    'total_fare': str(total_fare),  # Send total fare for tracking
                }
            )

            # Return the Stripe-hosted checkout page URL
            return Response({
                'status': 'success',
                'payment_url': checkout_session.url,
            }, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({'error': f"Failed to create payment session: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)




    def calculate_total_fare(self, user, trip_ids):
        """
        Calculates the total fare based on a list of trip IDs and the authenticated user.
        """
        try:
            # Assuming you have a Trip model with a 'fare' field
            print("trip_ids: ", trip_ids)
            trips = Trip.objects.filter(user=user, id__in=trip_ids, trip_status=TripStatus.COMPLETED)
            print("=======trips count=====: ", trips.count())
            
            total_fare = sum(trip.final_fare for trip in trips)
            print("=======total_fare=====: ", total_fare)
            return total_fare
        except Exception as e:
            print(f"Error calculating total fare: {str(e)}")
            return None







# views.py
class PaymentSuccessView(APIView):
    def get(self, request):
        # Logic for successful payment
        return Response({"message": "Payment was successful!"}, status=status.HTTP_200_OK)

class PaymentCancelView(APIView):
    def get(self, request):
        # Logic for canceled payment
        return Response({"message": "Payment was canceled!"}, status=status.HTTP_200_OK)




# Organziaton Payment View============= Session wise ========wroking well====
class CreatePaymentSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        print("hellow")
        # Get the authenticated user
        user = request.user

        try:
            # Retrieve the organization related to the authenticated user
            organization = user.organization  # Access the related organization directly
            print("organization", organization)

            if not organization:
                return Response({"error": "User is not associated with any organization"}, status=status.HTTP_400_BAD_REQUEST)

            # Retrieve and validate the amount
            amount_str = request.data.get('amount')  # Amount sent from client (as string)

            try:
                amount = int(amount_str)  # Convert to integer
            except (ValueError, TypeError):
                return Response({"error": "Invalid amount"}, status=status.HTTP_400_BAD_REQUEST)

            if amount <= 0:
                return Response({"error": "Amount must be greater than zero"}, status=status.HTTP_400_BAD_REQUEST)

            # Convert amount to pence (Stripe requires the smallest unit)
            amount_in_pence = amount * 100

            # Check if stripe_organization_id exists for the organization
            if not organization.stripe_organization_id:
                # Create a Stripe organization account (if required)
                stripe_account = stripe.Account.create(type="express")
                organization.stripe_organization_id = stripe_account.id
                organization.save()

            print("I am here---1")
            # Create a Stripe payment session
            line_items = [{
                'price_data': {
                    'currency': 'gbp',  # Use GBP for pounds
                    'product_data': {
                        'name': 'Payment',
                        'description': 'Payment for services',
                    },
                    'unit_amount': amount_in_pence,  # Amount in pence
                },
                'quantity': 1,
            }]
            
            print("I am here---2")
            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                mode="payment",
                line_items=line_items,
                
                success_url=settings.PAYMENT_SUCCESS_URL,  # Defined in settings.py
                cancel_url=settings.PAYMENT_CANCEL_URL,  # Defined in settings.py
                
                payment_intent_data={
                    "capture_method": "automatic",
                    "metadata": {
                        "organization_id": organization.id  # Pass organization ID as metadata
                        # "organization_id": str(organization.id),  # Pass organization ID as metadata
                        # "organization_name": organization.name,  # You can add more metadata if needed
                    }
                }
            )
            print("I am here---3")
            # Return the session URL for redirection
            return Response({"session_url": session.url}, status=status.HTTP_200_OK)

        except Organization.DoesNotExist:
            return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)













from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import stripe
from django.conf import settings








#=========================== Main WebHook==============Update==========================

@csrf_exempt
def stripe_webhook(request):
    
    '''
    Purpose: Automatically handle events from Stripe such as successful payments, refunds, etc.
    Steps:
    Create a View: Define a view to handle webhook events from Stripe.
    Update Models: Update your models based on the events received (e.g., successful payments).
    
    '''
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError as e:
        # Invalid payload
        print(f"Error: Invalid payload - {e}")
        return JsonResponse({'error': f'Invalid payload: {str(e)}'}, status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        print(f"Error: Invalid signature - {e}")
        return JsonResponse({'error': f'Invalid signature: {str(e)}'}, status=400)

    # Log event ID and type
    print("===================-------------------==================")
    print(f"Event received: {event['id']} - {event['type']}")

    # Handle specific event types
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        amount_total = session['amount_total']  
        print("amout is", amount_total)
        amount_total = amount_total / 100  # Convert from cents to GBP
        print("---2---- Amount total (GBP): ", amount_total)

        organization_id = session.get('metadata', {}).get('organization_id')
        trip_ids = session.get('metadata', {}).get('trip_ids', '').split(',')
        print(f"Checkout session completed with organization_id: {organization_id} and trip_ids: {trip_ids}")

        # Ensure organization_id exists
        if not organization_id:
            print("----- Error: organization_id missing in metadata -----")
            return JsonResponse({'error': 'organization_id not found in payment metadata'}, status=400)

        # Fetch the related organization
        try:
            organization = Organization.objects.get(id=organization_id)
            print(f"---4--- Organization found: {organization.name}")
        except Organization.DoesNotExist:
            print("----- Error: Organization not found -----")
            return JsonResponse({'error': 'Organization not found'}, status=404)

        # Ensure valid amount
        if amount_total <= 0:
            print("----- Error: Invalid amount total -----")
            return JsonResponse({'error': 'Invalid amount total.'}, status=400)

        # Create or get OrganizationAccount
        try:
            organization_account, created = OrganizationAccount.objects.get_or_create(
                organization=organization,
                defaults={'total_paid': Decimal('0.00'), 'total_dealings': Decimal('0.00'), 'balance': Decimal('0.00')}
            )
            if created:
                organization_account.total_paid = Decimal(amount_total)
                organization_account.save()
                print(f"OrganizationAccount created for {organization.name}")
            else:
                organization_account.total_paid += Decimal(amount_total)
                organization_account.total_due -= Decimal(amount_total)
                organization_account.save()
        except Exception as e:
            print(f"----- Error: Could not create or retrieve OrganizationAccount: {str(e)} -----")
            return JsonResponse({'error': f'Error handling account: {str(e)}'}, status=500)

        # Update trip payment status to 'Paid'
        update_trip_payment_status(trip_ids)

        # Add custom payment processing logic here, e.g., update balance
        print(f"---5--- Payment processing complete for {organization.name}")
        
    elif event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        print("========payment_intent.succeeded=========")
        # Optional: Handle any specific logic for payment_intent.succeeded if needed.

    else:
        # Handle other event types
        print(f"Unhandled event type: {event['type']}")

    return JsonResponse({'status': 'success'}, status=200)

def update_trip_payment_status(trip_ids):
    """
    Updates the payment status of trips to 'Paid' based on the provided trip IDs.
    """
    try:
        # Fetch trips by trip_ids and update payment status to 'Paid'
        trips = Trip.objects.filter(id__in=trip_ids, payment_status=PaymentStatus.UNPAID)
        for trip in trips:
            trip.payment_status = PaymentStatus.PAID
            trip.save()
        print(f"Updated payment status for {trips.count()} trips to 'Paid'")
    except Exception as e:
        print(f"Error updating trip payment status: {str(e)}")

