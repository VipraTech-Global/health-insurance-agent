"""Deterministically validate and atomically publish v2 comparisons."""

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
from ..errors import AccountErased, PinnedStateChanged, UnsupportedComparisonError
from ..models import (
    AdviceRequest,
    Calculation,
    Comparison,
    ComparisonCitation,
    ComparisonStatement,
    Conversation,
    CustomerFact,
    CustomerProfileRevision,
    CustomerRequirement,
    InformationNeed,
    KnowledgeChannel,
    KnowledgeRelease,
    Message,
    PolicyComparisonAssessment,
    PolicyRequirementMatch,
    PolicyRuleEvidence,
    Turn,
)
from ..release_scope import comparison_product_count
from ..retrieval import PolicyRetrievalContext
from ..rule_engine import (
    PolicyComparisonResult,
    Truth,
    _ayush_rule_inputs,
    _room_illustration_inputs,
    current_inputs,
    evaluate_expression,
    evaluate_release,
)
from ..schemas import ComparisonDraftV1


@dataclass(frozen=True)
class ComparisonContext:
    comparison: Comparison
    assessments: tuple[PolicyComparisonAssessment, ...]
    matches: tuple[PolicyRequirementMatch, ...]
    needs: tuple[InformationNeed, ...]
    evaluations: tuple[PolicyComparisonResult, ...]


def _room_ratio_percent(inputs: list[dict[str, Any]]) -> str:
    ratio = Decimal(inputs[0]["value"]["value"]) / Decimal(inputs[1]["value"]["value"]) * 100
    return format(ratio.normalize(), "f")


def _save_room_illustration(
    advice_request: AdviceRequest,
    facts: list[CustomerFact],
    evaluations: list[PolicyComparisonResult],
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
        "state": "known",
        "kind": "boolean",
        "value": True,
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
                "state": "finite",
                "value": result_value,
                "unit": "money",
                "currency": "INR",
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
                            "state": "finite",
                            "value": input_values[key],
                            "unit": "money",
                            "currency": "INR",
                        },
                        "assertion_ids": [str(by_type[key].id)],
                        "span_ids": [],
                        "provenance": "customer",
                    }
                    for key in keys
                ],
                operations=[
                    {
                        "ordinal": 1,
                        "step_key": "eligible_rent_divided_by_actual_rent_times_associated_expenses",
                        "expression": effect["amount"],
                        "input_keys": list(keys),
                        "result": output,
                        "policy_rule_ids": [str(rule.rule.id)],
                        "evidence_span_ids": evidence_ids,
                        "rounding": "none",
                    }
                ],
                result=output,
                assumptions=[
                    {
                        "statement": "This is a stipulated higher-room claim illustration; actual claim admissibility is unresolved.",
                        "status": "stipulated",
                        "span_ids": [],
                        "effect_if_false": "If the selected room is not above the eligible category, this proportional rule does not apply.",
                    }
                ],
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
            comparison__turn__conversation_id=conversation_id,
            status__in=("asked", "resolved", "waived", "unavailable"),
        ).values_list("information_key", flat=True)
    )


@transaction.atomic
def prepare_comparison(
    turn: Turn,
    advice_request: AdviceRequest,
    profile_revision: CustomerProfileRevision,
    release: KnowledgeRelease,
    *,
    clarification_question: str | None = None,
    information_key: str = "customer_clarification",
) -> ComparisonContext:
    facts, requirements = _current_assertions(
        turn.owner_id, turn.conversation_id, profile_revision.revision
    )
    evaluations = evaluate_release(release, facts, requirements)
    illustration = (
        None
        if clarification_question
        else _save_room_illustration(advice_request, facts, evaluations)
    )
    incomplete_products = sum(
        1
        for evaluation in evaluations
        if any(match.outcome in {"unknown", "partly_meets"} for match in evaluation.matches)
        or any(not rule.evidence_complete for rule in evaluation.rules)
    )
    if clarification_question:
        outcome = "clarification_required"
    elif illustration is not None:
        outcome = "conditional"
    elif not evaluations or incomplete_products == len(evaluations):
        outcome = "insufficient_evidence"
    elif incomplete_products:
        outcome = "conditional"
    else:
        outcome = "completed"
    comparison = Comparison.objects.create(
        owner_id=turn.owner_id,
        turn=turn,
        advice_request=advice_request,
        profile_revision=profile_revision,
        knowledge_release=release,
        outcome=outcome,
    )
    assessments: list[PolicyComparisonAssessment] = []
    matches: list[PolicyRequirementMatch] = []
    for result in evaluations:
        assessment = PolicyComparisonAssessment.objects.create(
            owner_id=turn.owner_id,
            comparison=comparison,
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
        )
        assessments.append(assessment)
        for result_match in result.matches:
            match = PolicyRequirementMatch.objects.create(
                owner_id=turn.owner_id,
                comparison_assessment=assessment,
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
                comparison=comparison,
                need_kind="fact",
                information_key=information_key,
                reason=clarification_question,
                priority="required",
                status="open",
            )
        )
    return ComparisonContext(
        comparison,
        tuple(assessments),
        tuple(matches),
        tuple(needs),
        tuple(evaluations),
    )


