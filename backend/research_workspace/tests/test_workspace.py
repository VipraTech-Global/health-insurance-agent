import io
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx
import pypdfium2
import pytest
from pydantic import ValidationError
from research_workspace.__main__ import build_register
from research_workspace.acquisition import acquire, allowed_url, document_links, reconcile_legacy
from research_workspace.benchmark import evaluation_report, freeze_evaluation, load_cases
from research_workspace.contracts import CaseRecord, EvaluationAttempt, EvidenceLocation
from research_workspace.storage import put_object, read_json, read_object, write_json


@pytest.mark.parametrize(
    "url",
    [
        "http://official.test/p.pdf",
        "https://official.test.evil.test/p.pdf",
        "https://evilofficial.test/p.pdf",
        "https://user:pass@official.test/p.pdf",
        "https://official.test:8443/p.pdf",
        "https://127.0.0.1/p.pdf",
    ],
)
def test_rejects_unapproved_destination(url: str) -> None:
    assert not allowed_url(url, ["official.test"])


def test_redirect_cannot_escape_allowlist(tmp_path: Path) -> None:
    calls = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(str(request.url))
        return httpx.Response(302, headers={"location": "https://private.test/secret"})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = acquire(
            tmp_path,
            "https://official.test/a.pdf",
            ["official.test"],
            client,
            insurer_id="test",
            expected_pdf=True,
        )
    assert calls == ["https://official.test/a.pdf"]
    assert result["issues"] == ["host_not_approved"]
    assert len(list((tmp_path / "registers/attempts").glob("*.json"))) == 1


def test_request_is_durable_before_network_and_timeout_remains_visible(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        records = list((tmp_path / "registers/attempts").glob("*.json"))
        assert len(records) == 1
        assert read_json(records[0])["status"] == "running"
        raise httpx.ReadTimeout("No response", request=request)

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        result = acquire(
            tmp_path,
            "https://official.test/p.pdf",
            ["official.test"],
            client,
            insurer_id="test",
            expected_pdf=True,
        )
    assert result["status"] == "failed" and result["issues"] == ["ReadTimeout"]
    records = list((tmp_path / "registers/attempts").glob("*.json"))
    assert read_json(records[0])["status"] == "failed"


def test_failed_http_body_is_preserved_without_becoming_a_document(tmp_path: Path) -> None:
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(403, content=b"access denied"))
    ) as client:
        result = acquire(
            tmp_path,
            "https://official.test/a.pdf",
            ["official.test"],
            client,
            insurer_id="test",
            expected_pdf=True,
        )
    assert result["status"] == "failed"
    assert result["page_count"] is None
    assert read_object(tmp_path, result["sha256"]) == b"access denied"


def test_html_cannot_masquerade_as_pdf(tmp_path: Path) -> None:
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(
                200, content=b"<html>login</html>", headers={"content-type": "text/html"}
            )
        )
    ) as client:
        result = acquire(
            tmp_path,
            "https://official.test/a.pdf",
            ["official.test"],
            client,
            insurer_id="test",
            expected_pdf=True,
        )
    assert result["status"] == "failed"
    assert result["issues"] == ["expected_pdf_received_other_content"]


def test_pdf_accounts_for_every_page_without_claiming_extraction(tmp_path: Path) -> None:
    pdf = pypdfium2.PdfDocument.new()
    for _ in range(3):
        pdf.new_page(100, 200)
    output = io.BytesIO()
    pdf.save(output)
    pdf.close()
    with httpx.Client(
        transport=httpx.MockTransport(lambda _: httpx.Response(200, content=output.getvalue()))
    ) as client:
        result = acquire(
            tmp_path,
            "https://official.test/a.pdf",
            ["official.test"],
            client,
            insurer_id="test",
            expected_pdf=True,
        )
    assert result["page_count"] == 3
    assert [page["page"] for page in result["pages"]] == [1, 2, 3]
    assert all(page["status"] == "preserved_not_read" for page in result["pages"])
    assert result["review_status"] == "not_reviewed"


