import datetime

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils.functional import SimpleLazyObject
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.conf import LazySettings
from django.contrib.auth.middleware import get_user
from rest_framework_simplejwt.authentication import JWTAuthentication


User = get_user_model()
settings = LazySettings()
JWT_authenticator = JWTAuthentication()


class ActiveUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        current_user = request.user
        if request.user.is_authenticated:
            now = datetime.datetime.now()
            cache.set(str(current_user.id), now, settings.USER_LASTSEEN_TIMEOUT)


class JWTAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.user = SimpleLazyObject(lambda: self.__class__.get_jwt_user(request))

    @staticmethod
    def get_jwt_user(request):
        user = get_user(request)
        if user.is_authenticated:
            return user
        try:
            response = JWT_authenticator.authenticate(request)
        except:
            return AnonymousUser()
        if response is not None:
            user, _ = response
            return user
        return AnonymousUser()
