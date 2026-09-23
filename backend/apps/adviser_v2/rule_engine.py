"""Deterministic policy-rule evaluation for neutral product comparisons."""

from __future__ import annotations

import calendar
import datetime as dt
import uuid
from dataclasses import dataclass
from decimal import (
    ROUND_CEILING,
    ROUND_FLOOR,
    ROUND_HALF_EVEN,
    ROUND_HALF_UP,
    Decimal,
    DivisionByZero,
    InvalidOperation,
)
from enum import StrEnum
from typing import Any

from .models import (
    CustomerFact,
    CustomerRequirement,
    KnowledgeRelease,
    KnowledgeReleaseRule,
    PersonRelationship,
    PolicyRule,
    PolicyRuleEvidence,
    PolicyRuleTableCell,
    ProductVariant,
)
from .release_scope import comparison_product_count


class Truth(StrEnum):
    TRUE = "true"
    FALSE = "false"
    UNKNOWN = "unknown"


type ScalarValue = Decimal | dt.date | dt.datetime | str | bool | int

MAX_EXPRESSION_DEPTH = 32
MAX_ROUNDING_SCALE = 12
ROUNDING_MODES = {
    "half_up": ROUND_HALF_UP,
    "half_even": ROUND_HALF_EVEN,
    "floor": ROUND_FLOOR,
    "ceiling": ROUND_CEILING,
}


@dataclass(frozen=True)
class Scalar:
    value: ScalarValue
    unit: str | None = None
    currency: str | None = None


@dataclass(frozen=True)
class RuleResult:
    rule: PolicyRule
    applies: Truth
    evidence_complete: bool
    evidence_span_ids: tuple[uuid.UUID, ...]
    subject_results: tuple[SubjectRuleResult, ...]


@dataclass(frozen=True)
class SubjectRuleResult:
    subject_person_id: uuid.UUID | None
    applies: Truth


@dataclass(frozen=True)
class RequirementResult:
    requirement: CustomerRequirement
    outcome: str
    comparison_value: dict[str, object] | None
    rule_ids: tuple[str, ...]


@dataclass(frozen=True)
class PolicyComparisonResult:
    variant: ProductVariant
    matches: tuple[RequirementResult, ...]
    rules: tuple[RuleResult, ...]


def _typed_value(value: object) -> Scalar | None:
    if not isinstance(value, dict):
        return None
    state = value.get("state")
    if state in {"unknown", "not_applicable", "unlimited"}:
        return None
    kind = value.get("kind")
    raw = value.get("value")
    if state == "finite" or (state == "known" and kind == "quantity"):
        unit = value.get("unit")
        currency = value.get("currency")
        if not isinstance(raw, str) or not isinstance(unit, str):
            return None
        if currency is not None and not isinstance(currency, str):
            return None
        try:
            return Scalar(Decimal(raw), unit, currency)
        except InvalidOperation:
            return None
    if kind == "date" and isinstance(raw, str):
        try:
            return Scalar(dt.date.fromisoformat(raw))
        except ValueError:
            return None
    if kind == "instant" and isinstance(raw, str):
        try:
            return Scalar(dt.datetime.fromisoformat(raw.replace("Z", "+00:00")))
        except ValueError:
            return None
    if kind == "duration" and isinstance(raw, dict):
        duration_value = raw.get("value")
        duration_unit = raw.get("unit")
        if (
            raw.get("state") != "known"
            or not isinstance(duration_value, int)
            or isinstance(duration_value, bool)
            or not isinstance(duration_unit, str)
        ):
            return None
        return Scalar(Decimal(duration_value), duration_unit)
    if kind == "reference":
        identifier = value.get("id")
        entity = value.get("entity")
        if isinstance(identifier, str) and isinstance(entity, str):
            return Scalar(identifier, entity)
        return None
    if kind == "code":
        code = value.get("value")
        namespace = value.get("namespace")
        if isinstance(code, str) and isinstance(namespace, str):
            return Scalar(code, namespace)
        return None
    if kind == "boolean" and isinstance(raw, bool):
        return Scalar(raw)
    if kind == "text" and isinstance(raw, str):
        return Scalar(raw)
    return None


def _same_dimension(left: Scalar, right: Scalar) -> bool:
    return left.unit == right.unit and left.currency == right.currency


def _same_value(left: Scalar, right: Scalar) -> bool:
    if not _same_dimension(left, right):
        return False
    if isinstance(left.value, bool) or isinstance(right.value, bool):
        return type(left.value) is type(right.value) and left.value == right.value
    return left.value == right.value


_QUANTITY_V1_UNITS = frozenset(
    {
        "money",
        "ratio",
        "day",
        "month",
        "year",
        "hour",
        "minute",
        "count",
        "money_per_day",
        "money_per_year",
        "dioptre",
        "kg_per_m2",
    }
)


def _serialize_comparison_value(actual: Scalar | None) -> dict[str, object] | None:
    """Encode a computed effect value as a TypedValueV1 QuantityV1 payload, when numeric."""
    if actual is None or not isinstance(actual.value, Decimal) or actual.unit is None:
        return None
    if actual.unit not in _QUANTITY_V1_UNITS:
        return None
    payload: dict[str, object] = {
        "state": "finite",
        "value": str(actual.value),
        "unit": actual.unit,
    }
    if actual.currency is not None:
        payload["currency"] = actual.currency
    return payload


def _aggregate_comparison_value(
    operator: str, values: list[dict[str, object] | None]
) -> dict[str, object] | None:
    candidates = [value for value in values if value is not None]
    if not candidates:
        return None
    if operator == "minimize":
        return min(candidates, key=lambda item: Decimal(str(item["value"])))
    if operator == "maximize":
        return max(candidates, key=lambda item: Decimal(str(item["value"])))
    return candidates[0]


