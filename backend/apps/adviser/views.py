import logging
import uuid
from pathlib import Path
from typing import cast

from config.lifecycle import runtime
from django.conf import settings
from django.core.cache import cache
from django.db import DatabaseError
from django.db.models import Count
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import status
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    AnswerArtifact,
    CatalogueListing,
    Conversation,
    CorpusRelease,
    DocumentVersion,
    EvidenceBundle,
    EvidenceSpan,
    Message,
    ProfileRevision,
    RecommendationSnapshot,
    RouteConfiguration,
    Turn,
    TurnAttempt,
)
from .serializers import (
    AnswerSerializer,
    ConversationSerializer,
    MessageSerializer,
    ProfileSerializer,
    TurnSerializer,
)
from .services import (
    ConflictError,
    cancel_attempt,
    confirm_profile,
    create_conversation,
    retry_turn,
    revise_profile,
)
from .source_maps import DocumentValidationError, verified_source_path

logger = logging.getLogger(__name__)


def conflict(message: str) -> Response:
    return Response(
        {"error": {"code": "conflict", "message": message}}, status=status.HTTP_409_CONFLICT
    )


def _user_id(request: Request) -> uuid.UUID:
    """Return the authenticated actor established by DRF permissions."""
    return cast(uuid.UUID, request.user.pk)


@extend_schema_view(
    get=extend_schema(operation_id="conversation_list"),
    post=extend_schema(operation_id="conversation_create"),
)
class ConversationList(APIView):
    serializer_class = ConversationSerializer

    def get(self, request: Request) -> Response:
        queryset = (
            Conversation.objects.filter(owner_id=_user_id(request))
            .select_related("current_profile")
            .order_by("-updated_at")
        )
        paginator = CursorPagination()
        paginator.ordering = "-created_at"
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(ConversationSerializer(page, many=True).data)

    def post(self, request: Request) -> Response:
        conversation = create_conversation(
            _user_id(request), str(request.data.get("title", "New conversation"))
        )
        return Response(ConversationSerializer(conversation).data, status=status.HTTP_201_CREATED)


class ConversationDetail(APIView):
    serializer_class = ConversationSerializer

    def get(self, request: Request, pk: uuid.UUID) -> Response:
        item = get_object_or_404(
            Conversation.objects.select_related("current_profile"),
            pk=pk,
            owner_id=_user_id(request),
        )
        return Response(ConversationSerializer(item).data)

    def delete(self, request: Request, pk: uuid.UUID) -> Response:
        deleted, _ = Conversation.objects.filter(pk=pk, owner_id=_user_id(request)).delete()
        if not deleted:
            return Response(
                {"error": {"code": "not_found", "message": "Conversation not found."}}, status=404
            )
        return Response(status=204)


class ConversationMessages(APIView):
    serializer_class = MessageSerializer

    def get(self, request: Request, pk: uuid.UUID) -> Response:
        queryset = (
            Message.objects.filter(conversation_id=pk, conversation__owner_id=_user_id(request))
            .select_related("answer")
            .prefetch_related(
                "answer__claims__evidence_bundles__evidencebundlespan_set__span__page__extraction_revision__document_version"
            )
            .order_by("created_at")
        )
        paginator = CursorPagination()
        paginator.ordering = "created_at"
        page = paginator.paginate_queryset(queryset, request, view=self)
        return paginator.get_paginated_response(MessageSerializer(page, many=True).data)


class ConversationProfile(APIView):
    serializer_class = ProfileSerializer

    def get(self, request: Request, pk: uuid.UUID) -> Response:
        profile = get_object_or_404(
            ProfileRevision,
            conversation_id=pk,
            conversation__owner_id=_user_id(request),
            current_for__isnull=False,
        )
        return Response(ProfileSerializer(profile).data)

    def patch(self, request: Request, pk: uuid.UUID) -> Response:
        expected = request.data.get("expected_revision")
        patch = request.data.get("patch")
        if not isinstance(expected, int) or not isinstance(patch, dict):
            return Response(
                {
                    "error": {
                        "code": "invalid_request",
                        "message": "expected_revision and object patch are required.",
                    }
                },
                status=400,
            )
        try:
            profile = revise_profile(_user_id(request), pk, expected, patch)
        except ConflictError as exc:
            return conflict(str(exc))
        return Response(ProfileSerializer(profile).data)


