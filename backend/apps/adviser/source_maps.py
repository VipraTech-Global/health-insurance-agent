import gzip
import hashlib
import json
import os
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Any

import pdfplumber
from django.conf import settings
from django.db import transaction

from .models import DocumentPage, DocumentVersion, ExtractionRevision, SourceBlob


class DocumentValidationError(ValueError):
    pass


def store_pdf_bytes(content: bytes) -> SourceBlob:
    if not content.startswith(b"%PDF-"):
        raise DocumentValidationError("Downloaded content is not a PDF.")
    if b"%%EOF" not in content[-8192:]:
        raise DocumentValidationError("Downloaded PDF appears truncated.")
    digest = hashlib.sha256(content).hexdigest()
    relative = Path("source-blobs") / digest[:2] / f"{digest}.pdf"
    target = (Path(settings.DATA_ROOT) / relative).resolve()
    root = Path(settings.DATA_ROOT).resolve()
    if root not in target.parents:
        raise DocumentValidationError("Invalid source storage path.")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise DocumentValidationError(
                "Existing source blob does not match its content address."
            )
    else:
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(content)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, target)
    target.chmod(0o644)
    blob, _ = SourceBlob.objects.get_or_create(
        sha256=digest,
        defaults={
            "stored_path": str(relative),
            "byte_size": len(content),
            "media_type": "application/pdf",
        },
    )
    if (
        blob.stored_path != str(relative)
        or blob.byte_size != len(content)
        or blob.media_type != "application/pdf"
    ):
        raise DocumentValidationError("Stored source metadata conflicts with its content address.")
    return blob


def verified_source_path(blob: SourceBlob) -> Path:
    root = Path(settings.DATA_ROOT).resolve()
    source = (root / blob.stored_path).resolve()
    if root not in source.parents or not source.is_file():
        raise DocumentValidationError("Preserved source file is unavailable.")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    if digest != blob.sha256:
        raise DocumentValidationError("Preserved source file failed its integrity check.")
    return source


def _page_map(page: Any, physical_index: int) -> dict[str, Any]:
    words = page.extract_words(
        x_tolerance=2,
        y_tolerance=3,
        keep_blank_chars=False,
        use_text_flow=False,
    )
    rows: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for word in words:
        rows[round(float(word["top"]) / 3)].append(word)

    line_candidates: list[dict[str, Any]] = []
    split_threshold = max(36.0, float(page.width) * 0.08)
    for _, row_words in sorted(rows.items()):
        ordered = sorted(row_words, key=lambda item: float(item["x0"]))
        groups: list[list[dict[str, Any]]] = [[]]
        previous_x1: float | None = None
        for word in ordered:
            x0 = float(word["x0"])
            if (
                previous_x1 is not None
                and x0 - previous_x1 > split_threshold
                and len(groups[-1]) >= 2
            ):
                groups.append([])
            groups[-1].append(word)
            previous_x1 = float(word["x1"])
        for group in groups:
            group_x0 = min(float(word["x0"]) for word in group)
            group_x1 = max(float(word["x1"]) for word in group)
            group_width = group_x1 - group_x0
            if group_width >= float(page.width) * 0.55:
                region_id = "full-width"
            elif (group_x0 + group_x1) / 2 < float(page.width) / 2:
                region_id = "left-column"
            else:
                region_id = "right-column"
            line_candidates.append(
                {
                    "top": min(float(word["top"]) for word in group),
                    "x0": group_x0,
                    "region": region_id,
                    "words": group,
                }
            )

    ordered_groups: list[dict[str, Any]] = []
    pending_columns: list[dict[str, Any]] = []

    def flush_columns() -> None:
        for region_id in ("left-column", "right-column"):
            ordered_groups.extend(
                sorted(
                    (item for item in pending_columns if item["region"] == region_id),
                    key=lambda item: (item["top"], item["x0"]),
                )
            )
        pending_columns.clear()

    for candidate in sorted(line_candidates, key=lambda item: (item["top"], item["x0"])):
        if candidate["region"] == "full-width":
            flush_columns()
            ordered_groups.append(candidate)
        else:
            pending_columns.append(candidate)
    flush_columns()

    mapped_words: list[dict[str, Any]] = []
    lines: list[dict[str, Any]] = []
    word_sequence = 0
    for line_sequence, candidate in enumerate(ordered_groups, start=1):
        region_id = str(candidate["region"])
        group = candidate["words"]
        line_word_ids: list[str] = []
        for word in group:
            word_sequence += 1
            word_id = f"p{physical_index}-w{word_sequence}"
            line_word_ids.append(word_id)
            mapped_words.append(
                {
                    "id": word_id,
                    "text": word["text"],
                    "raw_text": word["text"],
                    "line": line_sequence,
                    "region": region_id,
                    "bbox": [
                        round(float(word["x0"]), 4),
                        round(float(page.height) - float(word["bottom"]), 4),
                        round(float(word["x1"]), 4),
                        round(float(page.height) - float(word["top"]), 4),
                    ],
                    "method": "native",
                }
            )
        lines.append(
            {
                "number": line_sequence,
                "region": region_id,
                "word_ids": line_word_ids,
                "text": " ".join(str(word["text"]) for word in group),
            }
        )
    return {
        "physical_index": physical_index,
        "display_page": physical_index + 1,
        "width": round(float(page.width), 4),
        "height": round(float(page.height), 4),
        "rotation": int(page.rotation or 0),
        "crop_box": [round(float(value), 4) for value in page.cropbox],
        "media_box": [round(float(value), 4) for value in page.mediabox],
        "coordinate_system": "pdf-bottom-left",
        "words": mapped_words,
        "lines": lines,
        "raw_text": "\n".join(line["text"] for line in lines),
        "extraction_method": "pdfplumber-native",
    }


