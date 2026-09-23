from __future__ import annotations

import datetime as dt
import uuid
from decimal import Decimal
from types import SimpleNamespace
from typing import Any, cast

import pytest

from apps.adviser_v2.contracts import RuleV1, TableSelectorsV1
from apps.adviser_v2.models import (
    CustomerRequirement,
    EvidenceSpan,
    KnowledgeRelease,
    KnowledgeReleaseRule,
    PolicyRule,
    PolicyRuleEvidence,
    PolicyRuleTableCell,
    PolicyVersion,
    PolicyVersionDocument,
    Product,
    ProductVariant,
)
from apps.adviser_v2.processing.stages import _table_rule_problems
from apps.adviser_v2.rule_engine import (
    Scalar,
    Truth,
    _age_rule_inputs,
    _aggregate_comparison_value,
    _apply_parent_child_inputs,
    _ayush_rule_inputs,
    _child_entry_unverified,
    _childbirth_exclusion_match,
    _childbirth_rule_inputs,
    _compare_requirement,
    _deductible_configuration_inputs,
    _deductible_selection_match,
    _no_separate_room_icu_match,
    _room_illustration_inputs,
    _selected_policy_tenure,
    current_inputs,
    evaluate_expression,
    evaluate_predicate,
    evaluate_release,
    table_selectors_overlap,
)
from apps.adviser_v2.schemas import ExtractedPolicyRule
from apps.adviser_v2.tests.test_pipeline import public_html_capture


def _quantity(
    value: str,
    unit: str,
    *,
    currency: str | None = None,
) -> dict[str, object]:
    result: dict[str, object] = {"state": "finite", "value": value, "unit": unit}
    if currency is not None:
        result["currency"] = currency
    return result


def _literal(value: dict[str, object]) -> dict[str, object]:
    return {"node": "literal", "value": value}


def _table_rule(*axes: str) -> PolicyRule:
    return cast(
        PolicyRule,
        SimpleNamespace(
            body={
                "table": {
                    "table_key": "benefit-limit",
                    "axes": [{"key": axis} for axis in axes],
                }
            }
        ),
    )


def test_quantity_arithmetic_preserves_exact_units_and_currency() -> None:
    money = _literal(_quantity("100000", "money", currency="INR"))
    ratio = _literal(_quantity("0.02", "ratio"))

    assert evaluate_expression(
        {"node": "operation", "operator": "multiply", "arguments": [money, ratio]},
        {},
    ) == Scalar(Decimal("2000.00"), "money", "INR")
    assert evaluate_expression(
        {"node": "operation", "operator": "multiply", "arguments": [ratio, money]},
        {},
    ) == Scalar(Decimal("2000.00"), "money", "INR")
    assert evaluate_expression(
        {"node": "operation", "operator": "divide", "arguments": [money, money]},
        {},
    ) == Scalar(Decimal("1"), "ratio")
    assert (
        evaluate_expression(
            {"node": "operation", "operator": "multiply", "arguments": [money, money]},
            {},
        )
        is None
    )
    assert evaluate_expression(
        {"node": "input", "key": "customer_budget"},
        {
            "customer_budget": {
                "state": "known",
                "kind": "quantity",
                "value": "25000",
                "unit": "money",
                "currency": "INR",
            }
        },
    ) == Scalar(Decimal("25000"), "money", "INR")


def test_explicit_day_age_reaches_minimum_entry_age_rule() -> None:
    inputs = _age_rule_inputs(
        {"age": {"state": "known", "kind": "quantity", "value": "60", "unit": "day"}}
    )
    assert (
        evaluate_predicate(
            {
                "node": "compare",
                "left": {"node": "input", "key": "proposed_insured_age_days"},
                "operator": "lt",
                "right": _literal(_quantity("91", "day")),
            },
            inputs,
        )
        == Truth.TRUE
    )


def test_child_entry_needs_affirmative_verified_rule() -> None:
    child_id = uuid.uuid4()
    inputs = {
        child_id: {"age": {"state": "known", "kind": "quantity", "value": "60", "unit": "day"}}
    }
    assert _child_entry_unverified((child_id,), inputs, ())
    rule = SimpleNamespace(
        body={
            "effects": [
                {
                    "kind": "eligibility",
                    "target_key": "young_dependent_child_entry",
                    "decision": "eligible",
                }
            ]
        }
    )
    result = SimpleNamespace(
        rule=rule,
        evidence_complete=True,
        subject_results=(SimpleNamespace(subject_person_id=child_id, applies=Truth.TRUE),),
    )
    assert not _child_entry_unverified((child_id,), inputs, (result,))
    result.evidence_complete = False
    assert _child_entry_unverified((child_id,), inputs, (result,))


