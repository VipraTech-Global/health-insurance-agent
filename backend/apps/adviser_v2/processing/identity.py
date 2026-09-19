"""Evidence-backed document identity derived from exact preserved source bytes."""

from __future__ import annotations

import io
from dataclasses import dataclass
from typing import Any

import pdfplumber
from django.db import transaction

from ..manifest import html_text
from ..models import (
    AuditEvent,
    DocumentPage,
    DocumentVersion,
    EvidenceSpan,
    SourceCapture,
)


@dataclass(frozen=True)
class IdentityObservation:
    page_number: int | None
    quote: str
    locator: dict[str, Any]
    method: str
    page_count: int
    observed: bool


def _pdf_identity(payload: bytes, uin: str) -> tuple[int, str, list[float], int, bool]:
    with pdfplumber.open(io.BytesIO(payload), strict_metadata=True) as document:
        if not document.pages:
            raise ValueError("PDF has no pages.")
        for number, page in enumerate(document.pages, 1):
            text = page.extract_text() or ""
            position = text.casefold().find(uin.casefold())
            if position >= 0:
                start = max(0, position - 300)
                end = min(len(text), position + len(uin) + 300)
                return (
                    number,
                    " ".join(text[start:end].split()),
                    [0, 0, float(page.width), float(page.height)],
                    len(document.pages),
                    True,
                )
        first = document.pages[0]
        text = " ".join((first.extract_text() or "").split())
        return (
            1,
            text[:1000],
            [0, 0, float(first.width), float(first.height)],
            len(document.pages),
            False,
        )


def inspect_identity(
    payload: bytes,
    *,
    media_type: str,
    blob_sha256: str,
    uin: str,
) -> IdentityObservation:
    if media_type == "application/pdf":
        page_number, quote, bbox, page_count, observed = _pdf_identity(payload, uin)
        return IdentityObservation(
            page_number=page_number,
            quote=quote,
            locator={
                "schema_version": 1,
                "blob_sha256": blob_sha256,
                "resolver_version": "coverguide-pdf/1",
                "kind": "pdf_region",
                "physical_page": page_number,
                "bbox": bbox,
                "coordinate_space": "unrotated_pdf_points",
                "rotation": 0,
            },
            method="native_text",
            page_count=page_count,
            observed=observed,
        )
    if media_type != "text/html":
        raise ValueError(f"Unsupported identity media type: {media_type}.")
    decoded_text = html_text(payload)
    position = decoded_text.casefold().find(uin.casefold())
    observed = position >= 0
    if observed:
        start = max(0, position - 300)
        end = min(len(decoded_text), position + len(uin) + 300)
        quote = decoded_text[start:end]
    else:
        quote = decoded_text[:1000]
    return IdentityObservation(
        page_number=None,
        quote=quote,
        locator={
            "schema_version": 1,
            "blob_sha256": blob_sha256,
            "resolver_version": "coverguide-html/1",
            "kind": "html_element",
            "encoding": "utf-8",
            "selector": "body",
            "selector_language": "css",
            "occurrence": 0,
            "text_interpretation": "decoded_text_content",
            "attribute_name": None,
        },
        method="html",
        page_count=1,
        observed=observed,
    )


@transaction.atomic
def reconcile_capture_identity(
    capture: SourceCapture,
    payload: bytes,
    *,
    uin: str,
    issuer: str,
    notes: list[str],
    record_audit: bool,
) -> tuple[EvidenceSpan, bool]:
    if capture.original_file is None or capture.document_version_id is None:
        raise ValueError("Document identity requires preserved bytes and a document version.")
    original = capture.original_file
    version = DocumentVersion.objects.select_for_update().get(pk=capture.document_version_id)
    observation = inspect_identity(
        payload,
        media_type=original.media_type,
        blob_sha256=original.sha256,
        uin=uin,
    )
    page: DocumentPage | None = None
    if observation.page_number is not None:
        existing_pages = set(
            DocumentPage.objects.filter(original_file=original).values_list(
                "page_number", flat=True
            )
        )
        DocumentPage.objects.bulk_create(
            [
                DocumentPage(original_file=original, page_number=number)
                for number in range(1, observation.page_count + 1)
                if number not in existing_pages
            ]
        )
        page = DocumentPage.objects.get(
            original_file=original,
            page_number=observation.page_number,
        )
    candidates = list(
        EvidenceSpan.objects.filter(
            source_capture=capture,
            page=page,
            section_label="manifest identity",
        ).order_by("created_at")
    )
    span = next(
        (
            item
            for item in candidates
            if not observation.observed
            or (item.verification != "failed" and uin.casefold() in item.quote.casefold())
        ),
        None,
    )
    if span is None:
        span = EvidenceSpan.objects.create(
            source_capture=capture,
            page=page,
            section_label="manifest identity",
            quote=observation.quote or "No native identity text was extracted.",
            context={"span_ids": [], "notes": notes},
            method=observation.method,
            verification="unverified",
            locator=observation.locator,
        )
    identifiers = [
        {
            "issuer": issuer,
            "kind": "uin" if observation.observed else "expected_uin",
            "value": uin,
            **({"span_id": str(span.id)} if observation.observed else {}),
            "status": "observed" if observation.observed else "unresolved",
        }
    ]
    changed = version.identifiers != identifiers
    if changed:
        version.identifiers = identifiers
        version.save(update_fields=["identifiers", "updated_at"])
        if record_audit:
            AuditEvent.objects.create(
                operation="document_identity_reconciled",
                object_kind="document_version",
                object_id=version.id,
                outcome="succeeded",
                metadata={
                    "affected_count": 1,
                    "authorization_basis_code": "exact_preserved_source_bytes",
                },
            )
    return span, observation.observed


@transaction.atomic
def verify_observed_identity(capture: SourceCapture, *, uin: str) -> int:
    """Verify only an exact UIN passage after the document reconciliation succeeds."""

    if capture.document_version_id is None:
        raise ValueError("Document identity requires a document version.")
    version = DocumentVersion.objects.select_for_update().get(pk=capture.document_version_id)
    matching = [
        item for item in version.identifiers if isinstance(item, dict) and item.get("value") == uin
    ]
    if len(matching) != 1:
        raise ValueError("Document identity must contain one exact manifest UIN entry.")
    identifier = matching[0]
    if identifier.get("kind") == "expected_uin" and identifier.get("status") == "unresolved":
        return 0
    if identifier.get("kind") != "uin" or identifier.get("status") != "observed":
        raise ValueError("Document UIN identity has an invalid evidence state.")
    span_id = identifier.get("span_id")
    if not isinstance(span_id, str):
        raise ValueError("An observed document UIN requires an evidence span.")
    try:
        span = EvidenceSpan.objects.get(
            pk=span_id,
            source_capture=capture,
            section_label="manifest identity",
        )
    except (ValueError, EvidenceSpan.DoesNotExist) as exc:
        raise ValueError("Observed document UIN evidence is missing or foreign.") from exc
    if uin.casefold() not in span.quote.casefold():
        raise ValueError("Observed document UIN evidence does not contain the exact UIN.")
    if span.verification in {"text_verified", "visually_verified", "reviewed"}:
        return 0
    if span.verification != "unverified":
        raise ValueError("Observed document UIN evidence is not eligible for verification.")
    span.verification = "text_verified"
    span.save(update_fields=["verification"])
    return 1
