from django.contrib import admin
from subscription_management.models import Coupon, SubscriptionPlan, DriverSubscription, DriverTransaction


from django.contrib import admin
from .models import Coupon, SubscriptionPlan, DriverSubscription

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('title', 'code', 'discount_type', 'discount_value', 'valid_from', 'valid_to', 'is_active')
    search_fields = ('code', 'title')
    list_filter = ('discount_type', 'is_active', 'valid_from', 'valid_to')
    ordering = ('valid_from',)

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'base_price',
        'weekly_price', 'weekly_final_price', 'weekly_is_active',
        'monthly_price', 'monthly_final_price', 'monthly_is_active',
        'yearly_price', 'yearly_final_price', 'yearly_is_active',
        'is_active', 'is_popular'
    )
    search_fields = ('title',)
    list_filter = ('is_active', 'is_popular', 'weekly_is_active', 'monthly_is_active', 'yearly_is_active')
    # ordering = ('base_price',)
    ordering = ('yearly_price',)  # Sort by yearly_price in ascending order (low to high)

@admin.register(DriverSubscription)
class DriverSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('driver', 'package', 'start_date', 'end_date', 'price', 'total_price', 'is_active')
    search_fields = ('driver__username', 'package__title')
    list_filter = ('is_active', 'auto_renew', 'start_date', 'end_date')
    ordering = ('start_date',)


@admin.register(DriverTransaction)
class DriverTransactionAdmin(admin.ModelAdmin):
    list_display = ('driver', 'amount', 'payment_status', 'transaction_category', 'created_at')
    search_fields = ('driver__username', 'tran_id', 'payment_status')
    list_filter = ('payment_status', 'transaction_category')
    ordering = ('-created_at',)
