from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class UUIDModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class Insurer(UUIDModel):
    name = models.CharField(max_length=200, unique=True)
    aliases = models.JSONField(default=list)
    official_domains = models.JSONField(default=list)


class CatalogueListing(UUIDModel):
    class Status(models.TextChoices):
        DISCOVERED = "discovered"
        DOWNLOADED = "downloaded"
        PARSED = "parsed"
        AWAITING_REVIEW = "awaiting_review"
        ACTIVE = "active"
        SUPERSEDED = "superseded"
        UNAVAILABLE = "unavailable"

    ditto_path = models.CharField(max_length=500, unique=True)
    displayed_name = models.CharField(max_length=250)
    insurer = models.ForeignKey(Insurer, null=True, on_delete=models.PROTECT)
    status = models.CharField(max_length=30, choices=Status, default=Status.DISCOVERED)
    status_reason = models.TextField(blank=True)
    last_observed_at = models.DateTimeField()


class PlanVersion(UUIDModel):
    insurer = models.ForeignKey(Insurer, on_delete=models.PROTECT)
    uin = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=250)
    variant = models.CharField(max_length=200, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    available_for_new_purchase = models.BooleanField(null=True)
    review_state = models.CharField(max_length=30, default="pending")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["insurer", "uin", "variant", "effective_from"],
                name="unique_plan_identity",
                nulls_distinct=False,
            )
        ]


class SourceLocator(UUIDModel):
    url = models.URLField(max_length=1000)
    source_organisation = models.CharField(max_length=250)
    expected_document_type = models.CharField(max_length=100)


class SourceObservation(UUIDModel):
    locator = models.ForeignKey(SourceLocator, on_delete=models.PROTECT)
    fetched_at = models.DateTimeField()
    status_code = models.PositiveSmallIntegerField(null=True)
    final_url = models.URLField(max_length=1000, blank=True)
    content_sha256 = models.CharField(max_length=64, blank=True)
    available = models.BooleanField(default=False)
    error_code = models.CharField(max_length=100, blank=True)


class SourceBlob(UUIDModel):
    sha256 = models.CharField(max_length=64, unique=True)
    stored_path = models.CharField(max_length=500, unique=True)
    byte_size = models.PositiveBigIntegerField()
    media_type = models.CharField(max_length=100)


class DocumentVersion(UUIDModel):
    blob = models.ForeignKey(SourceBlob, on_delete=models.PROTECT)
    document_type = models.CharField(max_length=100)
    language = models.CharField(max_length=20, default="en")
    identity = models.CharField(max_length=300)
    effective_from = models.DateField(null=True, blank=True)


class PlanDocumentAssociation(UUIDModel):
    plan_version = models.ForeignKey(PlanVersion, on_delete=models.PROTECT)
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.PROTECT)
    role = models.CharField(max_length=100)
    applicability = models.JSONField(default=dict)
    reviewed = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["plan_version", "document_version", "role"],
                name="unique_plan_document_role",
            )
        ]


class ExtractionRevision(UUIDModel):
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    parser_manifest = models.JSONField(default=dict)
    artifact_sha256 = models.CharField(max_length=64)
    source_map_path = models.CharField(max_length=500)
    published = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["document_version", "revision"], name="unique_extraction_revision"
            )
        ]


class DocumentPage(UUIDModel):
    extraction_revision = models.ForeignKey(ExtractionRevision, on_delete=models.PROTECT)
    physical_index = models.PositiveIntegerField()
    printed_label = models.CharField(max_length=30, blank=True)
    width = models.DecimalField(max_digits=12, decimal_places=4)
    height = models.DecimalField(max_digits=12, decimal_places=4)
    rotation = models.SmallIntegerField(default=0)
    geometry = models.JSONField(default=dict)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["extraction_revision", "physical_index"], name="unique_extraction_page"
            )
        ]


class EvidenceSpan(UUIDModel):
    page = models.ForeignKey(DocumentPage, on_delete=models.PROTECT)
    region_id = models.CharField(max_length=100)
    start_line = models.PositiveIntegerField()
    end_line = models.PositiveIntegerField()
    source_word_ids = models.JSONField(default=list)
    quote = models.TextField()
    geometry = models.JSONField(default=list)


