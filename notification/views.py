from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from notifications.models import Notification


@login_required
def all_notifications(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    return render(request, 'notifications/all.html', {'notifications': notifications})
