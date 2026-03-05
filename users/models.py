from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

USER_ROLES = (
    ("admin","admin"),
    ("staff","staff"),
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