class EvidenceBundle(UUIDModel):
    label = models.CharField(max_length=250)
    review_state = models.CharField(max_length=30, default="pending")
    spans: models.ManyToManyField[EvidenceSpan, EvidenceBundleSpan] = models.ManyToManyField(
        EvidenceSpan, through="EvidenceBundleSpan"
    )


class EvidenceBundleSpan(models.Model):
    bundle = models.ForeignKey(EvidenceBundle, on_delete=models.CASCADE)
    span = models.ForeignKey(EvidenceSpan, on_delete=models.PROTECT)
    role = models.CharField(max_length=30, default="primary")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]
        constraints = [
            models.UniqueConstraint(fields=["bundle", "span"], name="unique_bundle_span")
        ]


class VerifiedFact(UUIDModel):
    plan_version = models.ForeignKey(PlanVersion, on_delete=models.PROTECT)
    category = models.CharField(max_length=100)
    value_type = models.CharField(max_length=30)
    value = models.JSONField()
    applicability = models.JSONField(default=dict)
    evidence_bundle = models.ForeignKey(EvidenceBundle, on_delete=models.PROTECT)
    verification_state = models.CharField(max_length=30, default="pending")
    conflict = models.BooleanField(default=False)


class Clause(UUIDModel):
    document_version = models.ForeignKey(DocumentVersion, on_delete=models.PROTECT)
    section_path = models.JSONField(default=list)
    heading = models.CharField(max_length=500, blank=True)
    evidence_bundles = models.ManyToManyField(EvidenceBundle)


class RatingObservation(UUIDModel):
    plan_version = models.ForeignKey(PlanVersion, on_delete=models.PROTECT)
    rating = models.DecimalField(max_digits=6, decimal_places=3)
    scale = models.DecimalField(max_digits=6, decimal_places=3)
    observed_at = models.DateTimeField()
    evidence_bundle = models.ForeignKey(EvidenceBundle, on_delete=models.PROTECT)


class PremiumObservation(UUIDModel):
    plan_version = models.ForeignKey(PlanVersion, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="INR")
    assumptions = models.JSONField(default=dict)
    tax_basis = models.CharField(max_length=100, blank=True)
    observed_at = models.DateTimeField()
    evidence_bundle = models.ForeignKey(EvidenceBundle, on_delete=models.PROTECT)


class ReviewEvent(UUIDModel):
    object_type = models.CharField(max_length=100)
    object_id = models.UUIDField()
    expected_revision = models.CharField(max_length=100)
    decision = models.CharField(max_length=30)
    reason = models.TextField()
    reviewer = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)


class IngestionRun(UUIDModel):
    stage = models.CharField(max_length=50)
    state = models.CharField(max_length=30)
    inputs = models.JSONField(default=dict)
    outputs = models.JSONField(default=dict)
    errors = models.JSONField(default=list)
    retry_count = models.PositiveSmallIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)


class CorpusRelease(UUIDModel):
    name = models.CharField(max_length=200, unique=True)
    manifest = models.JSONField(default=dict)
    activated_at = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["is_current"],
                condition=Q(is_current=True),
                name="one_current_corpus_release",
            )
        ]


class Conversation(UUIDModel):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, default="New conversation")
    updated_at = models.DateTimeField(auto_now=True)
    current_profile = models.ForeignKey(
        "ProfileRevision",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="current_for",
    )
    active_attempt = models.OneToOneField(
        "TurnAttempt",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="active_for_conversation",
    )


class ProfileRevision(UUIDModel):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="profiles"
    )
    revision = models.PositiveIntegerField()
    data = models.JSONField(default=dict)
    field_provenance = models.JSONField(default=dict)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "revision"], name="unique_profile_revision"
            )
        ]


class Message(UUIDModel):
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=[("user", "User"), ("assistant", "Assistant")])
    content = models.TextField()
    origin = models.CharField(max_length=30, default="text")
    answer = models.OneToOneField(
        "AnswerArtifact",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="message",
    )


class Turn(UUIDModel):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="turns")
    request_id = models.UUIDField()
    payload_hash = models.CharField(max_length=64)
    route = models.ForeignKey("RouteConfiguration", null=True, on_delete=models.PROTECT)
    input_text = models.TextField()
    operation = models.CharField(max_length=50, default="chat")
    expected_profile_revision = models.PositiveIntegerField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation", "request_id"], name="unique_turn_request"
            )
        ]


