"""Deterministically validate and atomically publish v2 recommendations."""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.accounts.models import User

from ..crypto import commitment
from ..errors import AccountErased, PinnedStateChanged, UnsupportedRecommendationError
from ..models import (
    AdviceRequest,
    Calculation,
    Conversation,
    CustomerFact,
    CustomerProfileRevision,
    CustomerRequirement,
    InformationNeed,
    KnowledgeChannel,
    KnowledgeRelease,
    Message,
    PolicyCandidateAssessment,
    PolicyRequirementMatch,
    PolicyRuleEvidence,
    Recommendation,
    RecommendationCitation,
    RecommendationStatement,
    Turn,
)
from ..release_scope import comparison_product_count
from ..retrieval import PolicyRetrievalContext
from ..rule_engine import (
    CandidateResult,
    Truth,
    _ayush_rule_inputs,
    _room_illustration_inputs,
    current_inputs,
    evaluate_expression,
    evaluate_release,
)
from ..schemas import RecommendationDraftV1, RecommendationStatementDraft


@dataclass(frozen=True)
class RecommendationContext:
    recommendation: Recommendation
    candidates: tuple[PolicyCandidateAssessment, ...]
    matches: tuple[PolicyRequirementMatch, ...]
    needs: tuple[InformationNeed, ...]
    evaluations: tuple[CandidateResult, ...]


def _room_ratio_percent(inputs: list[dict[str, Any]]) -> str:
    ratio = (
        Decimal(inputs[0]["value"]["value"])
        / Decimal(inputs[1]["value"]["value"])
        * 100
    )
    return format(ratio.normalize(), "f")


def _save_room_illustration(
    advice_request: AdviceRequest,
    facts: list[CustomerFact],
    evaluations: list[CandidateResult],
) -> Calculation | None:
    """Calculate the stipulated associated-expense amount from the pinned rule."""

    keys = (
        "eligible_room_rent_limit",
        "room_rent_actually_incurred",
        "total_associated_medical_expenses",
    )
    by_type = {fact.fact_type: fact for fact in facts if fact.fact_type in keys}
    inputs = _room_illustration_inputs(current_inputs(facts))
    if len(by_type) != 3 or any(key not in inputs for key in keys):
        return None
    input_values: dict[str, str] = {}
    for key in keys:
        raw_input = inputs[key]
        if not isinstance(raw_input, dict) or not isinstance(raw_input.get("value"), str):
            return None
        input_values[key] = raw_input["value"]
    if inputs.get("actual_room_category_higher_than_eligible") != {
        "state": "known", "kind": "boolean", "value": True
    }:
        return None
    for evaluation in evaluations:
        if evaluation.variant.policy_version.product.name != "ReAssure 3.0":
            continue
        for rule in evaluation.rules:
            if not (
                rule.rule.rule_key
                == "room_and_icu_limits.limit.higher_room_prorates_associated_medical_expenses"
                and rule.applies == Truth.TRUE
                and rule.evidence_complete
            ):
                continue
            effect = rule.rule.body["effects"][0]
            result = evaluate_expression(effect["amount"], inputs, table_rule=rule.rule)
            if (
                result is None
                or not isinstance(result.value, Decimal)
                or result.unit != "money"
                or result.currency != "INR"
            ):
                return None
            result_value = (
                str(result.value.quantize(Decimal("1")))
                if result.value == result.value.to_integral_value()
                else format(result.value.normalize(), "f")
            )
            output = {
                "state": "finite", "value": result_value,
                "unit": "money", "currency": "INR",
            }
            evidence_ids = [str(value) for value in rule.evidence_span_ids]
            return Calculation.objects.create(
                owner_id=advice_request.owner_id,
                advice_request=advice_request,
                calculation_type="higher_room_associated_expense_proration",
                engine_version="coverguide-room-proration/1",
                inputs=[
                    {
                        "key": key,
                        "value": {
                            "state": "finite", "value": input_values[key],
                            "unit": "money", "currency": "INR",
                        },
                        "assertion_ids": [str(by_type[key].id)],
                        "span_ids": [],
                        "provenance": "customer",
                    }
                    for key in keys
                ],
                operations=[{
                    "ordinal": 1,
                    "step_key": "eligible_rent_divided_by_actual_rent_times_associated_expenses",
                    "expression": effect["amount"],
                    "input_keys": list(keys),
                    "result": output,
                    "policy_rule_ids": [str(rule.rule.id)],
                    "evidence_span_ids": evidence_ids,
                    "rounding": "none",
                }],
                result=output,
                assumptions=[{
                    "statement": "This is a stipulated higher-room claim illustration; actual claim admissibility is unresolved.",
                    "status": "stipulated", "span_ids": [],
                    "effect_if_false": "If the selected room is not above the eligible category, this proportional rule does not apply.",
                }],
                status="complete",
            )
    return None