def test_parent_child_input_requires_both_recorded_people_to_be_insured() -> None:
    parent_id, child_id, unrelated_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    inputs: dict[uuid.UUID | None, dict[str, object]] = {child_id: {}}
    _apply_parent_child_inputs(inputs, (child_id,), [(parent_id, child_id)])
    assert "either_parent_insured_under_policy" not in inputs[child_id]
    _apply_parent_child_inputs(inputs, (parent_id, child_id), [(unrelated_id, child_id)])
    assert "either_parent_insured_under_policy" not in inputs[child_id]
    _apply_parent_child_inputs(inputs, (parent_id, child_id), [(parent_id, child_id)])
    assert inputs[child_id]["either_parent_insured_under_policy"] == {
        "state": "known",
        "kind": "boolean",
        "value": True,
    }


def test_deductible_configuration_uses_exact_stated_inr_amounts() -> None:
    facts = [
        SimpleNamespace(
            fact_type="sum_insured",
            status="reported",
            value={"state": "known", "kind": "quantity", "value": "10", "unit": "lakh"},
        )
    ]
    requirements = [
        SimpleNamespace(
            criterion="deductible",
            status="reported",
            target_value={"state": "known", "kind": "quantity", "value": "500000", "unit": "INR"},
        )
    ]
    inputs = _deductible_configuration_inputs(facts, requirements)
    assert (
        evaluate_predicate(
            {
                "node": "all",
                "arguments": [
                    {
                        "node": "compare",
                        "operator": "eq",
                        "left": {"node": "input", "key": "selected_aggregate_deductible"},
                        "right": _literal(_quantity("500000", "money", currency="INR")),
                    },
                    {
                        "node": "compare",
                        "operator": "lt",
                        "left": {"node": "input", "key": "selected_base_sum_insured"},
                        "right": _literal(_quantity("2500000", "money", currency="INR")),
                    },
                ],
            },
            inputs,
        )
        == Truth.TRUE
    )


def test_deductible_match_rejects_only_verified_ineligible_selection() -> None:
    requirement = SimpleNamespace(criterion="deductible")
    result = SimpleNamespace(
        rule=SimpleNamespace(
            id=uuid.uuid4(),
            body={
                "effects": [
                    {
                        "kind": "eligibility",
                        "target_key": "aggregate_deductible_selection",
                        "decision": "ineligible",
                    }
                ]
            },
        ),
        evidence_complete=True,
        subject_results=(SimpleNamespace(subject_person_id=None, applies=Truth.TRUE),),
    )
    assert _deductible_selection_match(requirement, (result,), None)[0] == "does_not_meet"
    result.evidence_complete = False
    assert _deductible_selection_match(requirement, (result,), None) is None


def test_childbirth_exclusion_applies_only_to_explicit_childbirth_request() -> None:
    requirement = SimpleNamespace(
        criterion="maternity",
        target_value={"state": "known", "kind": "boolean", "value": True},
        source_statement=SimpleNamespace(
            source_message=SimpleNamespace(content="Childbirth-expense cover is mandatory.")
        ),
    )
    assert (
        _childbirth_rule_inputs([requirement])["condition_is_ectopic_pregnancy"]["value"] is False
    )
    result = SimpleNamespace(
        rule=SimpleNamespace(
            id=uuid.uuid4(),
            body={"effects": [{"kind": "exclusion", "target_key": "childbirth_expense_exclusion"}]},
        ),
        evidence_complete=True,
        subject_results=(SimpleNamespace(subject_person_id=None, applies=Truth.TRUE),),
    )
    assert _childbirth_exclusion_match(requirement, (result,), None)[0] == "does_not_meet"
    requirement.source_statement.source_message.content = "Ectopic pregnancy cover is mandatory."
    assert _childbirth_exclusion_match(requirement, (result,), None) is None


