from hashlib import md5
from django.core.cache import cache

class CachedUserFunction:
    def __init__(self, func, timeout=60, key_prefix='cached'):
        self.func = func
        self.timeout = timeout
        self.key_prefix = key_prefix
        self.__name__ = func.__name__

    def make_key(self, user_id):
        key_data = f'{self.key_prefix}:{user_id}:{self.func.__name__}'
        return md5(key_data.encode()).hexdigest()

    def invalidate(self, user_id):

        cache_key = self.make_key(user_id)
        print(f"DELETE CACHE KEY: {cache_key}")
        cache.delete(cache_key)

    def __call__(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.func(request, *args, **kwargs)

        user_id = request.user.id
        cache_key = self.make_key(user_id)

        result = cache.get(cache_key)
        if result is None:
            result = self.func(request, *args, **kwargs)
            cache.set(cache_key, result, self.timeout)
        return result


def cached_user_function(timeout=60, key_prefix='cached'):
    def decorator(func):
        return CachedUserFunction(func, timeout=timeout, key_prefix=key_prefix)
    return decorator