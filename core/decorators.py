from django.http import HttpResponseForbidden
from functools import wraps

def localhost_only(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        allowed_ips = ['127.0.0.1', '::1']  # IPv4 и IPv6 для localhost
        client_ip = request.META.get('REMOTE_ADDR')

        if client_ip not in allowed_ips:
            return HttpResponseForbidden(f"Access Denied for {client_ip}")

        return view_func(request, *args, **kwargs)
    return _wrapped_view