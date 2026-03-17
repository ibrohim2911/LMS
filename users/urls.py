from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, getme, LogoutView, NotificationViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('', include(router.urls)),
    path('me/', getme.as_view(), name='getme'),
    path('logout/', LogoutView.as_view(), name='logout'),
]