def _current_assertions(
    owner_id: uuid.UUID,
    conversation_id: uuid.UUID,
    revision: int,
) -> tuple[list[CustomerFact], list[CustomerRequirement]]:
    fact_rows = (
        CustomerFact.objects.filter(
            owner_id=owner_id,
            introduced_in_revision__conversation_id=conversation_id,
            introduced_in_revision__revision__lte=revision,
        )
        .select_related("source_statement")
        .order_by("introduced_in_revision__revision", "created_at")
    )
    requirement_rows = CustomerRequirement.objects.filter(
        owner_id=owner_id,
        introduced_in_revision__conversation_id=conversation_id,
        introduced_in_revision__revision__lte=revision,
    ).order_by("introduced_in_revision__revision", "created_at")
    current_facts = {item.logical_key: item for item in fact_rows}
    current_requirements = {item.logical_key: item for item in requirement_rows}
    return (
        [item for item in current_facts.values() if item.status not in {"retracted", "disputed"}],
        [item for item in current_requirements.values() if item.status != "withdrawn"],
    )


CORE_FACT_SLOTS: tuple[tuple[str, frozenset[str], frozenset[str]], ...] = (
    ("age", frozenset({"age", "date_of_birth"}), frozenset()),
    ("who", frozenset({"family_composition", "purchase_for", "intended_insured"}), frozenset()),
    ("city", frozenset({"city"}), frozenset()),
    ("sum_insured", frozenset({"sum_insured"}), frozenset({"sum_insured"})),
    ("budget", frozenset({"budget"}), frozenset({"budget"})),
)

CORE_FACT_QUESTIONS: dict[str, str] = {
    "age": "How old are you (or what's your date of birth)?",
    "who": "Who do you need this cover for — just yourself, or your family as well?",
    "city": "Which city will you mainly need the policy to work in?",
    "sum_insured": "How much cover (sum insured) are you looking for?",
    "budget": "What premium budget do you have in mind?",
}

_ASSERTION_KNOWN_STATUSES = frozenset({"reported", "confirmed"})


def _fact_satisfies_slot(fact: dict[str, Any]) -> bool:
    value = fact.get("value") or {}
    if value.get("state") != "known" or fact.get("status") not in _ASSERTION_KNOWN_STATUSES:
        return False
    if fact.get("fact_type") == "intended_insured":
        return value.get("value") is True
    return True


def _requirement_satisfies_slot(requirement: dict[str, Any]) -> bool:
    target_value = requirement.get("target_value") or {}
    return (
        requirement.get("status") in _ASSERTION_KNOWN_STATUSES
        and target_value.get("state") == "known"
    )


def next_missing_core_fact(profile: dict[str, Any], already_asked: set[str]) -> str | None:
    """Return the highest-priority core fact slot still missing a known-value answer.

    A slot already in ``already_asked`` is treated as resolved even if it was
    never captured as a structured fact, so a conversation can never be asked
    about the same slot twice. A fact/requirement only resolves a slot when it
    carries a known value under an undisputed status — an ``unknown`` value or
    a ``disputed`` fact never silently satisfies the gate.
    """

    facts = profile.get("facts", [])
    requirements = profile.get("requirements", [])
    for slot_key, fact_types, requirement_criteria in CORE_FACT_SLOTS:
        if slot_key in already_asked:
            continue
        resolved = any(
            _fact_satisfies_slot(fact) for fact in facts if fact.get("fact_type") in fact_types
        )
        if not resolved and requirement_criteria:
            resolved = any(
                _requirement_satisfies_slot(requirement)
                for requirement in requirements
                if requirement.get("criterion") in requirement_criteria
            )
        if not resolved:
            return slot_key
    return None


