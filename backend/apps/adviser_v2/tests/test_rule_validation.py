from __future__ import annotations

import uuid

import pytest

from apps.adviser_v2 import rule_validation
from apps.adviser_v2.rule_validation import (
    rule_graph_problems,
    rule_link_references,
    rule_semantic_problems,
)


def _quantity(value: str, unit: str, *, currency: str | None = None) -> dict[str, object]:
    result: dict[str, object] = {"state": "finite", "value": value, "unit": unit}
    if currency is not None:
        result["currency"] = currency
    return result


def _literal(value: dict[str, object]) -> dict[str, object]:
    return {"node": "literal", "value": value}


def _scope(**overrides: object) -> dict[str, object]:
    result: dict[str, object] = {
        "subject": "person",
        "subject_ids": [],
        "period": "policy_term",
        "benefit_keys": [],
        "reset": "never",
    }
    result.update(overrides)
    return result


def _body(
    *,
    inputs: list[dict[str, object]] | None = None,
    effect: dict[str, object] | None = None,
    applies_when: dict[str, object] | None = None,
    mandatory_rule_keys: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": 1,
        "applies_when": applies_when or {"node": "constant", "value": "true"},
        "inputs": inputs or [],
        "effects": [
            effect
            or {
                "kind": "definition",
                "target_key": "test.term",
                "scope": _scope(),
                "term_key": "test.term",
                "value": _literal({"kind": "boolean", "value": True}),
            }
        ],
        "mandatory_rule_keys": mandatory_rule_keys or [],
        "source_span_ids": [str(uuid.uuid4())],
        "unresolved": [],
        "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
    }


def test_semantic_validator_accepts_approved_money_and_reference_dimensions() -> None:
    inputs = [
        {
            "key": "selected_policy_version",
            "value_kind": "reference",
            "unit": "identity",
            "required": True,
            "provenance_required": True,
        },
        {
            "key": "base_si",
            "value_kind": "quantity",
            "unit": "money",
            "required": True,
            "provenance_required": True,
        },
    ]
    body = _body(
        inputs=inputs,
        applies_when={
            "node": "compare",
            "operator": "eq",
            "left": {"node": "input", "key": "selected_policy_version"},
            "right": {
                "node": "literal",
                "value": {
                    "kind": "reference",
                    "entity": "PolicyVersion",
                    "id": str(uuid.uuid4()),
                },
            },
        },
        effect={
            "kind": "limit",
            "target_key": "room_limit",
            "scope": _scope(period="day", benefit_keys=["room"]),
            "amount": {
                "node": "operation",
                "operator": "multiply",
                "arguments": [
                    {"node": "input", "key": "base_si"},
                    _literal(_quantity("0.02", "ratio")),
                ],
            },
            "inclusive_categories": ["room"],
            "percentage_base_key": "base_si",
        },
    )

    assert rule_semantic_problems(body) == []


def test_semantic_validator_rejects_undeclared_and_duplicate_inputs() -> None:
    declaration = {
        "key": "base_si",
        "value_kind": "quantity",
        "unit": "money",
        "required": True,
        "provenance_required": True,
    }
    body = _body(
        inputs=[declaration, declaration],
        applies_when={"node": "present", "input_key": "missing_input"},
    )

    problems = rule_semantic_problems(body)

    assert "inputs contains duplicate key: base_si" in problems
    assert "applies_when references undeclared input: missing_input" in problems


def test_semantic_validator_rejects_invalid_arithmetic_dimensions_and_arity() -> None:
    body = _body(
        effect={
            "kind": "limit",
            "target_key": "bad_limit",
            "scope": _scope(),
            "amount": {
                "node": "operation",
                "operator": "add",
                "arguments": [
                    _literal(_quantity("100", "money", currency="INR")),
                    _literal(_quantity("0.10", "ratio")),
                ],
            },
            "inclusive_categories": [],
            "percentage_base_key": None,
        }
    )
    arity_body = _body(
        effect={
            "kind": "definition",
            "target_key": "bad_subtract",
            "scope": _scope(),
            "term_key": "bad_subtract",
            "value": {
                "node": "operation",
                "operator": "subtract",
                "arguments": [_literal(_quantity("1", "count"))],
            },
        }
    )

    assert any(
        "add requires compatible dimensions" in value for value in rule_semantic_problems(body)
    )
    assert any(
        "subtract requires exactly 2 arguments" in value
        for value in rule_semantic_problems(arity_body)
    )


