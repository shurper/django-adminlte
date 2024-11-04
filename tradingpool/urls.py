from django.urls import path
from . import views
from .views import orderbook_create_view

urlpatterns = [
    path('', views.index, name='index'),
    path('api/candles/<str:symbol>/<str:interval>/<int:start>/', views.bybit_candles, name='bybit_candles'),
    path('api/save_orderbook/', orderbook_create_view, name='orderbook-create'),
]
