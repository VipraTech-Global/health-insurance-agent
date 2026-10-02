"""Preserve Poppler pages; OCR only blank native pages, with token geometry."""

from __future__ import annotations

import csv
import hashlib
import io
import subprocess
import tempfile
import uuid
from pathlib import Path

import pdfplumber

from .evidence import atomic_json


def extract(document: dict, root: Path) -> list[dict]:
    path = Path(document["path"])
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != document["sha256"]:
        raise ValueError("PDF content hash changed before extraction.")
    saved = root / "raw" / (document["sha256"] + ".json")
    if saved.exists():
        import json
        value = json.loads(saved.read_text())
        if value["pdf_sha256"] != document["sha256"] or value["version"] != "poppler-raw-ocr/1":
            raise ValueError("Raw source cache is incompatible.")
        return value["pages"]
    result = subprocess.run(["pdftotext", "-raw", str(path), "-"], capture_output=True, check=True, timeout=120)
    original_pages = result.stdout.decode("utf-8").split("\f")
    pages, offset = [], 0
    with pdfplumber.open(io.BytesIO(payload)) as pdf:
        if original_pages[-1] != "" or len(original_pages) - 1 != len(pdf.pages):
            raise ValueError("Poppler physical page count mismatch.")
        for number, (raw, page) in enumerate(zip(original_pages[:-1], pdf.pages, strict=True), 1):
            method, words = "native_text", []
            if not raw.strip():
                method = "ocr"
                with tempfile.TemporaryDirectory(prefix="demo-ocr-", dir=root) as work:
                    prefix = Path(work) / "page"
                    subprocess.run(["pdftoppm", "-f", str(number), "-l", str(number), "-singlefile",
                        "-r", "180", "-png", str(path), str(prefix)], check=True, capture_output=True, timeout=90)
                    ocr = subprocess.run(["tesseract", str(prefix) + ".png", "stdout", "tsv"],
                                         capture_output=True, text=True, check=True, timeout=120)
                    rows = list(csv.DictReader(io.StringIO(ocr.stdout), delimiter="\t"))
                    page_row = next(row for row in rows if row["level"] == "1")
                    sx, sy = page.width / int(page_row["width"]), page.height / int(page_row["height"])
                    raw, line = "", None
                    for row in rows:
                        if row["level"] != "5" or not row["text"].strip():
                            continue
                        new_line = (row["block_num"], row["par_num"], row["line_num"])
                        if raw:
                            raw += "\n" if new_line != line else " "
                        start = len(raw)
                        raw += row["text"]
                        x, y, w, h = (int(row[k]) for k in ("left", "top", "width", "height"))
                        words.append({"start": start, "end": len(raw), "confidence": float(row["conf"]),
                                      "bbox": [x*sx, y*sy, (x+w)*sx, (y+h)*sy]})
                        line = new_line
            if not raw.strip():
                raise ValueError(f"No source text could be extracted on physical page {number}.")
            page_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"{document['sha256']}:raw-page:{number}"))
            pages.append({"evidence_span_id": page_id, "physical_page": number,
                "passage": raw, "native_text": original_pages[number-1], "document_char_start": offset,
                "document_key": document["document_key"], "document_version_id": document["document_version_id"],
                "document_sha256": document["sha256"], "method": method, "ocr_words": words,
                "width": float(page.width), "height": float(page.height)})
            offset += len(raw) + 1
    atomic_json(saved, {"version": "poppler-raw-ocr/1", "pdf_sha256": document["sha256"], "pages": pages})
    return pages
