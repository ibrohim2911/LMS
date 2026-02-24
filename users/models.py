from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

USER_ROLES = (
    ("admin","admin"),
    ("staff","staff"),
    ("student","student")
    )
class User(AbstractUser):
    """
    Custom user model that includes roles and a temporary ban mechanism.
    """

    role = models.IntegerField(default=1)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    ban_expires_at = models.DateTimeField(null=True, blank=True, default=None,
                                          help_text="The user is banned until this date and time.")
    max_allowed = models.IntegerField(default=3)
    @property
    def is_banned(self):
        """Checks if the user is currently banned."""
        if self.ban_expires_at is None:
            return False
        # Compare the expiration time with the current time 
        else:
            return timezone.now() < self.ban_expires_at