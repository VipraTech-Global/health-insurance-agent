"""The catalogue ledger accounts for sources without promoting identity leads."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from research_workspace.catalogue_ledger import build_ledger

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research/pilots"
VARIANT_LEADS = PILOT / "three-insurer/variant-leads-2026-09-29.json"


def _inputs() -> tuple[dict, dict, dict, dict, dict]:
    return (
        json.loads((PILOT / "star/source-snapshot-2026-09-27.json").read_text()),
        {},
        json.loads((PILOT / "three-insurer/audit-2026-09-29.json").read_text()),
        json.loads((PILOT / "three-insurer/care-roster-2026-09-29.json").read_text()),
        json.loads((PILOT / "three-insurer/niva-roster-2026-09-27.json").read_text()),
    )


def test_every_document_is_associated_or_visibly_unassigned() -> None:
    ledger = build_ledger(*_inputs())
    accounting = ledger["accounting"]
    assert accounting["source_document_rows"] == 1023
    assert accounting["associated_document_rows"] + accounting["unassigned_document_rows"] == 1023
    assert accounting["star_official_roster_rows"] == 56
    assert accounting["care_dated_roster_rows"] == 50
    assert accounting["care_current_wording_only_rows"] == 10
    assert accounting["niva_official_roster_rows"] == 44
    assert ledger["catalogue_complete"] is False
    assert all(document["role_class_reviewed"] is False for document in ledger["documents"])
    assert {
        document["role_class_candidate"]
        for document in ledger["documents"]
        if document["capture_status"] == "failed"
    } <= {"historical_context", "underwriting_context"}
    assert all(
        product["applicable_bundle_complete"] is False
        for products in ledger["insurers"].values()
        for product in products
    )


def test_new_care_wording_identity_does_not_become_verified_roster_row() -> None:
    ledger = build_ledger(*_inputs())
    care = {product["uin"]: product for product in ledger["insurers"]["care"]}
    new = care["CHIHLIP27063V012627"]
    assert new["origin"] == "current_wording_identity_only"
    assert new["variant_inventory"] == "unresolved"
    assert new["document_roles"]["policy_wording"] == 1


def test_duplicate_official_roster_uin_fails_closed() -> None:
    star, captures, audit, care, niva = _inputs()
    star["products"].append(dict(star["products"][0]))
    with pytest.raises(ValueError, match="Duplicate Star roster UIN"):
        build_ledger(star, captures, audit, care, niva)


def test_variant_leads_reconcile_to_captured_wordings() -> None:
    audit = _inputs()[2]
    leads = json.loads(VARIANT_LEADS.read_text())
    wording_by_url = {
        row["url"]: row for row in audit["documents"] if row["role"] == "policy_wording"
    }
    for lead in leads["care"]:
        wording = wording_by_url[lead["newer_wording_url"]]
        assert lead["newer_wording_uin"] in wording["first_two_page_uins"]
        assert lead["review_status"].endswith("unresolved")
    for lead in leads["niva"]:
        for wording_lead in lead["wordings"]:
            wording = wording_by_url[wording_lead["url"]]
            assert wording["sha256"] == wording_lead["sha256"]
            assert lead["uin_observed_in_both_wordings"] in wording["first_two_page_uins"]


def test_expanded_ledger_keeps_revision_identity_conflict_visible() -> None:
    star, captures, _, care, niva = _inputs()
    expanded = json.loads((PILOT / "three-insurer/audit-2026-09-29-expanded.json").read_text())
    ledger = build_ledger(star, captures, expanded, care, niva)
    assert ledger["accounting"]["source_document_rows"] == 1051
    assert ledger["accounting"]["associated_document_rows"] == 779
    assert ledger["accounting"]["unassigned_document_rows"] == 272
    assert any(
        document["listed_uin_reconciliation"] == "different_uin_observed"
        for document in ledger["documents"]
    )
    assert ledger["catalogue_complete"] is False
