"""Public `/api/v2/` request and response serializers."""

from __future__ import annotations

from typing import Any

from rest_framework import serializers

from .models import Conversation, Message, Turn, TurnRouteBinding


class V2ConversationSerializer(serializers.ModelSerializer[Conversation]):
    profile_revision = serializers.IntegerField(
        source="current_profile_revision.revision", read_only=True, allow_null=True
    )

    class Meta:
        model = Conversation
        fields = [
            "id",
            "title",
            "status",
            "preferred_language",
            "profile_revision",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "profile_revision", "created_at", "updated_at"]


class V2MessageSerializer(serializers.ModelSerializer[Message]):
    comparison_id = serializers.UUIDField(read_only=True, allow_null=True)

    class Meta:
        model = Message
        fields = [
            "id",
            "sequence",
            "role",
            "content",
            "origin",
            "submitted_at",
            "created_at",
            "comparison_id",
        ]


class ConversationPageSerializer(serializers.Serializer[dict[str, Any]]):
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = V2ConversationSerializer(many=True)


class MessagePageSerializer(serializers.Serializer[dict[str, Any]]):
    next = serializers.URLField(allow_null=True)
    previous = serializers.URLField(allow_null=True)
    results = V2MessageSerializer(many=True)


class MessageSubmissionSerializer(serializers.Serializer[dict[str, Any]]):
    request_id = serializers.UUIDField()
    text = serializers.CharField(min_length=1, max_length=20_000, trim_whitespace=False)
    expected_profile_revision = serializers.IntegerField(min_value=1, required=False)


class TurnRouteBindingSerializer(serializers.ModelSerializer[TurnRouteBinding]):
    route_id = serializers.UUIDField(read_only=True)
    qualification_id = serializers.UUIDField(read_only=True)

    class Meta:
        model = TurnRouteBinding
        fields = [
            "role",
            "route_id",
            "qualification_id",
            "requested_model",
            "expected_model",
            "observed_model",
            "endpoint_profile",
            "adapter_version",
            "route_configuration_sha256",
            "schema_sha256",
            "created_at",
        ]


class V2TurnSerializer(serializers.ModelSerializer[Turn]):
    input_message_id = serializers.UUIDField(read_only=True)
    starting_profile_revision = serializers.IntegerField(
        source="starting_profile_revision.revision", read_only=True, allow_null=True
    )
    route_bindings = TurnRouteBindingSerializer(many=True, read_only=True)

    class Meta:
        model = Turn
        fields = [
            "id",
            "request_id",
            "conversation_id",
            "input_message_id",
            "starting_profile_revision",
            "state",
            "deadline",
            "cancelled_at",
            "error_code",
            "route_commitment",
            "route_bindings",
            "created_at",
            "updated_at",
        ]


class ProfileCorrectionSerializer(serializers.Serializer[dict[str, Any]]):
    expected_revision = serializers.IntegerField(min_value=1)
    correction_text = serializers.CharField(min_length=1, max_length=20_000)
    facts = serializers.ListField(child=serializers.DictField(), required=False, default=list)
    requirements = serializers.ListField(
        child=serializers.DictField(), required=False, default=list
    )


class UploadSerializer(serializers.Serializer[dict[str, Any]]):
    file = serializers.FileField()
    kind = serializers.ChoiceField(
        choices=["offer", "quote", "policy_schedule", "endorsement", "member_certificate", "other"]
    )
    source_message_id = serializers.UUIDField(required=False)


class TurnAcceptedSerializer(serializers.Serializer[dict[str, Any]]):
    message_id = serializers.UUIDField()
    turn_id = serializers.UUIDField()
    event_url = serializers.CharField()
    created = serializers.BooleanField(required=False)


class ProfilePersonSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    display_name = serializers.CharField()


class ProfileFactSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    logical_key = serializers.UUIDField()
    fact_type = serializers.CharField()
    value = serializers.JSONField()
    status = serializers.CharField()
    subject_person_id = serializers.UUIDField(allow_null=True)


class ProfileRequirementSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    logical_key = serializers.UUIDField()
    criterion = serializers.CharField()
    operator = serializers.CharField()
    target_value = serializers.JSONField(allow_null=True)
    priority = serializers.CharField()
    scope = serializers.CharField()
    status = serializers.CharField()
    subject_person_id = serializers.UUIDField(allow_null=True)


class CurrentProfileSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    revision = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    people = ProfilePersonSerializer(many=True)
    facts = ProfileFactSerializer(many=True)
    requirements = ProfileRequirementSerializer(many=True)


class RequirementMatchSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    requirement_id = serializers.UUIDField()
    criterion = serializers.CharField()
    priority = serializers.CharField()
    outcome = serializers.CharField()
    comparison_value = serializers.JSONField(allow_null=True)


class InformationNeedSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    need_kind = serializers.CharField()
    information_key = serializers.CharField()
    reason = serializers.CharField()
    priority = serializers.CharField()
    status = serializers.CharField()


class ComparisonCitationSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    evidence_span_id = serializers.UUIDField()
    policy_rule_id = serializers.UUIDField(allow_null=True)
    role = serializers.CharField()
    quote = serializers.CharField()
    section_label = serializers.CharField(allow_null=True)
    page = serializers.IntegerField(allow_null=True)
    document_version_id = serializers.UUIDField(allow_null=True)
    locator = serializers.JSONField()


class EvidenceGapSerializer(serializers.Serializer[dict[str, Any]]):
    requirement_id = serializers.UUIDField()
    criterion = serializers.CharField()
    outcome = serializers.ChoiceField(choices=["unknown", "partly_meets"])


class ProductRestrictionSerializer(serializers.Serializer[dict[str, Any]]):
    statement_id = serializers.UUIDField()
    text = serializers.CharField()
    citations = ComparisonCitationSerializer(many=True)


class ComparedProductSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    product_variant_id = serializers.UUIDField()
    product = serializers.CharField()
    insurer = serializers.CharField()
    uin = serializers.CharField(allow_null=True)
    variant = serializers.CharField()
    evaluated_selection = serializers.JSONField()
    quote_id = serializers.UUIDField(allow_null=True)
    criteria = RequirementMatchSerializer(many=True)
    evidence_gaps = EvidenceGapSerializer(many=True)
    restrictions = ProductRestrictionSerializer(many=True)
    evidence = ComparisonCitationSerializer(many=True)


class ComparisonStatementSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    ordinal = serializers.IntegerField()
    text = serializers.CharField()
    statement_type = serializers.CharField()
    critical = serializers.BooleanField()
    support_status = serializers.CharField()
    comparison_assessment_id = serializers.UUIDField(allow_null=True)
    citations = ComparisonCitationSerializer(many=True)


class ComparisonDetailSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    turn_id = serializers.UUIDField()
    outcome = serializers.CharField()
    profile_revision = serializers.IntegerField()
    knowledge_release_id = serializers.UUIDField()
    catalogue_limit = serializers.IntegerField()
    comparison_label = serializers.CharField()
    created_at = serializers.DateTimeField()
    products = ComparedProductSerializer(many=True)
    information_needs = InformationNeedSerializer(many=True)
    statements = ComparisonStatementSerializer(many=True)


class EvidenceDetailSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    document_version_id = serializers.UUIDField(allow_null=True)
    customer_upload_id = serializers.UUIDField(allow_null=True)
    page = serializers.IntegerField(allow_null=True)
    section_label = serializers.CharField(allow_null=True)
    quote = serializers.CharField()
    context = serializers.JSONField()  # type: ignore[assignment]
    verification = serializers.CharField()
    locator = serializers.JSONField()


class UploadAcceptedSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    job_id = serializers.UUIDField()
    kind = serializers.CharField()
    review_status = serializers.CharField()


class CatalogueProductSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    name = serializers.CharField()
    insurer = serializers.CharField()
    uin = serializers.CharField(allow_null=True)
    version_id = serializers.UUIDField(allow_null=True)
    publication_status = serializers.CharField()
    document_count = serializers.IntegerField()
    required_documents = serializers.IntegerField()
    rule_count = serializers.IntegerField()
    covered_inventory_categories = serializers.ListField(child=serializers.CharField())
    missing_inventory_categories = serializers.ListField(child=serializers.CharField())
    unresolved_material_jobs = serializers.IntegerField()
    included_in_current_release = serializers.BooleanField()


class KnowledgeReleaseSerializer(serializers.Serializer[dict[str, Any]]):
    id = serializers.UUIDField()
    number = serializers.IntegerField()
    state = serializers.CharField()
    label = serializers.CharField()  # type: ignore[assignment]
    published_at = serializers.DateTimeField(allow_null=True)
    manifest_sha256 = serializers.CharField()


class InteractiveRouteStatusSerializer(serializers.Serializer[dict[str, Any]]):
    role = serializers.CharField()
    qualified = serializers.BooleanField()
    error_code = serializers.CharField(allow_null=True)
    requested_model = serializers.CharField()
    expected_model = serializers.CharField(allow_null=True)
    endpoint_profile = serializers.CharField(allow_null=True)
    adapter_version = serializers.CharField(allow_null=True)
    route_key = serializers.CharField(allow_null=True)
    configuration_sha256 = serializers.CharField(allow_null=True)
    schema_sha256 = serializers.CharField(allow_null=True)
    qualification_id = serializers.UUIDField(allow_null=True)


class CatalogueReadinessSerializer(serializers.Serializer[dict[str, Any]]):
    catalogue_limit = serializers.IntegerField()
    comparison_label = serializers.CharField()
    warning = serializers.CharField()
    channel = serializers.CharField()
    generation = serializers.IntegerField()
    release = KnowledgeReleaseSerializer(allow_null=True)
    ready = serializers.BooleanField()
    incomplete_comparison = serializers.BooleanField()
    products = CatalogueProductSerializer(many=True)
    interactive_routes = InteractiveRouteStatusSerializer(many=True)
    blocking_reason = serializers.CharField(allow_null=True)
