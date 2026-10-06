import base64
from copy import deepcopy

from apps.adviser_v2.demo.browser_sources import import_candidate
from apps.adviser_v2.demo.rejection_report import PARAPHRASE, paraphrase_only, summarize_rejections


def test_browser_viewer_html_is_not_a_pdf(tmp_path):
    row = {
        "insurer_id": "icici",
        "url": "https://www.icicilombard.com/elevate.pdf",
        "source_url": "https://www.icicilombard.com/downloads",
        "label": "Policy wordings",
        "status": 200,
        "data": "data:application/pdf;base64," + base64.b64encode(b"<html>viewer</html>").decode(),
    }
    result = import_candidate(row, tmp_path)
    assert result["status"] == "unavailable"
    assert "not PDF" in result["reason"]
    assert not (tmp_path / "objects").exists()


def test_official_pdf_cannot_be_imported_with_unverified_origin(tmp_path):
    result = import_candidate(
        {
            "insurer_id": "care",
            "url": "https://example.com/file.pdf",
            "source_url": "https://www.careinsurance.com/other-downloads.html",
        },
        tmp_path,
    )
    assert result["status"] == "unavailable"
    assert result["reason"] == "Unverified official source host."


def test_corrupt_pdf_is_retained_as_unavailable_instead_of_stopping_queue(tmp_path):
    row = {
        "insurer_id": "icici",
        "url": "https://www.icicilombard.com/elevate.pdf",
        "source_url": "https://www.icicilombard.com/downloads",
        "label": "Policy wordings",
        "status": 200,
        "data": "data:application/pdf;base64," + base64.b64encode(b"%PDF-1.7\ninvalid").decode(),
    }
    assert import_candidate(row, tmp_path)["status"] == "unavailable"


def test_raw_cache_reuses_physical_text_but_not_another_bundles_document_identity(tmp_path):
    import hashlib
    import json

    from apps.adviser_v2.demo.extraction import extract

    payload = b"%PDF-1.7\ncached original"
    sha = hashlib.sha256(payload).hexdigest()
    pdf = tmp_path / "source.pdf"
    pdf.write_bytes(payload)
    (tmp_path / "raw").mkdir()
    saved = {
        "pdf_sha256": sha,
        "version": "poppler-raw-ocr/1",
        "pages": [
            {
                "document_key": "old-key",
                "document_version_id": "old-id",
                "passage": "Exact original text",
                "physical_page": 1,
            }
        ],
    }
    path = tmp_path / "raw" / f"{sha}.json"
    path.write_text(json.dumps(saved))
    pages = extract(
        {
            "path": str(pdf),
            "sha256": sha,
            "document_key": "new-key",
            "document_version_id": "new-id",
        },
        tmp_path,
    )
    assert (
        pages[0]["document_version_id"] == "new-id" and pages[0]["passage"] == "Exact original text"
    )
    assert json.loads(path.read_text()) == saved


def test_inventory_preserves_uncertainty_and_excludes_administrative_items():
    from apps.adviser_v2.demo.catalogue import register_rows, scope

    assert scope("New India Floater Mediclaim")[0] == "review_pending"
    assert scope("Group Health", "ABC HLGP")[0] == "excluded"
    assert scope("Claims")[0] == "excluded"
    source = {
        "source_url": "https://www.icicilombard.com/downloads",
        "source_sha256": "sha",
        "retrieved_at": "now",
    }
    rows = register_rows(
        "icici",
        '<li>Elevate <a href="/elevate.pdf">Download PDF</a></li>'
        '<li>Group Health <a href="/group.pdf">Download PDF</a></li>',
        source,
    )
    assert len(rows) == 2
    assert rows[0]["name"] == "Elevate"
    assert rows[0]["edition_status"] == "unresolved"
    assert rows[0]["documents"][0]["role"] == "base_wording"
    assert rows[1]["scope"] == "excluded"


def test_only_paraphrase_failures_are_counted_separately():
    check = {
        "checks": [True, True, True, False, True, True],
        "problems": [PARAPHRASE],
        "rejected_wrong_plan": 0,
    }
    assert paraphrase_only(check)
    assert not paraphrase_only({**check, "problems": [PARAPHRASE, "Missing condition."]})
    assert not paraphrase_only({**check, "rejected_wrong_plan": 1})
    assert not paraphrase_only({**check, "checks": [True] * 6})
    assert not paraphrase_only(None)
    arm = {"status": "not_found", "validation": check, "attempts": [{"validation": check}]}
    corrected = deepcopy(arm)
    corrected.update(status="answered", validation={"checks": [True] * 6, "problems": []})
    corrected["attempts"].append({"validation": corrected["validation"]})
    rows = [
        {
            "job": {"kind": "answer", "id": "case"},
            "arms": {"H": arm, "P": corrected},
            "split_attempts": [{"H": arm, "P": arm}],
        },
        {
            "job": {"kind": "answer", "id": "unavailable"},
            "arms": {m: {"status": "documents_unavailable"} for m in ("H", "P")},
        },
    ]
    report = summarize_rejections(rows)["arms"]
    assert report["H"]["answer_cases"] == report["P"]["answer_cases"] == 2
    assert report["H"]["final_unanswered_only_paraphrase"] == 1
    assert report["P"]["final_unanswered_only_paraphrase"] == 0
    assert report["H"]["paraphrase_only_attempts"] == report["P"]["paraphrase_only_attempts"] == 1
    assert report["H"]["split_pair_paraphrase_only_attempts"] == 1
    assert report["H"]["case_ids"] == ["case"]
    rows.append({"job": {"kind": "star", "id": "reference-query"}, "arms": {"H": arm, "P": arm}})
    complete = summarize_rejections(rows)
    assert complete["arms"]["H"]["answer_cases"] == 2
    assert complete["star_query_arms"]["H"]["query_cases"] == 1
    assert complete["all_query_arms"]["H"]["query_cases"] == 3
    assert complete["all_query_arms"]["H"]["final_unanswered_only_paraphrase"] == 2
