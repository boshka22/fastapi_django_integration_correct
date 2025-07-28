from django.utils.deprecation import MiddlewareMixin
from prometheus_client import Counter, Histogram
import time
import geoip2.database
import socket

geoip_reader = geoip2.database.Reader('GeoLite2-City.mmdb')

DJANGO_REQUEST_COUNTER = Counter(
    'django_requests_total',
    'Total Django requests',
    ['method', 'view', 'status_code', 'country', 'city']
)

DJANGO_LATENCY = Histogram(
    'django_request_duration_seconds',
    'Django request duration in seconds',
    ['method', 'view']
)


class DjangoMetricsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request._start_time = time.time()

        # Геолокация
        client_ip = self.get_client_ip(request)
        try:
            geo_data = geoip_reader.city(client_ip)
            request._country = geo_data.country.name or 'unknown'
            request._city = geo_data.city.name or 'unknown'
        except:
            request._country = request._city = 'unknown'

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip or '127.0.0.1'

    def process_response(self, request, response):
        duration = time.time() - getattr(request, '_start_time', 0)

        view_name = getattr(getattr(request, 'resolver_match', None), 'view_name', 'unknown')

        DJANGO_REQUEST_COUNTER.labels(
            method=request.method,
            view=view_name,
            status_code=response.status_code,
            country=getattr(request, '_country', 'unknown'),
            city=getattr(request, '_city', 'unknown')
        ).inc()

        DJANGO_LATENCY.labels(
            method=request.method,
            view=view_name
        ).observe(duration)

        return response