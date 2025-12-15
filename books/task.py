from .models import Reservation
from django.utils import timezone
from celery import shared_task
from datetime import timedelta, date


@shared_task
def warning():
    now = timezone.now()
    warning_date = now + timedelta(days=1)
    reservations = Reservation.objects.filter(status=2,  place__lte=warning_date.day)
    for reservation in reservations:
        reservation.status = 4  # Mark as should have returned
        reservation.save()