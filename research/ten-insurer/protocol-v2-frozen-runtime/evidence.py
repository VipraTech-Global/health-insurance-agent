"""Original-text sections are a distinct type from generated navigation metadata."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path

from ..evidence_retrieval import token_count, tokenizer
from .relay import MODELS

PROCESSING_VERSION = "pageindex-sections/1"
MAP_SETTINGS = {"node_summaries": True, "document_description": True,
                "max_pages": 8, "max_tokens": 4000}


def digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def atomic_json(path: Path, value: object) -> None:
    import os
    import tempfile

    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=path.parent, prefix=path.name + ".", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as stream:
            json.dump(value, stream, ensure_ascii=False, sort_keys=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


@dataclass(frozen=True)
class Segment:
    page_id: str
    page: int
    start: int
    end: int
    document_start: int
    document_end: int
    text: str
    method: str = "native_text"


@dataclass(frozen=True)
class Section:
    id: str
    plan_id: str
    document_id: str
    document_sha256: str
    role: str
    title_path: tuple[str, ...]
    segments: tuple[Segment, ...]
    fallback: bool = False

    @property
    def text(self) -> str:
        return "\f".join(s.text for s in self.segments)

    @property
    def index_text(self) -> str:
        # Generated descriptions and summaries are structurally unavailable here.
        return " > ".join(self.title_path) + "\n" + self.text

    def payload(self) -> dict:
        return asdict(self)

    @classmethod
    def from_payload(cls, value: dict) -> Section:
        return cls(**{**value, "title_path": tuple(value["title_path"]),
                      "segments": tuple(Segment(**s) for s in value["segments"])})


@dataclass(frozen=True)
class Packet:
    plan_id: str
    sections: tuple[Section, ...]
    omitted_ids: tuple[str, ...]
    tokens: int
    budget: int = 16000
    tables: tuple[dict, ...] = ()

    def evidence(self) -> dict:
        # No navigation object is accepted or merged by this function.
        return {"plan_id": self.plan_id, "sections": [s.payload() for s in self.sections],
                "omitted_ids": list(self.omitted_ids), "tokens": self.tokens, "tables": list(self.tables)}


def cache_matches(saved: dict, *, pdf_sha: str, raw_sha: str, sdk_revision: str) -> bool:
    return (saved.get("pdf_sha256") == pdf_sha and saved.get("raw_sha256") == raw_sha
            and saved.get("sdk_revision") == sdk_revision
            and saved.get("processing_version") == PROCESSING_VERSION
            and saved.get("settings") == MAP_SETTINGS
            and bool(saved.get("models"))
            and all(model in MODELS for model in saved["models"]))


def map_ranges(nodes: list[dict], page_count: int) -> list[tuple[int, int, tuple[str, ...], str]]:
    """Validate nesting before assigning deepest ownership, including parent gaps.

    Printed sections can start/end on a shared boundary page. Such a page is kept
    intact once, with all overlapping leaf labels, so no source text is discarded.
    Crossing interior ranges, inversions and out-of-parent children are rejected.
    """
    identities = set()
    labels: dict[int, list[tuple[tuple[str, ...], str]]] = {p: [] for p in range(1, page_count + 1)}

    def walk(items, parent_start=1, parent_end=page_count, path=()):
        previous_end = None
        for node in items:
            a, b = node["start_index"], node["end_index"]
            if type(a) is not int or type(b) is not int or not parent_start <= a <= b <= parent_end:
                raise ValueError("Map node outside its ordered parent bounds.")
            if previous_end is not None and a < previous_end:
                raise ValueError("Map sibling ranges cross.")
            previous_end = b
            key, title = node["node_id"], node["title"]
            if not isinstance(key, str) or key in identities or not isinstance(title, str) or not title:
                raise ValueError("Map node IDs/titles are invalid or duplicated.")
            if not isinstance(node.get("summary"), str):
                raise ValueError("Map summaries are required for navigation.")
            identities.add(key)
            current = (*path, title)
            for page in range(a, b + 1):
                labels[page].append((current, node["summary"]))
            walk(node.get("nodes", []), a, b, current)

    if not nodes:
        raise ValueError("Map is empty.")
    walk(nodes)
    ranges = []
    for page, choices in labels.items():
        if choices:
            deepest = max(len(path) for path, _ in choices)
            leaves = [(path, summary) for path, summary in choices if len(path) == deepest]
            path = tuple(dict.fromkeys(title for p, _ in leaves for title in p))
            summary = "\n".join(s for _, s in leaves)
        else:
            path, summary = ("Document front matter / source outside mapped nodes",), ""
        if ranges and ranges[-1][2:] == (path, summary):
            ranges[-1] = (ranges[-1][0], page, path, summary)
        else:
            ranges.append((page, page, path, summary))
    return ranges


def _windows(text: str, *, fallback: bool) -> list[tuple[int, int]]:
    tokens = tokenizer().encode(text, disallowed_special=())
    if not fallback and len(tokens) <= 2000:
        return [(0, len(text))]
    _, offsets = tokenizer().decode_with_offsets(tokens)
    offsets.append(len(text))
    if fallback:
        result = []
        for first in range(0, len(tokens), 896):
            last = min(first + 1024, len(tokens))
            result.append((offsets[first], offsets[last]))
            if last == len(tokens):
                break
        return result
    # Prefer source subheading / paragraph / sentence boundaries without gaps.
    boundaries = [m.end() for m in re.finditer(r"\n\s*\n|(?<=[.!?;])\s+\n|\n(?=\s*(?:\d+[.)]|[A-Z][A-Z ]{5,})\s)", text)]
    result, start, first = [], 0, 0
    while start < len(text):
        while first < len(tokens) and offsets[first] < start:
            first += 1
        target = offsets[min(first + 1024, len(tokens))]
        maximum = offsets[min(first + 2000, len(tokens))]
        options = [b for b in boundaries if start < b <= target]
        end = max(options) if options else next((b for b in boundaries if target <= b <= maximum), target)
        if end <= start:
            end = min(len(text), start + 1)
        result.append((start, end))
        start = end
    return result


def build_sections(*, plan_id: str, document: dict, pages: list[dict], saved_map: dict | None) -> tuple[list[Section], list[dict], str | None]:
    pages = sorted(pages, key=lambda p: p["physical_page"])
    if [p["physical_page"] for p in pages] != list(range(1, len(pages) + 1)):
        raise ValueError("Original physical pages must be complete and ordered.")
    reason = None
    try:
        if saved_map is None:
            raise ValueError("No completed map.")
        if not isinstance(saved_map["tree"].get("doc_description"), str):
            raise ValueError("Map document description is required.")
        ranges = map_ranges(saved_map["tree"]["structure"], len(pages))
    except (ValueError, KeyError, TypeError) as exc:
        reason = str(exc)
        ranges = [(1, len(pages), ("Original source fallback",), "")]
    sections, navigation = [], []
    for a, b, path, summary in ranges:
        source_pages = pages[a - 1:b]
        source = "\f".join(p["passage"] for p in source_pages)
        local_starts, offset = [], 0
        for page in source_pages:
            local_starts.append(offset)
            offset += len(page["passage"]) + 1
        for left, right in _windows(source, fallback=reason is not None):
            segments = []
            for page, page_start in zip(source_pages, local_starts, strict=True):
                begin, end = max(0, left - page_start), min(len(page["passage"]), right - page_start)
                if begin < end:
                    segments.append(Segment(page["evidence_span_id"], page["physical_page"], begin, end,
                        page["document_char_start"] + begin, page["document_char_start"] + end,
                        page["passage"][begin:end], page.get("method", "native_text")))
            if not segments:
                continue
            key = digest([PROCESSING_VERSION, plan_id, document["sha256"], path,
                          [(s.page, s.start, s.end) for s in segments]])
            section = Section(key, plan_id, document["document_version_id"], document["sha256"],
                              document.get("role", "base_wording"), path, tuple(segments), bool(reason))
            sections.append(section)
            navigation.append({"section_id": key, "title_path": path,
                "pages": [segments[0].page, segments[-1].page],
                "summary": section.text.splitlines()[0] if reason else summary,
                "description": "" if reason else saved_map["tree"]["doc_description"],
                "fallback": bool(reason)})
    # All non-whitespace source characters must be represented, including front matter.
    for page in pages:
        spans = sorted((s.start, s.end) for c in sections for s in c.segments
                       if s.page_id == page["evidence_span_id"])
        cursor = 0
        for begin, end in spans:
            if begin > cursor and page["passage"][cursor:begin].strip():
                raise ValueError("Section derivation lost original source text.")
            cursor = max(cursor, end)
        if page["passage"][cursor:].strip():
            raise ValueError("Section derivation lost the end of a page.")
    return sections, navigation, reason


def pack_sections(plan_id: str, ranked: list[Section], *, budget: int = 16000, tables: list[dict] | None = None) -> Packet:
    if not 1 <= budget <= 16000:
        raise ValueError("Packet budget must be 1..16000.")
    selected, omitted, seen, used = [], [], set(), 0
    for section in ranked:
        if section.plan_id != plan_id:
            raise ValueError("Wrong-plan section rejected before packet assembly.")
        if section.id in seen:
            continue
        seen.add(section.id)
        cost = token_count(json.dumps(section.payload(), ensure_ascii=False))
        if used + cost <= budget:
            selected.append(section)
            used += cost
        else:
            omitted.append(section.id)
    regions = []
    selected_ids = {s.id for s in selected}
    for table in tables or []:
        cells = {k: c for k, c in table["cells"].items() if c["citation"]["section_id"] in selected_ids}
        if cells:
            candidate = {**table, "cells": cells}
            cost = token_count(json.dumps(candidate, ensure_ascii=False))
            if used + cost <= budget:
                regions.append(candidate)
                used += cost
            else:
                omitted.append("table:" + table["id"])
    # Include wrapper and omission metadata in the actual packet budget.
    while selected:
        packet = Packet(plan_id, tuple(selected), tuple(omitted), used, budget, tuple(regions))
        actual = token_count(json.dumps(packet.evidence(), ensure_ascii=False))
        if actual <= budget:
            return Packet(plan_id, tuple(selected), tuple(omitted), actual, budget, tuple(regions))
        if regions:
            omitted.append("table:" + regions.pop()["id"])
        else:
            omitted.append(selected.pop().id)
    return Packet(plan_id, (), tuple(omitted), 0, budget)


def reference_covered(reference: dict, packet: Packet) -> bool:
    spans = sorted((s.start, s.end) for c in packet.sections for s in c.segments
                   if s.page_id == reference["page_span_id"])
    cursor = reference["start"]
    for start, end in spans:
        if start <= cursor:
            cursor = max(cursor, end)
    return cursor >= reference["end"]
