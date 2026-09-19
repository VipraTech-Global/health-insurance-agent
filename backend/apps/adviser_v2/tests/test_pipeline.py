from __future__ import annotations

import copy
import uuid
from datetime import timedelta
from types import SimpleNamespace
from typing import Any, cast

import pytest
from django.db import DatabaseError, transaction
from django.utils import timezone

from apps.adviser_v2 import pipeline as pipeline_module
from apps.adviser_v2.models import (
    AuditEvent,
    DiscoveryRun,
    DocumentPage,
    DocumentSeries,
    DocumentVersion,
    EvidenceSpan,
    Insurer,
    OriginalFile,
    Outbox,
    PolicyRule,
    PolicyRuleEvidence,
    PolicySearchChunk,
    PolicyVersion,
    PolicyVersionDocument,
    ProcessingJob,
    Product,
    ProductVariant,
    SourceCapture,
    SourceURL,
)
from apps.adviser_v2.pipeline import (
    ADAPTER_VERSION,
    MAX_READ_PROCESSING_LEASE,
    NEXT_STAGE,
    READ_PROCESSING_LEASE,
    READ_PROCESSING_MINUTES_PER_PAGE,
    StaleProcessingLease,
    _claim_job,
    _finish_job,
    _rule_scope_identity,
    enqueue_stage,
    process_job,
)
from apps.adviser_v2.processing.adjudication import (
    _reader_text,
    adjudicate_classification,
    adjudicate_reconciliation,
    unresolved_issue_pages,
    validate_manual_transcriptions,
    validate_page_selections,
)
from apps.adviser_v2.processing.artifacts import read_artifact, write_artifact
from apps.adviser_v2.processing.readers import _table_text, classify_bytes
from apps.adviser_v2.processing.stages import (
    INVENTORY_CATEGORIES,
    INVENTORY_CATEGORY_BATCHES,
    RECONCILIATION_VERSION,
    RULE_PROMPT_VERSION,
    RULE_REVIEW_PROMPT_VERSION,
    RULE_VALIDATOR_VERSION,
    STAGE_RUNNERS,
    _bundle_passages,
    _combine_extraction_batches,
    _combine_extraction_evidence_batches,
    _combine_review_batches,
    _docling_page_table_text,
    _extraction_batch_targets,
    _get_or_create_policy_rule_revision,
    _has_meaningful_native_table,
    _line_group,
    _native_table_evidence,
    _native_table_text,
    _normalized_similarity,
    _passage_payloads,
    _request_ocr_for_layout_disagreements,
    _review_batch_targets,
    _selected_variant_name,
    _span_groups,
    index_policy_version,
    run_index,
)
from apps.adviser_v2.schemas import PolicyRuleExtractionV1, PolicyRuleReviewV1
from apps.adviser_v2.storage import store_public


def identifiers() -> list[dict[str, str]]:
    return [
        {
            "issuer": "Example Insurer",
            "kind": "uin",
            "value": "EXAMPLE-UIN",
            "status": "observed",
        }
    ]


def public_html_capture() -> SourceCapture:
    insurer = Insurer.objects.create(name="Example Insurer")
    run = DiscoveryRun.objects.create(
        insurer=insurer,
        instructions="Fixed test URL only.",
        session_id="fixed-test-html",
        model_name="none",
        completed_at=timezone.now(),
        status="completed",
    )
    source = SourceURL.objects.create(url="https://example.com/product", source_type="insurer_site")
    payload = (
        b"<html><body><h1>Example health product</h1><p>Currently available.</p></body></html>"
    )
    stored = store_public(payload)
    original = OriginalFile.objects.create(
        sha256=stored.plaintext_sha256,
        storage_key=stored.storage_key,
        byte_size=stored.plaintext_size,
        media_type="text/html",
    )
    series = DocumentSeries.objects.create(
        issuer=insurer,
        name="Example product page",
        kind="web_page",
        authority="insurer_issued",
        relevance="relevant",
    )
    version = DocumentVersion.objects.create(
        document_series=series,
        version_label=stored.plaintext_sha256,
        identifiers=identifiers(),
    )
    return SourceCapture.objects.create(
        discovery_run=run,
        source_url=source,
        completed_at=timezone.now(),
        status="captured",
        http_status=200,
        original_file=original,
        document_version=version,
    )


def rule_revision_policy() -> PolicyVersion:
    capture = public_html_capture()
    enqueue_stage(stage="classify", source_capture=capture)
    while queued := ProcessingJob.objects.filter(source_capture=capture, state="queued").first():
        process_job(queued.id)
    span = EvidenceSpan.objects.get(source_capture=capture)
    product = Product.objects.create(
        insurer=capture.discovery_run.insurer,
        name="Rule revision test product",
        benefit_type="medical_indemnity",
        lifecycle_status="open",
        recommendation_role="primary_policy",
        identity_evidence=span,
    )
    return PolicyVersion.objects.create(
        product=product,
        uin="RULE-REVISION-UIN",
        version_label="Current",
        applicability={
            "schema_version": 1,
            "predicate": {"node": "constant", "value": "true"},
            "event_basis": ["issue"],
            "source_span_ids": [str(span.id)],
            "unresolved": [],
        },
    )


def rule_revision_body(span_id: str) -> dict[str, object]:
    return {
        "schema_version": 1,
        "applies_when": {"node": "constant", "value": "true"},
        "inputs": [],
        "effects": [
            {
                "kind": "definition",
                "target_key": "test.term",
                "scope": {
                    "subject": "policy",
                    "subject_ids": [],
                    "period": "policy_term",
                    "benefit_keys": [],
                    "reset": "never",
                },
                "term_key": "test.term",
                "value": {"node": "literal", "value": {"kind": "boolean", "value": True}},
            }
        ],
        "mandatory_rule_keys": [],
        "source_span_ids": [span_id],
        "unresolved": [],
        "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
    }


