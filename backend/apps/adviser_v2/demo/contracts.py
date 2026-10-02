"""Closed versioned contracts for matching, prices and per-plan answers."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PlanType = Literal["medical_indemnity", "top_up", "super_top_up", "critical_illness", "fixed_benefit", "unresolved"]


class Closed(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Citation(Closed):
    section_id: str
    page_id: str
    quote: str = Field(min_length=1, max_length=1600)
    occurrence: int = Field(ge=0, default=0)


class SupportedText(Closed):
    text: str = Field(min_length=1, max_length=2000)
    citations: list[Citation] = Field(min_length=1, max_length=12)


class Statement(SupportedText):
    conditions: list[SupportedText] = Field(default_factory=list, max_length=12)
    restrictions: list[SupportedText] = Field(default_factory=list, max_length=12)


class Answer(Closed):
    schema_version: Literal[1] = 1
    plan_id: str
    status: Literal["answered", "not_found"]
    statements: list[Statement] = Field(max_length=8)


class Need(Closed):
    original_text: str = Field(max_length=1000)
    person_id: str | None
    field: Literal["maternity", "opd", "copay", "room_limit", "ped_waiting", "budget", "other"]
    mapped: bool


class NormalizedNeeds(Closed):
    schema_version: Literal[1] = 1
    needs: list[Need] = Field(max_length=20)


class PersonInput(Closed):
    id: str
    relationship: Literal["self", "spouse", "child", "parent", "parent_in_law", "other"]
    age_days: int | None = Field(ge=0, le=60000)
    dependent: bool | None = None


class Profile(Closed):
    schema_version: Literal[1] = 1
    revision: int = Field(default=1, ge=1)
    people: list[PersonInput] = Field(min_length=1, max_length=12)
    sum_insured: int | None = Field(ge=1)
    city: str | None = Field(max_length=120)
    zone: str | None = Field(max_length=120)
    plan_type: PlanType
    needs: list[str] = Field(default_factory=list, max_length=20)
    typed_needs: str = Field(default="", max_length=2000)
    annual_budget: int | None = Field(default=None, ge=1)


class CardField(Closed):
    state: Literal["stated", "not_stated"]
    # Typed alternatives avoid arbitrary JSON supplied by a model.
    numbers: list[int] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    conditions: list[SupportedText] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    variant: str | None = None
    exhaustive: bool = False


class AgeRule(Closed):
    relationship: str
    minimum_days: int | None = Field(ge=0)
    maximum_days: int | None = Field(ge=0)
    maximum_unbounded: bool = False
    citations: list[Citation] = Field(min_length=1)


class FamilyRule(Closed):
    allowed_relationships: list[str]
    maximum_adults: int = Field(ge=1)
    maximum_children: int = Field(ge=0)
    children_must_be_dependent: bool
    citations: list[Citation] = Field(min_length=1)


class PlanCard(Closed):
    schema_version: Literal[1] = 1
    plan_id: str
    index_version: str
    insurer: str
    name: str
    variant: str
    plan_type: PlanType
    model: str | None
    status: Literal["ready", "partial", "documents_unavailable"]
    entry_ages: list[AgeRule]
    renewal_ages: list[AgeRule]
    family_rule: FamilyRule | None
    sum_insured: CardField
    geography: CardField
    copay: CardField
    room_limit: CardField
    ped_waiting: CardField
    maternity: CardField
    opd: CardField


class FitReason(Closed):
    field: str
    status: Literal["fits", "doesnt_fit", "unresolved"]
    explanation: str
    citations: list[Citation]


class FitResult(Closed):
    schema_version: Literal[1] = 1
    plan_id: str
    index_version: str
    status: Literal["fits", "doesnt_fit", "unresolved"]
    hard_limits: list[FitReason]
    other_needs: list[FitReason]


class PremiumResult(Closed):
    schema_version: Literal[1] = 1
    status: Literal["available", "unpublished", "missing_details", "no_exact_combination", "invalid_chart"]
    amount_printed: str | None
    missing_axes: list[str]
    citations: list[Citation]
    label: str = "Indicative annual premium from the official chart, excluding tax"
    caveat: str = "The insurer's final premium may differ. No tax, discount or loading has been calculated."