def _calendar_add(value: dt.date, amount: int, unit: str) -> dt.date | None:
    if amount < 0:
        return None
    try:
        if unit == "elapsed_day":
            return value + dt.timedelta(days=amount)
        if unit == "calendar_year":
            year, month = value.year + amount, value.month
        elif unit == "calendar_month":
            index = value.year * 12 + value.month - 1 + amount
            year, month = divmod(index, 12)
            month += 1
        else:
            return None
        return dt.date(year, month, min(value.day, calendar.monthrange(year, month)[1]))
    except (OverflowError, ValueError):
        return None


def _table_axes(table_rule: PolicyRule, table_key: object) -> tuple[str, ...] | None:
    table = table_rule.body.get("table")
    if not isinstance(table, dict) or table.get("table_key") != table_key:
        return None
    axes = table.get("axes")
    if not isinstance(axes, list):
        return None
    keys: list[str] = []
    for axis in axes:
        if not isinstance(axis, dict) or not isinstance(axis.get("key"), str):
            return None
        keys.append(axis["key"])
    if not keys or len(keys) != len(set(keys)):
        return None
    return tuple(keys)


def _table_selector_matches(selected: Scalar, selector: object) -> bool:
    if not isinstance(selector, dict):
        return False
    boundary = _typed_value(selector.get("value"))
    if boundary is None or not _same_dimension(selected, boundary):
        return False
    operator = selector.get("operator")
    if operator == "eq":
        return _same_value(selected, boundary)
    if not isinstance(operator, str):
        return False
    outcome = _ordered_comparison(selected.value, boundary.value, operator)
    return outcome is True


def _selector_constraint_overlap(left: object, right: object) -> bool | None:
    if not isinstance(left, dict) or not isinstance(right, dict):
        return None
    left_boundary = _typed_value(left.get("value"))
    right_boundary = _typed_value(right.get("value"))
    if (
        left_boundary is None
        or right_boundary is None
        or not _same_dimension(left_boundary, right_boundary)
    ):
        return None
    left_operator = left.get("operator")
    right_operator = right.get("operator")
    operators = {"eq", "lt", "lte", "gt", "gte"}
    if left_operator not in operators or right_operator not in operators:
        return None
    if left_operator == "eq":
        return _table_selector_matches(left_boundary, right)
    if right_operator == "eq":
        return _table_selector_matches(right_boundary, left)
    left_is_lower = left_operator in {"gt", "gte"}
    right_is_lower = right_operator in {"gt", "gte"}
    if left_is_lower == right_is_lower:
        return True
    lower_selector, upper_selector = (left, right) if left_is_lower else (right, left)
    lower_boundary = _typed_value(lower_selector.get("value"))
    upper_boundary = _typed_value(upper_selector.get("value"))
    assert lower_boundary is not None
    assert upper_boundary is not None
    if _same_value(lower_boundary, upper_boundary):
        return lower_selector.get("operator") == "gte" and upper_selector.get("operator") == "lte"
    return _ordered_comparison(lower_boundary.value, upper_boundary.value, "lt")


def table_selectors_overlap(left: object, right: object) -> bool | None:
    """Return whether two complete table-cell selector regions intersect.

    ``None`` means one selector set is malformed or dimensionally incomparable.
    Publication treats both overlap and indeterminate comparison as fail-closed.
    """

    if not isinstance(left, list) or not isinstance(right, list):
        return None

    def by_axis(selectors: list[object]) -> dict[str, object] | None:
        result: dict[str, object] = {}
        for selector in selectors:
            if not isinstance(selector, dict) or not isinstance(selector.get("axis"), str):
                return None
            axis = selector["axis"]
            if axis in result:
                return None
            result[axis] = selector
        return result

    left_axes = by_axis(left)
    right_axes = by_axis(right)
    if left_axes is None or right_axes is None or set(left_axes) != set(right_axes):
        return None
    for axis in left_axes:
        overlap = _selector_constraint_overlap(left_axes[axis], right_axes[axis])
        if overlap is None:
            return None
        if not overlap:
            return False
    return True


def _matching_table_cells(
    table_rule: PolicyRule,
    axis_values: dict[str, Scalar],
) -> list[Any]:
    matches: list[Any] = []
    expected_axes = set(axis_values)
    for cell in PolicyRuleTableCell.objects.filter(policy_rule=table_rule):
        selectors = cell.selectors
        if not isinstance(selectors, list) or len(selectors) != len(expected_axes):
            continue
        by_axis: dict[str, object] = {}
        malformed = False
        for selector in selectors:
            if not isinstance(selector, dict) or not isinstance(selector.get("axis"), str):
                malformed = True
                break
            axis = selector["axis"]
            if axis in by_axis:
                malformed = True
                break
            by_axis[axis] = selector
        if malformed or set(by_axis) != expected_axes:
            continue
        if all(
            _table_selector_matches(selected, by_axis[axis])
            for axis, selected in axis_values.items()
        ):
            matches.append(cell)
    return matches


