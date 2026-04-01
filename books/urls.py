from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, CommentViewSet, TagViewSet, KitobViewSet, JournalsViewSet,
    ReservationViewSet, RatingViewSet, BookmarkViewSet, AuthorViewSet, SubCategoryViewSet
)
from .api_stats import profileStats, mainPageStats, bookdetailStats

router = DefaultRouter()
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'subcategories', SubCategoryViewSet, basename='subcategory')
router.register(r'tags', TagViewSet, basename='tag')
router.register(r'kitob', KitobViewSet, basename='kitob')
router.register(r'journals', JournalsViewSet, basename='journals')
router.register(r'reservations', ReservationViewSet, basename='reservation')
router.register(r'ratings', RatingViewSet, basename='rating')
router.register(r'bookmarks', BookmarkViewSet, basename='bookmark')
router.register(r'authors', AuthorViewSet, basename='author')
comment = CommentViewSet.as_view({
    'get': 'list',
    'post': 'create',
})

urlpatterns = [
    path('', include(router.urls)),
    path('kitob/<int:kitob_pk>/comments/', comment, name='kitob-comments'),
    path('kitob/<int:kitob_pk>/comments/<int:pk>/',
         CommentViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}),
         name='comment-detail'),
    path('user-profile-stats/', profileStats.as_view(), name='profile-stats'),
    path('main-page-stats/', mainPageStats.as_view(), name='main-page-stats'),
    path('book-detail-stats/', bookdetailStats.as_view(), name='book-detail-stats'),

]
