
import ipaddress
from functools import wraps
from hashlib import md5

from django.core.cache import cache
from django.http import HttpResponseForbidden


def localhost_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        allowed_networks = [
            '127.0.0.1',  # IPv4 localhost
            '::1',  # IPv6 localhost
            '172.16.0.0/12',  # Docker и другие частные диапазоны
            '192.168.0.0/16',  # Частная сеть
            '10.0.0.0/8',  # Частная сеть
        ]

        remote_addr = request.META.get('REMOTE_ADDR')

        # Проверяем, попадает ли IP-адрес в один из разрешенных диапазонов
        if not any(ipaddress.ip_address(remote_addr) in ipaddress.ip_network(network) for network in allowed_networks):
            return HttpResponseForbidden(f"Access Denied for {remote_addr}")

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def cache_for_user(timeout=60, key_prefix='cached'):
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return func(request, *args, **kwargs)

            key_data = f'{key_prefix}:{request.user.id}:{func.__name__}'
            cache_key = md5(key_data.encode()).hexdigest()

            result = cache.get(cache_key)
            if result is None:
                result = func(request, *args, **kwargs)
                cache.set(cache_key, result, timeout)
            return result
        return wrapper
    return decorator