def test_ayurveda_scenario_keeps_unstated_claim_admissibility_unknown() -> None:
    requirement = SimpleNamespace(
        criterion="specific_treatment",
        source_statement=SimpleNamespace(
            source_message=SimpleNamespace(
                content="Ayurveda hospitalization in India at an eligible AYUSH healthcare facility with a licensed practitioner."
            )
        ),
    )
    inputs = _ayush_rule_inputs([requirement])
    assert inputs["ayush_system"]["value"] == "ayurveda"
    assert inputs["treatment_at_eligible_ayush_hospital_or_healthcare_facility"]["value"] is True
    assert inputs["ayush_practitioner_has_valid_practicing_license"]["value"] is True
    assert inputs["treatment_taken_in_india"]["value"] is True
    assert "claim_admissible_under_hospitalization_expenses" not in inputs


def test_higher_room_claim_illustration_uses_exact_ratio() -> None:
    inputs = _room_illustration_inputs(
        {
            "eligible_room_rent_limit": {
                "state": "known",
                "kind": "quantity",
                "unit": "INR",
                "value": "5000",
            },
            "room_rent_actually_incurred": {
                "state": "known",
                "kind": "quantity",
                "unit": "INR",
                "value": "10000",
            },
            "total_associated_medical_expenses": {
                "state": "known",
                "kind": "quantity",
                "unit": "lakh",
                "value": "1",
            },
        }
    )
    expression = {
        "node": "operation",
        "operator": "multiply",
        "arguments": [
            {
                "node": "operation",
                "operator": "divide",
                "arguments": [
                    {"node": "input", "key": "eligible_room_rent_limit"},
                    {"node": "input", "key": "room_rent_actually_incurred"},
                ],
            },
            {"node": "input", "key": "total_associated_medical_expenses"},
        ],
    }
    assert evaluate_expression(expression, inputs) == Scalar(Decimal("50000"), "money", "INR")


def test_room_and_icu_requirement_needs_both_verified_unlimited_rules() -> None:
    requirement = cast(
        CustomerRequirement,
        SimpleNamespace(
            criterion="room_category",
            target_value={
                "kind": "text",
                "state": "known",
                "value": "no separate room-rent or ICU-charge limit",
            },
        ),
    )

    def result(key: str, *, verified: bool = True) -> Any:
        return SimpleNamespace(
            rule=SimpleNamespace(
                id=uuid.uuid4(),
                body={
                    "effects": [
                        {
                            "target_key": key,
                            "amount": {
                                "node": "literal",
                                "value": {"state": "unlimited", "unit": "money"},
                            },
                        }
                    ]
                },
            ),
            evidence_complete=verified,
            subject_results=(SimpleNamespace(subject_person_id=None, applies=Truth.TRUE),),
        )

    room = result("hospitalization_room_rent_limit")
    icu = result("hospitalization_icu_charge_limit")
    assert _no_separate_room_icu_match(requirement, (room, icu), None)[0] == "meets"
    requirement.operator = "excludes"
    requirement.target_value["value"] = "separate room-rent or ICU-charge limit"
    assert _no_separate_room_icu_match(requirement, (room, icu), None)[0] == "meets"
    assert _no_separate_room_icu_match(requirement, (room,), None)[0] == "partly_meets"
    assert (
        _no_separate_room_icu_match(
            requirement,
            (room, result("hospitalization_icu_charge_limit", verified=False)),
            None,
        )[0]
        == "partly_meets"
    )


def test_five_year_requirement_supplies_exact_tenure_rule_input() -> None:
    target = {"state": "known", "kind": "quantity", "value": "5", "unit": "year"}
    requirement = cast(
        CustomerRequirement,
        SimpleNamespace(
            criterion="policy_tenure_selection", status="reported", target_value=target
        ),
    )
    selected = _selected_policy_tenure([requirement])
    assert selected == target
    assert (
        evaluate_predicate(
            {
                "node": "membership",
                "item": {"node": "input", "key": "selected_policy_tenure"},
                "members": [_literal(_quantity("5", "year"))],
            },
            {"selected_policy_tenure": selected},
        )
        == Truth.TRUE
    )


def test_unknown_and_unlimited_quantities_propagate_as_unknown() -> None:
    for value in (
        {"state": "unknown", "expected_unit": "money", "reason": "not quoted"},
        {"state": "unlimited", "unit": "money", "basis_span_ids": [str(uuid.uuid4())]},
        {"state": "not_applicable", "reason": "not offered", "basis_span_ids": []},
    ):
        assert evaluate_expression(_literal(value), {}) is None


