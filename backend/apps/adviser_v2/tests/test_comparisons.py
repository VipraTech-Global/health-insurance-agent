from __future__ import annotations

import uuid
from types import SimpleNamespace
from typing import Any, cast

import pytest

from apps.accounts.models import User
from apps.adviser_v2.engine import _comparison_contract_guidance, _comparison_messages
from apps.adviser_v2.errors import UnsupportedComparisonError
from apps.adviser_v2.schemas import ComparisonDraftV1
from apps.adviser_v2.services.comparisons import (
    COMPARISON_FRAMING,
    ComparisonContext,
    _blank_ids_to_none,
    clarification_draft,
    validate_comparison_draft,
)


def _statement(text: str, **updates: Any) -> dict[str, Any]:
    value = {
        "text": text,
        "statement_type": "benefit",
        "comparison_assessment_id": str(uuid.uuid4()),
        "requirement_match_id": None,
        "calculation_id": None,
        "citations": [
            {
                "evidence_span_id": str(uuid.uuid4()),
                "policy_rule_id": str(uuid.uuid4()),
                "role": "supports",
            }
        ],
    }
    value.update(updates)
    return value


def test_comparison_prompt_keeps_outcome_and_customer_framing_in_the_application() -> None:
    guidance = _comparison_contract_guidance()
    messages = _comparison_messages(
        {
            "catalogue_limit": "2 reviewed products",
            "products": [{"product": "A"}, {"product": "B"}],
        }
    )

    assert "application supplies" in guidance
    assert "Do not rank, endorse, shortlist, identify a winner" in messages[0]["content"]
    assert '"products": [{"product": "A"}, {"product": "B"}]' in messages[1]["content"]
    assert COMPARISON_FRAMING == (
        "CoverGuide compares the reviewed products against the criteria you shared. "
        "It does not choose a policy; the decision is yours."
    )


def test_only_whitespace_optional_ids_are_normalized_to_null() -> None:
    draft = ComparisonDraftV1.model_validate(
        {
            "schema_version": 1,
            "statements": [
                _statement(
                    "A cited fact.",
                    comparison_assessment_id=" \t",
                    requirement_match_id=str(uuid.uuid4()),
                    calculation_id="",
                    citations=[
                        {
                            "evidence_span_id": str(uuid.uuid4()),
                            "policy_rule_id": " ",
                            "role": "supports",
                        }
                    ],
                )
            ],
        }
    )

    normalized = _blank_ids_to_none(draft).statements[0]
    assert normalized.comparison_assessment_id is None
    assert normalized.calculation_id is None
    assert normalized.citations[0].policy_rule_id is None


@pytest.mark.django_db
@pytest.mark.parametrize(
    "text",
    [
        "This is the best policy.",
        "Choose this product.",
        "It is our top pick.",
        "Buy this policy.",
        "This product is better.",
    ],
)
def test_generated_endorsement_or_purchase_language_fails_closed(v2_user: User, text: str) -> None:
    assessment_id = uuid.uuid4()
    draft = ComparisonDraftV1.model_validate(
        {
            "schema_version": 1,
            "statements": [_statement(text, comparison_assessment_id=str(assessment_id))],
        }
    )
    context = ComparisonContext(
        comparison=cast(
            Any,
            SimpleNamespace(owner_id=v2_user.id, advice_request=None, outcome="completed"),
        ),
        assessments=(
            cast(
                Any,
                SimpleNamespace(
                    id=assessment_id,
                    product_variant=SimpleNamespace(policy_version_id=uuid.uuid4()),
                ),
            ),
        ),
        matches=(),
        needs=(),
        evaluations=(),
    )

    with pytest.raises(UnsupportedComparisonError, match="ranking, endorsement"):
        validate_comparison_draft(draft, context, {})


def test_source_quotes_are_not_scanned_as_generated_endorsement_language() -> None:
    draft = ComparisonDraftV1.model_validate(
        {"schema_version": 1, "statements": [_statement("A cited factual limit applies.")]}
    )
    normalized = _blank_ids_to_none(draft)

    assert normalized.statements[0].text == "A cited factual limit applies."
    assert normalized.statements[0].citations


def test_clarification_draft_contains_no_generated_prose() -> None:
    draft = clarification_draft("Which city?", cast(Any, SimpleNamespace()))

    assert draft == ComparisonDraftV1(schema_version=1, statements=[])
