"""Fresh, one-attempt qualification of exact relay identities and v2 schemas."""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from typing import Any

import httpx
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.adviser.ai import RelayFailure, RelayRoute, StrictRelayAdapter
from apps.adviser.providers import provider_config
from apps.adviser_v2.contracts import validate_contract
from apps.adviser_v2.model_gateway import schema_sha256
from apps.adviser_v2.models import ModelQualification, ModelRoute
from apps.adviser_v2.rule_validation import rule_semantic_problems
from apps.adviser_v2.schemas import (
    CustomerInterpretationV1,
    PolicyRuleExtractionV1,
    PolicyRuleReviewV1,
    RecommendationDraftV1,
    StrictOutput,
)

TEST_POLICY_ID = "11111111-1111-4111-8111-111111111111"
TEST_SPAN_ID = "22222222-2222-4222-8222-222222222222"
TEST_RULE_BODY = {
    "schema_version": 1,
    "applies_when": {"node": "constant", "value": "true"},
    "inputs": [],
    "effects": [
        {
            "kind": "definition",
            "target_key": "qualification.term",
            "scope": {
                "subject": "person",
                "subject_ids": [],
                "period": "per_event",
                "benefit_keys": [],
                "reset": "never",
            },
            "term_key": "qualification.term",
            "value": {"node": "literal", "value": {"kind": "boolean", "value": True}},
        }
    ],
    "mandatory_rule_keys": [],
    "source_span_ids": [TEST_SPAN_ID],
    "unresolved": [],
    "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
}
TEST_RULE_BODY_JSON = json.dumps(TEST_RULE_BODY, separators=(",", ":"))


def _requests() -> list[tuple[str, str, type[StrictOutput], list[dict[str, str]]]]:
    return [
        (
            settings.COVERGUIDE_CUSTOMER_INTERPRETATION_MODEL,
            "fact_interpretation",
            CustomerInterpretationV1,
            [
                {
                    "role": "system",
                    "content": (
                        "Return CustomerInterpretationV1 for the exact five-character message. "
                        "Map it as one context statement at offsets 0 and 5, no subjects, facts, "
                        "requirements, corrections or ambiguity; intent conversation."
                    ),
                },
                {"role": "user", "content": "Hello"},
            ],
        ),
        (
            settings.COVERGUIDE_POLICY_EXTRACTION_MODEL,
            "policy_extraction",
            PolicyRuleExtractionV1,
            [
                {
                    "role": "system",
                    "content": (
                        "Return PolicyRuleExtractionV1 for policy_version_id "
                        f"{TEST_POLICY_ID}. Use schema_version 1. Return exactly one rules item with "
                        "rule_key qualification_definition, rule_type definition, inventory_category "
                        "eligibility, evidence_span_ids containing only "
                        f"{TEST_SPAN_ID}, table_cells and table_footnote_span_ids as empty arrays, "
                        "and body equal to this exact JSON-encoded object string: "
                        f"{TEST_RULE_BODY_JSON}. Omitted inventory categories and material issues "
                        "must both be empty arrays."
                    ),
                },
                {"role": "user", "content": "The defined test term is true."},
            ],
        ),
        (
            settings.COVERGUIDE_POLICY_REVIEW_MODEL,
            "policy_review",
            PolicyRuleReviewV1,
            [
                {
                    "role": "system",
                    "content": (
                        "Return PolicyRuleReviewV1 for policy_version_id "
                        f"{TEST_POLICY_ID}. Use schema_version 1. Inventory categories contains only "
                        "eligibility and reviews is empty. Put exactly one item in missing_rules with "
                        "rule_key qualification_definition, rule_type definition, inventory_category "
                        "eligibility, evidence_span_ids containing only "
                        f"{TEST_SPAN_ID}, table_cells and table_footnote_span_ids as empty arrays, "
                        "and body equal to this exact JSON-encoded object string: "
                        f"{TEST_RULE_BODY_JSON}."
                    ),
                },
                {"role": "user", "content": "The defined test term is true."},
            ],
        ),
        (
            settings.COVERGUIDE_FINAL_EXPLANATION_MODEL,
            "recommendation_answer",
            RecommendationDraftV1,
            [
                {
                    "role": "system",
                    "content": (
                        "Return RecommendationDraftV1 with outcome insufficient_evidence, a short "
                        "introduction saying evidence is insufficient, no statements, and a follow_up "
                        "asking for the missing evidence."
                    ),
                },
                {"role": "user", "content": "Recommend a policy."},
            ],
        ),
    ]


