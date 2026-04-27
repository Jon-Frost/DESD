from celery import shared_task
from django.contrib.auth.models import User
from .models import Notification


# GENERIC NOTIFICATION TASK - CREATES A NOTIFICATION ROW FOR THE GIVEN USER
@shared_task
def create_notification(user_id, message):
    user = User.objects.get(id=user_id)
    Notification.objects.create(user=user, message=message)
