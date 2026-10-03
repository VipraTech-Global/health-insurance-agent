from copy import deepcopy

import pytest

from apps.adviser_v2.demo.fact_table_projection import cell_citation
from apps.adviser_v2.tests.test_demo_contracts import packet


def source():
    raw = "5 lakh 5 lakh"
    bundle = {"sections": [packet(raw).sections[0].payload()]}
    bundle["sections"][0]["segments"][0].update(start=0, end=len(raw))
    page = {"passage": raw, "evidence_span_id": "p"}
    chars = [
        {"text": c, "x0": i * 5, "x1": (i + 1) * 5, "top": 10, "bottom": 20}
        for i, c in enumerate(raw)
    ]
    return bundle, page, chars


def test_repeated_table_value_uses_its_physical_cell_not_the_first_occurrence():
    bundle, page, chars = source()
    cite = cell_citation(bundle, page, chars, (35, 9, 65, 21), "5 lakh")
    assert cite.occurrence == 1 and cite.quote == "5 lakh"
    with pytest.raises(ValueError, match="unique exact"):
        cell_citation(bundle, page, chars, (0, 9, 65, 21), "5 lakh")
    with pytest.raises(ValueError, match="unique exact"):
        cell_citation(bundle, page, chars, (10, 9, 20, 21), "5 lakh")


def test_source_and_geometry_occurrence_counts_must_agree():
    bundle, page, chars = source()
    with pytest.raises(ValueError, match="occurrence differs"):
        cell_citation(bundle, {**page, "passage": "5 lakh"}, chars, (35, 9, 65, 21), "5 lakh")


def test_overlapping_windows_can_cite_the_same_unique_absolute_span():
    bundle, page, chars = source()
    second = deepcopy(bundle["sections"][0])
    second["id"] = "z"
    bundle["sections"].append(second)
    assert cell_citation(bundle, page, chars, (35, 9, 65, 21), "5 lakh").section_id == "s"


def test_continued_grid_recovers_only_the_geometrically_aligned_previous_header(
    tmp_path, monkeypatch
):
    import hashlib
    from dataclasses import replace
    from types import SimpleNamespace

    import apps.adviser_v2.demo.fact_table_projection as module
    from apps.adviser_v2.demo.evidence import Segment
    from apps.adviser_v2.demo.fact_table_projection import resolve_sum_grid

    path = tmp_path / "source.pdf"
    path.write_bytes(b"synthetic geometry fixture")
    sha = hashlib.sha256(path.read_bytes()).hexdigest()
    header = "Protect\nAdvantage"
    body = "Outpatient Expenses\nNot Available\nCovered"

    def chars(words):
        return [
            {"text": c, "x0": x + i * 2, "x1": x + (i + 1) * 2, "top": 10, "bottom": 20}
            for text, x in words
            for i, c in enumerate(text)
        ]

    class Table:
        bbox = (0, 0, 300, 100)

        def __init__(self, grid, boxes):
            self.grid = grid
            self.rows = [SimpleNamespace(cells=row) for row in boxes]

        def extract(self):
            return self.grid

    previous = Table([["Protect", "Advantage"]], [[(100, 9, 160, 21), (200, 9, 260, 21)]])
    current = Table(
        [["Outpatient Expenses", "Not Available", "Covered"]],
        [[(0, 9, 90, 21), (100, 9, 160, 21), (200, 9, 260, 21)]],
    )
    pages = [
        SimpleNamespace(
            chars=chars([("Protect", 100), ("Advantage", 200)]), find_tables=lambda: [previous]
        ),
        SimpleNamespace(
            chars=chars([("Outpatient Expenses", 0), ("Not Available", 100), ("Covered", 200)]),
            find_tables=lambda: [current],
        ),
    ]

    class PDF:
        def __enter__(self):
            return SimpleNamespace(pages=pages)

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(module.pdfplumber, "open", lambda _: PDF())
    pkt = packet(body)
    segments = (
        Segment("p1", 1, 0, len(header), 0, len(header), header),
        Segment("p2", 2, 0, len(body), len(header) + 1, len(header) + 1 + len(body), body),
    )
    section = replace(pkt.sections[0], document_sha256=sha, segments=segments)
    pkt = replace(pkt, sections=(section,))
    region = {
        "id": sha + ":2:0",
        "document_id": "doc",
        "cells": {"label": {"citation": {"page_id": "p2"}}},
    }
    bundle = {
        "policy_version_id": "plan",
        "variant": "Protect",
        "variants": ["Protect", "Advantage"],
        "documents": [{"sha256": sha, "path": str(path)}],
        "sections": [section.payload()],
        "tables": [region],
        "pages": [
            {"physical_page": 1, "document_id": "doc", "evidence_span_id": "p1", "passage": header},
            {"physical_page": 2, "document_id": "doc", "evidence_span_id": "p2", "passage": body},
        ],
    }
    result = {"packet": pkt.evidence()}
    found = resolve_sum_grid(result, bundle, [], field="opd")
    assert len(found) == 1 and found[0]["variant_axis_verified"]
    assert {c["page_id"] for c in found[0]["citations"]} == {"p1", "p2"}
    assert found[0]["citations"][1]["quote"] == "Protect"
    assert found[0]["citations"][2]["quote"] == "Not Available"
    assert all(result["table_projection_audit"][0]["checks"])
    previous.rows[0].cells[0] = (120, 9, 180, 21)
    assert resolve_sum_grid({"packet": pkt.evidence()}, bundle, [], field="opd") == []
