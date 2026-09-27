"""Focused checks for the official Star snapshot and fail-closed pilot rules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from research_workspace.release_gate import check_release_gate
from research_workspace.star_catalogue import (
    PILOT,
    audit,
    pilot_documents,
    primary_candidate_documents,
    probe_profiles,
    snapshot,
)

ROOT = Path(__file__).resolve().parents[3]
SNAPSHOT = ROOT / "research/pilots/star/source-snapshot-2026-09-27.json"
CAPTURES = ROOT / "research/pilots/star/captures-2026-09-27.json"


def test_official_snapshot_accounts_for_pilot_and_all_download_sections() -> None:
    source = json.loads(SNAPSHOT.read_text())
    captures = json.loads(CAPTURES.read_text())
    assert len(source["products"]) == 56
    assert len(source["documents"]) == 338
    assert sum(row["role"] == "withdrawn_document" for row in source["documents"]) == 30
    assert (
        sum(row["comparison_scope"] == "primary_health_candidate" for row in source["products"])
        == 10
    )
    assert (
        sum(row["comparison_scope"] == "outside_primary_candidate" for row in source["products"])
        == 43
    )
    assert {row["uin"] for row in source["products"] if row["uin"] in PILOT} == set(PILOT)
    assert {row["comparison_scope"] for row in source["documents"]} == {
        "primary_health_section",
        "outside_primary_section",
    }
    listed = pilot_documents(source)
    assert len(listed) == 23
    assert {row["url"] for row in listed}.issubset(captures)
    assert all(
        row["status"] == "acquired" and len(row["sha256"]) == 64 for row in captures.values()
    )
    primary = primary_candidate_documents(source)
    assert len(primary) == 91
    assert len({row["url"] for row in primary}) == 85
    accounting = audit(source, captures)["primary_candidate_accounting"]
    assert len(accounting) == 13
    assert all(
        row["candidate_document_links"] == row["captured_document_links"] for row in accounting
    )
    assert sum(row["core_document_uin_matches"] for row in accounting) == 39
    assert all(row["core_document_uin_matches"] == row["core_document_count"] for row in accounting)


@pytest.mark.parametrize("uin", sorted(PILOT))
def test_each_pilot_bundle_is_visible_and_unresolved(uin: str) -> None:
    result = audit(json.loads(SNAPSHOT.read_text()), json.loads(CAPTURES.read_text()))
    product = next(row for row in result["pilot_products"] if row["uin"] == uin)
    roles = {item["role"] for item in product["documents"]}
    assert {"policy_wording", "customer_information_sheet", "prospectus"}.issubset(roles)
    assert {"excluded_expenses", "modern_treatment_schedule"}.issubset(roles)
    assert all(
        uin in item["observed_uins"]
        for item in product["documents"]
        if item["role"] in ("policy_wording", "customer_information_sheet", "prospectus")
    )
    assert product["price"] == {"status": "unavailable", "amount": None}
    assert not product["pilot_ready"] and product["issues"]
    assert "variant_inventory:unresolved" in product["issues"]


def test_conflicting_cis_uin_is_reported() -> None:
    source = json.loads(SNAPSHOT.read_text())
    captures = json.loads(CAPTURES.read_text())
    cis = next(
        row
        for row in pilot_documents(source)
        if row["product_uin"] == "SHAHLIP26044V092526"
        and row["role"] == "customer_information_sheet"
    )
    captures[cis["url"]]["identity"]["uins"] = ["SHAHLIP26046V092526"]
    result = audit(source, captures)
    product = next(row for row in result["pilot_products"] if row["uin"] == "SHAHLIP26044V092526")
    assert "customer_information_sheet:uin_conflict" in product["issues"]
    assert not result["release_ready"]


def test_missing_preserved_original_blocks_audit(tmp_path: Path) -> None:
    source = json.loads(SNAPSHOT.read_text())
    captures = json.loads(CAPTURES.read_text())
    result = audit(source, captures, tmp_path)
    assert all(
        row["captured_document_links"] == 0 for row in result["primary_candidate_accounting"]
    )
    assert all("policy_wording:not_captured" in row["issues"] for row in result["pilot_products"])
    assert not result["release_ready"]


def test_synthetic_profiles_account_for_every_unresolved_cell() -> None:
    audit_result = audit(json.loads(SNAPSHOT.read_text()), json.loads(CAPTURES.read_text()))
    profiles = json.loads((ROOT / "research/pilots/star/synthetic-profiles.json").read_text())
    probe = probe_profiles(audit_result, profiles)
    assert len(probe["profiles"]) == 4
    assert all(len(case["cells"]) == 3 * 7 for case in probe["profiles"])
    assert all(
        cell["outcome"] == "unknown"
        and cell["reason"]
        and not {"rank", "winner", "recommendation", "selected_policy"}.intersection(cell)
        for case in probe["profiles"]
        for cell in case["cells"]
    )
    assert all(
        cell["reason"] == "verified_price_unavailable"
        for case in probe["profiles"]
        for cell in case["cells"]
        if cell["criterion"] == "price"
    )


def test_snapshot_rejects_missing_pilot_uin() -> None:
    product_html = b"<table><tr><td>1</td><td>Other</td><td>SHAHLIP26044V092526</td><td>today</td></tr></table>"
    download_html = b"<h2>Policy Clause</h2><h4>Health</h4><div><a href='https://starhealth.in/p.pdf'>Other</a></div>"
    with pytest.raises(ValueError, match="missing a pilot UIN"):
        snapshot(download_html, product_html, "2026-09-27T00:00:00+00:00")


def _hypothetical_release() -> tuple[list[dict], list[str], list[dict], dict]:
    criteria = ["age", "family", "sum_insured", "waiting_period", "exclusion", "addon", "price"]
    catalogues = []
    cells = []
    for insurer in ("star", "care", "niva"):
        variant_id = f"{insurer}:variant"
        document_sha = {"star": "b", "care": "c", "niva": "d"}[insurer] * 64
        catalogues.append(
            {
                "insurer_id": insurer,
                "source_roster_complete": True,
                "source_sha256": "a" * 64,
                "products": [
                    {
                        "uin": f"{insurer}-uin",
                        "name": insurer,
                        "scope": "included",
                        "scope_reviewed": True,
                        "scope_evidence": "official roster row",
                        "variant_inventory_complete": True,
                        "variants": [
                            {
                                "id": variant_id,
                                "option_inventory_complete": True,
                                "restriction_inventory_complete": True,
                                "documents": [
                                    {
                                        "role": role,
                                        "state": "verified_applicable",
                                        "sha256": document_sha,
                                        "url": "https://official.example/p.pdf",
                                        "captured_at": "2026-09-27T00:00:00Z",
                                        "edition_verified": True,
                                        "applicability_evidence": "reviewed clause",
                                    }
                                    for role in (
                                        "policy_wording",
                                        "customer_information_sheet",
                                        "prospectus",
                                    )
                                ],
                            }
                        ],
                    }
                ],
            }
        )
        for criterion in criteria:
            cells.append(
                {
                    "insurer_id": insurer,
                    "variant_id": variant_id,
                    "criterion": criterion,
                    "outcome": "meets" if criterion == "age" else "unknown",
                    "required_evidence_complete": criterion == "age",
                    "evidence": [
                        {
                            "source_sha256": document_sha,
                            "page": 1,
                            "quote": "synthetic verified age clause",
                        }
                    ]
                    if criterion == "age"
                    else [],
                    "unresolved_reason": None
                    if criterion == "age"
                    else "synthetic fact not supplied",
                }
            )
    heldout = {
        "cases_scored": 8,
        "decision_critical_errors": 0,
        "independent": True,
        "frozen_before_implementation": True,
        "frozen_set_sha256": "e" * 64,
        "scoring_report_sha256": "f" * 64,
        "material_criteria_passed": True,
        "essential_evidence_complete": True,
        "cross_account_leakage": False,
        "privacy_tests_run": True,
        "purchase_direction": False,
        "neutral_wording_reviewed": True,
    }
    return catalogues, criteria, cells, heldout


def test_release_gate_accounts_for_every_profile_criterion() -> None:
    catalogues, criteria, cells, heldout = _hypothetical_release()
    assert check_release_gate(catalogues, criteria, cells, heldout)["ready"]
    cells.pop()
    result = check_release_gate(catalogues, criteria, cells, heldout)
    assert not result["ready"]
    assert "missing_or_duplicate_comparison_cell" in result["blockers"]


def test_release_gate_blocks_unsupported_or_ranked_outcome() -> None:
    catalogues, criteria, cells, heldout = _hypothetical_release()
    cells[0].update(required_evidence_complete=False, rank=1)
    result = check_release_gate(catalogues, criteria, cells, heldout)
    assert {
        "supported_cell_lacks_complete_evidence",
        "ranking_or_selection_field_present",
    }.issubset(result["blockers"])
    assert not result["ready"]


def test_release_gate_blocks_cross_product_citation() -> None:
    catalogues, criteria, cells, heldout = _hypothetical_release()
    cells[0]["evidence"][0]["source_sha256"] = "c" * 64
    result = check_release_gate(catalogues, criteria, cells, heldout)
    assert "supported_cell_evidence_packet_invalid" in result["blockers"]
    assert not result["ready"]


def test_release_gate_requires_frozen_independent_scoring() -> None:
    catalogues, criteria, cells, heldout = _hypothetical_release()
    heldout["frozen_set_sha256"] = None
    result = check_release_gate(catalogues, criteria, cells, heldout)
    assert "heldout_freeze_or_scoring_provenance_missing" in result["blockers"]
    assert not result["ready"]


def test_release_gate_blocks_unresolved_editions_and_star_only_release() -> None:
    catalogues, criteria, cells, heldout = _hypothetical_release()
    catalogues[0]["products"][0]["variants"][0]["documents"][0]["state"] = "edition_unresolved"
    result = check_release_gate(
        catalogues[:1], criteria, [x for x in cells if x["insurer_id"] == "star"], heldout
    )
    assert "exact_star_care_niva_scope_required" in result["blockers"]
    assert "star:star:variant:required_documents_unverified" in result["blockers"]
    assert not result["ready"]
