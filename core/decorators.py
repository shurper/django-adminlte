from django.http import HttpResponseForbidden
from functools import wraps

def localhost_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        allowed_ips = ['127.0.0.1', '::1']  # IPv4 и IPv6 для localhost
        if request.META['REMOTE_ADDR'] not in allowed_ips:
            return HttpResponseForbidden("Access Denied")
        return view_func(request, *args, **kwargs)
    return _wrapped_view