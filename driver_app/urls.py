from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenVerifyView



from driver_app.views import driver, driver_vehicle_document, driver_accounts, driver_document, administrations

# App Name
app_name = "driver_app"



urlpatterns = [
    #  =========== For Admin Administration Panel =============
    path('v1/administration/driver/<uuid:trip_id>/eligible-drivers/', driver.GetAllVerifiedDriversToAssignTrip.as_view()),
    
    # ===============  For Update profile picture ===============
    path('v1/administration/driver/profile-edit-requests-list/', driver_accounts.AdministrationDriverProfileEditRequestListView.as_view()),
    path('v1/administration/driver/profile-edit-requests-detail/<int:pk>/', driver_accounts.AdministrationEditRequestDetailView.as_view()),
    path('v1/administration/driver/profile-edit-requests-approval/<int:pk>/', driver_accounts.AdminDriverProfileEditRequestApprovalView.as_view()),
    
    


    # ===============  For Driver App ===============
    path("v1/rydr-driver/driver/profile-edit-request/", driver_accounts.DriverProfileEditRequestView.as_view()),
    path("v1/rydr-driver/driver/profile-detail/", driver_accounts.DriverProfileDetailView.as_view()),

    path("v1/rydr-driver/driver/register/", driver_document.DriverRegisterView.as_view()),
    path("v1/rydr-driver/driver/submit-document/", driver_document.DriverDocumentUploadView.as_view()),
    path('v1/rydr-driver/driver/details/', driver_document.DriverDetailsAPIView.as_view()),
    path('v1/rydr-driver/driver/profile-picture-status/', driver_document.LastProfilePictureEditRequestStatus.as_view()),
    path("v1/rydr-driver/driver-document-status/", driver_document.DriverDocumentStatusView.as_view()),
    path('v1/rydr-driver/driver-info/', driver_document.DriverInfo.as_view()),
    path("v1/rydr-driver/driver/update-driver-reg-status/", driver_document.UpdateDriverRegNoStatus.as_view()),



    path('v1/rydr-driver/driver/vehicle/register/', driver_vehicle_document.VehicleRegisterView.as_view()),
    path('v1/rydr-driver/driver/vehicle/submit-documents/', driver_vehicle_document.VehicleDocumentUploadView.as_view(),),
    path('v1/rydr-driver/driver/documents/details/', driver_vehicle_document.VehicleDocumentDetailView.as_view(),),
    path('v1/rydr-driver/driver/vehicle-document-status/', driver_vehicle_document.VehicleStatus.as_view(),),
    path('v1/rydr-driver/driver/vehicle-info/', driver_vehicle_document.DriverVehicle.as_view(),),
    path('v1/rydr-driver/driver/update-vehicle-reg-no-status/', driver_vehicle_document.UpdateVehicleRegNoStatus.as_view(),),
    path('v1/rydr-driver/driver/vehicle/status/', driver.DriverVehicleStatus.as_view(),),
    path('v1/rydr-driver/driver/vehicle/document-info/', driver_document.DriverVehicleInfoAPIView.as_view(),),



    path('v1/administration/verified-drivers/', administrations.VerifiedDriverList.as_view()),
    path('v1/administration/submitted-drivers/', administrations.DocumentSubmittedDriverList.as_view()),
    path('v1/administration/expired-drivers/', administrations.ExpiredDriverList.as_view()),
    path('v1/administration/resubmitted-documents-drivers/', administrations.DocumentResubmittedDriverList.as_view()),
    path('v1/administration/document-details/<uuid:driver_id>/', administrations.DriverVehicleDetail.as_view()),
    path('v1/administration/document-update/<uuid:driver_id>/', administrations.DriverVehicleUpdate.as_view()), 





]
