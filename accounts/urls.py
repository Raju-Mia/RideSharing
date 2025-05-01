from django.urls import path
from django.contrib.auth import views as auth_views
from rest_framework_simplejwt.views import TokenVerifyView

from accounts.views.all_accounts import (
    AcceptOrDenyVehicleAssignRequest,
    ChangeEmail,
    ChangePasswordV2,
    ChangePhoneNumber,
    CheckIfUserIsDriver,
    CheckVehicleAPIView,
    DeleteAddress,
    DriversVerificationStatus,
    EmailExists,
    GetAllVehicles,
    GetDriversTripList,

    HasVehicleView,
    ListOfOnlineUsers,
    SuperAdminLoginView,
    OrganizationSignUp,
    RegisterHotel,
    ResetPasswordV2,
    UpdateUserInfo,
    UserCratesDriver,
    UserDetailAPI,
    UserProfileAPIView,
    ValidateResetPasswordOTPV2,
    ValidateToken,
    ResendToken,
    ResetPasswordAPIView,
    ValidateResetPasswordOTP,
    ResendOTP,
    ChangePassword,

    SocialLoginRegister,
    ValidateTokenFromUrl,
    VehicleTypesListView,
    PhoneExists,
    # GetManufacturer,
    # GetModels,
    GetTokenForWebSocket,
    SendVerificationMail,

)



from accounts.views import(
    account_login,
    account_logout,
    accounts_helper,
    driver_account,
    user_account,
    access_token,
    user_saved_place,
)



# App Name
app_name = "accounts"



