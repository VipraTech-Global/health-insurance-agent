import asyncio
import json
import logging
import time
import uuid
from collections.abc import AsyncIterator, Callable
from typing import Any, cast

from asgiref.sync import sync_to_async
from config.lifecycle import runtime
from django.core import signing
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse, StreamingHttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_http_methods

from .ai import InterviewDraft, RelayFailure, StrictRelayAdapter, StructuredAnswerDraft
from .ai_turns import attempt_active, fail_turn, finish_call, prepare_turn, publish_ai_answer
from .models import Turn, TurnAttempt
from .providers import provider_config
from .relay_accounts import active_account_identity
from .serializers import TurnSerializer
from .services import (
    ConflictError,
    OwnershipError,
    accept_turn,
    cancel_attempt,
    mark_running,
    publish_controlled_answer,
)

logger = logging.getLogger(__name__)


def _database_boundary[T](function: Callable[..., T], *args: Any) -> T:
    try:
        return function(*args)
    finally:
        connection.close()


async def _database_call[T](function: Callable[..., T], *args: Any) -> T:
    return await sync_to_async(_database_boundary, thread_sensitive=True)(function, *args)


def _event(name: str, payload: dict[str, object]) -> bytes:
    return f"event: {name}\ndata: {json.dumps(payload, separators=(',', ':'), cls=DjangoJSONEncoder)}\n\n".encode()


