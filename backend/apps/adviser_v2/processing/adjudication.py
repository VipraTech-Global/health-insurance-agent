"""Explicit operator adjudication for blocked document-processing evidence."""

from __future__ import annotations

import hashlib
import re
import uuid
from typing import Any, Literal

from django.db import transaction
from django.db.models import Q

from ..models import (
    AuditEvent,
    DocumentPage,
    EvidenceSpan,
    PolicyRuleEvidence,
    ProcessingJob,
)
from .artifacts import read_artifact, write_artifact
from .stages import _native_table_evidence, _span_groups

ReaderSelection = Literal["native", "ocr", "manual"]
PAGE_PATTERN = re.compile(r"physical page\s+(\d+)", re.IGNORECASE)


@transaction.atomic
def adjudicate_classification(
    job_id: uuid.UUID,
    accepted_kind: str,
    review_note: str,
) -> ProcessingJob:
    """Resolve one preserved classifier disagreement after exact-document review."""

    if len(review_note.strip()) < 20:
        raise ValueError("Classification adjudication requires a specific review note.")
    job = (
        ProcessingJob.objects.select_for_update(of=("self",))
        .select_related("source_capture__document_version")
        .get(pk=job_id)
    )
    result = read_artifact(job)
    decision = {
        "schema_version": 1,
        "accepted_kind": accepted_kind,
        "review_note": review_note.strip(),
    }
    if job.state == "succeeded" and result.get("classification_adjudication") == decision:
        return job
    if job.stage != "classify" or job.state != "blocked":
        raise ValueError("Only a blocked classification job can be adjudicated.")
    unresolved = [item for item in job.issues if item.get("material") and not item.get("resolved")]
    if not unresolved or any(
        item.get("code") != "classification_disagreement" for item in unresolved
    ):
        raise ValueError("Classification adjudication cannot resolve another blocker type.")
    candidates = {
        str(value)
        for value in [result.get("declared_kind"), *result.get("observed_markers", [])]
        if value
    }
    if accepted_kind not in candidates:
        raise ValueError(
            "The accepted kind must be the declared kind or an observed classifier marker."
        )

    resolved_issues = [
        {**item, "resolved": True}
        if item.get("code") == "classification_disagreement"
        and item.get("material")
        and not item.get("resolved")
        else item
        for item in job.issues
    ]
    previous = {
        "storage_key": job.result_storage_key,
        "stored_sha256": job.result_storage_sha256,
    }
    result["inferred_kind"] = accepted_kind
    result["issues"] = resolved_issues
    result["classification_adjudication"] = decision
    result["pre_adjudication_artifact"] = previous
    storage_key, storage_sha256 = write_artifact(job, result)

    job.issues = resolved_issues
    job.state = "succeeded"
    job.error_code = None
    job.result_storage_key = storage_key
    job.result_storage_sha256 = storage_sha256
    job.save(
        update_fields=[
            "issues",
            "state",
            "error_code",
            "result_storage_key",
            "result_storage_sha256",
            "updated_at",
        ]
    )
    AuditEvent.objects.create(
        operation="corpus_classification_adjudication",
        object_kind="processing_job",
        object_id=job.id,
        outcome="succeeded",
        metadata={
            "affected_count": 1,
            "authorization_basis_code": "operator_exact_document_review",
        },
    )
    return job


def issue_page(issue: dict[str, Any]) -> int | None:
    match = PAGE_PATTERN.search(str(issue.get("description", "")))
    return int(match.group(1)) if match else None


def unresolved_issue_pages(issues: list[dict[str, Any]]) -> set[int]:
    pages: set[int] = set()
    for item in issues:
        if not item.get("material") or item.get("resolved"):
            continue
        page_number = issue_page(item)
        if page_number is None:
            raise ValueError("Every adjudicated issue must identify one physical page.")
        pages.add(page_number)
    return pages


