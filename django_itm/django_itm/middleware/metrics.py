from django.utils.deprecation import MiddlewareMixin
from prometheus_client import Counter, Histogram
import time
import requests
import socket

DJANGO_REQUEST_COUNTER = Counter(
    'django_requests_total',
    'Total Django requests',
    ['method', 'view', 'status_code', 'country']
)

DJANGO_LATENCY = Histogram(
    'django_request_duration_seconds',
    'Django request duration in seconds',
    ['method', 'view']
)


class DjangoMetricsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()
        request._country = self.get_country_from_ip(self.get_client_ip(request))

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1'

    def get_country_from_ip(self, ip):
        """Определяем страну по IP с помощью бесплатного API"""
        if ip in ('127.0.0.1', 'localhost'):
            return 'local'

        try:
            response = requests.get(f'http://ip-api.com/json/{ip}?fields=country', timeout=1)
            if response.status_code == 200:
                return response.json().get('country', 'unknown')
        except:
            pass
        return 'unknown'

    def process_response(self, request, response):
        duration = time.time() - getattr(request, '_start_time', 0)
        view_name = getattr(getattr(request, 'resolver_match', None), 'view_name', 'unknown')

        DJANGO_REQUEST_COUNTER.labels(
            method=request.method,
            view=view_name,
            status_code=response.status_code,
            country=getattr(request, '_country', 'unknown')
        ).inc()

        DJANGO_LATENCY.labels(
            method=request.method,
            view=view_name
        ).observe(duration)

        return response