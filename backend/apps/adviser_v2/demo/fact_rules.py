"""Bounded projections. Complex wording stays quoted but non-executable."""

import re
from typing import Literal

from pydantic import Field, model_validator

from .cards import FieldSource, entry_rules, family_rule, sum_insured_field
from .contracts import Citation, Closed, Statement


class ExecutableRule(Closed):
    field: str
    kind: Literal["age", "family", "choices", "type", "basis", "coverage", "maximum"]
    value: str = ""
    unit: Literal["years", "days", "months", "rupees", "percent"] | None = None
    minimum: int | None = Field(default=None, ge=0)
    maximum: int | None = Field(default=None, ge=0)
    maximum_unbounded: bool = False
    inclusive: bool = True
    person_id: str | None = None
    relationship: str | None = None
    choices: list[int] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    maximum_adults: int | None = Field(default=None, ge=1, le=12)
    maximum_children: int | None = Field(default=None, ge=0, le=12)
    dependent_children: bool | None = None
    variant: str | None = None
    conditions: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(min_length=1)

    @model_validator(mode="after")
    def bounded(self):
        if self.kind == "age" and (
            self.unit is None
            or self.minimum is None
            or self.maximum is None
            and not self.maximum_unbounded
        ):
            raise ValueError("Age rules require explicit bounds and a printed unit.")
        if self.kind == "age" and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError("Contradictory age boundaries.")
        if self.kind == "coverage" and self.value not in {"covered", "not_covered"}:
            raise ValueError("Coverage needs explicit contrary or positive evidence.")
        if self.kind == "choices" and (not self.choices or any(v <= 0 for v in self.choices)):
            raise ValueError("Positive printed sum-insured choices required.")
        if self.kind == "family" and (
            not self.relationships or self.maximum_adults is None or self.maximum_children is None
        ):
            raise ValueError("Incomplete family composition.")
        if self.kind == "maximum" and (
            self.unit is None or not re.fullmatch(r"\d+(?:\.\d+)?", self.value)
        ):
            raise ValueError("A maximum must retain its numeric unit.")
        return self


NAMES = {
    "maternity": "maternity",
    "newborn": "newborn(?: baby)?",
    "opd": "(?:OPD|outpatient)",
    "restoration": "restoration",
    "no_claim_bonus": "no.claim bonus",
    "ayush": "AYUSH",
}


def project(field, result, variant):
    """Project only whole bounded clauses, including their conditions."""
    if result.get("status") != "answered":
        return [], {}
    statements = [Statement.model_validate(s) for s in result["answer"]["statements"]]
    rules = []
    legacy = {}
    # Existing tested narrow grammars remain available; their printed excerpts
    # are retained and contradictory projections are explicitly discarded.
    if field in {"entry_age", "family", "sum_insured"}:
        source = FieldSource(field=field, status="answered", statements=statements[:3])
        if len(statements) > 3:
            return [], {}
        if field == "entry_age":
            ages = entry_rules(source)
            if len({a.relationship for a in ages}) != len(ages):
                ages = []
            legacy["entry_ages"] = [a.model_dump() for a in ages]
            for a in ages:
                raw = " ".join(a.citations[0].quote.split())
                # Preserve the explicitly printed minimum and maximum units.
                bounds = re.findall(r"(\d+)\s*(years|days)", raw, re.I)
                if not bounds:
                    continue
                minimum, unit = bounds[0]
                maximum = int(bounds[1][0]) if len(bounds) > 1 else None
                if len(bounds) > 1 and bounds[1][1].lower() != unit.lower():
                    # Mixed units are retained in legacy exact-day checks, but
                    # are not represented as a single-unit executable rule.
                    continue
                rules.append(
                    ExecutableRule(
                        field=field,
                        kind="age",
                        minimum=int(minimum),
                        maximum=maximum,
                        maximum_unbounded=a.maximum_unbounded,
                        unit=unit.lower(),
                        relationship=a.relationship,
                        variant=variant,
                        citations=a.citations,
                    )
                )
        elif field == "family":
            family = family_rule(source)
            legacy["family_rule"] = family.model_dump() if family else None
            if family:
                rules.append(
                    ExecutableRule(
                        field=field,
                        kind="family",
                        relationships=family.allowed_relationships,
                        maximum_adults=family.maximum_adults,
                        maximum_children=family.maximum_children,
                        dependent_children=family.children_must_be_dependent,
                        variant=variant,
                        citations=family.citations,
                    )
                )
        else:
            choices = sum_insured_field(source)
            legacy["sum_insured"] = choices.model_dump()
            if choices.exhaustive and choices.numbers:
                rules.append(
                    ExecutableRule(
                        field=field,
                        kind="choices",
                        choices=choices.numbers,
                        unit="rupees",
                        variant=variant,
                        citations=choices.citations,
                    )
                )
    for statement in statements:
        if statement.conditions or statement.restrictions:
            continue
        for c in statement.citations:
            raw = " ".join(c.quote.split()).strip(" •▪")
            if field in NAMES:
                match = re.fullmatch(
                    NAMES[field]
                    + r"(?: cover| benefit| treatment)? (?:is |are )?(covered|not covered|excluded)\.",
                    raw,
                    re.I,
                )
                if match:
                    rules.append(
                        ExecutableRule(
                            field=field,
                            kind="coverage",
                            value="covered" if match[1].lower() == "covered" else "not_covered",
                            variant=variant,
                            citations=[c],
                        )
                    )
            elif field == "coverage_basis":
                match = re.fullmatch(
                    r"The (?:policy|plan) is available on (individual|floater|individual and floater) basis\.",
                    raw,
                    re.I,
                )
                if match:
                    rules.append(
                        ExecutableRule(
                            field=field,
                            kind="basis",
                            value=match[1].lower().replace(" and ", "|"),
                            variant=variant,
                            citations=[c],
                        )
                    )
            elif field == "plan_type":
                match = re.fullmatch(
                    r"This (?:is an?|policy is an?) (indemnity|top.up|super.top.up|critical illness|fixed benefit)(?: based)? (?:health )?(?:insurance )?(?:policy|plan)\.",
                    raw,
                    re.I,
                )
                if match:
                    value = {
                        "indemnity": "medical_indemnity",
                        "top up": "top_up",
                        "super top up": "super_top_up",
                        "critical illness": "critical_illness",
                        "fixed benefit": "fixed_benefit",
                    }[match[1].lower().replace("-", " ")]
                    rules.append(
                        ExecutableRule(
                            field=field, kind="type", value=value, variant=variant, citations=[c]
                        )
                    )
            elif field in {"ped_waiting", "specified_waiting", "copay", "deductible"}:
                label = {
                    "ped_waiting": "Pre-existing disease waiting period",
                    "specified_waiting": "Specified disease waiting period",
                    "copay": "Co-pay",
                    "deductible": "Deductible",
                }[field]
                match = re.fullmatch(
                    re.escape(label) + r": (\d+) (years|months|days|rupees|percent)\.", raw, re.I
                )
                if match:
                    rules.append(
                        ExecutableRule(
                            field=field,
                            kind="maximum",
                            value=match[1],
                            unit=match[2].lower(),
                            variant=variant,
                            citations=[c],
                        )
                    )
    # Repeated citations do not make multiple rules; contradictory values remain
    # unresolved instead of choosing the favourable interpretation.
    unique = {r.model_dump_json(exclude={"citations"}): r for r in rules}
    if field != "entry_age" and len(unique) > 1:
        return [], {}
    return [r.model_dump() for r in unique.values()], legacy
