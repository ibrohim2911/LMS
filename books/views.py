from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from django.db.models import F
from drf_spectacular.utils import extend_schema
from drf_spectacular.openapi import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from .models import Category, Tag, Kitob, Ebook, Reservation, Journals, Rating
from .serializers import (
    CategorySerializer, TagSerializer, KitobSerializer, EbookSerializer,
    ReservationSerializer, JournalsSerializer, RatingSerializer
)
from .paginator import KitobPagination
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
                name='latest',
                description='Get only the latest 8 books (boolean flag)',
                required=False,
                type=OpenApiTypes.BOOL,
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
        ]
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_queryset(self):
        category = self.request.query_params.get('category', None)
        sort = self.request.query_params.get('sort', None)
        tags = self.request.query_params.getlist('tags', None)
        time_range = self.request.query_params.get('time_range', None)
        published_date = self.request.query_params.get('published_date', None)
        author = self.request.query_params.get('author', None)
        search = self.request.query_params.get('search', None)
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
class EbookViewSet(viewsets.ModelViewSet):
    """API endpoint for ebooks."""
    queryset = Ebook.objects.all()
    serializer_class = EbookSerializer
    pagination_class = KitobPagination
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
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

class ReservationViewSet(viewsets.ModelViewSet):
    """API endpoint for reservations."""
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
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

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
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


class RatingViewSet(viewsets.ModelViewSet):
    """API endpoint for book ratings."""
    queryset = Rating.objects.all()
    serializer_class = RatingSerializer
    permission_classes = [IsAuthenticated]
    
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
