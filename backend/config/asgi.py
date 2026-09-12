import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

from django.core.asgi import get_asgi_application

from .lifecycle import LifespanApplication

application = LifespanApplication(get_asgi_application())
