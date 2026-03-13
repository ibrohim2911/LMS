
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsNotBanned(BasePermission):
    """
    Global permission check for banned users.
    """
    message = "You are temporarily banned and cannot perform this action."

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return not getattr(request.user, 'is_banned', False)
        return True

class GuestPermission(BasePermission):
    """
    Allow guests (unauthenticated) to view books, comments, ratings, authors.
    """
    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return False
        # Only allow safe (read-only) methods
        return request.method in SAFE_METHODS

class StudentPermission(BasePermission):
    """
    Allow students to post/view reservation, comment, rating.
    """
    def has_permission(self, request, view):
        user = request.user
        if user and user.is_authenticated and getattr(user, 'role', None) == 'student':
            # Allow GET, POST, PUT, PATCH, DELETE for reservation, comment, rating endpoints
            # You should use this permission on those views only
            return True
        return False

class TeacherPermission(BasePermission):
    """
    Allow teachers to post/view journals.
    """
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and getattr(user, 'role', None) == 'teacher'

class LibrarianPermission(BasePermission):
    """
    Allow librarians to post/view books, authors, and edit reservations.
    """
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and getattr(user, 'role', None) == 'librarian'

class AdminPermission(BasePermission):
    """
    Allow admins to post/view users.
    """
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and getattr(user, 'role', None) == 'admin'

class SuperAdminPermission(BasePermission):
    """
    Allow Django superusers (is_superuser) to do everything.
    """
    def has_permission(self, request, view):
        user = request.user
        return user and user.is_authenticated and getattr(user, 'is_superuser', False)
    