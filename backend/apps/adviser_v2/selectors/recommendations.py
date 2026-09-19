"""Owner-scoped recommendation serialization queries."""

from __future__ import annotations

import uuid
from typing import Any

from ..models import (
    InformationNeed,
    PolicyCandidateAssessment,
    PolicyRequirementMatch,
    Recommendation,
    RecommendationCitation,
    RecommendationStatement,
)
from ..release_scope import comparison_product_count


def recommendation_payload(owner_id: uuid.UUID, recommendation_id: uuid.UUID) -> dict[str, Any]:
    recommendation = Recommendation.objects.select_related(
        "profile_revision", "knowledge_release"
    ).get(pk=recommendation_id, owner_id=owner_id)
    candidates = list(
        PolicyCandidateAssessment.objects.filter(owner_id=owner_id, recommendation=recommendation)
        .select_related("product_variant__policy_version__product__insurer", "quote")
        .order_by("rank", "created_at")
    )
    candidate_ids = [item.id for item in candidates]
    matches = list(
        PolicyRequirementMatch.objects.filter(
            owner_id=owner_id, candidate_assessment_id__in=candidate_ids
        ).select_related("customer_requirement")
    )
    matches_by_candidate: dict[uuid.UUID, list[dict[str, Any]]] = {
        item.id: [] for item in candidates
    }
    for match in matches:
        matches_by_candidate[match.candidate_assessment_id].append(
            {
                "id": str(match.id),
                "requirement_id": str(match.customer_requirement_id),
                "criterion": match.customer_requirement.criterion,
                "priority": match.customer_requirement.priority,
                "outcome": match.outcome,
                "comparison_value": match.comparison_value,
            }
        )
    needs = list(InformationNeed.objects.filter(owner_id=owner_id, recommendation=recommendation))
    statements = list(
        RecommendationStatement.objects.filter(
            owner_id=owner_id, recommendation=recommendation
        ).order_by("ordinal")
    )
    statement_ids = [item.id for item in statements]
    citations = list(
        RecommendationCitation.objects.filter(
            owner_id=owner_id, recommendation_statement_id__in=statement_ids
        )
        .select_related(
            "evidence_span__page__original_file",
            "evidence_span__source_capture__document_version",
        )
        .order_by("recommendation_statement_id", "ordinal")
    )
    citations_by_statement: dict[uuid.UUID, list[dict[str, Any]]] = {
        item.id: [] for item in statements
    }
    for citation in citations:
        span = citation.evidence_span
        page = span.page
        capture = span.source_capture
        citations_by_statement[citation.recommendation_statement_id].append(
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
    product_count = comparison_product_count(recommendation.knowledge_release)
    return {
        "id": str(recommendation.id),
        "turn_id": str(recommendation.turn_id),
        "outcome": recommendation.outcome,
        "profile_revision": recommendation.profile_revision.revision,
        "knowledge_release_id": str(recommendation.knowledge_release_id),
        "catalogue_limit": product_count,
        "comparison_label": f"Only {product_count} reviewed products were compared.",
        "created_at": recommendation.created_at,
        "candidates": [
            {
                "id": str(candidate.id),
                "product_variant_id": str(candidate.product_variant_id),
                "product": candidate.product_variant.policy_version.product.name,
                "insurer": candidate.product_variant.policy_version.product.insurer.name,
                "uin": candidate.product_variant.policy_version.uin,
                "variant": candidate.product_variant.name,
                "disposition": candidate.disposition,
                "rank": candidate.rank,
                "evaluated_selection": candidate.evaluated_selection,
                "quote_id": str(candidate.quote_id) if candidate.quote_id else None,
                "requirement_matches": matches_by_candidate[candidate.id],
            }
            for candidate in candidates
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
                "candidate_assessment_id": (
                    str(item.candidate_assessment_id) if item.candidate_assessment_id else None
                ),
                "citations": citations_by_statement[item.id],
            }
            for item in statements
        ],
    }
