# =============================================================================
# managements/apps.py
# =============================================================================

from django.apps import AppConfig


class ManagementsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'managements'
    verbose_name = 'پنل مدیریت یکپارچه'

    def ready(self):
        import managements.signals  # noqa