def validate_page_selections(
    issues: list[dict[str, Any]], selections: dict[int, ReaderSelection]
) -> None:
    expected = unresolved_issue_pages(issues)
    supplied = set(selections)
    if expected != supplied:
        missing = ",".join(str(item) for item in sorted(expected - supplied)) or "none"
        extra = ",".join(str(item) for item in sorted(supplied - expected)) or "none"
        raise ValueError(
            f"Visual adjudication must cover the exact unresolved page set; "
            f"missing={missing}; extra={extra}."
        )


def validate_manual_transcriptions(
    selections: dict[int, ReaderSelection], transcriptions: dict[int, str]
) -> None:
    expected = {page for page, reader in selections.items() if reader == "manual"}
    supplied = set(transcriptions)
    if expected != supplied:
        missing = ",".join(str(item) for item in sorted(expected - supplied)) or "none"
        extra = ",".join(str(item) for item in sorted(supplied - expected)) or "none"
        raise ValueError(
            "Manual transcriptions must cover exactly the pages selecting the manual reader; "
            f"missing={missing}; extra={extra}."
        )
    if any(not value.strip() for value in transcriptions.values()):
        raise ValueError("A manual transcription cannot be blank.")


def _reader_text(
    artifact: dict[str, Any],
    page_number: int,
    selection: ReaderSelection,
    manual_transcription: str | None = None,
) -> tuple[dict[str, Any], str, str]:
    pages = {int(item["page_number"]): item for item in artifact["native"]["pages"]}
    try:
        page = pages[page_number]
    except KeyError as exc:
        raise ValueError(f"Physical page {page_number} is absent from the read artifact.") from exc
    if selection == "native":
        text = str(page.get("text", ""))
        method = "native_text"
    elif selection == "ocr":
        text = str(artifact.get("ocr", {}).get("pages", {}).get(str(page_number), ""))
        method = "ocr_verified"
    else:
        text = manual_transcription or ""
        method = "manual_visual"
    if not text.strip():
        raise ValueError(
            f"Selected {selection} reader has no text for physical page {page_number}."
        )
    return page, text, method


