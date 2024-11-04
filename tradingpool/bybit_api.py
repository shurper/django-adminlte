# bybit_api.py
#from pybit import HTTP
import threading

import ccxt
from pybit.unified_trading import HTTP
from pybit.unified_trading import WebSocket
import asyncio
import websocket


# Создание клиента Bybit
client = HTTP()

# def get_bybit_data(symbol="BTCUSDT"):
#     try:
#         # Пример получения свечей (OHLCV)
#         data = client.get_kline(symbol=symbol, interval="1", limit=200)
#         return data
#     except Exception as e:
#         print(f"Ошибка при получении данных с Bybit: {e}")
#         return None


def get_bybit_data(symbol="BTCUSDT", interval="1", limit=200, last_timestamp=None):
    bybit = ccxt.bybit({
        'enableRateLimit': True,  # Включение ограничения запросов
    })

    # Словарь для сопоставления интервалов между форматами ccxt и Bybit
    timeframes = {
        '1': '1',
        '5': '5',
        '15': '15',
        '60': '60',
        '240': '240',
        '360': '360',
        '720': '720',
        'D': 'D',
        'M': 'M',
        'W': 'W',

    }

    try:
        if last_timestamp is None:
            # Если last_timestamp не задан, получаем последние limit свечей
            ohlcv_data = bybit.fetch_ohlcv(symbol, timeframe=timeframes.get(interval, '1m'), limit=limit)
        else:
            # Запрашиваем новые свечи, начиная с последнего временного штампа
            since = last_timestamp * 1000  # Переводим временной штамп в миллисекунды
            ohlcv_data = bybit.fetch_ohlcv(symbol, timeframe=timeframes.get(interval, '1m'), since=since, limit=limit)

        return ohlcv_data

    except Exception as e:
        print(f"Ошибка при получении данных с Bybit: {e}")
        return {
            'retCode': 1,  # Ошибка
            'retMsg': str(e)
        }


ws_client = None
subscribed_topics = set()

def ensure_event_loop():
    try:
        print(f"пытаемся получить луп")
        loop = asyncio.get_running_loop()
    except RuntimeError:  # Если нет активного цикла событий
        print(f"нет активного лупа")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


async def handle_message_async(message, callback):
    print(f"Обработка сообщения: {message}")
    # Логика обработки сообщения
    # Вызов колбэка
    await callback(message)


def handle_message_sync(message, callback):
    """Синхронный обработчик сообщения для вызова в потоке"""
    #print(f"Получено сообщение: {message}")
    loop = ensure_event_loop()
    asyncio.run_coroutine_threadsafe(handle_message_async(message, callback), loop)


async def start_bybit_stream(symbol="BTCUSDT", interval="1", callback=None):
    #ensure_event_loop()
    global ws_client

    topic = f"kline.{interval}.{symbol}"

    if topic in subscribed_topics:
        print(f"Вы уже подписаны на эту тему: {topic}")
        return

    if ws_client is None:
        ws_client = WebSocket(channel_type="linear")

    # def handle_message(message):
    #     # Используем синхронный обработчик, чтобы передать результат в асинхронную часть
    #     threading.Thread(target=handle_message_sync, args=(message, callback)).start()


    def handle_message(message):
        print(f"Сырой ответ WebSocket: {message}")  # Сырой ответ
        threading.Thread(target=handle_message_sync, args=(message, callback)).start()

    try:
        ws_client.kline_stream(
            interval=int(interval),
            symbol=symbol,
            callback=callback
        )
        subscribed_topics.add(topic)
        print(f"Подписка на {topic} успешно выполнена")
    except websocket.WebSocketConnectionClosedException as e:
        print(f"Соединение закрыто: {e}. Переподключение...")
        await asyncio.sleep(5)
        await start_bybit_stream(symbol, interval, callback)
    except Exception as e:
        print(f"Ошибка: {e}")

async def stop_bybit_stream(symbol, interval):
    global ws_client
    topic = f"kline.{interval}.{symbol}"

    if ws_client:
        ws_client.exit()
        ws_client = None

    if topic in subscribed_topics:
        subscribed_topics.remove(topic)
        print(f"Подписка на {topic} отменена")