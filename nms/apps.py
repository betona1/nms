from django.apps import AppConfig


class NmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'nms'
    verbose_name = 'NMS 네트워크 모니터링'

    def ready(self):
        from .tasks import start_scheduler
        start_scheduler()
