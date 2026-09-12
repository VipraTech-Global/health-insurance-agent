"""Versioned evidence/case interchange contracts, not the final policy database schema."""

from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

Nonempty = Annotated[str, Field(min_length=1)]
Hash = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    format_version: Literal[1] = 1


class EvidenceLocation(Record):
    source_sha256: Hash
    page: Annotated[int, Field(ge=1)]
    passage: Nonempty
    section: Nonempty
    # Native PDF coordinates. Table evidence also needs all applicable header/footnote locations.
    bbox: tuple[float, float, float, float] | None = None
    table_context: tuple[Nonempty, ...] = ()


class Calculation(Record):
    label: Nonempty
    inputs: dict[str, Decimal]
    currency: Literal["INR"] = "INR"
    expression: Nonempty
    expected: Decimal
    assumptions: tuple[Nonempty, ...]
    independent_method: Nonempty
    evidence: tuple[EvidenceLocation, ...]


class CaseRecord(Record):
    case_id: Annotated[str, Field(pattern=r"^(ref|eval)-\d{2}-\d{2}$")]
    split: Literal["reference", "evaluation"]
    family: Annotated[int, Field(ge=1, le=20)]
    title: Nonempty
    # A decision distinction must change applicability, required evidence or the answer.
    decision_distinction: Nonempty
    factors: tuple[Nonempty, ...]
    boundary: Nonempty
    customer_facts: dict[str, str | int | bool | None]
    conversation: tuple[Nonempty, ...]
    known: tuple[Nonempty, ...]
    unknown: tuple[Nonempty, ...]
    corrections: tuple[Nonempty, ...]
    required_information: tuple[Nonempty, ...]
    candidate_configurations: tuple[Nonempty, ...]
    exclusion_reasons: tuple[Nonempty, ...]
    expected_answer: Nonempty
    acceptable_alternatives: tuple[Nonempty, ...]
    evidence: tuple[EvidenceLocation, ...]
    evidence_requirements: tuple[Nonempty, ...]
    calculations: tuple[Calculation, ...]
    gaps: tuple[Nonempty, ...]
    information_map: tuple[Nonempty, ...]
    pass_criteria: tuple[Nonempty, ...]
    assessment: Literal["draft", "evidence_incomplete", "worked"]
    synthetic_customer: Literal[True] = True
    evaluation_exposed: bool = False

    @model_validator(mode="after")
    def consistency(self) -> Self:
        prefix, family, _ = self.case_id.split("-")
        if (prefix == "ref") != (self.split == "reference") or int(family) != self.family:
            raise ValueError("Case identity disagrees with split or family")
        if not self.factors or not self.conversation or not self.pass_criteria:
            raise ValueError("Cases need factors, conversation and pass/fail criteria")
        if self.assessment == "worked" and (self.gaps or not self.evidence):
            raise ValueError("Worked cases require original evidence and no essential gaps")
        if self.assessment == "evidence_incomplete" and not self.gaps:
            raise ValueError("Incomplete cases must identify the missing evidence")
        return self


class RuleInventoryItem(Record):
    rule_id: Nonempty
    insurer_id: Nonempty
    product_version: Nonempty
    topic: Nonempty
    requirement: Nonempty
    evidence: tuple[EvidenceLocation, ...]
    dependencies: tuple[Nonempty, ...]
    critical: bool
    method: Literal["original_document_reading"]
    inventoried_by: Nonempty
    status: Literal["inventoried", "represented", "reviewed", "unsupported"]

    @model_validator(mode="after")
    def original_required(self) -> Self:
        if not self.evidence:
            raise ValueError("Rule denominator must come from an identified original passage")
        return self


class EvaluationAttempt(Record):
    case_id: Nonempty
    attempt: Annotated[int, Field(ge=1, le=3)]
    release_id: Nonempty
    conversation_id: Nonempty
    result: Literal["pass", "fail", "timeout", "technical_failure", "not_run"]
    material_criteria_passed: bool
    essential_evidence_complete: bool
    critical_failures: tuple[Nonempty, ...]
    artifact_sha256: Hash