urlpatterns = [
    
    #Accoutns_helper URL
    path('v1/check-username/', accounts_helper.CheckUsernameAvailability.as_view(), name='check-username'),

    
    #=========================== Login(for all kinds of user) ===================
    path("v1/login/", account_login.LoginView.as_view(), name="login"), # All Login
    path("v1/logout/", account_logout.LogOutAPIView.as_view(), name="logout"), # All Logout
    
    # path("v1/social-login/google/<str:provider>/",SocialLoginRegister.as_view(),name="social_login"),
    # path("v1/admin-login/", SuperAdminLoginView.as_view(), name="admin-login"), # Admin Login
    path("django-admin-login/",auth_views.LoginView.as_view(template_name="accounts/login.html"),name="login"), #No-Need
    


    #================== User/client Registration ============ old ===========
    path("v1/signup/", user_account.SignUpUser.as_view(), name="user_signup"), # User sign-in (no need)
    path("v1/validate-token/", ValidateToken.as_view(), name="validate_token"), # user sign-up varification (no need)
    
    
    #================ New User/client Registration ============= new ==========
    path("v1/user/login/", user_account.UserLogin.as_view(), name="user_login"),
    path("v1/user/login/verify/", user_account.UserLoginVerification.as_view()),
    path("v1/user/resend-otp-for-user-verification/<uuid:user_id>/",user_account.ResendOtpForUserVerificaiton.as_view()),
    path("v1/user/profile-create/", user_account.UserProfileCreateView.as_view()), # driver Profile create
    
    
    # path('user-details/a/', user_account.UserDetailsView.as_view(), name='user_details'),

    
    
    
    
    #================== Driver Account =======================
    path("v1/driver-signup/",driver_account.UserSignUpForDriverView.as_view()),
    path("v1/driver-signup/verify-otp/",driver_account.ValidateTokenFromSMS.as_view()), # name will be change
    path("v1/resend-otp-for-driver-number-verification/<uuid:user_id>/",driver_account.ResendOtpForNumberVerification.as_view()),
    path("v1/driver/profile-create/", driver_account.SignUpAsDriverView.as_view()), # driver Profile create
    
    # path("v1/driver/manufacturer-wise-vehicles-list/", driver_account.ManufacturerWiseVehiclesList.as_view()), # Medufecturer and Vehicles list
    # path("v1/driver/vehicle-register/",driver_account.RegisterVehicleView.as_view()), #Registering vehicle for Drivers.
    
    path("v1/driver/verifications-status/", driver_account.VerificationStatusView.as_view()), #check driver Verification Status
    # path("v1/driver/update-verification-info/", driver_account.ViewUpdateDriversInfoForVerification.as_view()), # Deriver Rejected Documentation resubmit.
    
    path("v2/driver/reset-password/", driver_account.DriverResetPasswordView.as_view()), # Driver Password reset
    path("v2/driver/reset-password/verify-otp/", driver_account.DriverPasswordResetVerification.as_view()),
    path("v2/driver/reset-password-change/",driver_account.DriverPasswordChnage.as_view()),
    
        
    path("v2/reset-password/", ResetPasswordV2.as_view(), name="password_reset_v2"), # Driver Password reset
    path("v2/password-reset/validate/",ValidateResetPasswordOTPV2.as_view(),name="password_reset_validationv2",),
    path("v2/password-reset/confirm/",ChangePasswordV2.as_view(),name="password_change",),
    
    path("v1/validate-token-from-url/<uuid:user_id>/<int:token>/",ValidateTokenFromUrl.as_view(),name="validate_token_from_url",),
    
    path("v1/hotel-registration/", RegisterHotel.as_view(), name="register_hotel"),
    path("v1/signup/organization/",OrganizationSignUp.as_view(),name="organization_signup",),
    # path("v1/organization-registers-driver/",OrganizationRegistersDriver.as_view(),name="organization_registers_drivers",),
    path("v1/user-registers-driver/",UserCratesDriver.as_view(),name="user_registers_driver",),
    
    
    # ====== otp code Resent
    path("v1/resend-token/", ResendToken.as_view(), name="resend_token"), # no need 
    path("v1/check-email/", EmailExists.as_view(), name="check_if_email_exists"),
    path("v1/check-phone/", PhoneExists.as_view(), name="check_if_phone_exists"),
    

    path("v1/user-is-driver/",CheckIfUserIsDriver.as_view(),name="check_if_user_is_driver",),
    path("v1/drivers-verification-status/",DriversVerificationStatus.as_view(),name="drivers_verification_status",), #driver Verification Status
    path("v1/list-of-users-online/",ListOfOnlineUsers.as_view(),name="list_of_online_users",), #online user
    

    # General Queries to Database for users and drivers
    path("v1/all-users/", UserDetailAPI.as_view(), name="all_users"),
    path("v1/profile/", UserProfileAPIView.as_view(), name="user_profile"),
    

    # ====Login JWT token ie. access, refresh token and verify access token=====
    path("v1/token/", access_token.MyTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("v1/refresh-token/", access_token.TokenRefreshView.as_view(), name="token_refresh"), # Refresh Token
    path("v1/token/getuser/", access_token.IndividualUserDetailAPI.as_view(), name="get_user"),
    path("v1/access-token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    

    # =========Password Reset / Forget Password (For all kinds of user)
    path("v1/password-reset/", ResetPasswordAPIView.as_view(), name="password_reset"),
    path("v1/password-reset/resend/", ResendOTP.as_view(), name="password_resend"),
    path("v1/password-reset/validate/",ValidateResetPasswordOTP.as_view(),name="password_reset_validation",),
    path("v1/password-reset/confirm/",ChangePassword.as_view(),name="password_reset_confirm",),
    
    
    path("v1/driver/show-my-trip-requests/",GetDriversTripList.as_view(),name="show_my_trip_requests",),
    path("v1/user/profile/", UserProfileAPIView.as_view(), name="user_profile"),
    path("v1/driver/vehicle-assign-request-status/",AcceptOrDenyVehicleAssignRequest.as_view(),name="vehicle_assign_request_status",),
    path("v1/get-all-vehicles/", GetAllVehicles.as_view(), name="get_all_vehicles"),
    path("v1/delete-address/<uuid:address_id>/",DeleteAddress.as_view(),name="delete_address"),
    
    
    # social
    path("v1/social-login/<str:provider>/", SocialLoginRegister.as_view(), name="social_auth"),
    # path("v1/get-user-info/", ClientInfo.as_view(), name="get_client_info"),
    path("v1/update-user-info/", UpdateUserInfo.as_view(), name="update_user_info"),
    # path("v1/register-source-service/", RegisterSource.as_view({"post": "create", "get": "list"}), name="register_source_service"),
    path("v1/check-if-driver-has-vehicle/<uuid:id>/", CheckVehicleAPIView.as_view(), name="check_if_driver_has_vehicle"),
    # path("v1/driver-info/<uuid:id>/", DriverInfoAPIView.as_view(), name="driver_info"),
    
    # path("v1/get-manufacturers/", GetManufacturer.as_view(), name="get_models"),
    # path("v1/get-models/", GetModels.as_view(), name="get_models"),
    
    # Send Verification Mail
    path("v1/send-verification-mail/", SendVerificationMail.as_view(), name="send_verification_mail"),
    path("v1/get-token-for-websocket/", GetTokenForWebSocket.as_view(), name="get_token_for_websocket"),
    path("v1/has-vehicle/", HasVehicleView.as_view(), name="has_vehicle"),
    path("v1/vehicle-types/", VehicleTypesListView.as_view(), name="vehicle_types_list"),
    path("v1/change-phone-number/", ChangePhoneNumber.as_view(), name="change_phone_number"),
    path("v1/change-email/", ChangeEmail.as_view(), name="change_email"),


    # saved place for user
    path('v1/saved-place/', user_saved_place.SavedPlaceListCreateView.as_view()),
    path('v1/saved-place/<int:pk>/', user_saved_place.SavedPlaceDetailView.as_view()),
    

]
