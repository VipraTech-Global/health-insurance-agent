"""Qualification and preferences. Discovery alone never makes a model selectable."""

import hashlib
import json
import re
import time
import uuid
from typing import Any

import httpx
from asgiref.sync import async_to_sync
from django.conf import settings
from django.db import connection, transaction
from pydantic import BaseModel

from .ai import (
    InterviewDraft,
    RelayFailure,
    RelayRoute,
    StrictRelayAdapter,
    StructuredAnswerDraft,
    loopback_url,
)
from .models import AIPreference, ModelCallAttempt, RouteConfiguration, RouteQualification
from .providers import omniroute_models, provider_config

INITIAL_MODELS = ("gpt-6-astra", "gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna")


def discover_models() -> list[str]:
    config = provider_config("cliproxyapi")
    base = loopback_url(config.base_url)
    if not config.api_key:
        raise RelayFailure("relay_unconfigured", "The relay is not configured.")
    try:
        with httpx.Client(timeout=5, follow_redirects=False, trust_env=False) as client:
            with client.stream(
                "GET",
                f"{base}/v1/models",
                headers={"Authorization": f"Bearer {config.api_key}"},
            ) as response:
                if response.status_code != 200:
                    raise RelayFailure(
                        "catalogue_unavailable", "The relay model catalogue is unavailable."
                    )
                chunks, size, started = [], 0, time.monotonic()
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > 262_144 or time.monotonic() - started > 5:
                        raise RelayFailure(
                            "catalogue_limit", "The relay model catalogue exceeded its limit."
                        )
                    chunks.append(chunk)
        data = json.loads(b"".join(chunks))["data"]
        if not isinstance(data, list) or len(data) > 200:
            raise ValueError
        models = {
            item["id"]
            for item in data
            if isinstance(item, dict)
            and isinstance(item.get("id"), str)
            and re.fullmatch(r"gpt-[a-zA-Z0-9._-]{1,190}", item["id"])
        }
        return sorted(models)
    except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
        raise RelayFailure(
            "catalogue_unavailable", "The relay model catalogue is unavailable."
        ) from exc


def discover_omniroute_models() -> list[str]:
    """Allowlisted OmniRoute ids the admin may qualify; empty while the provider is off."""

    if not settings.OMNIROUTE_ENABLED:
        return []
    try:
        return sorted(omniroute_models())
    except RelayFailure:
        return []


def route_values(model: str, relay_type: str = "cliproxyapi") -> dict[str, Any]:
    capabilities: dict[str, Any] = {
        "answer_schema": StructuredAnswerDraft.model_json_schema(),
        "interview_schema": InterviewDraft.model_json_schema(),
        "protocol_version": 1,
    }
    if relay_type == "omniroute":
        expected = omniroute_models().get(model)
        if expected is None:
            raise RelayFailure("model_missing", "Choose a model on the OmniRoute allowlist.")
        # Declared per route and part of the hash; relay rows keep their historical hash.
        capabilities["expected_identity"] = expected
        base_url = provider_config("omniroute").base_url
    else:
        base_url = loopback_url(settings.AI_RELAY_BASE_URL)
    return {
        "relay_type": relay_type,
        "base_url": base_url,
        "configured_model": model,
        "api_dialect": "openai_responses",
        "capabilities": capabilities,
        "context_limit": 100_000,
        "timeout_policy": {"seconds": 90},
    }


