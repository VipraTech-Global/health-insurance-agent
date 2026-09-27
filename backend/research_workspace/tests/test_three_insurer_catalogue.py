"""Source accounting and fail-closed checks for the three-insurer research inventory."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from research_workspace.three_insurer_assessment import assess
from research_workspace.three_insurer_catalogue import (
    audit_links,
    parse_niva_roster,
    recover_pdf_with_trailing_html,
    scope_lead,
    select_links,
)

ROOT = Path(__file__).resolve().parents[3]
LINKS = ROOT / "research/pilots/three-insurer/source-links-2026-09-27.json"
ROSTER = ROOT / "research/pilots/three-insurer/niva-roster-2026-09-27.json"
AUDIT = ROOT / "research/pilots/three-insurer/audit-2026-09-27.json"
STAR_SOURCE = ROOT / "research/pilots/star/source-snapshot-2026-09-27.json"
STAR_AUDIT = ROOT / "research/pilots/star/pilot-audit-2026-09-27.json"


def test_official_links_and_roster_have_complete_source_accounting() -> None:
    links = json.loads(LINKS.read_text())
    roster = json.loads(ROSTER.read_text())
    assert len(links["documents"]) == 638
    assert len({row["url"] for row in links["documents"]}) == 638
    assert (
        sum(
            row["source_link_id"] == 64
            for row in links["documents"]
            if row["source_page"] == "https://transactions.nivabupa.com/pages/downloads.aspx"
        )
        == 15
    )
    assert len(select_links(links, "wordings")) == 91
    assert len(roster["products"]) == 44
    assert "10th September 2026" in roster["update_marker"][0]
    assert len({row["uin"] for row in roster["products"]}) == 44
    assert any(row["name_as_listed"] == "ReAssure 3.0" for row in roster["products"])
    assert all(row["scope"] == "review_pending" for row in roster["products"])
    reconciliation = json.loads(AUDIT.read_text())["niva_wording_identity_reconciliation"]
    assert reconciliation["first_two_page_wording_uins_in_roster"] == 40
    assert len(reconciliation["roster_uins_without_first_two_page_wording_match"]) == 4
    assert reconciliation["wording_uins_outside_roster"] == []


def test_audit_keeps_uncaptured_and_unreviewed_documents_visible() -> None:
    links = json.loads(LINKS.read_text())
    roster = json.loads(ROSTER.read_text())
    result = audit_links(links, {}, roster)
    assert not result["release_ready"]
    assert result["capture_status_counts"] == {"not_attempted": 638}
    assert len(result["care_roster"]["wording_derived_candidates"]) == 46
    assert result["care_roster"]["source_roster_complete"] is False
    assert all(row["edition_status"] == "unresolved" for row in result["documents"])


def test_missing_preserved_pdf_is_not_counted_as_captured(tmp_path: Path) -> None:
    links = json.loads(LINKS.read_text())
    first = links["documents"][0]
    key = f"{first['insurer_id']}:{first['url']}"
    captures = {key: {"status": "acquired", "sha256": "a" * 64}}
    result = audit_links(links, captures, None, tmp_path)
    assert result["capture_status_counts"]["preserved_original_unreadable"] == 1
    recovered = recover_pdf_with_trailing_html(
        tmp_path, {"status": "unreadable", "sha256": "a" * 64}
    )
    assert recovered["status"] == "preserved_original_unreadable"


def test_scope_leads_never_mark_a_product_reviewed() -> None:
    assert scope_lead("Group Travel Insurance", "NBHHLIP26047V012526")[0] == (
        "outside_primary_candidate"
    )
    assert scope_lead("ReAssure 3.0", "NBHHLIP26047V012526")[0] == ("primary_health_candidate")
    assert scope_lead("Unknown", None)[0] == "review_pending"


def test_release_assessment_accounts_for_all_three_rosters_and_stays_blocked() -> None:
    links = json.loads(LINKS.read_text())
    roster = json.loads(ROSTER.read_text())
    other_audit = audit_links(links, {}, roster)
    report = assess(
        json.loads(STAR_SOURCE.read_text()),
        json.loads(STAR_AUDIT.read_text()),
        links,
        other_audit,
        {name: "a" * 64 for name in ("star_source", "star_audit", "links", "other_audit")},
    )
    assert report["manifest"]["insurer_roster_counts"] == {
        "star": 56,
        "care": 46,
        "niva": 44,
    }
    assert report["manifest"]["price_status"] == (
        "unavailable_without_current_chart_or_verified_quote"
    )
    assert report["release_ready"] is False
    assert report["gate"]["ready"] is False
    assert report["heldout"]["status"] == "not_frozen_or_run"


def test_roster_rejects_duplicate_uin(monkeypatch: pytest.MonkeyPatch) -> None:
    text = (
        "List of Products Offered\n"
        "Plan A    NBHHLIP26047V012526    1-Jan-26\n"
        "Plan B    NBHHLIP26047V012526    2-Jan-26\n"
        "Last Updated on 10th September 2026\n"
    )
    monkeypatch.setattr(
        "research_workspace.three_insurer_catalogue.text_from_pdf", lambda *_args: text
    )
    with pytest.raises(ValueError, match="Duplicate roster UIN"):
        parse_niva_roster(b"%PDF-test", "2026-09-27T00:00:00Z")