def test_html_streaming_preserves_discovery_provenance(tmp_path: Path) -> None:
    html = b'<h2>Medical policy</h2><a href="/p.pdf?v=2#page=3">Wording</a>'
    with httpx.Client(
        transport=httpx.MockTransport(
            lambda _: httpx.Response(200, content=html, headers={"content-type": "text/html"})
        )
    ) as client:
        result = acquire(
            tmp_path,
            "https://official.test/downloads",
            ["official.test"],
            client,
            insurer_id="test",
        )
    assert result["links"][0]["url"] == "https://official.test/p.pdf?v=2"
    assert "Medical policy" in result["links"][0]["preceding_text"]
    assert read_object(tmp_path, result["sha256"]) == html


def test_same_url_changed_bytes_preserves_both_attempts(tmp_path: Path) -> None:
    for content in (b"first", b"second"):
        with httpx.Client(
            transport=httpx.MockTransport(
                lambda _, content=content: httpx.Response(200, content=content)
            )
        ) as client:
            acquire(
                tmp_path,
                "https://official.test/p.pdf",
                ["official.test"],
                client,
                insurer_id="test",
                expected_pdf=True,
            )
    rows = [read_json(p) for p in (tmp_path / "registers/attempts").glob("*.json")]
    assert len(rows) == 2
    assert {read_object(tmp_path, row["sha256"]) for row in rows} == {b"first", b"second"}


def test_concurrent_duplicate_bytes_store_one_complete_original(tmp_path: Path) -> None:
    content = b"original" * 20000
    with ThreadPoolExecutor(max_workers=4) as pool:
        hashes = list(pool.map(lambda _: put_object(tmp_path, content), range(12)))
    assert len(set(hashes)) == 1
    assert read_object(tmp_path, hashes[0]) == content
    assert len(list((tmp_path / "objects").rglob("*"))) == 2


def test_corruption_is_not_silently_repaired(tmp_path: Path) -> None:
    sha = put_object(tmp_path, b"original")
    (tmp_path / "objects" / sha[:2] / sha).write_bytes(b"corruption")
    with pytest.raises(ValueError, match="Corrupt"):
        read_object(tmp_path, sha)
    with pytest.raises(ValueError, match="Corrupt"):
        put_object(tmp_path, b"original")


def test_legacy_reconciliation_accounts_for_exact_set_without_fuzzy_matching(
    tmp_path: Path,
) -> None:
    legacy = tmp_path / "legacy.json"
    insurers = tmp_path / "insurers.json"
    write_json(insurers, [{"id": "care", "aliases": ["Care"]}])
    write_json(
        legacy,
        {
            "listings": [
                {"ditto_path": "/care/a", "displayed_name": "A", "insurer__name": "Care"},
                {"ditto_path": "/car/b", "displayed_name": "B", "insurer__name": "Car"},
            ]
        },
    )
    rows = reconcile_legacy(legacy, insurers)
    assert {r["legacy_identity"] for r in rows} == {"/care/a", "/car/b"}
    assert rows[0]["status"] == "unresolved_product_identity"
    assert rows[1]["insurer_id"] is None
    assert all(r["product_version_id"] is None for r in rows)


def test_unknown_denominator_never_becomes_ninety_percent(tmp_path: Path) -> None:
    write_json(tmp_path / "seeds/insurers.json", [{"id": "care", "name": "Care"}])
    report = build_register(tmp_path)
    assert report["rule_coverage_percent"] is None
    assert report["insurers"][0]["rule_coverage_percent"] is None
    assert not report["release_ready"]


def case(family: int = 1, number: int = 1, **changes: object) -> CaseRecord:
    values = dict(
        case_id=f"eval-{family:02d}-{number:02d}",
        split="evaluation",
        family=family,
        title="Test-only worked fixture",
        decision_distinction=f"fixture-{family}-{number}",
        factors=("age", "budget"),
        boundary="inclusive maximum",
        customer_facts={"age": 35},
        conversation=("A question", "A clarification"),
        known=("age",),
        unknown=(),
        corrections=(),
        required_information=(),
        candidate_configurations=("test-configuration",),
        exclusion_reasons=(),
        expected_answer="Test fixture only",
        acceptable_alternatives=(),
        evidence=(
            EvidenceLocation(
                source_sha256="a" * 64, page=1, passage="test passage", section="test section"
            ),
        ),
        evidence_requirements=(),
        calculations=(),
        gaps=(),
        information_map=("age",),
        pass_criteria=("test criterion",),
        assessment="worked",
    )
    values.update(changes)
    return CaseRecord.model_validate(values)


