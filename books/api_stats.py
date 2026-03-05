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

from .models import Kitob, Reservation

User = get_user_model()

class Stats(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        tags=['Stats'],
        parameters=[
            OpenApiParameter(
                name='period',
                type=OpenApiTypes.STR,
                location=OpenApiParameter.QUERY,
                description="Time period for stats (day, week, month, custom). Default is 'day'.",
                enum=['day', 'week', 'month', 'custom'] # Optional: adds a dropdown in UI
            ),
            OpenApiParameter(
                name="start_time",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description="Start of the time window (ISO 8601 format)"
            ),
            OpenApiParameter(
                name="end_time",
                type=OpenApiTypes.DATETIME,
                location=OpenApiParameter.QUERY,
                description="End of the time window (ISO 8601 format)"
            ),
        ],
        responses={200: OpenApiTypes.OBJECT} # You can define a Serializer here for better docs
    )
    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period', 'day')
        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')
        now = datetime.now()

        # ... (rest of your logic remains exactly the same)
        # The logic for filtering and date calculation doesn't change 
        # because that's standard Django/Python.
        
        # Determine the date range
        if period == 'day':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'week':
            start_date = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif period == 'custom' and start_time_str and end_time_str:
            start_date = parse_datetime(start_time_str)
            end_date = parse_datetime(end_time_str)
        else:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        returned_reservations_filter = Q(
            reservation__status=3,
            reservation__created_at__range=(start_date, end_date)
        )
        # ... and so on for your queries
        
        # Return a response so the code is valid
        approved_reservations_filter = Q(
            reservation__status=2,
            reservation__created_at__range=(start_date, end_date)
        )
        pending_reservations_filter = Q(
            reservation__status=1,
            reservation__created_at__range=(start_date, end_date)
        )
 
        read_per_user = User.objects.annotate(
            books_read=Count('reservation', filter=returned_reservations_filter)
        ).values('id', 'username')
        readings_per_user = User.objects.annotate(
            books_reading=Count('reservation', filter=Q(approved_reservations_filter))
        ).values('id', 'username')
        pending_readings_per_user = User.objects.annotate(
            books_pending=Count('reservation', filter=Q(pending_reservations_filter))
        ).values('id', 'username')
        return Response({
            'read_per_user': read_per_user,
            'readings_per_user': readings_per_user,
            'pending_readings_per_user': pending_readings_per_user,
        })
        