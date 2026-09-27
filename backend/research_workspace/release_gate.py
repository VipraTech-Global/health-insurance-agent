"""Data-only gate for a future neutral, multi-insurer catalogue release.

This is an offline contract check. Passing it does not publish a release or
replace independent insurance review, retrieval evaluation, or runtime checks.
"""

from __future__ import annotations

from collections import Counter
from typing import Any
from urllib.parse import urlsplit

OUTCOMES = {"meets", "partly_meets", "does_not_meet", "unknown", "not_applicable"}
SUPPORTED = {"meets", "partly_meets", "does_not_meet"}
FORBIDDEN_OUTPUT_KEYS = {"rank", "score", "winner", "recommendation", "selected_policy"}


def check_release_gate(
    catalogues: list[dict[str, Any]],
    criteria: list[str],
    cells: list[dict[str, Any]],
    heldout: dict[str, Any],
) -> dict[str, Any]:
    """Account for every listed product, included variant and comparison cell."""
    blockers: list[str] = []
    insurer_ids = [item.get("insurer_id") for item in catalogues]
    if len(set(insurer_ids)) < 2 or len(insurer_ids) != len(set(insurer_ids)):
        blockers.append("at_least_two_distinct_insurers_required")
    if not criteria or len(criteria) != len(set(criteria)):
        blockers.append("criteria_missing_or_duplicated")
    expected: set[tuple[str, str, str]] = set()
    document_hashes_by_variant: dict[tuple[str, str], set[str]] = {}
    for insurer in catalogues:
        insurer_id = insurer.get("insurer_id")
        roster = insurer.get("products", [])
        if insurer.get("source_roster_complete") is not True or not _sha(
            insurer.get("source_sha256")
        ):
            blockers.append(f"{insurer_id}:official_roster_unverified")
        if not roster:
            blockers.append(f"{insurer_id}:empty_product_roster")
        identities = [row.get("uin") for row in roster]
        if len(identities) != len(set(identities)):
            blockers.append(f"{insurer_id}:duplicate_product")
        for product in roster:
            uin = product.get("uin")
            scope = product.get("scope")
            if product.get("scope_reviewed") is not True or not product.get("scope_evidence"):
                blockers.append(f"{insurer_id}:{uin}:scope_review_unverified")
            if scope == "excluded":
                if not product.get("exclusion_reason") or not product.get("scope_evidence"):
                    blockers.append(f"{insurer_id}:{uin}:unsupported_exclusion")
                continue
            if scope != "included":
                blockers.append(f"{insurer_id}:{uin}:scope_unresolved")
                continue
            variants = product.get("variants", [])
            if not product.get("variant_inventory_complete") or not variants:
                blockers.append(f"{insurer_id}:{uin}:variant_inventory_incomplete")
            variant_ids = [item.get("id") for item in variants]
            if len(variant_ids) != len(set(variant_ids)) or not all(variant_ids):
                blockers.append(f"{insurer_id}:{uin}:variant_identity_invalid")
            for variant in variants:
                variant_id = variant.get("id")
                if not variant_id:
                    continue
                expected.update((insurer_id, variant_id, criterion) for criterion in criteria)
                if not variant.get("option_inventory_complete"):
                    blockers.append(f"{insurer_id}:{variant_id}:option_inventory_incomplete")
                docs = variant.get("documents", [])
                document_hashes_by_variant[(insurer_id, variant_id)] = {
                    item["sha256"] for item in docs if _sha(item.get("sha256"))
                }
                roles = {
                    item.get("role") for item in docs if item.get("state") == "verified_applicable"
                }
                if not {"policy_wording", "customer_information_sheet", "prospectus"}.issubset(
                    roles
                ):
                    blockers.append(f"{insurer_id}:{variant_id}:required_documents_unverified")
                if any(item.get("state") != "verified_applicable" for item in docs):
                    blockers.append(f"{insurer_id}:{variant_id}:document_unresolved")
                if any(not _verified_document(item) for item in docs):
                    blockers.append(f"{insurer_id}:{variant_id}:document_provenance_incomplete")
                if not variant.get("restriction_inventory_complete"):
                    blockers.append(f"{insurer_id}:{variant_id}:restriction_inventory_incomplete")
    observed = Counter(
        (cell.get("insurer_id"), cell.get("variant_id"), cell.get("criterion")) for cell in cells
    )
    for key in expected:
        if observed[key] != 1:
            blockers.append("missing_or_duplicate_comparison_cell")
            break
    if set(observed) - expected:
        blockers.append("unexpected_comparison_cell")
    for cell in cells:
        outcome = cell.get("outcome")
        if outcome not in OUTCOMES:
            blockers.append("invalid_outcome")
        if FORBIDDEN_OUTPUT_KEYS.intersection(cell):
            blockers.append("ranking_or_selection_field_present")
        if outcome in SUPPORTED and not cell.get("required_evidence_complete"):
            blockers.append("supported_cell_lacks_complete_evidence")
        if outcome in SUPPORTED:
            evidence = cell.get("evidence")
            hashes = document_hashes_by_variant.get(
                (cell.get("insurer_id"), cell.get("variant_id")), set()
            )
            if (
                not isinstance(evidence, list)
                or not evidence
                or any(
                    not isinstance(ref, dict)
                    or ref.get("source_sha256") not in hashes
                    or type(ref.get("page")) is not int
                    or ref["page"] < 1
                    or not ref.get("quote")
                    for ref in evidence
                )
            ):
                blockers.append("supported_cell_evidence_packet_invalid")
        if cell.get("criterion") == "price" and outcome in SUPPORTED:
            if cell.get("price_source_role") not in {
                "verified_quote",
                "current_premium_chart",
            } or not cell.get("price_observed_at"):
                blockers.append("price_without_current_verified_source")
        if outcome == "unknown" and not cell.get("unresolved_reason"):
            blockers.append("unknown_cell_lacks_reason")
        if outcome == "not_applicable" and not cell.get("predicate_version"):
            blockers.append("unversioned_not_applicable")
    if heldout.get("cases_scored", 0) < 1:
        blockers.append("heldout_assessment_missing")
    if heldout.get("independent") is not True:
        blockers.append("heldout_independence_unverified")
    if heldout.get("material_criteria_passed") is not True:
        blockers.append("heldout_material_criteria_unverified")
    if heldout.get("essential_evidence_complete") is not True:
        blockers.append("heldout_evidence_unverified")
    if not any(cell.get("outcome") in SUPPORTED for cell in cells):
        blockers.append("comparison_has_no_supported_cells")
    if heldout.get("decision_critical_errors") != 0:
        blockers.append("heldout_decision_critical_errors")
    if heldout.get("cross_account_leakage") is not False:
        blockers.append("cross_account_boundary_unverified")
    if heldout.get("purchase_direction") is not False:
        blockers.append("purchase_direction_unverified")
    return {
        "ready": not blockers,
        "blockers": sorted(set(blockers)),
        "expected_cells": len(expected),
    }


def _sha(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(char in "0123456789abcdef" for char in value)
    )


def _verified_document(item: dict[str, Any]) -> bool:
    url = item.get("url")
    return (
        item.get("state") == "verified_applicable"
        and _sha(item.get("sha256"))
        and isinstance(url, str)
        and urlsplit(url).scheme == "https"
        and bool(item.get("captured_at"))
        and item.get("edition_verified") is True
        and bool(item.get("applicability_evidence"))
    )
