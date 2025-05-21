import hashlib
from django.core.cache import cache
from notifications.signals import notify
import logging

logger = logging.getLogger(__name__)

def notify_wb(
    sender,
    recipient,
    verb: str,
    description: str,
    extra_data: dict | None = None,
    freq_hours: int = 4,
) -> None:
    try:
        if extra_data is None:
            extra_data = {}

        data = {'source_app': 'wildberries', **extra_data}

        raw_string = f'{sender.id}_{recipient.id}_{verb}_{description}_{freq_hours}_{sorted(data.items())}'
        cache_key = f'notify:wb_error:{hashlib.md5(raw_string.encode()).hexdigest()}'

        if cache.get(cache_key):
            return

        notify.send(
            sender=sender,
            recipient=recipient,
            verb=verb,
            description=description,
            data=data
        )

        cache.set(cache_key, True, timeout=freq_hours * 60 * 60)

        logger.info(f'Notification created: {raw_string}')
    except Exception as e:
        logger.error(f'Failed to send notification: {e}', exc_info=True)

