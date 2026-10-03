"""Recover missing table cells only inside a validated H packet's source pages.

Repeated cell text is resolved by exact PDF glyph geometry, not first-match
selection. Indexes/maps/embeddings remain immutable. Every recovered unit passes
the same six answer checks before it becomes card evidence.
"""

import hashlib
import json
import re
from dataclasses import replace
from pathlib import Path

import pdfplumber

from .contracts import Answer, Citation, Statement, SupportedText, TableSupport
from .evidence import Section, pack_sections
from .highlighting import _normalized
from .quotations import locate, normalized
from .text import token_count
from .validation import validate


def cell_citation(bundle, page, chars, box, printed):
    target = _normalized(printed)
    mapped = [(letter, char) for char in chars for letter in _normalized(char["text"])]
    native = "".join(c for c, _ in mapped)
    positions = [m.start() for m in re.finditer(re.escape(target), native)]
    source, _ = normalized(page["passage"])
    source_matches = [m.start() for m in re.finditer(re.escape(normalized(printed)[0]), source)]
    if not target or len(positions) != len(source_matches):
        raise ValueError("Cell occurrence differs between source text and PDF geometry.")
    matches = []
    for occurrence, start in enumerate(positions):
        selected = [c for _, c in mapped[start : start + len(target)]]
        if all(
            box[0] - 1 <= (c["x0"] + c["x1"]) / 2 <= box[2] + 1
            and box[1] - 1 <= (c["top"] + c["bottom"]) / 2 <= box[3] + 1
            for c in selected
        ):
            matches.append(occurrence)
    if len(matches) != 1:
        raise ValueError("Cell has no unique exact occurrence inside its physical rectangle.")
    a, b = locate(page["passage"], printed, matches[0])
    candidates = []
    for section in bundle["sections"]:
        for segment in section["segments"]:
            if (
                segment["page_id"] == page["evidence_span_id"]
                and segment["start"] <= a
                and b <= segment["end"]
            ):
                quote = page["passage"][a:b]
                occurrence = 0
                while locate(segment["text"], quote, occurrence)[0] != a - segment["start"]:
                    occurrence += 1
                candidates.append(
                    Citation(
                        section_id=section["id"],
                        page_id=segment["page_id"],
                        quote=quote,
                        occurrence=occurrence,
                    )
                )
    if not candidates:
        raise ValueError("Cell crosses a source-section boundary.")
    # Overlapping fallback windows may contain the same uniquely resolved
    # absolute PDF span. Either window cites that same span; choose stably.
    return min(candidates, key=lambda c: c.section_id)


