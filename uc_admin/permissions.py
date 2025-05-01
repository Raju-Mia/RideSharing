from rest_framework import permissions


def is_admin(obj):
    """
    checks if user is admin
    """
    if hasattr(obj, "admin"):
        return True
    return False


class IsAdmin(permissions.BasePermission):
    """
    Grants permission to users who have admin privilege.
    """

    def has_permission(self, request, view):
        return is_admin(request.user)


class IsOrganizationAdmin(permissions.BasePermission):
    """
    Grants permission to users who have admin privilege.
    """

    def has_permission(self, request, view):
        return hasattr(request.user, "organization")