class ConfirmProfile(APIView):
    serializer_class = ProfileSerializer

    def post(self, request: Request, pk: uuid.UUID) -> Response:
        expected = request.data.get("expected_revision")
        if not isinstance(expected, int):
            return Response(
                {"error": {"code": "invalid_request", "message": "expected_revision is required."}},
                status=400,
            )
        try:
            profile = confirm_profile(_user_id(request), pk, expected)
        except ConflictError as exc:
            return conflict(str(exc))
        return Response(ProfileSerializer(profile).data)


class TurnDetail(APIView):
    serializer_class = TurnSerializer

    def get(self, request: Request, pk: uuid.UUID) -> Response:
        turn = get_object_or_404(
            Turn.objects.prefetch_related("attempts"),
            pk=pk,
            conversation__owner_id=_user_id(request),
        )
        return Response(TurnSerializer(turn).data)


class CancelTurn(APIView):
    serializer_class = TurnSerializer

    def post(self, request: Request, pk: uuid.UUID) -> Response:
        attempt = (
            TurnAttempt.objects.filter(turn_id=pk, turn__conversation__owner_id=_user_id(request))
            .order_by("-created_at")
            .first()
        )
        if attempt is None:
            return Response(
                {"error": {"code": "not_found", "message": "Turn not found."}}, status=404
            )
        if not cancel_attempt(_user_id(request), attempt.id):
            return conflict("The attempt is already terminal.")
        return Response({"attempt_id": str(attempt.id), "status": "cancelled"})


class RetryTurn(APIView):
    serializer_class = TurnSerializer

    def post(self, request: Request, pk: uuid.UUID) -> Response:
        try:
            attempt = retry_turn(_user_id(request), pk)
        except (ConflictError, Turn.DoesNotExist) as exc:
            return conflict(str(exc))
        from .services import mark_running, publish_controlled_answer

        if not mark_running(_user_id(request), attempt.id):
            return conflict("The retry could not be started.")
        answer = publish_controlled_answer(_user_id(request), attempt.id)
        return Response({"attempt_id": str(attempt.id), "answer": answer})


class AnswerDetail(APIView):
    serializer_class = AnswerSerializer

    def get(self, request: Request, pk: uuid.UUID) -> Response:
        answer = get_object_or_404(
            AnswerArtifact.objects.prefetch_related(
                "claims__evidence_bundles__evidencebundlespan_set__span__page__extraction_revision__document_version"
            ),
            pk=pk,
            attempt__turn__conversation__owner_id=_user_id(request),
        )
        return Response(AnswerSerializer(answer).data)


class RecommendationDetail(APIView):
    serializer_class = AnswerSerializer

    def get(self, request: Request, pk: uuid.UUID) -> Response:
        item = get_object_or_404(RecommendationSnapshot, pk=pk, owner_id=_user_id(request))
        return Response(
            {
                "id": str(item.id),
                "profile_revision": item.profile_revision,
                "corpus_release": str(item.corpus_release_id),
                "candidate_results": item.candidate_results,
                "rankings": item.rankings,
                "calculations": item.calculations,
                "rule_version": item.rule_version,
            }
        )


class EvidenceDetail(APIView):
    serializer_class = AnswerSerializer

    def get(self, request: Request, pk: uuid.UUID) -> Response:
        span = get_object_or_404(
            EvidenceSpan.objects.select_related("page__extraction_revision__document_version"),
            pk=pk,
        )
        page = span.page
        return Response(
            {
                "id": str(span.id),
                "document_id": str(page.extraction_revision.document_version_id),
                "physical_page": page.physical_index + 1,
                "printed_label": page.printed_label,
                "reference_lines": [span.start_line, span.end_line],
                "quote": span.quote,
                "word_ids": span.source_word_ids,
                "geometry": span.geometry,
                "rotation": page.rotation,
            }
        )


class DocumentDetail(APIView):
    serializer_class = AnswerSerializer

    def get(self, request: Request, pk: uuid.UUID) -> Response:
        document = get_object_or_404(DocumentVersion.objects.select_related("blob"), pk=pk)
        return Response(
            {
                "id": str(document.id),
                "identity": document.identity,
                "type": document.document_type,
                "language": document.language,
                "effective_from": document.effective_from,
                "sha256": document.blob.sha256,
                "size": document.blob.byte_size,
            }
        )


