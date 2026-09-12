from django.contrib import admin
from django.db import models
from django.http import HttpRequest

from .models import (
    CatalogueListing,
    Clause,
    CorpusRelease,
    DocumentPage,
    DocumentVersion,
    EvidenceBundle,
    EvidenceSpan,
    ExtractionRevision,
    IngestionRun,
    Insurer,
    ModelCallAttempt,
    PlanVersion,
    PremiumObservation,
    RatingObservation,
    ReviewEvent,
    RouteConfiguration,
    RouteQualification,
    SourceBlob,
    VerifiedFact,
)


class ImmutableEvidenceAdmin(admin.ModelAdmin):  # type: ignore[type-arg]
    """Evidence revisions are created by services and never edited in place."""

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False

    def has_delete_permission(self, request: HttpRequest, obj: models.Model | None = None) -> bool:
        return False


for immutable_model in (
    SourceBlob,
    DocumentVersion,
    ExtractionRevision,
    DocumentPage,
    EvidenceSpan,
    EvidenceBundle,
    VerifiedFact,
    Clause,
    RatingObservation,
    PremiumObservation,
    CorpusRelease,
    RouteConfiguration,
    RouteQualification,
    ModelCallAttempt,
):
    admin.site.register(immutable_model, ImmutableEvidenceAdmin)

admin.site.register(
    [
        Insurer,
        CatalogueListing,
        PlanVersion,
        ReviewEvent,
        IngestionRun,
    ]
)
