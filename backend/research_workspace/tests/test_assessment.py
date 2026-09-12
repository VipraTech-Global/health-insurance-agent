"""Regression checks for evidence-accounting failures, without application/benchmark access."""

import hashlib
import json
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest
from research_workspace.assessment import build_triage, inspect_pdf
from research_workspace.storage import put_object, write_json


def test_invalid_register_identifier_cannot_escape_report_directory(tmp_path: Path) -> None:
    write_json(
        tmp_path / "registers/attempts/bad.json",
        {
            "status": "acquired",
            "document_type": "pdf_unclassified",
            "sha256": "../../escaped",
            "insurer_id": "example",
            "url": "https://example.com/a.pdf",
            "acquired_at": "2026-09-10",
        },
    )
    with pytest.raises(ValueError, match="Invalid SHA-256"):
        build_triage(tmp_path, workers=1)
    assert not (tmp_path / "escaped.json").exists()
    assert not (tmp_path / "reports/document-triage.json").exists()


def test_corrupt_orphan_is_counted_even_when_pdf_header_is_damaged(tmp_path: Path) -> None:
    sha = hashlib.sha256(b"%PDF-original").hexdigest()
    path = tmp_path / "objects" / sha[:2] / sha
    path.parent.mkdir(parents=True)
    path.write_bytes(b"damaged header")
    report = build_triage(tmp_path, workers=1)
    assert report["all_preserved_objects"]["integrity_failure"] == 1
    assert report["reading_status"] == {"failed": 1}
    assert report["objects_considered"] == 1
    record = json.loads((tmp_path / "assessment/document-previews" / f"{sha}.json").read_text())
    assert record["error_category"] == "original_integrity_or_media_error"
    assert "Corrupt object" in record["diagnostic"]


def test_keyword_previews_never_establish_scope_or_coverage(tmp_path: Path) -> None:
    sha = put_object(tmp_path, b"%PDF-synthetic-reader-fixture")
    with patch(
        "research_workspace.assessment.subprocess.run",
        return_value=CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"Health insurance and hospital cash\f",
            stderr=b"",
        ),
    ):
        report = build_triage(tmp_path, workers=1)
    record = json.loads((tmp_path / "assessment/document-previews" / f"{sha}.json").read_text())
    assert len(record["signals"]) == 2
    assert record["scope_status"] == "unresolved"
    assert report["resolved_scope_count"] == 0
    assert report["independent_rule_denominator"] is None
    assert not report["design_ready"]


def test_reader_with_no_text_requires_further_reading(tmp_path: Path) -> None:
    sha = put_object(tmp_path, b"%PDF-synthetic-reader-fixture")
    with patch(
        "research_workspace.assessment.subprocess.run",
        return_value=CompletedProcess(
            args=[],
            returncode=0,
            stdout=b"\f\f",
            stderr=b"",
        ),
    ):
        record = inspect_pdf(tmp_path, sha)
    assert record["reading_status"] == "no_text_requires_visual_or_ocr"
    assert record["scope_status"] == "unresolved"
