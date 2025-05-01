import os

from celery import Celery
from django.conf import settings
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "uc_back.settings")

app = Celery("uc_back")
#   should have a `CELERY_` prefix.
app.conf.enable_utc = False
app.conf.update(timezone="Asia/Dhaka")
app.config_from_object(settings, namespace="CELERY")

# Celery beat configuration
app.conf.beat_schedule = {
    "send_trip_notifications": {
        "task": "trip.tasks.send_notification_before_trip_start",
        "schedule": crontab(minute="*/4"),  # Run every 30 minutes
        "args": (),
    },
}

# Load task modules from all registered Django apps.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self): 
    print(f"Request: {self.request!r}")
