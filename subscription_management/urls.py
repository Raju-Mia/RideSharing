from django.urls import path

#Import
from subscription_management.views import (
    coupon,
    subscription_plan,
    driver_subscription,
)

#App Name
app_name = 'subscription_management'



urlpatterns = [
    # Cupon Manage
    path('v1/coupons/', coupon.CouponListCreateView.as_view(), name='coupon-list-create'),
    path('v1/coupons/<int:pk>/', coupon.CouponRetrieveUpdateDestroyView.as_view(), name='coupon-detail'),

    # Subscription Plan
    path('v1/subscription-plans/', subscription_plan.SubscriptionPlanListCreateView.as_view()),
    path('v1/subscription-plans/<int:pk>/', subscription_plan.SubscriptionPlanRetrieveUpdateDestroyView.as_view()),

    # ✅ New API for Subscription Price Calculation
    path("v1/subscription-plans/calculate/", subscription_plan.SubscriptionPriceCalculationAPIView.as_view()),

    # DriverSubscription Manage
    path('v1/driver-subscriptions/', driver_subscription.SubscriptionListView.as_view(), name='subscription-list'),
    path('v1/driver-subscription/create/', driver_subscription.CreateSubscriptionView.as_view(), name='create-subscription'),
    path('v1/driver-subscription/activate/', driver_subscription.ActivateSubscriptionView.as_view(), name='activate-subscription'),

    path('v1/driver-subscription/cancel/', driver_subscription.CancelSubscriptionView.as_view(), name='cancel-subscription'),

    path('v1/driver-transactions/', driver_subscription.TransactionListView.as_view(), name='transaction-list'),


]