def test_round_uses_explicit_scale_and_registered_mode() -> None:
    expression = {
        "node": "operation",
        "operator": "round",
        "arguments": [
            _literal(_quantity("12.345", "money", currency="INR")),
            _literal(_quantity("2", "count")),
            _literal({"kind": "code", "namespace": "rounding", "value": "half_up"}),
        ],
    }

    assert evaluate_expression(expression, {}) == Scalar(Decimal("12.35"), "money", "INR")
    expression["arguments"][2] = _literal(
        {"kind": "code", "namespace": "rounding", "value": "unresolved"}
    )
    assert evaluate_expression(expression, {}) is None


def test_calendar_and_elapsed_operations_use_contract_units() -> None:
    calendar_result = evaluate_expression(
        {
            "node": "operation",
            "operator": "calendar_add",
            "arguments": [
                _literal({"kind": "date", "value": "2024-02-29"}),
                _literal(
                    {
                        "kind": "duration",
                        "value": {
                            "state": "known",
                            "value": 1,
                            "unit": "calendar_year",
                            "anchor_event": "policy_start",
                            "boundary": "inclusive",
                        },
                    }
                ),
            ],
        },
        {},
    )
    assert calendar_result == Scalar(dt.date(2025, 2, 28))

    elapsed_result = evaluate_expression(
        {
            "node": "operation",
            "operator": "elapsed_between",
            "arguments": [
                _literal({"kind": "date", "value": "2026-01-01"}),
                _literal({"kind": "date", "value": "2026-01-31"}),
                _literal({"kind": "code", "namespace": "duration", "value": "elapsed_day"}),
            ],
        },
        {},
    )
    assert elapsed_result == Scalar(Decimal(30), "elapsed_day")


def test_table_lookup_matches_typed_exact_selectors_and_evaluates_cell_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rule = _table_rule("sum_insured_inr", "procedure")
    cell = SimpleNamespace(
        selectors=[
            {
                "axis": "sum_insured_inr",
                "operator": "eq",
                "value": _quantity("1000000", "money", currency="INR"),
            },
            {
                "axis": "procedure",
                "operator": "eq",
                "value": {
                    "kind": "code",
                    "namespace": "test-procedure",
                    "value": "robotic_surgery",
                },
            },
        ],
        value=_literal(_quantity("300000", "money", currency="INR")),
    )

    def fake_filter(**kwargs: object) -> list[SimpleNamespace]:
        assert kwargs == {"policy_rule": rule}
        return [cell]

    monkeypatch.setattr(PolicyRuleTableCell.objects, "filter", fake_filter)
    result = evaluate_expression(
        {
            "node": "table_lookup",
            "table_key": "benefit-limit",
            "selectors": [
                {"axis": "procedure", "value": {"node": "input", "key": "procedure"}},
                {
                    "axis": "sum_insured_inr",
                    "value": {"node": "input", "key": "sum_insured_inr"},
                },
            ],
            "missing": "unknown",
        },
        {
            "sum_insured_inr": _quantity("1000000", "money", currency="INR"),
            "procedure": {
                "kind": "code",
                "namespace": "test-procedure",
                "value": "robotic_surgery",
            },
        },
        table_rule=rule,
    )

    assert result == Scalar(Decimal("300000"), "money", "INR")


