from decimal import Decimal

from apps.adviser.recommendations import (
    Candidate,
    CandidateOutcome,
    Truth,
    evaluate_candidate,
    evaluate_rule,
    rank_candidates,
)


def candidate(**changes: object) -> Candidate:
    values = {
        "id": "one",
        "insurer": "Alpha",
        "identity": "Plan A",
        "available": Truth.TRUE,
        "requirements": {"no_copay": Truth.TRUE},
        "rating": Decimal("4.5"),
        "premium": Decimal("20000"),
    }
    values.update(changes)
    return Candidate(**values)


def test_unknown_applicability_stays_unknown() -> None:
    assert evaluate_rule({"op": "gte", "field": "age", "value": 18}, {}) is Truth.UNKNOWN
    assert (
        evaluate_rule(
            {
                "op": "all",
                "rules": [
                    {"op": "eq", "field": "city", "value": "Pune"},
                    {"op": "gte", "field": "age", "value": 18},
                ],
            },
            {"city": "Pune"},
        )
        is Truth.UNKNOWN
    )


def test_highly_rated_unsuitable_candidate_is_excluded() -> None:
    result = evaluate_candidate(
        candidate(
            rating=Decimal("5"),
            requirements={"no_copay": Truth.FALSE},
        ),
        ("no_copay",),
        None,
    )
    assert result.outcome is CandidateOutcome.EXCLUDED


def test_missing_price_does_not_pass_hard_budget() -> None:
    result = evaluate_candidate(
        candidate(premium=None),
        ("no_copay",),
        Decimal("25000"),
    )
    assert result.outcome is CandidateOutcome.NEEDS_EVIDENCE


def test_tied_rating_stays_tied_when_any_price_is_missing() -> None:
    first = evaluate_candidate(candidate(id="a"), ("no_copay",), None)
    second = evaluate_candidate(
        candidate(id="b", insurer="Beta", premium=None),
        ("no_copay",),
        None,
    )
    groups = rank_candidates([second, first])
    assert len(groups) == 1
    assert [result.candidate.id for result in groups[0]] == ["a", "b"]


def test_comparable_price_breaks_rating_tie() -> None:
    expensive = evaluate_candidate(
        candidate(id="expensive", premium=Decimal("25000")),
        ("no_copay",),
        None,
    )
    affordable = evaluate_candidate(
        candidate(id="affordable", insurer="Beta", premium=Decimal("19000")),
        ("no_copay",),
        None,
    )
    groups = rank_candidates([expensive, affordable])
    assert [group[0].candidate.id for group in groups] == [
        "affordable",
        "expensive",
    ]
