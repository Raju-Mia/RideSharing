from rest_framework import serializers
import uuid
from third_party_org_manager.models import OrganizationCustomer, ConciageTripInvoice
from trip_management.models import Trip
from driver_app.models import Vehicle

from organization_manager.models import OrganizationBankAccount

class DriverVehicleInfoSerializer(serializers.ModelSerializer):
    model_name = serializers.CharField(source='model.model', read_only=True)
    manufacturer = serializers.CharField(source='model.manufacturer.name', read_only=True)
    service_type = serializers.CharField(source='model.service_type', read_only=True)
    max_passengers = serializers.IntegerField(source='model.vehicletypesinfo.max_passengers', read_only=True)
    
    class Meta:
        model = Vehicle
        fields = [
            'vehicle_registration_number',
            'model',
            'service_type',
            'manufacturer',
            'model_name',
            'maximum_passengers',
            'luggage_capacity',
            'max_passengers',  # Add this field here
            'status',


        ]


class OrganizationCompletedTripListSerializer(serializers.ModelSerializer):
    organization_name = serializers.CharField(source='user.organization.name', read_only=True)
    dropoff_location_name = serializers.SerializerMethodField()
    final_fare = serializers.SerializerMethodField()
    driver_vehicle_info = serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = [
            'id',
            'unique_id',
            'trip_method',
            'pickup_time',
            'pickup_location_name',
            'final_dropoff_time',
            'dropoff_location_name',
            'passenger_name',
            'luggage_type',
            'final_fare',
            'trip_status',
            'payment_status',
            'organization_name',
            'service_type',
            'final_distance_covered',
            'final_duration',
            'per_mile_cost',
            'per_hour_cost',
            'fare',
            'congestion_charge',
            'service_charge',
            'vat',
            'org_commission_rate',
            'driver_vehicle_info',
        ]

    def get_dropoff_location_name(self, obj):
        return obj.final_dropoff_location_name or obj.initial_dropoff_location_name

    def get_final_fare(self, obj):
        if obj.final_fare != 0:
            return obj.final_fare
        if obj.fare != 0:
            return obj.fare
        return obj.estimated_fare

    def get_driver_vehicle_info(self, obj):
        if obj.driver and hasattr(obj.driver, 'vehicles'):
            vehicle = obj.driver.vehicles
            return DriverVehicleInfoSerializer(vehicle).data
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)

        def format_decimal(value):
            try:
                return "{:.2f}".format(float(value))
            except (TypeError, ValueError):
                return value

        # Format final_fare if present and valid
        if representation.get('final_fare') is not None:
            representation['final_fare'] = format_decimal(representation['final_fare'])

        return representation



    

class OrganizationCustomerCompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationCustomer
        fields = ['id', 'company_name']


        

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationCustomer
        fields = [
            'id',
            'name',
            'email',
            'phone_number',
            'whatsapp_number',
            'company_name', # New field
            'address',
            'city',
            'state',
            'country',
            'postal_code',
        ]




class InvoiceListSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()  # Nested serializer for customer information

    class Meta:
        model = ConciageTripInvoice
        fields = [
            'id',
            'invoice_no',
            'issue_date',
            'customer',  # Customer details will be included here
            'quantity',
            'sub_total',
            'service_charge',
            'total',
            'status',
            'type',
            'created_at',
        ]







class ConciageTripInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConciageTripInvoice
        fields = [
            'id', 'organization', 'trip', 'invoice_no', 'secret_sign', 'issue_date',
            'customer', 'quantity', 'sub_total', 'service_charge', 'sub_total_with_service_charge',
            'vat', 'total', 'description', 'account_name', 'account_no', 'bank_name',
            'branch_name', 'sort_code', 'status', 'type', 'served_by', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'organization', 'invoice_no', 'secret_sign', 'created_at', 'updated_at']

    def validate_trip(self, value):
        if not all(Trip.objects.filter(id=trip.id).exists() for trip in value):
            raise serializers.ValidationError("One or more trip IDs are invalid.")
        return value

    def create(self, validated_data):
        # Set the organization to the request user's organization
        validated_data['organization'] = self.context['request'].user.organization

        # Generate invoice number and secret sign
        validated_data['invoice_no'] = f"INV-{uuid.uuid4().hex[:8].upper()}"
        validated_data['secret_sign'] = f"SS-{uuid.uuid4().hex[:6].upper()}"

        # Retrieve trips from validated data without popping
        trips = validated_data.get('trip', [])
        validated_data['quantity'] = len(trips)
        
        # Calculate totals
        sub_total = sum(trip.final_fare_with_org_commission_rate for trip in trips)
        
        # Default to 0 for service charge and VAT
        service_charge = 0  
        sub_total_with_service_charge = sub_total + service_charge
        vat = 0  
        total = sub_total_with_service_charge + vat

        # Assign calculated values
        validated_data['sub_total'] = sub_total
        validated_data['service_charge'] = service_charge
        validated_data['sub_total_with_service_charge'] = sub_total_with_service_charge
        validated_data['vat'] = vat
        validated_data['total'] = total

        # Retrieve the user's organization and default bank account
        organization = self.context['request'].user.organization
        default_bank_account = OrganizationBankAccount.objects.filter(
            organization=organization, is_default=True
        ).first()

        # If a default bank account is found, assign its data to the invoice
        if default_bank_account:
            validated_data['account_name'] = default_bank_account.account_name
            validated_data['account_no'] = default_bank_account.account_number
            validated_data['bank_name'] = default_bank_account.bank_name
            validated_data['branch_name'] = default_bank_account.branch_name
            validated_data['sort_code'] = default_bank_account.sort_code

        # Create invoice instance without removing 'trip' field
        trips_data = validated_data.pop('trip', [])
        invoice = super().create(validated_data)

        # Add trips to the invoice (ManyToMany relationship)
        if trips_data:
            invoice.trip.set(trips_data)

        return invoice

    def update(self, instance, validated_data):
        # Set the organization to the request user's organization
        validated_data['organization'] = self.context['request'].user.organization

        # Proceed with the regular update logic
        return super().update(instance, validated_data)



