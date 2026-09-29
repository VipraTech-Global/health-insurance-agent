"""Fail-closed checks for Star document identity triage."""

from pathlib import Path

import pytest
from research_workspace import star_document_triage


def _source() -> dict:
    return {
        "products": [
            {
                "uin": "SHAHLIP26048V032526",
                "name": "Star Health Assure",
                "comparison_scope": "internal_pilot",
            }
        ],
        "documents": [
            {
                "url": "https://example.test/one.pdf",
                "role": role,
                "candidate_product_uins": ["SHAHLIP26048V032526"],
            }
            for role in ("policy_wording", "modern_treatment_schedule", "excluded_expenses")
        ],
    }


def test_cross_role_listing_and_conflicting_heading_remain_unresolved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(star_document_triage, "read_object", lambda *_: b"%PDF-test")
    monkeypatch.setattr(
        star_document_triage,
        "_pdf_text",
        lambda _: (
            "SHAHLIP26048V032526\nPOL / SS / V.1 / 2024\n"
            "Items for which coverage is available in the policy\n"
            "(Not Applicable if Optional Cover Consumables is opted by the insured)"
        ),
    )
    captures = {
        "https://example.test/one.pdf": {
            "status": "acquired",
            "sha256": "a" * 64,
            "page_count": 1,
        }
    }
    result = star_document_triage.triage(_source(), captures, Path("/unused"))
    assert result["accounting"]["cross_role_url_count"] == 1
    assert result["accounting"]["review_role_associations"] == 3
    assert result["documents"][0]["excluded_expenses_heading_phrase"] == "coverage_available"
    assert result["accounting"]["excluded_expenses_option_condition_urls"] == 1
    assert result["products"][0]["candidate_uin_found_in_all_review_pdfs"]
    assert not result["products"][0]["applicable_bundle_complete"]
    assert not result["catalogue_complete"]


def test_unacquired_candidate_pdf_blocks_triage() -> None:
    with pytest.raises(ValueError, match="not acquired"):
        star_document_triage.triage(_source(), {}, Path("/unused"))
