"""Session-authenticated `/api/v2/` HTTP and durable SSE interfaces."""

from __future__ import annotations

import hashlib
import json
import logging
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any, cast

from django.db import transaction
from django.http import HttpResponse, StreamingHttpResponse
from django.shortcuts import get_object_or_404
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.pagination import CursorPagination
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Conversation,
    CustomerProfileRevision,
    CustomerUploadedDocument,
    DocumentVersion,
    EvidenceSpan,
    Message,
    OriginalFile,
    SourceCapture,
    Turn,
)
from .pipeline import enqueue_stage
from .selectors.catalogue import catalogue_readiness
from .selectors.customer import (
    conversations_for,
    current_profile_payload,
    events_after,
    messages_for,
    turn_for,
)
from .selectors.recommendations import recommendation_payload
from .serializers import (
    CatalogueReadinessSerializer,
    ConversationPageSerializer,
    CurrentProfileSerializer,
    EvidenceDetailSerializer,
    MessagePageSerializer,
    MessageSubmissionSerializer,
    ProfileCorrectionSerializer,
    RecommendationDetailSerializer,
    TurnAcceptedSerializer,
    UploadAcceptedSerializer,
    UploadSerializer,
    V2ConversationSerializer,
    V2MessageSerializer,
    V2TurnSerializer,
)
from .services.customer import ConflictError, cancel_turn, create_conversation, retry_turn
from .services.customer import safely_submit_message as submit_message
from .services.outbox import dispatch_processing_outbox, dispatch_turn_outbox
from .services.profile import correct_profile
from .storage import read_private, read_public, store_private

logger = logging.getLogger(__name__)


def _user_id(request: Request) -> uuid.UUID:
    return cast(uuid.UUID, request.user.pk)


def _error(code: str, message: str, response_status: int) -> Response:
    return Response({"error": {"code": code, "message": message}}, status=response_status)


def _schedule_turn(turn_id: uuid.UUID) -> None:
    try:
        dispatch_turn_outbox(turn_id)
    except Exception:
        logger.exception("Could not dispatch the v2 turn outbox; periodic delivery remains active")


def _schedule_document(job_id: uuid.UUID) -> None:
    try:
        dispatch_processing_outbox(job_id)
    except Exception:
        logger.exception("Could not dispatch the document outbox; periodic delivery remains active")


class PrivateNoStoreAPIView(APIView):
    def finalize_response(self, request: Request, response: Any, *args: Any, **kwargs: Any) -> Any:
        result = super().finalize_response(request, response, *args, **kwargs)
        result["Cache-Control"] = "private, no-store"
        result["Pragma"] = "no-cache"
        return result


class ConversationList(PrivateNoStoreAPIView):
    @extend_schema(responses=ConversationPageSerializer, operation_id="v2_conversation_list")
    def get(self, request: Request) -> Response:
        paginator = CursorPagination()
        paginator.ordering = "-updated_at"
        page = paginator.paginate_queryset(conversations_for(_user_id(request)), request, view=self)
        return paginator.get_paginated_response(V2ConversationSerializer(page, many=True).data)

    @extend_schema(
        request=V2ConversationSerializer,
        responses={status.HTTP_201_CREATED: V2ConversationSerializer},
        operation_id="v2_conversation_create",
    )
    def post(self, request: Request) -> Response:
        serializer = V2ConversationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = create_conversation(
            _user_id(request),
            title=serializer.validated_data.get("title", "Insurance planning"),
        )
        return Response(V2ConversationSerializer(item).data, status=status.HTTP_201_CREATED)


class ConversationDetail(PrivateNoStoreAPIView):
    @extend_schema(responses=V2ConversationSerializer, operation_id="v2_conversation_retrieve")
    def get(self, request: Request, pk: uuid.UUID) -> Response:
        item = get_object_or_404(
            Conversation.objects.select_related("current_profile_revision"),
            pk=pk,
            owner_id=_user_id(request),
        )
        return Response(V2ConversationSerializer(item).data)


