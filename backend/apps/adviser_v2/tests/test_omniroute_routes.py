from __future__ import annotations

import json
from typing import Any

import httpx
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import User
from apps.adviser.ai import RelayFailure
from apps.adviser_v2.model_gateway import call_model, qualified_route, schema_sha256
from apps.adviser_v2.models import ModelAttempt, ModelQualification, ModelRoute, ProcessingJob
from apps.adviser_v2.readiness import _model_gate
from apps.adviser_v2.role_routes import RoleRoute, configured_route
from apps.adviser_v2.schemas import PolicyRuleExtractionV1, RecommendationDraftV1
from apps.adviser_v2.selectors.catalogue import catalogue_readiness
from apps.adviser_v2.tests.test_outbox import queued_turn
from apps.adviser_v2.tests.test_pipeline import public_html_capture

REQUESTED, REPORTED = "gemini/gemini-test", "gemini-test"
SCHEMA = "recommendation_answer"


@pytest.fixture
def omni(settings: Any) -> Any:
    settings.DEBUG = True
    settings.OMNIROUTE_ENABLED = True
    settings.OMNIROUTE_BASE_URL = "http://127.0.0.1:20128"
    settings.OMNIROUTE_API_KEY = "omni-secret"
    settings.OMNIROUTE_LOGGING_DISABLED_CONFIRMED = True
    settings.COVERGUIDE_LOCAL_OMNIROUTE_PILOT_ACK = True
    settings.OMNIROUTE_MODELS = f"{REQUESTED}={REPORTED}"
    settings.COVERGUIDE_FINAL_EXPLANATION_ROUTE = f"omniroute:{REQUESTED}"
    return settings


def qualify(route: RoleRoute, schema_name: str = SCHEMA, output_type: Any = RecommendationDraftV1):
    row, _ = ModelRoute.objects.get_or_create(
        route_key=route.route_key,
        defaults={
            "endpoint_profile": route.endpoint_profile,
            "requested_model": route.requested_model,
            "adapter_version": route.configuration["adapter_version"],
            "configuration_sha256": route.configuration_sha256,
        },
    )
    return ModelQualification.objects.create(
        route=row,
        schema_name=schema_name,
        schema_sha256=schema_sha256(output_type),
        observed_model=route.expected_model,
        capabilities={
            "structured_output": True,
            "max_context_tokens_tested": 0,
            "image_input_tested": False,
            "image_formats": [],
            "schema_test_artifact_hashes": [],
            "identity_exact": True,
            "latency_ms": 1,
            "limitations": [],
        },
        result="passed",
    )


def draft_envelope(model: str = REPORTED) -> dict[str, Any]:
    draft = RecommendationDraftV1(
        schema_version=1,
        outcome="insufficient_evidence",
        introduction="Evidence is insufficient.",
        statements=[],
        follow_up=None,
    )
    return {
        "model": model,
        "status": "completed",
        "output": [
            {
                "type": "message",
                "content": [{"type": "output_text", "text": draft.model_dump_json()}],
            }
        ],
    }


def patch_transport(monkeypatch: Any, handler: Any) -> None:
    real = httpx.AsyncClient
    monkeypatch.setattr(
        "apps.adviser_v2.model_gateway.httpx.AsyncClient",
        lambda **kw: real(transport=httpx.MockTransport(handler), **kw),
    )


def test_defaults_stay_on_the_relay(settings: Any) -> None:
    route = configured_route("recommendation_answer")
    assert route == RoleRoute.relay(settings.COVERGUIDE_FINAL_EXPLANATION_MODEL)
    assert route.route_key.count(":") == 1 and len(route.route_key.split(":")[1]) == 16