def attempt(c: CaseRecord, n: int, **changes: object) -> EvaluationAttempt:
    values = dict(
        case_id=c.case_id,
        attempt=n,
        release_id="test-release",
        conversation_id=f"{c.case_id}-{n}",
        result="pass",
        material_criteria_passed=True,
        essential_evidence_complete=True,
        critical_failures=(),
        artifact_sha256="b" * 64,
    )
    values.update(changes)
    return EvaluationAttempt.model_validate(values)


def test_missing_evidence_cannot_be_marked_worked() -> None:
    with pytest.raises(ValidationError, match="original evidence"):
        case(evidence=())
    with pytest.raises(ValidationError, match="essential gaps"):
        case(gaps=("missing hospital observation",))


def test_three_independent_attempts_required_and_failures_retained() -> None:
    c = case()
    report = evaluation_report([c], [attempt(c, 1), attempt(c, 2)], "test-release")
    assert report["passed"] == 0 and report["missing_attempts"] == 1
    report = evaluation_report(
        [c], [attempt(c, 1), attempt(c, 2), attempt(c, 3, result="timeout")], "test-release"
    )
    assert report["passed"] == 0


def test_honest_evidence_gap_is_not_full_completion() -> None:
    c = case()
    runs = [attempt(c, n, essential_evidence_complete=False) for n in (1, 2, 3)]
    assert evaluation_report([c], runs, "test-release")["passed"] == 0


def test_duplicate_runs_and_reused_conversations_rejected() -> None:
    c = case()
    with pytest.raises(ValueError, match="Duplicate attempt"):
        evaluation_report([c], [attempt(c, 1), attempt(c, 1)], "test-release")
    with pytest.raises(ValueError, match="fresh conversation"):
        evaluation_report(
            [c], [attempt(c, 1), attempt(c, 2, conversation_id=f"{c.case_id}-1")], "test-release"
        )


def test_overall_ninety_percent_cannot_hide_failing_family_or_critical_failure() -> None:
    cases = [case(f, n) for f in range(1, 21) for n in range(1, 11)]
    runs = [
        attempt(c, n, result="fail" if c.family == 1 else "pass") for c in cases for n in (1, 2, 3)
    ]
    report = evaluation_report(cases, runs, "test-release")
    assert report["passed"] == 190 and not report["advice_target_passed"]
    runs = [attempt(c, n) for c in cases for n in (1, 2, 3)]
    runs[0] = attempt(cases[0], 1, critical_failures=("cross-customer data leak",))
    report = evaluation_report(cases, runs, "test-release")
    assert report["passed"] == 199 and not report["advice_target_passed"]


def test_frozen_drafts_are_rejected_and_duplicates_detected(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    c = case(assessment="draft", evidence=())
    path.write_text(c.model_dump_json() + "\n")
    with pytest.raises(ValueError, match="200"):
        freeze_evaluation(path, tmp_path / "frozen", tmp_path)
    path.write_text(c.model_dump_json() + "\n" + c.model_dump_json() + "\n")
    with pytest.raises(ValueError, match="Duplicate"):
        load_cases(path)


def test_structurally_worked_cases_cannot_freeze_with_missing_originals(tmp_path: Path) -> None:
    path = tmp_path / "cases.jsonl"
    cases = [case(f, n) for f in range(1, 21) for n in range(1, 11)]
    path.write_text("".join(c.model_dump_json() + "\n" for c in cases))
    with pytest.raises(FileNotFoundError):
        freeze_evaluation(path, tmp_path / "frozen", tmp_path)
    assert not (tmp_path / "frozen").exists()


def test_link_discovery_keeps_attachment_query_identity() -> None:
    links = document_links(
        '<a href="x.pdf?v=1">Old</a><a href="x.pdf?v=2">New</a>', "https://official.test/"
    )
    assert [r["url"] for r in links] == [
        "https://official.test/x.pdf?v=1",
        "https://official.test/x.pdf?v=2",
    ]


def test_document_base_href_controls_relative_downloads() -> None:
    links = document_links(
        '<base href="/"><a href="assets/policy.pdf">Wording</a>',
        "https://official.test/health/product",
    )
    assert links[0]["url"] == "https://official.test/assets/policy.pdf"
    assert links[0]["raw_href"] == "assets/policy.pdf"
