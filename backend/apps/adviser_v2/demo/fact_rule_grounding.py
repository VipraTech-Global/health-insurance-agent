"""Check every projected numeric value and categorical keyword in its own evidence."""

import re
from decimal import Decimal

from .fact_rules_v6 import KEYWORDS, MONEY


def money(raw):
    values = []
    for match in MONEY.finditer(raw):
        numeral = (match[1] or match[3]).replace(",", "")
        if not re.fullmatch(r"[0-9]+(?:\.[0-9]+)?", numeral):
            continue
        unit = (match[2] or match[4] or "").lower()
        multiplier = 10000000 if unit.startswith("crore") else 100000 if unit else 1
        values.append((int(Decimal(numeral) * multiplier), match[0]))
    return values


KEYS = {
    "single_private": r"single\s+private|private\s+single",
    "single_standard": r"single\s+standard",
    "actuals": r"at\s+actuals",
    "twin_sharing": r"twin\s+sharing",
    "shared": r"shared|general\s+(?:ward|room)",
    "any_room": r"(?:any|all)\s+rooms?",
    "any_room_except_suite": r"(?:except|excluding)\s+(?:a\s+)?suite",
    "percent_of_si": r"%\s*of\s*(?:the\s+)?sum\s*insured",
    "lifetime": r"life[ -]?time|life[ -]?long|no maximum cover ceasing age|no (?:upper|maximum) (?:renewal )?age limit",
    "medical_indemnity": r"indemnity",
    "super_top_up": r"super[ -]?top[ -]?up",
    "top_up": r"top[ -]?up",
    "critical_illness": r"critical\s+illness",
    "fixed_benefit": r"fixed\s+benefit",
}


def grounded(rule):
    raw = " ".join(" ".join(c["quote"].split()) for c in rule["citations"])
    if not re.search(KEYWORDS.get(rule["field"], r"(?!)"), raw, re.I):
        return False
    if " ".join(rule["printed"].split()) not in raw:
        return False
    if re.search(r"benefit illustration|illustrative example|assumed", raw, re.I):
        return False
    kind, value = rule["kind"], rule["value"]

    def numeric(number, unit, source=raw):
        if number is None:
            return True
        n = Decimal(str(number))
        if unit == "rupees":
            return int(n) in {v for v, _ in money(source)} or (
                n == 0
                and bool(re.search(r"no deductible|deductible[^.]{0,20}(?:nil|zero)", source, re.I))
            )
        suffix = {
            "years": r"years?",
            "days": r"days?",
            "months": r"months?",
            "percent": "%",
            "percent_per_day": "%",
        }.get(unit)
        if not suffix:
            return False
        matches = re.findall(r"(\d+(?:\.\d+)?)\s*" + suffix, source, re.I)
        if any(Decimal(v) == n for v in matches):
            return True
        if unit == "months":
            return any(Decimal(v) * 12 == n for v in re.findall(r"(\d+)\s*years?", source, re.I))
        # A shared printed unit in an explicit range is permitted.
        return bool(
            re.search(
                r"\b" + re.escape(str(number)) + r"\s*(?:to|and|[-–])\s*\d+\s*" + suffix,
                source,
                re.I,
            )
        )

    if kind == "age":
        return (
            numeric(rule["minimum"], rule["minimum_unit"], rule["printed"])
            and numeric(rule.get("maximum"), rule.get("maximum_unit"), rule["printed"])
            and bool(
                re.search(
                    {"adult": r"adult", "child": r"child|children", "person": r"persons?"}[
                        rule["relationship"]
                    ],
                    rule["printed"],
                    re.I,
                )
            )
        )
    if kind in {"maximum", "bonus"}:
        return (
            numeric(value, rule.get("unit"), rule["printed"])
            and numeric(rule.get("cap_percent"), "percent")
            and all(
                numeric(g["value"], g["unit"], g["quote"]) and g["quote"] in raw
                for g in rule.get("guards", [])
            )
        )
    if kind == "choices":
        # Shared-unit enumerations are expanded by the bounded choices parser.
        from .fact_projection import selectable_sums

        s = {"citations": rule["citations"], "conditions": [], "restrictions": [], "table": True}
        parsed = selectable_sums(s, rule["variant"])
        values = {v for v, _ in money(raw)} | {v for r in parsed for v in r["choices"]}
        return all(v in values for v in rule["choices"])
    if kind == "basis":
        return all(re.search(r"\b" + v + r"\b", raw, re.I) for v in value.split("|"))
    if kind in {"room", "renewal", "type"}:
        return bool(re.search(KEYS.get(value, r"(?!)"), raw, re.I)) and numeric(
            rule.get("percent"), rule.get("unit")
        )
    if kind == "coverage":
        if value == "not_covered":
            return bool(
                re.search(
                    r"not covered|not available|not payable|excluded|maternity.{0,65}Excl\s*\d+",
                    raw,
                    re.I,
                )
            )
        return (
            bool(re.search(r"covered|payable|reimburse|indemnify|\bpay\b", raw, re.I))
            and all(numeric(v, "rupees") for v in rule.get("limits_rupees", []))
            and all(numeric(v, "months") for v in rule.get("waiting_months", []))
        )
    if kind == "family":
        return bool(
            re.search(r"\b" + str(rule["maximum_adults"]) + r"\s*adults?", raw, re.I)
            and re.search(
                r"\b" + str(rule["maximum_children"]) + r"\s*(?:dependent )?child", raw, re.I
            )
        ) and all(
            re.search(
                {
                    "self": "self",
                    "spouse": "spouse",
                    "child": "child",
                    "parent": "parent",
                    "parent_in_law": r"parent.{0,3}in.{0,3}law",
                }.get(r, r"(?!)"),
                raw,
                re.I,
            )
            for r in rule["relationships"]
        )
    return False
