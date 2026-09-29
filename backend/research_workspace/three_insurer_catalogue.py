"""Offline Care/Niva document capture and independent Niva roster inventory.

Source-page links are discovery evidence. Capturing a PDF or finding a UIN in
its first pages does not establish its edition, variant, or legal applicability.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import subprocess
from collections import Counter
from pathlib import Path
from typing import Any

import httpx
import pdfplumber

from research_workspace.acquisition import acquire
from research_workspace.storage import digest, put_object, read_json, read_object, write_json

ROSTER_URL = (
    "https://www.nivabupa.com/content/dam/nivabupa/PDF/"
    "List%20of%20Products%20Offered_22nd%20November%202023.pdf"
)
CARE_ROSTER_URL = (
    "https://cms.careinsurance.com/cms/public/uploads/uploads/other_disclosure/"
    "Launch_and_Withdrawn_dates_of_Products_1754900556.pdf"
)
CARE_ROSTER_2025_SHA256 = "b2f77f605da9156dd4f470404b7d3b1a3222bdd4591705833058a3a1882945c7"
HOSTS = {
    "care": ["careinsurance.com"],
    "niva": ["nivabupa.com"],
}
UIN = re.compile(r"\b(?:CHI|RHI|NBH|MAX)[A-Z]{2,5}\d{4,7}V\d{2,3}\d{4,6}\b", re.I)
ROSTER_UIN = re.compile(
    r"(?:\b(?:NBH|MAX)[A-Z]{2,5}\d{4,7}V\d{2,3}\d{4,6}\b|"
    r"IRDAI?/[^\s]+|\b104Y134V01\b)",
    re.I,
)
CARE_ROSTER_UIN = re.compile(
    r"(?:\b(?:CHI|RHI)[A-Z]{2,5}\d{4,7}V\d{2,3}\d{4,6}\b|\bIRDAI?/[^\s]+)",
    re.I,
)
CARE_MULTILINE_NAMES = {
    "RHIHLIP20154V011920": "Arogya Sanjeevani Policy-Care Health Insurance",
    "RHIHLIP21087V012021": "Corona Kavach Policy -Care Health Insurance",
    "CHIHMGP25039V022425": "Grameen Care Plus - Micro Insurance Product",
    "CHIPAGP22044V012122": "Group Saral Suraksha Bima- Care Health Insurance",
    "CHIHLGP21597V012021": "Group Arogya Sanjeevani Policy - Care Health Insurance",
}
CURRENT_ROLES = {
    "policy_wording",
    "customer_information_sheet",
    "prospectus",
    "brochure",
    "premium_chart",
}
EXPECTED_INSURERS = {"care", "niva"}
PUBLIC_PDF_HEADERS = {"User-Agent": "Mozilla/5.0", "Accept": "application/pdf,*/*;q=0.8"}
OUTSIDE_SCOPE_HINTS = (
    "group",
    "travel",
    "accident",
    "add-on",
    "addon",
    "top-up",
    "top up",
    "opd",
    "critical illness",
    "hospital cash",
    "loansure",
    "credit protection",
)


def text_from_pdf(content: bytes, *, first_pages: int | None = None) -> str:
    command = ["pdftotext", "-layout"]
    if first_pages is not None:
        command.extend(["-f", "1", "-l", str(first_pages)])
    command.extend(["-", "-"])
    result = subprocess.run(command, input=content, capture_output=True, timeout=60, check=True)
    return result.stdout.decode("utf-8", errors="replace")


def parse_niva_roster(content: bytes, captured_at: str) -> dict[str, Any]:
    """Parse the official PDF as an independent roster, retaining review flags."""
    if not content.startswith(b"%PDF-"):
        raise ValueError("Niva roster is not a PDF")
    body = text_from_pdf(content)
    if "List of Products Offered" not in body or "Last Updated on" not in body:
        raise ValueError("Niva roster title or update marker is missing")
    products: list[dict[str, Any]] = []
    seen: set[str] = set()
    lines = [line.strip() for line in body.splitlines()]
    for index, line in enumerate(lines):
        match = ROSTER_UIN.search(line)
        if not match:
            continue
        uin = match.group(0)
        if uin in seen:
            raise ValueError(f"Duplicate roster UIN: {uin}")
        seen.add(uin)
        name = line[: match.start()].strip()
        if not name and index > 0:
            name = lines[index - 1].strip()
        if not line[: match.start()].strip() and index + 1 < len(lines):
            continuation = lines[index + 1].strip()
            if continuation and not ROSTER_UIN.search(continuation):
                name = f"{name} {continuation}"
        name = " ".join(name.split())
        if not name or name.startswith("Product "):
            raise ValueError(f"Roster name could not be parsed for {uin}")
        products.append(
            {
                "insurer_id": "niva",
                "source_row": len(products) + 1,
                "name_as_listed": name,
                "uin": uin,
                "launch_date_as_listed": line[match.end() :].strip(),
                "name_review_status": "unreviewed_multiline"
                if not line[: match.start()].strip()
                else "unreviewed",
                "scope": "review_pending",
                "variant_inventory": "unresolved",
                "option_inventory": "unresolved",
            }
        )
    if len(products) < 30:
        raise ValueError("Niva roster parse is unexpectedly short")
    return {
        "format_version": 1,
        "insurer_id": "niva",
        "source_url": ROSTER_URL,
        "source_sha256": digest(content),
        "captured_at": captured_at,
        "update_marker": re.findall(r"Last Updated on[^\n]+", body),
        "source_roster_complete": False,
        "products": products,
        "limitations": [
            "PDF rows are machine parsed and require independent completeness and currentness review.",
            "Scope, variants, options, editions, and supporting documents remain unresolved.",
        ],
    }


def parse_care_roster(content: bytes, captured_at: str) -> dict[str, Any]:
    """Parse Care's dated launch register without asserting 2026 currentness."""
    if not content.startswith(b"%PDF-"):
        raise ValueError("Care launch register is not a PDF")
    body = text_from_pdf(content)
    if "Launched Products:" not in body or "Withdrawn Products:" not in body:
        raise ValueError("Care launch or withdrawal section is missing")
    launched, withdrawn = body.split("Withdrawn Products:", 1)
    rows = []
    seen: set[str] = set()
    for section, section_text in (("launched", launched), ("withdrawn", withdrawn)):
        for line in section_text.splitlines():
            match = CARE_ROSTER_UIN.search(line)
            if not match:
                continue
            uin = match.group(0)
            if uin in seen:
                raise ValueError(f"Duplicate Care roster UIN: {uin}")
            seen.add(uin)
            name = " ".join(line[: match.start()].split())
            if uin in CARE_MULTILINE_NAMES:
                name = CARE_MULTILINE_NAMES[uin]
            if not name:
                raise ValueError(f"Care roster name could not be parsed for {uin}")
            date = line[match.end() :].strip()
            if not re.fullmatch(r"\d{2}[-/]\d{2}[-/]\d{4}", date):
                raise ValueError(f"Care roster date could not be parsed for {uin}")
            rows.append(
                {
                    "insurer_id": "care",
                    "source_row": len(rows) + 1,
                    "name_as_listed": name,
                    "uin": uin,
                    "roster_section": section,
                    "date_as_listed": date,
                    "name_review_status": (
                        "manual_multiline_join" if uin in CARE_MULTILINE_NAMES else "machine_parsed"
                    ),
                    "comparison_scope": "review_pending",
                    "variant_inventory": "unresolved",
                    "option_inventory": "unresolved",
                }
            )
    if len(rows) < 40 or not any(row["roster_section"] == "withdrawn" for row in rows):
        raise ValueError("Care launch register parse is unexpectedly short")
    observed_sha256 = digest(content)
    known_2025_edition = observed_sha256 == CARE_ROSTER_2025_SHA256
    return {
        "format_version": 1,
        "insurer_id": "care",
        "source_url": CARE_ROSTER_URL,
        "source_sha256": observed_sha256,
        "captured_at": captured_at,
        "source_last_modified": "2025-09-04" if known_2025_edition else None,
        "source_roster_complete": False,
        "status": (
            "dated_launch_register_requires_2026_reconciliation"
            if known_2025_edition
            else "source_changed_requires_date_review"
        ),
        "products": rows,
        "limitations": [
            "This linked first-party register was last modified in September 2025 and cannot establish the complete 2026 current roster.",
            "Product scope, variants, options, and document applicability remain unreviewed.",
        ],
    }


