# Celery configuration for JoKeR_Finance

from celery import Celery
from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    'joker_finance',
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=['app.tasks']
)

# Celery settings
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max
    worker_prefetch_multiplier=1,
)


@celery_app.on_after_configure.connect
def setup_handler(sender, **kwargs):
    """Log configuration after setup"""
    sender.log_warning('Celery configured with broker: %s', sender.conf.broker_url)
