"""Native, layout and narrowly-triggered OCR readers for exact source bytes."""

from __future__ import annotations

import hashlib
import io
import os
import re
import shutil
import subprocess
import tempfile
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Any

import pdfplumber
from django.conf import settings

from ..manifest import html_text

DOCLING_VERSION = "2.126.0"
TESSERACT_LANGUAGES = frozenset({"eng", "hin"})


class DependencyUnavailable(RuntimeError):
    pass


def classify_bytes(payload: bytes, declared_kind: str | None) -> dict[str, Any]:
    if payload.startswith(b"%PDF-"):
        media_type = "application/pdf"
        with pdfplumber.open(io.BytesIO(payload), strict_metadata=True) as document:
            sample = " ".join((page.extract_text() or "") for page in document.pages[:3])
            page_count = len(document.pages)
    else:
        media_type = "text/html"
        sample = html_text(payload)[:20_000]
        page_count = 1
    lowered = sample.lower()
    inferred = declared_kind or "other"
    markers = {
        "policy_wording": ("policy wording", "terms and conditions"),
        "customer_information_sheet": ("customer information sheet", "cis"),
        "prospectus": ("prospectus",),
        "premium_table": ("premium", "rate chart"),
        "endorsement": ("endorsement", "add-on", "rider"),
        "notice": ("revision", "modification", "amendment"),
        "provider_list": ("network hospital", "cashless hospital"),
    }
    observed = [kind for kind, values in markers.items() if any(item in lowered for item in values)]
    issues: list[dict[str, Any]] = []
    if (
        declared_kind
        and observed
        and declared_kind not in observed
        and declared_kind not in {"web_page", "other"}
    ):
        issues.append(
            issue(
                "classification_disagreement",
                f"Declared {declared_kind}; content markers suggest {', '.join(observed)}.",
                material=True,
                retry_instruction="Review the exact document role and manifest entry.",
            )
        )
    return {
        "schema_version": 1,
        "media_type": media_type,
        "declared_kind": declared_kind,
        "inferred_kind": inferred,
        "observed_markers": observed,
        "page_count": page_count,
        "relevant": inferred != "unrelated",
        "issues": issues,
    }


def issue(
    code: str,
    description: str,
    *,
    material: bool,
    retry_instruction: str,
    region_span_ids: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "region_span_ids": region_span_ids or [],
        "description": description,
        "material": material,
        "retry_instruction": retry_instruction,
        "resolved": False,
    }


def _line_dict(line: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": str(line.get("text", "")),
        "x0": float(line.get("x0", 0)),
        "top": float(line.get("top", 0)),
        "x1": float(line.get("x1", 0)),
        "bottom": float(line.get("bottom", 0)),
    }


def _word_dict(word: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": str(word.get("text", "")),
        "x0": float(word.get("x0", 0)),
        "top": float(word.get("top", 0)),
        "x1": float(word.get("x1", 0)),
        "bottom": float(word.get("bottom", 0)),
    }


