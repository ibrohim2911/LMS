from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from datetime import datetime, timedelta
from django.utils.dateparse import parse_datetime
from .models import Kitob, Reservation
User = get_user_model()
class Stats(APIView):
    permission_classes = [AllowAny]
    @swagger_auto_schema(tags=['Stats'],
        manual_parameters=[
                openapi.Parameter('period', openapi.IN_QUERY, description="Time period for stats (day, week, month, custom). Default is 'day'.", type=openapi.TYPE_STRING),
                openapi.Parameter("start_time", openapi.IN_QUERY, description="Start of the time window (ISO 8601 format)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
                openapi.Parameter("end_time", openapi.IN_QUERY, description="End of the time window (ISO 8601 format)", type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME),
            ])
    def get(self, request, *args, **kwargs):
        period = request.query_params.get('period', 'day')  # Default to 'day'
        start_time_str = request.query_params.get('start_time')
        end_time_str = request.query_params.get('end_time')
        now = datetime.now()

        # 2. Determine the date range based on the period
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
            # Default to 'day' if period is invalid or custom params are missing
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now

        # 3. Create a filter for reservations that are "returned" (status=3)
        #    and fall within the specified time window.
        # The reverse relation from User to Reservation is 'reservation_set'.
        returned_reservations_filter = Q(
            reservation__status=3,
            reservation__created_at__range=(start_date, end_date)
        )
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
        