from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, TagViewSet, KitobViewSet, EbookViewSet,
    JournalsViewSet, ReservationViewSet, RatingViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'kitob', KitobViewSet, basename='kitob')
router.register(r'ebooks', EbookViewSet, basename='ebook')
router.register(r'journals', JournalsViewSet, basename='journals')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'ratings', RatingViewSet, basename='rating')

urlpatterns = [
    path('', include(router.urls)),
]