def native_pdf_read(payload: bytes) -> dict[str, Any]:
    pages: list[dict[str, Any]] = []
    with pdfplumber.open(io.BytesIO(payload), strict_metadata=True) as document:
        for page_number, page in enumerate(document.pages, 1):
            text = page.extract_text(layout=False) or ""
            words = [_word_dict(item) for item in page.extract_words(use_text_flow=True)]
            raw_lines = page.extract_text_lines(strip=True, return_chars=False) or []
            lines = [_line_dict(item) for item in raw_lines if str(item.get("text", "")).strip()]
            tables = page.extract_tables() or []
            alphanumeric = len(re.findall(r"[A-Za-z0-9\u0900-\u097f]", text))
            replacement_ratio = text.count("�") / max(1, len(text))
            reasons: list[str] = []
            if alphanumeric < 20:
                reasons.append("too_little_native_text")
            if replacement_ratio > 0.02:
                reasons.append("high_replacement_character_ratio")
            if not words and page.images:
                reasons.append("image_only_page")
            pages.append(
                {
                    "page_number": page_number,
                    "width": float(page.width),
                    "height": float(page.height),
                    "rotation": int(page.rotation or 0) % 360,
                    "text": text,
                    "lines": lines,
                    "words": words,
                    "tables": tables,
                    "figure_count": len(page.images),
                    "needs_ocr": bool(reasons),
                    "unreliable_reasons": reasons,
                    "native_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                }
            )
    if not pages:
        raise ValueError("PDF has no physical pages.")
    return {"schema_version": 1, "reader": "pdfplumber-0.11.10", "pages": pages}


def _table_text(item: Any) -> str:
    rows: dict[int, list[tuple[int, str]]] = {}
    data = getattr(item, "data", None)
    for cell in getattr(data, "table_cells", []) if data is not None else []:
        text = str(getattr(cell, "text", "")).strip()
        if not text:
            continue
        row = int(getattr(cell, "start_row_offset_idx", 0))
        column = int(getattr(cell, "start_col_offset_idx", 0))
        rows.setdefault(row, []).append((column, text))
    return "\n".join(
        " | ".join(value for _column, value in sorted(cells))
        for _row, cells in sorted(rows.items())
    )


def _typed_layout_nodes(document: Any) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for item, _level in document.iterate_items(traverse_pictures=True):
        raw_label = getattr(item, "label", "unspecified")
        label = str(getattr(raw_label, "value", raw_label))
        text = _table_text(item) if label == "table" else str(getattr(item, "text", ""))
        provenance = [
            value.model_dump(mode="json")
            for value in (getattr(item, "prov", None) or [])
            if hasattr(value, "model_dump")
        ]
        nodes.append(
            {
                "order": len(nodes),
                "label": label,
                "text": text[:20_000],
                "provenance": provenance,
            }
        )
    return nodes


def docling_layout(payload: bytes) -> dict[str, Any]:
    artifacts_setting = settings.COVERGUIDE_DOCLING_ARTIFACTS_PATH
    if not artifacts_setting:
        raise DependencyUnavailable("COVERGUIDE_DOCLING_ARTIFACTS_PATH is not configured.")
    artifacts = Path(artifacts_setting).resolve()
    if not artifacts.is_dir():
        raise DependencyUnavailable("The configured Docling model-artifact directory is missing.")
    try:
        installed = version("docling")
        if installed != DOCLING_VERSION:
            raise DependencyUnavailable(
                f"Docling {DOCLING_VERSION} is required; found {installed}."
            )
        from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions
        from docling.document_converter import DocumentConverter, PdfFormatOption
    except (ImportError, PackageNotFoundError) as exc:
        raise DependencyUnavailable(f"Docling {DOCLING_VERSION} is not installed.") from exc

    class StablePdfPipelineOptions(PdfPipelineOptions):
        """Avoid serializing unused VLM option subtypes into Docling's cache key."""

        def model_dump_json(self, *args: Any, **kwargs: Any) -> str:
            # Docling 2.126.0 requests serialize_as_any=True for its pipeline cache.
            # Pydantic 2.11.9 detects a cycle in the default, disabled picture/code
            # VLM option graph. This pipeline disables those remote/VLM features, so
            # the declared base-field representation is the stable cache identity.
            kwargs["serialize_as_any"] = False
            return super().model_dump_json(*args, **kwargs)

    pipeline_options = StablePdfPipelineOptions(
        artifacts_path=artifacts,
        do_ocr=False,
        do_table_structure=True,
        do_code_enrichment=False,
        do_formula_enrichment=False,
        do_picture_classification=False,
        do_picture_description=False,
        enable_remote_services=False,
        allow_external_plugins=False,
        accelerator_options=AcceleratorOptions(
            device=AcceleratorDevice.CPU,
            num_threads=max(1, min(8, os.cpu_count() or 1)),
        ),
    )
    converter = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)}
    )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temporary:
            temporary.write(payload)
            temporary_path = Path(temporary.name)
        result = converter.convert(temporary_path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    nodes = _typed_layout_nodes(result.document)
    if not nodes:
        raise ValueError("Docling returned no layout nodes.")
    return {
        "schema_version": 1,
        "reader": f"docling-{DOCLING_VERSION}",
        "nodes": nodes,
        "node_counts": {
            label: sum(1 for item in nodes if item["label"] == label)
            for label in sorted({str(item["label"]) for item in nodes})
        },
    }


def tesseract_languages() -> set[str]:
    executable = settings.COVERGUIDE_TESSERACT_PATH or shutil.which("tesseract")
    if executable is None:
        raise DependencyUnavailable("Tesseract is not installed.")
    if not Path(executable).is_file():
        raise DependencyUnavailable("The configured Tesseract executable is missing.")
    result = subprocess.run(
        [executable, "--list-langs"],
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    )
    languages = {line.strip() for line in result.stdout.splitlines()[1:] if line.strip()}
    missing = TESSERACT_LANGUAGES - languages
    if missing:
        raise DependencyUnavailable(
            "Tesseract is missing required language data: " + ", ".join(sorted(missing))
        )
    return languages


def ocr_pdf_pages(payload: bytes, page_numbers: list[int]) -> dict[int, str]:
    if not page_numbers:
        return {}
    executable = settings.COVERGUIDE_TESSERACT_PATH or shutil.which("tesseract")
    if executable is None:
        raise DependencyUnavailable("Tesseract is not installed.")
    tesseract_languages()
    try:
        import pypdfium2
    except ImportError as exc:
        raise DependencyUnavailable("pypdfium2 is required for bounded OCR rendering.") from exc
    document = pypdfium2.PdfDocument(payload)
    results: dict[int, str] = {}
    try:
        for page_number in page_numbers:
            if page_number < 1 or page_number > len(document):
                raise ValueError("OCR page is outside the physical PDF range.")
            bitmap = document[page_number - 1].render(scale=2.5)
            image = bitmap.to_pil()
            image_bytes = io.BytesIO()
            image.save(image_bytes, format="PNG")
            completed = subprocess.run(
                [str(executable), "stdin", "stdout", "-l", "eng+hin", "--psm", "6"],
                input=image_bytes.getvalue(),
                check=True,
                capture_output=True,
                timeout=120,
            )
            results[page_number] = completed.stdout.decode("utf-8", errors="replace")
    finally:
        document.close()
    return results