class ConversationMessages(PrivateNoStoreAPIView):
    @extend_schema(responses=MessagePageSerializer, operation_id="v2_message_list")
    def get(self, request: Request, pk: uuid.UUID) -> Response:
        get_object_or_404(Conversation, pk=pk, owner_id=_user_id(request))
        paginator = CursorPagination()
        paginator.ordering = "sequence"
        page = paginator.paginate_queryset(messages_for(_user_id(request), pk), request, view=self)
        return paginator.get_paginated_response(V2MessageSerializer(page, many=True).data)

    @extend_schema(
        request=MessageSubmissionSerializer,
        responses={status.HTTP_202_ACCEPTED: TurnAcceptedSerializer},
        operation_id="v2_message_submit",
    )
    def post(self, request: Request, pk: uuid.UUID) -> Response:
        serializer = MessageSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            submitted = submit_message(
                _user_id(request),
                pk,
                request_id=serializer.validated_data["request_id"],
                text=serializer.validated_data["text"],
                expected_profile_revision=serializer.validated_data.get(
                    "expected_profile_revision"
                ),
            )
        except Conversation.DoesNotExist:
            return _error("not_found", "Conversation not found.", status.HTTP_404_NOT_FOUND)
        except ConflictError as exc:
            return _error("conflict", str(exc), status.HTTP_409_CONFLICT)
        if submitted.created:
            transaction.on_commit(lambda: _schedule_turn(submitted.turn.id))
        return Response(
            {
                "message_id": str(submitted.message.id),
                "turn_id": str(submitted.turn.id),
                "event_url": f"/api/v2/turns/{submitted.turn.id}/events/",
                "created": submitted.created,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ConversationProfile(PrivateNoStoreAPIView):
    @extend_schema(responses=CurrentProfileSerializer, operation_id="v2_profile_retrieve")
    def get(self, request: Request, pk: uuid.UUID) -> Response:
        try:
            return Response(current_profile_payload(_user_id(request), pk))
        except (Conversation.DoesNotExist, CustomerProfileRevision.DoesNotExist):
            return _error("not_found", "Customer profile not found.", status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=ProfileCorrectionSerializer,
        responses=CurrentProfileSerializer,
        operation_id="v2_profile_correct",
    )
    def patch(self, request: Request, pk: uuid.UUID) -> Response:
        serializer = ProfileCorrectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            correct_profile(
                _user_id(request),
                pk,
                expected_revision=serializer.validated_data["expected_revision"],
                correction_text=serializer.validated_data["correction_text"],
                facts=serializer.validated_data["facts"],
                requirements=serializer.validated_data["requirements"],
            )
            return Response(current_profile_payload(_user_id(request), pk))
        except Conversation.DoesNotExist:
            return _error("not_found", "Conversation not found.", status.HTTP_404_NOT_FOUND)
        except ConflictError as exc:
            return _error("conflict", str(exc), status.HTTP_409_CONFLICT)
        except ValueError as exc:
            return _error("invalid_correction", str(exc), status.HTTP_400_BAD_REQUEST)


class TurnDetail(PrivateNoStoreAPIView):
    @extend_schema(responses=V2TurnSerializer, operation_id="v2_turn_retrieve")
    def get(self, request: Request, pk: uuid.UUID) -> Response:
        try:
            item = turn_for(_user_id(request), pk)
        except Turn.DoesNotExist:
            return _error("not_found", "Turn not found.", status.HTTP_404_NOT_FOUND)
        return Response(V2TurnSerializer(item).data)


class TurnCancel(PrivateNoStoreAPIView):
    @extend_schema(request=None, responses=V2TurnSerializer, operation_id="v2_turn_cancel")
    def post(self, request: Request, pk: uuid.UUID) -> Response:
        try:
            item = cancel_turn(_user_id(request), pk)
        except Turn.DoesNotExist:
            return _error("not_found", "Turn not found.", status.HTTP_404_NOT_FOUND)
        except ConflictError as exc:
            return _error("conflict", str(exc), status.HTTP_409_CONFLICT)
        return Response(V2TurnSerializer(item).data)


class TurnRetry(PrivateNoStoreAPIView):
    @extend_schema(
        request=None,
        responses={status.HTTP_202_ACCEPTED: TurnAcceptedSerializer},
        operation_id="v2_turn_retry",
    )
    def post(self, request: Request, pk: uuid.UUID) -> Response:
        try:
            submitted = retry_turn(_user_id(request), pk)
        except Turn.DoesNotExist:
            return _error("not_found", "Turn not found.", status.HTTP_404_NOT_FOUND)
        except ConflictError as exc:
            return _error("conflict", str(exc), status.HTTP_409_CONFLICT)
        transaction.on_commit(lambda: _schedule_turn(submitted.turn.id))
        return Response(
            {
                "message_id": str(submitted.message.id),
                "turn_id": str(submitted.turn.id),
                "event_url": f"/api/v2/turns/{submitted.turn.id}/events/",
            },
            status=status.HTTP_202_ACCEPTED,
        )


_SSE_NAMES = {
    "queued": "turn.accepted",
    "started": "turn.started",
    "progress": "turn.progress",
    "clarification": "clarification.required",
    "recommendation": "recommendation.completed",
    "cancelled": "turn.cancelled",
    "failed": "turn.failed",
    "stale": "turn.stale",
}


def _sse(event: Any) -> bytes:
    body = json.dumps(event.payload, separators=(",", ":"), default=str)
    return f"id: {event.sequence}\nevent: {_SSE_NAMES[event.event_type]}\ndata: {body}\n\n".encode()


class TurnEvents(PrivateNoStoreAPIView):
    @extend_schema(
        responses={(200, "text/event-stream"): OpenApiResponse(description="Durable SSE events")},
        operation_id="v2_turn_events",
    )
    def get(self, request: Request, pk: uuid.UUID) -> StreamingHttpResponse | Response:
        owner_id = _user_id(request)
        try:
            turn_for(owner_id, pk)
        except Turn.DoesNotExist:
            return _error("not_found", "Turn not found.", status.HTTP_404_NOT_FOUND)
        try:
            after = max(0, int(request.query_params.get("after_sequence", "0")))
            timeout = min(30.0, max(0.0, float(request.query_params.get("timeout", "15"))))
        except ValueError:
            return _error(
                "invalid_cursor", "Event cursor must be numeric.", status.HTTP_400_BAD_REQUEST
            )

        def stream() -> Iterator[bytes]:
            cursor = after
            end = time.monotonic() + timeout
            yield b": coverguide-v2\n\n"
            while True:
                found = list(events_after(owner_id, pk, cursor))
                for event in found:
                    cursor = event.sequence
                    yield _sse(event)
                current = Turn.objects.only("state").get(pk=pk, owner_id=owner_id)
                if current.state in {"completed", "failed", "cancelled", "stale"}:
                    break
                if time.monotonic() >= end:
                    yield b": heartbeat\n\n"
                    break
                time.sleep(0.25)

        response = StreamingHttpResponse(stream(), content_type="text/event-stream")
        response["Cache-Control"] = "private, no-store"
        response["X-Accel-Buffering"] = "no"
        return response


class RecommendationDetail(PrivateNoStoreAPIView):
    @extend_schema(
        responses=RecommendationDetailSerializer,
        operation_id="v2_recommendation_retrieve",
    )
    def get(self, request: Request, pk: uuid.UUID) -> Response:
        from .models import Recommendation

        try:
            return Response(recommendation_payload(_user_id(request), pk))
        except Recommendation.DoesNotExist:
            return _error("not_found", "Recommendation not found.", status.HTTP_404_NOT_FOUND)


class EvidenceDetail(PrivateNoStoreAPIView):
    @extend_schema(responses=EvidenceDetailSerializer, operation_id="v2_evidence_retrieve")
    def get(self, request: Request, pk: uuid.UUID) -> Response:
        span = get_object_or_404(
            EvidenceSpan.objects.select_related(
                "page__original_file",
                "source_capture__document_version",
                "customer_uploaded_document",
            ),
            pk=pk,
        )
        customer_document = span.customer_uploaded_document
        if customer_document is not None and customer_document.owner_id != _user_id(request):
            return _error("not_found", "Evidence not found.", status.HTTP_404_NOT_FOUND)
        capture = span.source_capture
        page = span.page
        return Response(
            {
                "id": str(span.id),
                "document_version_id": (
                    str(capture.document_version_id)
                    if capture is not None and capture.document_version_id
                    else None
                ),
                "customer_upload_id": (
                    str(span.customer_uploaded_document_id)
                    if span.customer_uploaded_document_id
                    else None
                ),
                "page": page.page_number if page is not None else None,
                "section_label": span.section_label,
                "quote": span.quote,
                "context": span.context,
                "verification": span.verification,
                "locator": span.locator,
            }
        )


def _ranged_response(payload: bytes, request: Request, media_type: str) -> HttpResponse:
    range_header = request.META.get("HTTP_RANGE")
    headers = {"Accept-Ranges": "bytes", "Cache-Control": "private, no-store"}
    if not range_header:
        response = HttpResponse(payload, content_type=media_type, headers=headers)
        response["Content-Length"] = str(len(payload))
        return response
    try:
        unit, requested = range_header.split("=", 1)
        start_text, end_text = requested.split("-", 1)
        if unit != "bytes" or "," in requested:
            raise ValueError
        if start_text:
            start = int(start_text)
            requested_end = int(end_text) if end_text else len(payload) - 1
            if start < 0 or start >= len(payload) or requested_end < start:
                raise ValueError
            end = min(requested_end, len(payload) - 1)
        else:
            suffix = int(end_text)
            if suffix <= 0:
                raise ValueError
            start = max(0, len(payload) - suffix)
            end = len(payload) - 1
        if start < 0 or end < start:
            raise ValueError
    except (ValueError, TypeError):
        return HttpResponse(
            status=416,
            headers={**headers, "Content-Range": f"bytes */{len(payload)}"},
        )
    part = payload[start : end + 1]
    response = HttpResponse(part, status=206, content_type=media_type, headers=headers)
    response["Content-Range"] = f"bytes {start}-{end}/{len(payload)}"
    response["Content-Length"] = str(len(part))
    return response


class DocumentFile(PrivateNoStoreAPIView):
    @extend_schema(
        responses={(200, "application/pdf"): OpenApiTypes.BINARY},
        operation_id="v2_document_file_retrieve",
    )
    def get(self, request: Request, pk: uuid.UUID) -> HttpResponse | Response:
        get_object_or_404(DocumentVersion, pk=pk)
        capture = (
            SourceCapture.objects.filter(
                document_version_id=pk, status="captured", original_file__availability="available"
            )
            .select_related("original_file")
            .order_by("-completed_at")
            .first()
        )
        if capture is None or capture.original_file is None:
            return _error("not_found", "Document bytes are unavailable.", status.HTTP_404_NOT_FOUND)
        payload = read_public(capture.original_file.storage_key, capture.original_file.sha256)
        return _ranged_response(payload, request, capture.original_file.media_type)


class CustomerUploadList(PrivateNoStoreAPIView):
    @extend_schema(
        request=UploadSerializer,
        responses={status.HTTP_202_ACCEPTED: UploadAcceptedSerializer},
        operation_id="v2_customer_upload",
    )
    @transaction.atomic
    def post(self, request: Request, conversation_id: uuid.UUID) -> Response:
        conversation = get_object_or_404(
            Conversation, pk=conversation_id, owner_id=_user_id(request), status="open"
        )
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded = serializer.validated_data["file"]
        if uploaded.size > 20 * 1024 * 1024:
            return _error("file_too_large", "Uploads are limited to 20 MiB.", 413)
        payload = uploaded.read()
        if not payload.startswith(b"%PDF-"):
            return _error(
                "unsupported_file", "Only PDF quote or schedule uploads are accepted.", 400
            )
        owner_id = _user_id(request)
        plaintext_sha = hashlib.sha256(payload).hexdigest()
        original = OriginalFile.objects.filter(owner_id=owner_id, sha256=plaintext_sha).first()
        if original is None:
            stored = store_private(owner_id, "customer-document", payload)
            original = OriginalFile.objects.create(
                owner_id=owner_id,
                sha256=stored.plaintext_sha256,
                storage_key=stored.storage_key,
                byte_size=stored.plaintext_size,
                media_type="application/pdf",
            )
        source_message_id = serializer.validated_data.get("source_message_id")
        source_message = None
        if source_message_id:
            source_message = get_object_or_404(
                Message,
                pk=source_message_id,
                owner_id=owner_id,
                conversation=conversation,
            )
        customer_document = CustomerUploadedDocument.objects.create(
            owner_id=owner_id,
            original_file=original,
            source_message=source_message,
            display_name=Path(uploaded.name).name,
            kind=serializer.validated_data["kind"],
        )
        job = enqueue_stage(
            owner_id=owner_id,
            customer_uploaded_document_id=customer_document.id,
            stage="classify",
        )
        transaction.on_commit(lambda: _schedule_document(job.id))
        return Response(
            {
                "id": str(customer_document.id),
                "job_id": str(job.id),
                "kind": customer_document.kind,
                "review_status": customer_document.review_status,
            },
            status=status.HTTP_202_ACCEPTED,
        )


class CustomerUploadFile(PrivateNoStoreAPIView):
    @extend_schema(
        responses={(200, "application/pdf"): OpenApiTypes.BINARY},
        operation_id="v2_customer_upload_file_retrieve",
    )
    def get(self, request: Request, pk: uuid.UUID) -> HttpResponse | Response:
        document = get_object_or_404(
            CustomerUploadedDocument.objects.select_related("original_file"),
            pk=pk,
            owner_id=_user_id(request),
        )
        original = document.original_file
        stored_sha = Path(original.storage_key).stem
        payload = read_private(
            _user_id(request), "customer-document", original.storage_key, stored_sha
        )
        return _ranged_response(payload, request, original.media_type)


class CatalogueReadiness(PrivateNoStoreAPIView):
    @extend_schema(
        responses=CatalogueReadinessSerializer,
        operation_id="v2_catalogue_readiness",
    )
    def get(self, request: Request) -> Response:
        return Response(catalogue_readiness())


class KnowledgeReadiness(PrivateNoStoreAPIView):
    @extend_schema(
        responses=CatalogueReadinessSerializer,
        operation_id="v2_knowledge_readiness",
    )
    def get(self, request: Request) -> Response:
        return Response(catalogue_readiness())
