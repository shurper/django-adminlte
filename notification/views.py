from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, redirect
from notifications.models import Notification


@login_required
def all_notifications(request):
    notifications_qs = Notification.objects.filter(recipient=request.user).order_by('-timestamp')
    paginator = Paginator(notifications_qs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'notifications/all.html', {'page_obj': page_obj})


@login_required
def clear_notifications(request):
    if request.method == 'POST':
        Notification.objects.filter(recipient=request.user).delete()
    return redirect('notifications_all')