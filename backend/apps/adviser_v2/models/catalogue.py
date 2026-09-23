"""Generated from research/design/entity-field-dictionary.json (discussion-r26-neutral-comparison)."""

from __future__ import annotations

import uuid

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import F, Q
from pgvector.django import HnswIndex, VectorField

from ..fields import ValidatedJSONField
from .base import ApprovedModel


class Product(ApprovedModel):
    'Stable insurer product family, independent of policy editions, named variants and optional additions.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    insurer = models.ForeignKey('Insurer', on_delete=models.PROTECT, related_name='+')
    name = models.CharField(max_length=250)
    benefit_type = models.CharField(max_length=17, choices=[('medical_indemnity', 'medical_indemnity'), ('fixed_benefit', 'fixed_benefit'), ('hybrid', 'hybrid'), ('addon', 'addon'), ('unresolved', 'unresolved')], default='unresolved')
    lifecycle_status = models.CharField(max_length=16, choices=[('open', 'open'), ('withdrawn', 'withdrawn'), ('renewal_only', 'renewal_only'), ('historical', 'historical'), ('unresolved', 'unresolved')], default='unresolved')
    comparison_role = models.CharField(max_length=16, choices=[('primary_policy', 'primary_policy'), ('supplementary', 'supplementary'), ('reference_only', 'reference_only'), ('excluded', 'excluded'), ('unresolved', 'unresolved')], default='unresolved')
    identity_evidence = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'adviser_v2_product'


