"""Exact native PDF pages for the approved version-2 document bundles.

Page boundaries are citation locators, not retrieval chunks. Every selected document
is passed in full to extraction; no ranking, splitting or text truncation is used.
"""

from __future__ import annotations

import hashlib
import io
import json
import re
import subprocess
from typing import Any

import pdfplumber

from ..manifest import ManifestDocumentV2, ManifestProductV2
from ..models import (
    DocumentPage,
    EvidenceSpan,
    PolicyVersion,
    PolicyVersionDocument,
    ProcessingJob,
    SourceCapture,
)
from ..storage import read_public
from .artifacts import parent_artifact, read_artifact, source_bytes

RAW_READER_VERSION = "coverguide-manifest-v2-pdftotext-raw/1"
ANCHOR_PREFIX = RAW_READER_VERSION + ":"


def manifest_product(capture: SourceCapture | None) -> ManifestProductV2 | None:
    if capture is None or not (capture.discovery_run.session_id or "").startswith("fixed-manifest-v2:"):
        return None
    value = json.loads(capture.discovery_run.instructions)
    if value.get("manifest_schema_version") != 2:
        raise ValueError("The version-2 capture is missing its approved manifest identity.")
    return ManifestProductV2.model_validate(value["product"])


def executable_entry(capture: SourceCapture) -> ManifestDocumentV2:
    product = manifest_product(capture)
    if product is None or capture.original_file is None:
        raise ValueError("Raw-page processing requires a captured version-2 bundle.")
    entries = [entry for entry in product.documents if str(entry.url) == capture.source_url.url]
    if len(entries) != 1 or entries[0].evidence_use != "executable":
        raise ValueError("Reference and excluded documents cannot become executable evidence.")
    entry = entries[0]
    if capture.original_file.sha256 != entry.expected_sha256:
        raise ValueError("The preserved source differs from the reviewed manifest SHA-256.")
    return entry


def raw_pdf_pages(payload: bytes, *, expected_pages: int) -> list[dict[str, Any]]:
    """Preserve Poppler's complete native text byte for byte, including page breaks."""
    completed = subprocess.run(
        ["pdftotext", "-raw", "-enc", "UTF-8", "-", "-"],
        input=payload, capture_output=True, check=True, timeout=120,
    )
    text = completed.stdout.decode("utf-8", errors="strict")
    split_pages = text.split("\f")
    if split_pages[-1] != "" or len(split_pages) - 1 != expected_pages:
        raise ValueError("Raw text boundaries do not match the reviewed physical page count.")
    pages: list[dict[str, Any]] = []
    offset = 0
    with pdfplumber.open(io.BytesIO(payload), strict_metadata=True) as document:
        if len(document.pages) != expected_pages:
            raise ValueError("PDF page count differs from the approved manifest.")
        for number, (page, raw) in enumerate(zip(document.pages, split_pages[:-1], strict=True), 1):
            # Captured prospectuses use an unmapped diamond bullet at line starts.
            # Preserve it exactly; an unmapped character inside wording still blocks.
            bullet_offsets = [match.start() for match in re.finditer(r"(?m)^\ufffd(?=\s|\x07)", raw)]
            if not raw.strip() or "\x00" in raw or raw.count("\ufffd") != len(bullet_offsets):
                raise ValueError(f"Physical page {number} has no reliable native text.")
            pages.append({
                "page_number": number,
                "text": raw,
                "document_char_start": offset,
                "document_char_end": offset + len(raw),
                "text_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                "width": float(page.width),
                "height": float(page.height),
                "rotation": int(page.rotation),
                "unmapped_bullet_offsets": bullet_offsets,
            })
            offset += len(raw) + 1  # The preserved physical-page form feed.
    return pages


def read_raw_document(job: ProcessingJob) -> dict[str, Any]:
    capture = job.source_capture
    if capture is None:
        raise ValueError("Version-2 raw processing requires a public capture.")
    entry = executable_entry(capture)
    pages = raw_pdf_pages(source_bytes(job), expected_pages=entry.page_count)
    DocumentPage.objects.bulk_create([
        DocumentPage(original_file=capture.original_file, page_number=page["page_number"])
        for page in pages
    ], ignore_conflicts=True)
    return {
        "schema_version": 1,
        "reader": RAW_READER_VERSION,
        "classification": parent_artifact(job),
        "document_sha256": entry.expected_sha256,
        "pages": pages,
        "issues": [],
    }


def preserve_native_document(job: ProcessingJob) -> dict[str, Any]:
    value = parent_artifact(job)
    if value.get("reader") != RAW_READER_VERSION:
        raise ValueError("Version-2 native preservation requires the complete raw read artifact.")
    return {**value, "ocr": {"requested_pages": [], "reason": "Reliable native text preserved."}}


