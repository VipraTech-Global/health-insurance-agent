from __future__ import annotations

import uuid
from datetime import timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
from django.utils import timezone

from apps.accounts.models import User
from apps.adviser_v2.crypto import commitment
from apps.adviser_v2.engine import _recommendation_contract_guidance, _recommendation_messages
from apps.adviser_v2.errors import UnsupportedRecommendationError
from apps.adviser_v2.models import (
    InformationNeed,
    KnowledgeChannel,
    KnowledgeRelease,
    Message,
    Recommendation,
    Turn,
)
from apps.adviser_v2.retrieval import PolicyRetrievalContext
from apps.adviser_v2.rule_engine import Truth
from apps.adviser_v2.schemas import CustomerInterpretationV1, RecommendationDraftV1
from apps.adviser_v2.services.customer import create_conversation
from apps.adviser_v2.services.interpretation import apply_interpretation
from apps.adviser_v2.services.recommendations import (
    RecommendationContext,
    _allowed_citation_roles,
    _append_soft_fact_limitations,
    _canonicalize_statement_references,
    _distinct_citations_for_storage,
    _numbers_in,
    _room_ratio_percent,
    already_asked_information_keys,
    model_context,
    next_missing_core_fact,
    validate_recommendation_draft,
)


def test_room_claim_ratio_is_supplied_in_the_same_form_the_answer_uses() -> None:
    inputs = [
        {"value": {"value": "5000"}},
        {"value": {"value": "10000"}},
    ]
    ratio = _room_ratio_percent(inputs)
    assert ratio == "50"
    assert _numbers_in("The payable portion is 50%") <= _numbers_in(ratio)


def test_recommendation_prompt_exposes_policy_claim_citation_rules() -> None:
    guidance = _recommendation_contract_guidance()

    assert "eligibility requirement_match benefit restriction price provider calculation" in guidance
    assert "must include at least one supplied citation" in guidance
    assert "unknown or unavailable evidence" in guidance
    assert "statement_type limitation" in guidance


def test_allowed_citation_roles_are_derived_from_evidence_relationships() -> None:
    assert _allowed_citation_roles({"restricts"}) == ["restricts"]
    assert _allowed_citation_roles({"supports"}) == ["assumption_source", "supports"]
    assert _allowed_citation_roles({"contradicts"}) == ["conflicts"]


def test_shared_source_passage_is_stored_once_per_statement_and_role() -> None:
    span_id = str(uuid.uuid4())
    citations = [
        SimpleNamespace(evidence_span_id=span_id, role="restricts", policy_rule_id=str(uuid.uuid4())),
        SimpleNamespace(evidence_span_id=span_id, role="restricts", policy_rule_id=str(uuid.uuid4())),
    ]
    assert _distinct_citations_for_storage(citations) == citations[:1]


def test_recommendation_messages_send_profile_once_via_decision_context() -> None:
    decision_context = {
        "catalogue_limit": "the published reviewed products",
        "customer_profile": {"age": 32, "city": "Bengaluru"},
        "candidates": [],
    }

    messages = _recommendation_messages(decision_context)

    serialized = [message["content"] for message in messages]
    assert not any(content.startswith("Customer profile: ") for content in serialized)

    decision_context_messages = [
        content for content in serialized if content.startswith("Validated decision context: ")
    ]
    assert len(decision_context_messages) == 1
    assert "Bengaluru" in decision_context_messages[0]

    profile_occurrences = sum(content.count("Bengaluru") for content in serialized)
    assert profile_occurrences == 1


def _draft_with_statement(**reference_fields: str | None) -> RecommendationDraftV1:
    return RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "completed",
            "introduction": "Introduction.",
            "statements": [
                {
                    "text": "This limitation applies.",
                    "statement_type": "limitation",
                    "critical": False,
                    "candidate_assessment_id": None,
                    "requirement_match_id": None,
                    "information_need_id": None,
                    "calculation_id": None,
                    "citations": [],
                    **reference_fields,
                }
            ],
            "follow_up": None,
        }
    )


def _context_with_match(match_id: uuid.UUID, candidate_id: uuid.UUID) -> RecommendationContext:
    match = SimpleNamespace(id=match_id, candidate_assessment_id=candidate_id)
    return RecommendationContext(
        recommendation=cast(Any, SimpleNamespace()),
        candidates=(),
        matches=(cast(Any, match),),
        needs=(),
        evaluations=(),
    )


