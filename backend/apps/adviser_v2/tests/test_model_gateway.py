from __future__ import annotations

import runpy
from pathlib import Path
from typing import Any

import pytest
from django.utils import timezone
from research_workspace.legacy_v2.model_gateway import (
    call_model,
    qualified_route,
    route_timeout_seconds,
    schema_sha256,
)

from apps.adviser_v2.crypto import commitment
from apps.adviser_v2.models import (
    ModelAttempt,
    ModelQualification,
    ModelRoute,
    ProcessingJob,
)
from apps.adviser_v2.qualification_suite import expected_qualification_hashes
from apps.adviser_v2.role_routes import RoleRoute
from apps.adviser_v2.schemas import PolicyRuleExtractionV1
from apps.adviser_v2.storage import store_model_result
from apps.adviser_v2.tests.test_pipeline import public_html_capture


def test_historical_model_roles_are_retained_only_in_research_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("COVERGUIDE_CUSTOMER_INTERPRETATION_MODEL", raising=False)
    monkeypatch.delenv("COVERGUIDE_COMPARISON_MODEL", raising=False)
    root = Path(__file__).resolve().parents[3]
    live = runpy.run_path(str(root / 'config/settings.py'))
    assert not any(key in live for key in ('COVERGUIDE_POLICY_REVIEW_MODEL', 'COVERGUIDE_POLICY_EXTRACTION_MODEL',
                                         'OMNIROUTE_ENABLED', 'COVERGUIDE_EVIDENCE_RETRIEVAL'))
    defaults = runpy.run_path(str(root / 'research_workspace/test_settings.py'))
    assignments = {
        "fact_interpretation": defaults["COVERGUIDE_CUSTOMER_INTERPRETATION_MODEL"],
        "policy_extraction": defaults["COVERGUIDE_POLICY_EXTRACTION_MODEL"],
        "policy_review": defaults["COVERGUIDE_POLICY_REVIEW_MODEL"],
        "comparison_answer": defaults["COVERGUIDE_COMPARISON_MODEL"],
    }

    assert assignments == {
        "fact_interpretation": "gpt-5.6-luna",
        "policy_extraction": "gpt-5.6-sol",
        "policy_review": "gpt-5.6-terra",
        "comparison_answer": "gpt-5.6-sol",
    }
    assert all("astra" not in model.casefold() for model in assignments.values())


def test_qualified_route_checks_closed_capability_object_without_json_path_lookup(
    db: None,
) -> None:
    role_route = RoleRoute.relay("gpt-5.6-sol")
    route = ModelRoute.objects.create(
        route_key=role_route.route_key,
        endpoint_profile=role_route.endpoint_profile,
        requested_model=role_route.requested_model,
        adapter_version=role_route.configuration["adapter_version"],
        configuration_sha256=role_route.configuration_sha256,
    )
    qualification = ModelQualification.objects.create(
        route=route,
        schema_name="policy_extraction",
        schema_sha256=schema_sha256(PolicyRuleExtractionV1),
        observed_model="gpt-5.6-sol",
        capabilities={
            "structured_output": True,
            "max_context_tokens_tested": 1000,
            "image_input_tested": False,
            "image_formats": [],
            "schema_test_artifact_hashes": ["b" * 64],
            "identity_exact": True,
            "latency_ms": 10,
            "limitations": [],
            **expected_qualification_hashes("policy_extraction", PolicyRuleExtractionV1),
            "case_total": 1,
            "case_passed": 1,
            "failure_categories": [],
            "p95_latency_ms": 10,
        },
        result="passed",
    )

    assert (
        qualified_route("gpt-5.6-sol", "policy_extraction", PolicyRuleExtractionV1).id
        == qualification.id
    )


def test_offline_processing_uses_its_explicit_deadline(settings: Any) -> None:
    settings.AI_TURN_TIMEOUT_SECONDS = 120

    assert route_timeout_seconds(processing=True, remaining_seconds=1_800) == 1_800
    assert route_timeout_seconds(processing=False, remaining_seconds=1_800) == 120


