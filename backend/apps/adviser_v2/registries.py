"""Closed registries for customer assertions and executable policy rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AssertionType:
    key: str
    kinds: frozenset[str]
    person_scoped: bool = False


FACT_TYPES: dict[str, AssertionType] = {
    item.key: item
    for item in (
        AssertionType("date_of_birth", frozenset({"date", "unknown"}), True),
        AssertionType("age", frozenset({"quantity", "unknown"}), True),
        AssertionType("relationship", frozenset({"code", "text", "unknown"}), True),
        AssertionType("intended_insured", frozenset({"boolean", "unknown"}), True),
        AssertionType("medical_history_disclosed", frozenset({"boolean", "unknown"}), True),
        AssertionType("medical_condition", frozenset({"code", "text", "unknown"}), True),
        AssertionType("diagnosis_date", frozenset({"date", "unknown"}), True),
        AssertionType("treatment_status", frozenset({"code", "text", "unknown"}), True),
        AssertionType("city", frozenset({"text", "code", "unknown"})),
        AssertionType("postal_code", frozenset({"text", "code", "unknown"})),
        AssertionType("existing_cover", frozenset({"quantity", "boolean", "unknown"})),
        AssertionType("continuity_start", frozenset({"date", "unknown"})),
        AssertionType("policy_start", frozenset({"date", "unknown"})),
        AssertionType("budget", frozenset({"quantity", "unknown"})),
        AssertionType("sum_insured", frozenset({"quantity", "unknown"})),
        AssertionType("eligible_room_rent_limit", frozenset({"quantity", "unknown"})),
        AssertionType("room_rent_actually_incurred", frozenset({"quantity", "unknown"})),
        AssertionType("total_associated_medical_expenses", frozenset({"quantity", "unknown"})),
        AssertionType(
            "actual_room_category_higher_than_eligible", frozenset({"boolean", "unknown"})
        ),
        AssertionType("policy_tenure_selection", frozenset({"quantity", "unknown"})),
        AssertionType("family_composition", frozenset({"text", "code", "unknown"})),
        AssertionType("purchase_for", frozenset({"reference", "code", "text", "unknown"})),
        AssertionType("quote_reference", frozenset({"text", "unknown"})),
    )
}


REQUIREMENT_TYPES: dict[str, AssertionType] = {
    item.key: item
    for item in (
        AssertionType("budget", frozenset({"quantity", "unknown"})),
        AssertionType("sum_insured", frozenset({"quantity", "unknown"})),
        AssertionType("room_category", frozenset({"code", "text", "unknown"})),
        AssertionType("policy_tenure_selection", frozenset({"quantity", "unknown"})),
        AssertionType("no_copay", frozenset({"boolean", "unknown"})),
        AssertionType("copay", frozenset({"quantity", "boolean", "unknown"})),
        AssertionType("deductible", frozenset({"quantity", "boolean", "unknown"})),
        AssertionType("pre_existing_disease_wait", frozenset({"duration", "unknown"})),
        AssertionType("maternity", frozenset({"boolean", "unknown"})),
        AssertionType("newborn", frozenset({"boolean", "unknown"})),
        AssertionType("restoration", frozenset({"boolean", "quantity", "unknown"})),
        AssertionType("provider_hospital", frozenset({"text", "reference", "unknown"})),
        AssertionType("geography", frozenset({"code", "text", "unknown"})),
        AssertionType("portability", frozenset({"boolean", "unknown"})),
        AssertionType("specific_treatment", frozenset({"code", "text", "unknown"}), True),
        AssertionType("family_floater", frozenset({"boolean", "unknown"})),
        AssertionType("minimize_waiting_period", frozenset({"boolean", "unknown"})),
        AssertionType("maximize_cover", frozenset({"boolean", "quantity", "unknown"})),
    )
}


RULE_TYPES = frozenset(
    {
        "definition",
        "eligibility",
        "coverage",
        "exclusion",
        "exception",
        "waiting_period",
        "limit",
        "deduction",
        "accumulation",
        "restoration",
        "calculation",
        "precedence",
        "operational_right",
    }
)


def validate_fact_type(fact_type: str, value: object) -> None:
    assertion = FACT_TYPES.get(fact_type)
    if assertion is None:
        raise ValueError(f"Unregistered customer fact type: {fact_type}")
    _validate_value_kind(assertion, value)


def validate_requirement_type(criterion: str, value: object | None) -> None:
    assertion = REQUIREMENT_TYPES.get(criterion)
    if assertion is None:
        raise ValueError(f"Unregistered customer requirement type: {criterion}")
    if value is not None:
        _validate_value_kind(assertion, value)


def _validate_value_kind(assertion: AssertionType, value: object) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"{assertion.key} must use the approved FactValueV1 envelope.")
    state = value.get("state")
    kind = "unknown" if state in {"unknown", "not_applicable"} else value.get("kind")
    if kind not in assertion.kinds:
        allowed = ", ".join(sorted(assertion.kinds))
        raise ValueError(f"{assertion.key} requires one of these value kinds: {allowed}.")
