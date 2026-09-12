from collections.abc import Container
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum
from typing import Any


class Truth(StrEnum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


class CandidateOutcome(StrEnum):
    DOCUMENTED_FIT = "documented_fit"
    CONDITIONAL = "conditional_option"
    NEEDS_EVIDENCE = "needs_evidence"
    EXCLUDED = "excluded"


@dataclass(frozen=True)
class Candidate:
    id: str
    insurer: str
    identity: str
    available: Truth
    requirements: dict[str, Truth]
    rating: Decimal | None
    premium: Decimal | None
    underwriting_relevant: bool = False


@dataclass(frozen=True)
class CandidateResult:
    candidate: Candidate
    outcome: CandidateOutcome
    reasons: tuple[str, ...]


def evaluate_rule(rule: dict[str, Any], profile: dict[str, Any]) -> Truth:
    operator = rule.get("op")
    if operator == "all":
        values = [evaluate_rule(child, profile) for child in rule.get("rules", [])]
        if any(value is Truth.FALSE for value in values):
            return Truth.FALSE
        if any(value is Truth.UNKNOWN for value in values):
            return Truth.UNKNOWN
        return Truth.TRUE
    if operator == "any":
        values = [evaluate_rule(child, profile) for child in rule.get("rules", [])]
        if any(value is Truth.TRUE for value in values):
            return Truth.TRUE
        if any(value is Truth.UNKNOWN for value in values):
            return Truth.UNKNOWN
        return Truth.FALSE
    field = rule.get("field")
    if not isinstance(field, str) or field not in profile:
        return Truth.UNKNOWN
    actual = profile[field]
    expected = rule.get("value")
    try:
        if operator == "eq":
            result = actual == expected
        elif operator == "in":
            if not isinstance(expected, Container):
                return Truth.UNKNOWN
            result = actual in expected
        elif operator == "gte":
            result = Decimal(str(actual)) >= Decimal(str(expected))
        elif operator == "lte":
            result = Decimal(str(actual)) <= Decimal(str(expected))
        else:
            return Truth.UNKNOWN
    except (TypeError, ValueError, ArithmeticError):
        return Truth.UNKNOWN
    return Truth.TRUE if result else Truth.FALSE


def evaluate_candidate(
    candidate: Candidate,
    mandatory_requirements: tuple[str, ...],
    hard_budget: Decimal | None,
) -> CandidateResult:
    if candidate.available is Truth.FALSE:
        return CandidateResult(
            candidate, CandidateOutcome.EXCLUDED, ("Unavailable for the requested purchase.",)
        )
    if candidate.available is Truth.UNKNOWN:
        return CandidateResult(
            candidate, CandidateOutcome.NEEDS_EVIDENCE, ("Current availability is unverified.",)
        )
    reasons: list[str] = []
    for requirement in mandatory_requirements:
        result = candidate.requirements.get(requirement, Truth.UNKNOWN)
        if result is Truth.FALSE:
            return CandidateResult(
                candidate,
                CandidateOutcome.EXCLUDED,
                (f"Mandatory requirement is not met: {requirement}.",),
            )
        if result is Truth.UNKNOWN:
            reasons.append(f"Missing evidence for mandatory requirement: {requirement}.")
    if hard_budget is not None:
        if candidate.premium is None:
            reasons.append("Comparable premium is unknown for the hard budget.")
        elif candidate.premium > hard_budget:
            return CandidateResult(
                candidate,
                CandidateOutcome.EXCLUDED,
                ("Comparable observed premium exceeds the hard budget.",),
            )
    if reasons:
        return CandidateResult(candidate, CandidateOutcome.NEEDS_EVIDENCE, tuple(reasons))
    if candidate.underwriting_relevant:
        return CandidateResult(
            candidate,
            CandidateOutcome.CONDITIONAL,
            ("Documentary fit is supported; underwriting or a quote remains external.",),
        )
    return CandidateResult(
        candidate,
        CandidateOutcome.DOCUMENTED_FIT,
        ("Verified evidence supports every mandatory requirement.",),
    )


def rank_candidates(results: list[CandidateResult]) -> list[list[CandidateResult]]:
    eligible = [
        result
        for result in results
        if result.outcome in {CandidateOutcome.DOCUMENTED_FIT, CandidateOutcome.CONDITIONAL}
    ]
    rated: dict[Decimal, list[CandidateResult]] = {}
    unrated: list[CandidateResult] = []
    for result in eligible:
        rating = result.candidate.rating
        if rating is None:
            unrated.append(result)
        else:
            rated.setdefault(rating, []).append(result)
    groups: list[list[CandidateResult]] = []
    for rating in sorted(rated, reverse=True):
        group = rated[rating]
        if all(item.candidate.premium is not None for item in group):
            group.sort(
                key=lambda item: (
                    item.candidate.premium,
                    item.candidate.insurer,
                    item.candidate.identity,
                )
            )
            groups.extend([[item] for item in group])
        else:
            group.sort(key=lambda item: (item.candidate.insurer, item.candidate.identity))
            groups.append(group)
    if unrated:
        unrated.sort(key=lambda item: (item.candidate.insurer, item.candidate.identity))
        groups.append(unrated)
    return groups
