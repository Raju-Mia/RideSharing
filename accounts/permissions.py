from rest_framework import permissions
from uc_admin.permissions import is_admin

# from .models import DataForOrganizationsDriverRegistration


def is_driver(obj):
    """
    Checks if user is driver
    """
    if hasattr(obj, "driver"):
        return True
    return False


def is_organization(obj):
    if hasattr(obj, "organization"):
        return True
    return False


class IsDriver(permissions.BasePermission):
    """
    Grants permission users who are also driver
    """

    def has_permission(self, request, view):
        user = request.user
        return is_driver(user)


class IsHotel(permissions.BasePermission):
    """
    Allows access only to admin users.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_hotel)


class IsNotDriver(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        print("user status is:", user)
        return not is_driver(user)


# class UrlIsValid(permissions.BasePermission):
#     def has_permission(self, request, view):
#         return DataForOrganizationsDriverRegistration.objects.filter(
#             id=self.kwargs["code"]
#         ).exists()


class IsOrganization(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        return is_organization(user)


class DriverWithNoRegisteredVehicle(permissions.BasePermission):
    def has_permission(self, request, view):
        if is_driver(request.user):
            if hasattr(request.user.driver, "vehicle"):
                return False
            return True
        return False


class IsVerifiedDriver(permissions.BasePermission):
    """
    Grants permission to users who have verified driver account
    """

    def has_permission(self, request, view):
        user = request.user
        if is_driver(user):
            return user.driver.status == "verified"
        return False


class IsNotBlacklisted(permissions.BasePermission):
    """
    Grants permission to user who are not blacklisted.
    """

    def has_permission(self, request, view):
        return request.user.blacklisted == False


class LevelOnePermission(permissions.BasePermission):
    """
    Grants permission to users who have level one permission
    """

    def has_permission(self, request, view):
        user = request.user
        if is_driver(user):
            return user.driver.level == "level_one"
        return False


class HasPermissionToViewDriversVerificationData(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True
