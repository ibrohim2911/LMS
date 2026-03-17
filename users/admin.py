from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ActiveRefreshToken, Notification

admin.site.register(ActiveRefreshToken)
admin.site.register(Notification)
admin.site.register(User)  


