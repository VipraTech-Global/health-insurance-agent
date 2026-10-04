"""Versioned chat state; incomplete facts and proposed changes are explicit."""

from typing import Literal

from pydantic import Field

from .contracts import Closed, PlanType

Stage = Literal["details", "requirements", "narrowing", "stopped"]
Strength = Literal["must_have", "nice_to_have", "unclassified"]
FIELDS = (
    "maternity",
    "newborn",
    "opd",
    "room_limit",
    "copay",
    "ped_waiting",
    "specified_waiting",
    "deductible",
    "restoration",
    "no_claim_bonus",
    "ayush",
)


class ChatPerson(Closed):
    id: str = Field(max_length=80)
    relationship: Literal["self", "spouse", "child", "parent", "parent_in_law", "other"]
    age: int | None = Field(default=None, ge=0, le=60000)
    age_unit: Literal["years", "months", "days"] = "years"
    dependent: bool | None = None


class Requirement(Closed):
    field: str = Field(max_length=80)
    original_text: str = Field(max_length=2000)
    strength: Strength = "unclassified"
    person_id: str | None = None
    value: str = "covered"


class IncompleteProfile(Closed):
    schema_version: Literal[2] = 2
    people: list[ChatPerson] = Field(default_factory=list, max_length=12)
    city: str | None = Field(default=None, max_length=120)
    sum_insured: int | None = Field(default=None, ge=1)
    annual_budget: int | None = Field(default=None, ge=1)
    plan_type: PlanType = "unresolved"
    # The customer explicitly has no cover-type preference.
    any_type: bool = False
    coverage_basis: Literal["individual", "floater"] | None = None
    # Set only when the city answers "Which city in India do you live in?".
    resides_in_india: bool = False
    existing_cover: str | None = Field(default=None, max_length=1000)
    health_details: str | None = Field(default=None, max_length=2000)
    requirements: list[Requirement] = Field(default_factory=list, max_length=20)


class QuestionIntent(Closed):
    id: str
    field: str
    person_id: str | None = None
    stage: Stage
    template: str
    text: str
    source_indexes: list[str] = Field(default_factory=list)
    proposed_value: str | None = None


class PriceChoice(Closed):
    axis: str
    value: str


class ProposedChanges(Closed):
    schema_version: Literal[2] = 2
    people: list[ChatPerson] = Field(default_factory=list, max_length=12)
    city: str | None = None
    sum_insured: int | None = Field(default=None, ge=1)
    annual_budget: int | None = Field(default=None, ge=1)
    plan_type: PlanType | None = None
    coverage_basis: Literal["individual", "floater"] | None = None
    outside_india: bool = False
    existing_cover: str | None = None
    health_details: str | None = None
    requirements: list[Requirement] = Field(default_factory=list, max_length=20)
    removed_people: list[str] = Field(default_factory=list, max_length=12)
    correction: bool = False
    ambiguous_field: str | None = None
    ambiguity: str | None = None
    skip: bool = False
    skip_health_details: bool = False
    stop: bool = False
    affirmative: bool | None = None
    no_preference: bool = False
    no_more_needs: bool = False
    narrow_first: bool = False
    next_batch: bool = False
    policy_question: str | None = None
    selected_plans: list[str] = Field(default_factory=list, max_length=5)
    restored_plans: list[str] = Field(default_factory=list, max_length=5)
    withdrawn_requirements: list[str] = Field(default_factory=list, max_length=20)
    insurer_filter: str | None = None
    price_plan: str | None = None
    price_axis: str | None = None
    price_value: str | None = None
    price_axes: list[PriceChoice] = Field(default_factory=list, max_length=12)


class ChatState(Closed):
    schema_version: Literal[2] = 2
    revision: int = 0
    source_indexes: list[str] = Field(default_factory=list)
    stage: Stage = "details"
    profile: IncompleteProfile = Field(default_factory=IncompleteProfile)
    pending: QuestionIntent | None = None
    interrupted: QuestionIntent | None = None
    answered: list[str] = Field(default_factory=list)
    skipped: list[str] = Field(default_factory=list)
    narrowing_asked: list[str] = Field(default_factory=list)
    selected_plans: list[str] = Field(default_factory=list)
    restored_plans: list[str] = Field(default_factory=list)
    policy_question: str | None = None
    policy_deferred: bool = False
    # Code-chosen alphabetical groups of five when documents cannot narrow further.
    batch_question: str | None = None
    batch_queue: list[str] = Field(default_factory=list)
    insurer_filter: str | None = None
    question_count: int = 0
    stop_reason: str | None = None
    understanding: list[str] = Field(default_factory=list)
    message: str = ""
    question_id: str | None = None
    models: list[str] = Field(default_factory=list)
    fit_groups: dict[str, list[dict]] = Field(
        default_factory=lambda: {"fits": [], "unresolved": [], "doesnt_fit": []}
    )
    price_plan: str | None = None
    price_axes: dict[str, str] = Field(default_factory=dict)
    price: dict | None = None
    turns: list[dict] = Field(default_factory=list)
    transcript: list[dict] = Field(default_factory=list)
