from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, CommentViewSet, TagViewSet, KitobViewSet, JournalsViewSet, 
    ReservationViewSet, RatingViewSet, BookmarkViewSet
)
from .api_stats import Stats
router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'kitob', KitobViewSet, basename='kitob')
router.register(r'journals', JournalsViewSet, basename='journals')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')

comment = CommentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

urlpatterns = [
    path('', include(router.urls)),
    path('kitob/<int:kitob_pk>/comments/', comment, name='kitob-comments'),
    path('kitob/<int:kitob_pk>/comments/<int:pk>/', CommentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='comment-detail'),
    path('stats/', Stats.as_view(), name='stats'),
]