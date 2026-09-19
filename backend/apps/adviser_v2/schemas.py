"""Strict model-output contracts used by the v2 relay boundary."""

from __future__ import annotations

import json
from typing import Annotated, Literal, cast

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    Field,
    WithJsonSchema,
    field_validator,
    model_validator,
)

from .contracts import validate_contract


def _parse_json_object(value: object) -> dict[str, object]:
    """Decode an embedded closed object without exposing an open provider schema.

    OpenAI strict structured output rejects ``dict[str, object]`` because its JSON
    Schema necessarily permits arbitrary properties.  The relay therefore carries
    approved nested contracts as JSON-encoded strings.  They are decoded here and
    validated against the reviewed database contracts before callers can use them.
    In-process construction may continue to pass an already-decoded dictionary.
    """

    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Embedded contract value is not valid JSON.") from exc
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("Embedded contract value must be a JSON object.")
    return value


def _parse_json_array(value: object) -> list[object]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ValueError("Embedded contract value is not valid JSON.") from exc
    if not isinstance(value, list):
        raise ValueError("Embedded contract value must be a JSON array.")
    return value


ClosedJsonObject = Annotated[
    dict[str, object],
    BeforeValidator(_parse_json_object),
    WithJsonSchema(
        {
            "type": "string",
            "minLength": 2,
            "description": "A JSON-encoded object conforming to the named closed contract.",
        },
        mode="validation",
    ),
]

ClosedJsonArray = Annotated[
    list[object],
    BeforeValidator(_parse_json_array),
    WithJsonSchema(
        {
            "type": "string",
            "minLength": 2,
            "description": "A JSON-encoded array conforming to the named closed contract.",
        },
        mode="validation",
    ),
]


class StrictOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class InterpretedSubject(StrictOutput):
    key: str = Field(min_length=1, max_length=80)
    person_id: str | None
    display_name: str | None
    relationship: Literal[
        "self", "spouse", "parent", "child", "parent_in_law", "sibling", "dependent", "other"
    ]


class InterpretedStatement(StrictOutput):
    start_offset: int = Field(ge=0)
    end_offset: int = Field(gt=0)
    subject_key: str | None
    kind: Literal[
        "fact",
        "intended_insured",
        "requirement",
        "preference",
        "question",
        "correction",
        "context",
        "other",
    ]
    ambiguous: bool
    ambiguity_reason: str | None

    @model_validator(mode="after")
    def offsets_are_ordered(self) -> InterpretedStatement:
        if self.end_offset <= self.start_offset:
            raise ValueError("Statement offsets must identify a non-empty source span.")
        if self.ambiguous != (self.ambiguity_reason is not None):
            raise ValueError(
                "Ambiguous statements require one reason and clear statements forbid it."
            )
        return self


class InterpretedFact(StrictOutput):
    statement_index: int = Field(ge=0)
    subject_key: str | None
    fact_type: str = Field(min_length=1, max_length=100)
    value: ClosedJsonObject
    confidence: Literal["explicit", "inferred", "uncertain"]

    @field_validator("value")
    @classmethod
    def value_is_closed(cls, value: dict[str, object]) -> dict[str, object]:
        validated = validate_contract("FactValueV1", value)
        if not isinstance(validated, dict):
            raise ValueError("FactValueV1 must be an object.")
        return cast(dict[str, object], validated)


class InterpretedRequirement(StrictOutput):
    statement_index: int = Field(ge=0)
    subject_key: str | None
    criterion: str = Field(min_length=1, max_length=120)
    operator: Literal[
        "equals",
        "not_equals",
        "less_than_or_equal",
        "greater_than_or_equal",
        "includes",
        "excludes",
        "is_available",
        "is_not_available",
        "minimize",
        "maximize",
    ]
    target_value: ClosedJsonObject | None
    priority: Literal["mandatory", "preferred", "informational"]
    scope: Literal["entire_purchase", "all_intended_insured", "person"]

    @field_validator("target_value")
    @classmethod
    def target_is_closed(cls, value: dict[str, object] | None) -> dict[str, object] | None:
        if value is None:
            return None
        validated = validate_contract("FactValueV1", value)
        if not isinstance(validated, dict):
            raise ValueError("FactValueV1 must be an object.")
        return cast(dict[str, object], validated)


class InterpretedCorrection(StrictOutput):
    statement_index: int = Field(ge=0)
    assertion_kind: Literal["fact", "requirement"]
    logical_key: str
    replacement_value: ClosedJsonObject | None
    replacement_status: Literal["reported", "confirmed", "retracted", "withdrawn"]

    @field_validator("replacement_value")
    @classmethod
    def replacement_is_closed(cls, value: dict[str, object] | None) -> dict[str, object] | None:
        if value is None:
            return None
        validated = validate_contract("FactValueV1", value)
        if not isinstance(validated, dict):
            raise ValueError("FactValueV1 must be an object.")
        return cast(dict[str, object], validated)


