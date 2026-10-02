from __future__ import annotations

import json
import time
from types import SimpleNamespace

import httpx
import pytest
from research_workspace.legacy_relay import RelayFailure, StrictRelayAdapter

from apps.adviser.tests.test_ai import envelope, route
from apps.adviser_v2.processing import stages
from apps.adviser_v2.processing.criterion_evidence import CRITERIA
from apps.adviser_v2.schemas import PolicyRuleExtractionV1, PolicyRuleReviewV1


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["completed", "incomplete"])
async def test_generation_options_and_usage_survive_incomplete_output(status):
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json=envelope(
                status=status,
                usage={
                    "input_tokens": 500,
                    "output_tokens": 40,
                    "total_tokens": 540,
                    "input_tokens_details": {"cached_tokens": 384},
                    "output_tokens_details": {"reasoning_tokens": 12},
                },
            ),
        )

    from research_workspace.legacy_relay import StructuredAnswerDraft

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = StrictRelayAdapter(route(), client, "secret")
        if status == "incomplete":
            with pytest.raises(RelayFailure, match="did not finish"):
                await adapter.generate(
                    [], 5, StructuredAnswerDraft, reasoning_effort="low", max_output_tokens=8192
                )
        else:
            await adapter.generate(
                [], 5, StructuredAnswerDraft, reasoning_effort="low", max_output_tokens=8192
            )
    assert requests[0]["reasoning"] == {"effort": "low"}
    assert requests[0]["max_output_tokens"] == 8192
    assert adapter.usage["cached_input_tokens"] == 384
    assert adapter.usage["reasoning_tokens"] == 12


@pytest.mark.asyncio
async def test_other_routes_keep_default_generation_options_and_unknown_usage():
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json=envelope(
                usage={
                    "input_tokens_details": {"cached_tokens": True},
                    "output_tokens_details": {"reasoning_tokens": -1},
                }
            ),
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        adapter = StrictRelayAdapter(route(), client, "secret")
        await adapter.generate_structured_answer([], 5)
    assert "reasoning" not in requests[0] and "max_output_tokens" not in requests[0]
    assert "cached_input_tokens" not in adapter.usage and "reasoning_tokens" not in adapter.usage


@pytest.mark.parametrize("review", [False, True])
def test_actual_criterion_calls_share_full_prefix_before_dynamic_instructions(
    monkeypatch, settings, review
):
    settings.COVERGUIDE_POLICY_EXTRACTION_REASONING_EFFORT = "medium"
    settings.COVERGUIDE_POLICY_EXTRACTION_MAX_OUTPUT_TOKENS = 8192
    requests = []
    monkeypatch.setattr(stages, "_selected_variant_name", lambda _: "Base policy")
    monkeypatch.setattr(stages, "_renew_rule_lease", lambda _: None)
    version = SimpleNamespace(id="policy", uin="exact-uin")
    passages = json.dumps([{"evidence_span_id": "source", "passage": "FULL ORIGINAL TEXT"}])

    def call_model(**kwargs):
        requests.append(kwargs)
        criterion = CRITERIA[len(requests) - 1]
        if review:
            return PolicyRuleReviewV1(
                schema_version=1,
                policy_version_id="policy",
                inventory_categories=[criterion.category],
                reviews=[],
                missing_rules=[],
            )
        return PolicyRuleExtractionV1(
            schema_version=1,
            policy_version_id="policy",
            rules=[],
            omitted_inventory_categories=[criterion.category],
            material_issues=[
                f"{criterion.category}: {criterion.key}: Source does not answer this."
            ],
        )

    monkeypatch.setattr(stages, "call_model", call_model)
    for criterion in CRITERIA[:2]:
        kwargs = dict(
            job=SimpleNamespace(),
            policy_version=version,
            encoded_passages=passages,
            categories=(criterion.category,),
            evidence_batch_label="1/1",
            deadline=time.monotonic() + 60,
            criterion=criterion,
            max_attempts=1,
        )
        if review:
            stages._run_review_batch(**kwargs, candidates=())
        else:
            stages._run_extraction_batch(**kwargs, correction_context="RETRY LAST")
    assert requests[0]["messages"][:3] == requests[1]["messages"][:3]
    assert passages in requests[0]["messages"][2]["content"]
    assert "Fixed inventory batch" in requests[0]["messages"][3]["content"]
    assert "sum_insured" in requests[0]["messages"][-1 if review else -2]["content"]
    if review:
        assert requests[0]["reasoning_effort"] == "high"
        assert "max_output_tokens" not in requests[0]
    else:
        assert requests[0]["messages"][-1]["content"] == "RETRY LAST"
        assert requests[0]["reasoning_effort"] == "medium"
        assert requests[0]["max_output_tokens"] == 8192
