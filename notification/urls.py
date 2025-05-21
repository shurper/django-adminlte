# wildberries/urls.py
from django.urls import path

from notification.views import all_notifications

urlpatterns = [
    path('notifications/', all_notifications, name='notifications_all'),
]