def already_asked_information_keys(owner_id: uuid.UUID, conversation_id: uuid.UUID) -> set[str]:
    return set(
        InformationNeed.objects.filter(
            owner_id=owner_id,
            recommendation__turn__conversation_id=conversation_id,
            status__in=("asked", "resolved", "waived", "unavailable"),
        ).values_list("information_key", flat=True)
    )


@transaction.atomic
def prepare_recommendation(
    turn: Turn,
    advice_request: AdviceRequest,
    profile_revision: CustomerProfileRevision,
    release: KnowledgeRelease,
    *,
    clarification_question: str | None = None,
    information_key: str = "customer_clarification",
) -> RecommendationContext:
    facts, requirements = _current_assertions(
        turn.owner_id, turn.conversation_id, profile_revision.revision
    )
    evaluations = evaluate_release(release, facts, requirements)
    illustration = (
        None
        if clarification_question
        else _save_room_illustration(advice_request, facts, evaluations)
    )
    if clarification_question:
        outcome = "clarification_required"
    elif illustration is not None:
        outcome = "conditional"
    elif evaluations[0].disposition == "recommended":
        outcome = "completed"
    elif any(item.disposition == "conditional" for item in evaluations):
        outcome = "conditional"
    else:
        outcome = "insufficient_evidence"
    recommendation = Recommendation.objects.create(
        owner_id=turn.owner_id,
        turn=turn,
        advice_request=advice_request,
        profile_revision=profile_revision,
        knowledge_release=release,
        outcome=outcome,
    )
    candidates: list[PolicyCandidateAssessment] = []
    matches: list[PolicyRequirementMatch] = []
    for result in evaluations:
        candidate = PolicyCandidateAssessment.objects.create(
            owner_id=turn.owner_id,
            recommendation=recommendation,
            product_variant=result.variant,
            evaluated_selection={"members": [], "options": [], "quantities": []},
            selection_commitment=commitment(
                {
                    "variant": str(result.variant.id),
                    "members": [],
                    "options": [],
                    "quantities": [],
                }
            ),
            disposition=(
                "conditional"
                if illustration is not None and result.disposition in {"recommended", "alternative", "eligible"}
                else result.disposition
            ),
            rank=result.rank,
        )
        candidates.append(candidate)
        for result_match in result.matches:
            match = PolicyRequirementMatch.objects.create(
                owner_id=turn.owner_id,
                candidate_assessment=candidate,
                customer_requirement=result_match.requirement,
                outcome=result_match.outcome,
                comparison_value=result_match.comparison_value,
            )
            matches.append(match)
    needs: list[InformationNeed] = []
    if clarification_question:
        needs.append(
            InformationNeed.objects.create(
                owner_id=turn.owner_id,
                recommendation=recommendation,
                need_kind="fact",
                information_key=information_key,
                reason=clarification_question,
                priority="required",
                status="open",
            )
        )
    return RecommendationContext(
        recommendation,
        tuple(candidates),
        tuple(matches),
        tuple(needs),
        tuple(evaluations),
    )


