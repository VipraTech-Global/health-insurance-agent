"""Star public-document inventory and conservative internal-pilot audit.

This module never publishes policy knowledge or changes the customer adviser.
It records the independent product roster before associating documents. A URL,
name match, or successful download alone cannot establish legal applicability.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import Counter
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import httpx

from research_workspace.acquisition import acquire
from research_workspace.storage import digest, read_json, read_object, write_json

DOWNLOADS_URL = "https://www.starhealth.in/downloads/"
PRODUCTS_URL = "https://www.starhealth.in/list-products/"
HOSTS = ["starhealth.in", "d28c6jni2fmamz.cloudfront.net"]
UIN = re.compile(r"\bSHA[A-Z]{2,5}\d{4,7}V\d{2,3}\d{4,6}\b", re.I)
PILOT = {
    "SHAHLIP26044V092526": "Star Comprehensive Insurance Policy",
    "SHAHLIP26046V092526": "Family Health Optima Insurance Plan",
    "SHAHLIP26048V032526": "Star Health Assure Insurance Policy",
}
ROLE = {
    "Brochures": "brochure",
    "Prospectus": "prospectus",
    "Proposal": "proposal_form",
    "Policy Clause": "policy_wording",
    "Customer Information Sheet": "customer_information_sheet",
    "Other Excluded Expenses": "excluded_expenses",
    "Coverage for Modern Treatment": "modern_treatment_schedule",
    "Preventive Health Checkup": "preventive_health_schedule",
    "Withdrawn Products": "withdrawn_document",
}
REQUIRED_ROLES = ("policy_wording", "customer_information_sheet", "prospectus")
DEPENDENCY_ROLES = ("excluded_expenses", "modern_treatment_schedule", "preventive_health_schedule")
PROBE_CRITERIA = (
    "age_eligibility",
    "family_composition",
    "sum_insured",
    "waiting_period",
    "exclusions",
    "selected_addons",
    "price",
)


def normalized_name(value: str) -> str:
    """Conservative label equality, not legal identity resolution."""
    value = UIN.sub("", value)
    value = re.sub(r"\bSHAI\s*/\s*PR\d+\b", "", value, flags=re.I)
    return " ".join(re.findall(r"[a-z0-9]+", value.casefold()))


class StarPageParser(HTMLParser):
    """Read rendered anchors and table cells without treating page labels as proof."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.section = ""
        self.category = ""
        self.active: str | None = None
        self.text_parts: list[str] = []
        self.href = ""
        self.row: list[str] | None = None
        self.downloads: list[dict[str, str]] = []
        self.product_rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("h2", "h4", "a", "td"):
            self.active = tag
            self.text_parts = []
            if tag == "a":
                self.href = (dict(attrs).get("href") or "").strip()
        if tag == "tr":
            self.row = []

    def handle_data(self, data: str) -> None:
        if self.active:
            self.text_parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == self.active:
            value = " ".join(" ".join(self.text_parts).split())
            if tag == "h2":
                self.section, self.category = value, ""
            elif tag == "h4":
                self.category = value
            elif (
                tag == "a"
                and self.section
                and self.section != "Take the first step toward a healthier future"
                and self.href.lower().split("?", 1)[0].endswith(".pdf")
            ):
                self.downloads.append(
                    {
                        "role": ROLE.get(self.section, "other_official_download"),
                        "section": self.section,
                        "category": self.category,
                        "label": value,
                        "url": self.href,
                    }
                )
            elif tag == "td" and self.row is not None:
                self.row.append(value)
            self.active = None
        if tag == "tr" and self.row is not None:
            if len(self.row) == 4 and self.row[0].isdigit():
                self.product_rows.append(self.row)
            self.row = None


