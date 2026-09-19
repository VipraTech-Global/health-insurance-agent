from apps.adviser.streaming import stream_turn
from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.adviser.urls")),
    path("api/v1/conversations/<uuid:conversation_id>/turns/", stream_turn, name="stream-turn"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
if settings.COVERGUIDE_V2_ENABLED:
    urlpatterns.insert(3, path("api/v2/", include("apps.adviser_v2.urls")))
