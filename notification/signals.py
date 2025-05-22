from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from notifications.models import Notification


@receiver([post_save, post_delete], sender=Notification)
def clear_notification_cache(sender, instance, **kwargs):
    user_id = instance.recipient_id
    cache.delete(f'unread_notifications:{user_id}')