def snapshot(downloads_html: bytes, products_html: bytes, captured_at: str) -> dict[str, Any]:
    downloads = StarPageParser()
    downloads.feed(downloads_html.decode("utf-8", errors="replace"))
    products = StarPageParser()
    products.feed(products_html.decode("utf-8", errors="replace"))
    if not products.product_rows or not downloads.downloads:
        raise ValueError("Star source page has no product rows or document links")
    roster = []
    seen: set[str] = set()
    for number, name, uin, launch in products.product_rows:
        if not uin or uin in seen:
            raise ValueError(f"Invalid or duplicate product UIN: {uin}")
        seen.add(uin)
        roster.append(
            {
                "insurer_id": "star",
                "source_row": int(number),
                "name": name,
                "uin": uin,
                "launch_date_as_listed": launch,
                "comparison_scope": "review_pending",
                "variant_inventory": "unresolved",
                "option_inventory": "unresolved",
            }
        )
    if not set(PILOT).issubset(seen):
        raise ValueError("Star product list is missing a pilot UIN")
    if [row["source_row"] for row in roster] != list(range(1, len(roster) + 1)):
        raise ValueError("Star product list has missing or reordered rows")
    links = []
    for item in downloads.downloads:
        label_uins = sorted(set(UIN.findall(item["label"])))
        links.append(
            {
                **item,
                "insurer_id": "star",
                "label_uins": label_uins,
                "candidate_pilot_uins": [
                    uin for uin, name in PILOT.items() if item["label"].startswith(name)
                ],
                "association_status": "candidate_only",
                "comparison_scope": (
                    "primary_health_section"
                    if item["category"] == "Health"
                    else "outside_primary_section"
                ),
            }
        )
    for product in roster:
        uin = product["uin"]
        name = product["name"].casefold()
        wordings = [
            link for link in links if link["role"] == "policy_wording" and uin in link["label_uins"]
        ]
        product["scope_evidence"] = PRODUCTS_URL
        if uin in PILOT:
            scope, reason = "internal_pilot", "first_three_named_by_pilot_plan"
        elif uin.startswith(("SHAHLGP", "SHAHLIA", "SHAT", "SHAPA")) or any(
            term in name for term in ("group", "travel", "accident", "add on")
        ):
            scope, reason = (
                "outside_primary_candidate",
                "listed_name_or_uin_indicates_group_travel_accident_or_addon",
            )
        elif any(
            term in name
            for term in ("surplus", "top-up", "hospital cash", "out patient", "critical illness")
        ):
            scope, reason = (
                "outside_primary_candidate",
                "listed_name_indicates_topup_outpatient_or_fixed_benefit",
            )
        elif wordings and all(
            link["category"] == "Health - Speciality Products" for link in wordings
        ):
            scope, reason = "outside_primary_candidate", "wording_listed_in_speciality_section"
        elif any(link["category"] == "Health" for link in wordings):
            scope, reason = "primary_health_candidate", "wording_listed_in_health_section"
        else:
            scope, reason = "review_pending", "no_unambiguous_primary_wording_category"
        product["comparison_scope"] = scope
        product["scope_reason"] = reason
        product["scope_review_status"] = "pilot_only" if uin in PILOT else "provisional"
    names: dict[str, list[str]] = {}
    for product in roster:
        names.setdefault(normalized_name(product["name"]), []).append(product["uin"])
    for link in links:
        exact_uins = set(link["label_uins"]) & seen
        name_uins = names.get(normalized_name(link["label"]), [])
        link["candidate_product_uins"] = sorted(exact_uins or name_uins)
    return {
        "format_version": 1,
        "source_captured_at": captured_at,
        "sources": {
            "downloads": {"url": DOWNLOADS_URL, "sha256": digest(downloads_html)},
            "products": {"url": PRODUCTS_URL, "sha256": digest(products_html)},
        },
        "products": roster,
        "documents": links,
        "limitations": [
            "Only three products are selected for internal pilot; all other scope classifications are provisional and all variants await review.",
            "Document labels establish discovery candidates, never edition or applicability.",
            "The downloads page may include group, travel, accident, top-up, speciality and older publications.",
        ],
    }


def pdf_identity(content: bytes) -> dict[str, Any]:
    """First and last page triage only; a negative result does not prove absence."""
    if not content.startswith(b"%PDF-"):
        return {"status": "not_pdf", "uins": [], "edition_markers": []}
    try:
        result = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "2", "-layout", "-", "-"],
            input=content,
            capture_output=True,
            check=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {
            "status": "reader_failed",
            "error_type": type(exc).__name__,
            "uins": [],
            "edition_markers": [],
        }
    text = result.stdout.decode("utf-8", errors="replace")
    return {
        "status": "first_two_pages_only",
        "uins": sorted(set(UIN.findall(text))),
        "edition_markers": sorted(
            set(
                re.findall(
                    r"\b(?:POL|CIS|PRO)\s*/\s*[A-Z]+\s*/\s*V\.\d+\s*/\s*20\d{2}\b", text, re.I
                )
            )
        ),
    }


