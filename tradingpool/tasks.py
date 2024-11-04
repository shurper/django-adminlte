from celery import shared_task


@shared_task
def check_and_update_unknown_symbols():
    from django.core.mail import send_mail
    from django.contrib.auth.models import User
    from .models import OrderBook, SymbolDirectory
    # Шаг 1: Найти все записи с symbol="Unknown" и symbol_type="Unknown"
    unknown_records = OrderBook.objects.filter(symbol="Unknown", symbol_type="Unknown")

    if unknown_records.exists():
        # Шаг 2: Попытаться обновить записи, если данные для address уже добавлены в SymbolDirectory
        updated_count = 0
        for record in unknown_records:
            try:
                symbol_entry = SymbolDirectory.objects.get(address=record.address)
                record.symbol = symbol_entry.symbol
                record.symbol_type = symbol_entry.symbol_type
                record.save()
                updated_count += 1
            except SymbolDirectory.DoesNotExist:
                pass  # Если данных нет, пропустить запись

        # Шаг 3: Если обновить не удалось (т.е. остались записи с "Unknown"), отправить уведомление
        if updated_count < unknown_records.count():
            # Получить email-адреса всех суперпользователей
            superuser_emails = User.objects.filter(is_superuser=True).values_list('email', flat=True)
            if superuser_emails:
                message = (
                    f"Найдены записи в OrderBook с неизвестными символами (symbol='Unknown').\n"
                    f"Пожалуйста, добавьте соответствующие записи в SymbolDirectory.\n\n"
                    f"Количество записей с неизвестными символами: {unknown_records.count()}\n\n"
                    "Адреса с неизвестными символами:\n" +
                    "\n".join([f"{record.address}" for record in unknown_records])
                )

                send_mail(
                    subject="Неизвестные символы в OrderBook",
                    message=message,
                    from_email=None,  # Использует DEFAULT_FROM_EMAIL из настроек
                    recipient_list=superuser_emails,
                    fail_silently=False,
                )
