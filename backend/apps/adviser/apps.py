from django.apps import AppConfig


class AdviserConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.adviser"

    def ready(self) -> None:
        from . import providers  # noqa: F401  (registers the OmniRoute settings check)
