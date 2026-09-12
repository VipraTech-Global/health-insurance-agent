import gzip
import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any, cast

from django.conf import settings
from django.db import transaction

from .models import DocumentPage, EvidenceBundle, EvidenceBundleSpan, EvidenceSpan
from .source_maps import DocumentValidationError


def _load_frozen_page(page: DocumentPage) -> dict[str, Any]:
    revision = page.extraction_revision
    root = Path(settings.DATA_ROOT).resolve()
    artifact_path = (root / revision.source_map_path).resolve()
    if root not in artifact_path.parents or not artifact_path.is_file():
        raise DocumentValidationError("Frozen source map is unavailable.")
    compressed = artifact_path.read_bytes()
    if hashlib.sha256(compressed).hexdigest() != revision.artifact_sha256:
        raise DocumentValidationError("Frozen source map hash does not match its revision.")
    artifact = json.loads(gzip.decompress(compressed))
    if artifact.get("document_id") != str(revision.document_version_id):
        raise DocumentValidationError("Source map belongs to a different document.")
    try:
        frozen_page = artifact["pages"][page.physical_index]
    except (IndexError, KeyError, TypeError) as exc:
        raise DocumentValidationError("Physical page is missing from the source map.") from exc
    if frozen_page.get("physical_index") != page.physical_index:
        raise DocumentValidationError("Physical page identity does not match.")
    return cast(dict[str, Any], frozen_page)


def _span_values(page: DocumentPage, start_line: int, end_line: int) -> dict[str, Any]:
    if start_line < 1 or end_line < start_line:
        raise DocumentValidationError("Reference line range is invalid.")
    frozen_page = _load_frozen_page(page)
    selected_lines = [
        line for line in frozen_page["lines"] if start_line <= int(line["number"]) <= end_line
    ]
    expected_count = end_line - start_line + 1
    if len(selected_lines) != expected_count:
        raise DocumentValidationError("One or more reference lines do not exist.")
    words_by_id = {word["id"]: word for word in frozen_page["words"]}
    word_ids = [word_id for line in selected_lines for word_id in line["word_ids"]]
    if not word_ids or any(word_id not in words_by_id for word_id in word_ids):
        raise DocumentValidationError("Reference words do not resolve in the frozen source map.")
    regions = {line["region"] for line in selected_lines}
    if len(regions) != 1:
        raise DocumentValidationError(
            "One evidence span cannot cross source regions; create separate spans instead."
        )
    quote = "\n".join(line["text"] for line in selected_lines)
    geometry = [words_by_id[word_id]["bbox"] for word_id in word_ids]
    return {
        "page": page,
        "region_id": selected_lines[0]["region"],
        "start_line": start_line,
        "end_line": end_line,
        "source_word_ids": word_ids,
        "quote": quote,
        "geometry": geometry,
    }


def create_evidence_bundle_from_ranges(
    ranges: Sequence[tuple[DocumentPage, int, int, str]], label: str
) -> EvidenceBundle:
    """Create one contextual bundle while preserving each source region as its own span."""
    if not ranges:
        raise DocumentValidationError("At least one reference line range is required.")
    values = [_span_values(page, start, end) for page, start, end, _role in ranges]
    with transaction.atomic():
        bundle = EvidenceBundle.objects.create(label=label)
        for order, (span_values, (_page, _start, _end, role)) in enumerate(
            zip(values, ranges, strict=True)
        ):
            span = EvidenceSpan.objects.create(**span_values)
            EvidenceBundleSpan.objects.create(
                bundle=bundle,
                span=span,
                role=role,
                order=order,
            )
    return bundle


def create_evidence_bundle(
    page: DocumentPage, start_line: int, end_line: int, label: str
) -> EvidenceBundle:
    return create_evidence_bundle_from_ranges([(page, start_line, end_line, "primary")], label)


def validate_evidence_span(span: EvidenceSpan) -> None:
    """Require a stored citation to match its hash-verified frozen source map exactly."""
    expected = _span_values(span.page, span.start_line, span.end_line)
    stored = {
        "region_id": span.region_id,
        "source_word_ids": span.source_word_ids,
        "quote": span.quote,
        "geometry": span.geometry,
    }
    resolved = {key: expected[key] for key in stored}
    if stored != resolved:
        raise DocumentValidationError("Stored evidence span differs from its frozen source map.")
