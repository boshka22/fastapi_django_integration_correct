from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Counter, Histogram, Gauge, Summary

import logging
from urllib.parse import urlparse
import time

logger = logging.getLogger(__name__)

# Метрики Prometheus
REQUEST_COUNTER = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'country']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

ACTIVE_REQUESTS = Gauge(
    'http_active_requests',
    'Active HTTP requests'
)


class AdvancedMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        try:
            ACTIVE_REQUESTS.inc()
            start_time = time.time()

            # Упрощаем определение страны
            country = 'local' if request.client.host in ('127.0.0.1', 'localhost') else 'unknown'

            response = await call_next(request)

            REQUEST_COUNTER.labels(
                method=request.method,
                endpoint=request.url.path,
                status_code=response.status_code,
                country=country
            ).inc()

            REQUEST_LATENCY.labels(
                method=request.method,
                endpoint=request.url.path
            ).observe(time.time() - start_time)

            return response
        finally:
            ACTIVE_REQUESTS.dec()

    async def get_country_from_ip(self, ip):
        if ip in ('127.0.0.1', 'localhost'):
            return 'local'

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f'http://ip-api.com/json/{ip}?fields=country',
                    timeout=1.0
                )
                if response.status_code == 200:
                    return response.json().get('country', 'unknown')
        except:
            pass
        return 'unknown'