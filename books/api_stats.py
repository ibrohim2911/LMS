from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime

# drf-spectacular imports
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import Kitob, Reservation, Bookmark, Rating, Category, subCategory

User = get_user_model()


class bookdetailStats(APIView):
    """
    API endpoint to get statistics for a specific book.
    """
    permission_classes = [AllowAny]  # Allow any user to access this endpoint

    @extend_schema(
        parameters=[
            OpenApiParameter(name='book_id', type=OpenApiTypes.INT, description='ID of the book to get stats for'),
            OpenApiParameter(name='user_id', type=OpenApiTypes.INT,
                             description='ID of the user to get their rating for the book'),
        ],

        responses={200: 'A JSON object containing the book statistics.'},
        description="Get statistics for a specific book, including total reservations, average rating, and availability status."
    )
    def get(self, request):
        book_id = request.query_params.get('book_id')
        user_id = request.query_params.get('user_id')
        if not book_id:
            return Response({'error': 'book_id parameter is required.'}, status=400)
        if not user_id:
            user_id = request.user.id if request.user.is_authenticated else None
        try:
            book = Kitob.objects.get(id=book_id)
        except Kitob.DoesNotExist:
            return Response({'error': 'Book not found.'}, status=404)

        total_reservations = Reservation.objects.filter(book=book).count()
        total_ratings = Rating.objects.filter(book=book).count()
        star1 = Rating.objects.filter(book=book, score=1).count()
        star2 = Rating.objects.filter(book=book, score=2).count()
        star3 = Rating.objects.filter(book=book, score=3).count()
        star4 = Rating.objects.filter(book=book, score=4).count()
        star5 = Rating.objects.filter(book=book, score=5).count()
        self_score = Rating.objects.filter(book=book, user_id=user_id).first()
        stats = {
            'total_reservations': total_reservations,
            'total_ratings': total_ratings,
            'star1': star1,
            'star2': star2,
            'star3': star3,
            'star4': star4,
            'star5': star5,
            'self_score': self_score.score if self_score else None,

        }

        return Response(stats)


class profileStats(APIView):
    """
    API endpoint to get statistics for a user's profile.
    """
    permission_classes = [AllowAny]  # Allow any user to access this endpoint

    @extend_schema(
        parameters=[
            OpenApiParameter(name='user_id', type=OpenApiTypes.INT, description='ID of the user to get stats for'),
            OpenApiParameter(name='start_date', type=OpenApiTypes.DATE,
                             description='Start date for filtering reservations (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=OpenApiTypes.DATE,
                             description='End date for filtering reservations (YYYY-MM-DD)'),
        ],
        responses={200: 'A JSON object containing the user statistics.'},
        description="Get statistics for a user's profile, including total reservations, active reservations, and most reserved books."
    )
    def get(self, request):
        user_id = request.query_params.get('user_id')
        start_date_str = request.query_params.get('start_date')
        end_date_str = request.query_params.get('end_date')

        if not user_id:
            return Response({'error': 'user_id parameter is required.'}, status=400)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': 'User not found.'}, status=404)

        # Parse date parameters
        start_date = parse_datetime(start_date_str) if start_date_str else None
        end_date = parse_datetime(end_date_str) if end_date_str else None

        # Filter reservations based on date range
        reservations = Reservation.objects.filter(user=user)
        if start_date:
            reservations = reservations.filter(reservation_date__gte=start_date)
        if end_date:
            reservations = reservations.filter(reservation_date__lte=end_date)

        total_reservations = reservations.count()
        active_reservations = reservations.filter(status__in=['approved', 'given']).count()
        pending_reservations = reservations.filter(status='pending').count()
        returned_reservations = reservations.filter(status='returned').count()
        bookmarks = Bookmark.objects.filter(user=user).count()
        ratings = Rating.objects.filter(user=user).count()
        stats = {
            'total_reservations': total_reservations,
            'active_reservations': active_reservations,
            'bookmarks': bookmarks,
            'ratings': ratings,
            'pending_reservations': pending_reservations,
            'returned_reservations': returned_reservations,

        }

        return Response(stats)


class mainPageStats(APIView):
    """
    API endpoint to get statistics for the main page.
    """
    permission_classes = [AllowAny]  # Allow any user to access this endpoint

    @extend_schema(
        responses={200: 'A JSON object containing the main page statistics.'},
        description="Get statistics for the main page, including total books, active reservations, and most reserved books."
    )
    def get(self, request):
        total_books = Kitob.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        category_counts = Category.objects.count()
        category_counts += subCategory.objects.count()
        stats = {
            'total_books': total_books,
            'active_users': active_users,
            'category_counts': category_counts,
        }

        return Response(stats)
