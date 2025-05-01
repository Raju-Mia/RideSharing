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
from rest_framework.generics import ListAPIView


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


from third_party_org_manager.models import ConciageTripSummaryInvoice
from organization_manager.models import Organization
from third_party_org_manager.serializers.invoice_serializer import SummaryInvoiceListSerializer 
from third_party_org_manager.serializers.invoice_serializer import ConciageTripSummaryInvoiceSerializer  # adjust the import as needed
from utils.pagination import CustomPageNumberPagination

# Define the path where PDFs will be stored
PDF_STORAGE_PATH = 'invoices/'
os.makedirs(PDF_STORAGE_PATH, exist_ok=True)




from third_party_org_manager.serializers.invoice_serializer import InvoiceListSerializer, OrganizationCustomerCompanySerializer
from third_party_org_manager.models import ConciageTripInvoice



class OrganizationCustomerCompanyListView(ListAPIView):
    """
    API to get a list of all unique company names under an organization.
    Supports filtering by name, email, phone number, and company name using URL query parameters.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = OrganizationCustomerCompanySerializer

    def get_queryset(self):
        """
        Filter customers by organization and optional search parameters.
        """

        user = self.request.user  # ✅ Correct way to access request.user

        if not hasattr(user, "organization") or not user.organization:
            return OrganizationCustomer.objects.none()  # ✅ Returns an empty queryset instead of Response

        queryset = OrganizationCustomer.objects.filter(
            organization=user.organization
        ).exclude(company_name__isnull=True).exclude(company_name="")

        # Get query parameters from the URL
        name = self.request.query_params.get("name", None)
        email = self.request.query_params.get("email", None)
        phone_number = self.request.query_params.get("phone_number", None)
        company_name = self.request.query_params.get("company_name", None)

        # Apply filters dynamically based on parameters provided
        if name:
            queryset = queryset.filter(name__icontains=name)
        if email:
            queryset = queryset.filter(email__icontains=email)
        if phone_number:
            queryset = queryset.filter(phone_number__icontains=phone_number)
        if company_name:
            queryset = queryset.filter(company_name__icontains=company_name)

        # ✅ FIX: Correct ordering to avoid PostgreSQL DISTINCT error
        queryset = queryset.order_by('company_name').distinct('company_name')

        return queryset

    def list(self, request, *args, **kwargs):
        """
        Overriding the list method to return a proper error response.
        """
        user = request.user

        if not hasattr(user, "organization") or not user.organization:
            return Response(
                {"error": "User is not associated with any organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        queryset = self.get_queryset()
        if not queryset.exists():
            return Response(
                {"message": "No company names found!"}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)









class OrganizationTripInvoiceListAPIView(APIView):
    """
    API endpoint to list ConciageTripInvoice for an organization with filtering
    by customer name, email, phone number, and company name.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        user = request.user

        if not user.organization:
            return Response(
                {"error": "User is not associated with any organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Start with invoices for the user's organization
        # queryset = ConciageTripInvoice.objects.filter(organization=user.organization)
        queryset = ConciageTripInvoice.objects.filter(organization=user.organization).exclude(id__in=ConciageTripSummaryInvoice.objects.values_list('trip_invoice', flat=True))

        # Get filter query parameters
        name = request.query_params.get("name")
        email = request.query_params.get("email")
        phone_number = request.query_params.get("phone_number")
        company_name = request.query_params.get("company_name")

        # Apply filters on the related OrganizationCustomer fields
        if name:
            queryset = queryset.filter(customer__name__icontains=name)
        if email:
            queryset = queryset.filter(customer__email__icontains=email)
        if phone_number:
            queryset = queryset.filter(customer__phone_number__icontains=phone_number)
        if company_name:
            queryset = queryset.filter(customer__company_name__icontains=company_name)

        # Optionally, combine the filters into one Q object if needed:
        # filters = Q()
        # if name:
        #     filters &= Q(customer__name__icontains=name)
        # if email:
        #     filters &= Q(customer__email__icontains=email)
        # if phone_number:
        #     filters &= Q(customer__phone_number__icontains=phone_number)
        # if company_name:
        #     filters &= Q(customer__company_name__icontains=company_name)
        # queryset = queryset.filter(filters)

        # Paginate the results
        paginator = self.pagination_class()
        paginated_queryset = paginator.paginate_queryset(queryset, request)

        # Serialize the data
        serializer = InvoiceListSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)






# ---------- List Summary Invoices ----------
class OrganizationSummaryInvoiceList(APIView):
    """
    Lists summary invoices for the authenticated user's organization.
    """
    permission_classes = [IsAuthenticated]
    pagination_class = CustomPageNumberPagination

    def get(self, request, *args, **kwargs):
        user = request.user
        organization_id = user.organization.id if user.organization else None
        if not organization_id:
            return Response(
                {"error": "User is not associated with any organization."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            organization = Organization.objects.get(pk=organization_id)
        except Organization.DoesNotExist:
            return Response(
                {"error": "Organization not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        queryset = ConciageTripSummaryInvoice.objects.filter(organization=organization)
        
        # Optional search filtering by invoice number or customer name
        search_query = request.query_params.get("search", None)
        if search_query:
            queryset = queryset.filter(
                Q(invoice_no__icontains=search_query)
                | Q(customer__name__icontains=search_query)
            )

        paginator = self.pagination_class()
        paginated_invoices = paginator.paginate_queryset(queryset, request)
        serializer = SummaryInvoiceListSerializer(paginated_invoices, many=True)
        return paginator.get_paginated_response(serializer.data)

# ---------- Create Summary Invoice ----------
class SummaryInvoiceCreateAPIView(APIView):
    """
    Creates a summary invoice by aggregating multiple trip invoices.
    The request data must include a list of invoice IDs in the 'trip_invoice' field.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = ConciageTripSummaryInvoiceSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            invoice_ids = request.data.get('trip_invoice', [])
            if not invoice_ids:
                return Response({'detail': 'No invoices provided.'}, status=status.HTTP_400_BAD_REQUEST)

            # (Optional) You can validate here that all provided invoice IDs are valid
            summary_invoice = serializer.save()

            # Optionally set the customer to the customer of the first invoice
            if summary_invoice.trip_invoice.exists():
                summary_invoice.customer = summary_invoice.trip_invoice.first().customer
            summary_invoice.issue_date = datetime.now().date()
            summary_invoice.served_by = request.user
            summary_invoice.save()

            pdf_link = request.build_absolute_uri(
                reverse('third_party_org_manager:summary-invoice-pdf', kwargs={'invoice_id': str(summary_invoice.id)})
            )
            return Response({
                'message': 'Summary Invoice created successfully',
                'invoice_id': str(summary_invoice.id),
                'account_no': summary_invoice.account_no,
                'invoice_pdf_link': pdf_link,
            }, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Invalid data', 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)




# ---------- Generate Summary Invoice PDF for Viewing ----------
class SummaryInvoicePDFAPIView(APIView):
    """
    Generates and returns the PDF for a summary invoice.
    """
    
    def get(self, request, invoice_id):
        summary_invoice = get_object_or_404(ConciageTripSummaryInvoice, id=invoice_id)
        invoices = summary_invoice.trip_invoice.all()

        invoice_data = []
        
        for invoice in invoices:
            trips = invoice.trip.all().order_by("booking_time")
            if trips.exists():
                first_trip = trips.first()
                last_trip = trips.last()
                invoice_data.append({
                    "invoice": invoice,
                    "first_booking_time": first_trip.booking_time,
                    "last_booking_time": last_trip.booking_time,
                })
        
        html_string = render_to_string('summary-invoice.html', {
            'summary_invoice': summary_invoice,
            'invoice_data': invoice_data,
        })

        try:
            pdf_buffer = BytesIO()
            HTML(string=html_string).write_pdf(pdf_buffer)
            pdf_buffer.seek(0)
        except Exception as e:
            return HttpResponse(f"Error generating PDF: {str(e)}", status=500)

        response = HttpResponse(pdf_buffer, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="summary_invoice_{summary_invoice.invoice_no}.pdf"'
        return response
    
    
    

# ---------- Generate Summary Invoice PDF for Download ----------
class SummaryInvoicePDFDownloadAPIView(APIView):
    """
    Generates and returns the PDF for a summary invoice as a download.
    """
    def get(self, request, invoice_id):
        summary_invoice = get_object_or_404(ConciageTripSummaryInvoice, id=invoice_id)
        html_string = render_to_string('summary-invoice.html', {
            'invoice': summary_invoice,
            'invoices': summary_invoice.trip_invoice.all()
        })
        pdf_file_path = os.path.join(PDF_STORAGE_PATH, f'summary_invoice_{summary_invoice.invoice_no}.pdf')
        HTML(string=html_string).write_pdf(pdf_file_path)
        with open(pdf_file_path, 'rb') as pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="summary_invoice_{summary_invoice.invoice_no}.pdf"'
            return response