def evaluate_expression(
    expression: object,
    inputs: dict[str, object],
    *,
    table_rule: PolicyRule | None = None,
    _depth: int = 0,
) -> Scalar | None:
    if _depth > MAX_EXPRESSION_DEPTH or not isinstance(expression, dict):
        return None
    node = expression.get("node")
    if node == "literal":
        return _typed_value(expression.get("value"))
    if node == "input":
        return _typed_value(inputs.get(str(expression.get("key"))))
    if node == "conditional":
        state = evaluate_predicate(
            expression.get("when"),
            inputs,
            table_rule=table_rule,
            _depth=_depth + 1,
        )
        if state == Truth.UNKNOWN:
            return None
        branch = "then" if state == Truth.TRUE else "otherwise"
        return evaluate_expression(
            expression.get(branch),
            inputs,
            table_rule=table_rule,
            _depth=_depth + 1,
        )
    if node == "table_lookup" and table_rule is not None:
        expected_axes = _table_axes(table_rule, expression.get("table_key"))
        raw_selectors = expression.get("selectors")
        if expected_axes is None or not isinstance(raw_selectors, list):
            return None
        axis_values: dict[str, Scalar] = {}
        for selector in raw_selectors:
            if not isinstance(selector, dict) or not isinstance(selector.get("axis"), str):
                return None
            axis = selector["axis"]
            if axis in axis_values:
                return None
            selected = evaluate_expression(
                selector.get("value"),
                inputs,
                table_rule=table_rule,
                _depth=_depth + 1,
            )
            if selected is None:
                return None
            axis_values[axis] = selected
        if len(axis_values) != len(expected_axes) or set(axis_values) != set(expected_axes):
            return None
        matches = _matching_table_cells(table_rule, axis_values)
        if len(matches) != 1:
            return None
        return evaluate_expression(
            matches[0].value,
            inputs,
            table_rule=table_rule,
            _depth=_depth + 1,
        )
    if node != "operation":
        return None
    arguments = [
        evaluate_expression(item, inputs, table_rule=table_rule, _depth=_depth + 1)
        for item in expression.get("arguments", [])
    ]
    if not arguments or any(item is None for item in arguments):
        return None
    values = [item for item in arguments if item is not None]
    operator = expression.get("operator")
    if operator == "calendar_add" and len(values) == 2:
        base, duration = values
        if (
            isinstance(base.value, dt.date)
            and not isinstance(base.value, dt.datetime)
            and isinstance(duration.value, Decimal)
            and duration.value == duration.value.to_integral_value()
            and duration.unit
        ):
            calendar_result = _calendar_add(base.value, int(duration.value), duration.unit)
            return Scalar(calendar_result) if calendar_result else None
        return None
    if operator == "elapsed_between" and len(values) == 3:
        start, end, unit = values
        if (
            isinstance(start.value, dt.datetime)
            and isinstance(end.value, dt.datetime)
            and isinstance(unit.value, str)
        ):
            try:
                elapsed_seconds = Decimal(str((end.value - start.value).total_seconds()))
            except (TypeError, InvalidOperation):
                return None
            if elapsed_seconds < 0:
                return None
            divisors = {
                "elapsed_day": Decimal(86400),
                "elapsed_hour": Decimal(3600),
                "elapsed_minute": Decimal(60),
            }
            divisor = divisors.get(unit.value)
            return Scalar(elapsed_seconds / divisor, unit.value) if divisor else None
        if (
            isinstance(start.value, dt.date)
            and not isinstance(start.value, dt.datetime)
            and isinstance(end.value, dt.date)
            and not isinstance(end.value, dt.datetime)
        ):
            elapsed = (end.value - start.value).days
            if elapsed >= 0 and unit.value == "elapsed_day":
                return Scalar(Decimal(elapsed), "elapsed_day")
        return None
    if operator == "round" and len(values) == 3:
        value, scale, mode = values
        if (
            not isinstance(value.value, Decimal)
            or not isinstance(scale.value, Decimal)
            or scale.unit != "count"
            or scale.value != scale.value.to_integral_value()
            or not Decimal(0) <= scale.value <= Decimal(MAX_ROUNDING_SCALE)
            or not isinstance(mode.value, str)
            or mode.value not in ROUNDING_MODES
        ):
            return None
        try:
            numeric_result = value.value.quantize(
                Decimal(1).scaleb(-int(scale.value)),
                rounding=ROUNDING_MODES[mode.value],
            )
        except (ArithmeticError, DivisionByZero, InvalidOperation):
            return None
        return Scalar(numeric_result, value.unit, value.currency)
    numbers: list[Decimal] = []
    for item in values:
        if not isinstance(item.value, Decimal):
            return None
        numbers.append(item.value)
    if not all(_same_dimension(values[0], item) for item in values[1:]) and operator in {
        "add",
        "subtract",
        "min",
        "max",
        "sum",
    }:
        return None
    try:
        if operator in {"add", "sum"}:
            numeric_result = sum(numbers, Decimal(0))
        elif operator == "subtract" and len(numbers) == 2:
            numeric_result = numbers[0] - numbers[1]
        elif operator == "multiply" and len(numbers) == 2:
            if values[0].unit == "ratio":
                result_unit, result_currency = values[1].unit, values[1].currency
            elif values[1].unit == "ratio":
                result_unit, result_currency = values[0].unit, values[0].currency
            else:
                return None
            numeric_result = numbers[0] * numbers[1]
            return Scalar(numeric_result, result_unit, result_currency)
        elif operator == "divide" and len(numbers) == 2:
            if numbers[1] == 0:
                return None
            if values[1].unit == "ratio":
                result_unit, result_currency = values[0].unit, values[0].currency
            elif _same_dimension(values[0], values[1]):
                result_unit, result_currency = "ratio", None
            else:
                return None
            numeric_result = numbers[0] / numbers[1]
            return Scalar(numeric_result, result_unit, result_currency)
        elif operator == "min":
            numeric_result = min(numbers)
        elif operator == "max":
            numeric_result = max(numbers)
        elif operator == "abs" and len(numbers) == 1:
            numeric_result = abs(numbers[0])
        else:
            return None
    except (ArithmeticError, DivisionByZero, InvalidOperation):
        return None
    return Scalar(numeric_result, values[0].unit, values[0].currency)