def test_canonicalize_drops_redundant_candidate_id_matching_its_requirement_match() -> None:
    match_id, candidate_id = uuid.uuid4(), uuid.uuid4()
    draft = _draft_with_statement(
        candidate_assessment_id=str(candidate_id), requirement_match_id=str(match_id)
    )
    context = _context_with_match(match_id, candidate_id)

    canonicalized = _canonicalize_statement_references(draft, context)

    statement = canonicalized.statements[0]
    assert statement.candidate_assessment_id is None
    assert statement.requirement_match_id == str(match_id)


def test_canonicalize_leaves_a_mismatched_candidate_and_match_untouched() -> None:
    match_id, candidate_id, other_candidate_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    draft = _draft_with_statement(
        candidate_assessment_id=str(other_candidate_id), requirement_match_id=str(match_id)
    )
    context = _context_with_match(match_id, candidate_id)

    canonicalized = _canonicalize_statement_references(draft, context)

    statement = canonicalized.statements[0]
    assert statement.candidate_assessment_id == str(other_candidate_id)
    assert statement.requirement_match_id == str(match_id)


def test_canonicalize_leaves_information_need_combinations_untouched() -> None:
    match_id, candidate_id, need_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    context = _context_with_match(match_id, candidate_id)

    draft_with_need_and_match = _draft_with_statement(
        requirement_match_id=str(match_id), information_need_id=str(need_id)
    )
    canonicalized = _canonicalize_statement_references(draft_with_need_and_match, context)
    assert canonicalized.statements[0].requirement_match_id == str(match_id)
    assert canonicalized.statements[0].information_need_id == str(need_id)

    draft_with_need_and_candidate = _draft_with_statement(
        candidate_assessment_id=str(candidate_id), information_need_id=str(need_id)
    )
    canonicalized = _canonicalize_statement_references(draft_with_need_and_candidate, context)
    assert canonicalized.statements[0].candidate_assessment_id == str(candidate_id)
    assert canonicalized.statements[0].information_need_id == str(need_id)


def test_canonicalize_leaves_a_single_reference_or_no_reference_unchanged() -> None:
    match_id, candidate_id = uuid.uuid4(), uuid.uuid4()
    context = _context_with_match(match_id, candidate_id)

    only_candidate = _draft_with_statement(candidate_assessment_id=str(candidate_id))
    assert _canonicalize_statement_references(only_candidate, context).statements[
        0
    ].candidate_assessment_id == str(candidate_id)

    no_references = _draft_with_statement()
    unchanged = _canonicalize_statement_references(no_references, context)
    assert unchanged is no_references


@pytest.mark.django_db
def test_unsupported_number_has_a_distinct_failure_type(v2_user: User) -> None:
    draft = RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "completed",
            "introduction": "The unsupported amount is 99.",
            "statements": [],
            "follow_up": None,
        }
    )
    recommendation = SimpleNamespace(
        outcome="completed",
        owner_id=v2_user.id,
        advice_request=None,
    )
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(),
        matches=(),
        needs=(),
        evaluations=(),
    )

    with pytest.raises(UnsupportedRecommendationError, match="unsupported number"):
        validate_recommendation_draft(draft, context, {})


def test_model_context_records_the_exact_retrieval_set() -> None:
    rule_id = uuid.uuid4()
    span_id = uuid.uuid4()
    chunk = SimpleNamespace(id=uuid.uuid4(), evidence_span_ids=[str(span_id)])
    release = SimpleNamespace(
        release_label="development_alpha_3_product",
        readiness={"comparison_product_count": 3, "demo_subset": True},
    )
    recommendation = SimpleNamespace(
        id=uuid.uuid4(),
        outcome="conditional",
        owner_id=uuid.uuid4(),
        knowledge_release=release,
    )
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(),
        matches=(),
        needs=(),
        evaluations=(),
    )

    profile = {"facts": [{"fact_type": "age", "value": {"value": "32"}}]}
    payload = model_context(
        context,
        PolicyRetrievalContext(chunks=(cast(Any, chunk),), rule_ids=(rule_id,)),
        profile=profile,
    )

    assert payload["customer_profile"] == profile
    assert payload["retrieval"] == {
        "policy_search_chunk_ids": [str(chunk.id)],
        "policy_rule_ids": [str(rule_id)],
        "evidence_span_ids": [str(span_id)],
    }
    assert payload["catalogue_limit"] == "3 reviewed products"


