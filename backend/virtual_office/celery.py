import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "virtual_office.settings")
app = Celery("virtual_office")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()