def model_context(
    context: ComparisonContext,
    retrieval: PolicyRetrievalContext | None = None,
    *,
    profile: dict[str, Any] | None = None,
) -> dict[str, Any]:
    assessment_by_variant = {item.product_variant_id: item for item in context.assessments}
    match_by_pair = {
        (item.comparison_assessment.product_variant_id, item.customer_requirement_id): item
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
    product_count = comparison_product_count(context.comparison.knowledge_release)
    advice_request = getattr(context.comparison, "advice_request", None)
    calculations = (
        list(
            Calculation.objects.filter(
                owner_id=context.comparison.owner_id,
                advice_request=advice_request,
            ).order_by("created_at")
        )
        if advice_request is not None
        else []
    )
    return {
        "comparison_id": str(context.comparison.id),
        "catalogue_limit": f"{product_count} reviewed products",
        "customer_profile": profile or {},
        "ayush_scenario_conditions": _ayush_rule_inputs(
            [match.requirement for match in context.evaluations[0].matches]
        )
        if context.evaluations
        else {},
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
        "products": [
            {
                "comparison_assessment_id": str(assessment_by_variant[result.variant.id].id),
                "product_variant_id": str(result.variant.id),
                "product": result.variant.policy_version.product.name,
                "insurer": result.variant.policy_version.product.insurer.name,
                "uin": result.variant.policy_version.uin,
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
    assessment's matched amount when it actually references that match — otherwise the
    model could cite assessment A's comparison_value while writing about assessment B and
    still pass a purely "does this number appear anywhere in context" check.
    """

    numbers_by_match: dict[str, set[str]] = {}
    for product in supplied_context.get("products", []) or []:
        for match in product.get("requirement_matches", []) or []:
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
_ENDORSEMENT_LANGUAGE = re.compile(
    r"\b(?:best|better|winner|recommended|recommend|choose|chosen|top\s+pick|"
    r"shortlist(?:ed)?|rank(?:ed|ing)?|buy|purchase|select|go\s+with|opt\s+for)\b",
    re.IGNORECASE,
)


def _allowed_citation_roles(evidence_roles: set[str]) -> list[str]:
    return sorted(
        citation_role
        for citation_role, compatible_roles in _CITATION_EVIDENCE_ROLES.items()
        if compatible_roles & evidence_roles
    )


_OPTIONAL_STATEMENT_IDS = (
    "comparison_assessment_id",
    "requirement_match_id",
    "calculation_id",
)


def _blank_ids_to_none(draft: ComparisonDraftV1) -> ComparisonDraftV1:
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
    draft: ComparisonDraftV1, context: ComparisonContext
) -> ComparisonDraftV1:
    """Treat blank optional ids as absent, then drop a statement's redundant
    comparison_assessment_id when it agrees with the product implied by its own
    requirement_match_id. Genuine mismatches remain for validation to reject."""
    draft = _blank_ids_to_none(draft)
    match_assessment = {
        str(match.id): str(match.comparison_assessment_id) for match in context.matches
    }
    statements = []
    changed = False
    for statement in draft.statements:
        if (
            statement.comparison_assessment_id is not None
            and statement.requirement_match_id is not None
            and match_assessment.get(statement.requirement_match_id)
            == statement.comparison_assessment_id
        ):
            statements.append(statement.model_copy(update={"comparison_assessment_id": None}))
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


def validate_comparison_draft(
    draft: ComparisonDraftV1,
    context: ComparisonContext,
    supplied_context: dict[str, Any],
) -> None:
    assessment_ids = {str(item.id) for item in context.assessments}
    match_ids = {str(item.id) for item in context.matches}
    calculation_ids = set(
        str(value)
        for value in Calculation.objects.filter(
            owner_id=context.comparison.owner_id,
            advice_request=context.comparison.advice_request,
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
    assessment_policy_versions = {
        str(assessment.id): assessment.product_variant.policy_version_id
        for assessment in context.assessments
    }
    match_policy_versions = {
        str(match.id): match.comparison_assessment.product_variant.policy_version_id
        for match in context.matches
    }
    comparison_numbers_by_match = _comparison_numbers_by_match(supplied_context)
    all_comparison_numbers: set[str] = (
        set().union(*comparison_numbers_by_match.values())
        if (comparison_numbers_by_match)
        else set()
    )
    supplied_numbers = (
        _numbers_in(json.dumps(supplied_context, default=str)) - all_comparison_numbers
    )
    cited_rule_ids: set[str] = set()
    for statement in draft.statements:
        if _ENDORSEMENT_LANGUAGE.search(statement.text):
            raise UnsupportedComparisonError(
                "Generated comparison prose contains ranking, endorsement, or purchase direction."
            )
        references = [
            statement.comparison_assessment_id,
            statement.requirement_match_id,
        ]
        if sum(item is not None for item in references) != 1:
            raise UnsupportedComparisonError(
                "Every generated statement must identify exactly one compared product or criterion."
            )
        if statement.comparison_assessment_id not in assessment_ids | {None}:
            raise UnsupportedComparisonError("A statement references an unavailable assessment.")
        if statement.requirement_match_id not in match_ids | {None}:
            raise UnsupportedComparisonError(
                "A statement references an unavailable requirement match."
            )
        if statement.calculation_id not in calculation_ids | {None}:
            raise UnsupportedComparisonError("A statement references an unavailable calculation.")
        allowed_numbers = supplied_numbers
        if statement.requirement_match_id is not None:
            allowed_numbers = supplied_numbers | comparison_numbers_by_match.get(
                statement.requirement_match_id, set()
            )
        unsupported_numbers = _numbers_in(statement.text) - allowed_numbers
        if unsupported_numbers:
            raise UnsupportedComparisonError(
                "A comparison statement contains an unsupported number."
            )
        if not statement.citations:
            raise UnsupportedComparisonError(
                "Every generated comparison statement requires policy evidence."
            )
        expected_policy_version = None
        if statement.comparison_assessment_id is not None:
            expected_policy_version = assessment_policy_versions[statement.comparison_assessment_id]
        elif statement.requirement_match_id is not None:
            expected_policy_version = match_policy_versions[statement.requirement_match_id]
        for citation in statement.citations:
            if citation.evidence_span_id not in evidence_ids:
                raise UnsupportedComparisonError(
                    "A citation references evidence outside the pinned release."
                )
            if citation.policy_rule_id is None or citation.policy_rule_id not in release_rule_ids:
                raise UnsupportedComparisonError(
                    "A policy citation must reference a rule in the pinned release."
                )
            pair = (citation.policy_rule_id, citation.evidence_span_id)
            if pair not in rule_evidence:
                raise UnsupportedComparisonError(
                    "A citation is not evidence for its claimed policy rule."
                )
            if not (rule_evidence[pair] & _CITATION_EVIDENCE_ROLES.get(citation.role, set())):
                raise UnsupportedComparisonError(
                    "A citation role does not match the rule-evidence relationship."
                )
            if (
                expected_policy_version is not None
                and rule_policy_versions[citation.policy_rule_id] != expected_policy_version
            ):
                raise UnsupportedComparisonError(
                    "A statement cites evidence for a different product assessment."
                )
            cited_rule_ids.add(citation.policy_rule_id)
    if context.comparison.outcome != "clarification_required":
        required_restrictions = {
            str(result.rule.id)
            for evaluation in context.evaluations
            for result in evaluation.rules
            if result.applies == Truth.TRUE
            and result.rule.rule_type in _RESTRICTION_TYPES
            and result.evidence_complete
            and any(str(result.rule.id) in match.rule_ids for match in evaluation.matches)
        }
        if not required_restrictions.issubset(cited_rule_ids):
            raise UnsupportedComparisonError(
                "The comparison omitted an applicable decision-critical restriction."
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

COMPARISON_FRAMING = (
    "CoverGuide compares the reviewed products against the criteria you shared. "
    "It does not choose a policy; the decision is yours."
)
COMPARISON_CLOSING_NOTICE = (
    "This comparison is limited to the reviewed policy versions and cited evidence. "
    "Eligibility, underwriting, premium, and claim decisions remain subject to the insurer."
)
_OUTCOME_TEXT = {
    "completed": "The reviewed evidence supports a completed criterion-by-criterion comparison.",
    "conditional": "The comparison is conditional because some material conditions remain.",
    "clarification_required": "One missing detail is needed before the policy comparison can continue.",
    "insufficient_evidence": "The available reviewed evidence is insufficient for a complete comparison.",
}


def _soft_fact_limitations(supplied_context: dict[str, Any]) -> list[str]:
    """Return deterministic customer-data gaps without model-authored prose."""
    profile_facts = (supplied_context.get("customer_profile") or {}).get("facts", [])
    return [
        text
        for fact_type, text in _SOFT_FACT_LIMITATION_TEXT.items()
        if not any(
            _fact_satisfies_slot(fact)
            for fact in profile_facts
            if fact.get("fact_type") == fact_type
        )
    ]


@transaction.atomic
def publish_draft(
    turn: Turn,
    context: ComparisonContext,
    draft: ComparisonDraftV1,
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
        conversation.current_profile_revision_id != context.comparison.profile_revision_id
        or channel.current_release_id != expected_release_id
        or channel.generation != expected_channel_generation
    ):
        raise PinnedStateChanged("pinned_state_changed")
    draft = _canonicalize_statement_references(draft, context)
    validate_comparison_draft(draft, context, supplied_context)
    for ordinal, item in enumerate(draft.statements, 1):
        statement = ComparisonStatement.objects.create(
            owner_id=turn.owner_id,
            comparison=context.comparison,
            ordinal=ordinal,
            comparison_assessment_id=item.comparison_assessment_id,
            requirement_match_id=item.requirement_match_id,
            information_need_id=None,
            calculation_id=item.calculation_id,
            text=item.text,
            statement_type=item.statement_type,
            critical=True,
            support_status="supported",
        )
        for citation_ordinal, citation in enumerate(
            _distinct_citations_for_storage(item.citations), 1
        ):
            ComparisonCitation.objects.create(
                owner_id=turn.owner_id,
                comparison_statement=statement,
                evidence_span_id=citation.evidence_span_id,
                policy_rule_id=citation.policy_rule_id,
                role=citation.role,
                ordinal=citation_ordinal,
            )
    content_parts = [COMPARISON_FRAMING, _OUTCOME_TEXT[context.comparison.outcome]]
    content_parts.extend(item.text for item in draft.statements)
    if context.comparison.outcome == "clarification_required" and context.needs:
        content_parts.append(context.needs[0].reason)
    elif context.comparison.outcome != "clarification_required":
        content_parts.extend(_soft_fact_limitations(supplied_context))
    content_parts.append(COMPARISON_CLOSING_NOTICE)
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
            {"comparison_id": str(context.comparison.id), "content": content}
        ),
        submitted_at=timezone.now(),
        comparison=context.comparison,
    )
    asked_need_ids = {item.id for item in context.needs}
    if asked_need_ids:
        InformationNeed.objects.filter(owner_id=turn.owner_id, id__in=asked_need_ids).update(
            status="asked", asked_in_message=message
        )
    return message


def clarification_draft(_question: str, _context: ComparisonContext) -> ComparisonDraftV1:
    return ComparisonDraftV1(schema_version=1, statements=[])