def model_context(
    context: RecommendationContext,
    retrieval: PolicyRetrievalContext | None = None,
    *,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    candidate_by_variant = {item.product_variant_id: item for item in context.candidates}
    match_by_pair = {
        (item.candidate_assessment.product_variant_id, item.customer_requirement_id): item
        for item in context.matches
    }
    retrieved_rule_ids = (
        {str(rule_id) for rule_id in retrieval.rule_ids} if retrieval is not None else set()
    )
    release_rule_ids = {
        result.rule.id for evaluation in context.evaluations for result in evaluation.rules
    }
    evidence_roles: dict[tuple[str, str], set[str]] = {}
    for rule_id, span_id, role in PolicyRuleEvidence.objects.filter(
        policy_rule_id__in=release_rule_ids
    ).values_list("policy_rule_id", "evidence_span_id", "role"):
        evidence_roles.setdefault((str(rule_id), str(span_id)), set()).add(str(role))
    product_count = comparison_product_count(context.recommendation.knowledge_release)
    advice_request = getattr(context.recommendation, "advice_request", None)
    calculations = (
        list(
            Calculation.objects.filter(
                owner_id=context.recommendation.owner_id,
                advice_request=advice_request,
            ).order_by("created_at")
        )
        if advice_request is not None
        else []
    )
    return {
        "recommendation_id": str(context.recommendation.id),
        "outcome": context.recommendation.outcome,
        "catalogue_limit": f"{product_count} reviewed products",
        "customer_profile": profile or {},
        "ayush_scenario_conditions": _ayush_rule_inputs(
            [match.requirement for match in context.evaluations[0].matches]
        ) if context.evaluations else {},
        "claim_illustration": any(
            item.calculation_type == "higher_room_associated_expense_proration"
            for item in calculations
        ),
        "calculations": [
            {
                "calculation_id": str(item.id),
                "calculation_type": item.calculation_type,
                "inputs": item.inputs,
                "operations": item.operations,
                "result": item.result,
                "display_ratio_percent": (
                    _room_ratio_percent(item.inputs)
                    if item.calculation_type == "higher_room_associated_expense_proration"
                    else None
                ),
                "assumptions": item.assumptions,
                "status": item.status,
            }
            for item in calculations
        ],
        "candidates": [
            {
                "candidate_assessment_id": str(candidate_by_variant[result.variant.id].id),
                "product": result.variant.policy_version.product.name,
                "insurer": result.variant.policy_version.product.insurer.name,
                "uin": result.variant.policy_version.uin,
                "disposition": candidate_by_variant[result.variant.id].disposition,
                "rank": candidate_by_variant[result.variant.id].rank,
                "requirement_matches": [
                    {
                        "requirement_match_id": str(
                            match_by_pair[(result.variant.id, match.requirement.id)].id
                        ),
                        "criterion": match.requirement.criterion,
                        "priority": match.requirement.priority,
                        "outcome": match.outcome,
                        "comparison_value": match.comparison_value,
                        "rule_ids": list(match.rule_ids),
                    }
                    for match in result.matches
                ],
                "rules": [
                    {
                        "policy_rule_id": str(rule.rule.id),
                        "rule_key": rule.rule.rule_key,
                        "rule_type": rule.rule.rule_type,
                        "applies": rule.applies,
                        "body": rule.rule.body,
                        "evidence_complete": rule.evidence_complete,
                        "retrieved": str(rule.rule.id) in retrieved_rule_ids,
                        "evidence_span_ids": [str(span_id) for span_id in rule.evidence_span_ids],
                        "evidence": [
                            {
                                "evidence_span_id": str(span_id),
                                "allowed_citation_roles": _allowed_citation_roles(
                                    evidence_roles.get(
                                        (str(rule.rule.id), str(span_id)),
                                        set(),
                                    )
                                ),
                            }
                            for span_id in rule.evidence_span_ids
                        ],
                        "subject_applicability": [
                            {
                                "subject_person_id": (
                                    str(subject.subject_person_id)
                                    if subject.subject_person_id is not None
                                    else None
                                ),
                                "applies": subject.applies,
                            }
                            for subject in rule.subject_results
                        ],
                    }
                    for rule in result.rules
                ],
            }
            for result in context.evaluations
        ],
        "information_needs": [
            {
                "information_need_id": str(item.id),
                "information_key": item.information_key,
                "reason": item.reason,
                "priority": item.priority,
            }
            for item in context.needs
        ],
        "retrieval": {
            "policy_search_chunk_ids": (
                [str(item.id) for item in retrieval.chunks] if retrieval is not None else []
            ),
            "policy_rule_ids": sorted(retrieved_rule_ids),
            "evidence_span_ids": (
                sorted(
                    {
                        str(span_id)
                        for item in retrieval.chunks
                        for span_id in item.evidence_span_ids
                    }
                )
                if retrieval is not None
                else []
            ),
        },
    }


_NUMBER = re.compile(r"(?<![\w-])\d+(?:[.,]\d+)*(?![\w-])")


def _numbers_in(text: str) -> set[str]:
    """Extract numbers, normalizing away thousands-separator commas (e.g. "500,000" -> "500000")

    so a figure quoted with grouping in prose matches the same figure serialized plainly in
    supplied_context.
    """

    return {token.replace(",", "") for token in _NUMBER.findall(text)}


def _comparison_numbers_by_match(supplied_context: dict[str, Any]) -> dict[str, set[str]]:
    """Map each requirement_match_id to the numbers in its own comparison_value.

    Kept separate from the global supplied-numbers set so a statement can only quote a
    candidate's matched amount when it actually references that match — otherwise the
    model could cite candidate A's comparison_value while writing about candidate B and
    still pass a purely "does this number appear anywhere in context" check.
    """

    numbers_by_match: dict[str, set[str]] = {}
    for candidate in supplied_context.get("candidates", []) or []:
        for match in candidate.get("requirement_matches", []) or []:
            comparison_value = match.get("comparison_value")
            match_id = match.get("requirement_match_id")
            if comparison_value is None or match_id is None:
                continue
            numbers_by_match[match_id] = _numbers_in(json.dumps(comparison_value, default=str))
    return numbers_by_match

_RESTRICTION_TYPES = {
    "waiting_period",
    "limit",
    "deduction",
    "exclusion",
    "exception",
    "eligibility",
    "accumulation",
    "restoration",
    "precedence",
}
_POLICY_CLAIM_STATEMENT_TYPES = {
    "eligibility",
    "requirement_match",
    "benefit",
    "restriction",
    "price",
    "provider",
    "calculation",
}
_CITATION_EVIDENCE_ROLES = {
    "supports": {"supports", "defines", "precedence", "table_header", "table_cell", "footnote"},
    "restricts": {"restricts", "precedence", "table_header", "table_cell", "footnote"},
    "excepts": {"excepts", "table_header", "table_cell", "footnote"},
    "conflicts": {"contradicts"},
    "assumption_source": {"supports", "defines", "precedence", "footnote"},
}


def _allowed_citation_roles(evidence_roles: set[str]) -> list[str]:
    return sorted(
        citation_role
        for citation_role, compatible_roles in _CITATION_EVIDENCE_ROLES.items()
        if compatible_roles & evidence_roles
    )


_OPTIONAL_STATEMENT_IDS = (
    "candidate_assessment_id",
    "requirement_match_id",
    "information_need_id",
    "calculation_id",
)


def _blank_ids_to_none(draft: RecommendationDraftV1) -> RecommendationDraftV1:
    """Some providers fill an unused optional id with "" instead of null. A blank id names
    nothing, so treat it as absent; every non-blank id is still validated exactly."""
    statements = []
    for statement in draft.statements:
        updates: dict[str, Any] = {
            name: None
            for name in _OPTIONAL_STATEMENT_IDS
            if isinstance(getattr(statement, name), str) and not getattr(statement, name).strip()
        }
        citations = [
            citation.model_copy(update={"policy_rule_id": None})
            if isinstance(citation.policy_rule_id, str) and not citation.policy_rule_id.strip()
            else citation
            for citation in statement.citations
        ]
        if citations != statement.citations:
            updates["citations"] = citations
        statements.append(statement.model_copy(update=updates) if updates else statement)
    if statements == draft.statements:
        return draft
    return draft.model_copy(update={"statements": statements})


def _canonicalize_statement_references(
    draft: RecommendationDraftV1, context: RecommendationContext
) -> RecommendationDraftV1:
    """Treat blank optional ids as absent, then drop a statement's redundant
    candidate_assessment_id when it agrees with the candidate implied by its own
    requirement_match_id. Leaves genuine mismatches and any information_need_id combination
    untouched so validation still rejects them."""
    draft = _blank_ids_to_none(draft)
    match_candidate = {str(match.id): str(match.candidate_assessment_id) for match in context.matches}
    statements = []
    changed = False
    for statement in draft.statements:
        if (
            statement.candidate_assessment_id is not None
            and statement.requirement_match_id is not None
            and statement.information_need_id is None
            and match_candidate.get(statement.requirement_match_id) == statement.candidate_assessment_id
        ):
            statements.append(statement.model_copy(update={"candidate_assessment_id": None}))
            changed = True
        else:
            statements.append(statement)
    if not changed:
        return draft
    return draft.model_copy(update={"statements": statements})


def _distinct_citations_for_storage(citations: list[Any]) -> list[Any]:
    """One source passage and role has one citation row per statement."""

    seen: set[tuple[str, str]] = set()
    distinct = []
    for citation in citations:
        key = (citation.evidence_span_id, citation.role)
        if key not in seen:
            seen.add(key)
            distinct.append(citation)
    return distinct


def validate_recommendation_draft(
    draft: RecommendationDraftV1,
    context: RecommendationContext,
    supplied_context: dict[str, Any],
) -> None:
    if draft.outcome != context.recommendation.outcome:
        raise UnsupportedRecommendationError(
            "The model changed the deterministic recommendation outcome."
        )
    candidate_ids = {str(item.id) for item in context.candidates}
    match_ids = {str(item.id) for item in context.matches}
    need_ids = {str(item.id) for item in context.needs}
    calculation_ids = set(
        str(value)
        for value in Calculation.objects.filter(
            owner_id=context.recommendation.owner_id,
            advice_request=context.recommendation.advice_request,
        ).values_list("id", flat=True)
    )
    release_rule_ids = {
        str(result.rule.id) for evaluation in context.evaluations for result in evaluation.rules
    }
    rule_evidence: dict[tuple[str, str], set[str]] = {}
    for rule_id, span_id, role in PolicyRuleEvidence.objects.filter(
        policy_rule_id__in=release_rule_ids
    ).values_list("policy_rule_id", "evidence_span_id", "role"):
        rule_evidence.setdefault((str(rule_id), str(span_id)), set()).add(str(role))
    evidence_ids = {span_id for _, span_id in rule_evidence}
    rule_policy_versions = {
        str(result.rule.id): result.rule.policy_version_id
        for evaluation in context.evaluations
        for result in evaluation.rules
    }
    candidate_policy_versions = {
        str(candidate.id): candidate.product_variant.policy_version_id
        for candidate in context.candidates
    }
    match_policy_versions = {
        str(match.id): match.candidate_assessment.product_variant.policy_version_id
        for match in context.matches
    }
    comparison_numbers_by_match = _comparison_numbers_by_match(supplied_context)
    all_comparison_numbers: set[str] = set().union(*comparison_numbers_by_match.values()) if (
        comparison_numbers_by_match
    ) else set()
    supplied_numbers = _numbers_in(json.dumps(supplied_context, default=str)) - all_comparison_numbers
    cited_rule_ids: set[str] = set()
    for statement in draft.statements:
        references = [
            statement.candidate_assessment_id,
            statement.requirement_match_id,
            statement.information_need_id,
        ]
        if sum(item is not None for item in references) > 1:
            raise UnsupportedRecommendationError(
                "A statement may have at most one decision-object reference."
            )
        if statement.candidate_assessment_id not in candidate_ids | {None}:
            raise UnsupportedRecommendationError("A statement references an unavailable candidate.")
        if statement.requirement_match_id not in match_ids | {None}:
            raise UnsupportedRecommendationError(
                "A statement references an unavailable requirement match."
            )
        if statement.information_need_id not in need_ids | {None}:
            raise UnsupportedRecommendationError(
                "A statement references an unavailable information need."
            )
        if statement.calculation_id not in calculation_ids | {None}:
            raise UnsupportedRecommendationError(
                "A statement references an unavailable calculation."
            )
        allowed_numbers = supplied_numbers
        if statement.requirement_match_id is not None:
            allowed_numbers = supplied_numbers | comparison_numbers_by_match.get(
                statement.requirement_match_id, set()
            )
        unsupported_numbers = _numbers_in(statement.text) - allowed_numbers
        if unsupported_numbers:
            raise UnsupportedRecommendationError(
                "A recommendation statement contains an unsupported number."
            )
        if (
            statement.critical
            and statement.statement_type not in {"customer_context", "limitation", "next_step"}
            and not statement.citations
            and statement.calculation_id is None
        ):
            raise UnsupportedRecommendationError(
                "A critical insurance statement lacks evidence or a calculation."
            )
        if (
            statement.statement_type in _POLICY_CLAIM_STATEMENT_TYPES
            and not statement.citations
            and statement.calculation_id is None
        ):
            raise UnsupportedRecommendationError(
                "A policy claim lacks evidence or a deterministic calculation."
            )
        expected_policy_version = None
        if statement.candidate_assessment_id is not None:
            expected_policy_version = candidate_policy_versions[statement.candidate_assessment_id]
        elif statement.requirement_match_id is not None:
            expected_policy_version = match_policy_versions[statement.requirement_match_id]
        for citation in statement.citations:
            if citation.evidence_span_id not in evidence_ids:
                raise UnsupportedRecommendationError(
                    "A citation references evidence outside the pinned release."
                )
            if citation.policy_rule_id is None or citation.policy_rule_id not in release_rule_ids:
                raise UnsupportedRecommendationError(
                    "A policy citation must reference a rule in the pinned release."
                )
            pair = (citation.policy_rule_id, citation.evidence_span_id)
            if pair not in rule_evidence:
                raise UnsupportedRecommendationError(
                    "A citation is not evidence for its claimed policy rule."
                )
            if not (rule_evidence[pair] & _CITATION_EVIDENCE_ROLES.get(citation.role, set())):
                raise UnsupportedRecommendationError(
                    "A citation role does not match the rule-evidence relationship."
                )
            if (
                expected_policy_version is not None
                and rule_policy_versions[citation.policy_rule_id] != expected_policy_version
            ):
                raise UnsupportedRecommendationError(
                    "A statement cites evidence for a different product candidate."
                )
            cited_rule_ids.add(citation.policy_rule_id)
    if _numbers_in(draft.introduction) - supplied_numbers:
        raise UnsupportedRecommendationError(
            "The recommendation introduction contains an unsupported number."
        )
    if draft.follow_up and _numbers_in(draft.follow_up) - supplied_numbers:
        raise UnsupportedRecommendationError(
            "The recommendation follow-up contains an unsupported number."
        )
    if draft.outcome != "clarification_required":
        recommended_variant_ids = {
            item.product_variant_id
            for item in context.candidates
            if item.disposition == "recommended"
        }
        shortlisted_variant_ids = recommended_variant_ids
        if not shortlisted_variant_ids:
            non_excluded = [item for item in context.candidates if item.disposition != "excluded"]
            if non_excluded:
                ranks = [item.rank for item in non_excluded if item.rank is not None]
                if len(ranks) != len(non_excluded):
                    raise UnsupportedRecommendationError(
                        "A non-excluded candidate is missing its deterministic rank."
                    )
                best_rank = min(ranks)
                shortlisted_variant_ids = {
                    item.product_variant_id for item in non_excluded if item.rank == best_rank
                }
        required_restrictions = {
            str(result.rule.id)
            for evaluation in context.evaluations
            if evaluation.variant.id in shortlisted_variant_ids
            for result in evaluation.rules
            if result.applies == Truth.TRUE
            and result.rule.rule_type in _RESTRICTION_TYPES
            and result.evidence_complete
            and any(
                str(result.rule.id) in match.rule_ids
                for match in evaluation.matches
            )
        }
        if not required_restrictions.issubset(cited_rule_ids):
            raise UnsupportedRecommendationError(
                "The recommendation omitted an applicable decision-critical restriction."
            )


_SOFT_FACT_LIMITATION_TEXT: dict[str, str] = {
    "existing_cover": (
        "We have not confirmed whether you already hold health insurance, which affects "
        "portability and continuity of cover — let us know and we can refine this."
    ),
    "medical_history_disclosed": (
        "We have not confirmed your (or your family's) medical history or any pre-existing "
        "conditions, which can affect eligibility and pricing — let us know and we can refine "
        "this."
    ),
}


def _append_soft_fact_limitations(
    draft: RecommendationDraftV1, supplied_context: dict[str, Any]
) -> RecommendationDraftV1:
    """Deterministically flag existing-cover/medical-history as unconfirmed, if so.

    These facts are asked for but never block a recommendation (product decision:
    keep the intake to 5 hard-blocking questions), so the gap must be surfaced in
    the output itself instead.
    """

    profile_facts = (supplied_context.get("customer_profile") or {}).get("facts", [])
    extra_statements = [
        RecommendationStatementDraft(
            text=text,
            statement_type="limitation",
            critical=False,
            candidate_assessment_id=None,
            requirement_match_id=None,
            information_need_id=None,
            calculation_id=None,
            citations=[],
        )
        for fact_type, text in _SOFT_FACT_LIMITATION_TEXT.items()
        if not any(
            _fact_satisfies_slot(fact)
            for fact in profile_facts
            if fact.get("fact_type") == fact_type
        )
    ]
    if not extra_statements:
        return draft
    return draft.model_copy(update={"statements": [*draft.statements, *extra_statements]})


@transaction.atomic
def publish_draft(
    turn: Turn,
    context: RecommendationContext,
    draft: RecommendationDraftV1,
    supplied_context: dict[str, Any],
    *,
    expected_release_id: uuid.UUID,
    expected_channel_generation: int,
    expected_erasure_generation: int,
) -> Message:
    owner = User.objects.select_for_update().get(pk=turn.owner_id)
    if (
        owner.erasure_generation != expected_erasure_generation
        or owner.deleted_at is not None
        or not owner.is_active
    ):
        raise AccountErased("account_erased")
    channel = (
        KnowledgeChannel.objects.select_for_update(of=("self",))
        .select_related("current_release")
        .get(name="live")
    )
    conversation = Conversation.objects.select_for_update().get(
        pk=turn.conversation_id, owner_id=turn.owner_id
    )
    if (
        conversation.current_profile_revision_id != context.recommendation.profile_revision_id
        or channel.current_release_id != expected_release_id
        or channel.generation != expected_channel_generation
    ):
        raise PinnedStateChanged("pinned_state_changed")
    draft = _canonicalize_statement_references(draft, context)
    if context.recommendation.outcome != "clarification_required":
        draft = _append_soft_fact_limitations(draft, supplied_context)
    validate_recommendation_draft(draft, context, supplied_context)
    for ordinal, item in enumerate(draft.statements, 1):
        statement = RecommendationStatement.objects.create(
            owner_id=turn.owner_id,
            recommendation=context.recommendation,
            ordinal=ordinal,
            candidate_assessment_id=item.candidate_assessment_id,
            requirement_match_id=item.requirement_match_id,
            information_need_id=item.information_need_id,
            calculation_id=item.calculation_id,
            text=item.text,
            statement_type=item.statement_type,
            critical=item.critical,
            support_status=(
                "customer_profile_supported"
                if item.statement_type == "customer_context"
                else "supported"
                if item.citations or item.calculation_id
                else "partly_supported"
            ),
        )
        for citation_ordinal, citation in enumerate(_distinct_citations_for_storage(item.citations), 1):
            RecommendationCitation.objects.create(
                owner_id=turn.owner_id,
                recommendation_statement=statement,
                evidence_span_id=citation.evidence_span_id,
                policy_rule_id=citation.policy_rule_id,
                role=citation.role,
                ordinal=citation_ordinal,
            )
    content_parts = [draft.introduction, *(item.text for item in draft.statements)]
    if draft.follow_up:
        content_parts.append(draft.follow_up)
    content = "\n\n".join(content_parts)
    sequence = (
        Message.objects.filter(conversation=conversation).aggregate(value=Max("sequence"))["value"]
        or 0
    ) + 1
    message = Message.objects.create(
        owner_id=turn.owner_id,
        conversation=conversation,
        sequence=sequence,
        role="adviser",
        content=content,
        origin="system",
        payload_commitment=commitment(
            {"recommendation_id": str(context.recommendation.id), "content": content}
        ),
        submitted_at=timezone.now(),
        recommendation=context.recommendation,
    )
    asked_need_ids = {item.information_need_id for item in draft.statements if item.information_need_id}
    if asked_need_ids:
        InformationNeed.objects.filter(owner_id=turn.owner_id, id__in=asked_need_ids).update(
            status="asked", asked_in_message=message
        )
    return message


def clarification_draft(question: str, context: RecommendationContext) -> RecommendationDraftV1:
    need = context.needs[0]
    return RecommendationDraftV1(
        schema_version=1,
        outcome="clarification_required",
        introduction="I need one detail before I can compare the reviewed policies safely.",
        statements=[
            RecommendationStatementDraft(
                text=question,
                statement_type="next_step",
                critical=False,
                candidate_assessment_id=None,
                requirement_match_id=None,
                information_need_id=str(need.id),
                calculation_id=None,
                citations=[],
            )
        ],
        follow_up=None,
    )
