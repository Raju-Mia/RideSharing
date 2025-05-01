from django.urls import path

#Import


from third_party_org_manager.views.account import (
    ThirdPartyUserLoginView,
    ThirdPartyOrganizationRegister,
    ThirdPartyOrganizationMailOtpVerification,
    ThirdPartyOrganizationResentMailOtp,
    ThirdPartyOrganizationProfileUpdateView,
    ThirdPartyOrganizationCommissionSetView,
    ThirdPartyOrganizationProfileDetailsView,
    
    ThirdPartyOrganizationUserListView,
    ThirdPartySearchOperatorView,
    ThirdPartyUserRegistrationView,
    ThirdPartyOperatorEditView,
    ThirdPartOperatorProfileUpdateView,
    ThirdPartOperatorProfileDetailsView,
    ThirdPartyMyselfUserChangePassword,
    ThirdPartyOrganizationChangePasswordForUser,
    ThirdPartyOrganizationrUserTerminate,

)


from third_party_org_manager.views.customer import (
    OrganizationCustomerListCreateAPIView,
    OrganizationCustomerDetailAPIView
)

from third_party_org_manager.views.trips import (
    OrganizationTripListView,
    OrganizationTripRequestView,
    OrganizationTripdetailView,
)


from third_party_org_manager.views.stripe_transation import (
    OrganizationCompletedTripListView,
    OrganizationCompletedTripDetailView,
    ThirdPartyOrganizationAccountView,
    ThirdPartyOrganizationPaymentHistoryView
)



from third_party_org_manager.views import (
    invoice, summary_invoice, trip_live_tracking_views
)


from third_party_org_manager.views.bank_account import (
    BankAccountListCreateView,
    BankAccountDetailView,
)


from third_party_org_manager.views import (
    card_manage,
)


#App Name
app_name = 'third_party_org_manager'

