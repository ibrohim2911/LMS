from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Custom User Admin configuration that correctly handles password hashing
    and displays custom user fields.
    """
    # Add custom fields to the list display in the admin
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'role', 'is_banned')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'role')

    # Add custom fields to the fieldsets to make them editable in the admin form.
    # We start with the default fieldsets and add our own.
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'phone_number', 'ban_expires_at'),
        }),
    )
    # Add custom fields to the add-user form
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Custom Fields', {
            'fields': ('role', 'phone_number', 'ban_expires_at'),
        }),
    )