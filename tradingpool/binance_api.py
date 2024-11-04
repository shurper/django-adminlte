from binance.client import Client
from django.conf import settings

client = Client(settings.BINANCE_API_KEY, settings.BINANCE_API_SECRET)

def get_binance_data(symbol='BTCUSDT', interval='1m', limit=50):
    """Получаем данные с Binance"""
    try:
        candles = client.get_klines(symbol=symbol, interval=interval, limit=limit)
        formatted_candles = [
            {
                'time': candle[0],
                'open': float(candle[1]),
                'high': float(candle[2]),
                'low': float(candle[3]),
                'close': float(candle[4])
            }
            for candle in candles
        ]
        return formatted_candles
    except Exception as e:
        print(f"Ошибка получения данных с Binance: {e}")
        return []
