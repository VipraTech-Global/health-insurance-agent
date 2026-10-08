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
# Benefits the answer bank holds the engine's validated answer for, per plan.
TOPIC_KEYS = (
    "room_rent",
    "icu",
    "ped",
    "specified_waiting",
    "maternity",
    "newborn",
    "copay",
    "deductible",
    "restoration",
    "no_claim_bonus",
    "pre_post",
    "day_care",
    "road_ambulance",
    "air_ambulance",
    "ayush",
    "organ_donor",
    "home_care",
    "health_check",
    "opd",
    "cataract",
)
Topic = Literal[TOPIC_KEYS]
# Chat need fields and the bank topic that answers each; other topics keep their key.
FIELD_TOPICS = {field: field for field in FIELDS if field in TOPIC_KEYS} | {
    "room_limit": "room_rent",
    "ped_waiting": "ped",
}
TOPIC_FIELDS = {topic: field for field, topic in FIELD_TOPICS.items()}


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
    # "I don't know my budget" said outside the budget question.
    budget_unsure: bool = False
    # A bare "must have" restating the latest need.
    restated: bool = False
    narrow_first: bool = False
    next_batch: bool = False
    # Asks what the listed benefit terms mean; not a question about any plan.
    explain_terms: bool = False
    # Asks to see the plans now instead of answering more narrowing questions.
    show_plans: bool = False
    # Asks the assistant to pick a plan; set by code from the customer's words.
    suggest: bool = False
    # How many plans the customer asked to see ("top 3"); set by code.
    list_count: int | None = Field(default=None, ge=1, le=5)
    # Asks which choices exist for the pending detail (e.g. sum insured).
    options_asked: bool = False
    # Refers to the plans just shown ("these plans"); set by code.
    about_shown: bool = False
    # Also asks about a limit alongside another request; set by code.
    limit_asked: bool = False
    # Asks for printed premiums across the open plans (e.g. the 3 lowest).
    compare_prices: bool = False
    compare_count: int | None = Field(default=None, ge=1, le=20)
    policy_question: str | None = None
    # The one benefit a whole-benefit question is about; null for anything narrower.
    policy_topic: Topic | None = None
    # Send the customer's own wording to the engine instead of the topic answer; set by code.
    exact_question: bool = False
    # Answer the pending question for the next five plans; set by code.
    ask_next: bool = False
    # List the plans whose wording puts the last topic in the base cover; set by code.
    base_only: bool = False
    selected_plans: list[str] = Field(default_factory=list, max_length=5)
    restored_plans: list[str] = Field(default_factory=list, max_length=5)
    withdrawn_requirements: list[str] = Field(default_factory=list, max_length=20)
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
    # A benefit to answer from the answer bank this turn, for every open plan.
    policy_topic: str | None = None
    # Why it is shown: the customer's question, a need they named, or a shared illness.
    topic_reason: Literal["question", "need", "health"] | None = None
    # The last topic answered, the customer's own wording and where each plan put it.
    last_topic: str | None = None
    topic_original: str | None = Field(default=None, max_length=3000)
    topic_groups: dict[str, str] = Field(default_factory=dict)
    # Narrowing questions declined in a row; two stop narrowing until the needs change.
    declined_narrowing: int = 0
    # The customer said they need nothing more once the plans were shown; the next reply
    # signs off instead of asking again.
    wrapped_up: bool = False
    # Plans this turn's question is about ("these plans", named plans, the next five);
    # empty means every open plan.
    asked_plans: list[str] = Field(default_factory=list)
    # Limit the next plan list to these plans (e.g. those with a benefit in the base cover).
    list_only: list[str] = Field(default_factory=list)
    # Code-chosen alphabetical groups of five when documents cannot narrow further.
    batch_question: str | None = None
    batch_queue: list[str] = Field(default_factory=list)
    # Remaining plans listed on request, A–Z in groups of five; no ranking.
    plans_requested: bool = False
    plans_listed: bool = False
    list_queue: list[str] = Field(default_factory=list)
    # Plans this turn's message names (shortlist or listed page); reset every turn.
    shown_plans: list[str] = Field(default_factory=list)
    # The most recent plans shown, kept so "these plans" has a referent.
    last_shown: list[str] = Field(default_factory=list)
    # Requirements when the plans were last listed; a change lists them again.
    listed_for: str | None = None
    # How many plans the customer asked to see ("top 3").
    list_count: int | None = None
    # A vague need ("limits matter") awaiting a concrete choice.
    vague_need: str | None = None
    # The customer asked which choices exist for the pending detail.
    options_asked: bool = False
    # Ask which limit to quote after this turn's answer.
    limit_asked: bool = False
    # Answer how pre-existing illness is covered before asking anything else.
    ped_answer: bool = False
    # Price the plans last shown rather than every open plan.
    compare_shown: bool = False
    # Kept for stored states; no longer read.
    suggestion_asked: bool = False
    # Printed-premium comparison across open plans, lowest first; never a ranking of fit.
    compare_requested: bool = False
    compare_count: int | None = None
    price_comparison: dict | None = None
    # Kept for stored states; no longer read.
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
