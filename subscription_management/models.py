from django.db import models
from django.db import models
import uuid
import json
import datetime
import pytz
import calendar
import random
import zoneinfo
from django.utils import timezone
from django.utils.timezone import now


# Import
from django.contrib.auth import get_user_model
User = get_user_model()


TYPES = [
    ('flat', 'Flat'),
    ('percent', 'Percent'),
    ]

class Coupon(models.Model):
    CUPON_TYPE = [
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('custom', 'Custom'),
    ]

    title = models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    type = models.CharField(max_length=10, choices=CUPON_TYPE, default='monthly')
    discount_type = models.CharField(max_length=10, choices=TYPES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2) # Discount value mean percentage or amount.
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_to = models.DateTimeField(blank=True, null=True)
    max_uses = models.PositiveIntegerField(default=10)
    used_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_valid(self):
        return self.is_active and self.valid_from <= now() <= self.valid_to and self.used_count < self.max_uses



class SubscriptionPlan(models.Model): # Updated SubscriptionPlan model
    title = models.CharField(max_length=150, unique=True, blank=True)
    image = models.ImageField(upload_to='rydr/subscription_plan_images/', blank=True, null=True)

    base_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Weekly plan
    weekly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    weekly_duration = models.PositiveIntegerField(default=7)
    weekly_discount_type = models.CharField(max_length=10, choices=TYPES, default='percent')
    weekly_discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    weekly_final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    weekly_is_active = models.BooleanField(default=True)

    # Bi-weekly plan
    bi_weekly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bi_weekly_duration = models.PositiveIntegerField(default=14)
    bi_weekly_discount_type = models.CharField(max_length=10, choices=TYPES, default='percent')
    bi_weekly_discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    bi_weekly_final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    bi_weekly_is_active = models.BooleanField(default=True)

    # Monthly plan
    monthly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_duration = models.PositiveIntegerField(default=30)
    monthly_discount_type = models.CharField(max_length=10, choices=TYPES, default='percent')
    monthly_discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    monthly_final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    monthly_is_active = models.BooleanField(default=True)

    # Quarterly plan
    quarterly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quarterly_duration = models.PositiveIntegerField(default=90)
    quarterly_discount_type = models.CharField(max_length=10, choices=TYPES, default='percent')
    quarterly_discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    quarterly_final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    quarterly_is_active = models.BooleanField(default=True)

    # Half-yearly plan
    half_yearly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    half_yearly_duration = models.PositiveIntegerField(default=182)
    half_yearly_discount_type = models.CharField(max_length=10, choices=TYPES, default='percent')
    half_yearly_discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    half_yearly_final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    half_yearly_is_active = models.BooleanField(default=True)

    # Yearly plan
    yearly_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    yearly_duration = models.PositiveIntegerField(default=365)
    yearly_discount_type = models.CharField(max_length=10, choices=TYPES, default='percent')
    yearly_discount_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    yearly_final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    yearly_is_active = models.BooleanField(default=True)

    # VAT and service charge
    vat_type = models.CharField(max_length=10, choices=TYPES, default='flat')
    vat_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    service_charge_type = models.CharField(max_length=10, choices=TYPES, default='flat')
    service_charge_value = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    # Free trial info
    is_free_trial = models.BooleanField(default=False)
    free_trial_duration = models.PositiveIntegerField(default=0)

    features = models.JSONField(default=dict, blank=True, null=True)
    description = models.TextField(blank=True)

    is_popular = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    # def save(self, *args, **kwargs):
    #     # Example calculation for weekly final price
    #     final_price = self.weekly_price

    #     if self.weekly_discount_type == 'flat':
    #         final_price -= self.weekly_discount_value
    #     elif self.weekly_discount_type == 'percent':
    #         final_price -= (final_price * self.weekly_discount_value / 100)

    #     # Add VAT
    #     if self.vat_type == 'flat':
    #         final_price += self.vat_value
    #     elif self.vat_type == 'percent':
    #         final_price += (final_price * self.vat_value / 100)

    #     # Add service charge
    #     if self.service_charge_type == 'flat':
    #         final_price += self.service_charge_value
    #     elif self.service_charge_type == 'percent':
    #         final_price += (final_price * self.service_charge_value / 100)

    #     self.weekly_final_price = round(max(final_price, 0), 2)

    #     # Repeat similar logic for monthly_final_price, yearly_final_price, etc., if desired.

    #     super().save(*args, **kwargs)




class DriverSubscription(models.Model):
    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='driversubscriptions')
    package = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, related_name='driversubscriptionsplan', blank=True, null=True)
    stripe_payment_id = models.CharField(max_length=255, blank=True, null=True)


    start_date = models.DateTimeField(blank=True, null=True, default=timezone.now) 
    end_date = models.DateTimeField(blank=True, null=True) 
    total_days = models.PositiveIntegerField(blank=True, null=True, default=0)

    coupon_used = models.BooleanField(default=False)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    coupon_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # Plan Per Month Price.
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True) # Final Total Plan Price.

    status = models.BooleanField(default=True)
    auto_renew = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    

    updated_at = models.DateTimeField(auto_now=True, blank=True) 
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    
    
    def __str__(self):
        return f"{self.driver.username} - {self.package.title}"




class DriverTransaction(models.Model):
        
    PAYMENT_STATUS = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ]

    TRANSACTION_STATUS = [
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('withdraw', 'Withdraw'),
        ]

    

    driver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    subscription = models.ForeignKey(DriverSubscription, on_delete=models.SET_NULL, null=True, blank=True)

    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    store_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tran_id = models.CharField(max_length=256, null=True, blank=True)

    # Stripe Transaction IDs
    stripe_payment_intent_id = models.CharField(max_length=256, null=True, blank=True)
    stripe_charge_id = models.CharField(max_length=256, null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=256, null=True, blank=True)
    stripe_payment_method_id = models.CharField(max_length=256, null=True, blank=True)
    stripe_receipt_url = models.URLField(max_length=500, null=True, blank=True)

    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default='success')
    transaction_category = models.CharField(max_length=30, choices=TRANSACTION_STATUS, default='payment')

    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"Transaction({self.subscription}, {self.amount}, {self.payment_status})"
    
