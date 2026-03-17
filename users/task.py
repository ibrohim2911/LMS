from celery import shared_task
from .models import Notification, User

@shared_task
def send_notification(user_id, message, title="Notification"):
    try:
        user = User.objects.get(id=user_id)
        Notification.objects.create(user=user, message=message, title=title)
        return f"Notification sent to {user.username}"
    except User.DoesNotExist:
        return "User not found"