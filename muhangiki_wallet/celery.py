import os
from celery import Celery

# Définir le nom du projet Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'muhangiki_wallet.settings')

app = Celery('muhangiki_wallet')

# Charger les configurations Celery depuis le fichier Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Découvrir automatiquement les tâches dans les applications Django
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')