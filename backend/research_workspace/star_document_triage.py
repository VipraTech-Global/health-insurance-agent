"""Reproducible full-text identity triage of Star primary-candidate PDFs.

This records observable strings and listing anomalies. It does not decide which
edition, schedule, variant, option, or clause applies to a policyholder.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from research_workspace.star_catalogue import DEPENDENCY_ROLES, REQUIRED_ROLES, UIN
from research_workspace.storage import digest, read_json, read_object, write_json

PRIMARY_SCOPES = {"internal_pilot", "primary_health_candidate"}
REVIEW_ROLES = set(REQUIRED_ROLES) | set(DEPENDENCY_ROLES)
CODE = re.compile(r"\b(?:POL|CIS|PRO)\s*/\s*[A-Z]+\s*/\s*V\.?\s*\d+\s*/\s*20\d{2}\b", re.I)
AVAILABLE = re.compile(r"coverage\s+is\s+available\s+in\s+the\s+policy", re.I)
NOT_AVAILABLE = re.compile(r"coverage\s+is\s+not\s+available\s+in\s+the\s+policy", re.I)
OPTION_CONDITION = re.compile(r"Not Applicable if Optional Cover[^\n]+", re.I)


def _pdf_text(content: bytes) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", "-", "-"],
        input=content,
        capture_output=True,
        check=True,
        timeout=60,
    )
    return result.stdout.decode("utf-8", errors="replace")


def triage(source: dict[str, Any], captures: dict[str, Any], artifact_root: Path) -> dict[str, Any]:
    primary = {
        row["uin"]: row for row in source["products"] if row["comparison_scope"] in PRIMARY_SCOPES
    }
    by_url: dict[str, dict[str, Any]] = {}
    for row in source["documents"]:
        uins = sorted(set(row["candidate_product_uins"]) & primary.keys())
        if not uins or row["role"] not in REVIEW_ROLES:
            continue
        entry = by_url.setdefault(
            row["url"], {"url": row["url"], "listed_roles": [], "candidate_uins": []}
        )
        entry["listed_roles"].append(row["role"])
        entry["candidate_uins"] = sorted(set(entry["candidate_uins"]) | set(uins))

    documents = []
    for url, row in sorted(by_url.items()):
        capture = captures.get(url)
        if not capture or capture["status"] != "acquired":
            raise ValueError(f"Required candidate PDF not acquired: {url}")
        sha = capture["sha256"]
        content = read_object(artifact_root, sha)
        text = _pdf_text(content)
        observed_uins = sorted(set(UIN.findall(text)))
        documents.append(
            {
                **row,
                "listed_roles": sorted(set(row["listed_roles"])),
                "sha256": sha,
                "page_count": capture["page_count"],
                "observed_uins_full_text": observed_uins,
                "observed_code_strings_full_text": sorted(set(CODE.findall(text))),
                "candidate_uins_found_full_text": sorted(
                    set(row["candidate_uins"]) & set(observed_uins)
                ),
                "excluded_expenses_heading_phrase": (
                    "coverage_not_available"
                    if NOT_AVAILABLE.search(text)
                    else "coverage_available"
                    if AVAILABLE.search(text)
                    else "neither_phrase_found"
                )
                if "excluded_expenses" in row["listed_roles"]
                else None,
                "excluded_expenses_option_condition": (
                    " ".join(OPTION_CONDITION.search(text).group().split())
                    if OPTION_CONDITION.search(text)
                    else None
                )
                if "excluded_expenses" in row["listed_roles"]
                else None,
                "edition_status": "unresolved",
                "applicability_status": "unresolved",
            }
        )

    by_uin: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in documents:
        for uin in row["candidate_uins"]:
            by_uin[uin].append(row)
    products = []
    for uin, product in primary.items():
        refs = by_uin[uin]
        roles = Counter(role for row in refs for role in row["listed_roles"])
        products.append(
            {
                "uin": uin,
                "name": product["name"],
                "scope_status": "provisional",
                "candidate_document_urls": [row["url"] for row in refs],
                "role_counts": dict(sorted(roles.items())),
                "candidate_uin_found_in_all_review_pdfs": all(
                    uin in row["candidate_uins_found_full_text"] for row in refs
                ),
                "variant_inventory": "unresolved",
                "option_inventory": "unresolved",
                "applicable_bundle_complete": False,
            }
        )
    return {
        "format_version": 1,
        "method": "Full PDF text identity/code/heading scan; no clause or applicability adjudication.",
        "products": sorted(products, key=lambda row: row["uin"]),
        "documents": documents,
        "accounting": {
            "primary_candidate_products": len(products),
            "review_document_urls": len(documents),
            "review_role_associations": sum(len(row["listed_roles"]) for row in documents),
            "listed_role_counts": dict(
                sorted(Counter(role for row in documents for role in row["listed_roles"]).items())
            ),
            "candidate_uin_absent_urls": sum(
                set(row["candidate_uins"]) != set(row["candidate_uins_found_full_text"])
                for row in documents
            ),
            "cross_role_url_count": sum(len(row["listed_roles"]) > 1 for row in documents),
            "excluded_expenses_phrase_counts": dict(
                sorted(
                    Counter(
                        row["excluded_expenses_heading_phrase"]
                        for row in documents
                        if row["excluded_expenses_heading_phrase"] is not None
                    ).items()
                )
            ),
            "excluded_expenses_option_condition_urls": sum(
                row["excluded_expenses_option_condition"] is not None for row in documents
            ),
        },
        "catalogue_complete": False,
        "blockers": [
            "Observed UIN and code strings do not establish edition or variant applicability.",
            "The excluded-expenses sheet for Star Health Assure says coverage is available under that heading.",
            "The Star Health Premier modern-treatment listing reuses its policy-wording PDF URL.",
            "Smart Health Pro and Super Star excluded-expenses sheets state an optional-cover condition that needs variant review.",
            "Every variant, option, applicable document bundle, and product scope still needs review.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--captures", required=True, type=Path)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = triage(read_json(args.source), read_json(args.captures), args.root)
    result["input_sha256"] = {
        "source": digest(args.source.read_bytes()),
        "captures": digest(args.captures.read_bytes()),
    }
    write_json(args.output, result)
    print(json.dumps(result["accounting"], sort_keys=True))


if __name__ == "__main__":
    main()
