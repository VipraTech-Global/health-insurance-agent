"""Generated from research/design/entity-field-dictionary.json (discussion-r25-final-review)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.contrib.postgres.fields import DateRangeField
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField
from django.db import models
from django.db.models import F, Q
from pgvector.django import HnswIndex, VectorField

from ..fields import EncryptedCharField, EncryptedTextField, ValidatedJSONField
from .base import ApprovedModel, default_accepted_selection


class Person(ApprovedModel):
    "A minimal owner-scoped human label; medical, role and identity assertions live in sourced fact records."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    display_name = EncryptedCharField(max_length=200, default="", blank=True)

    class Meta:
        db_table = "adviser_v2_person"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_person_id_owner_uq"),
        ]


class PersonRelationship(ApprovedModel):
    "Directional relationship between two owner-scoped people, separate from proposed or issued policy membership."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    from_person = models.ForeignKey("Person", on_delete=models.PROTECT, related_name="+")
    to_person = models.ForeignKey("Person", on_delete=models.PROTECT, related_name="+")
    relationship_type = models.CharField(
        max_length=16,
        choices=[
            ("spouse", "spouse"),
            ("parent", "parent"),
            ("child", "child"),
            ("parent_in_law", "parent_in_law"),
            ("sibling", "sibling"),
            ("guardian", "guardian"),
            ("dependent", "dependent"),
            ("other", "other"),
        ],
    )
    source_statement = models.ForeignKey(
        "CustomerStatement", on_delete=models.PROTECT, related_name="+"
    )
    valid_from = models.DateField(null=True, blank=True)
    valid_to = models.DateField(null=True, blank=True)

    class Meta:
        db_table = "adviser_v2_person_relationship"
        constraints = [
            models.UniqueConstraint(
                fields=["id", "owner"], name="v2_person_relationship_id_owner_uq"
            ),
            models.UniqueConstraint(
                fields=[
                    "owner",
                    "from_person",
                    "to_person",
                    "relationship_type",
                    "valid_from",
                    "valid_to",
                ],
                name="v2_person_relationship_uq_1",
                nulls_distinct=False,
            ),
            models.CheckConstraint(
                condition=~Q(from_person=F("to_person")), name="v2_person_relationship_ck_1"
            ),
            models.CheckConstraint(
                condition=Q(valid_to__isnull=True)
                | Q(valid_from__isnull=True)
                | Q(valid_to__gte=F("valid_from")),
                name="v2_person_relationship_ck_2",
            ),
        ]


class Conversation(ApprovedModel):
    "Persistent conversation and its current accepted state."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    title = EncryptedCharField(max_length=200, default="", blank=True)
    current_profile_revision = models.ForeignKey(
        "CustomerProfileRevision", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    status = models.CharField(
        max_length=16,
        choices=[
            ("open", "open"),
            ("archived", "archived"),
            ("deleting", "deleting"),
            ("deleted", "deleted"),
        ],
        default="open",
    )
    updated_at = models.DateTimeField(auto_now=True)
    preferred_language = models.CharField(max_length=35, null=True, blank=True)

    class Meta:
        db_table = "adviser_v2_conversation"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_conversation_id_owner_uq"),
        ]
        indexes = [
            models.Index(fields=["owner", "-updated_at"], name="v2_conversation_ix_1"),
        ]


class Message(ApprovedModel):
    "Immutable submitted or published conversational content."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    conversation = models.ForeignKey("Conversation", on_delete=models.PROTECT, related_name="+")
    sequence = models.BigIntegerField()
    role = models.CharField(
        max_length=16,
        choices=[("customer", "customer"), ("adviser", "adviser"), ("system", "system")],
    )
    content = EncryptedTextField()
    origin = models.CharField(
        max_length=19,
        choices=[
            ("text", "text"),
            ("voice_transcription", "voice_transcription"),
            ("document_import", "document_import"),
            ("system", "system"),
            ("migration", "migration"),
        ],
    )
    client_request_id = models.UUIDField(null=True, blank=True)
    payload_commitment = models.CharField(max_length=64)
    submitted_at = models.DateTimeField()
    recommendation = models.ForeignKey(
        "Recommendation", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    redacted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "adviser_v2_message"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_message_id_owner_uq"),
            models.UniqueConstraint(fields=["conversation", "sequence"], name="v2_message_uq_1"),
            models.UniqueConstraint(
                fields=["owner", "client_request_id"],
                name="v2_message_uq_2",
                condition=Q(client_request_id__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["recommendation"],
                name="v2_message_uq_3",
                condition=Q(recommendation__isnull=False),
            ),
            models.CheckConstraint(condition=Q(sequence__gt=0), name="v2_message_ck_1"),
        ]
        indexes = [
            models.Index(fields=["conversation", "sequence"], name="v2_message_ix_1"),
        ]


class ConversationMessageChunk(ApprovedModel):
    "Replaceable private lexical/semantic index for an exact section of one immutable conversation message."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    conversation = models.ForeignKey("Conversation", on_delete=models.PROTECT, related_name="+")
    message = models.ForeignKey("Message", on_delete=models.PROTECT, related_name="+")
    chunk_index = models.IntegerField()
    start_offset = models.IntegerField()
    end_offset = models.IntegerField()
    lexical_vector = SearchVectorField()
    embedding = VectorField(dimensions=1024, null=True, blank=True)
    index_revision = models.CharField(max_length=160)
    content_commitment = models.CharField(max_length=64)
    invalidated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "adviser_v2_conversation_message_chunk"
        constraints = [
            models.UniqueConstraint(
                fields=["id", "owner"], name="v2_conversation_message_chunk_id_owner_uq"
            ),
            models.UniqueConstraint(
                fields=["message", "chunk_index", "index_revision"],
                name="v2_conversation_message_chunk_uq_1",
            ),
            models.CheckConstraint(
                condition=Q(chunk_index__gte=0), name="v2_conversation_message_chunk_ck_1"
            ),
            models.CheckConstraint(
                condition=Q(start_offset__gte=0) & Q(end_offset__gt=F("start_offset")),
                name="v2_conversation_message_chunk_ck_2",
            ),
        ]
        indexes = [
            GinIndex(fields=["lexical_vector"], name="v2_conversation_messa_d5d39113"),
            HnswIndex(
                fields=["embedding"],
                name="v2_conversation_messa_92df564e",
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
        ]


class CustomerStatement(ApprovedModel):
    "A meaningful source span inside one customer message, retained so unusual or unresolved information cannot be silently dropped."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    source_message = models.ForeignKey("Message", on_delete=models.PROTECT, related_name="+")
    start_offset = models.IntegerField()
    end_offset = models.IntegerField()
    subject_person = models.ForeignKey(
        "Person", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    kind = models.CharField(
        max_length=16,
        choices=[
            ("fact", "fact"),
            ("intended_insured", "intended_insured"),
            ("requirement", "requirement"),
            ("preference", "preference"),
            ("question", "question"),
            ("correction", "correction"),
            ("context", "context"),
            ("other", "other"),
        ],
    )
    status = models.CharField(
        max_length=22,
        choices=[
            ("pending", "pending"),
            ("mapped", "mapped"),
            ("clarification_required", "clarification_required"),
            ("ignored_with_reason", "ignored_with_reason"),
        ],
        default="pending",
    )
    resolution_note = EncryptedTextField(null=True, blank=True)

    class Meta:
        db_table = "adviser_v2_customer_statement"
        constraints = [
            models.UniqueConstraint(
                fields=["id", "owner"], name="v2_customer_statement_id_owner_uq"
            ),
            models.CheckConstraint(
                condition=Q(start_offset__gte=0) & Q(end_offset__gt=F("start_offset")),
                name="v2_customer_statement_ck_1",
            ),
        ]


class CustomerProfileRevision(ApprovedModel):
    "Small immutable checkpoint created only when customer facts or requirements change."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    conversation = models.ForeignKey("Conversation", on_delete=models.PROTECT, related_name="+")
    revision = models.BigIntegerField()

    class Meta:
        db_table = "adviser_v2_customer_profile_revision"
        constraints = [
            models.UniqueConstraint(
                fields=["id", "owner"], name="v2_customer_profile_revision_id_owner_uq"
            ),
            models.UniqueConstraint(
                fields=["conversation", "revision"], name="v2_customer_profile_revision_uq_1"
            ),
            models.CheckConstraint(
                condition=Q(revision__gt=0), name="v2_customer_profile_revision_ck_1"
            ),
        ]


class CustomerFact(ApprovedModel):
    "One validated version of a customer fact; active historical state is reconstructed by logical key and profile revision."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    introduced_in_revision = models.ForeignKey(
        "CustomerProfileRevision", on_delete=models.PROTECT, related_name="+"
    )
    source_statement = models.ForeignKey(
        "CustomerStatement", on_delete=models.PROTECT, related_name="+"
    )
    logical_key = models.UUIDField(default=uuid.uuid4)
    fact_type = models.CharField(max_length=100)
    schema_version = models.PositiveIntegerField()
    value = ValidatedJSONField(contract="FactValueV1")
    status = models.CharField(
        max_length=16,
        choices=[
            ("reported", "reported"),
            ("confirmed", "confirmed"),
            ("disputed", "disputed"),
            ("retracted", "retracted"),
        ],
        default="reported",
    )

    class Meta:
        db_table = "adviser_v2_customer_fact"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_customer_fact_id_owner_uq"),
            models.CheckConstraint(condition=Q(schema_version__gt=0), name="v2_customer_fact_ck_1"),
        ]
        indexes = [
            GinIndex(fields=["value"], name="v2_customer_fact_ix_1"),
        ]


class CustomerRequirement(ApprovedModel):
    "One atomic mandatory, preferred or informational condition used to filter, rank or explain policy configurations."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    introduced_in_revision = models.ForeignKey(
        "CustomerProfileRevision", on_delete=models.PROTECT, related_name="+"
    )
    source_statement = models.ForeignKey(
        "CustomerStatement", on_delete=models.PROTECT, related_name="+"
    )
    logical_key = models.UUIDField(default=uuid.uuid4)
    criterion = models.CharField(max_length=120)
    operator = models.CharField(
        max_length=21,
        choices=[
            ("equals", "equals"),
            ("not_equals", "not_equals"),
            ("less_than_or_equal", "less_than_or_equal"),
            ("greater_than_or_equal", "greater_than_or_equal"),
            ("includes", "includes"),
            ("excludes", "excludes"),
            ("is_available", "is_available"),
            ("is_not_available", "is_not_available"),
            ("minimize", "minimize"),
            ("maximize", "maximize"),
        ],
    )
    target_value = ValidatedJSONField(contract="FactValueV1", null=True, blank=True)
    priority = models.CharField(
        max_length=16,
        choices=[
            ("mandatory", "mandatory"),
            ("preferred", "preferred"),
            ("informational", "informational"),
        ],
    )
    scope = models.CharField(
        max_length=20,
        choices=[
            ("entire_purchase", "entire_purchase"),
            ("all_intended_insured", "all_intended_insured"),
            ("person", "person"),
        ],
    )
    subject_person = models.ForeignKey(
        "Person", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    status = models.CharField(
        max_length=16,
        choices=[
            ("reported", "reported"),
            ("confirmed", "confirmed"),
            ("disputed", "disputed"),
            ("withdrawn", "withdrawn"),
        ],
        default="reported",
    )

    class Meta:
        db_table = "adviser_v2_customer_requirement"
        constraints = [
            models.UniqueConstraint(
                fields=["id", "owner"], name="v2_customer_requirement_id_owner_uq"
            ),
        ]
        indexes = [
            GinIndex(fields=["target_value"], name="v2_customer_requirement_ix_1"),
        ]


class AdviceRequest(ApprovedModel):
    "One customer advice goal spanning any number of clarification messages; execution attempts later pin exact profile revisions."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    conversation = models.ForeignKey("Conversation", on_delete=models.PROTECT, related_name="+")
    source_statement = models.ForeignKey(
        "CustomerStatement", on_delete=models.PROTECT, related_name="+"
    )
    request_type = models.CharField(
        max_length=23,
        choices=[
            ("purchase_recommendation", "purchase_recommendation"),
            ("product_comparison", "product_comparison"),
            ("coverage_question", "coverage_question"),
            ("renewal_review", "renewal_review"),
            ("portability_review", "portability_review"),
        ],
    )
    status = models.CharField(
        max_length=16,
        choices=[("open", "open"), ("fulfilled", "fulfilled"), ("cancelled", "cancelled")],
        default="open",
    )

    class Meta:
        db_table = "adviser_v2_advice_request"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_advice_request_id_owner_uq"),
        ]


class CustomerPolicy(ApprovedModel):
    "Stable identity of one insurer-issued customer policy or customer-specific offer."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    policy_number = EncryptedCharField(max_length=200, null=True, blank=True)
    insurer = models.ForeignKey("Insurer", on_delete=models.PROTECT, related_name="+")
    proposer = models.ForeignKey(
        "Person", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    payer = models.ForeignKey(
        "Person", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    coverage_type = models.CharField(
        max_length=16,
        choices=[
            ("individual", "individual"),
            ("family_floater", "family_floater"),
            ("group_member", "group_member"),
            ("unresolved", "unresolved"),
        ],
        default="unresolved",
    )
    lifecycle_status = models.CharField(
        max_length=16,
        choices=[
            ("offered", "offered"),
            ("active", "active"),
            ("lapsed", "lapsed"),
            ("expired", "expired"),
            ("cancelled", "cancelled"),
            ("declined", "declined"),
            ("unresolved", "unresolved"),
        ],
        default="unresolved",
    )
    group_master_reference = EncryptedCharField(max_length=250, null=True, blank=True)

    class Meta:
        db_table = "adviser_v2_customer_policy"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_customer_policy_id_owner_uq"),
        ]


class CustomerPolicyRevision(ApprovedModel):
    "One exact set of insurer-issued customer selections applying during a defined interval."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    customer_policy = models.ForeignKey(
        "CustomerPolicy", on_delete=models.PROTECT, related_name="+"
    )
    revision_number = models.PositiveIntegerField()
    product_variant = models.ForeignKey(
        "ProductVariant", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    policy_term = DateRangeField(null=True, blank=True)
    effective_during = DateRangeField(null=True, blank=True)
    selected_choices = ValidatedJSONField(
        contract="CustomerPolicySelectionV1", default=default_accepted_selection
    )
    selection_evidence = models.ForeignKey(
        "EvidenceSpan", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    verification_status = models.CharField(
        max_length=16,
        choices=[("reported", "reported"), ("verified", "verified"), ("conflicted", "conflicted")],
        default="reported",
    )

    class Meta:
        db_table = "adviser_v2_customer_policy_revision"
        constraints = [
            models.UniqueConstraint(
                fields=["id", "owner"], name="v2_customer_policy_revision_id_owner_uq"
            ),
            models.UniqueConstraint(
                fields=["customer_policy", "revision_number"],
                name="v2_customer_policy_revision_uq_1",
            ),
        ]


class PolicyMember(ApprovedModel):
    "One person actually covered under one customer policy revision."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    customer_policy_revision = models.ForeignKey(
        "CustomerPolicyRevision", on_delete=models.PROTECT, related_name="+"
    )
    person = models.ForeignKey("Person", on_delete=models.PROTECT, related_name="+")
    covered_during = DateRangeField()
    member_identifier = EncryptedCharField(max_length=160, null=True, blank=True)
    evidence_span = models.ForeignKey(
        "EvidenceSpan", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    verification_status = models.CharField(
        max_length=16,
        choices=[("reported", "reported"), ("verified", "verified"), ("conflicted", "conflicted")],
        default="reported",
    )

    class Meta:
        db_table = "adviser_v2_policy_member"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_policy_member_id_owner_uq"),
        ]


class CustomerPolicyOption(ApprovedModel):
    "One customer-specific selected, declined or unresolved ProductOption decision."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    customer_policy_revision = models.ForeignKey(
        "CustomerPolicyRevision", on_delete=models.PROTECT, related_name="+"
    )
    product_option = models.ForeignKey("ProductOption", on_delete=models.PROTECT, related_name="+")
    selection_status = models.CharField(
        max_length=16,
        choices=[("selected", "selected"), ("declined", "declined"), ("unresolved", "unresolved")],
        default="unresolved",
    )
    evidence_span = models.ForeignKey(
        "EvidenceSpan", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    verification_status = models.CharField(
        max_length=16,
        choices=[("reported", "reported"), ("verified", "verified"), ("conflicted", "conflicted")],
        default="reported",
    )

    class Meta:
        db_table = "adviser_v2_customer_policy_option"
        constraints = [
            models.UniqueConstraint(
                fields=["id", "owner"], name="v2_customer_policy_option_id_owner_uq"
            ),
            models.UniqueConstraint(
                fields=["customer_policy_revision", "product_option"],
                name="v2_customer_policy_option_uq_1",
            ),
        ]


class CustomerPolicyFact(ApprovedModel):
    "One document-backed structured fact about a particular customer's issued policy revision."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    customer_policy_revision = models.ForeignKey(
        "CustomerPolicyRevision", on_delete=models.PROTECT, related_name="+"
    )
    person = models.ForeignKey(
        "Person", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    fact_type = models.CharField(max_length=100)
    value = ValidatedJSONField(contract="CustomerPolicyFactValueV1")
    related_customer_policy = models.ForeignKey(
        "CustomerPolicy", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    evidence_span = models.ForeignKey("EvidenceSpan", on_delete=models.PROTECT, related_name="+")
    verification_status = models.CharField(
        max_length=16,
        choices=[
            ("extracted", "extracted"),
            ("verified", "verified"),
            ("conflicted", "conflicted"),
        ],
        default="extracted",
    )
    supersedes = models.ForeignKey(
        "self", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )

    class Meta:
        db_table = "adviser_v2_customer_policy_fact"
        constraints = [
            models.UniqueConstraint(
                fields=["id", "owner"], name="v2_customer_policy_fact_id_owner_uq"
            ),
            models.UniqueConstraint(
                fields=["supersedes"],
                name="v2_customer_policy_fact_uq_1",
                condition=Q(supersedes__isnull=False),
            ),
        ]


class Quote(ApprovedModel):
    "One immutable, evidence-backed personal insurer quote for an exact customer profile and product selection."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    profile_revision = models.ForeignKey(
        "CustomerProfileRevision", on_delete=models.PROTECT, related_name="+"
    )
    product_variant = models.ForeignKey(
        "ProductVariant", on_delete=models.PROTECT, related_name="+"
    )
    quoted_selection = ValidatedJSONField(contract="AcceptedSelectionV1")
    insurer_quote_reference = EncryptedCharField(max_length=200, null=True, blank=True)
    issued_at = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)
    total = ValidatedJSONField(contract="QuantityV1")
    coverage_term = ValidatedJSONField(contract="TemporalExtentV1")
    price_breakdown = ValidatedJSONField(contract="QuotePriceBreakdownV1")
    payment_schedule = ValidatedJSONField(contract="QuotePaymentScheduleV1")
    source_evidence = models.ForeignKey("EvidenceSpan", on_delete=models.PROTECT, related_name="+")

    class Meta:
        db_table = "adviser_v2_quote"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_quote_id_owner_uq"),
        ]


class ConsentRecord(ApprovedModel):
    "One customer grant for CoverGuide to process account, health or uploaded-document data for buying advice, with optional later revocation."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    person = models.ForeignKey(
        "Person", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    consent_type = models.CharField(
        max_length=22,
        choices=[
            ("privacy_terms", "privacy_terms"),
            ("health_data_processing", "health_data_processing"),
            ("document_processing", "document_processing"),
        ],
    )
    notice_version = models.CharField(max_length=80)
    capture_method = models.CharField(
        max_length=17,
        choices=[
            ("web_checkbox", "web_checkbox"),
            ("conversation", "conversation"),
            ("uploaded_document", "uploaded_document"),
            ("migration", "migration"),
        ],
    )
    status = models.CharField(
        max_length=16,
        choices=[
            ("requested", "requested"),
            ("granted", "granted"),
            ("revoked", "revoked"),
        ],
        default="requested",
    )
    source_message = models.ForeignKey(
        "Message", on_delete=models.PROTECT, related_name="+", null=True, blank=True
    )
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "adviser_v2_consent_record"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_consent_record_id_owner_uq"),
            models.CheckConstraint(
                condition=(~Q(status="revoked") & Q(revoked_at__isnull=True))
                | (Q(status="revoked") & Q(revoked_at__isnull=False)),
                name="v2_consent_record_ck_1",
            ),
        ]


class DeletionRequest(ApprovedModel):
    "One durable customer request to erase an account, conversation, upload or selected disclosure and its derived private copies."

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    scope = ValidatedJSONField(contract="DeletionScopeV1")
    state = models.CharField(
        max_length=16,
        choices=[
            ("pending", "pending"),
            ("running", "running"),
            ("completed", "completed"),
            ("failed", "failed"),
        ],
        default="pending",
    )
    completed_at = models.DateTimeField(null=True, blank=True)
    verification = ValidatedJSONField(contract="DeletionVerificationV1")
    error_code = models.CharField(max_length=100, null=True, blank=True)

    class Meta:
        db_table = "adviser_v2_deletion_request"
        constraints = [
            models.UniqueConstraint(fields=["id", "owner"], name="v2_deletion_request_id_owner_uq"),
            models.CheckConstraint(
                condition=~Q(state="completed") | Q(completed_at__isnull=False),
                name="v2_deletion_request_ck_1",
            ),
            models.CheckConstraint(
                condition=~Q(state="failed") | Q(error_code__isnull=False),
                name="v2_deletion_request_ck_2",
            ),
        ]