def merge_source_register(base: dict[str, Any], supplement: dict[str, Any]) -> dict[str, Any]:
    """Add a separately observed official listing without losing source identity."""
    if supplement.get("insurer_id") != "care" or not supplement.get("source_page"):
        raise ValueError("Invalid Care supplement")
    additions = []
    for row in supplement.get("documents", []):
        if row.get("role") != "proposal_form" or not row.get("url"):
            raise ValueError("Invalid Care proposal link")
        additions.append({**row, "insurer_id": "care", "source_page": supplement["source_page"]})
    if not additions:
        raise ValueError("Care proposal supplement is empty")
    documents = [*base["documents"], *additions]
    identities = [(row["insurer_id"], row["url"]) for row in documents]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate insurer document URL after supplement")
    return {
        **base,
        "captured_at": supplement["source_observed_at"],
        "documents": documents,
        "supplemental_source": {
            "url": supplement["source_page"],
            "observed_at": supplement["source_observed_at"],
            "link_count": len(additions),
            "direct_html_status": "http_403",
        },
    }


def apply_source_refresh(register: dict[str, Any], refresh: dict[str, Any]) -> dict[str, Any]:
    """Replace only exact old listing links; preserve the prior dated snapshot."""
    if refresh.get("insurer_id") != "niva" or not refresh.get("source_html_sha256"):
        raise ValueError("Invalid Niva source refresh")
    documents = [dict(row) for row in register["documents"]]
    for change in refresh.get("material_source_changes", []):
        matches = [
            row
            for row in documents
            if row["insurer_id"] == refresh["insurer_id"]
            and row["source_page"] == refresh["source_page"]
            and row["role"] == change["role"]
            and row["label"] == change["label"]
            and row["url"] == change["previous_url"]
        ]
        if len(matches) != 1:
            raise ValueError(f"Niva source refresh has {len(matches)} old-link matches")
        matches[0]["url"] = change["url"]
        matches[0]["association_status"] = "unreviewed"
        matches[0]["applicability_status"] = "unresolved"
    if not refresh.get("material_source_changes"):
        raise ValueError("Niva source refresh has no changes")
    identities = [(row["insurer_id"], row["url"]) for row in documents]
    if len(identities) != len(set(identities)):
        raise ValueError("Duplicate insurer document URL after refresh")
    return {
        **register,
        "captured_at": refresh["observed_at"],
        "documents": documents,
        "source_refresh": {
            "url": refresh["source_page"],
            "observed_at": refresh["observed_at"],
            "source_html_sha256": refresh["source_html_sha256"],
            "material_change_count": len(refresh["material_source_changes"]),
        },
    }


