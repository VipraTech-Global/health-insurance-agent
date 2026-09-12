from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    AnswerArtifact,
    CatalogueListing,
    Conversation,
    EvidenceSpan,
    Message,
    ProfileRevision,
    Turn,
)


class ConversationSerializer(serializers.ModelSerializer[Conversation]):
    profile_revision = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = ["id", "title", "created_at", "updated_at", "profile_revision"]
        read_only_fields = ["id", "created_at", "updated_at", "profile_revision"]

    def get_profile_revision(self, obj: Conversation) -> int | None:
        return obj.current_profile.revision if obj.current_profile else None


class MessageSerializer(serializers.ModelSerializer[Message]):
    answer = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = ["id", "role", "content", "origin", "created_at", "answer"]

    @extend_schema_field(serializers.DictField(allow_null=True))
    def get_answer(self, obj: Message) -> dict[str, object] | None:
        if obj.answer_id is None:
            return None
        return dict(AnswerSerializer(obj.answer).data)


class ProfileSerializer(serializers.ModelSerializer[ProfileRevision]):
    class Meta:
        model = ProfileRevision
        fields = ["id", "revision", "data", "field_provenance", "confirmed_at", "created_at"]


class TurnSerializer(serializers.ModelSerializer[Turn]):
    attempts = serializers.SerializerMethodField()

    class Meta:
        model = Turn
        fields = [
            "id",
            "request_id",
            "input_text",
            "operation",
            "expected_profile_revision",
            "created_at",
            "attempts",
        ]

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_attempts(self, obj: Turn) -> list[dict[str, object]]:
        return [
            {"id": str(a.id), "status": a.status, "terminal_code": a.terminal_code}
            for a in obj.attempts.all()
        ]


class AnswerSerializer(serializers.ModelSerializer[AnswerArtifact]):
    claims = serializers.SerializerMethodField()

    class Meta:
        model = AnswerArtifact
        fields = [
            "id",
            "outcome",
            "blocks",
            "verification_status",
            "profile_revision",
            "corpus_release",
            "created_at",
            "claims",
        ]

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_claims(self, obj: AnswerArtifact) -> list[dict[str, object]]:
        claims: list[dict[str, object]] = []
        for claim in obj.claims.all():
            bundles = list(claim.evidence_bundles.all())
            citations: list[dict[str, object]] = []
            for bundle in bundles:
                links = bundle.evidencebundlespan_set.all()
                for link in links:
                    span = link.span
                    citations.append(
                        {
                            "documentId": str(span.page.extraction_revision.document_version_id),
                            "page": span.page.physical_index + 1,
                            "quote": span.quote,
                            "label": (
                                f"{bundle.label} · PDF page {span.page.physical_index + 1} · "
                                f"reference lines {span.start_line}–{span.end_line}"
                            ),
                            "rectangles": span.geometry,
                            "role": link.role,
                            "order": link.order,
                        }
                    )
            claims.append(
                {
                    "id": str(claim.id),
                    "type": claim.claim_type,
                    "text": claim.display_text,
                    "verification": claim.verification_result,
                    "evidence_bundle_ids": [str(bundle.id) for bundle in bundles],
                    "citations": citations,
                }
            )
        return claims


class EvidenceSpanSerializer(serializers.ModelSerializer[EvidenceSpan]):
    document_id = serializers.UUIDField(source="page.extraction_revision.document_version_id")
    pdf_page = serializers.SerializerMethodField()

    class Meta:
        model = EvidenceSpan
        fields = [
            "id",
            "document_id",
            "pdf_page",
            "start_line",
            "end_line",
            "quote",
            "geometry",
            "source_word_ids",
        ]

    def get_pdf_page(self, obj: EvidenceSpan) -> int:
        return obj.page.physical_index + 1


class CoverageSerializer(serializers.ModelSerializer[CatalogueListing]):
    insurer = serializers.CharField(source="insurer.name", allow_null=True)

    class Meta:
        model = CatalogueListing
        fields = [
            "id",
            "ditto_path",
            "displayed_name",
            "insurer",
            "status",
            "status_reason",
            "last_observed_at",
        ]
