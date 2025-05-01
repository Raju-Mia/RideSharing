from django.urls import path



from uc_admin.views import administration_operator, driver_views, service_pricing, trip_views, trip_live_tracking_views
from uc_admin.views import service_pricing

# app Name
app_name = "uc_admin"


urlpatterns = [
    
    # Administration User Manage (administration_operator.py)
    path('v1/admin/operators/list/', administration_operator.AdminOperatorsList.as_view()),
    path('v1/admin/operator/register/', administration_operator.AdminOperatorRegister.as_view()), # TODO Mail or Phone Otp not verify yet.
    path('v1/admin/operator/verify/', administration_operator.AdminOperatorVerify.as_view()), # TODO Future work with discuse
    path('v1/admin/operator/details/<uuid:operator_id>/', administration_operator.AdminOperatorDetails.as_view()),
    path('v1/admin/operator/<uuid:operator_id>/update/', administration_operator.AdminOperatorInfoUpdate.as_view()),
    path('v1/admin/operator/<uuid:operator_id>/password-change/', administration_operator.AdminOperatorPasswordChange.as_view()),
    path('v1/admin/operator/<uuid:operator_id>/password-reset/', administration_operator.AdminOperatorPasswordReset.as_view()), # TODO Future work
    
    # URL for handling all A,D,T operations
    path('v1/admin/operator/<uuid:operator_id>/status-update/', administration_operator.AdminOperatorStatusUpdate.as_view()),

    path('v1/admin/operator/<uuid:operator_id>/deactivated/', administration_operator.AdminOperatorDeactivated.as_view()), #IF NEEDED
    path('v1/admin/operator/<uuid:operator_id>/activated/', administration_operator.AdminOperatorActivated.as_view()), #IF NEEDED
    path('v1/admin/operator/<uuid:operator_id>/terminated/', administration_operator.AdminOperatorTerminated.as_view()), #IF NEEDED
    
    path('v1/admin/activated/operators-list/', administration_operator.AdminActivatedOperatorsList.as_view()), #IF NEEDED
    path('v1/admin/deactivated/operators-list/', administration_operator.AdminDeactivatedOperatorsList.as_view()), #IF NEEDED
    path('v1/admin/terminated/operators-list/', administration_operator.AdminTerminatedOperatorsList.as_view()), #IF NEEDED
     
    
    
    
    
    # service type Service Pricing
    # path("admin/get-vehicle-manufacturer-list/", service_pricing.GetManufacturerList.as_view()),
    path("administration/service-type-and-service-location-wise-price/", service_pricing.ServiceLocationWisePackagePrice.as_view()),
    path("administration/service-type-and-service-location-wise-price/<uuid:id>/", service_pricing.ServiceLocationWisePackagePrice.as_view()),
    


    path("administration/service-type-wise-price/", service_pricing.ServiceTypeWisePrice.as_view()),
    path("administration/service-type-wise-price/<str:id>/", service_pricing.ServiceTypeWisePrice.as_view()),




    # url for manage trips 
    path("trip-management/", trip_views.TripList.as_view()),
    path('trip/<uuid:trip_id>/', trip_views.TripDetailEdit.as_view()),
    path('trip/<uuid:trip_id>/add-extra-charges/', trip_views.AddExtraChargeFromAdministration.as_view()),
    path('trip/<uuid:trip_id>/extra-charges/<int:id>/', trip_views.ExtraChargeEditDeleteFromAdministration.as_view()),
    path('administration/org-trip/<uuid:org_id>/',trip_views.TripListForOrganization.as_view()),





    # url for manage drivers
    path("administration/driver/", driver_views.DriverListCreateEditDelete.as_view()),
    path('administration/driver/<uuid:driver_id>/', driver_views.DriverListCreateEditDelete.as_view()), 
    # path('administration/driver/<uuid:driver_id>/', driver_views.DriverListCreate.as_view()),

    path('administration/assign-driver/', trip_views.AssignDriver.as_view()),



    #live tracking
    path('administration/trip-list-for-live-tracking/', trip_live_tracking_views.TripListForLiveTracking.as_view()),
    path('administration/trips-current-location/', trip_live_tracking_views.TripCurrentLocation.as_view()),
    path('trips/<uuid:trip_id>/live-tracking/', trip_live_tracking_views.TripInfoForLiveTracking.as_view()),



]