def test_model_context_includes_each_matchs_comparison_value() -> None:
    variant_id = uuid.uuid4()
    sum_insured_requirement = SimpleNamespace(id=uuid.uuid4(), criterion="sum_insured", priority="required")
    no_copay_requirement = SimpleNamespace(id=uuid.uuid4(), criterion="no_copay", priority="preferred")
    matched_amount = {"state": "finite", "value": "1500000", "unit": "money", "currency": "INR"}
    variant = SimpleNamespace(
        id=variant_id,
        policy_version=SimpleNamespace(
            uin="UIN123",
            product=SimpleNamespace(name="Product A", insurer=SimpleNamespace(name="Insurer A")),
        ),
    )
    evaluation = SimpleNamespace(
        variant=variant,
        matches=[
            SimpleNamespace(
                requirement=sum_insured_requirement,
                outcome="meets",
                comparison_value=matched_amount,
                rule_ids=[],
            ),
            SimpleNamespace(
                requirement=no_copay_requirement,
                outcome="meets",
                comparison_value=None,
                rule_ids=[],
            ),
        ],
        rules=[],
    )
    candidate = SimpleNamespace(id=uuid.uuid4(), product_variant_id=variant_id, disposition="recommended", rank=1)
    sum_insured_match = SimpleNamespace(
        id=uuid.uuid4(),
        candidate_assessment=SimpleNamespace(product_variant_id=variant_id),
        customer_requirement_id=sum_insured_requirement.id,
    )
    no_copay_match = SimpleNamespace(
        id=uuid.uuid4(),
        candidate_assessment=SimpleNamespace(product_variant_id=variant_id),
        customer_requirement_id=no_copay_requirement.id,
    )
    release = SimpleNamespace(
        release_label="development_alpha_3_product",
        readiness={"comparison_product_count": 3, "demo_subset": True},
    )
    recommendation = SimpleNamespace(
        id=uuid.uuid4(), outcome="recommended", owner_id=uuid.uuid4(), knowledge_release=release
    )
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(cast(Any, candidate),),
        matches=(cast(Any, sum_insured_match), cast(Any, no_copay_match)),
        needs=(),
        evaluations=(cast(Any, evaluation),),
    )

    payload = model_context(context)

    requirement_matches = {
        item["requirement_match_id"]: item for item in payload["candidates"][0]["requirement_matches"]
    }
    assert requirement_matches[str(sum_insured_match.id)]["comparison_value"] == matched_amount
    assert requirement_matches[str(no_copay_match.id)]["comparison_value"] is None


@pytest.mark.django_db
def test_a_statement_may_quote_its_own_matchs_comparison_value(v2_user: User) -> None:
    match_id = uuid.uuid4()
    draft = RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "completed",
            "introduction": "Here is the comparison.",
            "statements": [
                {
                    "text": "This plan meets the requirement, offering INR 1500000 of cover.",
                    "statement_type": "limitation",
                    "critical": False,
                    "candidate_assessment_id": None,
                    "requirement_match_id": str(match_id),
                    "information_need_id": None,
                    "calculation_id": None,
                    "citations": [],
                }
            ],
            "follow_up": None,
        }
    )
    recommendation = SimpleNamespace(outcome="completed", owner_id=v2_user.id, advice_request=None)
    match = SimpleNamespace(
        id=match_id,
        candidate_assessment=SimpleNamespace(
            product_variant=SimpleNamespace(policy_version_id=uuid.uuid4())
        ),
    )
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(),
        matches=(cast(Any, match),),
        needs=(),
        evaluations=(),
    )
    supplied_context = {
        "candidates": [
            {
                "requirement_matches": [
                    {
                        "requirement_match_id": str(match_id),
                        "comparison_value": {
                            "state": "finite",
                            "value": "1500000",
                            "unit": "money",
                            "currency": "INR",
                        },
                    }
                ]
            }
        ]
    }

    validate_recommendation_draft(draft, context, supplied_context)


