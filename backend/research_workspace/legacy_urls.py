"""Historical API regression harness; never mounted by the local demo server."""

from config.urls import urlpatterns as current_urls
from django.urls import include, path

urlpatterns = [*current_urls, path("api/v2/", include("apps.adviser_v2.urls"))]
