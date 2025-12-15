from rest_framework.permissions import BasePermission


class IsNotBanned(BasePermission):
    """
    Global permission check for banned users.
    """
    message = "You are temporarily banned and cannot perform this action."

    def has_permission(self, request, view):
        # The `is_banned` property on the User model does all the work!
        if request.user and request.user.is_authenticated:
            return not request.user.is_banned
        return True