@pytest.mark.django_db
def test_a_statement_cannot_quote_a_different_matchs_comparison_value(v2_user: User) -> None:
    """The model must not attribute one candidate's matched amount to another (misattribution)."""

    match_a_id, match_b_id = uuid.uuid4(), uuid.uuid4()
    draft = RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "completed",
            "introduction": "Here is the comparison.",
            "statements": [
                {
                    "text": "This plan meets the requirement, offering INR 2500000 of cover.",
                    "statement_type": "limitation",
                    "critical": False,
                    "candidate_assessment_id": None,
                    "requirement_match_id": str(match_a_id),
                    "information_need_id": None,
                    "calculation_id": None,
                    "citations": [],
                }
            ],
            "follow_up": None,
        }
    )
    recommendation = SimpleNamespace(outcome="completed", owner_id=v2_user.id, advice_request=None)
    matches = tuple(
        cast(
            Any,
            SimpleNamespace(
                id=match_id,
                candidate_assessment=SimpleNamespace(
                    product_variant=SimpleNamespace(policy_version_id=uuid.uuid4())
                ),
            ),
        )
        for match_id in (match_a_id, match_b_id)
    )
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(),
        matches=matches,
        needs=(),
        evaluations=(),
    )
    supplied_context = {
        "candidates": [
            {
                "requirement_matches": [
                    {
                        "requirement_match_id": str(match_a_id),
                        "comparison_value": {
                            "state": "finite",
                            "value": "1500000",
                            "unit": "money",
                            "currency": "INR",
                        },
                    }
                ]
            },
            {
                "requirement_matches": [
                    {
                        "requirement_match_id": str(match_b_id),
                        "comparison_value": {
                            "state": "finite",
                            "value": "2500000",
                            "unit": "money",
                            "currency": "INR",
                        },
                    }
                ]
            },
        ]
    }

    with pytest.raises(UnsupportedRecommendationError, match="unsupported number"):
        validate_recommendation_draft(draft, context, supplied_context)


@pytest.mark.django_db
def test_noncritical_policy_claim_still_requires_support(v2_user: User) -> None:
    draft = RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "completed",
            "introduction": "Here is the evidence-backed comparison.",
            "statements": [
                {
                    "text": "This policy includes the requested benefit.",
                    "statement_type": "benefit",
                    "critical": False,
                    "candidate_assessment_id": None,
                    "requirement_match_id": None,
                    "information_need_id": None,
                    "calculation_id": None,
                    "citations": [],
                }
            ],
            "follow_up": None,
        }
    )
    recommendation = SimpleNamespace(
        outcome="completed",
        owner_id=v2_user.id,
        advice_request=None,
    )
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(),
        matches=(),
        needs=(),
        evaluations=(),
    )

    with pytest.raises(UnsupportedRecommendationError, match="policy claim lacks evidence"):
        validate_recommendation_draft(draft, context, {})


@pytest.mark.django_db
def test_follow_up_cannot_introduce_an_unsupported_number(v2_user: User) -> None:
    draft = RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "conditional",
            "introduction": "More information is needed.",
            "statements": [],
            "follow_up": "Please confirm whether the premium is 99999.",
        }
    )
    recommendation = SimpleNamespace(
        outcome="conditional",
        owner_id=v2_user.id,
        advice_request=None,
    )
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(),
        matches=(),
        needs=(),
        evaluations=(),
    )

    with pytest.raises(UnsupportedRecommendationError, match="follow-up"):
        validate_recommendation_draft(draft, context, {})


@pytest.mark.django_db
def test_a_comma_formatted_number_matches_the_same_figure_in_supplied_context(
    v2_user: User,
) -> None:
    """"INR 500,000" in prose must match a plain 500000 in supplied_context (same figure)."""

    draft = RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "conditional",
            "introduction": "A minimum Sum Insured of INR 500,000 is required.",
            "statements": [],
            "follow_up": "Confirm the configuration provides at least INR 500,000 of cover.",
        }
    )
    recommendation = SimpleNamespace(
        outcome="conditional",
        owner_id=v2_user.id,
        advice_request=None,
    )
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(),
        matches=(),
        needs=(),
        evaluations=(),
    )

    validate_recommendation_draft(draft, context, {"budget": {"amount": 500000}})


@pytest.mark.django_db
def test_non_excluded_candidate_requires_a_deterministic_rank(v2_user: User) -> None:
    draft = RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "conditional",
            "introduction": "More information is needed.",
            "statements": [],
            "follow_up": None,
        }
    )
    recommendation = SimpleNamespace(
        outcome="conditional",
        owner_id=v2_user.id,
        advice_request=None,
    )
    variant_id = uuid.uuid4()
    candidate = SimpleNamespace(
        id=uuid.uuid4(),
        disposition="conditional",
        rank=None,
        product_variant_id=variant_id,
        product_variant=SimpleNamespace(policy_version_id=uuid.uuid4()),
    )
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(cast(Any, candidate),),
        matches=(),
        needs=(),
        evaluations=(),
    )

    with pytest.raises(UnsupportedRecommendationError, match="deterministic rank"):
        validate_recommendation_draft(draft, context, {})