@require_http_methods(["GET", "POST"])
async def stream_turn(
    request: HttpRequest, conversation_id: uuid.UUID
) -> HttpResponse | StreamingHttpResponse:
    user = await request.auser()
    if not user.is_authenticated:
        return JsonResponse(
            {"error": {"code": "not_authenticated", "message": "Authentication is required."}},
            status=401,
        )
    if request.method == "GET":
        cursor_token = request.GET.get("cursor")

        def list_turns() -> dict[str, object]:
            query = Turn.objects.filter(
                conversation_id=conversation_id, conversation__owner_id=user.id
            ).order_by("-created_at", "-id")
            if cursor_token:
                try:
                    cursor = signing.loads(cursor_token, salt="turn-list-cursor")
                    created_at = parse_datetime(str(cursor["created_at"]))
                    cursor_id = uuid.UUID(str(cursor["id"]))
                except (signing.BadSignature, KeyError, TypeError, ValueError) as exc:
                    raise ValueError("The turn cursor is invalid.") from exc
                if created_at is None:
                    raise ValueError("The turn cursor is invalid.")
                query = query.filter(
                    Q(created_at__lt=created_at) | Q(created_at=created_at, id__lt=cursor_id)
                )
            values = list(query.prefetch_related("attempts")[:51])
            page = values[:50]
            next_cursor = None
            if len(values) > 50:
                last = page[-1]
                next_cursor = signing.dumps(
                    {"created_at": last.created_at.isoformat(), "id": str(last.id)},
                    salt="turn-list-cursor",
                    compress=True,
                )
            return {
                "results": cast(list[dict[str, object]], TurnSerializer(page, many=True).data),
                "next_cursor": next_cursor,
            }

        try:
            page_data = await _database_call(list_turns)
        except ValueError as exc:
            return JsonResponse(
                {"error": {"code": "invalid_cursor", "message": str(exc)}},
                status=400,
            )
        return JsonResponse(page_data)
    try:
        await asyncio.wait_for(runtime.turn_admission.acquire(), timeout=0.05)
    except TimeoutError:
        return JsonResponse(
            {
                "error": {
                    "code": "capacity_exceeded",
                    "message": "The adviser is at capacity. Try again shortly.",
                }
            },
            status=429,
        )
    try:
        payload = json.loads(request.body or b"{}")
        if not isinstance(payload, dict) or not payload.get("request_id"):
            raise ValueError("request_id is required")
        accepted = await _database_call(accept_turn, user.id, conversation_id, payload)
    except (json.JSONDecodeError, ValueError) as exc:
        runtime.turn_admission.release()
        return JsonResponse({"error": {"code": "invalid_request", "message": str(exc)}}, status=400)
    except OwnershipError:
        runtime.turn_admission.release()
        return JsonResponse(
            {"error": {"code": "not_found", "message": "Conversation not found."}}, status=404
        )
    except ConflictError as exc:
        runtime.turn_admission.release()
        return JsonResponse({"error": {"code": "conflict", "message": str(exc)}}, status=409)
    except Exception:
        runtime.turn_admission.release()
        logger.exception("turn_acceptance_failed")
        return JsonResponse(
            {
                "error": {
                    "code": "acceptance_failed",
                    "message": "The request could not be accepted.",
                }
            },
            status=500,
        )

    async def events() -> AsyncIterator[bytes]:
        completed = False
        prepared = None
        owns_attempt = not accepted.existing
        try:
            yield _event(
                "accepted",
                {
                    "turn_id": accepted.turn_id,
                    "attempt_id": accepted.attempt_id,
                    "profile_revision": accepted.profile_revision,
                },
            )
            if accepted.existing and accepted.terminal_answer_id:
                yield _event(
                    "result",
                    {"answer_id": accepted.terminal_answer_id, "reused": True},
                )
                completed = True
                return
            if accepted.existing and accepted.attempt_status in TurnAttempt.ACTIVE:
                yield _event(
                    "result",
                    {
                        "turn_id": accepted.turn_id,
                        "attempt_id": accepted.attempt_id,
                        "status": accepted.attempt_status,
                        "reused": True,
                    },
                )
                completed = True
                return
            if not await _database_call(mark_running, user.id, uuid.UUID(accepted.attempt_id)):
                yield _event(
                    "error",
                    {
                        "code": "attempt_not_active",
                        "message": "The attempt is no longer active.",
                        "retryable": False,
                    },
                )
                completed = True
                return
            yield _event("progress", {"stage": "profile", "message": "Checking your profile"})
            try:
                prepared = await _database_call(
                    prepare_turn, user.id, uuid.UUID(accepted.attempt_id)
                )
                if prepared is None:
                    answer = await _database_call(
                        publish_controlled_answer, user.id, uuid.UUID(accepted.attempt_id)
                    )
                else:
                    yield _event(
                        "progress",
                        {"stage": "model", "message": f"Consulting {prepared.route.model}"},
                    )
                    if runtime.http_client is None:
                        raise RelayFailure("relay_unconfigured", "The AI runtime is not ready.")
                    account_identity = await _database_call(active_account_identity)
                    adapter = StrictRelayAdapter(
                        prepared.route,
                        runtime.http_client,
                        provider_config(prepared.route.relay_type).api_key,
                    )
                    started = time.monotonic()
                    call_status, call_code = "failed", "interrupted"
                    task = asyncio.create_task(
                        adapter.generate(
                            prepared.messages,
                            (prepared.deadline_at - timezone.now()).total_seconds(),
                            StructuredAnswerDraft
                            if prepared.task == "policy_answer"
                            else InterviewDraft,
                        )
                    )
                    try:
                        while not task.done():
                            await asyncio.wait({task}, timeout=0.75)
                            if not await _database_call(
                                attempt_active, user.id, prepared.attempt_id
                            ):
                                raise RelayFailure(
                                    "attempt_not_active",
                                    "The turn was cancelled, changed, or expired.",
                                )
                        draft = await task
                        call_status, call_code = "succeeded", ""
                    except RelayFailure as exc:
                        call_code = exc.code
                        raise
                    finally:
                        if not task.done():
                            task.cancel()
                        await asyncio.gather(task, return_exceptions=True)
                        await asyncio.shield(
                            _database_call(
                                finish_call,
                                prepared.call_id,
                                call_status,
                                call_code,
                                adapter.reported_model,
                                adapter.usage,
                                int((time.monotonic() - started) * 1000),
                            )
                        )
                    if await _database_call(active_account_identity) != account_identity:
                        raise RelayFailure(
                            "account_changed",
                            "The laptop-wide Codex account changed while preparing this answer.",
                        )
                    answer = await _database_call(publish_ai_answer, user.id, prepared, draft)
            except (ConflictError, RelayFailure) as exc:
                code = exc.code if isinstance(exc, RelayFailure) else "superseded"
                if prepared is not None:
                    await _database_call(finish_call, prepared.call_id, "failed", code, "", {}, 0)
                await _database_call(fail_turn, user.id, uuid.UUID(accepted.attempt_id), code)
                yield _event(
                    "error",
                    {
                        "code": code,
                        "message": str(exc),
                        "retryable": isinstance(exc, RelayFailure) and exc.retryable,
                    },
                )
                completed = True
                return
            yield _event("result", {"answer": answer, "reused": False})
            completed = True
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("turn_stream_failed", extra={"attempt_id": accepted.attempt_id})
            yield _event(
                "error",
                {
                    "code": "pipeline_failed",
                    "message": "The request failed before a verified answer was saved.",
                    "retryable": True,
                },
            )
        finally:
            if prepared is not None:
                await asyncio.shield(
                    _database_call(
                        finish_call, prepared.call_id, "cancelled", "interrupted", "", {}, 0
                    )
                )
            if owns_attempt and not completed:
                try:
                    await asyncio.shield(
                        _database_call(cancel_attempt, user.id, uuid.UUID(accepted.attempt_id))
                    )
                except Exception as exc:
                    logger.warning("attempt_reconciliation_failed: %s", exc.__class__.__name__)
            runtime.turn_admission.release()

    response = StreamingHttpResponse(events(), content_type="text/event-stream")
    response["Cache-Control"] = "no-store"
    response["X-Accel-Buffering"] = "no"
    return response
