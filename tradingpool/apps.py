from django.apps import AppConfig


class TradingpoolConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'tradingpool'

    def ready(self):
        import tradingpool.signals
