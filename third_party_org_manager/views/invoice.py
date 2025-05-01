from django.urls import path
from django.http import JsonResponse, HttpResponse
from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import get_object_or_404
from django.template.loader import render_to_string
from weasyprint import HTML
from io import BytesIO

from datetime import datetime
from django.db.models import Q
from trip_management.models import Trip, TripStatus
from organization_manager.models import Organization
from third_party_org_manager.serializers.trip_serializers import TripListSerializer
from utils.pagination import CustomPageNumberPagination
from third_party_org_manager.models import OrganizationCustomer

import os
from django.urls import reverse
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated


from third_party_org_manager.models import ConciageTripInvoice
from third_party_org_manager.serializers.invoice_serializer import (
    OrganizationCompletedTripListSerializer,
    ConciageTripInvoiceSerializer,
    InvoiceListSerializer,
    )

# Directory for saving PDFs
PDF_STORAGE_PATH = 'invoices/'
os.makedirs(PDF_STORAGE_PATH, exist_ok=True)





#=========== OrganizationCompletedTripList =============
class OrganizationCompletedTripList(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to list only completed trips for the user's organization,
        excluding trips already linked to ConciageTripInvoice, with optional search functionality.
        """
        # Get organization ID from the user's profile
        user = request.user
        organization_id = user.organization.id

        # Query Parameters for search
        search_query = request.query_params.get('search', None)
        print("search_query", search_query)

        # Ensure the organization exists
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return Response({'error': 'Organization not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Get all trips already linked to an invoice
        invoiced_trips = ConciageTripInvoice.objects.values_list('trip', flat=True)

        # Base queryset for completed trips in the user's organization, excluding invoiced trips
        queryset = Trip.objects.filter(
            user__organization_id=organization_id,
            trip_status=TripStatus.COMPLETED
        ).exclude(id__in=invoiced_trips).order_by('-booking_time')

        # Apply search query if provided
        if search_query:
            queryset = queryset.filter(
                Q(passenger_phone_number__icontains=search_query) |  # Filtering by passenger_phone_number
                Q(passenger_name__icontains=search_query) |
                Q(pickup_location_name__icontains=search_query) |
                Q(final_dropoff_location_name__icontains=search_query)
            )

        # Paginate the filtered queryset
        paginator = self.pagination_class()
        paginated_trips = paginator.paginate_queryset(queryset, request)

        # Serialize the paginated trips
        print("i am here==============")
        serializer = OrganizationCompletedTripListSerializer(paginated_trips, many=True)

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)




#=========== OrganizationCompletedTripInvoiceList =============
class OrganizationCompletedTripInvoiceList(APIView): #updated
    """
    API View to list completed trip invoices for a specific organization
    with filtering by invoice_no, customer name, and company_name.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        user = request.user

        # Verify the user's associated organization
        organization = getattr(user, 'organization', None)
        if not organization:
            return Response(
                {"error": "User is not associated with any organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Base queryset filtered by organization
        queryset = ConciageTripInvoice.objects.filter(organization=organization)

        # Extract query parameters
        search_query = request.query_params.get("search", None)
        company_name = request.query_params.get("company_name", None)

        print("company_name:", company_name)

        # Apply search filter if provided
        if search_query:
            queryset = queryset.filter(
                Q(invoice_no__icontains=search_query) |
                # Q(customer__company_name__icontains=search_query) |
                Q(customer__name__icontains=search_query)
            )

        # Apply company_name filter if provided
        if company_name:
            queryset = queryset.filter(customer__company_name__icontains=company_name)

            print("queryset:", queryset)

        # Paginate results
        paginator = self.pagination_class()
        paginated_invoices = paginator.paginate_queryset(queryset, request)

        # Serialize paginated data
        serializer = InvoiceListSerializer(paginated_invoices, many=True)
        print("I am here---")

        # Return paginated response
        return paginator.get_paginated_response(serializer.data)






# =============== Invoice Create API View ======== Multiple tris =======
class InvoiceCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ConciageTripInvoiceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # # Get the total value provided by the user
            # provided_total = request.data.get('total', None)

            # # Calculate total manually
            # calculated_sub_total = sum(
            #     trip.final_fare_with_org_commission_rate for trip in Trip.objects.filter(id__in=trips)
            # )
            
            # Compare with the calculated total from the serializer
            trips = request.data.get('trip', [])
            if not trips:
                return Response({'detail': 'No trips provided.'}, status=status.HTTP_400_BAD_REQUEST)

            
            
            print("======= Collect all passenger phone numbers =====: ")
            # Collect all passenger phone numbers from the trips
            passenger_phone_numbers = [trip.passenger_phone_number for trip in Trip.objects.filter(id__in=trips)]

            # Check if all passenger phone numbers are the same
            if len(set(passenger_phone_numbers)) > 1:
                return Response({
                    'detail': 'The customer phone numbers do not match.',
                    'phone_numbers': passenger_phone_numbers
                }, status=status.HTTP_400_BAD_REQUEST)
                
                
                
            organization_customer = OrganizationCustomer.objects.filter(phone_number=passenger_phone_numbers[0]).first()
            if not organization_customer:
                return Response({
                    'detail': 'The customer does not exist.',
                    'phone_numbers': passenger_phone_numbers
            })
                
                
            #============== Crox checking ================
            # service_charge = 0  # Default service charge
            # sub_total_with_service_charge = calculated_sub_total + service_charge
            # vat = 0  # Default VAT
            # calculated_total = sub_total_with_service_charge + vat

            # if provided_total is not None and float(provided_total) != float(calculated_total):
            #     return Response({
            #         'detail': 'The provided total value does not match the calculated total.',
            #         'provided_total': provided_total,
            #         'calculated_total': calculated_total
            #     }, status=status.HTTP_400_BAD_REQUEST)


            # Save invoice if totals match
            invoice = serializer.save()
            invoice.customer = organization_customer
            invoice.issue_date = datetime.now().date()
            invoice.served_by = request.user
            invoice.save()
            
            
            invoice_pdf_link = request.build_absolute_uri(
                reverse('third_party_org_manager:invoice-pdf', kwargs={'invoice_id': str(invoice.id)})
            )
            return Response({
                'message': 'Invoice created successfully',
                'invoice_id': str(invoice.id),
                'account_no': invoice.account_no,
                'invoice_pdf_link': invoice_pdf_link,
            }, status=status.HTTP_201_CREATED)

        return Response({'detail': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




# =============== Invoice PDF API View ===============
class InvoicePDFAPIView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, invoice_id):
        """Generates and returns the PDF for an invoice."""
        # Fetch the invoice
        invoice = get_object_or_404(ConciageTripInvoice, id=invoice_id)

        # Fetch related trips
        trips = Trip.objects.filter(conciagetripinvoice=invoice)  # Replace 'conciagetripinvoice' with the correct field name.
        
        if trips.exists():
            first_trip_time = trips.first().booking_time  # Earliest trip booking time
            last_trip_time = trips.last().booking_time    # Latest trip booking time
        else:
            first_trip_time = None
            last_trip_time = None
        
        # for i in trips:
        #     print("trip_id: ", i.id)
        #     print("trip_status", i.trip_status)
        #     print("trip_fare: ", i.final_fare)
        #     print("commission_rate: ", i.org_commission_rate)
        #     print("trip_fare_with_org_commission_rate: ", i.final_fare_with_org_commission_rate)

        # Generate the HTML content for the PDF
        html_string = render_to_string('individual-invoice.html', {
            'invoice': invoice,
            'trips': trips,
            'first_trip_time': first_trip_time,
            'last_trip_time': last_trip_time,
        })
        
        # # Define PDF file storage path
        # PDF_STORAGE_PATH = '/media/ConciageTripInvoice'  # Replace with your actual storage path
        # os.makedirs(PDF_STORAGE_PATH, exist_ok=True)  # Ensure the directory exists
        # pdf_file_path = os.path.join(PDF_STORAGE_PATH, f'invoice_{invoice.invoice_no}.pdf')

        # # Generate the PDF
        # try:
        #     HTML(string=html_string).write_pdf(pdf_file_path)
        # except Exception as e:
        #     return HttpResponse(f"Error generating PDF: {str(e)}", status=500)
        

        # Generate the PDF in memory
        try:
            pdf_buffer = BytesIO()
            HTML(string=html_string).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)  # Move the buffer's cursor to the beginning
        except Exception as e:
            return HttpResponse(f"Error generating PDF: {str(e)}", status=500)

        # Serve the PDF for viewing in the browser
        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="invoice_{invoice.invoice_no}.pdf"'
        return response




# =============== Invoice PDF Download API View ===============
class InvoicePDFDownloadAPIView(APIView):
    # permission_classes = [IsAuthenticated]
    
    def get(self, request, invoice_id):
        print("==========i am here=========")
        """Generates and returns the PDF for an invoice."""
        try:
            invoice = get_object_or_404(ConciageTripInvoice, id=invoice_id)
        except ConciageTripInvoice.DoesNotExist:
            return HttpResponse('Conciage Trip Invoice does not exist!')

        # Generate HTML content
        html_string = render_to_string('individual-invoice.html', {'invoice': invoice})

        # Generate PDF
        pdf_file_path = os.path.join(PDF_STORAGE_PATH, f'invoice_{invoice.invoice_no}.pdf')
        HTML(string=html_string).write_pdf(pdf_file_path)

        # Serve the PDF for download
        with open(pdf_file_path, 'rb') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_no}.pdf"'
            return response

