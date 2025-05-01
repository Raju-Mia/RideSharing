
from django.db import models
import uuid
from django.utils.translation import gettext_lazy as _

#Import
from accounts.models import CustomUser
from organization_manager.models import Organization
from trip_management.models import Trip


class OrganizationCustomer(models.Model):
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Each customer is associated with an organization
    organization = models.ForeignKey(
        Organization, 
        on_delete=models.CASCADE, 
        related_name='organization_customers',  # Updated to avoid conflict
        blank=True,
        null=True
    )  # One organization will have many customers
    
    name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)  # WhatsApp contact

    #Company Info
    company_name = models.CharField(max_length=255, blank=True, null=True) #new
    
    # Address Information
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Relationship with Trips
    # One customer can have many trips.
    trips = models.ManyToManyField(
        Trip, 
        related_name='organization_trip_customers',  # Updated to avoid conflict
        blank=True
    )  # One customer can have many trips

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    # String representation
    def __str__(self):
        return f"{self.name} - {self.organization.name}"

    class Meta:
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'
        ordering = ['-created_at']  # Orders by the latest created customer first
        
        
        
        




class InvoiceStatus(models.TextChoices):
    PENDING = 'pending', _('Pending')
    PAID = 'paid', _('Paid')
    CANCELLED = 'cancelled', _('Cancelled')


class InvoiceType(models.TextChoices):
    INDIVIDUAL = 'individual', _('Individual')
    SUMMERY = 'summery', _('Summery')


class ConciageTripInvoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    trip = models.ManyToManyField(Trip, blank=True)  # Changed to ManyToManyField

    # Invoice Infomation
    invoice_no = models.CharField(max_length=40, unique=True, editable=False)
    secret_sign = models.CharField(max_length=20, null=True, blank=True, editable=False)
    issue_date = models.DateField(blank=True, null=True)
    
    # Customer Information
    customer = models.ForeignKey(OrganizationCustomer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Trip Information
    quantity = models.PositiveIntegerField(default=1)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sub_total_with_service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.CharField(max_length=255, blank=True, null=True)

    # Conciage Payment Information
    account_name = models.CharField(max_length=255, blank=True, null=True)
    account_no = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    sort_code = models.CharField(max_length=255, blank=True, null=True)

    
    status = models.CharField(
        max_length=10,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.PENDING
    )
    type = models.CharField(
        max_length=20,
        choices=InvoiceType.choices,
        default=InvoiceType.INDIVIDUAL
    )
    served_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self) -> str:
        return str(self.id)





class ConciageTripSummaryInvoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True)
    trip_invoice = models.ManyToManyField(ConciageTripInvoice, blank=True)  #

    # Invoice Infomation
    invoice_no = models.CharField(max_length=40, unique=True, editable=False)
    secret_sign = models.CharField(max_length=20, null=True, blank=True, editable=False)
    issue_date = models.DateField(blank=True, null=True)
    
    # Customer Information
    customer = models.ForeignKey(OrganizationCustomer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Trip Information
    quantity = models.PositiveIntegerField(default=1)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    sub_total_with_service_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    vat = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    description = models.CharField(max_length=255, blank=True, null=True)

    # Conciage Payment Information
    account_name = models.CharField(max_length=255, blank=True, null=True)
    account_no = models.CharField(max_length=255, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    branch_name = models.CharField(max_length=255, blank=True, null=True)
    sort_code = models.CharField(max_length=255, blank=True, null=True)

    
    status = models.CharField(
        max_length=10,
        choices=InvoiceStatus.choices,
        default=InvoiceStatus.PENDING
    )
    type = models.CharField(
        max_length=20,
        choices=InvoiceType.choices,
        default=InvoiceType.SUMMERY
    )
    served_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    def __str__(self) -> str:
        return str(self.id)