def test_html_pipeline_is_resumable_and_records_reconciled_evidence(db: None) -> None:
    capture = public_html_capture()
    first = enqueue_stage(stage="classify", source_capture=capture)
    same = enqueue_stage(stage="classify", source_capture=capture)
    assert same.id == first.id
    while True:
        queued = ProcessingJob.objects.filter(source_capture=capture, state="queued").first()
        if queued is None:
            break
        process_job(queued.id)
    jobs = list(ProcessingJob.objects.filter(source_capture=capture).order_by("created_at"))
    assert [item.stage for item in jobs] == ["classify", "read", "ocr", "reconcile"]
    assert all(item.state == "succeeded" for item in jobs)
    artifact = read_artifact(jobs[-1])
    assert artifact["page_count"] == 1
    assert artifact["reconciliation_version"] == RECONCILIATION_VERSION
    assert EvidenceSpan.objects.filter(source_capture=capture).exists()
    capture.document_version.refresh_from_db()
    assert capture.document_version.review_status == "verified"


def test_policy_rule_revision_is_idempotent_and_appends_one_lineage_head(db: None) -> None:
    policy = rule_revision_policy()
    body = rule_revision_body(str(policy.product.identity_evidence_id))

    first = _get_or_create_policy_rule_revision(
        policy_version=policy,
        rule_key="definition.test.term",
        rule_type="definition",
        body=body,
    )
    same = _get_or_create_policy_rule_revision(
        policy_version=policy,
        rule_key="definition.test.term",
        rule_type="definition",
        body=body,
    )
    corrected_body = copy.deepcopy(body)
    corrected_body["unresolved"] = ["The definition was corrected."]
    corrected = _get_or_create_policy_rule_revision(
        policy_version=policy,
        rule_key="definition.test.term",
        rule_type="definition",
        body=corrected_body,
    )

    assert same.id == first.id
    assert corrected.id != first.id
    assert corrected.supersedes_id == first.id
    assert (
        PolicyRule.objects.filter(
            policy_version=policy,
            rule_key="definition.test.term",
        ).count()
        == 2
    )


def test_policy_rule_revision_rejects_multiple_existing_heads(db: None) -> None:
    policy = rule_revision_policy()
    span_id = str(policy.product.identity_evidence_id)
    body = rule_revision_body(span_id)
    PolicyRule.objects.create(
        policy_version=policy,
        rule_key="definition.conflicted.term",
        rule_type="definition",
        body=body,
    )
    PolicyRule.objects.create(
        policy_version=policy,
        rule_key="definition.conflicted.term",
        rule_type="definition",
        body={**body, "unresolved": ["second head"]},
    )

    with pytest.raises(ValueError, match="exactly one lineage head"):
        _get_or_create_policy_rule_revision(
            policy_version=policy,
            rule_key="definition.conflicted.term",
            rule_type="definition",
            body=body,
        )


