from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import F
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Category, Tag, Kitob, Comment, Reservation, Journals, Rating
from .serializers import (
    CategorySerializer, TagSerializer, KitobSerializer, CommentSerializer,
    ReservationSerializer, JournalsSerializer, RatingSerializer
)
from .paginator import KitobPagination
@extend_schema(
    description="API endpoint for categories. Supports filtering and CRUD operations.",
    methods=["GET"],
    summary="Retrieve a list of categories.",
    tags=["Categories"],
    responses={
        200: CategorySerializer(many=True),
        401: OpenApiTypes.OBJECT,
    }
)
class CategoryViewSet(viewsets.ModelViewSet):
    """API endpoint for categories."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    @extend_schema(
        description="Retrieve a single category by its ID.",
        summary="Retrieve a category.",
        tags=["Categories"],
        responses={
            200: CategorySerializer(),
            401: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        }
    )
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
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
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
    queryset = Kitob.objects.all()
    serializer_class = KitobSerializer
    permission_classes = [AllowAny]
    pagination_class = KitobPagination

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='category',
                description='Filter books by category ID',
                required=False,
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='sort',
                description='sort books based on criteria (latest, oldest, rating-high, rating-low, name-high, name-low, published-date-high, published-date-low)',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='tags',
                description='Filter books by tag IDs (comma-separated or multiple parameters)',
                required=False,
                type=OpenApiTypes.INT,
                many=True,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='time_range',
                description='Filter books by time range (format: start_date,end_date)',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='published_date',
                description='Filter books by published date (format: YYYY-MM-DD)',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='author',
                description='Filter books by author name (partial match)',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='search',
                description='Search for books by name or author (partial match)',
                required=False,
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='is_audio',
                description='Filter books that have an audio version available',
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='is_pdf',
                description='Filter books that have a PDF version available',
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
            ),
            OpenApiParameter(
                name='is_physical',
                description='Filter books that are physical copies',
                required=False,
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
            ),
        ]
    )
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

    def get_queryset(self):
        category = self.request.query_params.getlist('category', None)
        sort = self.request.query_params.get('sort', None)
        tags = self.request.query_params.getlist('tags', None)
        time_range = self.request.query_params.get('time_range', None)
        published_date = self.request.query_params.get('published_date', None)
        author = self.request.query_params.get('author', None)
        search = self.request.query_params.get('search', None)
        is_audio = self.request.query_params.get('is_audio', None)
        is_pdf = self.request.query_params.get('is_pdf', None)
        is_physical = self.request.query_params.get('is_physical', None)
        if search:
            queryset = Kitob.objects.filter(visible=True, name__icontains=search) | Kitob.objects.filter(visible=True, author__icontains=search)
        else:
            queryset = Kitob.objects.filter(visible=True)
        if category:
            queryset = queryset.filter(category__id=category)
        if tags:
            queryset = queryset.filter(tags__id__in=tags)
        if time_range:
            start_date, end_date = time_range.split(',')
            queryset = queryset.filter(read_time__range=[start_date, end_date])
        if published_date:
            queryset = queryset.filter(published_date=published_date)
        if author:
            queryset = queryset.filter(author__icontains=author)
        if is_audio:
            queryset = queryset.filter(audio__isnull=False)
        if is_pdf:
            queryset = queryset.filter(pdf__isnull=False)
        if is_physical:
            queryset = queryset.filter(is_physical=True)
        if sort == 'latest':
            queryset = queryset.order_by('-c_at')
        elif sort == 'oldest':
            queryset = queryset.order_by('c_at')
        elif sort == 'rating-high':
            queryset = queryset.order_by('-rating')
        elif sort == 'rating-low':
            queryset = queryset.order_by('rating')
        elif sort =='name-high':
            queryset = queryset.order_by('name')
        elif sort == 'name-low':
            queryset = queryset.order_by('-name')
        elif sort == 'published-date-high':
            queryset = queryset.order_by('-published_date')
        elif sort == 'published-date-low':
            queryset = queryset.order_by('published_date')
        return queryset
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
@extend_schema(
    description="API endpoint for ebooks. Supports filtering and CRUD operations.",
    summary="Manage ebooks.",
    tags=["Ebooks"],
)

class JournalsViewSet(viewsets.ModelViewSet):
    """API endpoint for journals."""
    queryset = Journals.objects.all()
    serializer_class = JournalsSerializer
    pagination_class = KitobPagination

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

@extend_schema(
    description="API endpoint for reservations. Supports creating, managing, and tracking book reservations.",
    summary="Manage reservations.",
    tags=["Reservations"],
)
class ReservationViewSet(viewsets.ModelViewSet):
    """API endpoint for reservations."""
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

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
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
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
class CommentViewSet(viewsets.ModelViewSet):
    """API endpoint for book comments."""
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    def get_queryset(self):
        
        parent = self.request.query_params.get('parent', None)
        book = self.request.query_params.get('book', None)
        user = self.request.query_params.get('user', None)
        if parent:
            self.queryset = self.queryset.filter(parent=parent)
        if book:
            self.queryset = self.queryset.filter(book=book)
        if user:
            self.queryset = self.queryset.filter(user=user)
        
        
        return self.queryset.order_by('c_at')
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]