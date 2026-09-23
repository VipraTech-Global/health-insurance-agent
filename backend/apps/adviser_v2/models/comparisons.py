"""Generated from research/design/entity-field-dictionary.json (discussion-r26-neutral-comparison)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import Q

from ..fields import EncryptedTextField, ValidatedJSONField
from .base import ApprovedModel


class Comparison(ApprovedModel):
    'One saved neutral policy comparison for an exact customer profile and published policy-knowledge release.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    turn = models.ForeignKey('Turn', on_delete=models.PROTECT, related_name='+')
    advice_request = models.ForeignKey('AdviceRequest', on_delete=models.PROTECT, related_name='+')
    profile_revision = models.ForeignKey('CustomerProfileRevision', on_delete=models.PROTECT, related_name='+')
    knowledge_release = models.ForeignKey('KnowledgeRelease', on_delete=models.PROTECT, related_name='+')
    outcome = models.CharField(max_length=22, choices=[('completed', 'completed'), ('conditional', 'conditional'), ('clarification_required', 'clarification_required'), ('insufficient_evidence', 'insufficient_evidence')])
    supersedes = models.ForeignKey('self', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_comparison'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_comparison_id_owner_uq'),
            models.UniqueConstraint(fields=['turn'], name='v2_comparison_uq_1'),
        ]


class PolicyComparisonAssessment(ApprovedModel):
    'One exact public policy configuration evaluated neutrally against the customer criteria.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    comparison = models.ForeignKey('Comparison', on_delete=models.PROTECT, related_name='+')
    product_variant = models.ForeignKey('ProductVariant', on_delete=models.PROTECT, related_name='+')
    evaluated_selection = ValidatedJSONField(contract='AcceptedSelectionV1')
    selection_commitment = models.CharField(max_length=64)
    quote = models.ForeignKey('Quote', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_policy_comparison_assessment'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_policy_comparison_assessment_id_owner_uq'),
            models.UniqueConstraint(fields=['comparison', 'product_variant', 'selection_commitment'], name='v2_policy_comparison_assessment_uq_1'),
        ]


class PolicyRequirementMatch(ApprovedModel):
    'How one compared policy performs against one exact customer requirement.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    comparison_assessment = models.ForeignKey('PolicyComparisonAssessment', on_delete=models.PROTECT, related_name='+')
    customer_requirement = models.ForeignKey('CustomerRequirement', on_delete=models.PROTECT, related_name='+')
    outcome = models.CharField(max_length=16, choices=[('meets', 'meets'), ('partly_meets', 'partly_meets'), ('does_not_meet', 'does_not_meet'), ('unknown', 'unknown'), ('not_applicable', 'not_applicable')])
    comparison_value = ValidatedJSONField(contract='TypedValueV1', null=True, blank=True)
    provider_network_entry = models.ForeignKey('ProviderNetworkEntry', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_policy_requirement_match'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_policy_requirement_match_id_owner_uq'),
            models.UniqueConstraint(fields=['comparison_assessment', 'customer_requirement'], name='v2_policy_requirement_match_uq_1'),
        ]


class InformationNeed(ApprovedModel):
    'One missing customer fact, requirement or document confirmation that should be asked before stronger advice.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    comparison = models.ForeignKey('Comparison', on_delete=models.PROTECT, related_name='+')
    subject_person = models.ForeignKey('Person', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    need_kind = models.CharField(max_length=21, choices=[('fact', 'fact'), ('requirement', 'requirement'), ('document_confirmation', 'document_confirmation')])
    information_key = models.CharField(max_length=120)
    reason = EncryptedTextField()
    priority = models.CharField(max_length=16, choices=[('required', 'required'), ('important', 'important'), ('optional', 'optional')])
    status = models.CharField(max_length=16, choices=[('open', 'open'), ('asked', 'asked'), ('resolved', 'resolved'), ('waived', 'waived'), ('unavailable', 'unavailable')], default='open')
    asked_in_message = models.ForeignKey('Message', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    resolved_in_profile_revision = models.ForeignKey('CustomerProfileRevision', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_information_need'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_information_need_id_owner_uq'),
            models.UniqueConstraint(fields=['comparison', 'subject_person', 'need_kind', 'information_key'], name='v2_information_need_uq_1', nulls_distinct=False),
            models.CheckConstraint(condition=~Q(status='asked') | Q(asked_in_message__isnull=False), name='v2_information_need_ck_1'),
            models.CheckConstraint(condition=~Q(status='resolved') | Q(resolved_in_profile_revision__isnull=False), name='v2_information_need_ck_2'),
        ]


class ComparisonStatement(ApprovedModel):
    'One independently checkable cited factual statement in a policy comparison.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    comparison = models.ForeignKey('Comparison', on_delete=models.PROTECT, related_name='+')
    ordinal = models.IntegerField()
    comparison_assessment = models.ForeignKey('PolicyComparisonAssessment', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    requirement_match = models.ForeignKey('PolicyRequirementMatch', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    information_need = models.ForeignKey('InformationNeed', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    calculation = models.ForeignKey('Calculation', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    text = EncryptedTextField()
    statement_type = models.CharField(max_length=17, choices=[('customer_context', 'customer_context'), ('eligibility', 'eligibility'), ('requirement_match', 'requirement_match'), ('benefit', 'benefit'), ('restriction', 'restriction'), ('price', 'price'), ('provider', 'provider'), ('calculation', 'calculation'), ('limitation', 'limitation'), ('next_step', 'next_step')])
    critical = models.BooleanField(default=True)
    support_status = models.CharField(max_length=26, choices=[('supported', 'supported'), ('partly_supported', 'partly_supported'), ('unsupported', 'unsupported'), ('customer_profile_supported', 'customer_profile_supported')], default='unverified')

    class Meta:
        db_table = 'adviser_v2_comparison_statement'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_comparison_statement_id_owner_uq'),
            models.UniqueConstraint(fields=['comparison', 'ordinal'], name='v2_comparison_statement_uq_1'),
            models.CheckConstraint(condition=(Q(comparison_assessment__isnull=True) & Q(requirement_match__isnull=True) & Q(information_need__isnull=True)) | (Q(comparison_assessment__isnull=False) & Q(requirement_match__isnull=True) & Q(information_need__isnull=True)) | (Q(comparison_assessment__isnull=True) & Q(requirement_match__isnull=False) & Q(information_need__isnull=True)) | (Q(comparison_assessment__isnull=True) & Q(requirement_match__isnull=True) & Q(information_need__isnull=False)), name='v2_comparison_statement_ck_1'),
        ]


class ComparisonCitation(ApprovedModel):
    'Exact original policy passage supporting, restricting or conflicting with one comparison statement.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    comparison_statement = models.ForeignKey('ComparisonStatement', on_delete=models.PROTECT, related_name='+')
    evidence_span = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+')
    policy_rule = models.ForeignKey('PolicyRule', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    role = models.CharField(max_length=17, choices=[('supports', 'supports'), ('restricts', 'restricts'), ('excepts', 'excepts'), ('conflicts', 'conflicts'), ('assumption_source', 'assumption_source')])
    ordinal = models.IntegerField()

    class Meta:
        db_table = 'adviser_v2_comparison_citation'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_comparison_citation_id_owner_uq'),
            models.UniqueConstraint(fields=['comparison_statement', 'evidence_span', 'role'], name='v2_comparison_citation_uq_1'),
        ]


class Calculation(ApprovedModel):
    'One immutable deterministic calculation with exact inputs, operation order, assumptions and result.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    advice_request = models.ForeignKey('AdviceRequest', on_delete=models.PROTECT, related_name='+')
    calculation_type = models.CharField(max_length=120)
    engine_version = models.CharField(max_length=120)
    inputs = ValidatedJSONField(contract='CalculationInputsV1')
    operations = ValidatedJSONField(contract='CalculationOperationsV1')
    result = ValidatedJSONField(contract='TypedValueV1')
    assumptions = ValidatedJSONField(contract='AssumptionsV1', default=list)
    status = models.CharField(max_length=16, choices=[('complete', 'complete'), ('blocked', 'blocked'), ('failed', 'failed')])

    class Meta:
        db_table = 'adviser_v2_calculation'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_calculation_id_owner_uq'),
        ]