# ============ summary invoice serializer ============

from third_party_org_manager.models import ConciageTripInvoice, ConciageTripSummaryInvoice
from organization_manager.models import OrganizationBankAccount
from third_party_org_manager.models import OrganizationCustomer
from accounts.models import CustomUser

# Serializer used for listing summary invoices
class SummaryInvoiceListSerializer(serializers.ModelSerializer):
    customer = CustomerSerializer()  # Include nested customer details

    class Meta:
        model = ConciageTripSummaryInvoice
        fields = [
            'id',
            'invoice_no',
            'issue_date',
            'customer',
            'quantity',
            'sub_total',
            'service_charge',
            'total',
            'status',
            'type',
            'created_at',
        ]

# Main serializer for creating/updating a summary invoice
class ConciageTripSummaryInvoiceSerializer(serializers.ModelSerializer):
    # Accept a list of ConciageTripInvoice IDs for aggregation
    trip_invoice = serializers.PrimaryKeyRelatedField(
        many=True, 
        queryset=ConciageTripInvoice.objects.all()
    )

    class Meta:
        model = ConciageTripSummaryInvoice
        fields = [
            'id', 
            'organization', 
            'trip_invoice', 
            'invoice_no', 
            'secret_sign', 
            'issue_date',
            'customer', 
            'quantity', 
            'sub_total', 
            'service_charge', 
            'sub_total_with_service_charge',
            'vat', 
            'total', 
            'description', 
            'account_name', 
            'account_no', 
            'bank_name',
            'branch_name', 
            'sort_code', 
            'status', 
            'type', 
            'served_by', 
            'created_at', 
            'updated_at',
        ]
        read_only_fields = [
            'id', 'organization', 'invoice_no', 'secret_sign', 'quantity', 
            'sub_total', 'service_charge', 'sub_total_with_service_charge', 
            'vat', 'total', 'served_by', 'created_at', 'updated_at'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        organization = request.user.organization
        validated_data['organization'] = organization

        # Generate a unique invoice number and secret sign
        validated_data['invoice_no'] = f"SUM-{uuid.uuid4().hex[:8].upper()}"
        validated_data['secret_sign'] = f"SS-{uuid.uuid4().hex[:6].upper()}"

        # Extract the list of invoices that will be summarized
        invoices = validated_data.pop('trip_invoice', [])
        validated_data['quantity'] = len(invoices)
        
        # Aggregate totals from each selected invoice
        validated_data['sub_total'] = sum(invoice.sub_total for invoice in invoices)
        validated_data['service_charge'] = sum(invoice.service_charge for invoice in invoices)
        validated_data['sub_total_with_service_charge'] = sum(invoice.sub_total_with_service_charge for invoice in invoices)
        validated_data['vat'] = sum(invoice.vat for invoice in invoices)
        validated_data['total'] = sum(invoice.total for invoice in invoices)

        # Optionally, set default bank account details from the organization
        default_bank_account = OrganizationBankAccount.objects.filter(
            organization=organization, is_default=True
        ).first()
        if default_bank_account:
            validated_data['account_name'] = default_bank_account.account_name
            validated_data['account_no'] = default_bank_account.account_number
            validated_data['bank_name'] = default_bank_account.bank_name
            validated_data['branch_name'] = default_bank_account.branch_name
            validated_data['sort_code'] = default_bank_account.sort_code

        # Create the summary invoice and add the invoice relationships
        summary_invoice = ConciageTripSummaryInvoice.objects.create(**validated_data)
        summary_invoice.trip_invoice.set(invoices)
        return summary_invoice