def _ordered_comparison(left: ScalarValue, right: ScalarValue, operator: str) -> bool | None:
    comparable = (
        (isinstance(left, Decimal) and isinstance(right, Decimal))
        or (isinstance(left, dt.datetime) and isinstance(right, dt.datetime))
        or (
            isinstance(left, dt.date)
            and not isinstance(left, dt.datetime)
            and isinstance(right, dt.date)
            and not isinstance(right, dt.datetime)
        )
        or (isinstance(left, str) and isinstance(right, str))
        or (
            isinstance(left, int)
            and not isinstance(left, bool)
            and isinstance(right, int)
            and not isinstance(right, bool)
        )
    )
    if not comparable:
        return None
    try:
        if operator == "lt":
            return left < right  # type: ignore[operator]
        if operator == "lte":
            return left <= right  # type: ignore[operator]
        if operator == "gt":
            return left > right  # type: ignore[operator]
        if operator == "gte":
            return left >= right  # type: ignore[operator]
    except TypeError:
        return None
    return None


def evaluate_predicate(
    predicate: object,
    inputs: dict[str, object],
    *,
    table_rule: PolicyRule | None = None,
    _depth: int = 0,
) -> Truth:
    if _depth > MAX_EXPRESSION_DEPTH or not isinstance(predicate, dict):
        return Truth.UNKNOWN
    node = predicate.get("node")
    if node == "constant":
        try:
            return Truth(str(predicate.get("value")))
        except ValueError:
            return Truth.UNKNOWN
    if node == "present":
        return Truth.TRUE if str(predicate.get("input_key")) in inputs else Truth.FALSE
    if node == "not":
        result = evaluate_predicate(
            predicate.get("argument"),
            inputs,
            table_rule=table_rule,
            _depth=_depth + 1,
        )
        return {Truth.TRUE: Truth.FALSE, Truth.FALSE: Truth.TRUE}.get(result, Truth.UNKNOWN)
    if node in {"all", "any"}:
        results = [
            evaluate_predicate(
                item,
                inputs,
                table_rule=table_rule,
                _depth=_depth + 1,
            )
            for item in predicate.get("arguments", [])
        ]
        if node == "all":
            if Truth.FALSE in results:
                return Truth.FALSE
            return Truth.UNKNOWN if Truth.UNKNOWN in results else Truth.TRUE
        if Truth.TRUE in results:
            return Truth.TRUE
        return Truth.UNKNOWN if Truth.UNKNOWN in results else Truth.FALSE
    if node == "membership":
        item = evaluate_expression(
            predicate.get("item"), inputs, table_rule=table_rule, _depth=_depth + 1
        )
        members = [
            evaluate_expression(value, inputs, table_rule=table_rule, _depth=_depth + 1)
            for value in predicate.get("members", [])
        ]
        if item is None or any(value is None for value in members):
            return Truth.UNKNOWN
        return (
            Truth.TRUE
            if any(_same_value(item, value) for value in members if value)
            else Truth.FALSE
        )
    if node == "compare":
        left = evaluate_expression(
            predicate.get("left"), inputs, table_rule=table_rule, _depth=_depth + 1
        )
        right = evaluate_expression(
            predicate.get("right"), inputs, table_rule=table_rule, _depth=_depth + 1
        )
        if left is None or right is None or not _same_dimension(left, right):
            return Truth.UNKNOWN
        operator = str(predicate.get("operator"))
        if operator == "eq":
            outcome = _same_value(left, right)
        elif operator == "ne":
            outcome = not _same_value(left, right)
        else:
            compared = _ordered_comparison(left.value, right.value, operator)
            if compared is None:
                return Truth.UNKNOWN
            outcome = compared
        if not isinstance(outcome, bool):
            return Truth.UNKNOWN
        return Truth.TRUE if outcome else Truth.FALSE
    return Truth.UNKNOWN


def _fact_subject_id(fact: CustomerFact) -> uuid.UUID | None:
    statement = getattr(fact, "source_statement", None)
    return getattr(statement, "subject_person_id", None)


def current_inputs(
    facts: list[CustomerFact],
    subject_person_id: uuid.UUID | None = None,
) -> dict[str, object]:
    values: dict[str, object] = {}
    for fact in facts:
        if fact.status in {"retracted", "disputed"}:
            continue
        fact_subject_id = _fact_subject_id(fact)
        if fact_subject_id is not None and fact_subject_id != subject_person_id:
            continue
        existing = values.get(fact.fact_type)
        if existing is not None and existing != fact.value:
            values[fact.fact_type] = {
                "state": "unknown",
                "reason": "Multiple current values require focused clarification.",
            }
        else:
            values[fact.fact_type] = fact.value
    return values


def _age_rule_inputs(values: dict[str, object]) -> dict[str, object]:
    """Expose an explicitly reported age under the policy rule's age input names."""

    result = dict(values)
    age = _typed_value(values.get("age"))
    if age is None or not isinstance(age.value, Decimal) or age.value < 0:
        return result
    if age.unit == "day":
        result["proposed_insured_age_days"] = values["age"]
        result["dependent_child_age_days"] = values["age"]
        if age.value < 365:
            result["dependent_child_completed_age"] = {
                "state": "known",
                "kind": "quantity",
                "value": "0",
                "unit": "year",
            }
    elif age.unit == "year":
        result["dependent_child_completed_age"] = values["age"]
        if age.value >= 1 and age.value == age.value.to_integral_value():
            # Completed years guarantee at least this many elapsed days.
            minimum_days = age.value * 365
            result["proposed_insured_age_days"] = {
                "state": "known",
                "kind": "quantity",
                "value": str(minimum_days),
                "unit": "day",
            }
            result["dependent_child_age_days"] = result["proposed_insured_age_days"]
    return result


