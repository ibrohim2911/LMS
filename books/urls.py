from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, TagViewSet, KitobViewSet, EbookViewSet,
    JournalsViewSet, ReservationViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'kitob', KitobViewSet)
router.register(r'ebooks', EbookViewSet)
router.register(r'journals', JournalsViewSet)
router.register(r'reservations', ReservationViewSet)

urlpatterns = [
    path('', include(router.urls)),
]