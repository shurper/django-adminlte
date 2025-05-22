from notification.services.notifiers import unread_notifications

def notifications_context(request):
    return unread_notifications(request)