class DocumentFile(APIView):
    serializer_class = AnswerSerializer

    def get(self, request: Request, pk: uuid.UUID) -> HttpResponse | FileResponse | Response:
        document = get_object_or_404(DocumentVersion.objects.select_related("blob"), pk=pk)
        try:
            path = verified_source_path(document.blob)
        except DocumentValidationError:
            return Response(
                {
                    "error": {
                        "code": "source_unavailable",
                        "message": "The preserved source file is unavailable.",
                    }
                },
                status=404,
            )
        response: HttpResponse | FileResponse
        if settings.USE_X_ACCEL_REDIRECT:
            response = HttpResponse(content_type=document.blob.media_type)
            response["X-Accel-Redirect"] = f"/_protected/{document.blob.stored_path}"
        else:
            response = FileResponse(path.open("rb"), content_type=document.blob.media_type)
        response["Cache-Control"] = "private, no-store"
        response["Accept-Ranges"] = "bytes"
        response["Content-Disposition"] = f'inline; filename="{document.blob.sha256}.pdf"'
        return response


class CoverageView(APIView):
    serializer_class = AnswerSerializer

    def get(self, request: Request) -> Response:
        counts = {
            row["status"]: row["count"]
            for row in CatalogueListing.objects.values("status").annotate(count=Count("id"))
        }
        last = (
            CatalogueListing.objects.order_by("-last_observed_at")
            .values_list("last_observed_at", flat=True)
            .first()
        )
        total = sum(counts.values())
        active_test_plan_ids = {
            str(release.manifest.get("plan_version_id"))
            for release in CorpusRelease.objects.filter(activated_at__isnull=False, is_current=True)
            if release.manifest.get("test_only") and release.manifest.get("plan_version_id")
        }
        sample_bundle = (
            EvidenceBundle.objects.filter(review_state="verified")
            .prefetch_related("spans__page__extraction_revision__document_version")
            .order_by("-created_at")
            .first()
        )
        if sample_bundle is None:
            sample_bundle = (
                EvidenceBundle.objects.filter(review_state="pending")
                .prefetch_related("spans__page__extraction_revision__document_version")
                .order_by("-created_at")
                .first()
            )
        sample = None
        if sample_bundle:
            span = sample_bundle.spans.first()
            if span:
                sample = {
                    "documentId": str(span.page.extraction_revision.document_version_id),
                    "page": span.page.physical_index + 1,
                    "quote": span.quote,
                    "label": (
                        f"{sample_bundle.label} · PDF page "
                        f"{span.page.physical_index + 1} · reference lines "
                        f"{span.start_line}–{span.end_line}"
                    ),
                    "rectangles": span.geometry,
                    "reviewState": sample_bundle.review_state,
                }
        return Response(
            {
                "total_discovered": total,
                "counts": counts,
                "active_for_recommendation": counts.get(CatalogueListing.Status.ACTIVE, 0),
                "active_for_test": len(active_test_plan_ids),
                "last_successful_source_check": last,
                "as_of": timezone.now(),
                "sample_pending_evidence": sample,
            }
        )


class ReadinessView(APIView):
    serializer_class = AnswerSerializer
    permission_classes = []

    def get(self, request: Request) -> Response:
        from django.db import connection

        database_ready = False
        active_corpus = False
        qualified_route = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                database_ready = cursor.fetchone() == (1,)
            if database_ready:
                active_corpus = CorpusRelease.objects.filter(
                    activated_at__isnull=False, is_current=True
                ).exists()
                qualified_route = RouteConfiguration.objects.filter(
                    qualification_state="qualified"
                ).exists()
        except DatabaseError as exc:
            logger.warning("Readiness database check failed: %s", exc.__class__.__name__)
            database_ready = False
        try:
            reconciler_ready = cache.get("adviser:turn-reconciler-health") == "ok"
        except Exception as exc:
            logger.warning("Readiness cache check failed: %s", exc.__class__.__name__)
            reconciler_ready = False
        checks = {
            "database": database_ready,
            "source_storage": Path(settings.DATA_ROOT).is_dir(),
            "runtime": runtime.ready,
            "turn_reconciler": reconciler_ready,
            "active_corpus": active_corpus,
            "qualified_route": qualified_route,
        }
        ready = (
            checks["database"]
            and checks["source_storage"]
            and checks["runtime"]
            and checks["turn_reconciler"]
        )
        return Response(
            {"ready": ready, "checks": checks},
            status=200 if ready else 503,
        )
