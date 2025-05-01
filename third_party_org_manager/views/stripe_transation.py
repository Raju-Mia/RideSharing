from payment.helpers import card_logos
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from decimal import Decimal
from datetime import datetime
from django.db.models import Sum
import pytz
import stripe
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework import generics
from rest_framework import filters
from django.db.models import Q
from rest_framework.exceptions import NotFound

from utils.pagination import CustomPageNumberPagination
from django.contrib.auth import authenticate
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated



#Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY  # Use your Stripe secret key

#Import 
from organization_manager.models import Organization, OrganizationAccount
from third_party_org_manager.serializers.stripe_transaction_serializer import UnpaidCompletedTripListSerializer, UnpaidCompletedTripDetailSerializer, OrganizationAccountSerializer
from trip_management.models import PaymentStatus, TripStatus, Trip

from third_party_org_manager.serializers.trip_serializers import TripListSerializer, TripDetailSerializer


class OrganizationCompletedTripListView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        user = request.user
        organization_id = user.organization.id

        # Check for query parameters
        search_query = request.query_params.get('search', None)

        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Filter for completed trips with unpaid status
        queryset = Trip.objects.filter(
            user__organization_id=organization_id,
            trip_status=TripStatus.COMPLETED,
            payment_status=PaymentStatus.UNPAID
        ).order_by('-booking_time')

        print("queryset", queryset)
        
        # Add search query filtering
        if search_query:
            queryset = queryset.filter(
                Q(passenger_name__icontains=search_query) |
                Q(pickup_location_name__icontains=search_query) |
                Q(final_dropoff_location_name__icontains=search_query)
            )

        # Apply pagination
        paginator = self.pagination_class()
        paginated_trips = paginator.paginate_queryset(queryset, request)

        serializer = UnpaidCompletedTripListSerializer(paginated_trips, many=True)
        return paginator.get_paginated_response(serializer.data)