class TurnAttempt(UUIDModel):
    class Status(models.TextChoices):
        ACCEPTED = "accepted"
        RUNNING = "running"
        SUCCEEDED = "succeeded"
        NEEDS_INPUT = "needs_input"
        INSUFFICIENT_EVIDENCE = "insufficient_evidence"
        FAILED = "failed"
        CANCELLED = "cancelled"
        SUPERSEDED = "superseded"

    ACTIVE = [Status.ACCEPTED, Status.RUNNING]
    turn = models.ForeignKey(Turn, on_delete=models.CASCADE, related_name="attempts")
    conversation = models.ForeignKey(
        Conversation, on_delete=models.CASCADE, related_name="attempts", editable=False
    )
    status = models.CharField(max_length=30, choices=Status, default=Status.ACCEPTED)
    profile_revision = models.PositiveIntegerField(null=True)
    corpus_release = models.ForeignKey(CorpusRelease, null=True, on_delete=models.PROTECT)
    route = models.ForeignKey("RouteConfiguration", null=True, on_delete=models.PROTECT)
    deadline_at = models.DateTimeField()
    terminal_code = models.CharField(max_length=100, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["conversation"],
                condition=Q(status__in=["accepted", "running"]),
                name="one_active_attempt_per_conversation",
            )
        ]

    def save(self, *args: Any, **kwargs: Any) -> None:
        expected_conversation_id = self.turn.conversation_id
        if self.conversation_id is None:
            self.conversation_id = expected_conversation_id
        elif self.conversation_id != expected_conversation_id:
            raise ValidationError("Attempt and turn must belong to the same conversation.")
        super().save(*args, **kwargs)


class RouteConfiguration(UUIDModel):
    relay_type = models.CharField(max_length=40)
    base_url = models.URLField(max_length=1000)
    configured_model = models.CharField(max_length=200)
    api_dialect = models.CharField(max_length=50)
    capabilities = models.JSONField(default=dict)
    context_limit = models.PositiveIntegerField()
    timeout_policy = models.JSONField(default=dict)
    configuration_hash = models.CharField(max_length=64, unique=True)
    qualification_state = models.CharField(max_length=30, default="unqualified")


class RouteQualification(UUIDModel):
    route = models.ForeignKey(RouteConfiguration, on_delete=models.PROTECT)
    tested_configuration_hash = models.CharField(max_length=64)
    evaluation_results = models.JSONField(default=dict)
    state = models.CharField(max_length=30)


class ModelCallAttempt(UUIDModel):
    turn_attempt = models.ForeignKey(TurnAttempt, null=True, on_delete=models.CASCADE)
    task = models.CharField(max_length=50)
    route = models.ForeignKey(RouteConfiguration, on_delete=models.PROTECT)
    requested_model = models.CharField(max_length=200)
    upstream_reported_model = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=30)
    duration_ms = models.PositiveIntegerField(null=True)
    reported_usage = models.JSONField(default=dict)
    safe_error_code = models.CharField(max_length=100, blank=True)


class AnswerArtifact(UUIDModel):
    attempt = models.OneToOneField(TurnAttempt, on_delete=models.CASCADE, related_name="answer")
    outcome = models.CharField(max_length=40)
    blocks = models.JSONField(default=list)
    verification_status = models.CharField(max_length=30)
    profile_revision = models.PositiveIntegerField(null=True)
    corpus_release = models.ForeignKey(CorpusRelease, null=True, on_delete=models.PROTECT)


class AnswerClaim(UUIDModel):
    answer = models.ForeignKey(AnswerArtifact, on_delete=models.CASCADE, related_name="claims")
    claim_type = models.CharField(max_length=40)
    display_text = models.TextField()
    fact_ids = models.JSONField(default=list)
    evidence_bundles = models.ManyToManyField(EvidenceBundle)
    verification_result = models.CharField(max_length=30)


class RecommendationSnapshot(UUIDModel):
    answer = models.OneToOneField(AnswerArtifact, null=True, on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    profile_revision = models.PositiveIntegerField()
    corpus_release = models.ForeignKey(CorpusRelease, on_delete=models.PROTECT)
    candidate_results = models.JSONField(default=list)
    rankings = models.JSONField(default=list)
    calculations = models.JSONField(default=list)
    rule_version = models.CharField(max_length=50)


class AIPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, primary_key=True, on_delete=models.CASCADE)
    route = models.ForeignKey(RouteConfiguration, null=True, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)
