"""Pin source inventories and run the offline three-insurer release assessment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from research_workspace.release_gate import check_release_gate
from research_workspace.storage import digest, read_json, write_json

CRITERIA = (
    "age_eligibility",
    "family_composition",
    "sum_insured",
    "waiting_period",
    "exclusions",
    "selected_addons",
    "price",
)


def assess(
    star_source: dict[str, Any],
    star_audit: dict[str, Any],
    links: dict[str, Any],
    other_audit: dict[str, Any],
    source_hashes: dict[str, str],
) -> dict[str, Any]:
    """Account for listed products while refusing to invent variant-level facts."""
    care_candidates = other_audit["care_roster"]["wording_derived_candidates"]
    niva_roster = other_audit.get("niva_roster")
    catalogues = [
        {
            "insurer_id": "star",
            "source_sha256": source_hashes["star_source"],
            "source_roster_complete": False,
            "products": [
                {
                    "uin": item["uin"],
                    "name": item["name"],
                    "scope": "review_pending",
                    "scope_reviewed": False,
                    "scope_evidence": item.get("scope_evidence"),
                    "scope_candidate": item["comparison_scope"],
                    "variants": [],
                }
                for item in star_source["products"]
            ],
        },
        {
            "insurer_id": "care",
            "source_sha256": source_hashes["links"],
            "source_roster_complete": False,
            "products": [
                {
                    "uin": item["uin_candidate"],
                    "name": item["source_label"],
                    "scope": "review_pending",
                    "scope_reviewed": False,
                    "scope_evidence": item["source_url"],
                    "scope_candidate": item["comparison_scope_candidate"],
                    "variants": [],
                }
                for item in care_candidates
            ],
        },
        {
            "insurer_id": "niva",
            "source_sha256": niva_roster.get("source_sha256") if niva_roster else None,
            "source_roster_complete": False,
            "products": [
                {
                    "uin": item["uin"],
                    "name": item["name_as_listed"],
                    "scope": "review_pending",
                    "scope_reviewed": False,
                    "scope_evidence": niva_roster["source_url"],
                    "scope_candidate": item["comparison_scope_candidate"],
                    "variants": [],
                }
                for item in niva_roster["products"]
            ]
            if niva_roster
            else [],
        },
    ]
    heldout = {
        "cases_scored": 0,
        "independent": False,
        "frozen_before_implementation": False,
        "frozen_set_sha256": None,
        "scoring_report_sha256": None,
        "material_criteria_passed": False,
        "essential_evidence_complete": False,
        "decision_critical_errors": None,
        "cross_account_leakage": None,
        "privacy_tests_run": False,
        "purchase_direction": None,
        "neutral_wording_reviewed": False,
        "status": "not_frozen_or_run",
    }
    gate = check_release_gate(catalogues, list(CRITERIA), [], heldout)
    blockers = [
        "Star edition and applicability review remains unresolved.",
        "Care independent UIN roster and scope review remain unresolved.",
        "Care proposal-form download page has not been fully inventoried.",
        "Niva roster currentness, scope, variants and option review remain unresolved.",
        "No variant-by-criterion matrix or independently scored held-out set exists.",
        "BM25 and MiniLM retrieval have not been qualified on reviewed policy evidence.",
    ]
    capture_counts = other_audit["capture_status_counts"]
    captured = capture_counts.get("acquired", 0) + capture_counts.get(
        "acquired_with_trailing_html", 0
    )
    if captured < len(links["documents"]):
        blockers.append("Some Care or Niva official document links were not captured successfully.")
    if capture_counts.get("acquired_with_trailing_html", 0):
        blockers.append("Mixed PDF and HTML responses require source review before policy use.")
    if (
        star_audit.get("release_ready") is not False
        or other_audit.get("release_ready") is not False
    ):
        blockers.append("Source audit readiness is inconsistent with unresolved review state.")
    manifest = {
        "format_version": 1,
        "status": "blocked_research_candidate",
        "insurer_ids": ["star", "care", "niva"],
        "source_sha256": source_hashes,
        "criteria": list(CRITERIA),
        "insurer_roster_counts": {item["insurer_id"]: len(item["products"]) for item in catalogues},
        "price_status": "unavailable_without_current_chart_or_verified_quote",
        "variant_inventory_complete": False,
        "customer_release_authorized": False,
    }
    manifest["manifest_sha256"] = digest(json.dumps(manifest, sort_keys=True).encode())
    return {
        "manifest": manifest,
        "release_ready": False,
        "gate": gate,
        "heldout": heldout,
        "blockers": blockers,
        "catalogues": catalogues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--star-source", required=True, type=Path)
    parser.add_argument("--star-audit", required=True, type=Path)
    parser.add_argument("--links", required=True, type=Path)
    parser.add_argument("--other-audit", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    paths = {
        "star_source": args.star_source,
        "star_audit": args.star_audit,
        "links": args.links,
        "other_audit": args.other_audit,
    }
    report = assess(
        *(read_json(paths[name]) for name in paths),
        {name: digest(path.read_bytes()) for name, path in paths.items()},
    )
    write_json(args.output, report)
    print(
        json.dumps(
            {
                "release_ready": report["release_ready"],
                "manifest_sha256": report["manifest"]["manifest_sha256"],
                "gate_blockers": len(report["gate"]["blockers"]),
            }
        )
    )


if __name__ == "__main__":
    main()
