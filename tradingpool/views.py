import logging

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status

from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework.views import APIView

from core.decorators import localhost_only
from .binance_api import get_binance_data
from .bybit_api import get_bybit_data
from .serializers import OrderBookSerializer

logger = logging.getLogger(__name__)


@login_required
@api_view(['GET'])
def bybit_candles(request, symbol='BTCUSDT', interval=None, start=None):
    data = get_bybit_data(symbol=symbol, interval=interval, last_timestamp=start)
    return Response(data)


@login_required
def index(request):
    from pybit.unified_trading import WebSocket
    from time import sleep

    # ws = WebSocket(
    #     testnet=False,
    #     channel_type="spot",
    # )
    #
    # def handle_message(message):
    #     # print(f"{message}")
    #
    #     # Извлекаем цену последнего бида и первого аска
    #     best_bid_price = float(message["data"]["b"][-1][0])  # Последняя цена покупки (bid)
    #     best_ask_price = float(message["data"]["a"][-1][0])  # Первая цена продажи (ask)
    #
    #     # Выводим нужные данные и разницу между ними
    #     print(f"{message['type']}")
    #     print(f"{best_ask_price} - {best_bid_price} = {best_ask_price - best_bid_price}")
    #
    # ws.orderbook_stream(
    #     depth=200,
    #     symbol="BTCUSDT",
    #     callback=handle_message
    # )

    return render(request, 'tradingpool/index.html')

@localhost_only
@csrf_exempt
@api_view(['POST'])
def orderbook_create_view(request):
    serializer = OrderBookSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)