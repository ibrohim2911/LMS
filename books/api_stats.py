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

from .models import Kitob, Reservation, Bookmark, Rating

User = get_user_model()

class profileStats(APIView):
    """
    API endpoint to get statistics for a user's profile.
    """
    permission_classes = [AllowAny]  # Allow any user to access this endpoint

    @extend_schema(
        parameters=[
            OpenApiParameter(name='user_id', type=OpenApiTypes.INT, description='ID of the user to get stats for'),
            OpenApiParameter(name='start_date', type=OpenApiTypes.DATE, description='Start date for filtering reservations (YYYY-MM-DD)'),
            OpenApiParameter(name='end_date', type=OpenApiTypes.DATE, description='End date for filtering reservations (YYYY-MM-DD)'),
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
        active_reservations = reservations.filter(status=2).count()
        pending_reservations = reservations.filter(status=1).count()
        returned_reservations = reservations.filter(status=3).count()
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