def extract_native_document(document: DocumentVersion) -> ExtractionRevision:
    root = Path(settings.DATA_ROOT).resolve()
    source = verified_source_path(document.blob)
    with pdfplumber.open(source, strict_metadata=True) as pdf:
        pages = [_page_map(page, index) for index, page in enumerate(pdf.pages)]
    if not pages or not any(page["words"] for page in pages):
        raise DocumentValidationError("No native text geometry was found; OCR review is required.")
    with transaction.atomic():
        DocumentVersion.objects.select_for_update().get(id=document.id)
        latest = (
            ExtractionRevision.objects.filter(document_version=document)
            .order_by("-revision")
            .first()
        )
        revision_number = 1 if latest is None else latest.revision + 1
        artifact = {
            "schema_version": 1,
            "document_id": str(document.id),
            "document_sha256": document.blob.sha256,
            "revision": revision_number,
            "pages": pages,
        }
        compressed = gzip.compress(
            json.dumps(artifact, ensure_ascii=False, separators=(",", ":")).encode(),
            mtime=0,
        )
        artifact_hash = hashlib.sha256(compressed).hexdigest()
        relative = (
            Path("extractions")
            / str(document.id)
            / f"revision-{revision_number}-{artifact_hash}.json.gz"
        )
        target = (root / relative).resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as temporary:
            temporary.write(compressed)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary_path = Path(temporary.name)
        os.replace(temporary_path, target)
        revision = ExtractionRevision.objects.create(
            document_version=document,
            revision=revision_number,
            parser_manifest={
                "parser": "pdfplumber",
                "version": pdfplumber.__version__,
                "settings": {
                    "x_tolerance": 2,
                    "y_tolerance": 3,
                    "line_split_threshold": "max(36,page_width*0.08)",
                },
            },
            artifact_sha256=artifact_hash,
            source_map_path=str(relative),
            published=False,
        )
        DocumentPage.objects.bulk_create(
            [
                DocumentPage(
                    extraction_revision=revision,
                    physical_index=page["physical_index"],
                    width=page["width"],
                    height=page["height"],
                    rotation=page["rotation"],
                    geometry={
                        "crop_box": page["crop_box"],
                        "media_box": page["media_box"],
                        "coordinate_system": page["coordinate_system"],
                    },
                )
                for page in pages
            ]
        )
    return revision
