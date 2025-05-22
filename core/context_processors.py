from notification.services.notifiers import unread_notifications

def notifications_context(request):
    return unread_notifications(request)


def segment_processor(request):
    return {
        'segment': request.resolver_match.url_name if request.resolver_match else ''
    }