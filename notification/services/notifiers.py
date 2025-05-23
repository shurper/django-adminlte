from notifications.models import Notification

from core.utils.cache import cached_user_function


@cached_user_function(timeout=60, key_prefix='unread_notifications')
def unread_notifications(request):
    if not request.user.is_authenticated:
        return {
            'unread_notifications': {},
            'unread_count': 0
        }

    qs = Notification.objects.unread().filter(recipient=request.user)
    unread = list(qs.order_by('-timestamp')[:5])
    unread_count = qs.count()

    return {
        'unread_notifications': unread,
        'unread_count': unread_count
    }