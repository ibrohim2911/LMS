from .models import Reservation
from django.utils import timezone
from celery import shared_task
from datetime import timedelta
from users.task import send_notification

@shared_task
def check_reservation_status():
    """
    Periodic task to check for overdue books, upcoming deadlines, and expired approvals.
    """
    now = timezone.now()
    print(f"Running reservation status check at {now}")
    # 1. Handle Overdue Books (Given / Not Returned)
    # If deadline passed, status should be 'not_returned'
    # Send notification is overdue
    overdue_reservations = Reservation.objects.filter(
        status='given', 
        reserved_until__lt=now
    )
    for reservation in overdue_reservations:
        reservation.status = 'not_returned'
        reservation.save()
        send_notification.delay(
            reservation.user.id, 
            f"Your book '{reservation.book.name}' is overdue. Please return it immediately.",
            "Book Overdue"
        )

    # 2. Warning Notification (1 day before deadline)
    # Send warning if due date is within 24 hours from now
    warning_buffer_start = now
    warning_buffer_end = now + timedelta(days=1)
    
    warning_reservations = Reservation.objects.filter(
        status='given',
        reserved_until__gt=warning_buffer_start,
        reserved_until__lt=warning_buffer_end
    )
    
    for reservation in warning_reservations:
        send_notification.delay(
            reservation.user.id,
            f"The book '{reservation.book.name}' is due tomorrow. Please return it on time.",
            "Return Reminder"
        )
        
    # 3. Handle Expired Approvals (Approved -> Cancelled/Deleted)
    # If a user doesn't pick up the book within 24 hours of approval.
    pickup_deadline = now - timedelta(hours=24)
    expired_reservations = Reservation.objects.filter(
        status='approved',
        approved_at__lt=pickup_deadline,
    )
    
    for reservation in expired_reservations:
        send_notification.delay(
            reservation.user.id,
            f"Your reservation for '{reservation.book.name}' has been cancelled because you did not pick it up within 24 hours.",
            "Reservation Cancelled"
        )
        # Deleting trigger post_delete, restores quantity
        reservation.delete()