def _apply_parent_child_inputs(
    inputs_by_subject: dict[uuid.UUID | None, dict[str, object]],
    intended_subject_ids: tuple[uuid.UUID, ...],
    parent_child_pairs: list[tuple[uuid.UUID, uuid.UUID]],
) -> None:
    """Supply the young-child condition only for an intended, recorded parent-child pair."""

    intended = set(intended_subject_ids)
    for parent_id, child_id in parent_child_pairs:
        if parent_id in intended and child_id in intended:
            inputs_by_subject[child_id]["either_parent_insured_under_policy"] = {
                "state": "known",
                "kind": "boolean",
                "value": True,
            }


def _selected_policy_tenure(requirements: list[CustomerRequirement]) -> object | None:
    values = [
        item.target_value
        for item in requirements
        if item.criterion == "policy_tenure_selection"
        and item.status not in {"disputed", "withdrawn"}
        and item.target_value is not None
    ]
    return values[0] if len(values) == 1 and _typed_value(values[0]) is not None else None


def _money_input(value: object) -> dict[str, object] | None:
    """Normalize a customer-stated INR amount into the rule contract's money dimension."""

    scalar = _typed_value(value)
    if scalar is None or not isinstance(scalar.value, Decimal) or scalar.value < 0:
        return None
    if scalar.unit in {"INR", "money"} and scalar.currency in {None, "INR"}:
        rupees = scalar.value
    elif scalar.unit in {"lakh", "lakhs"} and scalar.currency is None:
        rupees = scalar.value * 100000
    else:
        return None
    return {
        "state": "known",
        "kind": "quantity",
        "value": str(rupees),
        "unit": "money",
        "currency": "INR",
    }


def _room_illustration_inputs(inputs: dict[str, object]) -> dict[str, object]:
    normalized = dict(inputs)
    for key in (
        "eligible_room_rent_limit",
        "room_rent_actually_incurred",
        "total_associated_medical_expenses",
    ):
        if key in inputs and (amount := _money_input(inputs[key])) is not None:
            normalized[key] = amount
    return normalized


def _deductible_configuration_inputs(
    facts: list[CustomerFact], requirements: list[CustomerRequirement]
) -> dict[str, object]:
    deductible = [
        item.target_value
        for item in requirements
        if item.criterion == "deductible" and item.status not in {"disputed", "withdrawn"}
    ]
    sum_insured = [
        item.value
        for item in facts
        if item.fact_type == "sum_insured" and item.status not in {"disputed", "retracted"}
    ]
    if not sum_insured:
        sum_insured = [
            item.target_value
            for item in requirements
            if item.criterion == "sum_insured" and item.status not in {"disputed", "withdrawn"}
        ]
    inputs: dict[str, object] = {}
    if len(deductible) == 1 and (amount := _money_input(deductible[0])) is not None:
        inputs["selected_aggregate_deductible"] = amount
    if len(sum_insured) == 1 and (amount := _money_input(sum_insured[0])) is not None:
        inputs["selected_base_sum_insured"] = amount
    return inputs


def _childbirth_request(requirement: CustomerRequirement) -> bool:
    if requirement.criterion != "maternity" or _typed_value(requirement.target_value) != Scalar(
        True
    ):
        return False
    statement = getattr(requirement, "source_statement", None)
    message = getattr(statement, "source_message", None)
    text = getattr(message, "content", "")
    return "childbirth" in text.casefold() and "ectopic" not in text.casefold()


def _childbirth_rule_inputs(requirements: list[CustomerRequirement]) -> dict[str, object]:
    if not any(_childbirth_request(item) for item in requirements):
        return {}
    return {
        "expense_traceable_to_childbirth": {"state": "known", "kind": "boolean", "value": True},
        "condition_is_ectopic_pregnancy": {"state": "known", "kind": "boolean", "value": False},
    }


def _ayush_rule_inputs(requirements: list[CustomerRequirement]) -> dict[str, object]:
    texts = [
        getattr(
            getattr(getattr(item, "source_statement", None), "source_message", None), "content", ""
        )
        for item in requirements
        if item.criterion == "specific_treatment"
    ]
    if len(texts) != 1 or "ayurveda" not in texts[0].casefold():
        return {}
    text = texts[0].casefold()
    inputs: dict[str, object] = {
        "ayush_system": {
            "state": "known",
            "kind": "code",
            "namespace": "ayush_system",
            "value": "ayurveda",
        }
    }
    for key, present in (
        (
            "treatment_at_eligible_ayush_hospital_or_healthcare_facility",
            any(
                phrase in text
                for phrase in (
                    "eligible facility",
                    "eligible hospital",
                    "eligible healthcare facility",
                    "eligible ayush hospital",
                    "eligible ayush healthcare facility",
                )
            ),
        ),
        ("ayush_practitioner_has_valid_practicing_license", "licensed practitioner" in text),
        ("treatment_taken_in_india", " in india" in text),
        ("claim_admissible_under_hospitalization_expenses", "admissible claim" in text),
    ):
        if present:
            inputs[key] = {"state": "known", "kind": "boolean", "value": True}
    return inputs


def _childbirth_exclusion_match(
    requirement: CustomerRequirement,
    evaluated_rules: tuple[RuleResult, ...],
    subject_person_id: uuid.UUID | None,
) -> tuple[str, tuple[str, ...], None] | None:
    if not _childbirth_request(requirement):
        return None
    for result in evaluated_rules:
        if not result.evidence_complete or not any(
            subject.subject_person_id == subject_person_id and subject.applies == Truth.TRUE
            for subject in result.subject_results
        ):
            continue
        if any(
            isinstance(effect, dict)
            and effect.get("kind") == "exclusion"
            and effect.get("target_key") == "childbirth_expense_exclusion"
            for effect in result.rule.body.get("effects", [])
        ):
            return "does_not_meet", (str(result.rule.id),), None
    return None


