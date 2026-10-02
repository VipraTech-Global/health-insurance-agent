"""Exact clause anchors and PDF geometry, without modifying the captured document."""

from __future__ import annotations

import hashlib
import io
import json
import unicodedata
from functools import lru_cache
from typing import Any

import pdfplumber
from apps.adviser_v2.models import EvidenceSpan
from apps.adviser_v2.storage import read_public

from research_workspace.legacy_v2.processing.cited_facts import Clause, clause_offsets
from research_workspace.legacy_v2.processing.manifest_v2 import ANCHOR_PREFIX, validate_raw_quote

RECTANGLES_PREFIX = "clause_rectangles:"


def _normalized(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKC", text) if not c.isspace() and unicodedata.category(c) != "Cc")


@lru_cache(maxsize=24)
def _page_characters(storage_key: str, sha256: str, number: int) -> tuple[dict[str, Any], ...]:
    with pdfplumber.open(io.BytesIO(read_public(storage_key, sha256))) as pdf:
        return tuple(
            {key: char[key] for key in ("text", "x0", "x1", "top", "bottom")}
            for char in pdf.pages[number - 1].chars
        )


def clause_rectangles(chars: tuple[dict[str, Any], ...], quote: str, occurrence: int = 0) -> list[list[float]]:
    # NFKC/whitespace folding is for PDF geometry only. Raw quotation validation
    # above remains exact, including original line endings, spelling and punctuation.
    mapped = [(letter, char) for char in chars for letter in _normalized(char["text"])]
    text = "".join(letter for letter, _char in mapped)
    target = _normalized(quote)
    start = -1
    for _ in range(occurrence + 1):
        start = text.find(target, start + 1)
        if start < 0:
            raise ValueError("Exact raw clause has no unambiguous PDF character geometry.")
    rectangles: list[list[float]] = []
    for _letter, char in mapped[start:start + len(target)]:
        box = [float(char[k]) for k in ("x0", "top", "x1", "bottom")]
        if rectangles and abs(rectangles[-1][1] - box[1]) < 3 and -2 <= box[0] - rectangles[-1][2] < 20:
            rectangles[-1][0] = min(rectangles[-1][0], box[0])
            rectangles[-1][2] = max(rectangles[-1][2], box[2])
            rectangles[-1][3] = max(rectangles[-1][3], box[3])
        else:
            rectangles.append(box)
    return rectangles


def store_clause(clause: Clause, passage: dict[str, Any]) -> EvidenceSpan:
    start, end = clause_offsets(clause, passage["passage"])
    raw_quote = passage["passage"][start:end]
    source = EvidenceSpan.objects.select_related("page__original_file", "source_capture").get(pk=clause.page_span_id)
    if source.quote != passage["passage"] or source.page is None:
        raise ValueError("Clause parent is not its intact original raw page.")
    original = source.page.original_file
    chars = _page_characters(original.storage_key, original.sha256, source.page.page_number)
    # Reject ambiguity caused by repeated PDF text rather than highlighting an
    # arbitrary occurrence. Raw and visual occurrence indexes must agree.
    folded_prefix = _normalized(passage["passage"][:start])
    visual_occurrence = folded_prefix.count(_normalized(raw_quote))
    boxes = clause_rectangles(chars, raw_quote, visual_occurrence)
    anchor = {
        "page": passage["physical_page"], "start": start, "end": end,
        "page_text_sha256": hashlib.sha256(passage["passage"].encode()).hexdigest(),
        "document_start": passage["document_char_start"] + start,
        "document_end": passage["document_char_start"] + end,
    }
    locator = {
        **source.locator,
        "bbox": [min(b[0] for b in boxes), min(b[1] for b in boxes), max(b[2] for b in boxes), max(b[3] for b in boxes)],
    }
    span, _created = EvidenceSpan.objects.get_or_create(
        source_capture=source.source_capture, page=source.page,
        section_label=f"manifest-v2-clause-{start}-{end}-{hashlib.sha256(raw_quote.encode()).hexdigest()[:16]}",
        defaults={
            "quote": raw_quote, "method": "native_text", "verification": "reviewed",
            "locator": locator,
            "context": {"span_ids": [str(source.id)], "notes": [
                ANCHOR_PREFIX + json.dumps(anchor, sort_keys=True),
                RECTANGLES_PREFIX + json.dumps(boxes),
            ]},
        },
    )
    validate_raw_quote(span, {
        "text": passage["passage"], "page_number": passage["physical_page"],
        "document_char_start": passage["document_char_start"],
    }, blob_sha256=passage["document_sha256"])
    if span.locator != locator or RECTANGLES_PREFIX + json.dumps(boxes) not in span.context["notes"]:
        raise ValueError("Stored clause geometry differs from the original PDF.")
    return span
