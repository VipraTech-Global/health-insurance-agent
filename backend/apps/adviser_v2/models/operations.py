"""Generated from research/design/entity-field-dictionary.json (discussion-r26-neutral-comparison)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from ..fields import ValidatedJSONField
from .base import ApprovedModel


class Turn(ApprovedModel):
    'One durable, idempotent and cancellable customer-message processing request.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    conversation = models.ForeignKey('Conversation', on_delete=models.PROTECT, related_name='+')
    request_id = models.UUIDField()
    input_message = models.ForeignKey('Message', on_delete=models.PROTECT, related_name='+')
    starting_profile_revision = models.ForeignKey('CustomerProfileRevision', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    state = models.CharField(max_length=16, choices=[('queued', 'queued'), ('running', 'running'), ('cancel_requested', 'cancel_requested'), ('cancelled', 'cancelled'), ('completed', 'completed'), ('failed', 'failed'), ('stale', 'stale')], default='queued')
    lease_token = models.UUIDField(null=True, blank=True)
    lease_until = models.DateTimeField(null=True, blank=True)
    deadline = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    error_code = models.CharField(max_length=100, null=True, blank=True)
    route_commitment = models.CharField(max_length=64, default="", editable=False)

    class Meta:
        db_table = 'adviser_v2_turn'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_turn_id_owner_uq'),
            models.UniqueConstraint(fields=['owner', 'request_id'], name='v2_turn_uq_1'),
            models.CheckConstraint(condition=~Q(state='running') | (Q(lease_token__isnull=False) & Q(lease_until__isnull=False)), name='v2_turn_ck_1'),
            models.CheckConstraint(condition=Q(deadline__gt=F('created_at')), name='v2_turn_ck_2'),
            models.CheckConstraint(condition=Q(route_commitment='') | Q(route_commitment__regex=r'^[0-9a-f]{64}$'), name='v2_turn_route_commitment_ck'),
        ]
        indexes = [
            models.Index(fields=['state', 'lease_until'], name='v2_turn_ix_1'),
        ]


class TurnRouteBinding(ApprovedModel):
    'One immutable exact route and passed qualification captured for an interactive role before a turn is queued.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    turn = models.ForeignKey('Turn', on_delete=models.PROTECT, related_name='route_bindings')
    role = models.CharField(max_length=19, choices=[('fact_interpretation', 'fact_interpretation'), ('comparison_answer', 'comparison_answer')])
    route = models.ForeignKey('ModelRoute', on_delete=models.PROTECT, related_name='turn_bindings')
    qualification = models.ForeignKey('ModelQualification', on_delete=models.PROTECT, related_name='turn_bindings')
    requested_model = models.CharField(max_length=160)
    expected_model = models.CharField(max_length=160)
    observed_model = models.CharField(max_length=160)
    endpoint_profile = models.CharField(max_length=120)
    adapter_version = models.CharField(max_length=120)
    route_configuration_sha256 = models.CharField(max_length=64)
    schema_sha256 = models.CharField(max_length=64)

    class Meta:
        db_table = 'adviser_v2_turn_route_binding'
        constraints = [
            models.UniqueConstraint(fields=['turn', 'role'], name='v2_turn_route_binding_uq_1'),
            models.CheckConstraint(condition=Q(role__in=['fact_interpretation', 'comparison_answer']), name='v2_turn_route_binding_role_ck'),
            models.CheckConstraint(condition=Q(route_configuration_sha256__regex=r'^[0-9a-f]{64}$'), name='v2_turn_route_binding_config_ck'),
            models.CheckConstraint(condition=Q(schema_sha256__regex=r'^[0-9a-f]{64}$'), name='v2_turn_route_binding_schema_ck'),
            models.CheckConstraint(condition=Q(expected_model=F('observed_model')), name='v2_turn_route_binding_identity_ck'),
        ]


class TurnEvent(ApprovedModel):
    'One immutable ordered UI event that reconnecting clients can replay without repeating inference.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    turn = models.ForeignKey('Turn', on_delete=models.PROTECT, related_name='+')
    sequence = models.BigIntegerField()
    event_type = models.CharField(max_length=16, choices=[('queued', 'queued'), ('started', 'started'), ('clarification', 'clarification'), ('progress', 'progress'), ('comparison', 'comparison'), ('cancelled', 'cancelled'), ('failed', 'failed'), ('stale', 'stale')])
    payload = ValidatedJSONField(contract='TurnEventV1')

    class Meta:
        db_table = 'adviser_v2_turn_event'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_turn_event_id_owner_uq'),
            models.UniqueConstraint(fields=['turn', 'sequence'], name='v2_turn_event_uq_1'),
            models.CheckConstraint(condition=Q(sequence__gt=0), name='v2_turn_event_ck_1'),
        ]


class Outbox(ApprovedModel):
    'Reliable typed dispatch record committed with the work that Celery or publication must deliver.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    event_type = models.CharField(max_length=21, choices=[('turn_dispatch', 'turn_dispatch'), ('document_processing', 'document_processing'), ('knowledge_publication', 'knowledge_publication')])
    turn = models.ForeignKey('Turn', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    processing_job = models.ForeignKey('ProcessingJob', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    knowledge_release = models.ForeignKey('KnowledgeRelease', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    idempotency_key = models.CharField(max_length=200)
    state = models.CharField(max_length=16, choices=[('pending', 'pending'), ('leased', 'leased'), ('delivered', 'delivered'), ('failed', 'failed')], default='pending')
    attempt_count = models.IntegerField(default=0)
    available_at = models.DateTimeField(default=timezone.now)
    lease_until = models.DateTimeField(null=True, blank=True)
    last_error_code = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_outbox'
        constraints = [
            models.UniqueConstraint(fields=['event_type', 'idempotency_key'], name='v2_outbox_uq_1'),
            models.CheckConstraint(condition=(Q(turn__isnull=False) & Q(processing_job__isnull=True) & Q(knowledge_release__isnull=True)) | (Q(turn__isnull=True) & Q(processing_job__isnull=False) & Q(knowledge_release__isnull=True)) | (Q(turn__isnull=True) & Q(processing_job__isnull=True) & Q(knowledge_release__isnull=False)), name='v2_outbox_ck_1'),
            models.CheckConstraint(condition=~Q(state='leased') | Q(lease_until__isnull=False), name='v2_outbox_ck_2'),
        ]
        indexes = [
            models.Index(fields=['state', 'available_at'], name='v2_outbox_ix_1'),
        ]


class ModelRoute(ApprovedModel):
    'One exact secret-free CLIProxyAPI/Codex route configuration.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    route_key = models.CharField(max_length=120)
    endpoint_profile = models.CharField(max_length=120)
    requested_model = models.CharField(max_length=160)
    adapter_version = models.CharField(max_length=120)
    configuration_sha256 = models.CharField(max_length=64)
    disabled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_model_route'
        constraints = [
            models.UniqueConstraint(fields=['route_key'], name='v2_model_route_uq_1'),
        ]


class ModelQualification(ApprovedModel):
    'One completed test of an exact route against one application schema and capability set.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    route = models.ForeignKey('ModelRoute', on_delete=models.PROTECT, related_name='+')
    schema_name = models.CharField(max_length=19, choices=[('fact_interpretation', 'fact_interpretation'), ('policy_extraction', 'policy_extraction'), ('policy_review', 'policy_review'), ('comparison_answer', 'comparison_answer')])
    schema_sha256 = models.CharField(max_length=64)
    observed_model = models.CharField(max_length=160)
    capabilities = ValidatedJSONField(contract='QualificationV1')
    result = models.CharField(max_length=16, choices=[('passed', 'passed'), ('failed', 'failed')])

    class Meta:
        db_table = 'adviser_v2_model_qualification'
        constraints = [
            models.UniqueConstraint(fields=['route', 'schema_name', 'schema_sha256', 'created_at'], name='v2_model_qualification_uq_1'),
        ]


class ModelAttempt(ApprovedModel):
    'One actual CLIProxyAPI/Codex call with explicit identity, timing, usage and failure.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    turn = models.ForeignKey('Turn', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    processing_job = models.ForeignKey('ProcessingJob', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    qualification = models.ForeignKey('ModelQualification', on_delete=models.PROTECT, related_name='+')
    attempt_number = models.IntegerField()
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True, blank=True)
    observed_model = models.CharField(max_length=160, null=True, blank=True)
    status = models.CharField(max_length=16, choices=[('started', 'started'), ('succeeded', 'succeeded'), ('timeout', 'timeout'), ('transport_error', 'transport_error'), ('schema_error', 'schema_error'), ('identity_error', 'identity_error'), ('cancelled', 'cancelled'), ('indeterminate', 'indeterminate')], default='started')
    usage = ValidatedJSONField(contract='UsageV1')
    error_code = models.CharField(max_length=100, null=True, blank=True)
    request_commitment = models.CharField(max_length=64)
    response_storage_key = models.CharField(max_length=500, null=True, blank=True)
    response_storage_sha256 = models.CharField(max_length=64, null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_model_attempt'
        constraints = [
            models.CheckConstraint(condition=(Q(turn__isnull=False) & Q(processing_job__isnull=True)) | (Q(turn__isnull=True) & Q(processing_job__isnull=False)), name='v2_model_attempt_ck_1'),
            models.CheckConstraint(condition=Q(attempt_number__gt=0), name='v2_model_attempt_ck_2'),
            models.CheckConstraint(condition=Q(completed_at__isnull=True) | Q(completed_at__gte=F('started_at')), name='v2_model_attempt_ck_3'),
            models.CheckConstraint(condition=(Q(response_storage_key__isnull=True) & Q(response_storage_sha256__isnull=True)) | (Q(response_storage_key__isnull=False) & Q(response_storage_sha256__isnull=False)), name='v2_model_attempt_ck_4'),
        ]


class ProcessingJob(ApprovedModel):
    'One resumable public-policy or private-upload classification, reading, extraction, validation or independent-review task.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    source_capture = models.ForeignKey('SourceCapture', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    customer_uploaded_document = models.ForeignKey('CustomerUploadedDocument', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    stage = models.CharField(max_length=18, choices=[('classify', 'classify'), ('read', 'read'), ('ocr', 'ocr'), ('extract', 'extract'), ('validate', 'validate'), ('index', 'index'), ('independent_review', 'independent_review'), ('reconcile', 'reconcile')])
    adapter_version = models.CharField(max_length=160)
    input_commitment = models.CharField(max_length=64)
    attempt_number = models.IntegerField(default=1)
    parent_job = models.ForeignKey('self', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    state = models.CharField(max_length=16, choices=[('queued', 'queued'), ('running', 'running'), ('succeeded', 'succeeded'), ('failed', 'failed'), ('blocked', 'blocked'), ('cancelled', 'cancelled')], default='queued')
    lease_token = models.UUIDField(null=True, blank=True)
    lease_until = models.DateTimeField(null=True, blank=True)
    result_storage_key = models.CharField(max_length=500, null=True, blank=True)
    result_storage_sha256 = models.CharField(max_length=64, null=True, blank=True)
    issues = ValidatedJSONField(contract='ProcessingIssuesV1', default=list)
    error_code = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_processing_job'
        constraints = [
            models.UniqueConstraint(fields=['source_capture', 'stage', 'input_commitment', 'attempt_number'], name='v2_processing_job_uq_1', condition=Q(source_capture__isnull=False)),
            models.UniqueConstraint(fields=['customer_uploaded_document', 'stage', 'input_commitment', 'attempt_number'], name='v2_processing_job_uq_2', condition=Q(customer_uploaded_document__isnull=False)),
            models.CheckConstraint(condition=(Q(source_capture__isnull=False) & Q(customer_uploaded_document__isnull=True)) | (Q(source_capture__isnull=True) & Q(customer_uploaded_document__isnull=False)), name='v2_processing_job_ck_1'),
            models.CheckConstraint(condition=Q(attempt_number__gte=1) & Q(attempt_number__lte=3), name='v2_processing_job_ck_2'),
            models.CheckConstraint(condition=~Q(state='running') | (Q(lease_token__isnull=False) & Q(lease_until__isnull=False)), name='v2_processing_job_ck_3'),
            models.CheckConstraint(condition=(Q(result_storage_key__isnull=True) & Q(result_storage_sha256__isnull=True)) | (Q(result_storage_key__isnull=False) & Q(result_storage_sha256__isnull=False)), name='v2_processing_job_ck_4'),
        ]
        indexes = [
            models.Index(fields=['state', 'lease_until'], name='v2_processing_job_ix_1'),
        ]


class AuditEvent(ApprovedModel):
    'Minimal append-only record of sensitive-data access, publication, deletion and administration without copied customer medical text.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    operation = models.CharField(max_length=100)
    object_kind = models.CharField(max_length=100)
    object_id = models.UUIDField(null=True, blank=True)
    outcome = models.CharField(max_length=16, choices=[('allowed', 'allowed'), ('denied', 'denied'), ('succeeded', 'succeeded'), ('failed', 'failed')])
    metadata = ValidatedJSONField(contract='AuditMetadataV1', default=dict)

    class Meta:
        db_table = 'adviser_v2_audit_event'