def test_reconciliation_version_participates_in_job_identity(
    db: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    capture = public_html_capture()
    parent = ProcessingJob.objects.create(
        source_capture=capture,
        stage="ocr",
        adapter_version=ADAPTER_VERSION,
        input_commitment="e" * 64,
        state="succeeded",
    )
    first = enqueue_stage(stage="reconcile", source_capture=capture, parent_job=parent)

    monkeypatch.setattr(
        pipeline_module,
        "RECONCILIATION_VERSION",
        "coverguide-reconciliation/test-next",
    )
    second = enqueue_stage(stage="reconcile", source_capture=capture, parent_job=parent)

    assert second.id != first.id


def test_read_stage_lease_covers_long_cpu_document_passes(db: None) -> None:
    capture = public_html_capture()
    job = ProcessingJob.objects.create(
        source_capture=capture,
        stage="read",
        adapter_version=ADAPTER_VERSION,
        input_commitment="f" * 64,
    )
    before = timezone.now()

    claimed = _claim_job(job.id)

    assert claimed is not None
    claimed_job, _token, _generation = claimed
    assert claimed_job.lease_until is not None
    assert claimed_job.lease_until >= before + READ_PROCESSING_LEASE - timedelta(seconds=1)


def test_read_stage_lease_scales_with_known_page_count(db: None) -> None:
    capture = public_html_capture()
    page_count = 100
    DocumentPage.objects.bulk_create(
        [
            DocumentPage(original_file=capture.original_file, page_number=page_number)
            for page_number in range(1, page_count + 1)
        ]
    )
    job = ProcessingJob.objects.create(
        source_capture=capture,
        stage="read",
        adapter_version=ADAPTER_VERSION,
        input_commitment="a" * 64,
    )
    before = timezone.now()

    claimed = _claim_job(job.id)

    assert claimed is not None
    claimed_job, _token, _generation = claimed
    assert claimed_job.lease_until is not None
    expected_lease = timedelta(minutes=page_count * READ_PROCESSING_MINUTES_PER_PAGE)
    assert claimed_job.lease_until >= before + expected_lease - timedelta(seconds=1)
    assert claimed_job.lease_until <= timezone.now() + expected_lease


def test_read_stage_lease_has_a_bounded_cap(db: None) -> None:
    capture = public_html_capture()
    DocumentPage.objects.bulk_create(
        [
            DocumentPage(
                original_file=capture.original_file,
                page_number=page_number,
            )
            for page_number in range(1, 401)
        ]
    )
    job = ProcessingJob.objects.create(
        source_capture=capture,
        stage="read",
        adapter_version=ADAPTER_VERSION,
        input_commitment="d" * 64,
    )
    before = timezone.now()

    claimed = _claim_job(job.id)

    assert claimed is not None
    claimed_job, _token, _generation = claimed
    assert claimed_job.lease_until is not None
    assert claimed_job.lease_until >= before + MAX_READ_PROCESSING_LEASE - timedelta(seconds=1)
    assert claimed_job.lease_until <= timezone.now() + MAX_READ_PROCESSING_LEASE


def test_expired_processing_job_is_reclaimed_with_a_new_fence(db: None) -> None:
    capture = public_html_capture()
    job = enqueue_stage(stage="classify", source_capture=capture)
    first_claim = _claim_job(job.id)
    assert first_claim is not None
    first_job, first_token, erasure_generation = first_claim
    ProcessingJob.objects.filter(pk=job.id).update(
        lease_until=timezone.now() - timedelta(seconds=1)
    )
    with pytest.raises(DatabaseError, match="unfenced"):
        with transaction.atomic():
            ProcessingJob.objects.filter(pk=job.id).update(
                state="queued",
                lease_token=None,
                lease_until=None,
            )

    second_claim = _claim_job(job.id)

    assert second_claim is not None
    second_job, second_token, _second_generation = second_claim
    assert second_token != first_token
    assert second_job.state == "running"
    assert second_job.lease_until is not None
    assert second_job.lease_until > timezone.now()
    outbox = Outbox.objects.get(processing_job=job)
    assert outbox.attempt_count == 0
    assert (
        AuditEvent.objects.filter(
            operation="processing_lease_recovered",
            object_id=job.id,
            outcome="succeeded",
        ).count()
        == 1
    )
    with pytest.raises(StaleProcessingLease, match="processing_lease_stale"):
        _finish_job(
            first_job,
            first_token,
            state="succeeded",
            result=None,
            issues=[],
            expected_erasure_generation=erasure_generation,
        )


def test_generic_buying_document_can_be_relevant_without_false_disagreement() -> None:
    result = classify_bytes(
        b"<html><body>Proposal form with optional add-on questions.</body></html>",
        "other",
    )

    assert result["relevant"] is True
    assert result["issues"] == []


def test_line_group_locator_is_bounded_to_the_physical_page() -> None:
    _text, bbox = _line_group(
        [
            {
                "text": "Rotated disclosure row",
                "x0": -12.0,
                "top": -179.0,
                "x1": 1380.0,
                "bottom": 659.0,
            }
        ],
        width=842.0,
        height=595.0,
    )

    assert bbox == [0.0, 0.0, 842.0, 595.0]


def test_reader_similarity_compares_token_coverage_not_layout_order() -> None:
    assert _normalized_similarity("room rent limit", "limit room rent") == 1.0
    assert _normalized_similarity("room rent limit and waiting period", "room rent") < 0.5


def test_reader_disagreement_requests_ocr_and_records_why() -> None:
    native = {
        "pages": [
            {
                "page_number": 3,
                "text": "visible disclosure plus hidden duplicated unrelated content",
                "needs_ocr": False,
                "unreliable_reasons": [],
            }
        ]
    }
    layout = {
        "nodes": [
            {
                "text": "visible disclosure",
                "provenance": [{"page_no": 3}],
            }
        ]
    }

    assert _request_ocr_for_layout_disagreements(native, layout) == [3]
    assert native["pages"][0]["needs_ocr"] is True
    assert native["pages"][0]["unreliable_reasons"] == ["native_layout_disagreement"]


def test_ocr_evidence_does_not_reuse_unreliable_native_lines() -> None:
    page = {
        "width": 100.0,
        "height": 200.0,
        "lines": [{"text": "hidden native text", "x0": 1, "top": 2, "x1": 10, "bottom": 12}],
    }

    groups = _span_groups(page, "visible OCR text", use_native_lines=False)

    assert groups == [("visible OCR text", [0.0, 0.0, 100.0, 200.0])]


def test_table_reconciliation_ignores_decorative_footer_grids() -> None:
    assert not _has_meaningful_native_table({"tables": [[["UIN", None, None], [None, None, None]]]})
    assert _has_meaningful_native_table({"tables": [[["Age", "5L"], ["30", "100"], ["31", "105"]]]})


def test_table_evidence_preserves_compact_grid_without_promoting_reader_conflict() -> None:
    page = {"tables": [[["Benefit", "Limit"], ["ICU", "No sub-limit"]]]}

    assert not _has_meaningful_native_table(page)
    assert len(_native_table_evidence(page)) == 1
    assert not _native_table_evidence({"tables": [[["UIN", None, None], [None, None, None]]]})


def test_table_reader_comparison_excludes_decorative_grids_and_detects_missing_cells() -> None:
    page = {
        "tables": [
            [["UIN", None, None], [None, None, None]],
            [["Age", "5L"], ["30", "100"], ["31", "105"]],
        ]
    }
    layout = {
        "nodes": [
            {
                "label": "table",
                "text": "Age | 5L\n30 | 100",
                "provenance": [{"page_no": 4}],
            }
        ]
    }

    native = _native_table_text(page)
    docling = _docling_page_table_text(layout)[4]

    assert "UIN" not in native
    assert "31 | 105" in native
    assert _normalized_similarity(native, docling) < 0.80


def test_native_table_evidence_preserves_explicit_grid_coordinates() -> None:
    tables = _native_table_evidence({"tables": [[["Age", "5L"], ["30", "100"], ["31", "105"]]]})

    assert len(tables) == 1
    table_index, quote, context = tables[0]
    assert table_index == 1
    assert 'row=0;values=["Age", "5L"]' in quote
    assert context["table"]["cell_coordinates"] == [
        'table=1;row=0;column=0;value="Age"',
        'table=1;row=0;column=1;value="5L"',
        'table=1;row=1;column=0;value="30"',
        'table=1;row=1;column=1;value="100"',
        'table=1;row=2;column=0;value="31"',
        'table=1;row=2;column=1;value="105"',
    ]


def test_docling_table_cells_are_preserved_as_ordered_text() -> None:
    def cell(row: int, column: int, text: str) -> object:
        return type(
            "Cell",
            (),
            {
                "start_row_offset_idx": row,
                "start_col_offset_idx": column,
                "text": text,
            },
        )()

    item = type(
        "Table",
        (),
        {
            "data": type(
                "Data", (), {"table_cells": [cell(1, 0, "30"), cell(0, 1, "5L"), cell(0, 0, "Age")]}
            )()
        },
    )()

    assert _table_text(item) == "Age | 5L\n30"


def test_visual_adjudication_requires_the_exact_issue_page_set() -> None:
    issues = [
        {
            "code": "reader_text_disagreement",
            "description": "Readers disagree on physical page 3 (similarity 0.400).",
            "material": True,
            "resolved": False,
        },
        {
            "code": "reader_table_disagreement",
            "description": "A table differs on physical page 4.",
            "material": True,
            "resolved": False,
        },
    ]

    assert unresolved_issue_pages(issues) == {3, 4}
    validate_page_selections(issues, {3: "native", 4: "ocr"})

    try:
        validate_page_selections(issues, {3: "native"})
    except ValueError as exc:
        assert "missing=4" in str(exc)
    else:
        raise AssertionError("A partial visual adjudication must fail closed.")


def test_manual_transcription_must_exactly_match_manual_reader_pages() -> None:
    validate_manual_transcriptions(
        {3: "manual", 4: "ocr"}, {3: "Exact text transcribed from physical page 3."}
    )

    for transcriptions in ({}, {3: "Exact text.", 4: "Unexpected text."}, {3: "  "}):
        try:
            validate_manual_transcriptions({3: "manual", 4: "ocr"}, transcriptions)
        except ValueError:
            continue
        raise AssertionError("Incomplete, extra or blank manual transcription must fail closed.")

    page = {"page_number": 3, "text": "Unusable native text."}
    _page, text, method = _reader_text(
        {"native": {"pages": [page]}, "ocr": {"pages": {"3": "Noisy OCR."}}},
        3,
        "manual",
        "Exact visual transcription.",
    )
    assert text == "Exact visual transcription."
    assert method == "manual_visual"


def test_classification_adjudication_is_audited_and_idempotent(db: None) -> None:
    capture = public_html_capture()
    blocker = {
        "code": "classification_disagreement",
        "region_span_ids": [],
        "description": "Declared prospectus; content markers suggest premium_table.",
        "material": True,
        "retry_instruction": "Review the exact document role and manifest entry.",
        "resolved": False,
    }
    job = ProcessingJob.objects.create(
        source_capture=capture,
        stage="classify",
        adapter_version="test-adapter",
        input_commitment="c" * 64,
        state="blocked",
        issues=[blocker],
        error_code="classification_disagreement",
    )
    job.result_storage_key, job.result_storage_sha256 = write_artifact(
        job,
        {
            "schema_version": 1,
            "media_type": "application/pdf",
            "declared_kind": "prospectus",
            "inferred_kind": "prospectus",
            "observed_markers": ["premium_table"],
            "page_count": 11,
            "relevant": True,
            "issues": [blocker],
        },
    )
    job.save(update_fields=["result_storage_key", "result_storage_sha256"])
    note = "Rendered title confirms this is an annexure to the product prospectus."

    adjudicated = adjudicate_classification(job.id, "prospectus", note)
    replayed = adjudicate_classification(job.id, "prospectus", note)

    adjudicated.refresh_from_db()
    assert replayed.id == adjudicated.id
    assert adjudicated.state == "succeeded"
    assert adjudicated.error_code is None
    assert adjudicated.issues[0]["resolved"] is True
    result = read_artifact(adjudicated)
    assert result["inferred_kind"] == "prospectus"
    assert result["classification_adjudication"] == {
        "schema_version": 1,
        "accepted_kind": "prospectus",
        "review_note": note,
    }
    assert result["pre_adjudication_artifact"]["storage_key"] is not None
    assert (
        AuditEvent.objects.filter(
            operation="corpus_classification_adjudication", object_id=job.id
        ).count()
        == 1
    )


def test_visual_adjudication_is_durable_audited_and_idempotent(db: None) -> None:
    capture = public_html_capture()
    original = capture.original_file
    assert original is not None
    original.media_type = "application/pdf"
    original.save(update_fields=["media_type"])
    page = DocumentPage.objects.create(
        original_file=original,
        page_number=1,
        review_state="unresolved",
    )
    parent = ProcessingJob.objects.create(
        source_capture=capture,
        stage="ocr",
        adapter_version="test-adapter",
        input_commitment="a" * 64,
        state="succeeded",
    )
    reader_artifact = {
        "schema_version": 1,
        "native": {
            "pages": [
                {
                    "page_number": 1,
                    "width": 100.0,
                    "height": 200.0,
                    "rotation": 0,
                    "text": "Exact visually confirmed policy wording.",
                    "tables": [[["Age", "5L"], ["30", "100"], ["31", "105"]]],
                    "lines": [
                        {
                            "text": "Exact visually confirmed policy wording.",
                            "x0": 2.0,
                            "top": 3.0,
                            "x1": 90.0,
                            "bottom": 12.0,
                        }
                    ],
                }
            ]
        },
        "ocr": {"pages": {}},
    }
    parent.result_storage_key, parent.result_storage_sha256 = write_artifact(
        parent, reader_artifact
    )
    parent.save(update_fields=["result_storage_key", "result_storage_sha256"])
    issue = {
        "code": "reader_text_disagreement",
        "region_span_ids": [],
        "description": "Readers disagree on physical page 1 (similarity 0.400).",
        "material": True,
        "retry_instruction": "Visually reconcile the exact page.",
        "resolved": False,
    }
    job = ProcessingJob.objects.create(
        source_capture=capture,
        stage="reconcile",
        adapter_version="test-adapter",
        input_commitment="b" * 64,
        parent_job=parent,
        state="blocked",
        issues=[issue],
        error_code="reader_text_disagreement",
    )
    job.result_storage_key, job.result_storage_sha256 = write_artifact(
        job,
        {
            "schema_version": 1,
            "document_sha256": original.sha256,
            "page_count": 1,
            "page_numbers": [1],
            "evidence_spans": [],
            "issues": [issue],
        },
    )
    job.save(update_fields=["result_storage_key", "result_storage_sha256"])
    old_storage_key = job.result_storage_key
    note = "Rendered page and native passage were compared line by line."

    adjudicated = adjudicate_reconciliation(job.id, {1: "native"}, note)
    replayed = adjudicate_reconciliation(job.id, {1: "native"}, note)

    adjudicated.refresh_from_db()
    page.refresh_from_db()
    assert replayed.id == adjudicated.id
    assert adjudicated.state == "succeeded"
    assert adjudicated.error_code is None
    assert adjudicated.issues[0]["resolved"] is True
    assert page.review_state == "fully_reviewed"
    spans = list(EvidenceSpan.objects.filter(source_capture=capture, page=page))
    assert len(spans) == 2
    text_span = next(item for item in spans if item.section_label.startswith("processed-page-"))
    table_span = next(item for item in spans if item.section_label.startswith("processed-table-"))
    assert text_span.quote == "Exact visually confirmed policy wording."
    assert text_span.verification == "visually_verified"
    assert table_span.verification == "visually_verified"
    assert table_span.context["table"]["cell_coordinates"][0] == (
        'table=1;row=0;column=0;value="Age"'
    )
    result = read_artifact(adjudicated)
    assert result["pre_adjudication_artifact"]["storage_key"] == old_storage_key
    assert result["visual_adjudication"]["page_reader_selections"] == {"1": "native"}
    assert (
        AuditEvent.objects.filter(operation="corpus_visual_adjudication", object_id=job.id).count()
        == 1
    )


def test_bundle_passages_use_only_latest_capture_for_each_document(db: None) -> None:
    first = public_html_capture()

    def evidence(capture: SourceCapture, quote: str) -> EvidenceSpan:
        assert capture.original_file is not None
        return EvidenceSpan.objects.create(
            source_capture=capture,
            quote=quote,
            context={"span_ids": [], "notes": ["Test passage."]},
            method="html",
            verification="text_verified",
            locator={
                "schema_version": 1,
                "blob_sha256": capture.original_file.sha256,
                "resolver_version": "coverguide-html/1",
                "kind": "html_element",
                "encoding": "utf-8",
                "selector": "body",
                "selector_language": "css",
                "occurrence": 0,
                "text_interpretation": "decoded_text_content",
                "attribute_name": None,
            },
        )

    old_span = evidence(first, "Superseded captured passage.")
    second_run = DiscoveryRun.objects.create(
        insurer=first.discovery_run.insurer,
        instructions="Fixed replacement test URL only.",
        session_id="fixed-test-html-replacement",
        model_name="none",
        completed_at=timezone.now(),
        status="completed",
    )
    second_url = SourceURL.objects.create(
        url="https://example.com/product?revision=2",
        source_type="insurer_site",
    )
    assert first.completed_at is not None
    second = SourceCapture.objects.create(
        discovery_run=second_run,
        source_url=second_url,
        completed_at=first.completed_at + timedelta(seconds=1),
        status="captured",
        http_status=200,
        original_file=first.original_file,
        document_version=first.document_version,
    )
    current_span = evidence(second, "Current frozen captured passage.")
    product = Product.objects.create(
        insurer=first.discovery_run.insurer,
        name="Example policy",
        benefit_type="medical_indemnity",
        lifecycle_status="open",
        recommendation_role="primary_policy",
        identity_evidence=old_span,
    )
    policy = PolicyVersion.objects.create(
        product=product,
        uin="EXAMPLE-UIN",
        version_label="Current",
        applicability={
            "schema_version": 1,
            "predicate": {"node": "constant", "value": "true"},
            "event_basis": ["issue"],
            "source_span_ids": [],
            "unresolved": [],
        },
    )
    PolicyVersionDocument.objects.create(
        policy_version=policy,
        document_version=first.document_version,
        role="base_wording",
        required_for_policy=True,
        applicability=policy.applicability,
    )

    passages = _bundle_passages(policy)

    assert passages == [
        {
            "evidence_span_id": str(current_span.id),
            "passage": "Current frozen captured passage.",
            "document_version_id": str(first.document_version_id),
            "document_role": "base_wording",
            "document_kind": "web_page",
            "document_authority": "insurer_issued",
            "document_name": "Example product page",
            "required_for_policy": True,
            "physical_page": None,
            "published_on": None,
            "effective_from": None,
            "effective_to": None,
        }
    ]


def test_rule_processing_requires_one_selected_comparison_variant(db: None) -> None:
    capture = public_html_capture()
    root = enqueue_stage(stage="classify", source_capture=capture)
    process_job(root.id)
    while True:
        queued = ProcessingJob.objects.filter(source_capture=capture, state="queued").first()
        if queued is None:
            break
        process_job(queued.id)
    span = EvidenceSpan.objects.get(source_capture=capture)
    applicability = {
        "schema_version": 1,
        "predicate": {"node": "constant", "value": "true"},
        "event_basis": ["issue"],
        "source_span_ids": [str(span.id)],
        "unresolved": [],
    }
    product = Product.objects.create(
        insurer=capture.discovery_run.insurer,
        name="Variant-scoped example policy",
        benefit_type="medical_indemnity",
        lifecycle_status="open",
        recommendation_role="primary_policy",
        identity_evidence=span,
    )
    policy = PolicyVersion.objects.create(
        product=product,
        uin="VARIANT-SCOPED-UIN",
        version_label="Current",
        applicability=applicability,
    )
    PolicyVersionDocument.objects.create(
        policy_version=policy,
        document_version=capture.document_version,
        role="base_wording",
        required_for_policy=True,
        applicability=applicability,
    )
    variant = ProductVariant.objects.create(
        policy_version=policy,
        name="Gold",
        choices={"other_selectors": []},
        availability=applicability,
        identity_evidence=span,
    )

    assert _selected_variant_name(policy) == "Gold"
    assert _rule_scope_identity(capture) == [
        {
            "id": str(variant.id),
            "policy_version_id": str(policy.id),
            "name": "Gold",
        }
    ]
    first_extract = enqueue_stage(stage="extract", source_capture=capture)
    variant.name = "Gold revised"
    variant.save(update_fields=["name", "updated_at"])
    second_extract = enqueue_stage(stage="extract", source_capture=capture)
    assert second_extract.id != first_extract.id

    ProductVariant.objects.create(
        policy_version=policy,
        name="Platinum",
        choices={"other_selectors": []},
        availability=applicability,
        identity_evidence=span,
    )
    with pytest.raises(ValueError, match="exactly one selected comparison variant"):
        _selected_variant_name(policy)


def test_rule_inventory_batches_are_complete_disjoint_and_merge_deterministically() -> None:
    flattened = [category for batch in INVENTORY_CATEGORY_BATCHES for category in batch]
    assert set(flattened) == INVENTORY_CATEGORIES
    assert len(flattened) == len(set(flattened))
    policy_version_id = "00000000-0000-0000-0000-000000000001"
    extraction_batches = [
        (
            batch,
            PolicyRuleExtractionV1(
                schema_version=1,
                policy_version_id=policy_version_id,
                rules=[],
                omitted_inventory_categories=list(batch),
                material_issues=[],
            ),
        )
        for batch in INVENTORY_CATEGORY_BATCHES
    ]
    review_batches = [
        (
            batch,
            PolicyRuleReviewV1(
                schema_version=1,
                policy_version_id=policy_version_id,
                inventory_categories=list(batch),
                reviews=[],
                missing_rules=[],
            ),
        )
        for batch in INVENTORY_CATEGORY_BATCHES
    ]

    extraction = _combine_extraction_batches(policy_version_id, extraction_batches)
    review = _combine_review_batches(policy_version_id, review_batches)

    assert set(extraction.omitted_inventory_categories) == INVENTORY_CATEGORIES
    assert set(review.inventory_categories) == INVENTORY_CATEGORIES


def test_evidence_batches_preserve_every_exact_passage_without_oversize_payloads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    passages = [{"evidence_span_id": f"span-{index}", "passage": "x" * 80} for index in range(4)]
    monkeypatch.setattr(
        "apps.adviser_v2.processing.stages._bundle_passages", lambda _policy: passages
    )
    monkeypatch.setattr("apps.adviser_v2.processing.stages.MAX_MODEL_PASSAGE_CHARACTERS", 180)

    payloads = _passage_payloads(cast(PolicyVersion, SimpleNamespace()))

    assert [passage["evidence_span_id"] for batch, _encoded in payloads for passage in batch] == [
        f"span-{index}" for index in range(4)
    ]
    assert all(len(encoded) <= 180 for _batch, encoded in payloads)


def test_cross_evidence_duplicate_rule_key_is_excluded_as_ambiguous() -> None:
    category = INVENTORY_CATEGORY_BATCHES[0][0]
    span_id = str(uuid.uuid4())
    extracted_rule = {
        "rule_key": "eligibility.definition.duplicate",
        "rule_type": "definition",
        "inventory_category": category,
        "body": rule_revision_body(span_id),
        "evidence_span_ids": [span_id],
        "table_cells": [],
        "table_footnote_span_ids": [],
    }
    values = [
        PolicyRuleExtractionV1(
            schema_version=1,
            policy_version_id="version-1",
            rules=[extracted_rule],
            omitted_inventory_categories=[],
            material_issues=[],
        )
        for _index in range(2)
    ]

    combined = _combine_extraction_evidence_batches("version-1", (category,), values)

    assert combined.rules == []
    assert combined.omitted_inventory_categories == [category]
    assert any("duplicate cross-evidence rule key" in item for item in combined.material_issues)


def test_index_is_a_distinct_resumable_processing_stage() -> None:
    stage_choices = {value for value, _label in ProcessingJob._meta.get_field("stage").choices}

    assert NEXT_STAGE["validate"] == "index"
    assert "index" in STAGE_RUNNERS
    assert "index" in stage_choices


def test_index_stage_pins_validation_and_embedding_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy_id = uuid.uuid4()
    validation_id = uuid.uuid4()
    validation = SimpleNamespace(id=validation_id, stage="validate", parent_job=None)
    job = cast(ProcessingJob, SimpleNamespace(parent_job=validation))
    policy = cast(PolicyVersion, SimpleNamespace(id=policy_id))
    rule_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
    validation_artifact = {
        "policy_version_id": str(policy_id),
        "rule_prompt_version": RULE_PROMPT_VERSION,
        "rule_review_prompt_version": RULE_REVIEW_PROMPT_VERSION,
        "rule_validator_version": RULE_VALIDATOR_VERSION,
        "verified_rule_ids": rule_ids,
        "issues": [],
    }
    monkeypatch.setattr("apps.adviser_v2.processing.stages._policy_version", lambda _job: policy)
    monkeypatch.setattr(
        "apps.adviser_v2.processing.stages.read_artifact",
        lambda _job: validation_artifact,
    )
    monkeypatch.setattr(
        "apps.adviser_v2.processing.stages.index_policy_version",
        lambda _policy: (2, 5, "bge-index/1:abc"),
    )
    monkeypatch.setattr(
        "apps.adviser_v2.processing.stages.PolicyRule.objects.filter",
        lambda **_kwargs: SimpleNamespace(count=lambda: len(rule_ids)),
    )

    assert run_index(job) == {
        "schema_version": 1,
        "policy_version_id": str(policy_id),
        "validation_job_id": str(validation_id),
        "rule_prompt_version": RULE_PROMPT_VERSION,
        "rule_review_prompt_version": RULE_REVIEW_PROMPT_VERSION,
        "rule_validator_version": RULE_VALIDATOR_VERSION,
        "verified_rule_ids": rule_ids,
        "index_version": "bge-index/1:abc",
        "newly_indexed_chunks": 2,
        "indexed_chunks": 5,
        "issues": [],
    }


def test_index_stage_rejects_an_artifact_omitting_a_current_verified_rule(
    db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = rule_revision_policy()
    body = rule_revision_body(str(policy.product.identity_evidence_id))
    PolicyVersionDocument.objects.create(
        policy_version=policy,
        document_version=policy.product.identity_evidence.source_capture.document_version,
        role="base_wording",
        required_for_policy=True,
        applicability=policy.applicability,
    )
    included = PolicyRule.objects.create(
        policy_version=policy,
        rule_key="definition.included",
        rule_type="definition",
        body=body,
        review_status="verified",
    )
    omitted = PolicyRule.objects.create(
        policy_version=policy,
        rule_key="definition.omitted",
        rule_type="definition",
        body=body,
        review_status="verified",
    )
    for rule in (included, omitted):
        PolicyRuleEvidence.objects.create(
            policy_rule=rule,
            evidence_span=policy.product.identity_evidence,
            role="defines",
            is_required=True,
        )
    validation = SimpleNamespace(id=uuid.uuid4(), stage="validate", parent_job=None)
    job = cast(ProcessingJob, SimpleNamespace(parent_job=validation))
    validation_artifact = {
        "policy_version_id": str(policy.id),
        "rule_prompt_version": RULE_PROMPT_VERSION,
        "rule_review_prompt_version": RULE_REVIEW_PROMPT_VERSION,
        "rule_validator_version": RULE_VALIDATOR_VERSION,
        "verified_rule_ids": [str(included.id)],
        "issues": [],
    }
    monkeypatch.setattr("apps.adviser_v2.processing.stages._policy_version", lambda _job: policy)
    monkeypatch.setattr(
        "apps.adviser_v2.processing.stages.read_artifact",
        lambda _job: validation_artifact,
    )

    with pytest.raises(ValueError, match="omits current verified"):
        run_index(job)


def test_policy_index_is_idempotent_and_merges_duplicate_passage_evidence(
    db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = rule_revision_policy()
    first_span = policy.product.identity_evidence
    second_span = EvidenceSpan.objects.create(
        source_capture=first_span.source_capture,
        section_label="duplicate-passage-test",
        quote="Same exact clause.",
        context=first_span.context,
        method="html",
        verification="text_verified",
        locator=first_span.locator,
    )
    passages = [
        {"evidence_span_id": str(first_span.id), "passage": "Same exact clause."},
        {"evidence_span_id": str(second_span.id), "passage": "Same exact clause."},
    ]
    monkeypatch.setattr(
        "apps.adviser_v2.processing.stages.qualified_embedding_status",
        lambda: (True, "qualified", SimpleNamespace()),
    )
    monkeypatch.setattr(
        "apps.adviser_v2.processing.stages.policy_index_version",
        lambda _qualification: "test-index/1",
    )
    monkeypatch.setattr(
        "apps.adviser_v2.processing.stages._bundle_passages",
        lambda _policy: passages,
    )
    embedded: list[list[str]] = []

    def embed_once(texts: list[str]) -> list[list[float]]:
        embedded.append(texts)
        return [[0.0] * 1024 for _text in texts]

    monkeypatch.setattr("apps.adviser_v2.processing.stages.embed_texts", embed_once)

    first_result = index_policy_version(policy)
    second_result = index_policy_version(policy)
    chunk = PolicySearchChunk.objects.get(index_version="test-index/1")
    PolicySearchChunk.objects.create(
        document_version=chunk.document_version,
        evidence_span_ids=[str(second_span.id)],
        text="Obsolete clause text.",
        lexical_vector=chunk.lexical_vector,
        embedding=chunk.embedding,
        index_version="test-index/1",
        chunk_sha256="f" * 64,
    )
    monkeypatch.setattr(
        "apps.adviser_v2.processing.stages._bundle_passages",
        lambda _policy: passages[:1],
    )
    refreshed_result = index_policy_version(policy)
    chunk.refresh_from_db()

    assert first_result == (1, 1, "test-index/1")
    assert second_result == (0, 1, "test-index/1")
    assert refreshed_result == (0, 1, "test-index/1")
    assert chunk.evidence_span_ids == [str(first_span.id)]
    assert PolicySearchChunk.objects.filter(index_version="test-index/1").count() == 1
    assert embedded == [["Same exact clause."]]


def test_rule_batch_targets_do_not_retry_supported_partial_omissions() -> None:
    categories = INVENTORY_CATEGORY_BATCHES[0]
    extraction = PolicyRuleExtractionV1(
        schema_version=1,
        policy_version_id="version-1",
        rules=[],
        omitted_inventory_categories=list(categories),
        material_issues=["Encode the complete selectable-option axes."],
    )
    review = PolicyRuleReviewV1(
        schema_version=1,
        policy_version_id="version-1",
        inventory_categories=list(categories),
        reviews=[],
        missing_rules=[],
    )

    extraction_targets = _extraction_batch_targets("version-1", categories, extraction)
    review_targets = _review_batch_targets("version-1", categories, review)

    assert extraction_targets == []
    assert review_targets == []


def test_rule_job_commitment_changes_with_exact_model_identity(db: None, settings: Any) -> None:
    capture = public_html_capture()
    settings.COVERGUIDE_POLICY_EXTRACTION_MODEL = "gpt-5.6-sol"
    first = enqueue_stage(stage="extract", source_capture=capture)
    settings.COVERGUIDE_POLICY_EXTRACTION_MODEL = "gpt-5.6-sol-requalified"
    second = enqueue_stage(stage="extract", source_capture=capture)

    assert first.input_commitment != second.input_commitment


def test_partial_validation_persists_supported_agreed_rules(db: None) -> None:
    capture = public_html_capture()
    root = enqueue_stage(stage="classify", source_capture=capture)
    while True:
        queued = ProcessingJob.objects.filter(source_capture=capture, state="queued").first()
        if queued is None:
            break
        process_job(queued.id)
    reconcile = ProcessingJob.objects.get(
        source_capture=capture, stage="reconcile", adapter_version=ADAPTER_VERSION
    )
    span = EvidenceSpan.objects.get(source_capture=capture)
    product = Product.objects.create(
        insurer=capture.discovery_run.insurer,
        name="Fail-closed example policy",
        benefit_type="medical_indemnity",
        lifecycle_status="open",
        recommendation_role="primary_policy",
        identity_evidence=span,
    )
    policy = PolicyVersion.objects.create(
        product=product,
        uin="FAIL-CLOSED-UIN",
        version_label="Current",
        applicability={
            "schema_version": 1,
            "predicate": {"node": "constant", "value": "true"},
            "event_basis": ["issue"],
            "source_span_ids": [str(span.id)],
            "unresolved": [],
        },
    )
    PolicyVersionDocument.objects.create(
        policy_version=policy,
        document_version=capture.document_version,
        role="base_wording",
        required_for_policy=True,
        applicability=policy.applicability,
    )
    body = {
        "schema_version": 1,
        "applies_when": {"node": "constant", "value": "true"},
        "inputs": [],
        "effects": [
            {
                "kind": "eligibility",
                "target_key": "policy_eligibility",
                "scope": {
                    "subject": "policy",
                    "subject_ids": [],
                    "period": "policy_term",
                    "benefit_keys": [],
                    "reset": "never",
                },
                "decision": "eligible",
                "reason": "Test-only exact policy evidence.",
            }
        ],
        "mandatory_rule_keys": [],
        "source_span_ids": [str(span.id)],
        "unresolved": [],
        "rounding": {"mode": "none", "scale": 0, "authority_span_ids": []},
    }
    extracted_rule = {
        "rule_key": "eligibility.eligibility.policy_entry",
        "rule_type": "eligibility",
        "inventory_category": "eligibility",
        "body": body,
        "evidence_span_ids": [str(span.id)],
        "table_cells": [],
        "table_footnote_span_ids": [],
    }
    extraction = ProcessingJob.objects.create(
        source_capture=capture,
        stage="extract",
        adapter_version=ADAPTER_VERSION,
        input_commitment="d" * 64,
        parent_job=reconcile,
        state="succeeded",
    )
    extraction.result_storage_key, extraction.result_storage_sha256 = write_artifact(
        extraction,
        {
            "schema_version": 1,
            "policy_version_id": str(policy.id),
            "rules": [extracted_rule],
            "omitted_inventory_categories": [],
            "material_issues": ["A material source conflict remains."],
        },
    )
    extraction.save(update_fields=["result_storage_key", "result_storage_sha256"])
    review = ProcessingJob.objects.create(
        source_capture=capture,
        stage="independent_review",
        adapter_version=ADAPTER_VERSION,
        input_commitment="e" * 64,
        parent_job=extraction,
        state="succeeded",
    )
    review.result_storage_key, review.result_storage_sha256 = write_artifact(
        review,
        {
            "schema_version": 1,
            "policy_version_id": str(policy.id),
            "inventory_categories": sorted(INVENTORY_CATEGORIES),
            "reviews": [
                {
                    "rule_key": extracted_rule["rule_key"],
                    "verdict": "agree",
                    "independent_body": body,
                    "evidence_span_ids": [str(span.id)],
                    "material_issue": None,
                }
            ],
            "missing_rules": [],
        },
    )
    review.save(update_fields=["result_storage_key", "result_storage_sha256"])
    validation = ProcessingJob.objects.create(
        source_capture=capture,
        stage="validate",
        adapter_version=ADAPTER_VERSION,
        input_commitment="f" * 64,
        parent_job=review,
    )

    process_job(validation.id)

    root.refresh_from_db()
    validation.refresh_from_db()
    span.refresh_from_db()
    assert root.state == "succeeded"
    assert validation.state == "succeeded"
    rule = PolicyRule.objects.get(policy_version=policy)
    assert rule.review_status == "verified"
    assert PolicyRuleEvidence.objects.filter(policy_rule=rule).count() == 1
    assert span.verification == "reviewed"
    result = read_artifact(validation)
    assert result["verified_rule_ids"] == [str(rule.id)]
    assert result["covered_inventory_categories"] == ["eligibility"]
    assert "waiting_periods" in result["missing_inventory_categories"]
    assert any(item["code"] == "rule_inventory_coverage_incomplete" for item in result["issues"])
    assert not any(item["material"] for item in result["issues"])
