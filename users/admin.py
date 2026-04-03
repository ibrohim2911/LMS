from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import User, ActiveRefreshToken, Notification

admin.site.register(ActiveRefreshToken)
admin.site.register(Notification)

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # Optional: show extra fields
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Extra", {"fields": ("role", "phone_number", "ban_expires_at", "max_allowed", "img")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {"fields": ("role", "phone_number")}),
    )
    list_display = ("username", "email", "role", "is_staff", "is_superuser", "is_active")
    search_fields = ("username", "email")