def test_omniroute_role_resolves_with_full_digest_key(omni: Any) -> None:
    route = configured_route(SCHEMA)
    assert (route.relay_type, route.requested_model, route.expected_model) == (
        "omniroute",
        REQUESTED,
        REPORTED,
    )
    assert route.route_key == f"omniroute:{route.configuration_sha256}"
    assert len(route.route_key) <= 120
    omni.OMNIROUTE_MODELS = f"{REQUESTED}=other"
    assert configured_route(SCHEMA).route_key != route.route_key


@pytest.mark.parametrize(
    ("value", "code"),
    [("gemini/x", "provider_misconfigured"), ("omniroute:not/listed", "provider_misconfigured")],
)
def test_bad_role_route_settings_fail_closed(omni: Any, value: str, code: str) -> None:
    omni.COVERGUIDE_FINAL_EXPLANATION_ROUTE = value
    with pytest.raises(RelayFailure) as caught:
        configured_route(SCHEMA)
    assert caught.value.code == code


def test_disabled_provider_never_falls_back_to_the_relay(omni: Any) -> None:
    omni.OMNIROUTE_ENABLED = False
    with pytest.raises(RelayFailure) as caught:
        configured_route(SCHEMA)
    assert caught.value.code == "provider_disabled"


def test_relay_only_roles_ignore_any_omniroute_setting(omni: Any) -> None:
    omni.COVERGUIDE_POLICY_EXTRACTION_ROUTE = f"omniroute:{REQUESTED}"
    assert not configured_route("policy_extraction").is_omniroute
    assert not configured_route("policy_review").is_omniroute


def test_qualification_must_match_route_profile_and_full_configuration(db: None, omni: Any) -> None:
    route = configured_route(SCHEMA)
    with pytest.raises(RelayFailure):
        qualified_route(route, SCHEMA, RecommendationDraftV1)
    stored = qualify(route)
    assert qualified_route(route, SCHEMA, RecommendationDraftV1).id == stored.id
    # A changed expected identity is a different immutable route, so it is unqualified.
    omni.OMNIROUTE_MODELS = f"{REQUESTED}=other"
    with pytest.raises(RelayFailure):
        qualified_route(configured_route(SCHEMA), SCHEMA, RecommendationDraftV1)
    # A relay route for the same model string never borrows the OmniRoute qualification.
    with pytest.raises(RelayFailure):
        qualified_route(REPORTED, SCHEMA, RecommendationDraftV1)


def test_omniroute_qualification_is_not_used_by_the_relay_lookup(db: None, omni: Any) -> None:
    qualify(RoleRoute("omniroute", "gpt-5.6-sol", "gpt-5.6-sol"))
    with pytest.raises(RelayFailure):
        qualified_route("gpt-5.6-sol", SCHEMA, RecommendationDraftV1)


def test_processing_jobs_are_refused_on_omniroute(db: None, omni: Any) -> None:
    job = ProcessingJob.objects.create(
        source_capture=public_html_capture(),
        stage="extract",
        adapter_version="test/1",
        input_commitment="c" * 64,
    )
    route = configured_route(SCHEMA)
    qualify(route, "policy_extraction", PolicyRuleExtractionV1)
    with pytest.raises(RelayFailure) as caught:
        call_model(
            route=route,
            schema_name="policy_extraction",
            output_type=PolicyRuleExtractionV1,
            messages=[{"role": "user", "content": "x"}],
            remaining_seconds=30,
            processing_job=job,
        )
    assert caught.value.code == "provider_not_allowed"
    assert not ModelAttempt.objects.exists()


def test_turn_call_uses_the_omniroute_qualification_and_records_raw_identity(
    v2_user: User, omni: Any, monkeypatch: Any
) -> None:
    route = configured_route(SCHEMA)
    stored = qualify(route)
    turn = queued_turn(v2_user)
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=draft_envelope())

    patch_transport(monkeypatch, handler)
    call_model(
        route=route,
        schema_name=SCHEMA,
        output_type=RecommendationDraftV1,
        messages=[{"role": "user", "content": "hi"}],
        remaining_seconds=30,
        turn=turn,
    )
    assert len(seen) == 1 and str(seen[0].url) == "http://127.0.0.1:20128/v1/responses"
    assert seen[0].headers["authorization"] == "Bearer omni-secret"
    assert json.loads(seen[0].content)["model"] == REQUESTED
    attempt = ModelAttempt.objects.get(turn=turn)
    assert attempt.qualification_id == stored.id and attempt.status == "succeeded"
    assert attempt.observed_model == REPORTED


