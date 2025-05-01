from rest_framework.test import APITestCase

# from accounts.models import CustomUser

from django.contrib.auth import get_user_model

User = get_user_model()


class ModelTest(APITestCase):
    def test_create_user(self):
        user = User.objects.create_user("afsan1@gmail.com", "afsan1@12345")
        self.assertIsInstance(user, User)
        self.assertFalse(user.is_staff)
        self.assertEqual(user.email, "afsan1@gmail.com")
