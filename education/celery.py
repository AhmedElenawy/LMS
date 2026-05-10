import os

from celery import Celery
# define how to access app
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'education.settings')
# make an instant app
app = Celery('education')
# if we define setting it will start with CELERY
app.config_from_object('django.conf:settings', namespace='CELERY')
# auto descover tasks in tasks.py that have decorator shared_task or @app.task
app.autodiscover_tasks()