@pytest.mark.django_db
def test_clarification_draft_is_not_required_to_cite_restrictions(v2_user: User) -> None:
    """A clarification-only draft makes no policy claim, so it can't omit one either."""

    draft = RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "clarification_required",
            "introduction": "I need one detail before I can compare the reviewed policies safely.",
            "statements": [
                {
                    "text": "How old are you?",
                    "statement_type": "next_step",
                    "critical": False,
                    "candidate_assessment_id": None,
                    "requirement_match_id": None,
                    "information_need_id": None,
                    "calculation_id": None,
                    "citations": [],
                }
            ],
            "follow_up": None,
        }
    )
    recommendation = SimpleNamespace(
        outcome="clarification_required",
        owner_id=v2_user.id,
        advice_request=None,
    )
    variant_id = uuid.uuid4()
    candidate = SimpleNamespace(
        id=uuid.uuid4(),
        disposition="conditional",
        rank=1,
        product_variant_id=variant_id,
        product_variant=SimpleNamespace(policy_version_id=uuid.uuid4()),
    )
    rule = SimpleNamespace(id=uuid.uuid4(), rule_type="waiting_period", policy_version_id=uuid.uuid4())
    rule_result = SimpleNamespace(rule=rule, applies=Truth.TRUE, evidence_complete=True)
    evaluation = SimpleNamespace(variant=SimpleNamespace(id=variant_id), rules=[rule_result])
    context = RecommendationContext(
        recommendation=cast(Any, recommendation),
        candidates=(cast(Any, candidate),),
        matches=(),
        needs=(),
        evaluations=(cast(Any, evaluation),),
    )

    validate_recommendation_draft(draft, context, {})


def _known_fact(fact_type: str, value: object = "32", status: str = "reported") -> dict[str, Any]:
    return {
        "fact_type": fact_type,
        "value": {"state": "known", "kind": "quantity", "value": str(value), "unit": "year"},
        "status": status,
    }


def test_next_missing_core_fact_returns_the_first_missing_slot_in_order() -> None:
    assert next_missing_core_fact({"facts": []}, set()) == "age"

    profile_with_age = {"facts": [_known_fact("age")]}
    assert next_missing_core_fact(profile_with_age, set()) == "who"

    profile_with_all_slots = {
        "facts": [
            _known_fact("age"),
            {
                "fact_type": "intended_insured",
                "value": {"state": "known", "kind": "boolean", "value": True},
                "status": "reported",
            },
            {
                "fact_type": "city",
                "value": {"state": "known", "kind": "text", "value": "Bengaluru"},
                "status": "reported",
            },
            _known_fact("sum_insured"),
            _known_fact("budget"),
        ]
    }
    assert next_missing_core_fact(profile_with_all_slots, set()) is None


def test_next_missing_core_fact_skips_a_slot_already_asked_even_if_still_unknown() -> None:
    assert next_missing_core_fact({"facts": []}, {"age"}) == "who"


def test_next_missing_core_fact_ignores_an_unknown_value() -> None:
    profile = {"facts": [{"fact_type": "age", "value": {"state": "unknown"}, "status": "reported"}]}
    assert next_missing_core_fact(profile, set()) == "age"


def test_next_missing_core_fact_ignores_a_disputed_fact() -> None:
    profile = {"facts": [_known_fact("age", status="disputed")]}
    assert next_missing_core_fact(profile, set()) == "age"


def test_next_missing_core_fact_accepts_a_requirement_for_sum_insured_and_budget() -> None:
    profile = {
        "facts": [_known_fact("age")],
        "requirements": [
            {
                "criterion": "sum_insured",
                "target_value": {"state": "known", "kind": "quantity", "value": "500000", "unit": "INR"},
                "status": "reported",
            }
        ],
    }
    already_asked = {"who", "city"}
    assert next_missing_core_fact(profile, already_asked) == "budget"


def test_next_missing_core_fact_rejects_intended_insured_false_for_who() -> None:
    profile = {
        "facts": [
            _known_fact("age"),
            {
                "fact_type": "intended_insured",
                "value": {"state": "known", "kind": "boolean", "value": False},
                "status": "reported",
            },
        ]
    }
    assert next_missing_core_fact(profile, set()) == "who"