def _deductible_selection_match(
    requirement: CustomerRequirement,
    evaluated_rules: tuple[RuleResult, ...],
    subject_person_id: uuid.UUID | None,
) -> tuple[str, tuple[str, ...], None] | None:
    if requirement.criterion != "deductible":
        return None
    for result in evaluated_rules:
        if not result.evidence_complete or not any(
            subject.subject_person_id == subject_person_id and subject.applies == Truth.TRUE
            for subject in result.subject_results
        ):
            continue
        if any(
            isinstance(effect, dict)
            and effect.get("kind") == "eligibility"
            and effect.get("target_key") == "aggregate_deductible_selection"
            and effect.get("decision") == "ineligible"
            for effect in result.rule.body.get("effects", [])
        ):
            return "does_not_meet", (str(result.rule.id),), None
    return None


def _child_entry_unverified(
    intended_subject_ids: tuple[uuid.UUID, ...],
    inputs_by_subject: dict[uuid.UUID | None, dict[str, object]],
    evaluated_rules: tuple[RuleResult, ...],
) -> bool:
    """A child needs affirmative, verified entry evidence before a product is eligible."""

    for subject_id in intended_subject_ids:
        age = _typed_value(inputs_by_subject[subject_id].get("age"))
        if age is None or not isinstance(age.value, Decimal):
            continue
        if not (
            (age.unit == "year" and age.value < 18) or (age.unit == "day" and age.value < 18 * 365)
        ):
            continue
        has_entry_rule = any(
            result.evidence_complete
            and any(
                subject.subject_person_id == subject_id and subject.applies == Truth.TRUE
                for subject in result.subject_results
            )
            and any(
                isinstance(effect, dict)
                and effect.get("kind") == "eligibility"
                and effect.get("decision") == "eligible"
                and effect.get("target_key") in {"young_dependent_child_entry", "minimum_entry_age"}
                for effect in result.rule.body.get("effects", [])
            )
            for result in evaluated_rules
        )
        if not has_entry_rule:
            return True
    return False


def _known_boolean(value: object) -> bool | None:
    if not isinstance(value, dict) or value.get("kind") != "boolean":
        return None
    raw = value.get("value")
    return raw if isinstance(raw, bool) else None


def _evaluation_subject_ids(
    facts: list[CustomerFact], requirements: list[CustomerRequirement]
) -> tuple[tuple[uuid.UUID, ...], tuple[uuid.UUID | None, ...]]:
    intended = {
        subject_id
        for fact in facts
        if fact.fact_type == "intended_insured"
        and _known_boolean(fact.value) is True
        and (subject_id := _fact_subject_id(fact)) is not None
    }
    requirement_subjects = {
        requirement.subject_person_id
        for requirement in requirements
        if requirement.subject_person_id is not None
    }
    all_subjects = tuple(sorted(intended | requirement_subjects, key=str))
    return tuple(sorted(intended, key=str)), all_subjects or (None,)


def _aggregate_truth(values: tuple[Truth, ...]) -> Truth:
    if Truth.TRUE in values:
        return Truth.TRUE
    if values and all(value == Truth.FALSE for value in values):
        return Truth.FALSE
    return Truth.UNKNOWN


def _effect_matches_requirement(
    rule: PolicyRule,
    effect: dict[str, object],
    requirement: CustomerRequirement,
) -> bool:
    return (
        str(effect.get("target_key", "")) == requirement.criterion
        or rule.rule_type == requirement.criterion
        or (
            requirement.criterion == "specific_treatment"
            and effect.get("target_key") == "ayush_treatment_cover"
            and "ayurveda" in str(requirement.target_value).casefold()
        )
    )


def _no_separate_room_icu_match(
    requirement: CustomerRequirement,
    evaluated_rules: tuple[RuleResult, ...],
    subject_person_id: uuid.UUID | None,
) -> tuple[str, tuple[str, ...], None] | None:
    target = requirement.target_value
    if requirement.criterion != "room_category" or not isinstance(target, dict):
        return None
    phrase = str(target.get("value", "")).casefold()
    if not (
        target.get("kind") == "text"
        and (
            "no separate" in phrase or (requirement.operator == "excludes" and "separate" in phrase)
        )
        and "room" in phrase
        and "icu" in phrase
        and "limit" in phrase
    ):
        return None
    expected = {"hospitalization_room_rent_limit", "hospitalization_icu_charge_limit"}
    found: dict[str, str] = {}
    ids: list[str] = []
    for result in evaluated_rules:
        applies = next(
            (
                item.applies
                for item in result.subject_results
                if item.subject_person_id == subject_person_id
            ),
            Truth.UNKNOWN,
        )
        if applies != Truth.TRUE or not result.evidence_complete:
            continue
        for effect in result.rule.body.get("effects", []):
            if not isinstance(effect, dict) or effect.get("target_key") not in expected:
                continue
            amount = effect.get("amount")
            if not isinstance(amount, dict) or amount.get("node") != "literal":
                continue
            value = amount.get("value")
            if not isinstance(value, dict):
                continue
            state = value.get("state")
            if state == "unlimited":
                found[str(effect["target_key"])] = "meets"
            elif state == "finite":
                found[str(effect["target_key"])] = "does_not_meet"
            else:
                continue
            ids.append(str(result.rule.id))
    if "does_not_meet" in found.values():
        outcome = "does_not_meet"
    elif expected.issubset(found):
        outcome = "meets"
    elif found:
        outcome = "partly_meets"
    else:
        outcome = "unknown"
    return outcome, tuple(dict.fromkeys(ids)), None


