"""Version-2 criterion scope and deterministic checks on quoted rule quantities."""

from __future__ import annotations

import re
from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


@dataclass(frozen=True)
class Criterion:
    key: str
    category: str
    instruction: str


CRITERIA = (
    Criterion("sum_insured", "sum_insured_choices", "Available new-purchase sums insured and their selection conditions; distinguish renewal-only choices."),
    Criterion("room_category", "room_and_icu_limits", "Permitted room category and any room/ICU limit or proportionate-deduction condition."),
    Criterion("copay", "copay", "Mandatory base copayment, including entry-age conditions. Voluntary copayment is not selected. Do not infer zero from silence."),
    Criterion("deductible", "deductible", "Base deductible. Optional aggregate deductible is not selected. Cite explicit support for zero or not applicable."),
    Criterion("ped_waiting_period", "waiting_periods", "Base pre-existing-disease waiting period and applicable continuity/credit conditions; no optional buyback."),
    Criterion("initial_specific_waiting_periods", "waiting_periods", "Both initial and specified-disease/procedure waiting periods, with accident exceptions, scope and credit conditions."),
    Criterion("maternity", "maternity_and_newborn", "Maternity cover or exclusion, waiting period, monetary limits, eligibility and event-count conditions."),
    Criterion("newborn", "maternity_and_newborn", "Newborn cover, start/end age, limits, parent/claim/continuity conditions and relevant exclusions."),
    Criterion("restoration", "restoration", "Restoration amount, frequency, exhaustion trigger, same/different illness and subsequent-claim conditions."),
    Criterion("family_floater", "family_composition", "Whether floater cover is available and its relationships, member limits and dependent-child conditions."),
    Criterion("portability", "portability", "Portability rights, credit for prior coverage and application timing/conditions. Do not promise acceptance."),
    Criterion("geography", "geography", "Territory of operative cover and any stated territorial exception; premium zones alone are not coverage."),
    Criterion("eligibility", "eligibility", "Adult/child entry ages, renewal distinctions, relationships and underwriting discretion; age alone must not imply acceptance."),
)
assert len(CRITERIA) == 13


def criterion_for_key(rule_key: str) -> Criterion | None:
    parts = rule_key.split(".", 2)
    if len(parts) != 3:
        return None
    return next((item for item in CRITERIA if parts[0] == item.category and parts[2].startswith(item.key + "_")), None)


_NUMBER = r"(?:\d[\d,]*(?:\.\d+)?|zero|one|two|three|four|five|six|seven|eight|nine|ten|twelve|sixteen|eighteen|twenty|thirty|sixty|ninety)"
_WORDS = dict(zip(
    "zero one two three four five six seven eight nine ten twelve sixteen eighteen twenty thirty sixty ninety".split(),
    (0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 16, 18, 20, 30, 60, 90), strict=True,
))


def _decimal(value: str) -> Decimal:
    return Decimal(_WORDS[value] if value in _WORDS else value.replace(",", ""))


def quoted_quantities(quote: str) -> dict[str, set[Decimal]]:
    """Normalize printed units without changing a quotation or inventing conversions."""
    text = " ".join(quote.casefold().split())
    quantities: dict[str, set[Decimal]] = {unit: set() for unit in ("money", "ratio", "day", "month", "year", "hour", "count")}
    numbers = {_decimal(match.group()) for match in re.finditer(rf"(?<!\w){_NUMBER}(?!\w)", text)}
    if re.search(r"\brs\.?|\brupees\b|\binr\b|₹", text):
        quantities["money"].update(numbers)
        for match in re.finditer(rf"({_NUMBER})\s*(lakh|lac|crore)s?\b", text):
            quantities["money"].add(_decimal(match[1]) * (10000000 if match[2] == "crore" else 100000))
    for match in re.finditer(rf"({_NUMBER})\s*(?:%|percent|per cent)", text):
        quantities["ratio"].add(_decimal(match[1]) / 100)
    for unit in ("day", "month", "year", "hour"):
        for match in re.finditer(rf"({_NUMBER})(?:\s*(?:-|–|to|and)\s*({_NUMBER}))?\s*{unit}s?\b", text):
            quantities[unit].add(_decimal(match[1]))
            if match[2]:
                quantities[unit].add(_decimal(match[2]))
    quantities["month"].update(value * 12 for value in quantities["year"])
    quantities["year"].update(value / 12 for value in quantities["month"])
    for match in re.finditer(rf"({_NUMBER})\s*(?:times?|occasions?|claims?|children|adults?|members?|deliveries|delivery)\b", text):
        quantities["count"].add(_decimal(match[1]))
    if re.search(r"\b(?:nil|zero|not applicable)\b|\bno\s+(?:co-?payment|deductible)\b", text):
        quantities["ratio"].add(Decimal(0))
        quantities["money"].add(Decimal(0))
    return quantities


def quantity_support_problems(value: object, quotes: list[str]) -> list[str]:
    """Check each authored number/unit against its quoted pages, before semantic review.

This does not establish entailment or table-cell association: the independent reviewer
must check those and every applicability condition against the complete source text.
"""
    support: dict[str, set[Decimal]] = {}
    for quote in quotes:
        for unit, numbers in quoted_quantities(quote).items():
            support.setdefault(unit, set()).update(numbers)
    problems: list[str] = []

    def visit(node: object, path: str) -> None:
        if isinstance(node, dict):
            if node.get("state") == "finite" or (node.get("unit") in {"day", "month", "year", "hour"} and type(node.get("value")) is int):
                try:
                    number = Decimal(str(node["value"]))
                except (KeyError, InvalidOperation):
                    problems.append(f"{path}: malformed source quantity")
                else:
                    unit = str(node.get("unit"))
                    if number not in support.get(unit, set()):
                        problems.append(f"{path}: {number} {unit} has no matching quoted number and unit")
            for key, child in node.items():
                visit(child, f"{path}.{key}")
        elif isinstance(node, list):
            for index, child in enumerate(node):
                visit(child, f"{path}[{index}]")

    visit(value, "rule")
    return problems


def no_copay_body(copay_key: str, validated_body: dict[str, Any]) -> dict[str, Any] | None:
    """Derive only a validated literal rate; retain its complete applicability and citations."""
    if validated_body.get("unresolved"):
        return None
    effects = validated_body.get("effects", [])
    if len(effects) != 1 or effects[0].get("kind") != "deduction":
        return None
    effect = effects[0]
    amount = effect.get("amount", {})
    value = amount.get("value", {})
    if amount.get("node") != "literal" or value.get("state") != "finite" or value.get("unit") != "ratio":
        return None
    rate = Decimal(str(value["value"]))
    if not Decimal(0) <= rate <= Decimal(1):
        return None
    body = deepcopy(validated_body)
    body["effects"] = [{
        "kind": "definition", "target_key": "no_copay", "scope": deepcopy(effect["scope"]),
        "term_key": "no_copay", "value": {"node": "literal", "value": {"kind": "boolean", "value": rate == 0}},
    }]
    body["mandatory_rule_keys"] = list(dict.fromkeys([*body["mandatory_rule_keys"], copay_key]))
    return body
