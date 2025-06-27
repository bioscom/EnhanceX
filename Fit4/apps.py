from django.apps import AppConfig


class FitConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Fit4'

    def ready(self):
        import Fit4.signals   # noqa: F401