def test_offline_processing_reuses_an_exact_successful_response(db: None, monkeypatch: Any) -> None:
    capture = public_html_capture()
    job = ProcessingJob.objects.create(
        source_capture=capture,
        stage="extract",
        adapter_version="test/1",
        input_commitment="c" * 64,
    )
    role_route = RoleRoute.relay("gpt-5.6-sol")
    route = ModelRoute.objects.create(
        route_key=role_route.route_key,
        endpoint_profile=role_route.endpoint_profile,
        requested_model=role_route.requested_model,
        adapter_version=role_route.configuration["adapter_version"],
        configuration_sha256=role_route.configuration_sha256,
    )
    qualification = ModelQualification.objects.create(
        route=route,
        schema_name="policy_extraction",
        schema_sha256=schema_sha256(PolicyRuleExtractionV1),
        observed_model="gpt-5.6-sol",
        capabilities={
            "structured_output": True,
            "max_context_tokens_tested": 1000,
            "image_input_tested": False,
            "image_formats": [],
            "schema_test_artifact_hashes": ["e" * 64],
            "identity_exact": True,
            "latency_ms": 10,
            "limitations": [],
            **expected_qualification_hashes("policy_extraction", PolicyRuleExtractionV1),
            "case_total": 1,
            "case_passed": 1,
            "failure_categories": [],
            "p95_latency_ms": 10,
        },
        result="passed",
    )
    messages = [{"role": "user", "content": "Fixed public policy passages."}]
    request_data = {
        "model": "gpt-5.6-sol",
        "expected_model": "gpt-5.6-sol",
        "endpoint_profile": role_route.endpoint_profile,
        "route_key": route.route_key,
        "route_configuration_sha256": route.configuration_sha256,
        "qualification_id": str(qualification.id),
        "schema": "policy_extraction",
        "schema_sha256": qualification.schema_sha256,
        "messages": messages,
    }
    now = timezone.now()
    attempt = ModelAttempt.objects.create(
        processing_job=job,
        qualification=qualification,
        attempt_number=1,
        started_at=now,
        completed_at=now,
        observed_model="gpt-5.6-sol",
        status="succeeded",
        usage={
            "input_tokens": 10,
            "output_tokens": 10,
            "cached_input_tokens": 0,
            "latency_ms": 10,
            "usage_source": "provider_reported",
        },
        request_commitment=commitment(request_data),
    )
    output = PolicyRuleExtractionV1(
        schema_version=1,
        policy_version_id="version-1",
        rules=[],
        omitted_inventory_categories=[],
        material_issues=[],
    )
    stored = store_model_result(None, str(attempt.id), output.model_dump_json().encode())
    attempt.response_storage_key = stored.storage_key
    attempt.response_storage_sha256 = stored.stored_sha256
    attempt.save(update_fields=["response_storage_key", "response_storage_sha256"])

    async def unexpected_generate(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("An exact successful processing response must not call the relay.")

    monkeypatch.setattr(
        "research_workspace.legacy_v2.model_gateway.StrictRelayAdapter.generate",
        unexpected_generate,
    )

    observed = call_model(
        model="gpt-5.6-sol",
        schema_name="policy_extraction",
        output_type=PolicyRuleExtractionV1,
        messages=messages,
        remaining_seconds=60,
        processing_job=job,
        reuse_successful_processing_result=True,
    )

    assert observed == output
    assert ModelAttempt.objects.filter(processing_job=job).count() == 1

    # Different generation options must not reuse a response from another request.
    async def changed_generate(adapter, messages, remaining_seconds, output_type, **options):
        assert options == {"reasoning_effort": "low", "max_output_tokens": 8192}
        adapter.reported_model = "gpt-5.6-sol"
        adapter.usage = {
            "input_tokens": 500,
            "cached_input_tokens": 384,
            "reasoning_tokens": 12,
            "output_tokens": 40,
        }
        return output

    monkeypatch.setattr(
        "research_workspace.legacy_v2.model_gateway.StrictRelayAdapter.generate", changed_generate
    )
    assert (
        call_model(
            model="gpt-5.6-sol",
            schema_name="policy_extraction",
            output_type=PolicyRuleExtractionV1,
            messages=messages,
            remaining_seconds=60,
            processing_job=job,
            reuse_successful_processing_result=True,
            reasoning_effort="low",
            max_output_tokens=8192,
        )
        == output
    )
    changed = ModelAttempt.objects.filter(processing_job=job).latest("started_at")
    assert changed.id != attempt.id
    assert changed.request_commitment != attempt.request_commitment
    assert changed.usage["cached_input_tokens"] == 384
    from apps.adviser_v2.contracts import validate_contract

    validate_contract("UsageV1", changed.usage)

    async def incomplete(adapter, *args, **options):
        from research_workspace.legacy_relay import RelayFailure

        adapter.usage = {
            "input_tokens": 500,
            "cached_input_tokens": 384,
            "reasoning_tokens": 12,
            "output_tokens": 40,
        }
        raise RelayFailure("incomplete_response", "The selected model did not finish its answer.")

    monkeypatch.setattr("research_workspace.legacy_v2.model_gateway.StrictRelayAdapter.generate", incomplete)
    from research_workspace.legacy_relay import RelayFailure

    with pytest.raises(RelayFailure):
        call_model(
            model="gpt-5.6-sol",
            schema_name="policy_extraction",
            output_type=PolicyRuleExtractionV1,
            messages=messages,
            remaining_seconds=60,
            processing_job=job,
        )
    failed = ModelAttempt.objects.filter(processing_job=job).latest("started_at")
    assert failed.error_code == "incomplete_response"
    assert failed.usage["output_tokens"] == 40
    assert failed.usage["cached_input_tokens"] == 384
    validate_contract("UsageV1", failed.usage)