class CustomerInterpretationV1(StrictOutput):
    schema_version: Literal[1]
    subjects: list[InterpretedSubject]
    statements: list[InterpretedStatement]
    facts: list[InterpretedFact]
    requirements: list[InterpretedRequirement]
    corrections: list[InterpretedCorrection]
    intent: Literal[
        "purchase_recommendation",
        "product_comparison",
        "coverage_question",
        "renewal_review",
        "portability_review",
        "conversation",
    ]
    ambiguity: bool
    clarification_question: str | None

    @model_validator(mode="after")
    def references_are_valid(self) -> CustomerInterpretationV1:
        subject_keys = [subject.key for subject in self.subjects]
        if len(subject_keys) != len(set(subject_keys)):
            raise ValueError("Subject keys must be unique within an interpretation.")
        known_subjects = set(subject_keys)
        for statement in self.statements:
            if statement.subject_key is not None and statement.subject_key not in known_subjects:
                raise ValueError("A statement references an unknown subject key.")
        for fact in self.facts:
            if fact.statement_index >= len(self.statements):
                raise ValueError("An assertion references an unknown statement index.")
            if fact.subject_key is not None and fact.subject_key not in known_subjects:
                raise ValueError("An assertion references an unknown subject key.")
        for requirement in self.requirements:
            if requirement.statement_index >= len(self.statements):
                raise ValueError("An assertion references an unknown statement index.")
            if (
                requirement.subject_key is not None
                and requirement.subject_key not in known_subjects
            ):
                raise ValueError("An assertion references an unknown subject key.")
        for correction in self.corrections:
            if correction.statement_index >= len(self.statements):
                raise ValueError("A correction references an unknown statement index.")
        if self.ambiguity != (self.clarification_question is not None):
            raise ValueError("Ambiguity requires one focused clarification question.")
        return self


class ExtractedPolicyTableCell(StrictOutput):
    selectors: ClosedJsonArray
    value: ClosedJsonObject
    evidence_span_id: str = Field(min_length=36, max_length=36)

    @field_validator("selectors")
    @classmethod
    def selectors_are_closed(cls, value: list[object]) -> list[object]:
        validated = validate_contract("TableSelectorsV1", value)
        if not isinstance(validated, list):
            raise ValueError("TableSelectorsV1 must be an array.")
        return cast(list[object], validated)

    @field_validator("value")
    @classmethod
    def value_is_closed(cls, value: dict[str, object]) -> dict[str, object]:
        validated = validate_contract("ExpressionV1", value)
        if not isinstance(validated, dict):
            raise ValueError("ExpressionV1 must be an object.")
        return cast(dict[str, object], validated)


class ExtractedPolicyRule(StrictOutput):
    rule_key: str = Field(min_length=1, max_length=160)
    rule_type: str = Field(min_length=1, max_length=80)
    inventory_category: str = Field(min_length=1, max_length=120)
    body: ClosedJsonObject
    evidence_span_ids: list[str]
    table_cells: list[ExtractedPolicyTableCell]
    table_footnote_span_ids: list[str]

    @field_validator("body")
    @classmethod
    def body_is_closed(cls, value: dict[str, object]) -> dict[str, object]:
        validated = validate_contract("RuleV1", value)
        if not isinstance(validated, dict):
            raise ValueError("RuleV1 must be an object.")
        return cast(dict[str, object], validated)


class PolicyRuleExtractionV1(StrictOutput):
    schema_version: Literal[1]
    policy_version_id: str
    rules: list[ExtractedPolicyRule]
    omitted_inventory_categories: list[str]
    material_issues: list[str]


class ReviewedPolicyRule(StrictOutput):
    rule_key: str = Field(min_length=1, max_length=160)
    verdict: Literal["agree", "disagree", "missing", "ambiguous"]
    independent_body: ClosedJsonObject | None
    evidence_span_ids: list[str]
    material_issue: str | None

    @field_validator("independent_body")
    @classmethod
    def independent_body_is_closed(
        cls, value: dict[str, object] | None
    ) -> dict[str, object] | None:
        if value is None:
            return None
        validated = validate_contract("RuleV1", value)
        if not isinstance(validated, dict):
            raise ValueError("RuleV1 must be an object.")
        return cast(dict[str, object], validated)


class PolicyRuleReviewV1(StrictOutput):
    schema_version: Literal[1]
    policy_version_id: str
    inventory_categories: list[str]
    reviews: list[ReviewedPolicyRule]
    missing_rules: list[ExtractedPolicyRule]


class RecommendationCitationDraft(StrictOutput):
    evidence_span_id: str
    policy_rule_id: str | None
    role: Literal["supports", "restricts", "excepts", "conflicts", "assumption_source"]


class RecommendationStatementDraft(StrictOutput):
    text: str = Field(min_length=1, max_length=4000)
    statement_type: Literal[
        "customer_context",
        "eligibility",
        "requirement_match",
        "benefit",
        "restriction",
        "price",
        "provider",
        "calculation",
        "limitation",
        "next_step",
    ]
    critical: bool
    candidate_assessment_id: str | None
    requirement_match_id: str | None
    information_need_id: str | None
    calculation_id: str | None
    citations: list[RecommendationCitationDraft]


class RecommendationDraftV1(StrictOutput):
    schema_version: Literal[1]
    outcome: Literal["completed", "conditional", "clarification_required", "insufficient_evidence"]
    introduction: str = Field(min_length=1, max_length=4000)
    statements: list[RecommendationStatementDraft]
    follow_up: str | None
