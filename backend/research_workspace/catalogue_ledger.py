"""Account for three-insurer products and public documents without claiming applicability.

The ledger indexes discovery evidence. A UIN or source label is only an identity
lead, so every variant, option, edition, and document bundle stays unreviewed.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from research_workspace.star_catalogue import PRODUCTS_URL
from research_workspace.storage import digest, read_json, write_json
from research_workspace.three_insurer_catalogue import scope_lead

DOCUMENT_ROLE_CLASS = {
    "policy_wording": "coverage_candidate",
    "customer_information_sheet": "coverage_candidate",
    "prospectus": "coverage_candidate",
    "excluded_expenses": "supporting_schedule_candidate",
    "modern_treatment_schedule": "supporting_schedule_candidate",
    "preventive_health_schedule": "supporting_schedule_candidate",
    "other_support": "supporting_document_review_pending",
    "proposal_form": "underwriting_context",
    "proposal_form_translation": "underwriting_context",
    "proposal_form_index": "underwriting_context",
    "brochure": "marketing_context",
    "premium_chart": "price_context",
    "historical_wording": "historical_context",
    "withdrawn_document": "historical_context",
    "other_official_download": "role_review_pending",
}


def _product(
    insurer_id: str,
    uin: str,
    name: str,
    origin: str,
    scope_candidate: str,
    scope_reason: str,
) -> dict[str, Any]:
    return {
        "insurer_id": insurer_id,
        "uin": uin,
        "name_as_source": name,
        "origin": origin,
        "scope_candidate": scope_candidate,
        "scope_reason": scope_reason,
        "scope_reviewed": False,
        "variant_inventory": "unresolved",
        "option_inventory": "unresolved",
        "edition_reconciliation": "unresolved",
        "applicable_bundle_complete": False,
        "document_refs": [],
        "document_roles": {},
    }


def build_ledger(
    star_source: dict[str, Any],
    star_captures: dict[str, Any],
    other_audit: dict[str, Any],
    care_roster: dict[str, Any],
    niva_roster: dict[str, Any],
) -> dict[str, Any]:
    """Build a complete source-row index and a deliberately incomplete review ledger."""
    products: dict[str, dict[str, dict[str, Any]]] = {
        insurer: {} for insurer in ("star", "care", "niva")
    }
    for row in star_source["products"]:
        uin = row["uin"]
        if uin in products["star"]:
            raise ValueError(f"Duplicate Star roster UIN: {uin}")
        products["star"][uin] = _product(
            "star",
            uin,
            row["name"],
            "official_current_product_list",
            row["comparison_scope"],
            row["scope_reason"],
        )
        products["star"][uin]["source_row"] = row["source_row"]
        products["star"][uin]["source_url"] = PRODUCTS_URL
    for row in care_roster["products"]:
        uin = row["uin"]
        if uin in products["care"]:
            raise ValueError(f"Duplicate Care dated roster UIN: {uin}")
        scope, reason = scope_lead(row["name_as_listed"], uin)
        products["care"][uin] = _product(
            "care",
            uin,
            row["name_as_listed"],
            f"dated_2025_{row['roster_section']}_register",
            scope,
            reason,
        )
        products["care"][uin]["source_row"] = row["source_row"]
        products["care"][uin]["source_url"] = care_roster["source_url"]
    for row in niva_roster["products"]:
        uin = row["uin"]
        if uin in products["niva"]:
            raise ValueError(f"Duplicate Niva roster UIN: {uin}")
        scope, reason = scope_lead(row["name_as_listed"], uin)
        products["niva"][uin] = _product(
            "niva", uin, row["name_as_listed"], "official_product_list", scope, reason
        )
        products["niva"][uin]["source_row"] = row["source_row"]
        products["niva"][uin]["source_url"] = niva_roster["source_url"]

    # Current Care wordings expose newer UINs than the linked 2025 register.
    # Keep them as identity leads instead of silently omitting them.
    for row in other_audit["documents"]:
        if row["insurer_id"] != "care" or row["role"] != "policy_wording":
            continue
        for uin in row["first_two_page_uins"]:
            if uin not in products["care"]:
                scope, reason = scope_lead(row["label"], uin)
                products["care"][uin] = _product(
                    "care", uin, row["label"], "current_wording_identity_only", scope, reason
                )
                products["care"][uin]["source_url"] = row["source_page"]

    documents = []
    for index, row in enumerate(star_source["documents"]):
        capture = star_captures.get(row["url"], {})
        document = {
            "ref": f"star:{index}",
            "insurer_id": "star",
            "source_index": index,
            "source_register": "star_source",
            "role": row["role"],
            "role_class_candidate": DOCUMENT_ROLE_CLASS[row["role"]],
            "role_class_reviewed": False,
            "url": row["url"],
            "capture_status": capture.get("status", "not_attempted"),
            "sha256": capture.get("sha256"),
            "candidate_uins": sorted(
                set(row.get("candidate_product_uins", [])) & products["star"].keys()
            ),
            "association_basis": "source_label_or_uin_candidate",
        }
        documents.append(document)
    for index, row in enumerate(other_audit["documents"]):
        insurer_id = row["insurer_id"]
        document = {
            "ref": f"other:{index}",
            "insurer_id": insurer_id,
            "source_index": index,
            "source_register": "other_audit",
            "role": row["role"],
            "role_class_candidate": DOCUMENT_ROLE_CLASS[row["role"]],
            "role_class_reviewed": False,
            "url": row["url"],
            "capture_status": row["capture_status"],
            "sha256": row.get("sha256"),
            "candidate_uins": sorted(set(row["first_two_page_uins"]) & products[insurer_id].keys()),
            "association_basis": "first_two_page_uin_identity_only",
        }
        documents.append(document)

    role_counts: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    unassigned_refs: list[str] = []
    for document in documents:
        uins = document["candidate_uins"]
        if not uins:
            unassigned_refs.append(document["ref"])
        for uin in uins:
            product = products[document["insurer_id"]][uin]
            product["document_refs"].append(document["ref"])
            role_counts[(document["insurer_id"], uin)][document["role"]] += 1
    for insurer_id, by_uin in products.items():
        for uin, product in by_uin.items():
            product["document_roles"] = dict(sorted(role_counts[(insurer_id, uin)].items()))

    refs = {document["ref"] for document in documents}
    assigned = {
        ref for by_uin in products.values() for p in by_uin.values() for ref in p["document_refs"]
    }
    if assigned | set(unassigned_refs) != refs or assigned & set(unassigned_refs):
        raise ValueError("Source document accounting is incomplete")
    return {
        "format_version": 1,
        "status": "catalogue_review_incomplete",
        "catalogue_complete": False,
        "insurers": {
            insurer_id: sorted(by_uin.values(), key=lambda row: row["uin"])
            for insurer_id, by_uin in products.items()
        },
        "documents": documents,
        "unassigned_document_refs": unassigned_refs,
        "accounting": {
            "star_official_roster_rows": len(star_source["products"]),
            "care_dated_roster_rows": len(care_roster["products"]),
            "care_current_wording_only_rows": sum(
                row["origin"] == "current_wording_identity_only"
                for row in products["care"].values()
            ),
            "niva_official_roster_rows": len(niva_roster["products"]),
            "source_document_rows": len(documents),
            "associated_document_rows": len(assigned),
            "unassigned_document_rows": len(unassigned_refs),
            "capture_status_counts": dict(Counter(row["capture_status"] for row in documents)),
        },
        "blockers": [
            "Care linked launch register was last modified in September 2025; current product/UIN roster is not independently complete.",
            "All primary-versus-other classifications need reviewed evidence.",
            "Every product variant, option, edition, and applicable document bundle still needs review.",
            "Unassigned source documents and failed captures require classification or resolution.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--star-source", required=True, type=Path)
    parser.add_argument("--star-captures", required=True, type=Path)
    parser.add_argument("--other-audit", required=True, type=Path)
    parser.add_argument("--care-roster", required=True, type=Path)
    parser.add_argument("--niva-roster", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    inputs = {
        "star_source": args.star_source,
        "star_captures": args.star_captures,
        "other_audit": args.other_audit,
        "care_roster": args.care_roster,
        "niva_roster": args.niva_roster,
    }
    ledger = build_ledger(*(read_json(path) for path in inputs.values()))
    ledger["input_sha256"] = {name: digest(path.read_bytes()) for name, path in inputs.items()}
    write_json(args.output, ledger)
    print(json.dumps(ledger["accounting"], sort_keys=True))


if __name__ == "__main__":
    main()
