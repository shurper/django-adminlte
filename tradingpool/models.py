from django.db import models
from django.utils import timezone


class OrderBook(models.Model):
    exchange = models.CharField(max_length=255, null=True )
    address = models.CharField(max_length=512, null=True)
    symbol = models.CharField(max_length=32, null=True)
    symbol_type = models.CharField(max_length=255, null=True)
    start = models.BigIntegerField()
    end = models.BigIntegerField()
    bid = models.JSONField()
    ask = models.JSONField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.exchange} | {self.start}-{self.end}"


# see signals.py
class SymbolDirectory(models.Model):
    address = models.CharField(max_length=512, unique=True)
    symbol = models.CharField(max_length=32)
    symbol_type = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.symbol} ({self.symbol_type})"

