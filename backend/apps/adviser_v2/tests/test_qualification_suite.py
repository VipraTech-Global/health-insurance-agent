from __future__ import annotations

from typing import Any

import pytest

from apps.adviser.ai import RelayFailure
from apps.adviser_v2.management.commands import qualify_v2_models
from apps.adviser_v2.management.commands.qualify_v2_models import SuiteResult
from apps.adviser_v2.qualification_suite import COMPARISON_CASES, INTERPRETATION_CASES
from apps.adviser_v2.role_routes import RoleRoute
from apps.adviser_v2.schemas import ComparisonDraftV1


def result(model: str, *, passed: int = 8, p95: int = 100) -> SuiteResult:
    return SuiteResult(
        role="comparison_answer",
        route=RoleRoute("omniroute", model, model.removeprefix("gemini/")),
        passed=passed,
        total=8,
        p95_latency_ms=p95,
        failure_categories=(),
        artifact_hashes=(),
        identity_exact=True,
    )


def test_interactive_smoke_suite_has_fixed_case_totals() -> None:
    assert len(INTERPRETATION_CASES) == 12
    assert len(COMPARISON_CASES) == 8


def test_qualification_numbers_match_production_grouping_semantics() -> None:
    assert qualify_v2_models._numbers_in("INR 1,000,000 and 500000") == {
        "1000000",
        "500000",
    }


def test_interpretation_prompt_bounds_python_unicode_offsets() -> None:
    case = next(item for item in INTERPRETATION_CASES if item.name == "utf8-offsets")
    prompt = qualify_v2_models._messages_for_interpretation(case)[0]["content"]
    assert f"length is {len(case.text)} characters" in prompt
    assert "never UTF-8 byte offsets" in prompt


def test_selection_prefers_assertions_then_latency_then_gemini_35() -> None:
    model_35, model_31 = qualify_v2_models.GEMINI_REQUESTED_MODELS
    assert qualify_v2_models._selected(
        [result(model_35, passed=7), result(model_31)], "comparison_answer"
    ).route.requested_model == model_31
    assert qualify_v2_models._selected(
        [result(model_35, p95=200), result(model_31, p95=100)], "comparison_answer"
    ).route.requested_model == model_31
    assert qualify_v2_models._selected(
        [result(model_31), result(model_35)], "comparison_answer"
    ).route.requested_model == model_35


@pytest.mark.parametrize("code", ["provider_transport", "provider_quota"])
def test_only_no_output_transport_or_quota_failure_is_retried(
    monkeypatch: Any, code: str
) -> None:
    calls: list[str] = []
    route = RoleRoute("omniroute", "gemini/test", "test")

    async def fake_call(*args: Any) -> tuple[ComparisonDraftV1, str, int]:
        calls.append(args[0].requested_model)
        if len(calls) == 1:
            raise RelayFailure(code, "safe synthetic failure")
        return ComparisonDraftV1(schema_version=1, statements=[]), "test", 1

    monkeypatch.setattr(qualify_v2_models, "_call", fake_call)
    output, observed, _latency = qualify_v2_models._run_call(
        route, ComparisonDraftV1, [{"role": "user", "content": "synthetic"}]
    )
    assert output.statements == []
    assert observed == "test"
    assert calls == ["gemini/test", "gemini/test"]


@pytest.mark.parametrize(
    "code", ["invalid_structured_output", "model_identity_mismatch", "provider_timeout"]
)
def test_semantic_schema_identity_and_timeout_failures_are_not_retried(
    monkeypatch: Any, code: str
) -> None:
    calls = 0

    async def fake_call(*args: Any) -> tuple[ComparisonDraftV1, str, int]:
        nonlocal calls
        calls += 1
        raise RelayFailure(code, "safe synthetic failure")

    monkeypatch.setattr(qualify_v2_models, "_call", fake_call)
    with pytest.raises(RelayFailure, match="safe synthetic failure"):
        qualify_v2_models._run_call(
            RoleRoute("omniroute", "gemini/test", "test"),
            ComparisonDraftV1,
            [{"role": "user", "content": "synthetic"}],
        )
    assert calls == 1
