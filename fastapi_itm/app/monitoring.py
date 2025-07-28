# monitoring.py (упрощенная версия)
from prometheus_client import make_asgi_app

def setup_metrics(app):
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    return app