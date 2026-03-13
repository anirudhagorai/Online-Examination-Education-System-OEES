from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_filed = 'django.db.models.BigAutoField'
    name = 'core'
    
    def ready(self):
        import core.signals