def _selected_spans(
    *,
    job: ProcessingJob,
    artifact: dict[str, Any],
    page_number: int,
    selection: ReaderSelection,
    review_note: str,
    manual_transcription: str | None = None,
) -> list[EvidenceSpan]:
    if job.source_capture is None or job.source_capture.original_file is None:
        raise ValueError("Visual corpus adjudication requires a captured original file.")
    page_data, text, method = _reader_text(artifact, page_number, selection, manual_transcription)
    page = DocumentPage.objects.get(
        original_file=job.source_capture.original_file,
        page_number=page_number,
    )
    prior = EvidenceSpan.objects.filter(
        source_capture=job.source_capture,
        page=page,
    ).filter(
        Q(section_label__startswith=f"processed-page-{page_number}-")
        | Q(section_label__startswith=f"processed-table-{page_number}-")
    )
    if PolicyRuleEvidence.objects.filter(evidence_span__in=prior).exists():
        raise ValueError("Cannot replace reader evidence after a policy rule cites this page.")
    prior.update(verification="failed")

    groups = _span_groups(
        page_data,
        text,
        use_native_lines=selection == "native",
    )
    selected: list[EvidenceSpan] = []
    for index, (quote, bbox) in enumerate(groups, 1):
        quote_hash = hashlib.sha256(quote.encode()).hexdigest()[:16]
        section = f"processed-page-{page_number}-{index}-{quote_hash}"
        span, _created = EvidenceSpan.objects.get_or_create(
            source_capture=job.source_capture,
            customer_uploaded_document=None,
            page=page,
            section_label=section,
            defaults={
                "quote": quote,
                "context": {"span_ids": [], "notes": [review_note]},
                "method": method,
                "verification": "visually_verified",
                "locator": {
                    "schema_version": 1,
                    "blob_sha256": job.source_capture.original_file.sha256,
                    "resolver_version": "coverguide-pdf/1",
                    "kind": "pdf_region",
                    "physical_page": page_number,
                    "bbox": bbox,
                    "coordinate_space": "unrotated_pdf_points",
                    "rotation": int(page_data["rotation"]),
                },
            },
        )
        span.context = {
            "span_ids": [],
            "notes": [
                f"Visual adjudication selected the {selection} reader for physical page {page_number}.",
                review_note,
            ],
        }
        span.verification = "visually_verified"
        span.save(update_fields=["context", "verification"])
        selected.append(span)
    if selection == "native":
        locator = {
            "schema_version": 1,
            "blob_sha256": job.source_capture.original_file.sha256,
            "resolver_version": "coverguide-pdf/1",
            "kind": "pdf_region",
            "physical_page": page_number,
            "bbox": [
                0.0,
                0.0,
                float(page_data["width"]),
                float(page_data["height"]),
            ],
            "coordinate_space": "unrotated_pdf_points",
            "rotation": int(page_data["rotation"]),
        }
        for table_index, table_quote, table_context in _native_table_evidence(page_data):
            quote_hash = hashlib.sha256(table_quote.encode()).hexdigest()[:16]
            section = f"processed-table-{page_number}-{table_index}-{quote_hash}"
            table_context["notes"] = [
                *table_context["notes"],
                (
                    f"Visual adjudication selected the native table grid for physical page "
                    f"{page_number}."
                ),
                review_note,
            ]
            span, _created = EvidenceSpan.objects.get_or_create(
                source_capture=job.source_capture,
                customer_uploaded_document=None,
                page=page,
                section_label=section,
                defaults={
                    "quote": table_quote,
                    "context": table_context,
                    "method": "native_text",
                    "verification": "visually_verified",
                    "locator": locator,
                },
            )
            span.context = table_context
            span.method = "native_text"
            span.verification = "visually_verified"
            span.locator = locator
            span.save(update_fields=["context", "method", "verification", "locator"])
            selected.append(span)
    if not selected:
        raise ValueError(f"Selected reader produced no evidence spans for page {page_number}.")
    page.review_state = "fully_reviewed"
    page.save(update_fields=["review_state", "updated_at"])
    return selected


def _synchronize_result_spans(job: ProcessingJob, result: dict[str, Any]) -> int:
    if job.source_capture is None or job.source_capture.document_version is None:
        raise ValueError("Reconciled evidence requires an identified public document.")
    if any(
        item.get("material") and not item.get("resolved")
        for item in result.get("issues", [])
        if isinstance(item, dict)
    ):
        raise ValueError("Unresolved material issues prevent evidence verification.")
    identifiers = {
        str(item.get("id"))
        for item in result.get("evidence_spans", [])
        if isinstance(item, dict) and item.get("id")
    }
    spans = EvidenceSpan.objects.filter(
        id__in=identifiers,
        source_capture=job.source_capture,
    )
    found = {str(item) for item in spans.values_list("id", flat=True)}
    if identifiers != found:
        raise ValueError("Reconciliation artifact references missing or foreign evidence spans.")
    updated = spans.exclude(verification__in=["visually_verified", "reviewed"]).update(
        verification="text_verified"
    )
    document_version = job.source_capture.document_version
    document_version.review_status = "verified"
    document_version.save(update_fields=["review_status", "updated_at"])
    return updated


@transaction.atomic
def synchronize_reconciliation_evidence(job_id: uuid.UUID) -> int:
    job = (
        ProcessingJob.objects.select_for_update(of=("self",))
        .select_related("source_capture__document_version")
        .get(pk=job_id)
    )
    if job.stage != "reconcile" or job.state != "succeeded":
        raise ValueError("Only successful reconciliation evidence can be synchronized.")
    return _synchronize_result_spans(job, read_artifact(job))


