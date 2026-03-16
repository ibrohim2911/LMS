from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from users.permissions import (
    GuestPermission, StudentPermission, TeacherPermission, LibrarianPermission, AdminPermission, SuperAdminPermission, IsNotBanned
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters as drf_filters
from django_filters import rest_framework as filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import F
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Category, Tag, Kitob, Comment, Reservation, Journals, Rating, Bookmark,Author
from .serializers import (
    CategorySerializer, TagSerializer, KitobSerializer, CommentSerializer,
    ReservationSerializer, JournalsSerializer, RatingSerializer, BookmarkSerializer, AuthorSerializer
)
from .paginator import KitobPagination, ReservationPagination

class KitobFilter(filters.FilterSet):
    # AllValuesMultipleFilter automatically handles lists like ?category=1&category=2 
    # and performs an 'IN' lookup, fixing potential issues in the original code.
    category = filters.AllValuesMultipleFilter(field_name='category__id')
    tags = filters.AllValuesMultipleFilter(field_name='tags__id')

    # Exact matches and standard lookups
    published_date = filters.DateFilter(field_name='published_date')
    author = filters.CharFilter(field_name='author', lookup_expr='icontains')
    is_physical = filters.BooleanFilter(field_name='is_physical')

    # Custom behavior filters
    time_range = filters.CharFilter(method='filter_time_range')
    is_audio = filters.BooleanFilter(method='filter_is_audio')
    is_pdf = filters.BooleanFilter(method='filter_is_pdf')

    # Map your custom sorting strings to actual model fields
    SORT_CHOICES = (
        ('latest', 'Latest'),
        ('oldest', 'Oldest'),
        ('rating-high', 'Rating High'),
        ('rating-low', 'Rating Low'),
        ('name-high', 'Name High'),
        ('name-low', 'Name Low'),
        ('published-date-high', 'Published Date High'),
        ('published-date-low', 'Published Date Low'),
    )
    sort = filters.ChoiceFilter(choices=SORT_CHOICES, method='filter_sort')

    class Meta:
        model = Kitob
        fields = ['category', 'tags', 'published_date', 'author', 'is_physical']

    def filter_time_range(self, queryset, name, value):
        if value and ',' in value:
            try:
                start_date, end_date = value.split(',')
                return queryset.filter(read_time__range=[start_date.strip(), end_date.strip()])
            except ValueError:
                pass # Fails gracefully if format is incorrect
        return queryset

    def filter_is_audio(self, queryset, name, value):
        if value is True:
            return queryset.filter(audio__isnull=False)
        elif value is False:
            return queryset.filter(audio__isnull=True)
        return queryset

    def filter_is_pdf(self, queryset, name, value):
        if value is True:
            return queryset.filter(pdf__isnull=False)
        elif value is False:
            return queryset.filter(pdf__isnull=True)
        return queryset

    def filter_sort(self, queryset, name, value):
        sort_mapping = {
            'latest': '-c_at',
            'oldest': 'c_at',
            'rating-high': '-rating',
            'rating-low': 'rating',
            'name-high': 'name',
            'name-low': '-name',
            'published-date-high': '-published_date',
            'published-date-low': 'published_date',
        }
        if value in sort_mapping:
            return queryset.order_by(sort_mapping[value])
        return queryset
class AuthorViewSet(viewsets.ModelViewSet):
    """API endpoint for authors."""
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer
    permission_classes = [AllowAny]

class BookmarkViewSet(viewsets.ModelViewSet):
    """API endpoint for bookmarks."""
    queryset = Bookmark.objects.all()
    serializer_class = BookmarkSerializer
    permission_classes = [StudentPermission|LibrarianPermission|SuperAdminPermission, IsNotBanned]
class CategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [GuestPermission|StudentPermission|TeacherPermission|LibrarianPermission|SuperAdminPermission]
        else:
            permission_classes = [LibrarianPermission|SuperAdminPermission]
        return [permission() for permission in permission_classes]
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

@extend_schema(
    description="API endpoint for tags. Supports filtering and CRUD operations.",
    methods=["GET"],
    summary="Retrieve a list of tags.",
    tags=["Tags"],
    responses={
        200: TagSerializer(many=True),
        401: OpenApiTypes.OBJECT,
    }
)
class TagViewSet(viewsets.ModelViewSet):
    """API endpoint for tags."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [GuestPermission|StudentPermission|TeacherPermission|LibrarianPermission|SuperAdminPermission]
        else:
            permission_classes = [LibrarianPermission|SuperAdminPermission]
        return [permission() for permission in permission_classes]
    @extend_schema(
        description="Retrieve a single tag by its ID.",
        summary="Retrieve a tag.",
        tags=["Tags"],
        responses={
            200: TagSerializer(),
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

@extend_schema(
    description="API endpoint for books (Kitob). Supports filtering, sorting, and searching.",
    summary="Manage books (Kitob).",
    tags=["Books (Kitob)"],
)
class KitobViewSet(viewsets.ModelViewSet):
    """API endpoint for books (Kitob)."""
    queryset = Kitob.objects.filter(visible=True)
    serializer_class = KitobSerializer  
    pagination_class = KitobPagination
    filter_backends = [DjangoFilterBackend, drf_filters.SearchFilter]
    filterset_class = KitobFilter
    search_fields = ['name', 'author__name']
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [GuestPermission|StudentPermission|TeacherPermission|LibrarianPermission|SuperAdminPermission]
        else:
            permission_classes = [LibrarianPermission|SuperAdminPermission]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a single book by ID.",
        description="""
        Get detailed information about a specific book, including its author, category, tags, and availability.
        This endpoint provides comprehensive data for a single book entry.
        """,
        responses={
            200: KitobSerializer(),
            404: OpenApiTypes.OBJECT,
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class JournalsViewSet(viewsets.ModelViewSet):
    """API endpoint for journals."""
    queryset = Journals.objects.all()
    serializer_class = JournalsSerializer
    pagination_class = KitobPagination
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
            permission_classes = [TeacherPermission|SuperAdminPermission]
        else:
            permission_classes = [SuperAdminPermission]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Retrieve a list of journals.",
        description="Get a paginated list of journals. Supports filtering by various attributes.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a single journal by ID.",
        description="Get detailed information about a specific journal, including its publisher and publication date.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new journal.",
        description="Create a new journal. This endpoint is restricted to authenticated users.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class ReservationFilter(filters.FilterSet):
    # Exact matches for IDs and Status
    user_id = filters.NumberFilter(field_name='user_id')
    status = filters.CharFilter(field_name='status')

    class Meta:
        model = Reservation
        fields = ['user_id', 'status']
@extend_schema(
    description="API endpoint for reservations. Supports creating, managing, and tracking book reservations.",
    summary="Manage reservations.",
    tags=["Reservations"],
)
class ReservationViewSet(viewsets.ModelViewSet):
    """API endpoint for reservations."""
    serializer_class = ReservationSerializer
    queryset = Reservation.objects.all()
    pagination_class = ReservationPagination
    filter_backends = [
        DjangoFilterBackend, 
        drf_filters.SearchFilter, 
        drf_filters.OrderingFilter
    ]
    filterset_class = ReservationFilter
    search_fields = ['book__name', 'book__author__name']
    ordering_fields = '__all__'
    ordering = ['-id']
    ordering_param = 'sort'
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
            permission_classes = [StudentPermission|LibrarianPermission|SuperAdminPermission]
        else:
            permission_classes = [SuperAdminPermission]
        return [permission() for permission in permission_classes]

    @extend_schema(
        summary="Retrieve a list of reservations.",
        description="Get a paginated list of reservations. This endpoint is restricted to authenticated users.",
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(
        summary="Retrieve a single reservation by ID.",
        description="Get detailed information about a specific reservation, including the book and user details.",
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    @extend_schema(
        summary="Create a new reservation.",
        description="Create a new reservation for a book. This endpoint is restricted to authenticated users.",
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    @extend_schema(
        summary="Approve a reservation.",
        description="""
        Approve a pending reservation for a book. This action decrements the book's quantity and marks the reservation as approved.
        This endpoint is restricted to authenticated users.
        """,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
            409: OpenApiTypes.OBJECT,
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        """Approve a reservation and decrement book quantity."""
        reservation = self.get_object()
        
        # Check if already approved
        if reservation.status == 2:
            return Response(
                {'detail': 'Reservation is already approved.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use atomic transaction to ensure consistency
        try:
            with transaction.atomic():
                book = Kitob.objects.select_for_update().get(pk=reservation.book.pk)
                
                # Validate availability
                if book.quantity <= 0:
                    return Response(
                        {'detail': 'No copies available for this book.'},
                        status=status.HTTP_409_CONFLICT
                    )
                
                # Decrement quantity and update availability
                book.quantity -= 1
                book.is_available = book.quantity > 0
                book.save(update_fields=['quantity', 'is_available'])
                
                # Update reservation status
                reservation.status = 2
                reservation.save()
        except Kitob.DoesNotExist:
            return Response(
                {'detail': 'Book not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            {'detail': 'Reservation approved successfully.'},
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary="Mark a book as returned.",
        description="""
        Mark a book as returned. This action increments the book's quantity and updates the reservation status.
        This endpoint is restricted to authenticated users.
        """,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAdminUser])
    def return_book(self, request, pk=None):
        """Mark a reservation as returned and increment book quantity."""
        reservation = self.get_object()
        
        # Check if reservation is currently approved
        if reservation.status != 2:
            return Response(
                {'detail': 'Only approved reservations can be marked as returned.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use atomic transaction to ensure consistency
        try:
            with transaction.atomic():
                # Increment quantity
                Kitob.objects.filter(pk=reservation.book.pk).update(
                    quantity=F('quantity') + 1
                )
                
                # Update book availability
                book = Kitob.objects.select_for_update().get(pk=reservation.book.pk)
                book.is_available = book.quantity > 0
                book.save(update_fields=['is_available'])
                
                # Update reservation status
                reservation.status = 3
                reservation.save()
        except Kitob.DoesNotExist:
            return Response(
                {'detail': 'Book not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(
            {'detail': 'Book marked as returned successfully.'},
            status=status.HTTP_200_OK
        )


@extend_schema(
    description="API endpoint for book ratings. Allows users to rate books and view ratings.",
    summary="Manage book ratings.",
    tags=["Ratings"],
)
class RatingViewSet(viewsets.ModelViewSet):
    """API endpoint for book ratings."""
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
            permission_classes = [StudentPermission|SuperAdminPermission]
        else:
            permission_classes = [SuperAdminPermission]
        return [permission() for permission in permission_classes]
    
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='book_id',
                description='Filter ratings by book ID.',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
        ],
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        """Allow filtering by book_id query parameter."""
        queryset = Rating.objects.all()
        book_id = self.request.query_params.get('book_id', None)
        if book_id:
            queryset = queryset.filter(book_id=book_id)
        return queryset
    
    def perform_create(self, serializer):
        """Automatically set the user to the current authenticated user."""
        serializer.save(user=self.request.user)
@extend_schema(
    description="API endpoint for book comments. Allows users to comment on books and view comments.",
    summary="Manage book comments.",
    tags=["Comments"],
)
class CommentViewSet(viewsets.ModelViewSet):
    """API endpoint for book comments."""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def get_queryset(self):
        parent = self.request.query_params.get('parent', None)
        book_id = self.kwargs.get('kitob_pk')
        user = self.request.query_params.get('user', None)
        if parent:
            self.queryset = self.queryset.filter(parent=parent)
        if book_id:
            self.queryset = self.queryset.filter(book_id=book_id)
        if user:
            self.queryset = self.queryset.filter(user=user)
        return self.queryset.order_by('c_at')

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy']:
            permission_classes = [StudentPermission|SuperAdminPermission]
        else:
            permission_classes = [SuperAdminPermission]
        return [permission() for permission in permission_classes]
    