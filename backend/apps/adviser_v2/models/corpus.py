"""Generated from research/design/entity-field-dictionary.json (discussion-r26-neutral-comparison)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from ..fields import EncryptedCharField, EncryptedTextField, ValidatedJSONField
from .base import ApprovedModel


class Insurer(ApprovedModel):
    'One insurer in the approved research roster and the issuer identity used by products and official documents.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    name = models.CharField(max_length=250)

    class Meta:
        db_table = 'adviser_v2_insurer'


class DiscoveryRun(ApprovedModel):
    'One autonomous Codex session tasked with discovering public documents for one insurer.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    insurer = models.ForeignKey('Insurer', on_delete=models.PROTECT, related_name='+')
    instructions = models.TextField()
    session_id = models.CharField(max_length=250)
    model_name = models.CharField(max_length=160)
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=[('queued', 'queued'), ('running', 'running'), ('completed', 'completed'), ('failed', 'failed'), ('cancelled', 'cancelled')], default='queued')
    error_summary = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_discovery_run'
        constraints = [
            models.UniqueConstraint(fields=['session_id'], name='v2_discovery_run_uq_1'),
            models.CheckConstraint(condition=~Q(status__in=['completed', 'failed', 'cancelled']) | Q(completed_at__isnull=False), name='v2_discovery_run_ck_1'),
            models.CheckConstraint(condition=~Q(status='failed') | (Q(error_summary__isnull=False) & ~Q(error_summary='')), name='v2_discovery_run_ck_2'),
        ]


class SourceURL(ApprovedModel):
    'One unique public web address discovered by Codex, independent of how often or where it was observed.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    url = models.TextField()
    source_type = models.CharField(max_length=16, choices=[('insurer_site', 'insurer_site'), ('regulator_site', 'regulator_site'), ('government_site', 'government_site'), ('independent_site', 'independent_site'), ('archive', 'archive'), ('other', 'other'), ('unknown', 'unknown')], default='unknown')

    class Meta:
        db_table = 'adviser_v2_source_url'
        constraints = [
            models.UniqueConstraint(fields=['url'], name='v2_source_url_uq_1'),
        ]


class SourceObservation(ApprovedModel):
    'One retained occasion on which a Codex discovery run encountered a source URL.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    discovery_run = models.ForeignKey('DiscoveryRun', on_delete=models.PROTECT, related_name='+')
    source_url = models.ForeignKey('SourceURL', on_delete=models.PROTECT, related_name='+')
    found_in_capture = models.ForeignKey('SourceCapture', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    observation_type = models.CharField(max_length=17, choices=[('search_result', 'search_result'), ('page_link', 'page_link'), ('attachment', 'attachment'), ('document_register', 'document_register'), ('sitemap', 'sitemap'), ('known_url', 'known_url'), ('other', 'other')], default='other')
    label_or_context = models.TextField(null=True, blank=True)
    disposition = models.CharField(max_length=16, choices=[('relevant', 'relevant'), ('irrelevant', 'irrelevant'), ('unresolved', 'unresolved')], default='unresolved')
    disposition_reason = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_source_observation'
        constraints = [
            models.CheckConstraint(condition=~Q(disposition='irrelevant') | (Q(disposition_reason__isnull=False) & ~Q(disposition_reason='')), name='v2_source_observation_ck_1'),
        ]


class SourceCapture(ApprovedModel):
    'One attempt by a Codex discovery run to preserve the content currently returned by a source URL.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    discovery_run = models.ForeignKey('DiscoveryRun', on_delete=models.PROTECT, related_name='+')
    source_url = models.ForeignKey('SourceURL', on_delete=models.PROTECT, related_name='+')
    completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=16, choices=[('running', 'running'), ('captured', 'captured'), ('failed', 'failed')], default='running')
    http_status = models.SmallIntegerField(null=True, blank=True)
    original_file = models.ForeignKey('OriginalFile', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    document_version = models.ForeignKey('DocumentVersion', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    error_summary = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'adviser_v2_source_capture'
        constraints = [
            models.CheckConstraint(condition=Q(http_status__isnull=True) | (Q(http_status__gte=100) & Q(http_status__lte=599)), name='v2_source_capture_ck_1'),
            models.CheckConstraint(condition=~Q(status='captured') | (Q(original_file__isnull=False) & Q(completed_at__isnull=False)), name='v2_source_capture_ck_2'),
            models.CheckConstraint(condition=~Q(status='failed') | (Q(error_summary__isnull=False) & Q(completed_at__isnull=False)), name='v2_source_capture_ck_3'),
            models.CheckConstraint(condition=~Q(status='running') | Q(completed_at__isnull=True), name='v2_source_capture_ck_4'),
        ]


class OriginalFile(ApprovedModel):
    'Content-addressed exact bytes preserved from a public source or private customer upload.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    sha256 = models.CharField(max_length=64)
    storage_key = models.CharField(max_length=500)
    byte_size = models.BigIntegerField()
    media_type = models.CharField(max_length=150)
    availability = models.CharField(max_length=16, choices=[('available', 'available'), ('quarantined', 'quarantined'), ('deleted', 'deleted')], default='available')
    last_verified_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'adviser_v2_original_file'
        constraints = [
            models.UniqueConstraint(fields=['owner', 'sha256'], name='v2_original_file_uq_1', nulls_distinct=False),
            models.UniqueConstraint(fields=['storage_key'], name='v2_original_file_uq_2'),
            models.CheckConstraint(condition=Q(byte_size__gte=0), name='v2_original_file_ck_1'),
        ]


class CustomerUploadedDocument(ApprovedModel):
    'One private document supplied by a customer, separate from its content-addressed bytes.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='+')
    original_file = models.ForeignKey('OriginalFile', on_delete=models.PROTECT, related_name='+')
    source_message = models.ForeignKey('Message', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    display_name = EncryptedCharField(max_length=300, null=True, blank=True)
    kind = models.CharField(max_length=18, choices=[('offer', 'offer'), ('quote', 'quote'), ('policy_schedule', 'policy_schedule'), ('endorsement', 'endorsement'), ('member_certificate', 'member_certificate'), ('other', 'other')], default='other')
    review_status = models.CharField(max_length=16, choices=[('received', 'received'), ('readable', 'readable'), ('classified', 'classified'), ('unusable', 'unusable'), ('conflicted', 'conflicted')], default='received')

    class Meta:
        db_table = 'adviser_v2_customer_uploaded_document'
        constraints = [
            models.UniqueConstraint(fields=['id', 'owner'], name='v2_customer_uploaded_document_id_owner_uq'),
        ]


class DocumentSeries(ApprovedModel):
    'Stable identity of one continuing publication across editions, such as a product policy wording.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    issuer = models.ForeignKey('Insurer', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    name = models.TextField()
    kind = models.CharField(max_length=26, choices=[('policy_wording', 'policy_wording'), ('customer_information_sheet', 'customer_information_sheet'), ('prospectus', 'prospectus'), ('endorsement', 'endorsement'), ('premium_table', 'premium_table'), ('provider_list', 'provider_list'), ('regulation', 'regulation'), ('notice', 'notice'), ('comparison', 'comparison'), ('web_page', 'web_page'), ('other', 'other')], default='other')
    authority = models.CharField(max_length=20, choices=[('insurer_issued', 'insurer_issued'), ('regulator_issued', 'regulator_issued'), ('government_issued', 'government_issued'), ('independent_analysis', 'independent_analysis'), ('unknown', 'unknown')], default='unknown')
    relevance = models.CharField(max_length=16, choices=[('relevant', 'relevant'), ('supporting', 'supporting'), ('unrelated', 'unrelated'), ('unresolved', 'unresolved')], default='unresolved')

    class Meta:
        db_table = 'adviser_v2_document_series'


class DocumentVersion(ApprovedModel):
    'One identified edition within a DocumentSeries, with evidence-backed dates and explicit supersession.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    document_series = models.ForeignKey('DocumentSeries', on_delete=models.PROTECT, related_name='+')
    version_label = models.CharField(max_length=200, null=True, blank=True)
    identifiers = ValidatedJSONField(contract='IdentifiersV1', default=list)
    language = models.CharField(max_length=35, null=True, blank=True)
    published_on = models.DateField(null=True, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    effective_to = models.DateField(null=True, blank=True)
    supersedes = models.ForeignKey('self', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    review_status = models.CharField(max_length=16, choices=[('unreviewed', 'unreviewed'), ('identified', 'identified'), ('verified', 'verified'), ('conflicted', 'conflicted')], default='unreviewed')

    class Meta:
        db_table = 'adviser_v2_document_version'
        constraints = [
            models.CheckConstraint(condition=Q(effective_to__isnull=True) | Q(effective_from__isnull=True) | Q(effective_to__gte=F('effective_from')), name='v2_document_version_ck_1'),
        ]


class DocumentPage(ApprovedModel):
    'One physical PDF page and its explicit review state, including pages on which extraction failed.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    original_file = models.ForeignKey('OriginalFile', on_delete=models.PROTECT, related_name='+')
    page_number = models.IntegerField()
    printed_label = models.CharField(max_length=80, null=True, blank=True)
    review_state = models.CharField(max_length=17, choices=[('unread', 'unread'), ('text_read', 'text_read'), ('visually_reviewed', 'visually_reviewed'), ('fully_reviewed', 'fully_reviewed'), ('unresolved', 'unresolved')], default='unread')

    class Meta:
        db_table = 'adviser_v2_document_page'
        constraints = [
            models.UniqueConstraint(fields=['original_file', 'page_number'], name='v2_document_page_uq_1'),
            models.CheckConstraint(condition=Q(page_number__gt=0), name='v2_document_page_ck_1'),
        ]


class EvidenceSpan(ApprovedModel):
    'One exact passage, table cell, footnote or region from either a public capture or private customer upload.'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    source_capture = models.ForeignKey('SourceCapture', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    customer_uploaded_document = models.ForeignKey('CustomerUploadedDocument', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    page = models.ForeignKey('DocumentPage', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    section_label = models.CharField(max_length=200, null=True, blank=True)
    quote = EncryptedTextField()
    context = ValidatedJSONField(contract='EvidenceContextV1', default=dict)
    method = models.CharField(max_length=16, choices=[('native_text', 'native_text'), ('ocr_verified', 'ocr_verified'), ('manual_visual', 'manual_visual'), ('html', 'html'), ('json', 'json')])
    verification = models.CharField(max_length=17, choices=[('unverified', 'unverified'), ('text_verified', 'text_verified'), ('visually_verified', 'visually_verified'), ('reviewed', 'reviewed'), ('failed', 'failed')], default='unverified')
    locator = ValidatedJSONField(contract='OriginalLocatorV1')

    class Meta:
        db_table = 'adviser_v2_evidence_span'
        constraints = [
            models.CheckConstraint(condition=(Q(source_capture__isnull=False) & Q(customer_uploaded_document__isnull=True)) | (Q(source_capture__isnull=True) & Q(customer_uploaded_document__isnull=False)), name='v2_evidence_span_ck_1'),
        ]
