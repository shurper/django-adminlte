# routing.py

from django.urls import path
from tradingpool import consumers

websocket_urlpatterns = [
    path('ws/candles/', consumers.CandleConsumer.as_asgi()),
]
