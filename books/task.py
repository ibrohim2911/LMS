from .models import Reservation
from django.utils import timezone
from celery import shared_task
from datetime import timedelta


@shared_task
def check_reservation_status():
    """
    Periodic task to check for overdue books and expired approvals.
    """
    now = timezone.now()
    
    # 1. Handle Overdue Books (Given -> Not Returned)
    # If the book was given and the return deadline (reserved_until) has passed.
    overdue_reservations = Reservation.objects.filter(
        status='given', 
        reserved_until__lt=now
    )
    for reservation in overdue_reservations:
        reservation.status = 'not_returned'
        reservation.save()

    # 2. Handle Expired Approvals (Approved -> Cancelled/Deleted)
    # If a user doesn't pick up the book within 24 hours of approval.
    pickup_deadline = now - timedelta(hours=24)
    expired_reservations = Reservation.objects.filter(
        status='approved',
        approved_at__lt=pickup_deadline
    )
    # Deleting the reservation will trigger the post_delete signal in models.py,
    # which restores book quantity and updates availability.
    expired_reservations.delete()