@transaction.atomic
def adjudicate_reconciliation(
    job_id: uuid.UUID,
    selections: dict[int, ReaderSelection],
    review_note: str,
    manual_transcriptions: dict[int, str] | None = None,
) -> ProcessingJob:
    if len(review_note.strip()) < 20:
        raise ValueError("Visual adjudication requires a specific review note.")
    job = (
        ProcessingJob.objects.select_for_update(of=("self",))
        .select_related(
            "source_capture__original_file",
            "source_capture__document_version",
            "parent_job",
        )
        .get(pk=job_id)
    )
    transcriptions = manual_transcriptions or {}
    validate_manual_transcriptions(selections, transcriptions)
    result = read_artifact(job)
    existing = result.get("visual_adjudication")
    encoded_selections = {str(key): value for key, value in sorted(selections.items())}
    decision: dict[str, Any] = {
        "schema_version": 1,
        "page_reader_selections": encoded_selections,
        "review_note": review_note.strip(),
    }
    if transcriptions:
        decision["manual_transcription_sha256"] = {
            str(page): hashlib.sha256(text.encode()).hexdigest()
            for page, text in sorted(transcriptions.items())
        }
    if job.state == "succeeded" and existing == decision:
        _synchronize_result_spans(job, result)
        return job
    if job.stage != "reconcile" or job.state != "blocked":
        raise ValueError("Only a blocked reconciliation job can be visually adjudicated.")
    if job.source_capture is None or job.source_capture.document_version is None:
        raise ValueError("Visual corpus adjudication requires an identified public document.")
    if job.parent_job is None or job.parent_job.stage != "ocr":
        raise ValueError("Reconciliation job is missing its OCR/read artifact parent.")
    validate_page_selections(job.issues, selections)
    reader_artifact = read_artifact(job.parent_job)
    selected_by_page: dict[int, list[EvidenceSpan]] = {}
    for page_number, selection in sorted(selections.items()):
        selected_by_page[page_number] = _selected_spans(
            job=job,
            artifact=reader_artifact,
            page_number=page_number,
            selection=selection,
            review_note=review_note.strip(),
            manual_transcription=transcriptions.get(page_number),
        )

    resolved_issues: list[dict[str, Any]] = []
    for item in job.issues:
        updated = dict(item)
        issue_page_number = issue_page(updated)
        if updated.get("material") and not updated.get("resolved"):
            assert issue_page_number is not None
            updated["resolved"] = True
            updated["region_span_ids"] = [
                str(span.id) for span in selected_by_page[issue_page_number]
            ]
        resolved_issues.append(updated)

    previous = {
        "storage_key": job.result_storage_key,
        "stored_sha256": job.result_storage_sha256,
    }
    result["issues"] = resolved_issues
    result["evidence_spans"] = [
        {
            "id": str(span.id),
            "page_number": page_number,
            "quote": span.quote,
            "method": span.method,
        }
        for page_number, spans in selected_by_page.items()
        for span in spans
    ] + [
        item
        for item in result.get("evidence_spans", [])
        if int(item.get("page_number", 0)) not in selections
    ]
    result["visual_adjudication"] = decision
    result["pre_adjudication_artifact"] = previous
    storage_key, storage_sha256 = write_artifact(job, result)

    job.issues = resolved_issues
    job.state = "succeeded"
    job.error_code = None
    job.result_storage_key = storage_key
    job.result_storage_sha256 = storage_sha256
    job.save(
        update_fields=[
            "issues",
            "state",
            "error_code",
            "result_storage_key",
            "result_storage_sha256",
            "updated_at",
        ]
    )
    _synchronize_result_spans(job, result)
    AuditEvent.objects.create(
        operation="corpus_visual_adjudication",
        object_kind="processing_job",
        object_id=job.id,
        outcome="succeeded",
        metadata={
            "affected_count": len(selections),
            "authorization_basis_code": "operator_visual_review",
        },
    )
    return job