@pytest.mark.parametrize(
    ("response", "status", "code"),
    [
        (httpx.Response(429, text="quota"), "indeterminate", "provider_quota"),
        (
            httpx.Response(200, json=draft_envelope("gemini-other")),
            "identity_error",
            "model_identity_mismatch",
        ),
    ],
)
def test_omniroute_failures_make_one_call_and_never_fall_back(
    v2_user: User, omni: Any, monkeypatch: Any, response: httpx.Response, status: str, code: str
) -> None:
    route = configured_route(SCHEMA)
    qualify(route)
    turn = queued_turn(v2_user)
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return response

    patch_transport(monkeypatch, handler)
    with pytest.raises(RelayFailure) as caught:
        call_model(
            route=route,
            schema_name=SCHEMA,
            output_type=RecommendationDraftV1,
            messages=[{"role": "user", "content": "hi"}],
            remaining_seconds=30,
            turn=turn,
        )
    assert caught.value.code == code and calls == ["http://127.0.0.1:20128/v1/responses"]
    attempt = ModelAttempt.objects.get(turn=turn)
    assert (attempt.status, attempt.error_code) == (status, code)


def test_call_requires_exactly_one_of_model_or_route(db: None) -> None:
    with pytest.raises(ValueError):
        call_model(
            schema_name=SCHEMA,
            output_type=RecommendationDraftV1,
            messages=[],
            remaining_seconds=1,
            turn=None,
            processing_job=None,
        )


def test_readiness_blocks_an_unqualified_omniroute_role_only(db: None, omni: Any) -> None:
    blockers = _model_gate()
    assert f"model:{REQUESTED}:{SCHEMA}:route_unqualified" in blockers
    status = next(
        item
        for item in catalogue_readiness()["interactive_routes"]
        if item["role"] == SCHEMA
    )
    assert status == {
        "role": SCHEMA,
        "qualified": False,
        "error_code": "route_unqualified",
        "requested_model": REQUESTED,
        "expected_model": REPORTED,
        "endpoint_profile": "omniroute-loopback",
        "adapter_version": "strict-relay-v2/1",
        "route_key": configured_route(SCHEMA).route_key,
        "configuration_sha256": configured_route(SCHEMA).configuration_sha256,
        "schema_sha256": None,
        "qualification_id": None,
    }
    qualify(configured_route(SCHEMA))
    assert not [b for b in _model_gate() if f":{SCHEMA}:" in b]
    omni.OMNIROUTE_ENABLED = False
    assert any(f":{SCHEMA}:provider_disabled" in b for b in _model_gate())


def test_check_omniroute_reports_missing_models_and_is_quiet_when_present(
    omni: Any, monkeypatch: Any
) -> None:
    real = httpx.Client

    def install(ids: list[str]) -> None:
        monkeypatch.setattr(
            "apps.adviser_v2.management.commands.check_omniroute.httpx.Client",
            lambda **kw: real(
                transport=httpx.MockTransport(
                    lambda request: httpx.Response(200, json={"data": [{"id": i} for i in ids]})
                ),
                **kw,
            ),
        )

    install([REQUESTED])
    call_command("check_omniroute")
    install(["something-else"])
    with pytest.raises(CommandError, match="Not in the live catalogue"):
        call_command("check_omniroute")
    omni.OMNIROUTE_API_KEY = ""
    with pytest.raises(CommandError, match="OMNIROUTE_API_KEY"):
        call_command("check_omniroute")
