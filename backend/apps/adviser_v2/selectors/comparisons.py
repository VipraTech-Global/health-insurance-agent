"""Owner-scoped comparison serialization queries."""

from __future__ import annotations

import uuid
from typing import Any

from ..models import (
    Comparison,
    ComparisonCitation,
    ComparisonStatement,
    InformationNeed,
    PolicyComparisonAssessment,
    PolicyRequirementMatch,
)
from ..release_scope import comparison_product_count


def comparison_payload(owner_id: uuid.UUID, comparison_id: uuid.UUID) -> dict[str, Any]:
    comparison = Comparison.objects.select_related("profile_revision", "knowledge_release").get(
        pk=comparison_id, owner_id=owner_id
    )
    assessments = list(
        PolicyComparisonAssessment.objects.filter(owner_id=owner_id, comparison=comparison)
        .select_related("product_variant__policy_version__product__insurer", "quote")
        .order_by(
            "product_variant__policy_version__product__insurer__name",
            "product_variant__policy_version__product__name",
            "product_variant__policy_version__uin",
            "product_variant_id",
        )
    )
    assessment_ids = [item.id for item in assessments]
    matches = list(
        PolicyRequirementMatch.objects.filter(
            owner_id=owner_id, comparison_assessment_id__in=assessment_ids
        )
        .select_related("customer_requirement")
        .order_by("customer_requirement__criterion", "customer_requirement_id")
    )
    matches_by_assessment: dict[uuid.UUID, list[dict[str, Any]]] = {
        item.id: [] for item in assessments
    }
    for match in matches:
        matches_by_assessment[match.comparison_assessment_id].append(
            {
                "id": str(match.id),
                "requirement_id": str(match.customer_requirement_id),
                "criterion": match.customer_requirement.criterion,
                "priority": match.customer_requirement.priority,
                "outcome": match.outcome,
                "comparison_value": match.comparison_value,
            }
        )
    needs = list(InformationNeed.objects.filter(owner_id=owner_id, comparison=comparison))
    statements = list(
        ComparisonStatement.objects.filter(owner_id=owner_id, comparison=comparison).order_by(
            "ordinal"
        )
    )
    statement_ids = [item.id for item in statements]
    citations = list(
        ComparisonCitation.objects.filter(
            owner_id=owner_id, comparison_statement_id__in=statement_ids
        )
        .select_related(
            "evidence_span__page__original_file",
            "evidence_span__source_capture__document_version",
        )
        .order_by("comparison_statement_id", "ordinal")
    )
    citations_by_statement: dict[uuid.UUID, list[dict[str, Any]]] = {
        item.id: [] for item in statements
    }
    for citation in citations:
        span = citation.evidence_span
        page = span.page
        capture = span.source_capture
        citations_by_statement[citation.comparison_statement_id].append(
            {
                "id": str(citation.id),
                "evidence_span_id": str(span.id),
                "policy_rule_id": str(citation.policy_rule_id) if citation.policy_rule_id else None,
                "role": citation.role,
                "quote": span.quote,
                "section_label": span.section_label,
                "page": page.page_number if page is not None else None,
                "document_version_id": (
                    str(capture.document_version_id)
                    if capture is not None and capture.document_version_id
                    else None
                ),
                "locator": span.locator,
            }
        )
    match_assessment = {match.id: match.comparison_assessment_id for match in matches}
    statements_by_assessment: dict[uuid.UUID, list[ComparisonStatement]] = {
        item.id: [] for item in assessments
    }
    for statement in statements:
        assessment_id = statement.comparison_assessment_id
        if assessment_id is None and statement.requirement_match_id is not None:
            assessment_id = match_assessment.get(statement.requirement_match_id)
        if assessment_id in statements_by_assessment:
            statements_by_assessment[assessment_id].append(statement)
    product_count = comparison_product_count(comparison.knowledge_release)
    return {
        "id": str(comparison.id),
        "turn_id": str(comparison.turn_id),
        "outcome": comparison.outcome,
        "profile_revision": comparison.profile_revision.revision,
        "knowledge_release_id": str(comparison.knowledge_release_id),
        "catalogue_limit": product_count,
        "comparison_label": f"Only {product_count} reviewed products were compared.",
        "created_at": comparison.created_at,
        "products": [
            {
                "id": str(assessment.id),
                "product_variant_id": str(assessment.product_variant_id),
                "product": assessment.product_variant.policy_version.product.name,
                "insurer": assessment.product_variant.policy_version.product.insurer.name,
                "uin": assessment.product_variant.policy_version.uin,
                "variant": assessment.product_variant.name,
                "evaluated_selection": assessment.evaluated_selection,
                "quote_id": str(assessment.quote_id) if assessment.quote_id else None,
                "criteria": matches_by_assessment[assessment.id],
                "evidence_gaps": [
                    {
                        "requirement_id": item["requirement_id"],
                        "criterion": item["criterion"],
                        "outcome": item["outcome"],
                    }
                    for item in matches_by_assessment[assessment.id]
                    if item["outcome"] in {"unknown", "partly_meets"}
                ],
                "restrictions": [
                    {
                        "statement_id": str(statement.id),
                        "text": statement.text,
                        "citations": citations_by_statement[statement.id],
                    }
                    for statement in statements_by_assessment[assessment.id]
                    if statement.statement_type == "restriction"
                ],
                "evidence": [
                    citation
                    for statement in statements_by_assessment[assessment.id]
                    for citation in citations_by_statement[statement.id]
                ],
            }
            for assessment in assessments
        ],
        "information_needs": [
            {
                "id": str(item.id),
                "need_kind": item.need_kind,
                "information_key": item.information_key,
                "reason": item.reason,
                "priority": item.priority,
                "status": item.status,
            }
            for item in needs
        ],
        "statements": [
            {
                "id": str(item.id),
                "ordinal": item.ordinal,
                "text": item.text,
                "statement_type": item.statement_type,
                "critical": item.critical,
                "support_status": item.support_status,
                "comparison_assessment_id": (
                    str(item.comparison_assessment_id) if item.comparison_assessment_id else None
                ),
                "citations": citations_by_statement[item.id],
            }
            for item in statements
        ],
    }