class PolicyVersion(ApprovedModel):
    'One complete legal terms package for a Product, assembled from every applicable governing document.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    product = models.ForeignKey('Product', on_delete=models.PROTECT, related_name='+')
    uin = models.CharField(max_length=100, null=True, blank=True)
    version_label = models.CharField(max_length=200, null=True, blank=True)
    publication_status = models.CharField(max_length=16, choices=[('draft', 'draft'), ('reviewed', 'reviewed'), ('published', 'published'), ('superseded', 'superseded'), ('blocked', 'blocked')], default='draft')
    supersedes = models.ForeignKey('self', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    applicability = ValidatedJSONField(contract='ApplicabilityV1')

    class Meta:
        db_table = 'adviser_v2_policy_version'


class PolicyVersionDocument(ApprovedModel):
    'Membership, role, conditional applicability and proven precedence of one DocumentVersion in a PolicyVersion.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    policy_version = models.ForeignKey('PolicyVersion', on_delete=models.PROTECT, related_name='+')
    document_version = models.ForeignKey('DocumentVersion', on_delete=models.PROTECT, related_name='+')
    role = models.CharField(max_length=26, choices=[('base_wording', 'base_wording'), ('customer_information_sheet', 'customer_information_sheet'), ('prospectus', 'prospectus'), ('endorsement', 'endorsement'), ('regulatory_modification', 'regulatory_modification'), ('referenced_schedule', 'referenced_schedule'), ('other_dependency', 'other_dependency')])
    required_for_policy = models.BooleanField(default=True)
    applicability = ValidatedJSONField(contract='ApplicabilityV1')
    precedence_evidence = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_policy_version_document'
        constraints = [
            models.UniqueConstraint(fields=['policy_version', 'document_version', 'role'], name='v2_policy_version_document_uq_1'),
        ]


class ProductVariant(ApprovedModel):
    'One insurer-defined base variant and its allowed sums insured, deductibles, room categories and family choices.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    policy_version = models.ForeignKey('PolicyVersion', on_delete=models.PROTECT, related_name='+')
    name = models.CharField(max_length=200, default='Default')
    choices = ValidatedJSONField(contract='ConfigurationV1')
    availability = ValidatedJSONField(contract='ApplicabilityV1')
    identity_evidence = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'adviser_v2_product_variant'
        constraints = [
            models.UniqueConstraint(fields=['policy_version', 'name'], name='v2_product_variant_uq_1'),
        ]


class ProductOption(ApprovedModel):
    'One optional or mandatory add-on, rider or election available with a ProductVariant.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    product_variant = models.ForeignKey('ProductVariant', on_delete=models.PROTECT, related_name='+')
    option_policy_version = models.ForeignKey('PolicyVersion', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    name = models.CharField(max_length=200)
    selection_kind = models.CharField(max_length=16, choices=[('optional', 'optional'), ('mandatory', 'mandatory')], default='optional')
    conditions = ValidatedJSONField(contract='ApplicabilityV1')
    identity_evidence = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'adviser_v2_product_option'
        constraints = [
            models.UniqueConstraint(fields=['product_variant', 'name'], name='v2_product_option_uq_1'),
        ]


class PolicyRule(ApprovedModel):
    'One immutable, reviewed condition, benefit, restriction or calculation instruction from a public policy version.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    policy_version = models.ForeignKey('PolicyVersion', on_delete=models.PROTECT, related_name='+')
    rule_key = models.CharField(max_length=160)
    rule_type = models.CharField(max_length=17, choices=[('definition', 'definition'), ('eligibility', 'eligibility'), ('coverage', 'coverage'), ('exclusion', 'exclusion'), ('exception', 'exception'), ('waiting_period', 'waiting_period'), ('limit', 'limit'), ('deduction', 'deduction'), ('accumulation', 'accumulation'), ('restoration', 'restoration'), ('calculation', 'calculation'), ('precedence', 'precedence'), ('operational_right', 'operational_right')])
    body = ValidatedJSONField(contract='RuleV1')
    review_status = models.CharField(max_length=16, choices=[('draft', 'draft'), ('verified', 'verified'), ('blocked', 'blocked'), ('superseded', 'superseded')], default='draft')
    supersedes = models.ForeignKey('self', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_policy_rule'
        constraints = [
            models.UniqueConstraint(fields=['supersedes'], name='v2_policy_rule_uq_1', condition=Q(supersedes__isnull=False)),
        ]


class PolicyRuleEvidence(ApprovedModel):
    'One exact public source passage supporting, defining, restricting or contradicting a policy rule.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    policy_rule = models.ForeignKey('PolicyRule', on_delete=models.PROTECT, related_name='+')
    evidence_span = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+')
    role = models.CharField(max_length=16, choices=[('supports', 'supports'), ('defines', 'defines'), ('restricts', 'restricts'), ('excepts', 'excepts'), ('contradicts', 'contradicts'), ('precedence', 'precedence'), ('table_header', 'table_header'), ('table_cell', 'table_cell'), ('footnote', 'footnote')])
    is_required = models.BooleanField(default=True)

    class Meta:
        db_table = 'adviser_v2_policy_rule_evidence'
        constraints = [
            models.UniqueConstraint(fields=['policy_rule', 'evidence_span', 'role'], name='v2_policy_rule_evidence_uq_1'),
        ]


class PolicyRuleLink(ApprovedModel):
    'A reviewed connection requiring two policy rules to be interpreted together.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    from_policy_rule = models.ForeignKey('PolicyRule', on_delete=models.PROTECT, related_name='+')
    to_policy_rule = models.ForeignKey('PolicyRule', on_delete=models.PROTECT, related_name='+')
    link_type = models.CharField(max_length=17, choices=[('definition', 'definition'), ('prerequisite', 'prerequisite'), ('exception', 'exception'), ('overrides', 'overrides'), ('calculation_input', 'calculation_input'), ('scope', 'scope')])

    class Meta:
        db_table = 'adviser_v2_policy_rule_link'
        constraints = [
            models.UniqueConstraint(fields=['from_policy_rule', 'to_policy_rule', 'link_type'], name='v2_policy_rule_link_uq_1'),
            models.CheckConstraint(condition=~Q(from_policy_rule=F('to_policy_rule')), name='v2_policy_rule_link_ck_1'),
        ]


class PolicyRuleTableCell(ApprovedModel):
    'One original-backed result selected by the complete axes declared in a policy rule body.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    policy_rule = models.ForeignKey('PolicyRule', on_delete=models.PROTECT, related_name='+')
    selectors = ValidatedJSONField(contract='TableSelectorsV1')
    value = ValidatedJSONField(contract='ExpressionV1')
    evidence_span = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'adviser_v2_policy_rule_table_cell'
        constraints = [
            models.UniqueConstraint(fields=['policy_rule', 'selectors'], name='v2_policy_rule_table_cell_uq_1'),
        ]


class ProviderLocation(ApprovedModel):
    'One exact public hospital or healthcare-facility branch identity used for network matching.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    facility_name = models.CharField(max_length=300)
    organization_name = models.CharField(max_length=250, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=150, null=True, blank=True)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    country_code = models.CharField(max_length=2, default='IN')
    external_identifiers = ValidatedJSONField(contract='IdentifiersV1', default=list)
    identity_status = models.CharField(max_length=16, choices=[('unresolved', 'unresolved'), ('verified', 'verified'), ('conflicted', 'conflicted')], default='unresolved')
    supersedes = models.ForeignKey('self', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_provider_location'
        constraints = [
            models.UniqueConstraint(fields=['supersedes'], name='v2_provider_location_uq_1', condition=Q(supersedes__isnull=False)),
        ]


class ProviderNetworkSnapshot(ApprovedModel):
    'One dated, scoped insurer network source or directory query, including a zero-result or failed check.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    insurer = models.ForeignKey('Insurer', on_delete=models.PROTECT, related_name='+')
    product_variant = models.ForeignKey('ProductVariant', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    source_capture = models.ForeignKey('SourceCapture', on_delete=models.PROTECT, related_name='+')
    scope = ValidatedJSONField(contract='ProviderNetworkScopeV1')
    observed_at = models.DateTimeField()
    completeness = models.CharField(max_length=18, choices=[('complete_for_scope', 'complete_for_scope'), ('partial', 'partial'), ('unknown', 'unknown'), ('failed', 'failed')], default='unknown')
    scope_evidence = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+', null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_provider_network_snapshot'


class ProviderNetworkEntry(ApprovedModel):
    'One exact facility branch status printed in one immutable provider-network snapshot.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    provider_network_snapshot = models.ForeignKey('ProviderNetworkSnapshot', on_delete=models.PROTECT, related_name='+')
    provider_location = models.ForeignKey('ProviderLocation', on_delete=models.PROTECT, related_name='+')
    network_status = models.CharField(max_length=16, choices=[('network', 'network'), ('restricted', 'restricted'), ('excluded', 'excluded'), ('unknown', 'unknown')])
    restrictions = ValidatedJSONField(contract='NetworkRestrictionsV1')
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    evidence_span = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'adviser_v2_provider_network_entry'
        constraints = [
            models.UniqueConstraint(fields=['provider_network_snapshot', 'provider_location', 'network_status'], name='v2_provider_network_entry_uq_1'),
            models.CheckConstraint(condition=Q(effective_to__isnull=True) | Q(effective_from__isnull=True) | Q(effective_to__gte=F('effective_from')), name='v2_provider_network_entry_ck_1'),
        ]


class KnowledgeRelease(ApprovedModel):
    'Immutable set of reviewed policy rules that the buying adviser may use together.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    release_number = models.BigIntegerField()
    state = models.CharField(max_length=16, choices=[('draft', 'draft'), ('ready', 'ready'), ('published', 'published'), ('retired', 'retired'), ('blocked', 'blocked')], default='draft')
    supported_scope = ValidatedJSONField(contract='CapabilityScopeV1')
    published_at = models.DateTimeField(null=True, blank=True)
    previous_release = models.ForeignKey('self', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    release_label = models.CharField(max_length=32, default='development_alpha')
    readiness = models.JSONField(default=dict)
    manifest_sha256 = models.CharField(max_length=64)

    class Meta:
        db_table = 'adviser_v2_knowledge_release'
        constraints = [
            models.UniqueConstraint(fields=['release_number'], name='v2_knowledge_release_uq_1'),
            models.CheckConstraint(condition=Q(release_number__gt=0), name='v2_knowledge_release_ck_1'),
            models.CheckConstraint(condition=(Q(state__in=['draft', 'ready', 'blocked']) & Q(published_at__isnull=True)) | (Q(state__in=['published', 'retired']) & Q(published_at__isnull=False)), name='v2_knowledge_release_ck_2'),
        ]


class KnowledgeReleaseRule(ApprovedModel):
    'Includes one exact reviewed policy rule in one knowledge release.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    knowledge_release = models.ForeignKey('KnowledgeRelease', on_delete=models.PROTECT, related_name='+')
    policy_rule = models.ForeignKey('PolicyRule', on_delete=models.PROTECT, related_name='+')

    class Meta:
        db_table = 'adviser_v2_knowledge_release_rule'
        constraints = [
            models.UniqueConstraint(fields=['knowledge_release', 'policy_rule'], name='v2_knowledge_release_rule_uq_1'),
        ]


class KnowledgeChannel(ApprovedModel):
    'Selects the current published knowledge release for one application environment.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=80)
    current_release = models.ForeignKey('KnowledgeRelease', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    generation = models.BigIntegerField(default=0)

    class Meta:
        db_table = 'adviser_v2_knowledge_channel'
        constraints = [
            models.UniqueConstraint(fields=['name'], name='v2_knowledge_channel_uq_1'),
        ]


class PolicySearchChunk(ApprovedModel):
    'Replaceable public search index text for one exact section of a policy document.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    document_version = models.ForeignKey('DocumentVersion', on_delete=models.PROTECT, related_name='+')
    evidence_span_ids = ValidatedJSONField(contract='UuidListV1')
    text = models.TextField()
    lexical_vector = SearchVectorField()
    embedding = VectorField(dimensions=1024, null=True, blank=True)
    index_version = models.CharField(max_length=160)
    chunk_sha256 = models.CharField(max_length=64)

    class Meta:
        db_table = 'adviser_v2_policy_search_chunk'
        constraints = [
            models.UniqueConstraint(fields=['document_version', 'index_version', 'chunk_sha256'], name='v2_policy_search_chunk_uq_1'),
        ]
        indexes = [
            GinIndex(fields=['lexical_vector'], name='v2_policy_search_chunk_ix_1'),
            HnswIndex(fields=['embedding'], name='v2_policy_search_chunk_ix_2', m=16, ef_construction=64, opclasses=['vector_cosine_ops']),
        ]


class PolicyPackageComponent(ApprovedModel):
    'One original-backed component slot in a public packaged policy, used to compare which separately issued product supplies medical or supplementary cover.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    package_policy_version = models.ForeignKey('PolicyVersion', on_delete=models.PROTECT, related_name='+')
    slot_key = models.CharField(max_length=80)
    component_product = models.ForeignKey('Product', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    component_policy_version = models.ForeignKey('PolicyVersion', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    asserted_component_uin = models.CharField(max_length=100, null=True, blank=True)
    role = models.CharField(max_length=16, choices=[('medical', 'medical'), ('life', 'life'), ('other', 'other'), ('unresolved', 'unresolved')], default='unresolved')
    selection_kind = models.CharField(max_length=16, choices=[('required', 'required'), ('optional', 'optional'), ('conditional', 'conditional'), ('unresolved', 'unresolved')], default='unresolved')
    selection_policy_rule = models.ForeignKey('PolicyRule', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    evidence_span = models.ForeignKey('EvidenceSpan', on_delete=models.PROTECT, related_name='+')
    review_status = models.CharField(max_length=16, choices=[('unresolved', 'unresolved'), ('reviewed', 'reviewed'), ('conflict', 'conflict'), ('excluded', 'excluded')], default='unresolved')

    class Meta:
        db_table = 'adviser_v2_policy_package_component'
        constraints = [
            models.UniqueConstraint(fields=['package_policy_version', 'slot_key'], name='v2_policy_package_component_uq_1'),
            models.CheckConstraint(condition=~Q(review_status='reviewed') | (Q(component_product__isnull=False) & Q(evidence_span__isnull=False)), name='v2_policy_package_component_ck_1'),
        ]