def _subject_requirement_result(
    requirement: CustomerRequirement,
    evaluated_rules: tuple[RuleResult, ...],
    subject_person_id: uuid.UUID | None,
    inputs: dict[str, object],
) -> tuple[str, tuple[str, ...], dict[str, object] | None]:
    room_icu = _no_separate_room_icu_match(requirement, evaluated_rules, subject_person_id)
    if room_icu is not None:
        return room_icu
    childbirth = _childbirth_exclusion_match(requirement, evaluated_rules, subject_person_id)
    if childbirth is not None:
        return childbirth
    deductible = _deductible_selection_match(requirement, evaluated_rules, subject_person_id)
    if deductible is not None:
        return deductible
    outcomes: list[str] = []
    rule_ids: list[str] = []
    uncertain_rule_ids: list[str] = []
    comparison_values: list[dict[str, object] | None] = []
    for rule_result in evaluated_rules:
        subject_state = next(
            (
                result.applies
                for result in rule_result.subject_results
                if result.subject_person_id == subject_person_id
            ),
            Truth.UNKNOWN,
        )
        effects = rule_result.rule.body.get("effects", [])
        for effect in effects if isinstance(effects, list) else []:
            if not isinstance(effect, dict) or not _effect_matches_requirement(
                rule_result.rule, effect, requirement
            ):
                continue
            rule_id = str(rule_result.rule.id)
            if subject_state == Truth.UNKNOWN:
                uncertain_rule_ids.append(rule_id)
            elif subject_state == Truth.TRUE:
                outcome, comparison_value = _compare_requirement(
                    requirement, effect, inputs, rule_result.rule
                )
                outcomes.append(outcome)
                comparison_values.append(comparison_value)
                rule_ids.append(rule_id)
    identifiers = tuple(dict.fromkeys(rule_ids + uncertain_rule_ids))
    comparison_value = _aggregate_comparison_value(requirement.operator, comparison_values)
    if "does_not_meet" in outcomes:
        return "does_not_meet", identifiers, comparison_value
    if outcomes and all(item == "meets" for item in outcomes) and not uncertain_rule_ids:
        return "meets", identifiers, comparison_value
    if outcomes and all(item == "unknown" for item in outcomes) and not uncertain_rule_ids:
        return "unknown", identifiers, comparison_value
    if outcomes:
        return "partly_meets", identifiers, comparison_value
    return "unknown", identifiers, comparison_value


def _effect_value(effect: dict[str, object]) -> object | None:
    if "amount" in effect:
        return effect["amount"]
    if "duration" in effect:
        duration = effect["duration"]
        return {"kind": "duration", "value": duration}
    if effect.get("kind") == "definition" and "value" in effect:
        return effect["value"]
    if effect.get("kind") == "exception" and "replacement" in effect:
        return effect["replacement"]
    if effect.get("kind") == "right":
        return {"kind": "boolean", "value": True}
    if effect.get("kind") == "eligibility":
        return {"kind": "code", "namespace": "eligibility", "value": effect.get("decision")}
    return None


def _compare_requirement(
    requirement: CustomerRequirement,
    effect: dict[str, object],
    inputs: dict[str, object],
    rule: PolicyRule,
) -> tuple[str, dict[str, object] | None]:
    if effect.get("kind") == "eligibility":
        decision = effect.get("decision")
        if decision == "ineligible":
            return "does_not_meet", None
        return ("meets" if decision == "eligible" else "unknown"), None
    if effect.get("kind") == "exclusion":
        return "does_not_meet", None
    target = _typed_value(requirement.target_value) if requirement.target_value else None
    raw_effect = _effect_value(effect)
    actual = (
        evaluate_expression(raw_effect, inputs, table_rule=rule)
        if isinstance(raw_effect, dict) and raw_effect.get("node")
        else _typed_value(raw_effect)
    )
    comparison_value = _serialize_comparison_value(actual)
    if requirement.operator in {"is_available", "is_not_available"}:
        available = actual is not None and actual.value is not False
        result = available if requirement.operator == "is_available" else not available
        return ("meets" if result else "does_not_meet"), comparison_value
    if target is None or actual is None or not _same_dimension(actual, target):
        return "unknown", comparison_value
    operator = requirement.operator
    if operator == "equals":
        outcome = _same_value(actual, target)
    elif operator == "not_equals":
        outcome = not _same_value(actual, target)
    elif operator in {
        "less_than_or_equal",
        "greater_than_or_equal",
        "minimize",
        "maximize",
    }:
        comparison_operator = "lte" if operator in {"less_than_or_equal", "minimize"} else "gte"
        compared = _ordered_comparison(actual.value, target.value, comparison_operator)
        if compared is None:
            return "unknown", comparison_value
        outcome = compared
    elif operator in {"includes", "excludes"}:
        if not isinstance(actual.value, str) or not isinstance(target.value, str):
            return "unknown", comparison_value
        contains = target.value in actual.value
        outcome = contains if operator == "includes" else not contains
    else:
        return "unknown", comparison_value
    return ("meets" if outcome else "does_not_meet"), comparison_value


