from rest_framework.test import APITestCase

from accounts.helpers import generate_otp


class OTPTest(APITestCase):
    def test_generate_otp(self):
        otp = len(generate_otp)
        self.assertEqual(otp, 4)