def configuration_hash(values: dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(values, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def usable_route(route: RouteConfiguration) -> bool:
    try:
        values = route_values(route.configured_model, route.relay_type)
    except RelayFailure:
        # A disabled or reconfigured provider makes its routes unusable; never fall back.
        return False
    stored = {field: getattr(route, field) for field in values}
    return (
        stored == values
        and route.configuration_hash == configuration_hash(values)
        and route.qualification_state == "qualified"
        and RouteQualification.objects.filter(
            route=route, tested_configuration_hash=route.configuration_hash
        )
        .order_by("-created_at", "-id")
        .values_list("state", flat=True)
        .first()
        == "qualified"
    )


def selected_route(user_id: uuid.UUID) -> RouteConfiguration | None:
    preference = AIPreference.objects.select_related("route").filter(user_id=user_id).first()
    if preference:
        # Never replace an explicit choice just because it becomes unavailable.
        return preference.route
    candidate = (
        RouteConfiguration.objects.filter(
            configured_model="gpt-6-astra", qualification_state="qualified"
        )
        .order_by("-created_at")
        .first()
    )
    return candidate if candidate and usable_route(candidate) else None


def model_choices(user_id: uuid.UUID) -> dict[str, Any]:
    models = [
        {"route_id": str(route.id), "model": route.configured_model, "provider": route.relay_type}
        for route in RouteConfiguration.objects.filter(qualification_state="qualified").order_by(
            "configured_model", "-created_at"
        )
        if usable_route(route)
    ]
    selected = selected_route(user_id)
    return {
        "models": models,
        "selected_route_id": str(selected.id) if selected else None,
        "selected_model": selected.configured_model if selected else None,
        "selected_available": bool(selected and usable_route(selected)),
    }


def choose_model(user_id: uuid.UUID, route_id: uuid.UUID) -> dict[str, Any]:
    with transaction.atomic():
        route = RouteConfiguration.objects.select_for_update().filter(id=route_id).first()
        if route is None or not usable_route(route):
            raise RelayFailure("route_unqualified", "Choose a currently qualified model.")
        AIPreference.objects.update_or_create(user_id=user_id, defaults={"route": route})
    return model_choices(user_id)


def route_snapshot(route: RouteConfiguration) -> RelayRoute:
    return RelayRoute(
        "omniroute" if route.relay_type == "omniroute" else "cliproxyapi",
        route.base_url,
        route.configured_model,
        "openai_responses",
        route.context_limit,
        float(route.timeout_policy["seconds"]),
        True,
        route.capabilities.get("expected_identity") if route.relay_type == "omniroute" else None,
    )


async def probe(
    route: RelayRoute, output_type: type[BaseModel], instruction: str
) -> tuple[str, dict[str, int]]:
    async with httpx.AsyncClient(trust_env=False, follow_redirects=False) as client:
        adapter = StrictRelayAdapter(route, client, provider_config(route.relay_type).api_key)
        result = await adapter.generate([{"role": "user", "content": instruction}], 90, output_type)
        if isinstance(result, StructuredAnswerDraft) and (
            result.outcome != "needs_input" or result.claims
        ):
            raise RelayFailure(
                "qualification_content", "The model failed the answer qualification."
            )
        if isinstance(result, InterviewDraft) and [
            (item.field, item.value) for item in result.fields
        ] != [("location", "Bengaluru")]:
            raise RelayFailure(
                "qualification_content", "The model failed the interview qualification."
            )
        return adapter.reported_model, adapter.usage


def qualify_model(model: str, relay_type: str = "cliproxyapi") -> RouteQualification:
    if relay_type == "omniroute":
        # The allowlist, not discovery, decides; provider_config fails closed when disabled.
        provider_config("omniroute")
    else:
        if model not in discover_models():
            raise RelayFailure("model_missing", "Choose a model in the current relay catalogue.")
        from .relay_management import RelayManagementClient

        accounts = [
            account
            for account in RelayManagementClient().credentials("codex")
            if not account.disabled
        ]
        if len(accounts) != 1 or accounts[0].unavailable:
            raise RelayFailure(
                "account_unavailable", "Exactly one healthy Codex account is required."
            )
    values = route_values(model, relay_type)
    route, _ = RouteConfiguration.objects.get_or_create(
        configuration_hash=configuration_hash(values), defaults=values
    )
    results: dict[str, Any] = {}
    for task, output, instruction in (
        (
            "qualification_answer",
            StructuredAnswerDraft,
            'Return outcome needs_input, introduction "Please confirm your profile.", no claims, and follow_up null. Do not give policy advice.',
        ),
        (
            "qualification_interview",
            InterviewDraft,
            'Extract this location exactly: Bengaluru. Return one field with field "location" and value "Bengaluru".',
        ),
    ):
        audit = ModelCallAttempt.objects.create(
            task=task, route=route, requested_model=model, status="running"
        )
        started = time.monotonic()
        connection.close()
        try:
            reported, usage = async_to_sync(probe)(route_snapshot(route), output, instruction)
            audit.upstream_reported_model, audit.reported_usage, audit.status = (
                reported,
                usage,
                "succeeded",
            )
        except RelayFailure as exc:
            audit.status, audit.safe_error_code = "failed", exc.code
        finally:
            audit.duration_ms = int((time.monotonic() - started) * 1000)
            audit.save()
        results[task] = {
            "call_id": str(audit.id),
            "status": audit.status,
            "code": audit.safe_error_code,
        }
        if audit.status == "failed":
            break
    state = (
        "qualified"
        if len(results) == 2 and all(item["status"] == "succeeded" for item in results.values())
        else "failed"
    )
    with transaction.atomic():
        RouteConfiguration.objects.select_for_update().get(pk=route.pk)
        qualification = RouteQualification.objects.create(
            route=route,
            tested_configuration_hash=route.configuration_hash,
            state=state,
            evaluation_results=results,
        )
        RouteConfiguration.objects.filter(pk=route.pk).update(qualification_state=state)
    return qualification


def verify_account_readiness() -> None:
    """Qualify the preferred model after an account change; preserve user choices."""
    models = discover_models()
    if not models:
        raise RelayFailure("model_missing", "Codex returned no eligible models.")
    model = "gpt-6-astra" if "gpt-6-astra" in models else models[0]
    # All model calls, including account checks, are audited via qualification.
    qualification = qualify_model(model)
    if qualification.state != "qualified":
        raise RelayFailure("account_unavailable", "Codex account readiness could not be verified.")
