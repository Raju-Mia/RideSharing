from rest_framework.permissions import BasePermission
from django.utils import timezone
from subscription_management.models import DriverSubscription

"""
decorators in Django REST Framework (DRF) function-based views work on individual methods (like get, post, etc.), but for class-based views (CBVs) like APIView need custom permission class, 
"""




class HasActiveSubscription(BasePermission):
    """Permission to check if the driver has an active subscription."""
    
    message = "Access denied: You need an active subscription to use this feature. Please subscribe to continue."

    def has_permission(self, request, view):
        user = request.user

        # Check if the user has an active subscription
        has_active_subscription = DriverSubscription.objects.filter(
            driver=user, is_active=True, end_date__gt=timezone.now()
        ).exists()

        return has_active_subscription  # ✅ Returns True if an active subscription exists




# #used
# from subscription_management.permissions import HasActiveSubscription
# """This API is only accessible if the user has an active subscription."""
# permission_classes = [IsAuthenticated, HasActiveSubscription]