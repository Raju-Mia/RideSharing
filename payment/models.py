import uuid
from django.db import models
from django.conf import settings

#Import
from organization_manager.models import Organization

class ClientWallet(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255)
    stripe_connected_account_id = models.CharField(max_length=255, blank=True, null=True)  # New field for connected account ID
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    # topup_amount = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    default_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    default_payment_verified = models.BooleanField(default=False) 
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - ClinentWallet"


class DriverWallet(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    stripe_customer_id = models.CharField(max_length=255)
    stripe_connected_account_id = models.CharField(max_length=255, blank=True, null=True)  # New field for connected account ID
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    default_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    default_payment_verified = models.BooleanField(default=False) 
    status = models.BooleanField(default=True)
    

    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - Driver Wallet"






class OrganizationWallet(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    organization = models.OneToOneField(Organization, on_delete=models.SET_NULL, blank=True, null=True)
    
    # stripe_organization_id = models.CharField(max_length=255, blank=True, null=True)
    # stripe_connected_account_id = models.CharField(max_length=255, blank=True, null=True)  # New field for connected account ID
    # default_payment_method_id = models.CharField(max_length=255, blank=True, null=True)
    # default_payment_verified = models.BooleanField(default=False) 
    
    credit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    debit = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    balance = models.DecimalField(max_digits=15, decimal_places=2, default=0.00)
    
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"{self.organization} - Organization Wallet"



class Transaction(models.Model): #Not Apply Yet
    TRANSACTION_TYPES = [
        ('top_up', 'Top-Up'),
        ('booking_payment', 'Booking Payment'),
        ('refund', 'Refund'),
        ('earnings_transfer', 'Earnings Transfer'),
        ('withdrawal', 'Withdrawal'),
    ]
    id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES, blank=True, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    client_wallet = models.ForeignKey(ClientWallet, null=True, blank=True, on_delete=models.SET_NULL)
    driver_wallet = models.ForeignKey(DriverWallet, null=True, blank=True, on_delete=models.SET_NULL)
    transaction_id = models.CharField(max_length=256, blank=True, null=True)
    description = models.TextField(blank=True,null=True)
    status = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return f"Transaction {self.transaction_id} - {self.transaction_type}"



class HeldAmounts(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    intent_id = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