def _minimal_interpretation(text: str) -> CustomerInterpretationV1:
    return CustomerInterpretationV1.model_validate(
        {
            "schema_version": 1,
            "subjects": [],
            "statements": [
                {
                    "start_offset": 0,
                    "end_offset": len(text),
                    "subject_key": None,
                    "kind": "context",
                    "ambiguous": False,
                    "ambiguity_reason": None,
                }
            ],
            "facts": [],
            "requirements": [],
            "corrections": [],
            "intent": "purchase_recommendation",
            "ambiguity": False,
            "clarification_question": None,
        }
    )


def _seeded_recommendation(user: User) -> tuple[Any, Recommendation, Message]:
    """Build a real conversation -> recommendation DB chain an InformationNeed can attach to."""

    KnowledgeChannel.objects.get_or_create(name="live")
    conversation = create_conversation(user.id)
    message = Message.objects.create(
        owner_id=user.id,
        conversation=conversation,
        sequence=1,
        role="customer",
        content="I want health insurance.",
        origin="text",
        payload_commitment=commitment("I want health insurance."),
        submitted_at=timezone.now(),
    )
    applied = apply_interpretation(
        message,
        _minimal_interpretation(message.content),
        expected_profile_revision_id=conversation.current_profile_revision_id,
        expected_release_id=None,
        expected_channel_generation=0,
        expected_erasure_generation=0,
    )
    release = KnowledgeRelease.objects.create(
        release_number=KnowledgeRelease.objects.count() + 1,
        supported_scope={
            "intent_kinds": [],
            "insurer_ids": [],
            "rule_keys": [],
            "state": "blocked",
            "unresolved": [],
        },
        manifest_sha256="0" * 64,
    )
    turn = Turn.objects.create(
        owner_id=user.id,
        conversation=conversation,
        request_id=uuid.uuid4(),
        input_message=message,
        starting_profile_revision=applied.profile_revision,
        state="completed",
        deadline=timezone.now() + timedelta(minutes=5),
    )
    recommendation = Recommendation.objects.create(
        owner_id=user.id,
        turn=turn,
        advice_request=applied.advice_request,
        profile_revision=applied.profile_revision,
        knowledge_release=release,
        outcome="clarification_required",
    )
    return conversation, recommendation, message


@pytest.mark.django_db
def test_already_asked_information_keys_scopes_by_conversation_and_terminal_status(
    v2_user: User,
) -> None:
    conversation, recommendation, message = _seeded_recommendation(v2_user)
    _other_conversation, other_recommendation, _other_message = _seeded_recommendation(v2_user)

    InformationNeed.objects.create(
        owner_id=v2_user.id,
        recommendation=recommendation,
        need_kind="fact",
        information_key="age",
        reason="Need age to personalize.",
        priority="required",
        status="asked",
        asked_in_message=message,
    )
    InformationNeed.objects.create(
        owner_id=v2_user.id,
        recommendation=recommendation,
        need_kind="fact",
        information_key="budget",
        reason="Still open.",
        priority="required",
        status="open",
    )
    InformationNeed.objects.create(
        owner_id=v2_user.id,
        recommendation=other_recommendation,
        need_kind="fact",
        information_key="city",
        reason="Belongs to a different conversation.",
        priority="required",
        status="waived",
    )

    assert already_asked_information_keys(v2_user.id, conversation.id) == {"age"}


def _limitation_draft() -> RecommendationDraftV1:
    return RecommendationDraftV1.model_validate(
        {
            "schema_version": 1,
            "outcome": "completed",
            "introduction": "Here is the comparison.",
            "statements": [],
            "follow_up": None,
        }
    )


def test_append_soft_fact_limitations_flags_unknown_existing_cover_and_medical_history() -> None:
    draft = _append_soft_fact_limitations(_limitation_draft(), {"customer_profile": {"facts": []}})

    assert len(draft.statements) == 2
    assert all(item.statement_type == "limitation" for item in draft.statements)
    assert all(not item.citations for item in draft.statements)


def test_append_soft_fact_limitations_is_a_noop_when_both_are_known() -> None:
    profile = {
        "facts": [
            {
                "fact_type": "existing_cover",
                "value": {"state": "known", "kind": "boolean", "value": False},
                "status": "reported",
            },
            {
                "fact_type": "medical_history_disclosed",
                "value": {"state": "known", "kind": "boolean", "value": True},
                "status": "reported",
            },
        ]
    }

    draft = _append_soft_fact_limitations(_limitation_draft(), {"customer_profile": profile})

    assert draft.statements == []
