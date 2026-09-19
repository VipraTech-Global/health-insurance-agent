"""Published-catalogue and readiness queries."""

from __future__ import annotations

from collections import defaultdict
from typing import Any

from django.db.models import Count

from ..models import (
    KnowledgeChannel,
    KnowledgeReleaseRule,
    PolicyVersion,
    PolicyVersionDocument,
    ProcessingJob,
    Product,
)
from ..release_scope import FIVE_PRODUCT_COUNT, comparison_product_count


def catalogue_readiness(channel_name: str = "live") -> dict[str, Any]:
    channel = (
        KnowledgeChannel.objects.select_related("current_release").filter(name=channel_name).first()
    )
    release = channel.current_release if channel else None
    comparison_count = comparison_product_count(release) if release is not None else 0
    products = list(Product.objects.select_related("insurer").order_by("insurer__name", "name"))
    published_rule_product_ids: set[object] = set()
    rule_counts: dict[object, int] = defaultdict(int)
    category_readiness: dict[str, dict[str, Any]] = {}
    if release is not None:
        rows = (
            KnowledgeReleaseRule.objects.filter(knowledge_release=release)
            .values("policy_rule__policy_version__product_id")
            .annotate(total=Count("id"))
        )
        for row in rows:
            product_id = row["policy_rule__policy_version__product_id"]
            published_rule_product_ids.add(product_id)
            rule_counts[product_id] = row["total"]
        category_readiness = {
            str(item.get("policy_version_id")): item
            for item in release.readiness.get("products", [])
            if isinstance(item, dict) and item.get("policy_version_id")
        }
    items: list[dict[str, Any]] = []
    for product in products:
        versions = PolicyVersion.objects.filter(product=product).order_by("-created_at")
        current = versions.filter(publication_status="published").first() or versions.first()
        documents: list[PolicyVersionDocument] = []
        if current:
            documents = list(
                PolicyVersionDocument.objects.filter(policy_version=current).select_related(
                    "document_version"
                )
            )
        document_version_ids = [item.document_version_id for item in documents]
        jobs = (
            ProcessingJob.objects.filter(
                source_capture__document_version_id__in=document_version_ids
            )
            if current
            else ProcessingJob.objects.none()
        )
        coverage = category_readiness.get(str(current.id), {}) if current else {}
        unresolved_material_jobs = sum(
            1
            for job in jobs.only("state", "issues")
            if job.state in {"failed", "blocked"}
            or any(
                isinstance(issue, dict)
                and issue.get("material") is True
                and issue.get("resolved") is False
                for issue in job.issues
            )
        )
        items.append(
            {
                "id": str(product.id),
                "name": product.name,
                "insurer": product.insurer.name,
                "uin": current.uin if current else None,
                "version_id": str(current.id) if current else None,
                "publication_status": current.publication_status if current else "missing",
                "document_count": len(documents),
                "required_documents": sum(1 for item in documents if item.required_for_policy),
                "rule_count": rule_counts[product.id],
                "covered_inventory_categories": coverage.get("covered_inventory_categories", []),
                "missing_inventory_categories": coverage.get("missing_inventory_categories", []),
                "unresolved_material_jobs": unresolved_material_jobs,
                "included_in_current_release": product.id in published_rule_product_ids,
            }
        )
    included_count = sum(1 for item in items if item["included_in_current_release"])
    comparison_label = (
        f"Development demo: {comparison_count} of {FIVE_PRODUCT_COUNT} products available."
        if release is not None and comparison_count < FIVE_PRODUCT_COUNT
        else "Development alpha: five products with incomplete knowledge."
    )
    warning = (
        f"This demo compares only {comparison_count} of {FIVE_PRODUCT_COUNT} planned products. "
        "Missing products and categories are unknown, not evidence of coverage or exclusion. "
        "Eligibility remains conditional unless verified."
        if release is not None and comparison_count < FIVE_PRODUCT_COUNT
        else (
            "This comparison is incomplete. Missing categories are unknown, not evidence of "
            "coverage or exclusion. Eligibility remains conditional unless verified."
        )
    )
    return {
        "catalogue_limit": comparison_count,
        "comparison_label": comparison_label,
        "warning": warning,
        "channel": channel_name,
        "generation": channel.generation if channel else 0,
        "release": (
            {
                "id": str(release.id),
                "number": release.release_number,
                "state": release.state,
                "label": release.release_label,
                "published_at": release.published_at,
                "manifest_sha256": release.manifest_sha256,
            }
            if release
            else None
        ),
        "ready": (
            release is not None
            and release.state == "published"
            and included_count == comparison_count
        ),
        "incomplete_comparison": True,
        "products": items,
        "blocking_reason": None if release else "No knowledge release is published.",
    }