def pilot_documents(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Bind only exact pilot names for review; never infer a legal edition."""
    rows = []
    for row in source["documents"]:
        if row["category"] != "Health":
            continue
        for uin in row["candidate_pilot_uins"]:
            rows.append({**row, "product_uin": uin})
    return rows


def primary_candidate_documents(source: dict[str, Any]) -> list[dict[str, Any]]:
    """Return all possible Health-section links for the 13 current scope candidates."""
    target = {
        item["uin"]
        for item in source["products"]
        if item["comparison_scope"] in ("internal_pilot", "primary_health_candidate")
    }
    return [
        {**item, "product_uin": uin}
        for item in source["documents"]
        if item["category"] == "Health"
        for uin in item.get("candidate_product_uins", [])
        if uin in target
    ]


def audit(
    source: dict[str, Any], captures: dict[str, dict[str, Any]], root: Path | None = None
) -> dict[str, Any]:
    if root is not None:
        checked = {}
        for url, row in captures.items():
            if row.get("status") == "acquired":
                try:
                    read_object(root, row["sha256"])
                except (OSError, KeyError, ValueError) as exc:
                    checked[url] = {
                        **row,
                        "status": "unreadable",
                        "issues": [
                            *row.get("issues", []),
                            f"original_integrity:{type(exc).__name__}",
                        ],
                    }
                    continue
            checked[url] = row
        captures = checked
    documents = pilot_documents(source)
    products = []
    for product in source["products"]:
        if product["uin"] not in PILOT:
            continue
        uin = product["uin"]
        attached = []
        issues = []
        for item in [d for d in documents if d["product_uin"] == uin]:
            capture = captures.get(item["url"])
            identity = capture.get("identity", {}) if capture else {}
            observed_uins = identity.get("uins", [])
            if not capture or capture.get("status") != "acquired":
                state = "not_captured"
            elif observed_uins and uin not in observed_uins:
                state = "uin_conflict"
            elif item["role"] in REQUIRED_ROLES and uin not in observed_uins:
                state = "uin_unverified"
            elif item["role"] in REQUIRED_ROLES:
                state = "edition_unresolved"
            elif item["role"] in DEPENDENCY_ROLES:
                state = "applicability_unresolved"
            else:
                state = "discovery_only"
            if state not in ("discovery_only",):
                issues.append(f"{item['role']}:{state}")
            attached.append(
                {
                    "insurer_id": "star",
                    "product_uin": uin,
                    "variant": None,
                    "option": None,
                    "role": item["role"],
                    "url": item["url"],
                    "captured_at": capture.get("acquired_at") if capture else None,
                    "sha256": capture.get("sha256") if capture else None,
                    "observed_uins": observed_uins,
                    "edition_markers": identity.get("edition_markers", []),
                    "state": state,
                }
            )
        for role in REQUIRED_ROLES:
            if not any(d["role"] == role for d in attached):
                issues.append(f"{role}:not_listed")
        issues.extend(
            ("variant_inventory:unresolved", "option_inventory:unresolved", "rule_review:not_done")
        )
        products.append(
            {
                **product,
                "documents": attached,
                "price": {"status": "unavailable", "amount": None},
                "pilot_ready": False,
                "issues": sorted(set(issues)),
            }
        )
    primary = primary_candidate_documents(source)
    candidate_accounting = []
    for product in source["products"]:
        if product["comparison_scope"] not in ("internal_pilot", "primary_health_candidate"):
            continue
        links = [row for row in primary if row["product_uin"] == product["uin"]]
        roles = sorted({row["role"] for row in links})
        core = [row for row in links if row["role"] in REQUIRED_ROLES]
        core_uin_matches = sum(
            product["uin"] in captures.get(row["url"], {}).get("identity", {}).get("uins", [])
            for row in core
        )
        candidate_accounting.append(
            {
                "uin": product["uin"],
                "name": product["name"],
                "comparison_scope": product["comparison_scope"],
                "candidate_document_links": len(links),
                "captured_document_links": sum(
                    captures.get(row["url"], {}).get("status") == "acquired" for row in links
                ),
                "core_document_uin_matches": core_uin_matches,
                "core_document_count": len(core),
                "listed_roles": roles,
                "missing_core_roles": sorted(set(REQUIRED_ROLES) - set(roles)),
                "status": "unresolved",
            }
        )
    return {
        "format_version": 1,
        "source_captured_at": source["source_captured_at"],
        "insurer_id": "star",
        "status": "unresolved",
        "release_ready": False,
        "product_count_on_official_list": len(source["products"]),
        "download_link_count": len(source["documents"]),
        "pilot_products": sorted(products, key=lambda row: (row["name"], row["uin"])),
        "primary_candidate_accounting": sorted(
            candidate_accounting, key=lambda row: (row["name"], row["uin"])
        ),
        "document_states": dict(Counter(d["state"] for p in products for d in p["documents"])),
        "release_blockers": [
            "Only Star has been inventoried for this pilot; multi-insurer scope is incomplete.",
            "Variant and option universes, applicable document editions and complete rule evidence remain unreviewed.",
            "No independent held-out domain assessment or release gate has passed.",
        ],
    }


def probe_profiles(result: dict[str, Any], profiles: list[dict[str, Any]]) -> dict[str, Any]:
    """Produce complete unknown matrices until the actual policy rules are reviewed."""
    ids = [item.get("id") for item in profiles]
    if (
        not ids
        or any(not isinstance(item, str) or not item for item in ids)
        or len(ids) != len(set(ids))
    ):
        raise ValueError("Synthetic profile IDs must be nonempty and unique")
    products = result["pilot_products"]
    if {row["uin"] for row in products} != set(PILOT) or any(
        row["pilot_ready"] for row in products
    ):
        raise ValueError("Probe requires the three unresolved pilot products")
    cases = []
    for profile in profiles:
        if not isinstance(profile.get("facts"), dict) or not profile["facts"]:
            raise ValueError("Synthetic profiles require stated facts")
        cells = []
        for product in products:
            for criterion in PROBE_CRITERIA:
                cells.append(
                    {
                        "insurer_id": "star",
                        "product_uin": product["uin"],
                        "variant": None,
                        "option": None,
                        "criterion": criterion,
                        "outcome": "unknown",
                        "reason": (
                            "verified_price_unavailable"
                            if criterion == "price"
                            else "policy_rules_and_applicability_unreviewed"
                        ),
                        "evidence": [],
                    }
                )
        cases.append(
            {"profile_id": profile["id"], "synthetic_facts": profile["facts"], "cells": cells}
        )
    return {
        "format_version": 1,
        "status": "provisional_unresolved_probe",
        "profiles": cases,
        "limitations": "No coverage, eligibility or price outcome is asserted. These matrices test complete accounting and abstention only.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("snapshot", "capture", "audit", "probe"))
    parser.add_argument("--root", type=Path, required=True, help="Isolated research artifact root")
    parser.add_argument("--scope", choices=("pilot", "primary"), default="pilot")
    parser.add_argument("--profiles", type=Path, help="Synthetic profile JSON for probe")
    args = parser.parse_args()
    root = args.root
    source_path = root / "star/source-snapshot.json"
    if args.command == "snapshot":
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            pages = []
            for url in (DOWNLOADS_URL, PRODUCTS_URL):
                response = client.get(url)
                response.raise_for_status()
                pages.append(response.content)
        now = datetime.now(UTC).isoformat()
        result = snapshot(*pages, now)
        for name, content in zip(("downloads", "products"), pages, strict=True):
            path = root / "star" / f"{name}.html"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        write_json(source_path, result)
    elif args.command == "capture":
        source = read_json(source_path)
        rows = (
            pilot_documents(source)
            if args.scope == "pilot"
            else primary_candidate_documents(source)
        )
        unique_urls = sorted({row["url"] for row in rows})
        capture_path = root / "star/captures.json"
        previous: dict[str, dict[str, Any]] = (
            read_json(capture_path) if capture_path.exists() else {}
        )
        current_urls = {row["url"] for row in source["documents"]}
        captures = {url: row for url, row in previous.items() if url in current_urls}
        with httpx.Client(timeout=30, follow_redirects=False) as client:
            for url in unique_urls:
                if captures.get(url, {}).get("status") == "acquired":
                    continue
                row = acquire(
                    root,
                    url,
                    HOSTS,
                    client,
                    insurer_id="star",
                    linking_url=DOWNLOADS_URL,
                    expected_pdf=True,
                )
                if row["status"] == "acquired":
                    row["identity"] = pdf_identity(read_object(root, row["sha256"]))
                captures[url] = row
        write_json(capture_path, captures)
    elif args.command == "audit":
        source = read_json(source_path)
        captures_path = root / "star/captures.json"
        captures = read_json(captures_path) if captures_path.exists() else {}
        result = audit(source, captures, root)
        write_json(root / "star/pilot-audit.json", result)
        print(
            json.dumps(
                {
                    "status": result["status"],
                    "document_states": result["document_states"],
                    "product_count_on_official_list": result["product_count_on_official_list"],
                },
                sort_keys=True,
            )
        )
    else:
        if args.profiles is None:
            parser.error("probe requires --profiles")
        result = probe_profiles(read_json(root / "star/pilot-audit.json"), read_json(args.profiles))
        write_json(root / "star/synthetic-probe.json", result)
        print(json.dumps({"profiles": len(result["profiles"]), "status": result["status"]}))


if __name__ == "__main__":
    main()
