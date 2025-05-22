from notifications.models import Notification

from core.decorators import cache_for_user

@cache_for_user(timeout=60, key_prefix='unread_notifications')
def unread_notifications(request):
    if not request.user.is_authenticated:
        return {}

    qs = Notification.objects.unread().filter(recipient=request.user)
    unread = list(qs.order_by('-timestamp')[:5])
    unread_count = qs.count()

    return {
        'unread_notifications': unread,
        'unread_count': unread_count
    }
