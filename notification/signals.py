from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from notifications.models import Notification
from .services.notifiers import unread_notifications


@receiver([post_save, post_delete], sender=Notification)
def clear_notification_cache(sender, instance, **kwargs):
    unread_notifications.invalidate(instance.recipient_id)
