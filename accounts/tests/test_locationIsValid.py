from rest_framework.test import APITestCase

from accounts.helpers import check_location


class LocationIsValidTest(APITestCase):
    def test_locationIsValid(self):
        location_is_valid = check_location("23.145601, 89.208946")
        location_is_not_valid = check_location("23.14560sdsada")
        location_exception = check_location("asdasdasdasd")
        # self.assertFalse(location_exception)
        self.assertFalse(location_is_not_valid)
        self.assertTrue(location_is_valid)
