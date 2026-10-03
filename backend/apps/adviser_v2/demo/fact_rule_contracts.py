"""Closed, bounded schema for code-derived executable card rules."""

from decimal import Decimal
from typing import Literal

from pydantic import Field, model_validator

from .contracts import Citation, Closed


class RuleGuard(Closed):
    field: Literal["entry_age"]
    operator: Literal["gte"]
    value: int = Field(ge=0, le=150)
    unit: Literal["years"]
    quote: str


class FactRule(Closed):
    field: Literal[
        "geography",
        "entry_age",
        "renewal_age",
        "sum_insured",
        "coverage_basis",
        "plan_type",
        "family",
        "ped_waiting",
        "specified_waiting",
        "copay",
        "room_limit",
        "no_claim_bonus",
        "deductible",
        "maternity",
        "newborn",
        "opd",
        "restoration",
        "ayush",
    ]
    kind: Literal[
        "geography",
        "age",
        "renewal",
        "choices",
        "basis",
        "type",
        "family",
        "maximum",
        "room",
        "bonus",
        "coverage",
    ]
    value: str
    printed: str = Field(min_length=1)
    variant: str
    scope: Literal["base"]
    citations: list[Citation] = Field(min_length=1)
    conditions: list[str]
    condition_mode: Literal["quoted"]
    guards: list[RuleGuard]
    supported: Literal[True]
    restricted_scope: bool = False
    unit: Literal["years", "months", "days", "rupees", "percent", "percent_per_day"] | None = None
    minimum: int | None = Field(default=None, ge=0, le=60000)
    minimum_unit: Literal["years", "months", "days"] | None = None
    maximum: int | None = Field(default=None, ge=0, le=60000)
    maximum_unit: Literal["years", "months", "days"] | None = None
    maximum_unbounded: bool = False
    inclusive: bool = True
    relationship: Literal["adult", "child", "person"] | None = None
    geography_basis: Literal["residence", "nationwide_premium_zones"] | None = None
    unlimited_choice: bool = False
    primary_spouse_pair_only: bool = False
    maximum_members: int | None = Field(default=None, ge=1, le=20)
    choices: list[int] = Field(default_factory=list)
    exhaustive: bool = False
    maximum_adults: int | None = Field(default=None, ge=1, le=12)
    maximum_children: int | None = Field(default=None, ge=0, le=12)
    relationship_limits: dict[str, int] = Field(default_factory=dict)
    relationships: list[str] = Field(default_factory=list)
    dependent_children: bool | None = None
    coverage_basis: Literal["individual", "floater"] | None = None
    percent: str | None = None
    cap_percent: str | None = None
    limits_rupees: list[int] = Field(default_factory=list)
    waiting_months: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def valid_boundaries(self):
        if self.kind == "age":
            if self.minimum is None or not self.minimum_unit or not self.relationship:
                raise ValueError("An age rule needs a lower bound, unit and person applicability.")
            if not self.maximum_unbounded and (self.maximum is None or not self.maximum_unit):
                raise ValueError("An age rule needs an upper bound and unit.")
            for value, unit in (
                (self.minimum, self.minimum_unit),
                (self.maximum, self.maximum_unit),
            ):
                if (
                    value is not None
                    and value > {"years": 150, "months": 1800, "days": 60000}[unit]
                ):
                    raise ValueError("Age projection is outside supported bounds.")
            if (
                self.minimum_unit == self.maximum_unit
                and self.maximum is not None
                and self.minimum > self.maximum
            ):
                raise ValueError("Contradictory age range.")
        if self.kind == "choices" and (not self.choices or any(v <= 0 for v in self.choices)):
            raise ValueError("Sum-insured choices must be positive printed amounts.")
        if self.kind == "family" and (
            (
                self.maximum_adults is None
                and self.maximum_members is None
                and not {"self", "spouse"} <= set(self.relationships)
            )
            or not self.relationships
        ):
            raise ValueError("Family combinations must have explicit limits and relationships.")
        if self.kind == "coverage" and self.value not in {"covered", "not_covered"}:
            raise ValueError("Coverage is positive or explicitly contrary, never absence.")
        if self.kind in {"maximum", "bonus"}:
            amount = Decimal(self.value)
            if not amount.is_finite() or amount < 0 or self.unit is None:
                raise ValueError("A numeric rule needs a finite nonnegative amount and unit.")
            if self.field == "copay" and amount > 100:
                raise ValueError("Co-pay exceeds 100 percent.")
            if self.unit == "months" and amount > 120:
                raise ValueError("Unsupported waiting period.")
        if self.percent is not None and not 0 <= Decimal(self.percent) <= 100:
            raise ValueError("Room percentage is outside supported bounds.")
        if any(m < 0 or m > 120 for m in self.waiting_months):
            raise ValueError("Unsupported benefit waiting period.")
        return self
