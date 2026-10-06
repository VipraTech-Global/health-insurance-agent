"""Compile reviewed per-edition premium charts with exact merged-cell provenance.

Each adapter is pinned to one inspected source hash and its printed layout. Code
checks the printed title, axis labels, age-band order and merged plan-type bounds
against the reviewed grammar, then binds every amount to its physical row, column
and heading. A table or group that differs is reported, never guessed.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, replace
from pathlib import Path

import pdfplumber

from .annual_charts import row_cells, source_quote
from .evidence import atomic_json
from .page_charts import NIVA_REASSURE_3, PageAdapter, parse_page_chart
from .pricing import PrintedPrice, validate_price
from .tier_charts import HDFC_OPTIMA_SECURE, TierAdapter, parse_tier_chart
from .validation import fold, locate

REQUIRED_AXES = {"age", "sum_insured", "composition", "zone", "term", "tax_basis"}
SUM_INSURED = re.compile(r"\d{1,2}(?:,\d{2})*,\d{3}")


@dataclass(frozen=True)
class Adapter:
    sha256: str
    version: str
    title: re.Pattern  # Named groups: term, tax_basis, zone.
    header: tuple[re.Pattern, re.Pattern]
    width: int
    compositions: re.Pattern
    bands: dict[str, tuple[str, ...]]  # Printed age bands per plan type; "*" otherwise.


ASSURE_ADULT = (
    "18-35",
    "36-45",
    "46-50",
    "51-55",
    "56-59",
    "60",
    "61-65",
    "66-70",
    "71-75",
    "76-80",
    "Above 80",
)
# Star Health Assure prospectus PROS / SHA / V.6 / 2026, pages 42-52.
STAR_ASSURE = Adapter(
    sha256="91a761206899caafe957f0c874d75c1b05b9e0b53601d2f57761309a9b0899be",
    version="star-assure-chart/1",
    title=re.compile(
        r"Premium Chart for (?P<term>1 Year) \(in Rs\.\) \((?P<tax_basis>Excluding GST)\)"
        r" \| (?P<zone>Zone [A-D]) \| A-Adult, C-Child"
    ),
    header=(re.compile(r"Plan\s*Type"), re.compile(r"Age\s*Band\s*/\s*SI")),
    width=12,
    compositions=re.compile(r"Individual|[12]A(?:\+[1-3]C)?"),
    bands={"Individual": ("91days-17yrs", *ASSURE_ADULT), "*": ASSURE_ADULT},
)
ADAPTERS = {a.sha256: a for a in (STAR_ASSURE, HDFC_OPTIMA_SECURE, NIVA_REASSURE_3)}


def compile_table(bundle, raw, table, grid, table_id, adapter, place=lambda row: (0, 1)):
    """place(row) gives the row's (occurrence, printed count) among the page's grids."""
    title = adapter.title.fullmatch(" ".join((grid[0][0] or "").split()))
    if (
        not title
        or any(grid[0][1:])
        or any(len(row) != adapter.width for row in grid)
        or not all(p.fullmatch(grid[1][n] or "") for n, p in enumerate(adapter.header))
        or not all(SUM_INSURED.fullmatch(text or "") for text in grid[1][2:])
    ):
        raise ValueError("Printed chart heading or axis labels differ from the reviewed layout.")
    heading = row_cells(bundle, raw, table_id, 0, [grid[0][0]], 0, *place(0))[0]
    heading = replace(heading, column_end=adapter.width - 1)
    cells = {heading.id: heading}
    axes = {}
    heading_start, _ = locate(raw["passage"], heading.text, place(0)[0])
    for name in ("term", "tax_basis", "zone"):
        start, end = locate(raw["passage"][heading_start:], title[name])
        key = heading.id + ":" + name
        cells[key] = replace(
            heading,
            id=key,
            text=title[name],
            citation=source_quote(bundle, raw, heading_start + start, heading_start + end),
        )
        axes[name] = key
    headers = row_cells(bundle, raw, table_id, 1, grid[1], 0, *place(1))
    cells.update({cell.id: cell for cell in headers})
    starts = [n for n in range(2, len(grid)) if grid[n][0]]
    prices, failures = [], []
    if starts[:1] != [2]:
        failures.append({"page": raw["physical_page"], "reason": "No plan type above the rows."})
    for first, end in zip(starts, [*starts[1:], len(grid)], strict=True):
        try:
            label = grid[first][0]
            if not adapter.compositions.fullmatch(label):
                raise ValueError("Plan type is outside the reviewed grammar.")
            expected = adapter.bands.get(label, adapter.bands["*"])
            if tuple(grid[n][1] for n in range(first, end)) != expected:
                raise ValueError("Age bands differ from the reviewed printed order.")
            bbox = table.rows[first].cells[0]
            covered = [
                n
                for n in range(first, len(grid))
                if table.rows[n].cells[1]
                and bbox[1] <= table.rows[n].cells[1][1] + 0.01
                and table.rows[n].cells[1][3] <= bbox[3] + 0.01
            ]
            if covered != list(range(first, end)):
                raise ValueError("Plan-type merged-cell bounds do not cover its age rows.")
        except ValueError as exc:
            failures.append({"page": raw["physical_page"], "row": first, "reason": str(exc)})
            continue
        composition = None
        for row_number in range(first, end):
            row = grid[row_number]
            try:
                if not all(row[1:]):
                    raise ValueError("Amount cells are incomplete.")
                if row_number == first:
                    values = row_cells(
                        bundle, raw, table_id, row_number, row, 0, *place(row_number)
                    )
                    composition = replace(values[0], row_end=end - 1)
                    values[0] = composition
                else:
                    values = row_cells(
                        bundle, raw, table_id, row_number, row[1:], 1, *place(row_number)
                    )
                if composition is None:
                    raise ValueError("No physically aligned plan-type cell.")
                cells.update({cell.id: cell for cell in values})
                age = next(cell for cell in values if cell.column == 1)
                for value in (cell for cell in values if cell.column >= 2):
                    axis_ids = {
                        **axes,
                        "age": age.id,
                        "composition": composition.id,
                        "sum_insured": headers[value.column].id,
                    }
                    price = PrintedPrice(
                        value.id,
                        {name: cells[key].text for name, key in axis_ids.items()},
                        axis_ids,
                        (heading.id, headers[0].id, headers[1].id),
                    )
                    if not validate_price(price, cells, REQUIRED_AXES):
                        raise ValueError("Printed amount or aligned axes failed validation.")
                    prices.append(price)
            except ValueError as exc:
                failures.append(
                    {"page": raw["physical_page"], "row": row_number, "reason": str(exc)}
                )
    return prices, cells, failures


def parse_reviewed_chart(bundle: dict, document: dict, root: Path, adapter) -> dict:
    if isinstance(adapter, TierAdapter):
        return parse_tier_chart(bundle, document, root, adapter)
    if isinstance(adapter, PageAdapter):
        return parse_page_chart(bundle, document, root, adapter)
    prices, cells, failures = [], {}, []
    pages = [p for p in bundle["pages"] if p["document_sha256"] == adapter.sha256]
    with pdfplumber.open(document["path"]) as pdf:
        for raw in pages:
            if not adapter.title.search(" ".join(raw["passage"].split())):
                continue
            tables = [(t, t.extract()) for t in pdf.pages[raw["physical_page"] - 1].find_tables()]
            # Each printed row's text, in reading order across the page's grids.
            texts = [
                [fold(" ".join(text for text in row if text)) for row in grid] for _, grid in tables
            ]
            order = [text for rows in texts for text in rows]
            for n, (table, grid) in enumerate(tables):
                table_id = f"{adapter.sha256}:{raw['physical_page']}:{n}"
                before = [text for rows in texts[:n] for text in rows]

                def place(row, rows=texts[n], before=before, order=order):
                    return (before + rows[:row]).count(rows[row]), order.count(rows[row])

                try:
                    accepted, table_cells, rejected = compile_table(
                        bundle, raw, table, grid, table_id, adapter, place
                    )
                except ValueError as exc:
                    failures.append({"table": table_id, "reason": str(exc)})
                    continue
                prices.extend(accepted)
                cells.update(table_cells)
                failures.extend(rejected)
    result = {
        "index_id": bundle["index_id"],
        "parser_version": adapter.version,
        "required_axes": sorted(REQUIRED_AXES),
        "prices": [asdict(p) for p in prices],
        "cells": {
            key: asdict(c) | {"citation": c.citation.model_dump()} for key, c in cells.items()
        },
        "models": [],
        "failures": failures,
        "status": "parsed" if prices else "invalid_chart",
        "scope": "Exact printed choices for this prospectus edition. No automatic profile-to-age/zone mapping or quotation.",
    }
    atomic_json(root / "premiums" / (bundle["index_id"] + ".json"), result)
    return result
