from __future__ import annotations

from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from .models import ModelAttempt, ModelQualification, ModelRoute, TurnRouteBinding


class ReadOnlyRouteEvidenceAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Expose secret-free route evidence without allowing admin mutation."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False


@admin.register(ModelRoute)
class ModelRouteAdmin(ReadOnlyRouteEvidenceAdmin):
    list_display = (
        "route_key",
        "endpoint_profile",
        "requested_model",
        "adapter_version",
        "configuration_sha256",
        "disabled_at",
    )
    search_fields = ("route_key", "requested_model", "configuration_sha256")


@admin.register(ModelQualification)
class ModelQualificationAdmin(ReadOnlyRouteEvidenceAdmin):
    list_display = (
        "route",
        "schema_name",
        "observed_model",
        "schema_sha256",
        "result",
        "created_at",
    )
    list_filter = ("schema_name", "result")


@admin.register(TurnRouteBinding)
class TurnRouteBindingAdmin(ReadOnlyRouteEvidenceAdmin):
    list_display = (
        "turn",
        "role",
        "requested_model",
        "expected_model",
        "endpoint_profile",
        "adapter_version",
        "route_configuration_sha256",
        "schema_sha256",
        "created_at",
    )
    list_filter = ("role", "endpoint_profile")


@admin.register(ModelAttempt)
class ModelAttemptAdmin(ReadOnlyRouteEvidenceAdmin):
    list_display = (
        "id",
        "turn",
        "processing_job",
        "qualification",
        "attempt_number",
        "observed_model",
        "status",
        "created_at",
    )
    list_filter = ("status",)
