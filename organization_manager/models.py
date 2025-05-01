
from django.db import models
from django.conf import settings
import uuid
from PIL import Image  # You can use this for image processing if needed


# #Import
# from trip_management.models import Trip
# from accounts.models import Driver, VehicleTypes, CustomUser



class Organization(models.Model):
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    
    stripe_organization_id = models.CharField(max_length=255, blank=True, null=True)
    stripe_connected_account_id = models.CharField(max_length=255, blank=True, null=True)  # New field for connected account ID
    default_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    default_payment_verified = models.BooleanField(default=False) 
    payment_link = models.URLField(blank=True, null=True)  # Allow blank and null values
    
    #Trip Rtd Info
    org_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    
    # Contact Information
    email = models.EmailField(max_length=255, unique=True, blank=True, null=True)
    phone_number = models.CharField(max_length=20, unique=True, blank=True, null=True)
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)
    
    
    
    # Address
    address_line1 = models.CharField(max_length=255, blank=True, null=True)
    address_line2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    
    # Organization Admin (Owner)
    admin_user = models.OneToOneField(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='admin_organization')

    # Profile Picture
    picture = models.ImageField(upload_to='organization_pictures/', blank=True, null=True)

    # Status and Other Metadata
    is_main_org = models.BooleanField(default=False)
    is_third_party_org = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    is_hold = models.BooleanField(default=False)
    is_terminate = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} - {self.name}"

    class Meta:
        verbose_name = 'Organization'
        verbose_name_plural = 'Organizations'
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        # Custom save logic if needed
        super(Organization, self).save(*args, **kwargs)





class OrganizationBankAccount(models.Model):
    organization = models.ForeignKey(
        Organization, on_delete=models.CASCADE, related_name="bank_accounts"
    )
    account_name = models.CharField(max_length=255, blank=True, null=True, help_text="Name on the bank account")
    account_number = models.CharField(max_length=20, blank=True, null=True, help_text="Bank account number")
    sort_code = models.CharField(max_length=8, blank=True, null=True, help_text="UK sort code in the format 'XX-XX-XX'")
    iban = models.CharField(max_length=34, blank=True, null=True, help_text="International Bank Account Number")
    bic_swift = models.CharField(max_length=11, blank=True, null=True, help_text="Bank Identifier Code (SWIFT)")
    bank_name = models.CharField(max_length=255, blank=True, null=True, help_text="Name of the bank")
    branch_name = models.CharField(max_length=255, blank=True, null=True, help_text="Name of the bank branch")
    address = models.TextField(blank=True, null=True, help_text="Bank address")
    is_default = models.BooleanField(default=False, blank=True, null=True, help_text="Set as default bank account for payments")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bank Account"
        verbose_name_plural = "Bank Accounts"

    def save(self, *args, **kwargs):
        # Ensure only one default bank account per organization
        if self.is_default:
            OrganizationBankAccount.objects.filter(organization=self.organization, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.account_name} - {self.bank_name} ({self.account_number})"






class OrganizationAccount(models.Model):
    # Basic Information
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.OneToOneField('Organization', on_delete=models.CASCADE, related_name='account')

    # Financial Information
    total_dealings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_due = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_trips_completed = models.IntegerField(default=0)
    final_fare_with_org_commission = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    total_org_commission_earn = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    
    credit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    debit = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    is_active = models.BooleanField(default=True)  # To deactivate an account if needed
    status = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Account for {self.organization.name}"

    class Meta:
        verbose_name = 'Organization Account'
        verbose_name_plural = 'Organization Accounts'
        ordering = ['-created_at']




class OrganizationTransaction(models.Model):
    TRANSACTION_TYPES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('payment', 'Payment'),
    )
    

    TRANSACTION_STATUS = (
        ('pending', 'Pending'),
        ('successed', 'Successful'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
        ('cancled', 'Cancled'),
        ('reversed', 'Reversed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization_account = models.ForeignKey('OrganizationAccount', on_delete=models.CASCADE, related_name='transactions')
    
    transaction_id = models.CharField(max_length=256, blank=True, null=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='payment')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=40, blank=True, null=True) # Card last 4 digit info with card images
    customer_info = models.CharField(max_length=256, blank=True, null=True) 
    payment_date = models.DateTimeField(blank=True, null=True)
    refund_date = models.DateTimeField(blank=True, null=True)
    refund_reason = models.TextField(blank=True, null=True)  # Reason for refund, if applicable
    decline_resone = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    # Status Information
    status = models.CharField(max_length=20, choices=TRANSACTION_STATUS, default='pending')
    is_successful = models.BooleanField(default=False)
    is_reversed = models.BooleanField(default=False)
    is_refunded = models.BooleanField(default=False)


    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.transaction_type.capitalize()} of {self.amount} for {self.organization_account.organization.name}"

    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        ordering = ['-created_at']

    def mark_as_successful(self):
        self.status = 'successed'
        self.is_successful = True
        self.save()

    def mark_as_failed(self):
        self.status = 'failed'
        self.is_successful = False
        self.save()

    def mark_as_reversed(self):
        self.status = 'reversed'
        self.is_reversed = True
        self.save()

    def mark_as_refunded(self, reason):
        self.status = 'refunded'
        self.is_refunded = True
        self.refund_reason = reason
        self.save()