def resolve_sum_grid(result, bundle, statements, *, field="sum_insured"):
    packet_data = result.get("packet")
    if not packet_data:
        return statements
    sections = [Section.from_payload(s) for s in packet_data["sections"]]
    pages = {c["page_id"] for s in statements for c in s["citations"]}
    if field in {"opd", "room_limit"}:
        pages = {p.page_id for s in sections for p in s.segments}
    recovered = []
    diagnostics = result.setdefault("table_projection_omissions", [])
    for region in bundle.get("tables", []):
        # Only augment tables on already-cited H packet pages, preserving the
        # retrieval scope. Three required cells can fit when a whole grid cannot.
        if not any(c["citation"]["page_id"] in pages for c in region["cells"].values()):
            continue
        sha, physical, number = region["id"].rsplit(":", 2)
        doc = next((d for d in bundle["documents"] if d["sha256"] == sha), None)
        if not doc or hashlib.sha256(Path(doc["path"]).read_bytes()).hexdigest() != sha:
            continue
        raw = next(
            (
                p
                for p in bundle["pages"]
                if p["physical_page"] == int(physical)
                and p.get("document_id") == region["document_id"]
            ),
            None,
        )
        if raw is None:
            raw = next(
                (
                    p
                    for p in bundle["pages"]
                    if p["evidence_span_id"] in pages
                    and p["physical_page"] == int(physical)
                    and any(
                        s.document_id == region["document_id"]
                        and any(seg.page_id == p["evidence_span_id"] for seg in s.segments)
                        for s in sections
                    )
                ),
                None,
            )
        if raw is None:
            continue
        with pdfplumber.open(doc["path"]) as pdf:
            page = pdf.pages[int(physical) - 1]
            tables = page.find_tables()
            if int(number) >= len(tables):
                continue
            table = tables[int(number)]
            grid = table.extract()
            headers = [
                (r, c, None)
                for r, row in enumerate(grid)
                for c, v in enumerate(row)
                if v
                and normalized(v)[0].casefold()
                == normalized(bundle.get("variant", "Default"))[0].casefold()
            ]
            labels = [
                (r, c)
                for r, row in enumerate(grid)
                for c, v in enumerate(row)
                if v
                and re.fullmatch(
                    (
                        r"(?:Base\s*)?Sum\s*Insured\s*(?:\[BSI\])?\s*\(in\s*Lakhs?\)"
                        if field == "sum_insured"
                        else r"Room\s*(?:Type|Rent|Category)[\s\S]*"
                        if field == "room_limit"
                        else r"(?:Out[ -]?patient(?:\s+(?:Treatment|Cover|Benefit|Expenses))?|OPD)(?:\s*\([^)]*\))?"
                    ),
                    v,
                    re.I,
                )
            ]
            # A benefits grid may continue onto the next physical page.
            # Reuse only a unique header in the immediately preceding page's
            # same-width table, aligned to the selected value column.
            if field == "opd" and not headers and int(physical) > 1:
                previous = pdf.pages[int(physical) - 2]
                previous_raw = next(
                    (
                        p
                        for p in bundle["pages"]
                        if p["physical_page"] == int(physical) - 1
                        and any(
                            s["document_id"] == region["document_id"]
                            and any(
                                seg["page_id"] == p["evidence_span_id"] for seg in s["segments"]
                            )
                            for s in bundle["sections"]
                        )
                    ),
                    None,
                )
                if previous_raw:
                    possibilities = []
                    for previous_table in previous.find_tables():
                        if (
                            abs(previous_table.bbox[0] - table.bbox[0]) > 2
                            or abs(previous_table.bbox[2] - table.bbox[2]) > 2
                        ):
                            continue
                        previous_grid = previous_table.extract()
                        for r, row in enumerate(previous_grid):
                            for c, value in enumerate(row):
                                if not value or not re.search(
                                    r"\b" + re.escape(bundle.get("variant", "Default")) + r"\b",
                                    value,
                                    re.I,
                                ):
                                    continue
                                if any(
                                    v != bundle.get("variant")
                                    and re.search(r"\b" + re.escape(v) + r"\b", value, re.I)
                                    for v in bundle.get("variants", [])
                                ):
                                    continue
                                header_box = previous_table.rows[r].cells[c]
                                for vr, rc in labels:
                                    for column, printed in enumerate(grid[vr]):
                                        if (
                                            column <= rc
                                            or not printed
                                            or not re.fullmatch(
                                                r"Not\s+(?:Available|Covered)", printed, re.I
                                            )
                                        ):
                                            continue
                                        value_box = table.rows[vr].cells[column]
                                        if (
                                            abs(header_box[0] - value_box[0]) <= 2
                                            and abs(header_box[2] - value_box[2]) <= 2
                                        ):
                                            possibilities.append(
                                                (
                                                    -1,
                                                    column,
                                                    (
                                                        previous_raw,
                                                        previous.chars,
                                                        header_box,
                                                        value,
                                                    ),
                                                )
                                            )
                    if len(possibilities) == 1:
                        headers = possibilities
                    elif possibilities:
                        diagnostics.append(
                            {
                                "region": region["id"],
                                "reason": "Preceding-page variant header is ambiguous.",
                            }
                        )
            for hr, hc, previous_header in headers:
                for vr, rc in labels:
                    if not hr < vr or not rc < hc or not grid[vr][hc]:
                        continue
                    printed = grid[vr][hc]
                    if not re.fullmatch(
                        r"[\d\s/.,&]+\s*(?:Lakhs?|Lacs?)"
                        if field == "sum_insured"
                        else r"[^\n]*(?:room|sharing)[\s\S]*"
                        if field == "room_limit"
                        else r"Not\s+(?:Available|Covered)",
                        printed,
                        re.I,
                    ):
                        continue
                    selected = [(vr, rc), (hr, hc), (vr, hc)]
                    cells = {}
                    try:
                        for r, c in selected:
                            key = f"{region['id']}:{r}:{c}"
                            if r == -1 and previous_header:
                                cite = cell_citation(bundle, *previous_header)
                            else:
                                cite = cell_citation(
                                    bundle, raw, page.chars, table.rows[r].cells[c], grid[r][c]
                                )
                            cells[key] = {
                                "id": key,
                                "table_id": region["id"],
                                "row": r,
                                "column": c,
                                "text": cite.quote,
                                "citation": cite.model_dump(),
                            }
                    except (ValueError, IndexError, TypeError) as exc:
                        diagnostics.append({"region": region["id"], "reason": str(exc)})
                        continue  # Leave this bounded projection unresolved.
                    identifiers = list(cells)
                    citations = [Citation.model_validate(c["citation"]) for c in cells.values()]
                    conditions = [
                        item for original in statements for item in original.get("conditions", [])
                    ]
                    restrictions = [
                        item for original in statements for item in original.get("restrictions", [])
                    ]
                    if len(conditions) > 12 or len(restrictions) > 12:
                        diagnostics.append(
                            {
                                "region": region["id"],
                                "reason": "Required conditions exceed the bounded statement contract.",
                            }
                        )
                        continue
                    statement = Statement(
                        text="\n\n".join(c.quote for c in citations),
                        citations=citations,
                        excerpts=[c.quote for c in citations],
                        heading="Table excerpts",
                        conditions=[
                            SupportedText.model_validate(item)
                            for original in statements
                            for item in original.get("conditions", [])
                        ],
                        restrictions=[
                            SupportedText.model_validate(item)
                            for original in statements
                            for item in original.get("restrictions", [])
                        ],
                        table=TableSupport(
                            region_id=region["id"],
                            row_label_ids=[identifiers[0]],
                            column_label_ids=[identifiers[1]],
                            value_cell_id=identifiers[2],
                        ),
                    )
                    extended_region = {**region, "cells": cells}
                    required_sections = list(sections)
                    for cite in citations:
                        if not any(s.id == cite.section_id for s in required_sections):
                            required_sections.append(
                                Section.from_payload(
                                    next(
                                        s for s in bundle["sections"] if s["id"] == cite.section_id
                                    )
                                )
                            )
                    packet = pack_sections(
                        bundle["policy_version_id"],
                        required_sections,
                        budget=16000,
                        tables=[extended_region],
                    )
                    packet = replace(
                        packet,
                        omitted_ids=tuple(
                            dict.fromkeys(
                                [*packet_data.get("omitted_ids", []), *packet.omitted_ids]
                            )
                        ),
                    )
                    packet = replace(
                        packet,
                        tokens=token_count(json.dumps(packet.evidence(), ensure_ascii=False)),
                    )
                    if packet.tokens > packet.budget:
                        diagnostics.append(
                            {
                                "region": region["id"],
                                "reason": "Required cell metadata and preserved omissions exceed the evidence budget.",
                            }
                        )
                        continue
                    check = validate(
                        Answer(
                            plan_id=bundle["policy_version_id"],
                            status="answered",
                            statements=[statement],
                        ),
                        packet,
                        variant=bundle.get("variant", "Default"),
                        known_variants=tuple(bundle.get("variants", [])),
                    )
                    if not check.passed:
                        diagnostics.append(
                            {"region": region["id"], "reason": "; ".join(check.problems)}
                        )
                    if check.passed:
                        recovered.append(
                            {
                                **statement.model_dump(),
                                "complete_options": field == "sum_insured",
                                "variant_axis_verified": True,
                            }
                        )
                        result.setdefault("table_projection_audit", []).append(
                            {
                                "region": region["id"],
                                "selected_cells": identifiers,
                                "checks": list(check.checks),
                                "packet_tokens": packet.tokens,
                                "packet_budget": packet.budget,
                                "omitted_ids": list(packet.omitted_ids),
                            }
                        )
    return recovered or statements
