"""
Celery configuration untuk PPDB System.
Digunakan untuk:
- Send email notification async
- Process payment status check
- Generate reports
"""
import os
from celery import Celery
from decouple import config

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('ppdb_system')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery Beat Schedule (periodic tasks)
app.conf.beat_schedule = {
    'expire-unpaid-payments': {
        'task': 'apps.payments.tasks.expire_unpaid_payments',
        'schedule': 3600.0,  # Every hour
    },
}

app.conf.timezone = 'Asia/Jakarta'