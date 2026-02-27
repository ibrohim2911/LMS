from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, getme

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('me/', getme, name='getme'),
]