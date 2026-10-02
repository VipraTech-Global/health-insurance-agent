"""Plan-scoped free answers, independently reviewed within the qualified fact contract.

These descriptive answers never enter the deterministic rule engine. The packet,
local checks and independent review are replayed before comparison publication.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.utils import timezone
from research_workspace.legacy_relay import RelayFailure

from .evidence_retrieval import EvidencePacket
from .model_gateway import call_model
from .models import PolicyVersion
from .processing.cited_facts import (
    FACT_SYSTEM,
    REVIEW_SYSTEM,
    anchor_transcribed_quotes,
    carrier_fact,
    clause_offsets,
    fact_instruction,
    fact_problems,
    omit_secondary_statements,
    review_disposition,
)
from .processing.clause_citations import store_clause
from .processing.criterion_attempts import TRANSPORT_FAILURES
from .processing.criterion_evidence import Criterion, quoted_quantities, request_bytes_with_headroom
from .processing.manifest_v2 import raw_bundle_passages
from .schemas import ComparisonDraftV1, PolicyRuleExtractionV1, PolicyRuleReviewV1


def question_criterion(question: str) -> Criterion:
    return Criterion(
        "coverage_question",
        "coverage",
        "Answer ONLY for the single policy_version_id in this packet. The application combines separate per-plan answers, so a request about three policies does not require the other policies in this call. Customer question: "
        + question,
    )


@dataclass(frozen=True)
class SourceAnswer:
    packet: EvidencePacket
    criterion: Criterion
    extraction: PolicyRuleExtractionV1 | None
    reviewed_extraction: PolicyRuleExtractionV1 | None
    review: PolicyRuleReviewV1 | None
    unknown_reason: str | None


def packet_pages(packet: EvidencePacket) -> list[dict[str, Any]]:
    pages = raw_bundle_passages(
        PolicyVersion.objects.get(pk=packet.policy_version_id), include_prospectus=True
    )
    ids = {s["page_span_id"] for c in packet.chunks for s in c.segments}
    return [p for p in pages if p["evidence_span_id"] in ids]


def source_problems(answer: SourceAnswer) -> list[str]:
    if answer.extraction is None:
        return [] if answer.unknown_reason else ["Missing answer and unknown reason."]
    if answer.review is None or answer.reviewed_extraction is None:
        return ["Independent source review is missing."]
    pages = packet_pages(answer.packet)
    problems = fact_problems(
        answer.packet.policy_version_id, answer.criterion, answer.extraction, pages
    )
    problems.extend(answer.extraction.material_issues)
    if answer.unknown_reason:
        problems.append("A supported answer cannot also carry an unresolved reason.")
    problems.extend(
        review_disposition(answer.review, answer.reviewed_extraction, answer.criterion)[0]
    )
    projected = omit_secondary_statements(
        answer.review, answer.reviewed_extraction, answer.criterion
    )
    if projected != answer.extraction:
        problems.append("Published answer differs from the independently reviewed candidate.")
    if not answer.extraction.rules:
        return problems + ["No supported source answer."]
    fact = carrier_fact(answer.extraction.rules[0])
    prose = " ".join(
        [
            fact.value,
            *(c.text for c in fact.conditions),
            *(s.text for s in fact.secondary_statements),
        ]
    )
    from .services.comparisons import _ENDORSEMENT_LANGUAGE

    banned = _ENDORSEMENT_LANGUAGE.search(prose)
    if banned:
        problems.append(
            f"Neutral wording check: prose contains {banned.group()!r}. Keep exact quotes unchanged, but describe policy conditions without ranking or endorsement words (including medically contextual uses of 'better')."
        )
    quoted = quoted_quantities(" ".join(c.quote for c in fact.citations))
    for unit, values in quoted_quantities(prose).items():
        if not values.issubset(quoted[unit]):
            problems.append(f"Answer prose contains unsupported {unit} quantities.")
    by_id = {p["evidence_span_id"]: p for p in pages}
    for clause in carrier_fact(answer.extraction.rules[0]).citations:
        try:
            start, end = clause_offsets(clause, by_id[clause.page_span_id]["passage"])
            intervals = sorted(
                (s["start"], s["end"])
                for c in answer.packet.chunks
                for s in c.segments
                if s["page_span_id"] == clause.page_span_id
            )
            cursor = start
            for left, right in intervals:
                if left <= cursor < right:
                    cursor = right
            if cursor < end:
                problems.append("The quoted clause is outside the retrieved text segments.")
        except (KeyError, ValueError) as exc:
            problems.append(str(exc))
    return problems


def _relay(turn, *, model, schema_name, output_type, messages, effort):
    request_bytes_with_headroom(model, messages, output_type.model_json_schema())
    for attempt in range(3):
        try:
            return call_model(
                model=model,
                schema_name=schema_name,
                output_type=output_type,
                messages=messages,
                turn=turn,
                remaining_seconds=max(0, (turn.deadline - timezone.now()).total_seconds()),
                reasoning_effort=effort,
                max_output_tokens=8192,
            )
        except RelayFailure as exc:
            if exc.code not in TRANSPORT_FAILURES or attempt == 2:
                raise
    raise AssertionError("Unreachable relay retry state")


def answer_question(turn, question: str, profile: dict, packet: EvidencePacket) -> SourceAnswer:
    criterion = question_criterion(question)
    if packet.unavailable_reason or not packet.chunks:
        return SourceAnswer(packet, criterion, None, None, None,
            packet.unavailable_reason or "No applicable original evidence fit the source packet.")
    pages = packet_pages(packet)
    failure = "The retrieved evidence is incomplete for this question."
    packet_data = packet.payload()
    # The originals occur only once. Each segment carries its physical page and
    # original character offsets; no whole page is smuggled past the token budget.
    for chunk in packet_data["chunks"]:
        chunk.pop("text")
    evidence = json.dumps(packet_data, ensure_ascii=False)
    shared = [
        {
            "role": "system",
            "content": FACT_SYSTEM
            + " Supplied evidence is a bounded retrieval packet, not the whole bundle. Never infer absence from an omitted page. Do not infer personal eligibility or a claim outcome. Keep the answer below 2000 characters, including conditions. All measured quantities (amounts, percentages, durations and counts) must have quantities entries and quoted support. Statute years, clause numbers and policy identifiers are identifiers, not measured quantities: retain their exact source-supported text but never encode an Act dated 1994 as a duration of 1994 years. In plain-English value and conditions, avoid endorsement or comparison words such as better, best, recommend, choose, buy, purchase, select. For example paraphrase ambulance transfer for better medical treatment as transfer for improved medical treatment; do not narrow it to a higher level or specialist treatment. Preserve the original meaning and breadth of every condition; the supporting quote must retain the exact original wording. Quote each enumerated hospital condition or bullet SEPARATELY, starting after its bullet/control marker. Never combine a., b., c. bullet items into one quote: raw U+0007 control characters between items are NOT whitespace and must not be silently removed. Each quote should be one clause, not a reconstructed paragraph.",
        },
        {"role": "system", "content": evidence},
    ]
    for correction in range(2):
        messages = shared + [
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "policy_version_id": packet.policy_version_id,
                        "criterion_instruction": fact_instruction(criterion),
                        "customer_profile": profile,
                        "retry_context": failure if correction else None,
                    },
                    default=str,
                ),
            }
        ]
        try:
            candidate = _relay(
                turn,
                model=settings.COVERGUIDE_POLICY_EXTRACTION_MODEL,
                schema_name="policy_extraction",
                output_type=PolicyRuleExtractionV1,
                messages=messages,
                effort=settings.COVERGUIDE_POLICY_EXTRACTION_REASONING_EFFORT,
            )
            candidate, _changes = anchor_transcribed_quotes(criterion, candidate, pages)
            problems = fact_problems(packet.policy_version_id, criterion, candidate, pages)
            if candidate.material_issues or not candidate.rules:
                return SourceAnswer(
                    packet,
                    criterion,
                    None,
                    None,
                    None,
                    "Retrieved evidence incomplete: "
                    + "; ".join(candidate.material_issues or ["No supported clause was returned."]),
                )
            if problems:
                failure = "; ".join(problems)
                continue
            messages = [
                {
                    "role": "system",
                    "content": REVIEW_SYSTEM
                    + " Review only the bounded packet. Do not demand unrelated benefits. Reject any personal computed outcome. Check every measured amount, percentage, duration and count against the quoted clause; missing quantity entries for these are a material error. Statute years, clause numbers and policy identifiers require exact quoted support, but are identifiers rather than measured quantities.",
                },
                {"role": "system", "content": evidence},
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "criterion": criterion.__dict__,
                            "candidate": candidate.model_dump(mode="json"),
                        }
                    ),
                },
            ]
            review = _relay(
                turn,
                model=settings.COVERGUIDE_POLICY_REVIEW_MODEL,
                schema_name="policy_review",
                output_type=PolicyRuleReviewV1,
                messages=messages,
                effort="high",
            )
            projected = omit_secondary_statements(review, candidate, criterion)
            answer = SourceAnswer(packet, criterion, projected, candidate, review, None)
            problems = source_problems(answer)
            if not problems:
                # Geometry is also a publication requirement, not a deferred UI guess.
                _source_statement(answer, "validation", "validation")
                return answer
            failure = "; ".join(problems)
        except RelayFailure as exc:
            if exc.code in TRANSPORT_FAILURES:
                return SourceAnswer(
                    packet,
                    criterion,
                    None,
                    None,
                    None,
                    "Evidence answer unavailable after separate transport retries: " + exc.code,
                )
            failure = "The answer did not validate: " + exc.code
        except ValueError as exc:
            failure = "The source citation did not validate: " + str(exc)
    return SourceAnswer(
        packet,
        criterion,
        None,
        None,
        None,
        "Retrieved evidence incomplete after validation: " + failure,
    )


def _source_statement(answer: SourceAnswer, assessment_id: str, name: str) -> dict:
    fact = carrier_fact(answer.extraction.rules[0])
    pages = {p["evidence_span_id"]: p for p in packet_pages(answer.packet)}
    spans = [store_clause(c, pages[c.page_span_id]) for c in fact.citations]
    text = (
        name
        + ": "
        + " ".join(
            [
                fact.value,
                *(c.text for c in fact.conditions),
                *(s.text for s in fact.secondary_statements),
            ]
        )
    )
    if len(text) > 4000:
        raise ValueError("The answer exceeded the compact statement contract.")
    return {
        "text": text,
        "statement_type": "benefit",
        "comparison_assessment_id": assessment_id,
        "requirement_match_id": None,
        "calculation_id": None,
        "citations": [
            {"evidence_span_id": str(s.id), "policy_rule_id": None, "role": "supports"}
            for s in spans
        ],
    }


def source_draft(context, answers: tuple[SourceAnswer, ...]) -> ComparisonDraftV1:
    from .prepared_facts import FACT_RELEASE_VERSION, facts_for_release

    release = context.comparison.knowledge_release
    if release.readiness.get("fact_release_version") != FACT_RELEASE_VERSION:
        raise ValueError("Prepared fact publication requires the matching release protocol.")
    facts = facts_for_release(release)
    assessments = {str(a.product_variant.policy_version_id): a for a in context.assessments}
    if set(facts) != set(assessments):
        raise ValueError("Prepared comparison does not account for every released plan.")
    if answers and (
        len(answers) != len(facts) or {a.packet.policy_version_id for a in answers} != set(facts)
    ):
        raise ValueError("Free answers must account for each plan exactly once.")
    statements = []
    for answer in answers:
        problems = source_problems(answer)
        if problems:
            raise ValueError("; ".join(problems))
        if answer.extraction is not None:
            assessment = assessments[answer.packet.policy_version_id]
            statements.append(
                _source_statement(
                    answer,
                    str(assessment.id),
                    assessment.product_variant.policy_version.product.name,
                )
            )
    return ComparisonDraftV1(schema_version=1, statements=statements)


def source_unknowns(context, answers) -> list[tuple[Any, str]]:
    assessments = {str(a.product_variant.policy_version_id): a for a in context.assessments}
    return [
        (assessments[a.packet.policy_version_id], a.unknown_reason)
        for a in answers
        if a.unknown_reason
    ]


def needs_source_retrieval(question: str, intent: str) -> bool:
    """Prepared comparisons need no retrieval; other coverage questions fail open to search."""
    import re

    outside = r"ambulance|ayush|organ|donor|consumable|non.?medical|modern treatment|dialysis|cataract|domiciliary|hospital cash|bariatric|dental|outpatient"
    if re.search(outside, question, re.IGNORECASE):
        return True
    if intent != "coverage_question":
        return False
    prepared = r"sum insured|room|co.?pay|deductible|pre.?existing|PED\b|waiting|maternity|newborn|restor|family size|family composition|floater|portab|geograph|eligib|entry age"
    return re.search(prepared, question, re.IGNORECASE) is None
