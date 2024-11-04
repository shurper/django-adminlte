# consumers.py

import json
from channels.generic.websocket import AsyncWebsocketConsumer
import asyncio
from pybit.unified_trading import WebSocket


class SubscriptionManager:
    def __init__(self):
        self.subscriptions = {}
        self.ws_client = None
        self.loop = None  # Инициализируем позже

    def _format_topic(self, symbol, timeframe):
        # Унифицированный формат топика
        return f"kline.{timeframe}.{symbol}"

    async def start_subscription(self, symbol, timeframe, callback):
        # Получаем текущий цикл событий при первом использовании
        if not self.loop:
            self.loop = asyncio.get_running_loop()

        topic = self._format_topic(symbol, timeframe)

        if topic not in self.subscriptions:
            if not self.ws_client:
                self.ws_client = WebSocket(channel_type="linear", testnet=False)

            # Создаём задачу для стрима данных
            task = asyncio.create_task(self._stream_candles(symbol, timeframe))
            self.subscriptions[topic] = {"clients": set(), "task": task}

        self.subscriptions[topic]["clients"].add(callback)

    async def stop_subscription(self, symbol, timeframe, callback):
        topic = self._format_topic(symbol, timeframe)

        if topic in self.subscriptions:
            self.subscriptions[topic]["clients"].remove(callback)

            if not self.subscriptions[topic]["clients"]:
                self.subscriptions[topic]["task"].cancel()
                del self.subscriptions[topic]

        #Внимание! На момент разработки отсутствует функционал отписки, поэтому после первой подписки на топик поставщик
        # будет подавать данные даже если нет потребителя. Нужно проверить влияние на производительность.


    async def _stream_candles(self, symbol, timeframe):
        topic = self._format_topic(symbol, timeframe)

        try:
            def on_data(candle_data):
                #print(f"Получены данные для {topic}")  # Логируем полученные данные
                # Выполняем обработку данных в основном цикле событий
                asyncio.run_coroutine_threadsafe(self._handle_data(topic, candle_data), self.loop)

            # Подписываемся на поток API
            print(f"Подключение к потоку для {topic}")
            self.ws_client.kline_stream(
                interval=int(timeframe),
                symbol=symbol,
                callback=on_data
            )
            print(f"{topic} подключен -------")
        except Exception as e:
            print(f"Ошибка подписки на {topic}: {e}")


    async def _handle_data(self, topic, candle_data):
        # Внимание! На момент разработки отсутствует функционал отписки, поэтому после первой подписки на топик поставщик
        # будет подавать данные даже если нет потребителя. Нужно проверить влияние на производительность.
        #print(f"_handle_data для {topic}")

        # Рассылаем данные всем активным клиентам
        for client_callback in self.subscriptions[topic]["clients"]:
            #print(f"Отправляем данные клиенту: {client_callback}")
            await client_callback(candle_data)




# Глобальный экземпляр менеджера подписок
subscription_manager = SubscriptionManager()


class CandleConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.symbol = None
        self.timeframe = None

    async def disconnect(self, close_code):
        if self.symbol and self.timeframe:
            await subscription_manager.stop_subscription(self.symbol, self.timeframe, self.send_candle_data)

    async def receive(self, text_data):
        data = json.loads(text_data)
        symbol = "BTCUSDT"
        timeframe = data.get("timeframe")

        #print(f"Полученные данные: {data}")

        if not symbol or not timeframe:
            print("Ошибка: символ или таймфрейм не указаны.")
            return

        if symbol != self.symbol or timeframe != self.timeframe:
            # Остановка старой подписки, если изменился символ или таймфрейм
            if self.symbol and self.timeframe:
                await subscription_manager.stop_subscription(self.symbol, self.timeframe, self.send_candle_data)

            # Обновляем текущие символ и таймфрейм
            self.symbol = symbol
            self.timeframe = timeframe

            # Запускаем новую подписку
            await subscription_manager.start_subscription(self.symbol, self.timeframe, self.send_candle_data)

    async def send_candle_data(self, candle_data):
        #print("Отправка данных клиенту:", candle_data)
        await self.send(text_data=json.dumps({"candles": candle_data}))