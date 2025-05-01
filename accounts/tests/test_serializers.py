from unittest import TestCase

from django.contrib.auth import get_user_model

from accounts.serializers import TokenObtainPairSerializer
from . import test_views

User = get_user_model()


class TokenObtainPairSerializerTest(TestCase):
    def setUp(self) -> None:
        self.user = test_views.create_users(1)[0]

    def test_token_is_returned(self):
        token = TokenObtainPairSerializer.get_token(self.user)
        assert token != None
