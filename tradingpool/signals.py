from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import OrderBook, SymbolDirectory

@receiver(pre_save, sender=OrderBook)
def set_symbol_and_symbol_type(sender, instance, **kwargs):
    try:
        symbol_entry = SymbolDirectory.objects.get(address=instance.address)
        instance.symbol = symbol_entry.symbol
        instance.symbol_type = symbol_entry.symbol_type
    except SymbolDirectory.DoesNotExist:
        # Логика на случай, если запись для адреса не найдена
        instance.symbol = "Unknown"
        instance.symbol_type = "Unknown"