def evaluate_release(
    release: KnowledgeRelease,
    facts: list[CustomerFact],
    requirements: list[CustomerRequirement],
) -> list[PolicyComparisonResult]:
    rules = list(
        PolicyRule.objects.filter(
            id__in=KnowledgeReleaseRule.objects.filter(knowledge_release=release).values(
                "policy_rule_id"
            )
        )
        .select_related("policy_version__product__insurer")
        .order_by("policy_version_id", "rule_key", "id")
    )
    evidence_rows = list(
        PolicyRuleEvidence.objects.filter(
            policy_rule_id__in=[rule.id for rule in rules]
        ).select_related("evidence_span")
    )
    required_evidence: dict[uuid.UUID, list[PolicyRuleEvidence]] = {rule.id: [] for rule in rules}
    for row in evidence_rows:
        if row.is_required:
            required_evidence[row.policy_rule_id].append(row)
    all_evidence: dict[uuid.UUID, list[PolicyRuleEvidence]] = {rule.id: [] for rule in rules}
    for row in evidence_rows:
        all_evidence[row.policy_rule_id].append(row)
    verified_states = {"text_verified", "visually_verified", "reviewed"}
    evidence_complete: dict[uuid.UUID, bool] = {
        rule_id: bool(rows)
        and all(row.evidence_span.verification in verified_states for row in rows)
        for rule_id, rows in required_evidence.items()
    }
    rules_by_version: dict[uuid.UUID, list[PolicyRule]] = {}
    for rule in rules:
        rules_by_version.setdefault(rule.policy_version_id, []).append(rule)
    variants: list[ProductVariant] = []
    seen_products: set[uuid.UUID] = set()
    for version_id in sorted(rules_by_version, key=str):
        available = (
            ProductVariant.objects.filter(policy_version_id=version_id)
            .select_related("policy_version__product__insurer")
            .order_by("created_at")
        )
        variant = available.first()
        if variant and variant.policy_version.product_id not in seen_products:
            variants.append(variant)
            seen_products.add(variant.policy_version.product_id)
    expected_count = comparison_product_count(release)
    if len(variants) != expected_count:
        raise ValueError(
            f"The release does not resolve to exactly {expected_count} product variants."
        )
    intended_subject_ids, evaluation_subject_ids = _evaluation_subject_ids(facts, requirements)
    inputs_by_subject = {
        subject_id: _room_illustration_inputs(_age_rule_inputs(current_inputs(facts, subject_id)))
        for subject_id in evaluation_subject_ids
    }
    relationships = list(
        PersonRelationship.objects.filter(
            from_person_id__in=intended_subject_ids,
            to_person_id__in=intended_subject_ids,
            relationship_type="child",
            valid_from__isnull=True,
            valid_to__isnull=True,
        ).values_list("from_person_id", "to_person_id")
    )
    _apply_parent_child_inputs(inputs_by_subject, intended_subject_ids, relationships)
    selected_tenure = _selected_policy_tenure(requirements)
    configuration_inputs = _deductible_configuration_inputs(facts, requirements)
    configuration_inputs.update(_childbirth_rule_inputs(requirements))
    configuration_inputs.update(_ayush_rule_inputs(requirements))
    if selected_tenure is not None:
        for inputs in inputs_by_subject.values():
            inputs["selected_policy_tenure"] = selected_tenure
    for inputs in inputs_by_subject.values():
        inputs.update(configuration_inputs)
    products: list[PolicyComparisonResult] = []
    ordered_variants = sorted(
        variants,
        key=lambda item: (
            item.policy_version.product.insurer.name.casefold(),
            item.policy_version.product.name.casefold(),
            (item.policy_version.uin or "").casefold(),
            str(item.id),
        ),
    )
    for variant in ordered_variants:
        variant_rules = rules_by_version[variant.policy_version_id]
        evaluated_rule_values: list[RuleResult] = []
        for rule in variant_rules:
            subject_results = tuple(
                SubjectRuleResult(
                    subject_id,
                    evaluate_predicate(
                        rule.body.get("applies_when"),
                        inputs_by_subject[subject_id],
                        table_rule=rule,
                    ),
                )
                for subject_id in evaluation_subject_ids
            )
            evaluated_rule_values.append(
                RuleResult(
                    rule,
                    _aggregate_truth(tuple(result.applies for result in subject_results)),
                    evidence_complete[rule.id],
                    tuple(
                        sorted(
                            (row.evidence_span_id for row in all_evidence[rule.id]),
                            key=str,
                        )
                    ),
                    subject_results,
                )
            )
        evaluated_rules = tuple(evaluated_rule_values)
        matches: list[RequirementResult] = []
        for requirement in requirements:
            if requirement.scope == "person":
                target_subjects: tuple[uuid.UUID | None, ...] = (
                    (requirement.subject_person_id,)
                    if requirement.subject_person_id is not None
                    else ()
                )
            elif requirement.scope == "all_intended_insured":
                target_subjects = intended_subject_ids
            else:
                target_subjects = evaluation_subject_ids
            subject_matches = [
                _subject_requirement_result(
                    requirement,
                    evaluated_rules,
                    subject_id,
                    inputs_by_subject[subject_id],
                )
                for subject_id in target_subjects
            ]
            subject_outcomes = [value[0] for value in subject_matches]
            if "does_not_meet" in subject_outcomes:
                outcome = "does_not_meet"
            elif subject_outcomes and all(value == "meets" for value in subject_outcomes):
                outcome = "meets"
            elif subject_outcomes and all(value == "unknown" for value in subject_outcomes):
                outcome = "unknown"
            elif subject_outcomes:
                outcome = "partly_meets"
            else:
                outcome = "unknown"
            rule_ids = tuple(
                dict.fromkeys(
                    rule_id
                    for _subject_outcome, ids, _comparison_value in subject_matches
                    for rule_id in ids
                )
            )
            comparison_value = _aggregate_comparison_value(
                requirement.operator, [value[2] for value in subject_matches]
            )
            matches.append(RequirementResult(requirement, outcome, comparison_value, rule_ids))
        products.append(
            PolicyComparisonResult(
                variant=variant,
                matches=tuple(matches),
                rules=evaluated_rules,
            )
        )
    return products