class OrganizationCompletedTripDetailView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UnpaidCompletedTripDetailSerializer

    def get(self, request, *args, **kwargs):
        trip_id = self.kwargs.get('id')
        
        try:
            # Filter for completed and unpaid trip
            trip = Trip.objects.get(pk=trip_id, trip_status=TripStatus.COMPLETED, payment_status=PaymentStatus.UNPAID)
        except Trip.DoesNotExist:
            return Response({'error': 'Trip not found or does not meet the criteria.'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize and return the trip details
        serializer = UnpaidCompletedTripDetailSerializer(trip)
        return Response(serializer.data)




class ThirdPartyOrganizationAccountView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationAccountSerializer

    def get_object(self):
        # Fetch the organization linked to the logged-in user
        organization = self.request.user.organization
        # print("Organization name:", organization.name)

        # Get or create the OrganizationAccount for the organization
        try:
            organization_account, created = OrganizationAccount.objects.get_or_create(
                organization=organization
            )
        except OrganizationAccount.DoesNotExist:
            return Response({'error': "Organization account not found"}, status=status.HTTP_404_NOT_FOUND)
        
        return organization_account

    def retrieve(self, request, *args, **kwargs):
        # Get organization account
        organization_account = self.get_object()
        if isinstance(organization_account, Response):  # If it's already a response (error), return it
            return organization_account
        
        # Get the organization linked to the user
        organization_id = request.user.organization.id
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)

       
        
        # Filter trips for the organization with status 'COMPLETED'
        trips = Trip.objects.filter(user__organization_id=organization_id, trip_status=TripStatus.COMPLETED)
        
        for i in trips:
            print("trip_id: ", i.id)
            print("trip_status", i.trip_status)
            print("trip_fare: ", i.final_fare)
            print("commission_rate: ", i.org_commission_rate)
            print("trip_fare_with_org_commission_rate: ", i.final_fare_with_org_commission_rate)



        # Calculate total final fare and final fare with organization commission rate
        total_final_fare = trips.aggregate(total_fare=Sum('final_fare'))['total_fare'] or 0
        print("total_final_fare:", total_final_fare)
        final_fare_with_org_commission_rate = sum(trip.final_fare_with_org_commission_rate for trip in trips)
        print("final_fare_with_org_commission_rate:", final_fare_with_org_commission_rate)


        # Calculate total organization commission earned
        # total_org_commission_earn = final_fare_with_org_commission_rate - total_final_fare # Real
        total_org_commission_earn = max(final_fare_with_org_commission_rate - total_final_fare, 0.00) # if negative then return = 0
        print("Total organization commission earned====:", total_org_commission_earn)



        # Update organization account details
        organization_account.total_trips_completed = trips.count()
        organization_account.total_dealings = total_final_fare
        organization_account.final_fare_with_org_commission = final_fare_with_org_commission_rate
        organization_account.total_org_commission_earn = total_org_commission_earn

        # Ensure total_paid is not None
        total_paid = organization_account.total_paid or 0  
        organization_account.total_due = total_final_fare - total_paid  

        organization_account.save()

        # Serialize organization account data
        serializer = self.get_serializer(organization_account)

        # Combine the organization account data with trip fare data
        data = serializer.data
        data.update({
            "total_due": round(total_final_fare - total_paid, 2)
        })
        
        print("data:", data)

        return Response(data, status=status.HTTP_200_OK)




        
    
# class ThirdPartyOrganizationAccountTripFareView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, *args, **kwargs):
#         user = request.user
#         organization_id = user.organization.id

#         # Get the organization
#         try:
#             organization = Organization.objects.get(pk=organization_id)
#         except Organization.DoesNotExist:
#             return Response({'error': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)


#         # Filter trips for the organization with status completed
#         trips = Trip.objects.filter(user__organization_id=organization_id, trip_status=TripStatus.COMPLETED)

#         # Calculate total final fare and final fare with organization commission rate
#         total_final_fare = trips.aggregate(total_fare=Sum('final_fare'))['total_fare'] or 0

#         final_fare_with_org_commission_rate = sum(
#             trip.final_fare_with_org_commission_rate for trip in trips
#         )
        
#         total_org_commission_earn = final_fare_with_org_commission_rate - total_final_fare
        

#         data = {
#             "completed_trip_count": trips.count(),
#             "total_final_fare": total_final_fare,
#             "total_org_commission_earn": total_org_commission_earn,
#             "final_fare_with_org_commission_rate": final_fare_with_org_commission_rate,
#         }

#         return Response(data, status=status.HTTP_200_OK)




# Stripe Transactions list for Organization wise.== Main
class ThirdPartyOrganizationPaymentHistoryView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get the authenticated user
        user = request.user

        try:
            # Retrieve the organization related to the authenticated user
            organization = user.organization  # Access the related organization directly
            print("Organization Is: ", organization)
            
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
        
        


        # Create or get OrganizationAccount
        try:
            organization_account, created = OrganizationAccount.objects.get_or_create(
                organization=organization
                # defaults={'total_paid': Decimal('0.00'), 'total_dealings': Decimal('0.00'), 'balance': Decimal('0.00')}
            )
        except Exception as e:
            return JsonResponse({'error': f'Error handling organization account: {str(e)}'}, status=500)
        



        try:
            # Retrieve all charges for this customer (the charges are linked to payment intents)
            charges = stripe.Charge.list(
                customer=organization.stripe_organization_id,  # Filter by the Stripe customer ID
                limit=100,  # Adjust the limit as needed
            )
            

            # If no charges exist, return an empty response without error
            if not charges.data:
                print(" Stripe Transaction data is not available!")
                return Response({
                    'organization': organization.name,
                    'total_payments': 0,
                    'payments': []  # Return an empty list if there are no payments
                }, status=status.HTTP_200_OK)

            payment_data = []
            for charge in charges.data:
                payment_method_details = charge.payment_method_details

                # Convert the Stripe Unix timestamp to a human-readable format
                # payment_date = datetime.utcfromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M:%S')
                # payment_date = datetime.fromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M:%S')
                # Assuming `charge.created` is in UTC
                utc_time = datetime.fromtimestamp(charge.created, tz=pytz.UTC)
                bd_time = utc_time.astimezone(pytz.timezone('Asia/Dhaka')).strftime('%Y-%m-%d %H:%M:%S')
                # print("UTC time: ", utc_time)
                # print("BD time: ", bd_time)

                # print("Payment Date:======== ", payment_date, charge.created)

                # Basic payment info
                payment_info = {
                    'id': charge.id,
                    'amount': charge.amount / 100,  # Convert from cents to dollars
                    'currency': charge.currency,
                    'status': charge.status,
                    'description': charge.description,
                    'created_at': bd_time,  # Payment date and time
                    'customer_email': charge.billing_details.email,
                    'customer_name': charge.billing_details.name,
                    'receipt_url': charge.receipt_url,  # Stripe-generated receipt link
                    'payment_method': payment_method_details['type'],
                }
                
                
                
                # # Determine card logo
                # print("===========i am here=============")
                # card_brand = payment_method_details['card']['brand'] if payment_method_details['type'] == 'card' else 'default'
                # payment_info['card_logo'] = payment_method_details.get('card', {}).get('brand') and (
                #     f"https://stripe.com/img/icons/payments/brands/{card_brand}.svg"  # Use Stripe logo if available
                # ) or card_logos.get(card_brand, card_logos['default'])  # Fallback to custom logos
                # print("===========i am here=========222====")





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






##============================= with picture response ==========================
# from rest_framework import status
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.views import APIView
# from decimal import Decimal
# from datetime import datetime
# import stripe

# class ThirdPartyOrganizationPaymentHistoryView(APIView):
#     permission_classes = [IsAuthenticated]
    
#     def get(self, request):
#         user = request.user

#         try:
#             # Retrieve the organization related to the authenticated user
#             organization = user.organization
#         except Organization.DoesNotExist:
#             return Response({"error": "Organization not found"}, status=status.HTTP_404_NOT_FOUND)
        
#         # Create Stripe Customer for the organization (if not already created)
#         if not organization.stripe_organization_id:
#             try:
#                 customer = stripe.Customer.create(
#                     name=organization.name,
#                     email=organization.email,
#                 )
#                 organization.stripe_organization_id = customer['id']
#                 organization.save()
#             except stripe.error.StripeError as e:
#                 return Response({'error': f"Failed to create Stripe customer: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

#         # Ensure the organization has a Stripe customer ID
#         if not organization.stripe_organization_id:
#             return Response({"error": "This organization does not have a Stripe customer ID."}, status=status.HTTP_400_BAD_REQUEST)

#         # Create or get OrganizationAccount
#         organization_account, created = OrganizationAccount.objects.get_or_create(
#             organization=organization
#         )

#         try:
#             # Retrieve all charges for this customer
#             charges = stripe.Charge.list(
#                 customer=organization.stripe_organization_id,
#                 limit=100,
#             )

#             # If no charges exist, return an empty response without error
#             if not charges.data:
#                 return Response({
#                     'organization': organization.name,
#                     'total_payments': 0,
#                     'payments': []
#                 }, status=status.HTTP_200_OK)

#             payment_data = []
#             # Pre-fetch card logos
#             card_logos = self.get_card_logos()

#             for charge in charges.data:
#                 payment_info = self.construct_payment_info(charge, card_logos)
#                 payment_data.append(payment_info)

#             return Response({
#                 'organization': organization.name,
#                 'total_payments': len(payment_data),
#                 'payments': payment_data
#             }, status=status.HTTP_200_OK)

#         except stripe.error.StripeError as e:
#             return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

#     def construct_payment_info(self, charge, card_logos):
#         payment_method_details = charge.payment_method_details
#         payment_date = datetime.utcfromtimestamp(charge.created).strftime('%Y-%m-%d %H:%M:%S')

#         # Basic payment info
#         payment_info = {
#             'id': charge.id,
#             'amount': charge.amount / 100,
#             'currency': charge.currency,
#             'status': charge.status,
#             'description': charge.description,
#             'created_at': payment_date,
#             'customer_email': charge.billing_details.email,
#             'customer_name': charge.billing_details.name,
#             'receipt_url': charge.receipt_url,
#             'payment_method': payment_method_details['type'],
#             'card_logo': card_logos.get(payment_method_details['card']['brand'], card_logos['default'])  # Use card logo from mapping
#         }

#         # Payment method details (if it's a card)
#         if payment_method_details['type'] == 'card':
#             payment_info.update({
#                 'card_last4': payment_method_details['card']['last4'],
#                 'card_exp_month': payment_method_details['card']['exp_month'],
#                 'card_exp_year': payment_method_details['card']['exp_year'],
#             })

#         # Refund information (if any)
#         if charge.refunded:
#             refund = stripe.Refund.retrieve(charge.refunds.data[0].id)
#             payment_info.update({
#                 'refunded': True,
#                 'refund_amount': refund.amount / 100,
#                 'refund_date': datetime.utcfromtimestamp(refund.created).strftime('%Y-%m-%d %H:%M:%S'),
#                 'refund_status': refund.status,
#             })

#         # Decline reason (if the payment failed)
#         if charge.status == 'failed' and 'card' in payment_method_details:
#             payment_info.update({
#                 'decline_reason': payment_method_details['card'].get('decline_code')
#             })

#         # Balance transaction details (fees, net amount)
#         if charge.balance_transaction:
#             balance_transaction = stripe.BalanceTransaction.retrieve(charge.balance_transaction)
#             payment_info.update({
#                 'balance_transaction_amount': balance_transaction.amount / 100,
#                 'balance_transaction_fee': balance_transaction.fee / 100,
#                 'balance_transaction_net': balance_transaction.net / 100,
#             })

#         return payment_info

#     def get_card_logos(self):
#         return {
#             "visa": "https://drive.google.com/uc?export=view&id=1ngjJ-okelAQ3Ir13dm6xKrIkdKJCC7Gb",
#             "mastercard": "https://drive.google.com/uc?export=view&id=1Vayk-L92CjrGk-ZjYLIlxw9XEwnS3X4G",
#             "amex": "https://drive.google.com/uc?export=view&id=1JOlwvY8oI6UlM6Pn1ymGft650ilEfumT",
#             "discover": "https://drive.google.com/uc?export=view&id=15XnJS04RsVmf-cq5N6VMzRKUulwHYr-0",
#             "diners_club": "https://drive.google.com/uc?export=view&id=190EAGJy6bE2p9TrpI99FllkcFJ6h3cNk",
#             "jcb": "https://drive.google.com/uc?export=view&id=1mSqQ8bLXH-v4piIXDEH_FaOrH1n-4f_i",
#             "maestro": "https://drive.google.com/uc?export=view&id=1LAaGfquaj5LHBdLYFMVkVhYapb3Kw0xF",
#             "unionpay": "https://drive.google.com/uc?export=view&id=1KqWnslX1GytGrHWXNqZroiwf2DozWhNB",
#             "solo": "https://drive.google.com/uc?export=view&id=1d1JVaarj4hVi4r1y46l5wPtccYPwMNnY",
#             "visa_electron": "https://drive.google.com/uc?export=view&id=1mO9gzVqEDv0xhrFtKDChw7iRtDAe-ld7",
#             "default": "https://drive.google.com/uc?export=view&id=1ngjJ-okelAQ3Ir13dm6xKrIkdKJCC7Gb"
#         }