def select_links(register: dict[str, Any], scope: str) -> list[dict[str, Any]]:
    rows = register.get("documents")
    if not isinstance(rows, list) or not rows:
        raise ValueError("Source link register is empty")
    ids = [
        (
            row.get("insurer_id"),
            row.get("source_page"),
            row.get("source_link_id"),
            row.get("label"),
        )
        for row in rows
    ]
    if len(ids) != len(set(ids)) or {row.get("insurer_id") for row in rows} != EXPECTED_INSURERS:
        raise ValueError("Source link register has duplicate or unexpected source identities")
    if scope == "all":
        return rows
    if scope == "current":
        return [row for row in rows if row.get("role") in CURRENT_ROLES]
    if scope == "wordings":
        return [row for row in rows if row.get("role") == "policy_wording"]
    if scope == "proposal_forms":
        return [row for row in rows if row.get("role") == "proposal_form"]
    raise ValueError(f"Unknown capture scope: {scope}")


def scope_lead(label: str, uin: str | None) -> tuple[str, str]:
    """Flag obvious non-primary names without making a reviewed scope decision."""
    name = label.casefold()
    if any(hint in name for hint in OUTSIDE_SCOPE_HINTS):
        return "outside_primary_candidate", "listed_name_indicates_other_product_category"
    if uin and "HLIP" in uin:
        return "primary_health_candidate", "individual_health_uin_requires_benefit_review"
    return "review_pending", "identity_or_benefit_type_not_established"


