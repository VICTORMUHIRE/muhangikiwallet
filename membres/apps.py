from django.apps import AppConfig
import os

class MembresConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'membres'

    # def ready(self):
    #     from .scheduler import start_scheduler
    #     start_scheduler()

    def ready(self):
        if os.environ.get('RUN_MAIN') == 'true':  # seulement le thread principal (utile en mode dev)
            from .scheduler import start_scheduler
            start_scheduler()

