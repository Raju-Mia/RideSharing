from django.urls import path

#Import
from organization_manager.views.organization import (
    OrganizationList,
    OrganizationRegister,
    OrganizationUpdate,
    OrganizationDelete,
    OrganizationSearchView,
    OrganizationChangePasswordForUser,
    OrganizationrUserTerminate,

)

from organization_manager.views.stripe_account import (
    OrganizationAccountDetails,
    OrganizationPaymentHistoryView,
    )


#App Name
app_name = 'organization_manager'

urlpatterns = [
    
    path('v1/admin/organizations/list/', OrganizationList.as_view()),
    path('v1/admin/organizations/search/', OrganizationSearchView.as_view()), #Not Used Yet
    path('v1/admin/organizations/create/', OrganizationRegister.as_view()),
    path('v1/admin/organizations/<uuid:pk>/update/', OrganizationUpdate.as_view()), 
    path('v1/admin/organizations/<uuid:pk>/delete/', OrganizationDelete.as_view()),
    
    path('v1/admin/organizations/change-password/<uuid:user_id>/', OrganizationChangePasswordForUser.as_view()), #UC Admin/Operator can cng Pass
    path('v1/admin/organizations/operator/terminate/<uuid:user_id>/',  OrganizationrUserTerminate.as_view()), # Organization Terminated
    
    
    # Strap Account Transactin
    path('v1/admin/organizations/account/<uuid:organization_id>/', OrganizationAccountDetails.as_view()), 
    path('v1/admin/organizations/stripe/transactions/<uuid:organization_id>/', OrganizationPaymentHistoryView.as_view(), name='transaction-history'),
    
]

