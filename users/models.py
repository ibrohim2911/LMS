from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

USER_ROLES = (
    ("admin","admin"),
    ("librarian","librarian"),
    ("student","student"),
    ("teacher","teacher"),
    )
class User(AbstractUser):
    """
    Custom user model that includes roles and a temporary ban mechanism.
    """
    role = models.CharField(max_length=10, choices=USER_ROLES, default="student")
    is_banned = models.BooleanField(default=False)  # This field is now redundant but kept for backward compatibility
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    ban_expires_at = models.DateTimeField(null=True, blank=True, default=None,
                                          help_text="The user is banned until this date and time.")
    max_allowed = models.IntegerField(default=3)
    img = models.ImageField(upload_to='user_images/', null=True, blank=True)
    @property
    def is_banned(self):
        """Checks if the user is currently banned."""
        if self.ban_expires_at is None:
            return False
        else:
            return timezone.now() < self.ban_expires_at


class ActiveRefreshToken(models.Model):
    """Stores active refresh tokens for logout / refresh validation."""

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Active Refresh Token"
        verbose_name_plural = "Active Refresh Tokens"

class Notification(models.Model):
    """Model to store notifications for users."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Notification for {self.user.username} at {self.created_at}'
    class Meta:
        ordering = ['-created_at']