def test_table_lookup_returns_unknown_for_overlapping_ranges(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rule = _table_rule("entry_age")
    cells = [
        SimpleNamespace(
            selectors=[
                {
                    "axis": "entry_age",
                    "operator": "lte",
                    "value": _quantity(limit, "year"),
                }
            ],
            value=_literal(_quantity(result, "money", currency="INR")),
        )
        for limit, result in (("60", "100"), ("65", "200"))
    ]

    def fake_filter(**kwargs: object) -> list[SimpleNamespace]:
        assert kwargs == {"policy_rule": rule}
        return cells

    monkeypatch.setattr(PolicyRuleTableCell.objects, "filter", fake_filter)
    expression = {
        "node": "table_lookup",
        "table_key": "benefit-limit",
        "selectors": [{"axis": "entry_age", "value": {"node": "input", "key": "age"}}],
        "missing": "unknown",
    }

    assert (
        evaluate_expression(
            expression,
            {"age": _quantity("55", "year")},
            table_rule=rule,
        )
        is None
    )


def test_table_selector_overlap_understands_boundaries_and_dimensions() -> None:
    at_most_60 = [{"axis": "age", "operator": "lte", "value": _quantity("60", "year")}]
    over_60 = [{"axis": "age", "operator": "gt", "value": _quantity("60", "year")}]
    from_60 = [{"axis": "age", "operator": "gte", "value": _quantity("60", "year")}]

    assert table_selectors_overlap(at_most_60, over_60) is False
    assert table_selectors_overlap(at_most_60, from_60) is True
    assert (
        table_selectors_overlap(
            at_most_60,
            [{"axis": "age", "operator": "gt", "value": _quantity("60", "count")}],
        )
        is None
    )


def test_table_lookup_rejects_wrong_key_or_incomplete_axes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rule = _table_rule("age", "sum_insured")

    def unexpected_filter(**kwargs: object) -> list[object]:
        raise AssertionError(f"table cells should not be queried: {kwargs}")

    monkeypatch.setattr(PolicyRuleTableCell.objects, "filter", unexpected_filter)
    selector = {"axis": "age", "value": {"node": "input", "key": "age"}}
    inputs = {"age": _quantity("35", "year")}
    assert (
        evaluate_expression(
            {
                "node": "table_lookup",
                "table_key": "another-table",
                "selectors": [selector],
                "missing": "unknown",
            },
            inputs,
            table_rule=rule,
        )
        is None
    )
    assert (
        evaluate_expression(
            {
                "node": "table_lookup",
                "table_key": "benefit-limit",
                "selectors": [selector],
                "missing": "unknown",
            },
            inputs,
            table_rule=rule,
        )
        is None
    )


def test_expression_depth_limit_fails_closed() -> None:
    expression: dict[str, object] = _literal(_quantity("1", "count"))
    for _ in range(34):
        expression = {
            "node": "operation",
            "operator": "abs",
            "arguments": [expression],
        }

    assert evaluate_expression(expression, {}) is None


def test_predicates_compare_typed_values_and_propagate_unknown() -> None:
    predicate = {
        "node": "compare",
        "operator": "gte",
        "left": {"node": "input", "key": "age"},
        "right": _literal(_quantity("18", "year")),
    }
    assert evaluate_predicate(predicate, {"age": _quantity("42", "year")}) == Truth.TRUE
    assert evaluate_predicate(predicate, {}) == Truth.UNKNOWN
    assert evaluate_predicate(predicate, {"age": _quantity("42", "count")}) == Truth.UNKNOWN


def test_current_inputs_keep_each_insured_person_separate() -> None:
    first_person_id = uuid.uuid4()
    second_person_id = uuid.uuid4()
    global_budget = cast(
        Any,
        SimpleNamespace(
            status="reported",
            fact_type="budget",
            value={
                "state": "known",
                "kind": "quantity",
                "value": "30000",
                "unit": "money",
                "currency": "INR",
            },
            source_statement=SimpleNamespace(subject_person_id=None),
        ),
    )
    first_age = cast(
        Any,
        SimpleNamespace(
            status="reported",
            fact_type="age",
            value={
                "state": "known",
                "kind": "quantity",
                "value": "35",
                "unit": "year",
            },
            source_statement=SimpleNamespace(subject_person_id=first_person_id),
        ),
    )
    second_age = cast(
        Any,
        SimpleNamespace(
            status="reported",
            fact_type="age",
            value={
                "state": "known",
                "kind": "quantity",
                "value": "67",
                "unit": "year",
            },
            source_statement=SimpleNamespace(subject_person_id=second_person_id),
        ),
    )

    first_inputs = current_inputs([global_budget, first_age, second_age], first_person_id)
    second_inputs = current_inputs([global_budget, first_age, second_age], second_person_id)

    assert first_inputs["age"] == first_age.value
    assert second_inputs["age"] == second_age.value
    assert first_inputs["budget"] == global_budget.value
    assert second_inputs["budget"] == global_budget.value


def test_table_contract_helpers_are_closed_and_resolvable() -> None:
    header_span_id = str(uuid.uuid4())
    source_span_id = str(uuid.uuid4())
    body = {
        "schema_version": 1,
        "applies_when": {"node": "constant", "value": "true"},
        "inputs": [],
        "effects": [
            {
                "kind": "limit",
                "target_key": "robotic_surgery_limit",
                "scope": {
                    "subject": "policy",
                    "subject_ids": [],
                    "period": "policy_term",
                    "benefit_keys": ["robotic_surgery"],
                    "reset": "never",
                },
                "amount": {
                    "node": "table_lookup",
                    "table_key": "benefit-limit",
                    "selectors": [
                        {
                            "axis": "sum_insured_inr",
                            "value": {"node": "input", "key": "sum_insured_inr"},
                        }
                    ],
                    "missing": "unknown",
                },
                "inclusive_categories": ["robotic_surgery"],
                "percentage_base_key": None,
            }
        ],
        "mandatory_rule_keys": [],
        "source_span_ids": [source_span_id],
        "unresolved": [],
        "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
        "table": {
            "table_key": "benefit-limit",
            "axes": [
                {
                    "key": "sum_insured_inr",
                    "meaning": "Selected base sum insured",
                    "value_kind": "quantity",
                    "unit": "money",
                    "header_span_id": header_span_id,
                }
            ],
            "result_unit": "money",
            "scope": {
                "subject": "policy",
                "subject_ids": [],
                "period": "policy_term",
                "benefit_keys": ["robotic_surgery"],
                "reset": "never",
            },
        },
    }
    selectors = [
        {
            "axis": "sum_insured_inr",
            "operator": "eq",
            "value": _quantity("1000000", "money", currency="INR"),
        }
    ]

    assert RuleV1.model_validate(body).root == body
    assert TableSelectorsV1.model_validate(selectors).root == selectors

    invalid = selectors + [{"axis": "extra", "operator": "eq", "value": {"x": 1}}]
    with pytest.raises(ValueError, match="TableSelectorsV1"):
        TableSelectorsV1.model_validate(invalid)


def test_extracted_table_cells_cross_validate_axes_units_and_evidence() -> None:
    source_span_id = str(uuid.uuid4())
    header_span_id = str(uuid.uuid4())
    first_cell_span_id = str(uuid.uuid4())
    second_cell_span_id = str(uuid.uuid4())
    footnote_span_id = str(uuid.uuid4())
    body = {
        "schema_version": 1,
        "applies_when": {"node": "constant", "value": "true"},
        "inputs": [
            {
                "key": "procedure",
                "value_kind": "code",
                "unit": "procedure-code",
                "required": True,
                "provenance_required": True,
            }
        ],
        "effects": [
            {
                "kind": "limit",
                "target_key": "procedure_limit",
                "scope": {
                    "subject": "policy",
                    "subject_ids": [],
                    "period": "policy_term",
                    "benefit_keys": ["procedure"],
                    "reset": "never",
                },
                "amount": {
                    "node": "table_lookup",
                    "table_key": "procedure-limit",
                    "selectors": [
                        {
                            "axis": "procedure",
                            "value": {"node": "input", "key": "procedure"},
                        }
                    ],
                    "missing": "unknown",
                },
                "inclusive_categories": ["procedure"],
                "percentage_base_key": None,
            }
        ],
        "mandatory_rule_keys": [],
        "source_span_ids": [source_span_id],
        "unresolved": [],
        "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
        "table": {
            "table_key": "procedure-limit",
            "axes": [
                {
                    "key": "procedure",
                    "meaning": "Covered procedure",
                    "value_kind": "code",
                    "unit": "procedure-code",
                    "header_span_id": header_span_id,
                }
            ],
            "result_unit": "money",
            "scope": {
                "subject": "policy",
                "subject_ids": [],
                "period": "policy_term",
                "benefit_keys": ["procedure"],
                "reset": "never",
            },
        },
    }
    rule = ExtractedPolicyRule.model_validate(
        {
            "rule_key": "special_treatments.limit.procedure_table",
            "rule_type": "limit",
            "inventory_category": "special_treatments",
            "body": body,
            "evidence_span_ids": [source_span_id],
            "table_cells": [
                {
                    "selectors": '[{"axis":"procedure","operator":"eq","value":'
                    '{"kind":"code","namespace":"procedure-code","value":"robotic"}}]',
                    "value": '{"node":"literal","value":{"state":"finite",'
                    '"value":"300000","unit":"money","currency":"INR"}}',
                    "evidence_span_id": first_cell_span_id,
                },
                {
                    "selectors": '[{"axis":"procedure","operator":"eq","value":'
                    '{"kind":"code","namespace":"procedure-code","value":"cataract"}}]',
                    "value": '{"node":"literal","value":{"state":"finite",'
                    '"value":"40000","unit":"money","currency":"INR"}}',
                    "evidence_span_id": second_cell_span_id,
                },
            ],
            "table_footnote_span_ids": [footnote_span_id],
        }
    )
    allowed = {
        source_span_id,
        header_span_id,
        first_cell_span_id,
        second_cell_span_id,
        footnote_span_id,
    }

    problems, cells, headers, footnotes = _table_rule_problems(
        rule,
        rule.body,
        allowed_span_ids=allowed,
    )

    assert problems == []
    assert len(cells) == 2
    assert headers == {header_span_id}
    assert footnotes == {footnote_span_id}


def test_extracted_table_cells_reject_overlapping_numeric_ranges() -> None:
    source_span_id = str(uuid.uuid4())
    header_span_id = str(uuid.uuid4())
    cell_span_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    body = {
        "table": {
            "table_key": "age-limit",
            "axes": [
                {
                    "key": "age",
                    "meaning": "Entry age",
                    "value_kind": "quantity",
                    "unit": "year",
                    "header_span_id": header_span_id,
                }
            ],
            "result_unit": "money",
        },
        "effects": [
            {
                "amount": {
                    "node": "table_lookup",
                    "table_key": "age-limit",
                    "selectors": [{"axis": "age", "value": {"node": "input", "key": "age"}}],
                    "missing": "unknown",
                }
            }
        ],
    }
    rule = cast(
        ExtractedPolicyRule,
        SimpleNamespace(
            rule_key="limit.limit.age_table",
            body=body,
            evidence_span_ids=[source_span_id],
            table_footnote_span_ids=[],
            table_cells=[
                SimpleNamespace(
                    selectors=[
                        {
                            "axis": "age",
                            "operator": "lte",
                            "value": _quantity(limit, "year"),
                        }
                    ],
                    value=_literal(_quantity(value, "money", currency="INR")),
                    evidence_span_id=span_id,
                )
                for limit, value, span_id in (
                    ("60", "100", cell_span_ids[0]),
                    ("65", "200", cell_span_ids[1]),
                )
            ],
        ),
    )

    problems, _cells, _headers, _footnotes = _table_rule_problems(rule, body)

    assert "table cell selector ranges overlap" in problems


def _requirement(
    *,
    operator: str,
    priority: str = "preferred",
    target_value: dict[str, object] | None = None,
) -> CustomerRequirement:
    return cast(
        CustomerRequirement,
        SimpleNamespace(operator=operator, priority=priority, target_value=target_value),
    )


def test_compare_requirement_reports_the_actual_coverage_amount_with_no_target() -> None:
    requirement = _requirement(operator="maximize", target_value=None)
    effect = {"kind": "coverage", "amount": _quantity("1500000", "money", currency="INR")}
    rule = _table_rule()

    outcome, comparison_value = _compare_requirement(requirement, effect, {}, rule)

    assert outcome == "unknown"
    assert comparison_value == {
        "state": "finite",
        "value": "1500000",
        "unit": "money",
        "currency": "INR",
    }


def test_compare_requirement_meets_a_higher_actual_against_a_minimum_floor() -> None:
    requirement = _requirement(
        operator="greater_than_or_equal",
        target_value=_quantity("1000000", "money", currency="INR"),
    )
    effect = {"kind": "coverage", "amount": _quantity("1500000", "money", currency="INR")}
    rule = _table_rule()

    outcome, comparison_value = _compare_requirement(requirement, effect, {}, rule)

    assert outcome == "meets"
    assert comparison_value is not None
    assert comparison_value["value"] == "1500000"


def test_compare_requirement_does_not_serialize_a_boolean_actual() -> None:
    requirement = _requirement(operator="is_available")
    effect = {"kind": "right"}
    rule = _table_rule()

    outcome, comparison_value = _compare_requirement(requirement, effect, {}, rule)

    assert outcome == "meets"
    assert comparison_value is None


def test_aggregate_comparison_value_picks_the_maximum_for_maximize() -> None:
    low = _quantity("500000", "money", currency="INR")
    high = _quantity("1500000", "money", currency="INR")

    assert _aggregate_comparison_value("maximize", [low, None, high]) == high


def test_aggregate_comparison_value_picks_the_minimum_for_minimize() -> None:
    low = _quantity("500000", "money", currency="INR")
    high = _quantity("1500000", "money", currency="INR")

    assert _aggregate_comparison_value("minimize", [high, low]) == low


@pytest.mark.django_db
def test_evaluate_release_keeps_stable_product_order_regardless_of_coverage() -> None:
    """DB-level neutral-order proof using synthetic test-only fixtures.

    Builds a throwaway five-product KnowledgeRelease with one rule per product so
    evaluate_release()'s comparison_product_count() gate (exactly 5, standard label) is
    satisfied, then proves criterion outcomes cannot alter the stable product order.
    """
    capture = public_html_capture()
    span = EvidenceSpan.objects.create(
        source_capture=capture,
        section_label="coverage",
        quote="Test-only synthetic coverage amount, not attributed to any real insurer document.",
        context={"span_ids": [], "notes": []},
        method="html",
        verification="reviewed",
        locator={
            "schema_version": 1,
            "blob_sha256": capture.original_file.sha256,
            "resolver_version": "test-html/1",
            "kind": "html_element",
            "encoding": "utf-8",
            "selector": "body",
            "selector_language": "css",
            "occurrence": 0,
            "text_interpretation": "decoded_text_content",
            "attribute_name": None,
        },
    )
    applicability = {
        "schema_version": 1,
        "predicate": {"node": "constant", "value": "true"},
        "event_basis": ["issue"],
        "source_span_ids": [str(span.id)],
        "unresolved": [],
    }
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
    coverage_amounts = ["500000", "1500000", None, None, None]
    for index, amount in enumerate(coverage_amounts):
        product = Product.objects.create(
            insurer=capture.discovery_run.insurer,
            name=f"Coverage test product {index}",
            benefit_type="medical_indemnity",
            lifecycle_status="open",
            comparison_role="primary_policy",
            identity_evidence=span,
        )
        policy = PolicyVersion.objects.create(
            product=product,
            uin=f"COVERAGE-TEST-UIN-{index}",
            version_label="Current",
            applicability=applicability,
        )
        PolicyVersionDocument.objects.create(
            policy_version=policy,
            document_version=capture.document_version,
            role="base_wording",
            required_for_policy=True,
            applicability=applicability,
        )
        effects: list[dict[str, object]] = (
            [
                {
                    "kind": "grant",
                    "target_key": "maximize_cover",
                    "scope": {
                        "subject": "policy",
                        "subject_ids": [],
                        "period": "policy_term",
                        "benefit_keys": [],
                        "reset": "never",
                    },
                    "amount": _literal(_quantity(amount, "money", currency="INR")),
                    "expense_categories": [],
                }
            ]
            if amount is not None
            else [
                {
                    "kind": "eligibility",
                    "target_key": "policy_eligibility",
                    "scope": {
                        "subject": "policy",
                        "subject_ids": [],
                        "period": "policy_term",
                        "benefit_keys": [],
                        "reset": "never",
                    },
                    "decision": "eligible",
                    "reason": "Test-only inert filler effect, unrelated to maximize_cover.",
                }
            ]
        )
        rule = PolicyRule.objects.create(
            policy_version=policy,
            rule_key=f"coverage-test-{index}",
            rule_type="coverage",
            body={
                "schema_version": 1,
                "applies_when": {"node": "constant", "value": "true"},
                "inputs": [],
                "effects": effects,
                "mandatory_rule_keys": [],
                "source_span_ids": [str(span.id)],
                "unresolved": [],
                "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
            },
            review_status="verified",
        )
        PolicyRuleEvidence.objects.create(policy_rule=rule, evidence_span=span, role="supports")
        KnowledgeReleaseRule.objects.create(knowledge_release=release, policy_rule=rule)
        ProductVariant.objects.create(
            policy_version=policy,
            name="Default",
            choices={"other_selectors": []},
            availability=applicability,
            identity_evidence=span,
        )

    requirement = cast(
        CustomerRequirement,
        SimpleNamespace(
            criterion="maximize_cover",
            operator="maximize",
            priority="preferred",
            scope="entire_purchase",
            subject_person_id=None,
            target_value=None,
        ),
    )

    results = evaluate_release(release, [], [requirement])

    assert [result.variant.policy_version.product.name for result in results] == [
        f"Coverage test product {index}" for index in range(5)
    ]
    assert results[0].matches[0].comparison_value == _quantity("500000", "money", currency="INR")
    assert results[1].matches[0].comparison_value == _quantity("1500000", "money", currency="INR")