def recover_pdf_with_trailing_html(root: Path, row: dict[str, Any]) -> dict[str, Any]:
    """Retain the HTTP original and identify a parseable PDF followed by HTML."""
    if row.get("status") != "unreadable" or not row.get("sha256"):
        return row
    try:
        content = read_object(root, row["sha256"])
    except (OSError, ValueError):
        return {**row, "status": "preserved_original_unreadable"}
    end = content.rfind(b"%%EOF")
    if (
        not content.startswith(b"%PDF-")
        or end < 0
        or not content[end + 5 :].lstrip().lower().startswith(b"<!doctype html")
    ):
        return row
    pdf_bytes = content[: end + 5]
    try:
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            page_count = len(pdf.pages)
        if page_count < 1:
            return row
        uins = sorted(set(UIN.findall(text_from_pdf(pdf_bytes, first_pages=2))))
    except (OSError, ValueError, subprocess.SubprocessError):
        return row
    return {
        **row,
        "status": "acquired_with_trailing_html",
        "document_type": "pdf_with_trailing_html",
        "pdf_page_count": page_count,
        "derived_pdf_sha256": put_object(root, pdf_bytes),
        "first_two_page_uins": uins,
        "issues": [*row.get("issues", []), "trailing_html_after_pdf_eof"],
    }


def capture_links(
    root: Path,
    register: dict[str, Any],
    scope: str,
    *,
    max_new_bytes: int,
    client: httpx.Client,
) -> dict[str, dict[str, Any]]:
    """Resume bounded original capture; failed links stay visible and retryable."""
    path = root / "three-insurer/captures.json"
    previous: dict[str, dict[str, Any]] = read_json(path) if path.exists() else {}
    rows = select_links(register, scope)
    selected = {(row["insurer_id"], row["url"]): row for row in rows}
    all_keys = {f"{row['insurer_id']}:{row['url']}" for row in register["documents"]}
    captures = {key: value for key, value in previous.items() if key in all_keys}
    new_bytes = 0
    for (insurer_id, url), row in sorted(selected.items()):
        key = f"{insurer_id}:{url}"
        if captures.get(key, {}).get("status") in {"acquired", "acquired_with_trailing_html"}:
            try:
                read_object(root, captures[key]["sha256"])
                continue
            except (OSError, KeyError, ValueError):
                captures[key]["status"] = "preserved_original_unreadable"
        if captures.get(key, {}).get("status") == "unreadable":
            recovered = recover_pdf_with_trailing_html(root, captures[key])
            if recovered["status"] == "acquired_with_trailing_html":
                captures[key] = recovered
                write_json(path, captures)
                continue
        if new_bytes >= max_new_bytes:
            captures[key] = {
                "status": "capture_budget_reached",
                "url": url,
                "insurer_id": insurer_id,
            }
            continue
        result = acquire(
            root,
            url,
            HOSTS[insurer_id],
            client,
            insurer_id=insurer_id,
            linking_url=row["source_page"],
            expected_pdf=row["role"] != "proposal_form_index",
        )
        result = recover_pdf_with_trailing_html(root, result)
        if result["status"] in {"acquired", "acquired_with_trailing_html"}:
            new_bytes += result.get("byte_count", 0)
            if result["document_type"] == "pdf_unclassified":
                try:
                    result["first_two_page_uins"] = sorted(
                        set(
                            UIN.findall(
                                text_from_pdf(read_object(root, result["sha256"]), first_pages=2)
                            )
                        )
                    )
                except (OSError, subprocess.SubprocessError, ValueError):
                    result["first_two_page_uins"] = []
                    result["issues"].append("first_two_page_identity_unreadable")
        captures[key] = result
        write_json(path, captures)
    write_json(path, captures)
    return captures