def test_semantic_validator_enforces_scope_field_conditions() -> None:
    body = _body()
    effect = body["effects"][0]
    assert isinstance(effect, dict)
    effect["scope"] = _scope(
        subject="body_part",
        period_start="2026-02-01",
        period_end="2026-01-01",
        reset="explicit_rule",
    )

    problems = rule_semantic_problems(body)

    assert any("body_part is required" in value for value in problems)
    assert any("period_start must not follow period_end" in value for value in problems)
    assert any("reset_rule_key is required" in value for value in problems)


def test_semantic_validator_enforces_depth_and_total_node_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    predicate: dict[str, object] = {"node": "constant", "value": "true"}
    for _ in range(rule_validation.MAX_RULE_AST_DEPTH + 1):
        predicate = {"node": "not", "argument": predicate}
    depth_problems = rule_semantic_problems(_body(applies_when=predicate))

    monkeypatch.setattr(rule_validation, "MAX_RULE_AST_NODES", 3)
    count_problems = rule_semantic_problems(
        _body(
            applies_when={
                "node": "all",
                "arguments": [
                    {"node": "constant", "value": "true"},
                    {"node": "constant", "value": "false"},
                    {"node": "constant", "value": "unknown"},
                ],
            }
        )
    )

    assert any("AST depth exceeds 32" in value for value in depth_problems)
    assert any("AST node count exceeds 3" in value for value in count_problems)


def test_rule_graph_rejects_missing_references_and_executable_cycles() -> None:
    first = _body(mandatory_rule_keys=["second"])
    second = _body(mandatory_rule_keys=["first"])
    missing = _body(mandatory_rule_keys=["not_in_release"])

    cycle_problems = rule_graph_problems(
        {
            "first": ("calculation", first),
            "second": ("calculation", second),
        }
    )
    missing_problems = rule_graph_problems({"only": ("limit", missing)})

    assert any("executable dependency cycle" in value for value in cycle_problems)
    assert "only references missing rule: not_in_release" in missing_problems


def test_rule_graph_allows_non_executable_definition_language_cycle() -> None:
    first = _body(mandatory_rule_keys=["second"])
    second = _body(mandatory_rule_keys=["first"])

    assert (
        rule_graph_problems(
            {
                "first": ("definition", first),
                "second": ("definition", second),
            }
        )
        == []
    )


def test_rule_graph_handles_a_dependency_chain_beyond_python_recursion_depth() -> None:
    rules = {
        f"rule_{index:04d}": (
            "calculation",
            _body(mandatory_rule_keys=([f"rule_{index + 1:04d}"] if index < 1_499 else [])),
        )
        for index in range(1_500)
    }

    assert rule_graph_problems(rules) == []


def test_rule_links_cover_prerequisites_exceptions_ordering_overrides_and_scope() -> None:
    body = _body(mandatory_rule_keys=["prerequisite"])
    body["effects"] = [
        {
            "kind": "exception",
            "scope": _scope(),
            "target_rule_keys": ["excluded"],
        },
        {
            "kind": "deduction",
            "scope": _scope(),
            "order_after_rule_keys": ["prior_deduction"],
        },
        {
            "kind": "precedence",
            "scope": _scope(reset="explicit_rule", reset_rule_key="reset_rule"),
            "overridden_rule_keys": ["older_rule"],
        },
    ]

    assert rule_link_references(body) == [
        ("excluded", "exception"),
        ("older_rule", "overrides"),
        ("prerequisite", "prerequisite"),
        ("prior_deduction", "calculation_input"),
        ("reset_rule", "scope"),
    ]
