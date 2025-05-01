from django.urls import path

#Import
from payment.views import driver, driver_card_manage, payment_view, old_views, payments, stripe_accounts, new_driver, driver_v1
from payment.views.org_payment import CreateOrganizationPaymentLinkView, stripe_webhook
from payment.views.org_payment import CreatePaymentSessionView, PaymentSuccessView, PaymentCancelView
from payment.views import future

#App Name
app_name = 'payment'

urlpatterns = [
    
    # Administration API==========================
    path("merchant-balance/", stripe_accounts.MerchantAccountBalance.as_view()), #stripe merchant Balance
    
    
    # Administration Driver API==========================
    
    
    # Administration Client API==========================
    
    
    # ========== For Clinet ==== Customer Account=========== Version_1=========
    path("create-stripe-customer/", payment_view.CreateStripeCustomer.as_view()), #phase-0
    path('stripe-user-secret/', payment_view.StripeUserSecret.as_view()), # Phase-1
    path("add-payment-method/", payment_view.AddPaymentMethodView.as_view()), # Phase-2
    path("view-users-card-info/", payment_view.ViewUserCardsInfo.as_view()), # Phase-3
    path("set-primary-card/<str:payment_method_id>/", payment_view.SetPrimaryCard.as_view()), # Phase-4
    path("remove-card/<str:payment_method_id>/", payment_view.RemoveUuserCard.as_view()), # Phase-5
    
    path("customer-balance/", stripe_accounts.CustomerBalanceView.as_view()),
    path("customer-has-balance/", stripe_accounts.CustomerHasBalance.as_view()),
    path("customer-transactions/", stripe_accounts.CustomerTransactionListView.as_view()),
    path("user-has-card/", stripe_accounts.UserHasCard.as_view()),
    
    
    
    # ========== For Driver App==== Conneected Account=========== Version_1=========
    path("v1/driver/onboarding/refresh/", driver_v1.DriverStripeAccountStatusView.as_view()),
    path("v1/driver/onboarding/complete/", driver_v1.DriverStripeAccountStatusView.as_view()),
    
    path('v1/driver/stripe-account-status/', driver_v1.DriverStripeAccountStatusView.as_view()), #0
    path("v1/driver/stripe-account-wallet/", driver_v1.DriverStripeAccountWallet.as_view()), #1
    path('v1/driver/account-onboarding-complete/', driver_v1.DriverAccountOnboardingComplate.as_view()), #2 (update)
    path('v1/driver/bank-accounts-list/', driver_v1.DriverBankAccountListView.as_view()), #3
    path('v1/driver/bank-account/details/<str:bank_account_id>/', driver_v1.DriverBankAccountDetails.as_view()),  #4
    
    path('v1/driver/payout-eligibility-status/', driver_v1.DriverPayoutEligibilityView.as_view()), #5
    path('v1/driver/default-payout-schedule-status/', driver_v1.DriverPayoutScheduleStatusView.as_view()), #6
    path('v1/driver/payout-default-schedule-setup/', driver_v1.DriverPayoutScheduleSetupView.as_view()), #7
    path('v1/driver/set-default-bank-account/', driver_v1.SetDefaultBankAccountView.as_view()), #8 (opstional)
    path('v1/driver/apply-payout-request/', driver_v1.DriverManualPayoutView.as_view()), #9 
    path('v1/driver/stripe-express-dashboard-link/', driver_v1.DriverStripeExpressDashboard.as_view()), #10
    
    path("v1/driver/all-transactions/", driver_v1.DriverAllTransactionsListView.as_view()),
    path("v1/driver/payout-request-transactions/", driver_v1.DriverPayoutRequestTransactionListView.as_view()),
    path("v1/driver/payout-successful-transactions/", driver_v1.DriverSuccessfulPayoutTransactionListView.as_view()),
    path("v1/driver/driver-earnings-details/", driver_v1.DriverEarningsDetailsView.as_view()),
    path("v1/driver/driver-earnings-details-overview/", driver_v1.DriverEarningsDetailsOverView.as_view()),
    path("v1/driver/driver-earnings/", driver.DriverEarningsView.as_view()), #old
    

    
    # ========== For Driver App==== Customer Account for cash job payment ======= Version_1=========
    path("v1/driver/create-stripe-customer/", driver_card_manage.DriverCreateStripeCustomer.as_view()), #phase-0
    path('v1/driver/stripe-user-secret/', driver_v1.StripeUserSecret.as_view()), # Phase-1
    path("v1/driver/add-payment-method/", driver_v1.AddPaymentMethodView.as_view()), # Phase-2
    path("v1/driver/view-users-card-info/", driver_v1.ViewUserCardsInfo.as_view()), # Phase-3
    path("v1/driver/set-primary-card/<str:payment_method_id>/", driver_v1.SetPrimaryCard.as_view()), # Phase-4
    path("v1/driver/remove-card/<str:payment_method_id>/", driver_v1.RemoveUuserCard.as_view()), # Phase-5

    


    path("v1/driver/deposit/add-fund-to-stripe-account/", driver_v1.DriverAddFundsToCustomerStripeAccount.as_view()), # Phase-6


    
    # Earnings Management-old
    path("v1/driver/driver-stripe-balance/", driver.DriverBalanceView.as_view()), #customer
    path("v1/driver/driver-transactions/", driver.DriverTransactionListView.as_view()), #customer
    


    # ============ Trip Payments Management ========================
    path("v1/client/payment/hold-payment-list/", payments.HeldPaymentsListView.as_view()), # Administration
    path('v1/clinet/payment/hold/<uuid:trip_id>/', payments.HoldPaymentView.as_view()),
    path('v1/clinet/payment/complete/<uuid:trip_id>/', payments.CompletePaymentView.as_view()),
    



    # ========== Third Party || Concierge Organization session Payment(Same link can be multiple times used)
    path('organization/create-payment-session/', CreatePaymentSessionView.as_view(), name='create-payment-session'), #Not sued
    path('payment-success/', PaymentSuccessView.as_view(), name='payment-success'),
    path('payment-cancel/', PaymentCancelView.as_view(), name='payment-cancel'),

    
    # =============== Third Party || Concierge Organization session Payment (One Time Use)
    path('third-party-org/create-payment-link/', CreateOrganizationPaymentLinkView.as_view(), name='create_payment_link'), #used
    path('webhook/stripe/', stripe_webhook, name='stripe_webhook'), #main
    
    

    


    # path("get-primary-card/", old_views.GetPrimaryCard.as_view(), name="get_primary_card"),
    # path("remove-a-card/<str:method_id>/", old_views.RemoveACard.as_view(), name="remove_a_card"),
    # path("user-is-stripe-customer/", old_views.UserIsStripeCustomer.as_view(), name="user_is_stripe_customer"),
    # path("perform-payment/<uuid:trip_id>/<str:payment_method>/", old_views.PerformPayment.as_view(), name="perform_payment"), # No Need
    # path("create-account-link/", old_views.CreateAccountLink.as_view(), name="create_account_link"), # No Need
    # path("payout/<uuid:user_id>/", old_views.Payout.as_view(), name="payout"), # No Need
    # path("webhook-test/", old_views.WebHook.as_view(), name="webhook_test"), # No Need
    
    
    

    
    #----------------------------- New for Testing --------------------------------
    path('v1/driver/account/create/', new_driver.DriverAccountCreateView.as_view()), # 1
    path('v1/driver/account/update/', new_driver.DriverAccountUpdateView.as_view()), 
    path('v1/driver/account-onboard/', new_driver.DriverAccountOnboardingView.as_view()), #2
    path('v1/driver/bank-account/add/', new_driver.AddBankAccountView.as_view()), 
    path("v1/driver/add-bank-account/", new_driver.DriverAddBankAccountView.as_view()), #3
    path("v1/customer-pay-the-trip-bill/", new_driver.CustomerPaymentView.as_view()), #4


    # #--------------------------driver Package Payment api--------------------------------
    # path("v1/driver/package-pay/", driver_subscription.subscription_pay),
    # path("v1/driver/package-pay-success/", driver_subscription.subscription_pay_success),
    # path("v1/driver/package-pay-failed/", driver_subscription.subscription_pay_failed),
    # path("v1/driver/package-pay-cancel/", driver_subscription.subscription_pay_cancel),

      
]
