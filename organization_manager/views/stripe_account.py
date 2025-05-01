from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import stripe
from django.db.models import Sum

from rest_framework import generics

from organization_manager.models import Organization


import stripe
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

#Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY  # Use your Stripe secret key
from datetime import datetime


#import 
from organization_manager.models import Organization, OrganizationAccount
from third_party_org_manager.serializers.stripe_transaction_serializer import OrganizationAccountSerializer
from trip_management.models import TripStatus, Trip



class OrganizationAccountDetails(APIView):
    permission_classes = [IsAuthenticated]

    def get_organization_account(self, organization_id):
        try:
            # Fetch the organization using the organization_id from the URL
            organization = Organization.objects.get(pk=organization_id)
            print("Organization name:", organization.name)
        except Organization.DoesNotExist:
            return Response({'error': "Organization not found"}, status=status.HTTP_404_NOT_FOUND)

        # Get or create the OrganizationAccount for the organization
        try:
            organization_account, created = OrganizationAccount.objects.get_or_create(
                organization=organization
            )
        except OrganizationAccount.DoesNotExist:
            return Response({'error': "Organization account not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return organization_account

    def get(self, request, organization_id, *args, **kwargs):
        # Get organization account
        organization_account = self.get_organization_account(organization_id)
        if isinstance(organization_account, Response):  # If it's already a response (error), return it
            return organization_account
        
        # Filter trips for the organization with status 'COMPLETED'
        trips = Trip.objects.filter(user__organization_id=organization_id, trip_status=TripStatus.COMPLETED)

        # Calculate total final fare and final fare with organization commission rate
        total_final_fare = trips.aggregate(total_fare=Sum('final_fare'))['total_fare'] or 0
        final_fare_with_org_commission_rate = sum(
            trip.final_fare_with_org_commission_rate for trip in trips
        )
        total_org_commission_earn = final_fare_with_org_commission_rate - total_final_fare
        
        # Update the organization account with calculated values
        organization_account.total_trips_completed = trips.count()
        organization_account.total_dealings = total_final_fare
        organization_account.final_fare_with_org_commission = final_fare_with_org_commission_rate
        organization_account.total_org_commission_earn = total_org_commission_earn
        organization_account.save()

        # Serialize organization account data
        serializer = OrganizationAccountSerializer(organization_account)

        # Combine the organization account data with additional trip fare data
        data = serializer.data
        data.update({
            "total_due": total_final_fare - organization_account.total_paid,
        })

        return Response(data, status=status.HTTP_200_OK)

    
    
    
    
    
    
class OrganizationPaymentHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, organization_id):
        
        try:
            # Retrieve the organization related to the authenticated user
            organization = get_object_or_404(Organization, id=organization_id)
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

        
        # Ensure the organization has a Stripe customer ID
        if not organization.stripe_organization_id:
            return Response({"error": "This organization does not have a Stripe customer ID."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Retrieve all charges for this customer (the charges are linked to payment intents)
            charges = stripe.Charge.list(
                customer=organization.stripe_organization_id,  # Filter by the Stripe customer ID
                limit=100,  # Adjust the limit as needed
            )

            payment_data = []
            for charge in charges.data:
                payment_method_details = charge.payment_method_details

                # Convert the Stripe Unix timestamp to a human-readable format
                payment_date = datetime.utcfromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M:%S')

                # Basic payment info
                payment_info = {
                    'id': charge.id,
                    'amount': charge.amount / 100,  # Convert from cents to dollars
                    'currency': charge.currency,
                    'status': charge.status,
                    'description': charge.description,
                    'created_at': payment_date,  # Payment date and time
                    'customer_email': charge.billing_details.email,
                    'customer_name': charge.billing_details.name,
                    'receipt_url': charge.receipt_url,  # Stripe-generated receipt link
                    'payment_method': payment_method_details['type'],
                }

                # Payment method details (if it's a card)
                if payment_method_details['type'] == 'card':
                    payment_info.update({
                        'card_last4': payment_method_details['card']['last4'],
                        'card_brand': payment_method_details['card']['brand'],
                        'card_exp_month': payment_method_details['card']['exp_month'],
                        'card_exp_year': payment_method_details['card']['exp_year'],
                    })

                # Refund information (if any)
                if charge.refunded:
                    refund = stripe.Refund.retrieve(charge.refunds.data[0].id)  # Retrieve the first refund if it exists
                    payment_info.update({
                        'refunded': True,
                        'refund_amount': refund.amount / 100,  # Convert from cents to dollars
                        'refund_date': datetime.utcfromtimestamp(refund.created).strftime('%Y-%m-%d %H:%M:%S'),  # Refund date and time
                        'refund_status': refund.status,
                    })

                # Decline reason (if the payment failed)
                if charge.status == 'failed' and 'card' in payment_method_details:
                    payment_info.update({
                        'decline_reason': payment_method_details['card']['decline_code']
                    })

                # Balance transaction details (fees, net amount)
                if charge.balance_transaction:
                    balance_transaction = stripe.BalanceTransaction.retrieve(charge.balance_transaction)
                    payment_info.update({
                        'balance_transaction_amount': balance_transaction.amount / 100,  # Convert from cents to dollars
                        'balance_transaction_fee': balance_transaction.fee / 100,  # Stripe fee in dollars
                        'balance_transaction_net': balance_transaction.net / 100,  # Net after fees
                    })

                payment_data.append(payment_info)

            return Response({
                'organization': organization.name,
                'total_payments': len(payment_data),
                'payments': payment_data
            }, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
