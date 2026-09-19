"""Static publication checks for closed ``RuleV1`` programs.

JSON Schema closes the wire shape.  These checks close the executable meaning:
input references must resolve, operations must be dimensionally valid, scope-only
fields must appear in the right scope, and executable rule dependencies must form
an acyclic graph.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

MAX_RULE_AST_DEPTH = 32
MAX_RULE_AST_NODES = 10_000

QUANTITY_UNITS = frozenset(
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
DURATION_UNITS = frozenset(
    {"calendar_month", "calendar_year", "elapsed_day", "elapsed_hour", "elapsed_minute"}
)
INPUT_VALUE_KINDS = frozenset(
    {"quantity", "boolean", "text", "code", "date", "instant", "duration", "reference"}
)
ROUNDING_CODES = frozenset({"half_up", "half_even", "floor", "ceiling"})
EXACT_OPERATION_ARITIES = {
    "subtract": 2,
    "multiply": 2,
    "divide": 2,
    "calendar_add": 2,
    "abs": 1,
    "round": 3,
    "elapsed_between": 3,
}
VARIADIC_OPERATIONS = frozenset({"add", "min", "max", "sum"})


@dataclass(frozen=True)
class _ValueType:
    kind: str
    unit: str | None = None
    currency: str | None = None
    literal_value: str | None = None


_INVALID = _ValueType("invalid")


def semantic_contract_summary() -> dict[str, object]:
    """Return the pinned limits and vocabularies included in extraction prompts."""

    return {
        "max_ast_depth": MAX_RULE_AST_DEPTH,
        "max_ast_nodes_per_rule": MAX_RULE_AST_NODES,
        "input_value_kinds": sorted(INPUT_VALUE_KINDS),
        "quantity_units": sorted(QUANTITY_UNITS),
        "duration_units": sorted(DURATION_UNITS),
        "boolean_unit": "truth",
        "text_unit": "text",
        "date_unit": "date",
        "instant_unit": "instant",
        "rounding_codes": sorted(ROUNDING_CODES),
        "reference_rule": "Every input and rule key must be declared in the same pinned rule set.",
    }


def _compatible(left: _ValueType, right: _ValueType) -> bool:
    if _INVALID in {left, right}:
        return False
    if left.kind != right.kind:
        return False
    if left.unit is not None and right.unit is not None and left.unit != right.unit:
        return False
    if (
        left.kind == "quantity"
        and (left.unit == "money" or right.unit == "money")
        and left.currency is not None
        and right.currency is not None
        and left.currency != right.currency
    ):
        return False
    return True


def _merged(left: _ValueType, right: _ValueType) -> _ValueType:
    if not _compatible(left, right):
        return _INVALID
    return _ValueType(
        left.kind,
        left.unit or right.unit,
        left.currency or right.currency,
        left.literal_value if left.literal_value == right.literal_value else None,
    )


def _is_numeric(value_type: _ValueType) -> bool:
    return value_type.kind in {"quantity", "duration"}


def _literal_type(value: object) -> _ValueType:
    if not isinstance(value, dict):
        return _INVALID
    state = value.get("state")
    if state == "finite":
        unit = value.get("unit")
        if not isinstance(unit, str):
            return _INVALID
        currency = value.get("currency")
        return _ValueType(
            "quantity",
            unit,
            currency if isinstance(currency, str) else None,
        )
    if state == "unlimited":
        unit = value.get("unit")
        return _ValueType("quantity", unit if isinstance(unit, str) else None)
    if state == "unknown":
        unit = value.get("expected_unit")
        return _ValueType("quantity", unit if isinstance(unit, str) else None)
    if state == "not_applicable":
        return _ValueType("quantity")
    kind = value.get("kind")
    if kind == "duration":
        duration = value.get("value")
        if not isinstance(duration, dict):
            return _INVALID
        unit = duration.get("unit")
        return _ValueType("duration", unit if isinstance(unit, str) else None)
    if kind == "code":
        namespace = value.get("namespace")
        literal = value.get("value")
        return _ValueType(
            "code",
            namespace if isinstance(namespace, str) else None,
            literal_value=literal if isinstance(literal, str) else None,
        )
    if kind == "reference":
        entity = value.get("entity")
        return _ValueType("reference", entity if isinstance(entity, str) else None)
    if kind in {"boolean", "text", "date", "instant"}:
        return _ValueType(str(kind))
    return _INVALID


def _input_type(value_kind: str, unit: str) -> _ValueType:
    if value_kind == "quantity":
        return _ValueType("quantity", unit)
    if value_kind == "duration":
        return _ValueType("duration", None if unit == "duration" else unit)
    # Reference declarations intentionally use a generic identity unit while a
    # concrete literal carries its entity name (for example PolicyVersion).
    if value_kind == "reference":
        return _ValueType("reference")
    if value_kind == "code":
        return _ValueType("code", unit)
    return _ValueType(value_kind)


def _table_result_type(unit: object) -> _ValueType:
    if not isinstance(unit, str):
        return _INVALID
    if unit in QUANTITY_UNITS:
        return _ValueType("quantity", unit)
    if unit in DURATION_UNITS:
        return _ValueType("duration", unit)
    if unit == "truth":
        return _ValueType("boolean")
    if unit in {"date", "instant", "text"}:
        return _ValueType(unit)
    return _ValueType("code", unit)


class _RuleValidator:
    def __init__(self, body: Mapping[str, Any]) -> None:
        self.body = body
        self.problems: list[str] = []
        self._problem_set: set[str] = set()
        self.node_count = 0
        self.inputs = self._read_inputs(body.get("inputs"))
        self.table_axes, self.table_key, self.table_result = self._read_table(body.get("table"))

    def problem(self, description: str) -> None:
        if description not in self._problem_set:
            self._problem_set.add(description)
            self.problems.append(description)

    def _read_inputs(self, raw_inputs: object) -> dict[str, _ValueType]:
        result: dict[str, _ValueType] = {}
        if not isinstance(raw_inputs, list):
            self.problem("inputs must be an array")
            return result
        for index, declaration in enumerate(raw_inputs):
            if not isinstance(declaration, dict):
                self.problem(f"inputs[{index}] must be an object")
                continue
            key = declaration.get("key")
            value_kind = declaration.get("value_kind")
            unit = declaration.get("unit")
            if (
                not isinstance(key, str)
                or not isinstance(value_kind, str)
                or not isinstance(unit, str)
            ):
                self.problem(f"inputs[{index}] has an invalid key, value_kind, or unit")
                continue
            if key in result:
                self.problem(f"inputs contains duplicate key: {key}")
                continue
            if value_kind not in INPUT_VALUE_KINDS:
                self.problem(f"inputs[{index}] uses unregistered value_kind: {value_kind}")
                result[key] = _INVALID
                continue
            if value_kind == "quantity" and unit not in QUANTITY_UNITS:
                self.problem(f"inputs[{index}] uses unregistered quantity unit: {unit}")
            elif value_kind == "duration" and unit not in DURATION_UNITS | {"duration"}:
                self.problem(f"inputs[{index}] uses unregistered duration unit: {unit}")
            elif value_kind == "boolean" and unit != "truth":
                self.problem(f"inputs[{index}] boolean unit must be truth")
            elif value_kind == "text" and unit != "text":
                self.problem(f"inputs[{index}] text unit must be text")
            elif value_kind == "date" and unit != "date":
                self.problem(f"inputs[{index}] date unit must be date")
            elif value_kind == "instant" and unit != "instant":
                self.problem(f"inputs[{index}] instant unit must be instant")
            result[key] = _input_type(value_kind, unit)
        return result

    def _read_table(
        self, raw_table: object
    ) -> tuple[dict[str, _ValueType], str | None, _ValueType | None]:
        if raw_table is None:
            return {}, None, None
        if not isinstance(raw_table, dict):
            self.problem("table must be an object or null")
            return {}, None, None
        raw_key = raw_table.get("table_key")
        table_key = raw_key if isinstance(raw_key, str) else None
        result_type = _table_result_type(raw_table.get("result_unit"))
        axes: dict[str, _ValueType] = {}
        raw_axes = raw_table.get("axes")
        if not isinstance(raw_axes, list):
            self.problem("table.axes must be an array")
        else:
            for index, axis in enumerate(raw_axes):
                if not isinstance(axis, dict):
                    self.problem(f"table.axes[{index}] must be an object")
                    continue
                key = axis.get("key")
                value_kind = axis.get("value_kind")
                unit = axis.get("unit")
                if not isinstance(key, str) or not isinstance(unit, str):
                    self.problem(f"table.axes[{index}] has an invalid key or unit")
                    continue
                if key in axes:
                    self.problem(f"table.axes contains duplicate key: {key}")
                    continue
                if value_kind == "quantity":
                    if unit not in QUANTITY_UNITS:
                        self.problem(f"table.axes[{index}] uses unregistered quantity unit: {unit}")
                    axes[key] = _ValueType("quantity", unit)
                elif value_kind == "code":
                    axes[key] = _ValueType("code", unit)
                else:
                    self.problem(f"table.axes[{index}] uses unsupported value_kind: {value_kind}")
                    axes[key] = _INVALID
        scope = raw_table.get("scope")
        self.scope(scope, "table.scope")
        return axes, table_key, result_type

    def enter_node(self, path: str, depth: int) -> bool:
        self.node_count += 1
        if self.node_count > MAX_RULE_AST_NODES:
            self.problem(f"AST node count exceeds {MAX_RULE_AST_NODES}")
        if depth > MAX_RULE_AST_DEPTH:
            self.problem(f"{path}: AST depth exceeds {MAX_RULE_AST_DEPTH}")
            return False
        return True

    def input_reference(self, key: object, path: str) -> _ValueType:
        if not isinstance(key, str) or key not in self.inputs:
            rendered = key if isinstance(key, str) else "<invalid>"
            self.problem(f"{path} references undeclared input: {rendered}")
            return _INVALID
        return self.inputs[key]

    def expression(self, raw: object, path: str, depth: int = 0) -> _ValueType:
        if not isinstance(raw, dict):
            self.problem(f"{path}: expression must be an object")
            return _INVALID
        if not self.enter_node(path, depth):
            return _INVALID
        node = raw.get("node")
        if node == "literal":
            result = _literal_type(raw.get("value"))
            if result == _INVALID:
                self.problem(f"{path}: literal has no supported static type")
            return result
        if node == "input":
            return self.input_reference(raw.get("key"), path)
        if node == "conditional":
            self.predicate(raw.get("when"), f"{path}.when", depth + 1)
            then_type = self.expression(raw.get("then"), f"{path}.then", depth + 1)
            otherwise_type = self.expression(raw.get("otherwise"), f"{path}.otherwise", depth + 1)
            if _INVALID not in {then_type, otherwise_type} and not _compatible(
                then_type, otherwise_type
            ):
                self.problem(f"{path}: conditional branches require compatible dimensions")
                return _INVALID
            return _merged(then_type, otherwise_type)
        if node == "table_lookup":
            return self._table_lookup(raw, path, depth)
        if node != "operation":
            self.problem(f"{path}: unsupported expression node: {node}")
            return _INVALID
        return self._operation(raw, path, depth)

    def _table_lookup(self, raw: Mapping[str, Any], path: str, depth: int) -> _ValueType:
        if self.table_key is None or raw.get("table_key") != self.table_key:
            self.problem(f"{path}: table_key does not resolve to body.table")
        selectors = raw.get("selectors")
        if not isinstance(selectors, list):
            self.problem(f"{path}.selectors must be an array")
            return _INVALID
        seen: set[str] = set()
        for index, selector in enumerate(selectors):
            selector_path = f"{path}.selectors[{index}]"
            if not isinstance(selector, dict) or not isinstance(selector.get("axis"), str):
                self.problem(f"{selector_path} has no valid axis")
                continue
            axis = selector["axis"]
            if axis in seen:
                self.problem(f"{path}.selectors repeats axis: {axis}")
            seen.add(axis)
            selected_type = self.expression(
                selector.get("value"), f"{selector_path}.value", depth + 1
            )
            expected_type = self.table_axes.get(axis)
            if expected_type is None:
                self.problem(f"{selector_path} references undeclared axis: {axis}")
            elif _INVALID not in {selected_type, expected_type} and not _compatible(
                selected_type, expected_type
            ):
                self.problem(f"{selector_path}.value has the wrong axis dimension")
        if seen != set(self.table_axes):
            self.problem(f"{path}.selectors must supply every table axis exactly once")
        return self.table_result or _INVALID

    def _operation(self, raw: Mapping[str, Any], path: str, depth: int) -> _ValueType:
        operator = raw.get("operator")
        raw_arguments = raw.get("arguments")
        if not isinstance(operator, str) or not isinstance(raw_arguments, list):
            self.problem(f"{path}: operation has an invalid operator or arguments")
            return _INVALID
        expected_arity = EXACT_OPERATION_ARITIES.get(operator)
        if expected_arity is not None and len(raw_arguments) != expected_arity:
            self.problem(f"{path}: {operator} requires exactly {expected_arity} arguments")
        elif operator in VARIADIC_OPERATIONS and not raw_arguments:
            self.problem(f"{path}: {operator} requires at least 1 argument")
        elif expected_arity is None and operator not in VARIADIC_OPERATIONS:
            self.problem(f"{path}: unsupported operator: {operator}")
        arguments = [
            self.expression(value, f"{path}.arguments[{index}]", depth + 1)
            for index, value in enumerate(raw_arguments)
        ]
        if expected_arity is not None and len(arguments) != expected_arity:
            return _INVALID
        if operator in VARIADIC_OPERATIONS:
            if not arguments:
                return _INVALID
            result = arguments[0]
            for argument in arguments[1:]:
                if _INVALID not in {result, argument} and not _compatible(result, argument):
                    self.problem(f"{path}: {operator} requires compatible dimensions")
                    return _INVALID
                result = _merged(result, argument)
            if result != _INVALID and not _is_numeric(result):
                self.problem(f"{path}: {operator} requires numeric arguments")
                return _INVALID
            return result
        if operator in {"subtract", "abs"}:
            if not arguments or any(value == _INVALID for value in arguments):
                return _INVALID
            if not all(_is_numeric(value) for value in arguments):
                self.problem(f"{path}: {operator} requires numeric arguments")
                return _INVALID
            if operator == "subtract" and not _compatible(arguments[0], arguments[1]):
                self.problem(f"{path}: subtract requires compatible dimensions")
                return _INVALID
            return arguments[0]
        if operator == "multiply":
            if any(value == _INVALID for value in arguments):
                return _INVALID
            left, right = arguments
            if left.kind == "quantity" and left.unit == "ratio" and _is_numeric(right):
                return right
            if right.kind == "quantity" and right.unit == "ratio" and _is_numeric(left):
                return left
            self.problem(f"{path}: multiply requires exactly one dimensionless ratio")
            return _INVALID
        if operator == "divide":
            if any(value == _INVALID for value in arguments):
                return _INVALID
            left, right = arguments
            if not _is_numeric(left) or not _is_numeric(right):
                self.problem(f"{path}: divide requires numeric arguments")
                return _INVALID
            if right.kind == "quantity" and right.unit == "ratio":
                return left
            if _compatible(left, right):
                return _ValueType("quantity", "ratio")
            self.problem(f"{path}: divide requires a ratio divisor or compatible dimensions")
            return _INVALID
        if operator == "round":
            if any(value == _INVALID for value in arguments):
                return _INVALID
            value, scale, mode = arguments
            if not _is_numeric(value):
                self.problem(f"{path}: round value must be numeric")
            if scale.kind != "quantity" or scale.unit != "count":
                self.problem(f"{path}: round scale must use the count unit")
            if mode.kind != "code" or mode.unit not in {None, "rounding"}:
                self.problem(f"{path}: round mode must use the rounding code namespace")
            if mode.literal_value is not None and mode.literal_value not in ROUNDING_CODES:
                self.problem(f"{path}: round mode is not executable: {mode.literal_value}")
            return value if _is_numeric(value) else _INVALID
        if operator == "calendar_add":
            if any(value == _INVALID for value in arguments):
                return _INVALID
            base, duration = arguments
            if base.kind != "date":
                self.problem(f"{path}: calendar_add base must be a date")
            if duration.kind != "duration" or duration.unit not in {
                None,
                "calendar_month",
                "calendar_year",
                "elapsed_day",
            }:
                self.problem(f"{path}: calendar_add duration uses an unsupported unit")
            return _ValueType("date")
        if operator == "elapsed_between":
            if any(value == _INVALID for value in arguments):
                return _INVALID
            start, end, unit = arguments
            if start.kind not in {"date", "instant"} or start.kind != end.kind:
                self.problem(f"{path}: elapsed_between endpoints must share a temporal kind")
            if unit.kind != "code" or unit.unit not in {None, "duration"}:
                self.problem(f"{path}: elapsed_between unit must use the duration code namespace")
            allowed = {"elapsed_day", "elapsed_hour", "elapsed_minute"}
            if unit.literal_value is not None and unit.literal_value not in allowed:
                self.problem(f"{path}: elapsed_between uses an unsupported elapsed unit")
            if start.kind == "date" and unit.literal_value not in {None, "elapsed_day"}:
                self.problem(f"{path}: date endpoints only support elapsed_day")
            return _ValueType("duration", unit.literal_value)
        return _INVALID

    def predicate(self, raw: object, path: str, depth: int = 0) -> None:
        if not isinstance(raw, dict):
            self.problem(f"{path}: predicate must be an object")
            return
        if not self.enter_node(path, depth):
            return
        node = raw.get("node")
        if node == "constant":
            return
        if node == "present":
            self.input_reference(raw.get("input_key"), path)
            return
        if node == "not":
            self.predicate(raw.get("argument"), f"{path}.argument", depth + 1)
            return
        if node in {"all", "any"}:
            arguments = raw.get("arguments")
            if not isinstance(arguments, list) or not arguments:
                self.problem(f"{path}: {node} requires at least 1 predicate")
                return
            for index, argument in enumerate(arguments):
                self.predicate(argument, f"{path}.arguments[{index}]", depth + 1)
            return
        if node == "compare":
            left = self.expression(raw.get("left"), f"{path}.left", depth + 1)
            right = self.expression(raw.get("right"), f"{path}.right", depth + 1)
            if _INVALID not in {left, right} and not _compatible(left, right):
                self.problem(f"{path}: comparison requires compatible dimensions")
            if raw.get("operator") in {"lt", "lte", "gt", "gte"} and left.kind not in {
                "quantity",
                "duration",
                "date",
                "instant",
                "text",
            }:
                self.problem(f"{path}: ordered comparison does not support {left.kind}")
            return
        if node == "membership":
            item = self.expression(raw.get("item"), f"{path}.item", depth + 1)
            members = raw.get("members")
            if not isinstance(members, list):
                self.problem(f"{path}.members must be an array")
                return
            for index, member in enumerate(members):
                member_type = self.expression(member, f"{path}.members[{index}]", depth + 1)
                if _INVALID not in {item, member_type} and not _compatible(item, member_type):
                    self.problem(f"{path}.members[{index}] has an incompatible dimension")
            return
        self.problem(f"{path}: unsupported predicate node: {node}")

    def scope(self, raw: object, path: str) -> None:
        if not isinstance(raw, dict):
            self.problem(f"{path} must be an object")
            return
        subject = raw.get("subject")
        body_part = raw.get("body_part")
        if subject == "body_part" and not isinstance(body_part, str):
            self.problem(f"{path}: body_part is required for body_part subject")
        elif subject != "body_part" and body_part is not None:
            self.problem(f"{path}: body_part is only allowed for body_part subject")
        reset = raw.get("reset")
        reset_rule_key = raw.get("reset_rule_key")
        if reset == "explicit_rule" and not isinstance(reset_rule_key, str):
            self.problem(f"{path}: reset_rule_key is required when reset is explicit_rule")
        elif reset != "explicit_rule" and reset_rule_key is not None:
            self.problem(f"{path}: reset_rule_key is only allowed when reset is explicit_rule")
        period_start = raw.get("period_start")
        period_end = raw.get("period_end")
        if (period_start is None) != (period_end is None):
            self.problem(f"{path}: period_start and period_end must be supplied together")
        elif isinstance(period_start, str) and isinstance(period_end, str):
            try:
                if dt.date.fromisoformat(period_start) > dt.date.fromisoformat(period_end):
                    self.problem(f"{path}: period_start must not follow period_end")
            except ValueError:
                self.problem(f"{path}: period boundaries must be valid dates")
        if raw.get("period") == "unknown" and period_start is not None:
            self.problem(f"{path}: an unknown period cannot carry exact boundaries")
        for field in ("subject_ids", "benefit_keys"):
            values = raw.get(field)
            if isinstance(values, list) and len(values) != len(set(map(str, values))):
                self.problem(f"{path}: {field} contains duplicates")

    def validate(self, table_cell_values: Sequence[object]) -> list[str]:
        self.predicate(self.body.get("applies_when"), "applies_when")
        raw_effects = self.body.get("effects")
        if not isinstance(raw_effects, list):
            self.problem("effects must be an array")
            return self.problems
        for index, effect in enumerate(raw_effects):
            path = f"effects[{index}]"
            if not isinstance(effect, dict):
                self.problem(f"{path} must be an object")
                continue
            self.scope(effect.get("scope"), f"{path}.scope")
            kind = effect.get("kind")
            if kind == "definition":
                self.expression(effect.get("value"), f"{path}.value")
            elif kind == "grant":
                self._numeric_effect(effect.get("amount"), f"{path}.amount")
            elif kind == "exclusion":
                self.predicate(effect.get("expense_predicate"), f"{path}.expense_predicate")
            elif kind == "exception":
                self.expression(effect.get("replacement"), f"{path}.replacement")
                self._unique_strings(effect.get("target_rule_keys"), f"{path}.target_rule_keys")
            elif kind == "limit":
                self._numeric_effect(effect.get("amount"), f"{path}.amount")
                base_key = effect.get("percentage_base_key")
                if base_key is not None:
                    base_type = self.input_reference(base_key, f"{path}.percentage_base_key")
                    if base_type != _INVALID and not _is_numeric(base_type):
                        self.problem(f"{path}.percentage_base_key must reference a numeric input")
            elif kind == "waiting":
                self.input_reference(effect.get("trigger_input"), f"{path}.trigger_input")
                credit_key = effect.get("credit_input")
                if credit_key is not None:
                    credit_type = self.input_reference(credit_key, f"{path}.credit_input")
                    if credit_type != _INVALID and not _is_numeric(credit_type):
                        self.problem(f"{path}.credit_input must reference a duration input")
            elif kind == "deduction":
                self._numeric_effect(effect.get("amount"), f"{path}.amount")
                base_type = self.input_reference(effect.get("base_input"), f"{path}.base_input")
                if base_type != _INVALID and not _is_numeric(base_type):
                    self.problem(f"{path}.base_input must reference a numeric input")
                self._unique_strings(
                    effect.get("order_after_rule_keys"), f"{path}.order_after_rule_keys"
                )
            elif kind == "accumulation":
                self._numeric_effect(effect.get("amount"), f"{path}.amount")
                self.predicate(effect.get("membership"), f"{path}.membership")
            elif kind == "precedence":
                self._unique_strings(
                    effect.get("overridden_rule_keys"), f"{path}.overridden_rule_keys"
                )
            elif kind == "right":
                self.expression(effect.get("deadline"), f"{path}.deadline")
                self.input_reference(effect.get("trigger_input"), f"{path}.trigger_input")
            elif kind not in {"eligibility", "bundle_consequence"}:
                self.problem(f"{path} has unsupported effect kind: {kind}")
        self._unique_strings(self.body.get("mandatory_rule_keys"), "mandatory_rule_keys")
        for index, value in enumerate(table_cell_values):
            result = self.expression(value, f"table_cells[{index}].value")
            if (
                self.table_result is not None
                and _INVALID not in {result, self.table_result}
                and not _compatible(result, self.table_result)
            ):
                self.problem(f"table_cells[{index}].value has the wrong result dimension")
        return self.problems

    def _numeric_effect(self, raw: object, path: str) -> None:
        result = self.expression(raw, path)
        if result != _INVALID and not _is_numeric(result):
            self.problem(f"{path} must produce a numeric value")

    def _unique_strings(self, raw: object, path: str) -> None:
        if not isinstance(raw, list):
            self.problem(f"{path} must be an array")
            return
        strings = [value for value in raw if isinstance(value, str)]
        if len(strings) != len(raw):
            self.problem(f"{path} must contain only rule keys")
        if len(strings) != len(set(strings)):
            self.problem(f"{path} contains duplicate rule keys")


def rule_semantic_problems(
    body: Mapping[str, Any], *, table_cell_values: Sequence[object] = ()
) -> list[str]:
    """Return deterministic material problems for one schema-valid ``RuleV1`` body."""

    return _RuleValidator(body).validate(table_cell_values)


def _rule_references(body: Mapping[str, Any]) -> list[tuple[str, str]]:
    references: list[tuple[str, str]] = []
    mandatory = body.get("mandatory_rule_keys")
    if isinstance(mandatory, list):
        references.extend((value, "mandatory") for value in mandatory if isinstance(value, str))
    effects = body.get("effects")
    scopes: list[object] = []
    if isinstance(effects, list):
        for effect in effects:
            if not isinstance(effect, dict):
                continue
            scopes.append(effect.get("scope"))
            fields = {
                "exception": ("target_rule_keys", "exception"),
                "deduction": ("order_after_rule_keys", "calculation"),
                "precedence": ("overridden_rule_keys", "override"),
            }
            selected = fields.get(str(effect.get("kind")))
            if selected is not None:
                field, relation = selected
                values = effect.get(field)
                if isinstance(values, list):
                    references.extend(
                        (value, relation) for value in values if isinstance(value, str)
                    )
    table = body.get("table")
    if isinstance(table, dict):
        scopes.append(table.get("scope"))
    for scope in scopes:
        if isinstance(scope, dict) and scope.get("reset") == "explicit_rule":
            reset_rule_key = scope.get("reset_rule_key")
            if isinstance(reset_rule_key, str):
                references.append((reset_rule_key, "scope"))
    return references


def rule_link_references(body: Mapping[str, Any]) -> list[tuple[str, str]]:
    """Return deduplicated ``(rule_key, PolicyRuleLink.link_type)`` pairs."""

    link_types = {
        "mandatory": "prerequisite",
        "exception": "exception",
        "calculation": "calculation_input",
        "override": "overrides",
        "scope": "scope",
    }
    links = {
        (target, link_types[relation])
        for target, relation in _rule_references(body)
        if relation in link_types
    }
    return sorted(links)


def rule_graph_problems(
    rules: Mapping[str, tuple[str, Mapping[str, Any]]],
) -> list[str]:
    """Resolve rule references and reject executable dependency cycles.

    A cycle made only of definition-to-definition language links is retained for
    bounded retrieval, as approved.  Any calculation, exception, ordering, scope,
    or override edge makes the cycle executable and therefore unpublishable.
    """

    problems: list[str] = []
    adjacency: dict[str, set[str]] = {key: set() for key in rules}
    for source in sorted(rules):
        source_type, body = rules[source]
        seen: set[tuple[str, str]] = set()
        for target, relation in _rule_references(body):
            edge = (target, relation)
            if edge in seen:
                continue
            seen.add(edge)
            if target not in rules:
                problems.append(f"{source} references missing rule: {target}")
                continue
            if source == target:
                problems.append(f"{source} contains a self-referencing {relation} dependency")
                continue
            target_type = rules[target][0]
            is_definition_language = (
                relation == "mandatory"
                and source_type == "definition"
                and target_type == "definition"
            )
            if not is_definition_language:
                adjacency[source].add(target)

    state: dict[str, int] = {key: 0 for key in rules}
    reported: set[tuple[str, ...]] = set()

    for rule_key in sorted(rules):
        if state[rule_key] != 0:
            continue
        state[rule_key] = 1
        path = [rule_key]
        path_positions = {rule_key: 0}
        frames: list[tuple[str, Iterator[str]]] = [(rule_key, iter(sorted(adjacency[rule_key])))]
        while frames:
            node, raw_targets = frames[-1]
            targets = raw_targets
            try:
                target = next(targets)
            except StopIteration:
                frames.pop()
                state[node] = 2
                path_positions.pop(node)
                path.pop()
                continue
            if state[target] == 0:
                state[target] = 1
                path_positions[target] = len(path)
                path.append(target)
                frames.append((target, iter(sorted(adjacency[target]))))
            elif state[target] == 1:
                start = path_positions[target]
                cycle = tuple(path[start:] + [target])
                rotations = [cycle[index:-1] + cycle[:index] for index in range(len(cycle) - 1)]
                canonical_body = min(rotations)
                canonical = canonical_body + (canonical_body[0],)
                if canonical not in reported:
                    reported.add(canonical)
                    problems.append("executable dependency cycle: " + " -> ".join(canonical))
    return problems
