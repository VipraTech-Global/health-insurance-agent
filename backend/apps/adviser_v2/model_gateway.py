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

from .crypto import commitment, commitment_matches
from .errors import AccountErased
from .models import ModelAttempt, ModelQualification, ProcessingJob, Turn, TurnRouteBinding
from .role_routes import (
    OMNIROUTE_CONTEXT_LIMIT_BYTES,
    OMNIROUTE_ENDPOINT_PROFILE,
    RoleRoute,
    configured_route,
)
from .schemas import CustomerInterpretationV1, RecommendationDraftV1
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
    # A qualification is valid only for the complete immutable route identity. This prevents a
    # qualification for one endpoint/configuration from being borrowed by another route that
    # happens to use the same model string.
    candidates = candidates.filter(
        route__route_key=route.route_key,
        route__endpoint_profile=route.endpoint_profile,
        route__configuration_sha256=route.configuration_sha256,
    )
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


_TURN_ROUTE_OUTPUTS: dict[str, type[BaseModel]] = {
    "fact_interpretation": CustomerInterpretationV1,
    "recommendation_answer": RecommendationDraftV1,
}


def _binding_payload(binding: TurnRouteBinding) -> dict[str, str]:
    return {
        "role": binding.role,
        "route_id": str(binding.route_id),
        "route_key": binding.route.route_key,
        "qualification_id": str(binding.qualification_id),
        "requested_model": binding.requested_model,
        "expected_model": binding.expected_model,
        "observed_model": binding.observed_model,
        "endpoint_profile": binding.endpoint_profile,
        "adapter_version": binding.adapter_version,
        "route_configuration_sha256": binding.route_configuration_sha256,
        "schema_sha256": binding.schema_sha256,
    }


def turn_route_commitment(bindings: Sequence[TurnRouteBinding]) -> str:
    return commitment(_turn_route_payload(bindings))


def _turn_route_payload(bindings: Sequence[TurnRouteBinding]) -> dict[str, list[dict[str, str]]]:
    return {"bindings": [_binding_payload(item) for item in sorted(bindings, key=lambda x: x.role)]}


@transaction.atomic
def pin_turn_routes(turn: Turn) -> list[TurnRouteBinding]:
    """Resolve and persist both interactive routes before a turn enters the outbox."""

    if turn.route_bindings.exists():
        raise RelayFailure("route_binding_exists", "The turn already has immutable route bindings.")
    bindings: list[TurnRouteBinding] = []
    for role, output_type in _TURN_ROUTE_OUTPUTS.items():
        role_route = configured_route(role)
        qualification = qualified_route(role_route, role, output_type)
        route = qualification.route
        if (
            route.route_key != role_route.route_key
            or route.endpoint_profile != role_route.endpoint_profile
            or route.requested_model != role_route.requested_model
            or route.configuration_sha256 != role_route.configuration_sha256
            or qualification.observed_model != role_route.expected_model
        ):
            raise RelayFailure("route_identity_mismatch", f"The {role} route identity changed.")
        bindings.append(
            TurnRouteBinding.objects.create(
                turn=turn,
                role=role,
                route=route,
                qualification=qualification,
                requested_model=role_route.requested_model,
                expected_model=role_route.expected_model,
                observed_model=qualification.observed_model,
                endpoint_profile=role_route.endpoint_profile,
                adapter_version=role_route.configuration["adapter_version"],
                route_configuration_sha256=role_route.configuration_sha256,
                schema_sha256=qualification.schema_sha256,
            )
        )
    turn.route_commitment = turn_route_commitment(bindings)
    turn.save(update_fields=["route_commitment", "updated_at"])
    return bindings