def audit_links(
    register: dict[str, Any],
    captures: dict[str, dict[str, Any]],
    niva_roster: dict[str, Any] | None,
    root: Path | None = None,
    care_roster: dict[str, Any] | None = None,
) -> dict[str, Any]:
    documents = []
    care_candidates = []
    identity_roles: Counter[tuple[str, str, str]] = Counter()
    for row in register["documents"]:
        capture = captures.get(f"{row['insurer_id']}:{row['url']}")
        capture_status = capture.get("status") if capture else "not_attempted"
        if root is not None and capture_status in {"acquired", "acquired_with_trailing_html"}:
            try:
                read_object(root, capture["sha256"])
                if capture.get("derived_pdf_sha256"):
                    read_object(root, capture["derived_pdf_sha256"])
            except (OSError, KeyError, ValueError):
                capture_status = "preserved_original_unreadable"
        observed_uins = (
            capture.get("first_two_page_uins", [])
            if capture_status in {"acquired", "acquired_with_trailing_html"}
            else []
        )
        for observed_uin in set(observed_uins):
            identity_roles[(row["insurer_id"], observed_uin, row["role"])] += 1
        candidate_uin = observed_uins[0] if len(observed_uins) == 1 else None
        scope, scope_reason = scope_lead(row["label"], candidate_uin)
        documents.append(
            {
                **row,
                "capture_status": capture_status,
                "sha256": capture.get("sha256") if capture else None,
                "captured_at": capture.get("acquired_at") if capture else None,
                "first_two_page_uins": observed_uins,
                "comparison_scope_candidate": scope,
                "scope_reason": scope_reason,
                "edition_status": "unresolved",
                "variant_applicability": "unresolved",
            }
        )
        if row["insurer_id"] == "care" and row["role"] == "policy_wording":
            care_candidates.append(
                {
                    "source_label": row["label"],
                    "source_url": row["url"],
                    "uin_candidate": candidate_uin,
                    "comparison_scope_candidate": scope,
                    "scope_reason": scope_reason,
                    "scope_reviewed": False,
                    "variant_inventory_complete": False,
                }
            )
    for candidate in care_candidates:
        uin = candidate["uin_candidate"]
        candidate["first_two_page_document_roles"] = {
            role: count
            for (insurer, observed_uin, role), count in identity_roles.items()
            if insurer == "care" and observed_uin == uin and uin is not None
        }
    niva_products = []
    if niva_roster is not None:
        for item in niva_roster["products"]:
            scope, reason = scope_lead(item["name_as_listed"], item["uin"])
            niva_products.append(
                {
                    **item,
                    "comparison_scope_candidate": scope,
                    "scope_reason": reason,
                    "first_two_page_document_roles": {
                        role: count
                        for (insurer, observed_uin, role), count in identity_roles.items()
                        if insurer == "niva" and observed_uin == item["uin"]
                    },
                }
            )
    niva_uins = {item["uin"] for item in niva_products}
    wording_uins = {
        uin
        for (insurer, uin, role), count in identity_roles.items()
        if insurer == "niva" and role == "policy_wording" and count > 0
    }
    return {
        "format_version": 1,
        "source_snapshot_date": register["captured_at"],
        "release_ready": False,
        "documents": documents,
        "capture_status_counts": dict(Counter(row["capture_status"] for row in documents)),
        "niva_roster": {**niva_roster, "products": niva_products} if niva_roster else None,
        "niva_wording_identity_reconciliation": {
            "first_two_page_wording_uins_in_roster": len(wording_uins & niva_uins),
            "roster_uins_without_first_two_page_wording_match": sorted(niva_uins - wording_uins),
            "wording_uins_outside_roster": sorted(wording_uins - niva_uins),
            "status": "identity_leads_only",
        },
        "care_roster": (
            {**care_roster, "wording_derived_candidates": care_candidates}
            if care_roster
            else {
                "source_roster_complete": False,
                "status": "independent_product_uin_roster_not_verified",
                "wording_derived_candidates": care_candidates,
            }
        ),
        "release_blockers": [
            "Care independent current product/UIN roster has not been verified; its linked launch register was last modified in September 2025."
            if care_roster
            else "Care independent current product/UIN roster has not been verified.",
            "Care listing pages were browser-readable but raw HTML could not be preserved.",
            "Care proposal-form listing has not been fully inventoried."
            if not register.get("supplemental_source")
            else "Care proposal-form links are inventoried, but applicability is unreviewed.",
            "Document editions, variants, options, schedules and amendments are not reconciled.",
            "No policy rules or independent held-out assessment are reviewed.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("roster", "care-roster", "capture", "audit"))
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--links", required=True, type=Path)
    parser.add_argument(
        "--scope", choices=("all", "current", "wordings", "proposal_forms"), default="current"
    )
    parser.add_argument("--supplement", type=Path)
    parser.add_argument("--refresh", type=Path)
    parser.add_argument("--max-new-bytes", type=int, default=1_000_000_000)
    args = parser.parse_args()
    root: Path = args.root
    register = read_json(args.links)
    if args.supplement:
        register = merge_source_register(register, read_json(args.supplement))
    if args.refresh:
        register = apply_source_refresh(register, read_json(args.refresh))
    if args.command == "roster":
        with httpx.Client(timeout=45, follow_redirects=False, headers=PUBLIC_PDF_HEADERS) as client:
            result = acquire(
                root, ROSTER_URL, HOSTS["niva"], client, insurer_id="niva", expected_pdf=True
            )
        if result["status"] != "acquired":
            raise RuntimeError(f"Niva official roster capture failed: {result['issues']}")
        roster = parse_niva_roster(read_object(root, result["sha256"]), result["acquired_at"])
        write_json(root / "three-insurer/niva-roster.json", roster)
        print(json.dumps({"niva_roster_products": len(roster["products"])}))
    elif args.command == "care-roster":
        with httpx.Client(timeout=45, follow_redirects=False, headers=PUBLIC_PDF_HEADERS) as client:
            result = acquire(
                root, CARE_ROSTER_URL, HOSTS["care"], client, insurer_id="care", expected_pdf=True
            )
        if result["status"] != "acquired":
            raise RuntimeError(f"Care official launch register capture failed: {result['issues']}")
        roster = parse_care_roster(read_object(root, result["sha256"]), result["acquired_at"])
        write_json(root / "three-insurer/care-roster.json", roster)
        print(json.dumps({"care_dated_roster_products": len(roster["products"])}))
    elif args.command == "capture":
        if args.max_new_bytes < 0:
            parser.error("--max-new-bytes must be nonnegative")
        with httpx.Client(timeout=45, follow_redirects=False, headers=PUBLIC_PDF_HEADERS) as client:
            captures = capture_links(
                root, register, args.scope, max_new_bytes=args.max_new_bytes, client=client
            )
        print(json.dumps(dict(Counter(row["status"] for row in captures.values())), sort_keys=True))
    else:
        captures_path = root / "three-insurer/captures.json"
        roster_path = root / "three-insurer/niva-roster.json"
        care_roster_path = root / "three-insurer/care-roster.json"
        audit = audit_links(
            register,
            read_json(captures_path) if captures_path.exists() else {},
            read_json(roster_path) if roster_path.exists() else None,
            root,
            read_json(care_roster_path) if care_roster_path.exists() else None,
        )
        write_json(root / "three-insurer/audit.json", audit)
        print(
            json.dumps(
                {"release_ready": False, "capture_status_counts": audit["capture_status_counts"]}
            )
        )


if __name__ == "__main__":
    main()