urlpatterns = [
    path('v1/third-party-org/operator/login/', ThirdPartyUserLoginView.as_view()),
    path('v1/third-party-org/create/', ThirdPartyOrganizationRegister.as_view()),
    path("v1/third-party-org/mail-otp-verify/", ThirdPartyOrganizationMailOtpVerification.as_view()),
    path("v1/third-party-org/resend-mail-otp/<uuid:user_id>/", ThirdPartyOrganizationResentMailOtp.as_view()),
    path('v1/third-party-org/profile/update/', ThirdPartyOrganizationProfileUpdateView.as_view()),
    path('v1/third-party-org/commission/set/', ThirdPartyOrganizationCommissionSetView.as_view()), #new Add
    
    path('v1/third-party-org/profile/details/', ThirdPartyOrganizationProfileDetailsView.as_view()),
    
    
    path('v1/third-party-org/operator/list/', ThirdPartyOrganizationUserListView.as_view()),
    path('v1/third-party-org/operator/search/', ThirdPartySearchOperatorView.as_view()), #No Used Yet
    path('v1/third-party-org/operator/register/', ThirdPartyUserRegistrationView.as_view()),
    path('v1/third-party-org/admin/operator/edit/<uuid:user_id>/', ThirdPartyOperatorEditView.as_view()), # admin can change ony
    path('v1/third-party-org/myself-operator/profile/update/', ThirdPartOperatorProfileUpdateView.as_view()), # Myself
    path('v1/third-party-org/myself-operator/profile/details/', ThirdPartOperatorProfileDetailsView.as_view()), # Myself
    path('v1/third-party-org/myself-operator/change-password/', ThirdPartyMyselfUserChangePassword.as_view()), # Mysefl Pass cng
    
    
    path('v1/third-party-org/operator/change-password/<uuid:user_id>/',  ThirdPartyOrganizationChangePasswordForUser.as_view()), # Admin Pass cng
    path('v1/third-party-org/operator/terminate/<uuid:user_id>/',  ThirdPartyOrganizationrUserTerminate.as_view()), # Admin user terminate

    # Customer
    path('v1/third-party-org/customers/', OrganizationCustomerListCreateAPIView.as_view()),
    path('v1/third-party-org/customers/<uuid:pk>/', OrganizationCustomerDetailAPIView.as_view()),
    
    # Bank Account
    path('v1/third-party-org/bank-accounts/', BankAccountListCreateView.as_view()),
    path('v1/third-party-org/bank-accounts/<int:pk>/', BankAccountDetailView.as_view()),


    # Organization Payment Transactions form stripe
    path('v1/third-party-org/unpaid-completed-trips/', OrganizationCompletedTripListView.as_view()),
    path('v1/third-party-org/unpaid-completed-trip-detail/<uuid:id>/', OrganizationCompletedTripDetailView.as_view()),
    
    path('v1/third-party-org/account/', ThirdPartyOrganizationAccountView.as_view()),
    path('v1/third-party-org/stripe/transactions/', ThirdPartyOrganizationPaymentHistoryView.as_view()),
    

    # Organization Trips 
    path('v1/organization/trip-request/', OrganizationTripRequestView.as_view()),
    path('v1/admin/organizations/trips/', OrganizationTripListView.as_view()),
    path('v1/admin/organizations/<uuid:id>/trip-detail/', OrganizationTripdetailView.as_view()),
    
    
    
    # Organization Invoice management
    path('v1/organizations/completed-trip/list/', invoice.OrganizationCompletedTripList.as_view()),
    path("v1/organizations/completed-trip-invoice/list/", invoice.OrganizationCompletedTripInvoiceList.as_view()),
    path('v1/organizations/invoice/create/', invoice.InvoiceCreateAPIView.as_view(), name='invoice-create'),
    path('v1/organizations/invoice/<uuid:invoice_id>/pdf/', invoice.InvoicePDFAPIView.as_view(), name='invoice-pdf'),
    path('v1/organizations/invoice/<uuid:invoice_id>/pdf/download/', invoice.InvoicePDFDownloadAPIView.as_view(), name='invoice-pdf-download'),

    # Organization Summery Invoice management=======
    path('v1/organizations/companies-customer-list/', summary_invoice.OrganizationCustomerCompanyListView.as_view()),

    path("v1/organizations/trip-invoices/", summary_invoice.OrganizationTripInvoiceListAPIView.as_view(), name="organization-trip-invoice-list"),
    path("v1/organizations/summary-invoice/list/", summary_invoice.OrganizationSummaryInvoiceList.as_view(), name="summary-invoice-list"),
    path("v1/organizations/summary-invoice/create/", summary_invoice.SummaryInvoiceCreateAPIView.as_view(), name="summary-invoice-create"),
    path("v1/organizations/summary-invoice/<uuid:invoice_id>/pdf/", summary_invoice.SummaryInvoicePDFAPIView.as_view(), name="summary-invoice-pdf"),
    path("v1/organizations/summary-invoice/<uuid:invoice_id>/pdf/download/", summary_invoice.SummaryInvoicePDFDownloadAPIView.as_view(), name="summary-invoice-pdf-download"),


    


    # Organization Trip Live tracking
    path('v1/organizations/trip-list-for-live-tracking/', trip_live_tracking_views.OrganizationTripListForLiveTracking.as_view()),
    path('v1/organizations/trips-current-location/', trip_live_tracking_views.OrganizationTripCurrentLocation.as_view()),
    path('v1/organizations/trips/<uuid:trip_id>/live-tracking/', trip_live_tracking_views.OrganizationTripInfoForLiveTracking.as_view()),




    # ========== Third Party Organization Card Maagement ===========
    path("v1/organizations/create-stripe-customer/", card_manage.CreateStripeCustomer.as_view()), #phase-0
    path("v1/organizations/stripe-user-secret/", card_manage.StripeUserSecret.as_view()), # Phase-1
    path("v1/organizations/add-payment-method/", card_manage.AddPaymentMethodView.as_view()), # Phase-2
    path("v1/organizations/view-users-card-info/", card_manage.ViewUserCardsInfo.as_view()), # Phase-3
    path("v1/organizations/set-primary-card/<str:payment_method_id>/", card_manage.SetPrimaryCard.as_view()), # Phase-4
    path("v1/organizations/remove-card/<str:payment_method_id>/", card_manage.RemoveUuserCard.as_view()), # Phase-5
    
    # path("v1/organizations/customer-balance/", card_manage.CustomerBalanceView.as_view()),
    # path("v1/organizations/customer-has-balance/", card_manage.CustomerHasBalance.as_view()),
    # path("v1/organizations/customer-transactions/", card_manage.CustomerTransactionListView.as_view()),
    # path("v1/organizations/user-has-card/", card_manage.UserHasCard.as_view()),
    

    
]