@transaction.atomic
def copy_turn_routes(source: Turn, target: Turn) -> list[TurnRouteBinding]:
    """Copy, never re-resolve, the source turn's route bindings for an explicit retry."""

    source_bindings = list(source.route_bindings.select_related("route", "qualification"))
    if sorted(binding.role for binding in source_bindings) != sorted(_TURN_ROUTE_OUTPUTS):
        raise RelayFailure("route_binding_missing", "The original turn has no complete route pin.")
    copied = [
        TurnRouteBinding.objects.create(
            turn=target,
            role=binding.role,
            route=binding.route,
            qualification=binding.qualification,
            requested_model=binding.requested_model,
            expected_model=binding.expected_model,
            observed_model=binding.observed_model,
            endpoint_profile=binding.endpoint_profile,
            adapter_version=binding.adapter_version,
            route_configuration_sha256=binding.route_configuration_sha256,
            schema_sha256=binding.schema_sha256,
        )
        for binding in source_bindings
    ]
    target.route_commitment = turn_route_commitment(copied)
    target.save(update_fields=["route_commitment", "updated_at"])
    return copied


def route_for_binding(
    binding: TurnRouteBinding, schema_name: str, output_type: type[BaseModel]
) -> tuple[RoleRoute, ModelQualification]:
    """Validate a stored binding without consulting the mutable operator settings."""

    if binding.role != schema_name:
        raise RelayFailure("route_binding_mismatch", "The stored route role does not match the call.")
    route = binding.route
    qualification = binding.qualification
    expected_hash = schema_sha256(output_type)
    all_bindings = list(
        binding.turn.route_bindings.select_related("route", "qualification").order_by("role")
    )
    if not binding.turn.route_commitment or not commitment_matches(
        binding.turn.route_commitment, _turn_route_payload(all_bindings)
    ):
        raise RelayFailure("route_commitment_mismatch", "The turn route commitment is invalid.")
    if route.disabled_at is not None:
        raise RelayFailure("route_disabled", "The pinned route is disabled.")
    if (
        route.id != qualification.route_id
        or route.endpoint_profile != binding.endpoint_profile
        or route.requested_model != binding.requested_model
        or route.adapter_version != binding.adapter_version
        or route.configuration_sha256 != binding.route_configuration_sha256
        or qualification.schema_name != schema_name
        or qualification.schema_sha256 != expected_hash
        or binding.schema_sha256 != expected_hash
        or qualification.result != "passed"
        or qualification.observed_model != binding.observed_model
        or binding.observed_model != binding.expected_model
        or not isinstance(qualification.capabilities, dict)
        or qualification.capabilities.get("structured_output") is not True
        or qualification.capabilities.get("identity_exact") is not True
    ):
        raise RelayFailure("route_binding_invalid", "The pinned route qualification is invalid.")
    if route.endpoint_profile == OMNIROUTE_ENDPOINT_PROFILE:
        role_route = RoleRoute("omniroute", binding.requested_model, binding.expected_model)
    else:
        role_route = RoleRoute.relay(binding.requested_model)
    if (
        role_route.endpoint_profile != binding.endpoint_profile
        or role_route.route_key != route.route_key
        or role_route.configuration_sha256 != binding.route_configuration_sha256
    ):
        raise RelayFailure(
            "route_configuration_mismatch",
            "The pinned route no longer matches the active endpoint configuration.",
        )
    return role_route, qualification


def call_model[OutputT: BaseModel](
    *,
    model: str | None = None,
    route: RoleRoute | None = None,
    binding: TurnRouteBinding | None = None,
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
    supplied_routes = sum(value is not None for value in (model, route, binding))
    if supplied_routes != 1:
        raise ValueError("Exactly one model, route, or binding is required.")
    if binding is not None:
        if turn is None or binding.turn_id != turn.id:
            raise RelayFailure("route_binding_mismatch", "The route binding belongs to another turn.")
        role_route, qualification = route_for_binding(binding, schema_name, output_type)
    else:
        role_route = route if route is not None else RoleRoute.relay(str(model))
        qualification = qualified_route(role_route, schema_name, output_type)
    if role_route.is_omniroute and processing_job is not None:
        # Processing jobs can carry private uploads, so they never reach a third-party gateway.
        raise RelayFailure(
            "provider_not_allowed", "Offline processing may only use the relay route."
        )
    model = role_route.requested_model
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
        "expected_model": role_route.expected_model,
        "endpoint_profile": role_route.endpoint_profile,
        "route_key": qualification.route.route_key,
        "route_configuration_sha256": qualification.route.configuration_sha256,
        "qualification_id": str(qualification.id),
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
