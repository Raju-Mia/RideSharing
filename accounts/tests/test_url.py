from django.test import SimpleTestCase
from django.urls import reverse, resolve
from accounts.views import (
    RegisterUserAPIView,
    CreateDriver,
    LoginAPIView,
    LogOutAPIView,
    ValidateToken,
    ResendToken,
    ToggleBlockedStatus,
    VehicleAPIView,
    UserDetailAPI,
    DriverDetailAPI,
    DriversVehicle,
    CheckEmailIfExists,
    MyTokenObtainPairView,
    IndividualUserDetailAPI,
    ResetPasswordAPIView,
    ResendOTP,
    ValidateResetPasswordOTP,
    ChangePassword,
    CreateTripRequestAPIView,
    EditTrips,
    EditChildData,
    EditStops,
    CancelTrip,
    UserRatesDriver,
    DriverRatesUser,
)

# TokenRefreshView,TokenVerifyView,


class TestUrls(SimpleTestCase):
    def test_signup_url_is_resolves(self):
        url = reverse("signup")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, RegisterUserAPIView)

    def test_create_driver_url_is_resolves(self):
        url = reverse("create_driver")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, CreateDriver)

    def test_login_url_is_resolves(self):
        url = reverse("login")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, LoginAPIView)

    def test_logout_url_is_resolves(self):
        url = reverse("logout")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, LogOutAPIView)

    def test_validate_token_url_is_resolves(self):
        url = reverse("validate_token")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, ValidateToken)

    def test_validate_token_url_is_resolves(self):
        url = reverse("validate_token")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, ResendToken)

    def test_toggle_block_status_url_is_resolves(self):
        url = reverse(
            "toggle_block_status", args=["95e214ac-207f-43ec-a96f-dca847317436"]
        )
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, ToggleBlockedStatus)

    def test_register_vehicle_url_is_resolves(self):
        url = reverse("register_vehicle")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, VehicleAPIView)

    def test_all_users_url_is_resolves(self):
        url = reverse("all_users")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, UserDetailAPI)

    def test_all_drivers_url_is_resolves(self):
        url = reverse("all_drivers")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, DriverDetailAPI)

    def test_drivers_vehicle_url_is_resolves(self):
        url = reverse("drivers_vehicle", args=["95e214ac-207f-43ec-a96f-dca847317436"])
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, DriversVehicle)

    def test_check_email_url_is_resolves(self):
        url = reverse("check_email")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, CheckEmailIfExists)

    def test_token_obtain_pair_url_is_resolves(self):
        url = reverse("token_obtain_pair")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, MyTokenObtainPairView)

    # def test_token_refresh_url_is_resolved(self):
    #     url = reverse('token_refresh')
    #     print(resolve(url))
    #     self.assertEquals(resolve(url).func.view_class,TokenRefreshView)
    # def test_token_verify_url_is_resolved(self):
    #     url = reverse('token_verify')
    #     print(resolve(url))
    #     self.assertEquals(resolve(url).func.view_class,TokenVerifyView)
    def test_get_user_url_is_resolves(self):
        url = reverse("get_user")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, IndividualUserDetailAPI)

    def test_password_reset_url_is_resolves(self):
        url = reverse("password_reset")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, ResetPasswordAPIView)

    def test_password_resend_url_is_resolves(self):
        url = reverse("password_resend")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, ResendOTP)

    def test_password_reset_validation_url_is_resolves(self):
        url = reverse("password_reset_validation")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, ValidateResetPasswordOTP)

    def test_password_reset_confirm_url_is_resolves(self):
        url = reverse("password_reset_confirm")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, ChangePassword)

    def test_trip_request_url_is_resolves(self):
        url = reverse("trip_request")
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, CreateTripRequestAPIView)

    def test_edit_trips_url_is_resolves(self):
        url = reverse("edit_trips", args=["95e214ac-207f-43ec-a96f-dca847317436"])
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, EditTrips)

    def test_edit_child_info_url_is_resolves(self):
        url = reverse("edit_child_info", args=["1"])
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, EditChildData)

    def test_edit_stops_url_is_resolves(self):
        url = reverse("edit_stops", args=["2"])
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, EditStops)

    def test_cancel_trip_url_is_resolves(self):
        url = reverse("cancel_trip", args=["95e214ac-207f-43ec-a96f-dca847317436"])
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, CancelTrip)

    def test_user_rates_driver_url_is_resolves(self):
        url = reverse(
            "user_rates_driver", args=["95e214ac-207f-43ec-a96f-dca847317436"]
        )
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, UserRatesDriver)

    def test_driver_rates_user_url_is_resolves(self):
        url = reverse(
            "driver_rates_user", args=["95e214ac-207f-43ec-a96f-dca847317436"]
        )
        print(resolve(url))
        self.assertEquals(resolve(url).func.view_class, DriverRatesUser)
