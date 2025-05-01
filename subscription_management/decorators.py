from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from subscription_management.models import DriverSubscription


"""
decorators in Django REST Framework (DRF) function-based views work on individual methods (like get, post, etc.)
"""


def active_subscription_status():
    """Decorator to check if the driver has an active subscription."""
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(view, request, *args, **kwargs):
            user = request.user

            # Check if user has an active subscription
            active_subscription = DriverSubscription.objects.filter(driver=user, status=True, is_active=True, end_date__gt=timezone.now()).first()

            if not active_subscription:
                return Response(
                    {'message': 'You need an active subscription to access this feature.'},
                    status=status.HTTP_200_OK
                )

            return view_func(view, request, *args, **kwargs)
        return _wrapped_view
    return decorator


# #USED METHOD
# from subscription_management.decorators import active_subscription_status
# @active_subscription_status()
