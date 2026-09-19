"""Exact-identity, single-attempt v2 relay calls with encrypted retained results."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
import uuid
from collections.abc import Sequence

import httpx
from django.conf import settings
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from pydantic import BaseModel

from apps.accounts.models import User
from apps.adviser.ai import RelayFailure, RelayRoute, StrictRelayAdapter
from apps.adviser.providers import provider_config

from .crypto import commitment
from .errors import AccountErased
from .models import ModelAttempt, ModelQualification, ProcessingJob, Turn
from .role_routes import (
    OMNIROUTE_CONTEXT_LIMIT_BYTES,
    OMNIROUTE_ENDPOINT_PROFILE,
    RoleRoute,
)
from .storage import read_private, store_model_result


def schema_sha256(output_type: type[BaseModel]) -> str:
    encoded = json.dumps(
        output_type.model_json_schema(), sort_keys=True, separators=(",", ":")
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def route_timeout_seconds(*, processing: bool, remaining_seconds: float) -> float:
    if remaining_seconds <= 0:
        raise ValueError("Model deadline must be positive.")
    if processing:
        return remaining_seconds
    return min(float(settings.AI_TURN_TIMEOUT_SECONDS), remaining_seconds)


def qualified_route(
    route: RoleRoute | str, schema_name: str, output_type: type[BaseModel]
) -> ModelQualification:
    if isinstance(route, str):
        route = RoleRoute.relay(route)
    expected_hash = schema_sha256(output_type)
    candidates = ModelQualification.objects.select_related("route").filter(
        route__requested_model=route.requested_model,
        route__disabled_at__isnull=True,
        schema_name=schema_name,
        schema_sha256=expected_hash,
        observed_model=route.expected_model,
        result="passed",
    )
    if route.is_omniroute:
        # The immutable route row pins endpoint, base URL, requested and expected identity.
        candidates = candidates.filter(
            route__endpoint_profile=OMNIROUTE_ENDPOINT_PROFILE,
            route__route_key=route.route_key,
            route__configuration_sha256=route.configuration_sha256,
        )
    else:
        candidates = candidates.exclude(route__endpoint_profile=OMNIROUTE_ENDPOINT_PROFILE)
    for candidate in candidates.order_by("-created_at"):
        capabilities = candidate.capabilities
        if (
            isinstance(capabilities, dict)
            and capabilities.get("structured_output") is True
            and capabilities.get("identity_exact") is True
        ):
            return candidate
    raise RelayFailure(
        "route_unqualified",
        f"The exact {route.requested_model} route has not passed the current {schema_name} schema.",
    )


def call_model[OutputT: BaseModel](
    *,
    model: str | None = None,
    route: RoleRoute | None = None,
    schema_name: str,
    output_type: type[OutputT],
    messages: Sequence[dict[str, str]],
    remaining_seconds: float,
    turn: Turn | None = None,
    processing_job: ProcessingJob | None = None,
    reuse_successful_processing_result: bool = False,
) -> OutputT:
    if (turn is None) == (processing_job is None):
        raise ValueError("Exactly one turn or processing job is required.")
    if (model is None) == (route is None):
        raise ValueError("Exactly one model or route is required.")
    role_route = route if route is not None else RoleRoute.relay(str(model))
    if role_route.is_omniroute and processing_job is not None:
        # Processing jobs can carry private uploads, so they never reach a third-party gateway.
        raise RelayFailure(
            "provider_not_allowed", "Offline processing may only use the relay route."
        )
    model = role_route.requested_model
    qualification = qualified_route(role_route, schema_name, output_type)
    owner_id: uuid.UUID | None
    if turn is not None:
        parent_attempts = ModelAttempt.objects.filter(turn=turn)
        owner_id = turn.owner_id
    else:
        assert processing_job is not None
        parent_attempts = ModelAttempt.objects.filter(processing_job=processing_job)
        owner_id = processing_job.owner_id
    owner_generation: int | None = None
    if owner_id is not None:
        with transaction.atomic():
            owner = User.objects.select_for_update().get(pk=owner_id)
            if owner.deleted_at is not None or not owner.is_active:
                raise AccountErased("account_erased")
            owner_generation = owner.erasure_generation
    attempt_number = (parent_attempts.aggregate(value=Max("attempt_number"))["value"] or 0) + 1
    started = timezone.now()
    request_data = {
        "model": model,
        "schema": schema_name,
        "schema_sha256": qualification.schema_sha256,
        "messages": list(messages),
    }
    request_commitment = commitment(request_data)
    if reuse_successful_processing_result:
        if processing_job is None:
            raise ValueError("Only offline processing calls may reuse an exact retained result.")
        reusable = (
            ModelAttempt.objects.filter(
                processing_job__isnull=False,
                owner_id=owner_id,
                qualification=qualification,
                request_commitment=request_commitment,
                status="succeeded",
                response_storage_key__isnull=False,
                response_storage_sha256__isnull=False,
            )
            .order_by("-completed_at")
            .first()
        )
        if reusable is not None:
            assert reusable.response_storage_key is not None
            assert reusable.response_storage_sha256 is not None
            namespace = reusable.owner_id or uuid.UUID(int=0)
            try:
                payload = read_private(
                    namespace,
                    f"model-result-{reusable.id}",
                    reusable.response_storage_key,
                    reusable.response_storage_sha256,
                )
                return output_type.model_validate_json(payload)
            except Exception as exc:
                raise RelayFailure(
                    "retained_result_invalid",
                    "An exact retained processing response failed integrity or schema validation.",
                ) from exc
    unavailable_usage = {
        "input_tokens": None,
        "output_tokens": None,
        "cached_input_tokens": None,
        "latency_ms": 0,
        "usage_source": "unavailable",
    }
    attempt = ModelAttempt.objects.create(
        owner_id=owner_id,
        turn=turn,
        processing_job=processing_job,
        qualification=qualification,
        attempt_number=attempt_number,
        started_at=started,
        usage=unavailable_usage,
        request_commitment=request_commitment,
    )
    provider = provider_config(role_route.relay_type)
    relay_route = RelayRoute(
        relay_type=role_route.relay_type,  # type: ignore[arg-type]
        base_url=provider.base_url,
        model=model,
        api_dialect="openai_responses",
        context_limit=(OMNIROUTE_CONTEXT_LIMIT_BYTES if role_route.is_omniroute else 1_000_000),
        timeout_seconds=route_timeout_seconds(
            processing=processing_job is not None,
            remaining_seconds=remaining_seconds,
        ),
        qualified=True,
        expected_model=role_route.expected_model if role_route.is_omniroute else None,
    )
    began = time.monotonic()

    async def invoke() -> tuple[OutputT, StrictRelayAdapter]:
        async with httpx.AsyncClient(trust_env=False) as client:
            adapter = StrictRelayAdapter(relay_route, client, provider.api_key)
            result = await adapter.generate(list(messages), remaining_seconds, output_type)
            return result, adapter

    try:
        result, adapter = asyncio.run(invoke())
    except RelayFailure as exc:
        if owner_id is not None:
            with transaction.atomic():
                owner = User.objects.select_for_update().get(pk=owner_id)
                if (
                    owner.erasure_generation != owner_generation
                    or owner.deleted_at is not None
                    or not owner.is_active
                ):
                    ModelAttempt.objects.filter(pk=attempt.id).update(
                        completed_at=timezone.now(),
                        status="cancelled",
                        error_code="account_erased",
                    )
                    raise AccountErased("account_erased") from exc
        attempt.completed_at = timezone.now()
        attempt.status = {
            "provider_timeout": "timeout",
            "provider_transport": "transport_error",
            "invalid_structured_output": "schema_error",
            "model_identity_mismatch": "identity_error",
        }.get(exc.code, "indeterminate")
        attempt.error_code = exc.code
        attempt.usage = {
            **unavailable_usage,
            "latency_ms": round((time.monotonic() - began) * 1000),
        }
        attempt.save(update_fields=["completed_at", "status", "error_code", "usage"])
        raise
    usage = {
        "input_tokens": adapter.usage.get("input_tokens"),
        "output_tokens": adapter.usage.get("output_tokens"),
        "cached_input_tokens": adapter.usage.get("cached_input_tokens"),
        "latency_ms": round((time.monotonic() - began) * 1000),
        "usage_source": "provider_reported" if adapter.usage else "unavailable",
    }
    with transaction.atomic():
        if owner_id is not None:
            owner = User.objects.select_for_update().get(pk=owner_id)
            if (
                owner.erasure_generation != owner_generation
                or owner.deleted_at is not None
                or not owner.is_active
            ):
                ModelAttempt.objects.filter(pk=attempt.id).update(
                    completed_at=timezone.now(),
                    status="cancelled",
                    error_code="account_erased",
                )
                raise AccountErased("account_erased")
        encoded = result.model_dump_json().encode()
        stored = store_model_result(attempt.owner_id, str(attempt.id), encoded)
        attempt.completed_at = timezone.now()
        attempt.observed_model = adapter.reported_model
        attempt.status = "succeeded"
        attempt.usage = usage
        attempt.response_storage_key = stored.storage_key
        attempt.response_storage_sha256 = stored.stored_sha256
        attempt.save(
            update_fields=[
                "completed_at",
                "observed_model",
                "status",
                "usage",
                "response_storage_key",
                "response_storage_sha256",
            ]
        )
    return result
