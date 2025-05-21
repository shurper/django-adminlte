from notifications.models import Notification

def unread_notifications(request):
    if request.user.is_authenticated:
        unread = request.user.notifications.unread()
        return {
            'unread_notifications': unread,
            'unread_count': unread.count()
        }
    return {}