def _semantic_check(schema_name: str, result: StrictOutput) -> None:
    if schema_name == "fact_interpretation":
        interpretation = CustomerInterpretationV1.model_validate(result)
        if len(interpretation.statements) != 1 or interpretation.statements[0].start_offset != 0:
            raise ValueError("Interpretation qualification did not preserve the required offset.")
    elif schema_name == "policy_extraction":
        extraction = PolicyRuleExtractionV1.model_validate(result)
        if extraction.policy_version_id != TEST_POLICY_ID or len(extraction.rules) != 1:
            raise ValueError("Extraction qualification changed the pinned identities.")
        validate_contract("RuleV1", extraction.rules[0].body)
        semantic_problems = rule_semantic_problems(extraction.rules[0].body)
        if semantic_problems:
            raise ValueError("Extraction qualification returned invalid rule semantics.")
        if extraction.rules[0].body != TEST_RULE_BODY:
            raise ValueError("Extraction qualification changed the pinned rule body.")
    elif schema_name == "policy_review":
        review = PolicyRuleReviewV1.model_validate(result)
        if review.policy_version_id != TEST_POLICY_ID or len(review.missing_rules) != 1:
            raise ValueError("Review qualification changed the pinned identities.")
        validate_contract("RuleV1", review.missing_rules[0].body)
        semantic_problems = rule_semantic_problems(review.missing_rules[0].body)
        if semantic_problems:
            raise ValueError("Review qualification returned invalid rule semantics.")
        if review.missing_rules[0].body != TEST_RULE_BODY:
            raise ValueError("Review qualification changed the pinned rule body.")
    else:
        recommendation = RecommendationDraftV1.model_validate(result)
        if recommendation.outcome != "insufficient_evidence" or recommendation.statements:
            raise ValueError("Recommendation qualification invented a supported answer.")


async def _call(
    model: str, output_type: type[StrictOutput], messages: list[dict[str, str]]
) -> tuple[StrictOutput, StrictRelayAdapter]:
    route = RelayRoute(
        relay_type="cliproxyapi",
        base_url=provider_config("cliproxyapi").base_url,
        model=model,
        api_dialect="openai_responses",
        context_limit=1_000_000,
        timeout_seconds=120,
        qualified=True,
    )
    async with httpx.AsyncClient(trust_env=False) as client:
        adapter = StrictRelayAdapter(route, client, provider_config(route.relay_type).api_key)
        result = await adapter.generate(messages, 120, output_type)
        return result, adapter


class Command(BaseCommand):
    help = "Qualify the four exact v2 model/schema routes with one fresh attempt each."

    def handle(self, *args: Any, **options: Any) -> None:
        failures: list[str] = []
        for model, schema_name, output_type, messages in _requests():
            configuration = {
                "endpoint_profile": "shared-job-in-loopback-relay",
                "base_url": settings.AI_RELAY_BASE_URL,
                "requested_model": model,
                "adapter_version": "strict-relay-v2/1",
            }
            configuration_hash = hashlib.sha256(
                json.dumps(configuration, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            route, _ = ModelRoute.objects.get_or_create(
                route_key=f"{model}:{configuration_hash[:16]}",
                defaults={
                    "endpoint_profile": configuration["endpoint_profile"],
                    "requested_model": model,
                    "adapter_version": configuration["adapter_version"],
                    "configuration_sha256": configuration_hash,
                },
            )
            started = time.monotonic()
            result_name = "failed"
            observed_model = ""
            artifact_hashes: list[str] = []
            limitations: list[str] = []
            try:
                result, adapter = asyncio.run(_call(model, output_type, messages))
                _semantic_check(schema_name, result)
                observed_model = adapter.reported_model
                artifact_hashes = [
                    hashlib.sha256(
                        json.dumps(
                            {
                                "messages": messages,
                                "result": result.model_dump(mode="json"),
                            },
                            sort_keys=True,
                            separators=(",", ":"),
                        ).encode()
                    ).hexdigest()
                ]
                result_name = "passed"
            except (RelayFailure, ValueError) as exc:
                limitations.append(f"{type(exc).__name__}:{getattr(exc, 'code', str(exc))}")
                failures.append(f"{model}:{schema_name}:{limitations[-1]}")
            ModelQualification.objects.create(
                route=route,
                schema_name=schema_name,
                schema_sha256=schema_sha256(output_type),
                observed_model=observed_model,
                capabilities={
                    "structured_output": result_name == "passed",
                    "max_context_tokens_tested": 0,
                    "image_input_tested": False,
                    "image_formats": [],
                    "schema_test_artifact_hashes": artifact_hashes,
                    "identity_exact": observed_model == model,
                    "latency_ms": round((time.monotonic() - started) * 1000),
                    "limitations": limitations,
                },
                result=result_name,
            )
            self.stdout.write(f"{model} {schema_name}: {result_name}")
        if failures:
            raise CommandError("Fresh relay qualification failed: " + "; ".join(failures))
        self.stdout.write(self.style.SUCCESS("All four exact v2 model/schema routes passed."))