def reconcile_raw_document(job: ProcessingJob, *, reconciliation_version: str) -> dict[str, Any]:
    value = parent_artifact(job)
    capture = job.source_capture
    if capture is None or capture.original_file is None:
        raise ValueError("Version-2 reconciliation requires a public original file.")
    entry = executable_entry(capture)
    pages = raw_pdf_pages(source_bytes(job), expected_pages=entry.page_count)
    if value.get("reader") != RAW_READER_VERSION or value.get("pages") != pages:
        raise ValueError("Raw page artifact does not match the preserved original PDF.")
    spans = []
    for page in pages:
        number, quote = page["page_number"], page["text"]
        page_row = DocumentPage.objects.get(original_file=capture.original_file, page_number=number)
        anchor = {
            "page": number, "start": 0, "end": len(quote),
            "page_text_sha256": page["text_sha256"],
            "document_start": page["document_char_start"],
            "document_end": page["document_char_end"],
        }
        span, _ = EvidenceSpan.objects.get_or_create(
            source_capture=capture, page=page_row,
            section_label=f"manifest-v2-raw-page-{number}-{page['text_sha256'][:16]}",
            defaults={
                "quote": quote,
                "context": {"span_ids": [], "notes": [ANCHOR_PREFIX + json.dumps(anchor, sort_keys=True)]},
                "method": "native_text", "verification": "text_verified",
                "locator": {
                    "schema_version": 1, "blob_sha256": entry.expected_sha256,
                    "resolver_version": RAW_READER_VERSION, "kind": "pdf_region",
                    "physical_page": number,
                    "bbox": [0.0, 0.0, page["width"], page["height"]],
                    "coordinate_space": "unrotated_pdf_points", "rotation": page["rotation"],
                },
            },
        )
        validate_raw_quote(span, page, blob_sha256=entry.expected_sha256)
        page_row.review_state = "text_read"
        page_row.save(update_fields=["review_state", "updated_at"])
        spans.append({"id": str(span.id), "page_number": number, "quote": quote, "method": "native_text"})
    version = capture.document_version
    if version is None:
        raise ValueError("A raw document is missing its captured document version.")
    version.review_status = "verified"
    version.save(update_fields=["review_status", "updated_at"])
    return {
        "schema_version": 1, "reader": RAW_READER_VERSION,
        "reconciliation_version": reconciliation_version,
        "document_sha256": entry.expected_sha256,
        "page_count": len(pages), "page_numbers": [page["page_number"] for page in pages],
        "evidence_spans": spans, "issues": [],
    }


def validate_raw_quote(span: EvidenceSpan, page: dict[str, Any], *, blob_sha256: str) -> None:
    anchors = [note.removeprefix(ANCHOR_PREFIX) for note in span.context.get("notes", []) if note.startswith(ANCHOR_PREFIX)]
    if len(anchors) != 1:
        raise ValueError("Raw citation requires exactly one preserved character-offset anchor.")
    anchor = json.loads(anchors[0])
    start, end = anchor.get("start"), anchor.get("end")
    text = page["text"]
    if (
        type(start) is not int or type(end) is not int or not 0 <= start < end <= len(text)
        or span.quote != text[start:end]
        or anchor.get("page_text_sha256") != hashlib.sha256(text.encode()).hexdigest()
        or anchor.get("document_start") != page["document_char_start"] + start
        or anchor.get("document_end") != page["document_char_start"] + end
        or anchor.get("page") != page["page_number"]
        or span.page is None or span.page.page_number != page["page_number"]
        or span.locator.get("physical_page") != page["page_number"]
        or span.locator.get("blob_sha256") != blob_sha256
    ):
        raise ValueError("Citation quotation, physical page, SHA-256 or character offsets disagree.")


def raw_bundle_passages(version: PolicyVersion, *, include_prospectus: bool = False) -> list[dict[str, Any]]:
    """Return every physical page of the core bundle; optionally add the whole prospectus."""
    passages = []
    members = PolicyVersionDocument.objects.filter(policy_version=version).select_related("document_version__document_series")
    for member in members:
        capture = SourceCapture.objects.filter(
            document_version=member.document_version, status="captured", original_file__isnull=False,
        ).select_related("original_file", "discovery_run", "source_url").order_by("-completed_at", "-created_at").first()
        if capture is None or capture.original_file is None:
            raise ValueError("A complete version-2 bundle capture is missing.")
        entry = executable_entry(capture)
        if entry.role == "prospectus" and not include_prospectus:
            continue
        original = capture.original_file
        job = ProcessingJob.objects.filter(source_capture=capture, stage="reconcile").order_by("-created_at", "-attempt_number").first()
        if job is None or job.state != "succeeded":
            raise ValueError(f"Raw reconciliation is incomplete for {entry.document_key}.")
        artifact = read_artifact(job)
        if artifact.get("reader") != RAW_READER_VERSION:
            raise ValueError("Version-2 extraction requires complete original raw-page evidence.")
        pages = raw_pdf_pages(read_public(original.storage_key, original.sha256), expected_pages=entry.page_count)
        spans = list(EvidenceSpan.objects.filter(
            id__in=[item["id"] for item in artifact["evidence_spans"]], source_capture=capture,
            verification__in=["text_verified", "visually_verified", "reviewed"],
        ).select_related("page").order_by("page__page_number"))
        if len(spans) != len(pages):
            raise ValueError(f"The raw evidence does not cover every page of {entry.document_key}.")
        for span, page in zip(spans, pages, strict=True):
            validate_raw_quote(span, page, blob_sha256=original.sha256)
            passages.append({
                "evidence_span_id": str(span.id), "passage": span.quote,
                "document_version_id": str(member.document_version_id),
                "document_key": entry.document_key, "document_role": entry.role,
                "document_authority": entry.authority, "document_sha256": original.sha256,
                "document_name": member.document_version.document_series.name,
                "physical_page": page["page_number"], "physical_page_count": entry.page_count,
                "page_char_start": 0, "page_char_end": len(page["text"]),
                "document_char_start": page["document_char_start"],
                "document_char_end": page["document_char_end"],
                "unmapped_bullet_offsets": page["unmapped_bullet_offsets"],
            })
    if not passages:
        raise ValueError("The version-2 bundle has no executable raw pages.")
    role_order = {"base_wording": 0, "customer_information_sheet": 1, "prospectus": 3}
    return sorted(passages, key=lambda item: (role_order.get(item["document_role"], 2), item["document_key"], item["physical_page"]))
